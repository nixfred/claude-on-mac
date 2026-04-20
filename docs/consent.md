# Consent: human-in-the-loop for outbound communications

> Hard rule: every message that another person will see requires explicit per-message authorization from the user. Auto mode does NOT override this.

## What needs consent

Anything that produces output another human can see:

- iMessage / SMS / RCS sends (`imsg-send`)
- Outbound Mail (Apple Mail send, future `mail-cli send`)
- Calendar invites with attendees
- Reminders shared to another iCloud user
- Notes shared with collaborators
- Any AppleScript that posts content to a third-party app (Slack, Discord, etc.)

## What does NOT need consent

Internal-only writes that stay private to the user:

- Reading anything (Messages, Contacts, Calendar, Notes, Mail, Reminders)
- Creating a private Reminder for the user
- Creating a Calendar event with no attendees
- Appending to a private Note
- Writing to local files (markdown daily notes, scripts, configs)

The line: would another person see this? If yes, consent gate. If no, proceed.

## What "explicit per-message authorization" means

Two acceptable forms:

1. **Pre-discussed.** The recipient, content, and tone have been agreed in this conversation. "Send Alice a quick `running 10 min late` text" + a previous draft you've reviewed = consent.
2. **Direct one-shot instruction.** "Send Bob a hello at +1 706 202 4891 telling him what we just did" = consent for that one specific send.

Vague encouragement does NOT count:
- "Use the tools you need" → not consent for any send
- "Go ahead with your plan" → not consent for any send
- Auto mode being active → not consent for any send

## How the helpers enforce this

- `~/bin/imsg-send` defaults to dry-run. `--yes` is required to transmit.
- Any future `mail-cli send`, `cal add --invitee ...`, etc. follow the same `--yes` gate.
- The dry-run prints the exact text and recipient so you can sanity-check before authorizing.
- All drafted text auto-scrubs em/en dashes (per `feedback_no_dashes`); pass `--keep-dashes` to override.

## When in doubt

Pause and ask. The cost of asking is one round-trip; the cost of an unwanted send is irreversible (you can delete a Messages thread on your end, but the recipient's copy stays on their device). Always err toward asking.

## Audit trail

Every actual send is observable in `chat.db` (Messages), Mail's Sent mailbox, etc. To review what the agent has sent on the user's behalf:

```bash
imsg from <handle> --chrono   # see the thread, the agent's sends interleaved
sqlite3 -readonly ~/Library/Messages/chat.db \
  "SELECT datetime(date/1000000000+978307200,'unixepoch','localtime'), text
   FROM message WHERE is_from_me=1 ORDER BY date DESC LIMIT 50;"
```
