# Mail

**Status: read shipped (envelope SQLite + .emlx parser pattern). Send shipped (`~/bin/mail-send`).**

> Send is gated by `consent.md`: every outbound email needs explicit per-message authorization from the user. `mail-send` defaults to dry-run and requires `--yes` to transmit.

## Where the data lives

```
~/Library/Mail/V10/
├── MailData/
│   ├── Envelope Index           ← SQLite: messages, mailboxes, threads
│   └── Envelope Index-{wal,shm}
└── <UUID-per-account>/
    └── INBOX.mbox/
        └── Data/<XX>/<YY>/Messages/<ID>.emlx   ← actual messages
```

The `Envelope Index` SQLite has all the metadata (subjects, dates, from/to, threading) needed for queries. Bodies are in `.emlx` files, RFC-822 with a small length-prefixed header.

## Read pattern (envelope only)

```bash
sqlite3 -readonly "$HOME/Library/Mail/V10/MailData/Envelope Index" "
  SELECT m.subject_prefix, s.subject, a.address,
         datetime(m.date_received,'unixepoch','localtime')
  FROM messages m
  LEFT JOIN subjects  s ON s.ROWID = m.subject
  LEFT JOIN addresses a ON a.ROWID = m.sender
  ORDER BY m.date_received DESC LIMIT 20;
"
```

(`messages.date_received` is a UNIX epoch on macOS Mail, NOT Cocoa epoch. Different from Messages/Calendar.)

## Read pattern (with body)

The `.emlx` file format is:
```
<length-of-rfc822-bytes>\n
<rfc822 message, headers + body>
<XML plist with Mail-specific metadata>
```

Use Python's `email` module to parse the rfc822 portion:
```python
import email
with open(emlx_path, "rb") as f:
    length = int(f.readline().strip())
    msg = email.message_from_bytes(f.read(length))
print(msg["Subject"], msg.get_content())
```

## Write / Send (`~/bin/mail-send`)

AppleScript only. The KEY property for routing through the right account is `sender` on the outgoing message. Set it to a configured email address and Mail.app uses that account's SMTP/IMAP config.

```applescript
tell application "Mail"
  set newMsg to make new outgoing message with properties {¬
    subject:"Hello", ¬
    content:"From the agent.", ¬
    sender:"you@gmail.com",   -- routes via Google account
    visible:false}
  tell newMsg
    make new to recipient at end of to recipients with properties {address:"alice@example.com"}
    send
  end tell
end tell
```

Switching to `sender:"you@icloud.com"` routes via the iCloud account instead. The list of valid sender addresses comes from `email addresses of every account` (which the helper queries at runtime).

### Account map on this Mac

| Alias | Address | Mail.app account |
|-------|---------|------------------|
| `gmail` | `you@gmail.com` | Google |
| `mac` / `icloud` | `you@icloud.com` | iCloud |
| (no alias) | any other addresses you've added in System Settings → Internet Accounts (e.g., extra iCloud aliases) | iCloud (additional aliases) |

Pass any of the full addresses to `--from` to use it; the helper validates the address against `email addresses of every account` before composing.

### `mail-send` quick reference

```
mail-send accounts                                         # list configured accounts
mail-send compose --from gmail --to a@b.c \
                  --subject "..." --body "..." [--yes]     # new message
mail-send compose --from mac --to a@b.c \
                  --cc x@y.z --bcc q@r.s \
                  --subject "..." --body "..." --yes
echo "long body" | mail-send compose --from gmail --to a@b.c \
                                     --subject "..." --yes  # body via stdin
mail-send reply --to-search "Project sync" \
                --body "Confirming." [--from gmail] [--reply-all] [--yes]
mail-send reply --to-message-id "<msg-id@host>" --body "ack" --yes
```

### Reply matching

`reply` walks every mailbox of every account looking for messages matching either:
- `--to-message-id "<RFC822 Message-ID>"` (most precise; copy from any client's "View Source")
- `--to-search "subject substring"` (most recent match wins; useful for one-shots like "reply to that PR review thread")

If `--from` is omitted, Mail.app sends the reply from the account that received the original.

### Set `visible:true` for inspection

For tricky drafts you want to eyeball before send, change `visible:false` to `visible:true` (an open Compose window will appear). The helper currently always uses `false` for clean unattended sends; add a `--visible` flag if you want it.

## TCC

- **Full Disk Access**, for the SQLite envelope index and `.emlx` files.
- **Automation → Mail.app**, for AppleScript reads/sends.

## Planned helper: `~/bin/mail` (read companion)

`mail-send` only handles outbound. A read-side helper is the obvious next build:

```
mail inbox [N]                          # latest envelopes
mail search "<query>"                   # subject + sender LIKE
mail show <message-id>                  # render body
mail unread
mail from <address>                     # thread by sender
```

This will live alongside `mail-send` rather than as a single `mail-cli` to keep responsibilities clean (read tool never has a `--yes` foot-gun; send tool always requires it).

## Pitfalls

- Different macOS versions use different `V<N>` directories (`V8`, `V9`, `V10` on Tahoe). Discover with `ls ~/Library/Mail/`.
- Each Mail account stores messages independently, search across `*.mbox` directories, not just one.
- Encrypted/S-MIME messages need decryption you can't do from the CLI; let Mail.app do it then read.
- Sending via AppleScript respects Mail's outbox + signature, so it'll add your default signature unless you suppress it.
- Apple Intelligence triage (Priority, important) data lives in plists in `MailData/`, not the envelope index.
