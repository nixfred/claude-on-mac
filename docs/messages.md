# Messages (iMessage + SMS)

**Status: read shipped (`~/bin/imsg`). Write TODO.**

## Where the data lives

| Path | What |
|------|------|
| `~/Library/Messages/chat.db` | SQLite store of all message metadata + recent text |
| `~/Library/Messages/chat.db-wal` | WAL log; the most recent messages live here until checkpoint |
| `~/Library/Messages/Attachments/<XX>/<YY>/<UUID>/...` | image/video/audio attachments |

## Schema cheat sheet

- `message`, one row per message. Key columns:
  - `text`, plain text (NULL for macOS Ventura+; text moved to `attributedBody`)
  - `attributedBody`, BLOB (NSAttributedString typedstream); contains the text
  - `date`, Apple Cocoa epoch in **nanoseconds** since 2001-01-01 UTC
  - `is_from_me`, 1 = sent by you, 0 = received
  - `handle_id` → `handle.ROWID`, sender's identity
  - `account`, your sending identity, prefixed (`E:foo@bar.com`, `P:+15555550100`)
  - `destination_caller_id`, your sending identity, plain (used by `imsg-send --list-self`)
  - `service`, "iMessage" / "SMS" / "RCS"
- `handle`, phone numbers / emails. One row per `(id, service)` pair.
- `chat`, conversations (`style=43` for 1:1, `style=45` for group).
- `chat_message_join`, many-to-many between chats and messages.

### Detecting your own handles (no hardcoding)

To find out which addresses YOU send from on this Mac, query `account` and `destination_caller_id` on outgoing messages:

```sql
SELECT DISTINCT destination_caller_id
FROM message
WHERE is_from_me = 1
  AND destination_caller_id IS NOT NULL;
```

`account` rows look like `E:foo@bar.com` (email) or `P:+15555550100` (phone). RCS service rows prefix phone numbers with `tel:` which you'll want to strip. `imsg-send --list-self` does all of this for you and prints the deduped result.

To convert the date: `unix_ts = date / 1e9 + 978307200`.

## Read pattern

```python
con = sqlite3.connect("file:" + db + "?mode=ro", uri=True)   # NOT immutable=1
for r in con.execute("""
  SELECT m.date, m.is_from_me, m.text, m.attributedBody, h.id
  FROM message m LEFT JOIN handle h ON h.ROWID = m.handle_id
  ORDER BY m.date DESC LIMIT 50
"""):
    text = r["text"] or decode_attributed_body(r["attributedBody"])
    ...
```

See `~/bin/imsg` for the full helper, including the `attributedBody` decoder and Contacts name resolution.

## The attributedBody decoder

Apple stores message text as an `NSAttributedString` archived via the typedstream format. The text payload sits at this layout:

```
NSString class declaration … then …
\x84  \x01  +     <length>     <utf-8 bytes>
\x84  literal byte
\x01  ?
+     C-string type signature (0x2B)
length: 1 byte, OR \x81 + u16 LE, OR \x82 + u32 LE
```

The Python decoder is ~15 lines (see `~/bin/imsg`).

## Write (shipped: `~/bin/imsg-send`)

There is no safe way to write to `chat.db` directly. Messages and iCloud will fight you. Use AppleScript via the `~/bin/imsg-send` helper, which defaults to dry-run and requires `--yes` to transmit. See also `consent.md` (every outbound message needs explicit per-message authorization from the user).

### What actually works on macOS Tahoe (26)

The textbook pattern recommended in older blog posts:

```applescript
tell application "Messages"
  set targetService to 1st service whose service type = iMessage   -- BREAKS on Tahoe
  set targetBuddy to buddy "+15555550100" of targetService
  send "..." to targetBuddy
end tell
```

does NOT work on this Mac. Two failure modes observed:

1. `name of every service` → error -1728 ("Can't get name of every account").
2. `service type of s as text` → error -10000 (AppleEvent handler failed) for some services in the list.

The reliable shape is to **enumerate service IDs once, find the iMessage service, then reference it by ID**:

```applescript
tell application "Messages"
  set svc to service id "<YOUR-IMESSAGE-SERVICE-UUID>"
  set p to participant "+15555550100" of svc
  send "On my way" to p
end tell
```

Discover the ID once (it's stable per macOS install) by running:

```applescript
tell application "Messages"
  set out to ""
  repeat with s in services
    try
      set out to out & (id of s) & "|" & (service type of s as text) & linefeed
    end try
  end repeat
  return out
end tell
```

`imsg-send --list-services` does this for you and prints a table.

### Send to an existing chat by GUID

For group chats or when you already know the chat:

```applescript
tell application "Messages"
  send "..." to chat id "iMessage;-;+15555550100"
end tell
```

Note: `chat.db` stores GUIDs as `any;-;<handle>`, but Messages.app expects `<service>;-;<handle>` for the `chat id` form. Convert before passing.

### Naming changes

`buddy` is the old class name; `participant` is the modern synonym. Both work in `sdef`, but new code should use `participant`. The class is `IMHandle` under the hood.

### `imsg-send` quick reference

```
imsg-send --to <handle> [--service iMessage|SMS|RCS] <text>...   # dry run
imsg-send --to <handle> --yes <text>...                          # actually sends
imsg-send --self --yes <text>...                                 # send to your own iMessage
imsg-send --chat-id <guid> --yes <text>...                       # into existing chat by GUID
imsg-send --list-services                                        # show service IDs + types
```

### Pitfalls (learned the hard way)

- **Recipient must already be a known participant**: if Messages.app has never seen this handle, it may silently drop, queue forever, or open a new chat window. Pre-check with `sqlite3 ~/Library/Messages/chat.db "SELECT 1 FROM chat WHERE chat_identifier='<handle>'"`. The helper warns if no prior chat exists for non-iMessage services.
- **SMS/RCS sends require iPhone Continuity**: without an iPhone hooked up via Continuity, they silently fail. iMessage works without an iPhone present.
- **Verify delivery in chat.db, not from osascript exit code**: `osascript` returns 0 the moment Messages accepts the call, NOT when the message is delivered. Check `is_delivered=1` on the new row in `message` to confirm.
- **Drafted text must be scrubbed for em/en dashes** before sending on the user's behalf (per `feedback_no_dashes` rule). `imsg-send` auto-warns if dashes are present.

- **Keep message text out of argv.** Anything in argv is visible to every `ps` on the Mac and ends up in shell history and remote logs. `imsg-send --text-stdin` reads the body from stdin; with `--file-stdin`, `--text-stdin-bytes N` sends the first N bytes as the caption, and `--file-bytes N` refuses a short stream (a cut ssh connection must never become a truncated photo). The AppleScript itself goes to `osascript` on stdin, not `-e`.
- **A group can own several chat rows.** Messages keeps one chat row per service, so a group that moved between iMessage, SMS and RCS leaves rows that share one identifier and differ only by GUID. Exactly one holds the messages. `ORDER BY last_date DESC` sorts the empty shells (NULL last_date) LAST, so a "last row wins" map picked an empty shell, and AppleScript fails with `Can't get chat id (-1728)`. `imsg groups` returns one row per identifier, the one with messages. On one real Mac, 27 of 28 duplicated identifiers were broken this way.

## What chat.db really holds (learned running Blip on it daily)

These were all found by [Blip](https://github.com/nixfred/blip), which reads this database every few seconds from Linux. The helpers here now handle each one.

- **JSON timestamps are UTC ISO-8601** (`2026-09-07T18:33:12Z`) as of v2.0.0. They used to be the Mac's naive wall clock. Compared against a clock in another zone, that string is wrong by hours, and in the DST fall-back hour two messages an hour apart carry the SAME stamp. Fixed-width UTC sorts lexically in time order. Plain-text output keeps local time, because a person reading it wants the time they remember.
- **Announcements are not messages.** Joins, leaves, renames and location-sharing notices live in `message` with `item_type != 0`, have no text, and are never marked read. Counted as messages they are empty rows that stay unread forever. `imsg` hides them; `groups` still reads rename rows for group names.
- **Recently Deleted is still in the table** for 30 days (`chat_recoverable_message_join`). Hidden by default; `IMSG_INCLUDE_DELETED=1` shows them.
- **An unsend is not an edit, and on macOS 26 it never sets `date_retracted`.** Undo Send stamps `date_edited`, clears the body, and lists the withdrawn parts as `rp` in `message_summary_info`. A real edit carries `ec` and keeps its body. `imsg` reads both and reports `retracted` over `edited`.
- **Send Later rows exist before they are sent.** A scheduled message is written the moment it is queued, dated at the FUTURE send time, with `schedule_type = 2` and `schedule_state = 2` (3 once sent; observed on macOS 27). JSON rows carry `"scheduled": true` while it waits, and `chats` does not use it as the conversation's newest message. Anything that takes a watermark or "last seen" time from the newest row must skip it, or it waits until tomorrow.
- **iMessage-app cards store U+FFFD as the text.** Ask to Buy, Fitness sharing, Find My and similar put an `MSMessage` archive in `payload_data`; `imsg` reads the sentence Messages itself shows (`ldtext`), then the caption, then the app name.
- **Newer bodies live only in `attributedBody`**, which SQL `LIKE` cannot case-fold. `imsg search` tries lower, upper and title case.
- **`is_read` is phone-synced but has ghosts.** It reflects the iPhone through Messages in iCloud, but chat.db keeps years-old `is_read = 0` rows. Never count unread from `is_read` alone.
- **Marking read IS possible, through the Messages menu, not the database.** `Conversation > Mark All as Read` is scriptable through System Events (needs Accessibility for the calling process) and reaches the iPhone. The menu reads `enabled=false` whenever Messages is in the background (AppKit validates menus against the active app), so a disabled item proves nothing; count unread in chat.db before and after. Never write `is_read` directly. Blip's `imsg-read` does this; it is not in this toolkit because it acts on the user's account.
- **Tapbacks and edits out are half possible on macOS 26.** Messages has real `Edit > Tapback Message...`, `Reply to Message...` and `Edit Last Message...` menu items, scriptable with SIP on. They act on the SELECTED message, and selecting an arbitrary bubble remotely is the unsolved part. Typing indicators have no menu item.
- **Outbound attachments must be staged under `~/Pictures`** on Sequoia and later, or Messages fails silently (`error = 25`). `imsg-send --file` handles this.
- **macOS 27** (27.0, build 26A428): every read path, contacts, photos and sending verified working on 2026-09-16 with no schema change the helpers depend on.

## Helper: `~/bin/imsg`

```
imsg recent [N]              # newest first
imsg from <handle> [N]       # substring match against handle.id
imsg thread <handle> [N]     # oldest first
imsg search <text> [N]       # LIKE search across text + attributedBody
imsg contacts [N]            # handles ranked by recency, with names
imsg chats [N]               # 1:1 + group chats by recency
imsg groups [N]              # group chats with guid (for imsg-send --chat-id) + members
imsg --json recent 5         # JSON
imsg --no-names recent 5     # skip Contacts resolution (faster on cold cache)
```

## Privacy note

`chat.db` contains everything: family, work, 2FA codes, banking alerts. Treat any read as sensitive. Never dump bulk messages to logs, transcripts, or external services without explicit consent.
