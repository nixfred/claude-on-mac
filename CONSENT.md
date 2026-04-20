# 🔒 CONSENT: the only rule that matters

> **You, the AI agent, are NEVER permitted to send an iMessage, SMS, RCS, or email on behalf of the user without explicit per-message authorization for that specific send.**

This file is load-bearing. Every helper in `bin/` that produces output other people see is gated by this rule. Every doc in `docs/` defers to this rule. The user's trust depends on it.

## What "explicit per-message authorization" means

Two acceptable forms, both very specific:

1. **Pre-discussed.** Recipient, content, and tone have been agreed in the current conversation. The user has reviewed the draft and said "yes" / "send" / "go" for THIS send.
2. **Direct one-shot instruction.** The user named the recipient, the channel, and the gist of what to say (e.g., *"Send Bob a hello at +15555550101 telling him the build is done"*). That counts as authorization for that one send.

Vague encouragement does NOT count:

- ❌ "Use the tools you need." → Not consent for any send.
- ❌ "Auto mode is on." → Not consent for any send.
- ❌ "We talked about this already." → Not consent for THIS send.
- ❌ "Go ahead with your plan." → Not consent for any send.
- ❌ "Reply to that one." → If the user hasn't named the recipient and reviewed the body, ASK FIRST.
- ❌ Implied consent from prior approvals → Each send stands alone.

## You are not OpenClaude

Don't ask "should I send this?" twenty times in a row, batched, while you wait for a thumbs-up. Treat each send as a deliberate act:

1. Draft the message yourself.
2. Show the user the dry-run (recipient + exact text).
3. WAIT for an explicit "send" / "yes" / "go" for THAT specific message.
4. Send.
5. Confirm to the user that it landed (with delivery proof if possible).

The user will say go when they're ready. You will not chase, suggest, or remind.

## What does NOT need consent

Everything that stays private to the user:

- Reading anything (Messages, Contacts, Calendar, Notes, Mail, Reminders).
- Creating a private Reminder or Calendar event with no attendees.
- Appending to a private Note.
- Writing local files (markdown notes, configs).

The line: **does another human see this?** If yes → consent gate. If no → proceed.

## How the helpers enforce this

| Helper | Default | To send |
|--------|---------|---------|
| `imsg-send` | dry-run | requires `--yes` (per send) |
| `mail-send compose` | dry-run | requires `--yes` (per send) |
| `mail-send reply` | dry-run | requires `--yes` (per send) |
| (future write helpers) | dry-run | requires `--yes` |

A loud `CONSENT-GATED SEND` banner is printed to stderr immediately before any actual transmit. If you see that banner without having received explicit per-send authorization from the user, you have made a mistake.

## When in doubt

Pause and ask. The cost of asking is one round-trip. The cost of an unwanted send is irreversible (the user can delete the thread on their end; the recipient's copy stays on their device forever).

## Auto-scrub: dashes

Drafted messages also auto-scrub em-dashes (`—`), en-dashes (`–`), and `--`, replacing them with `, `. This matches a separate editorial preference. Pass `--keep-dashes` to override on a specific send.

## Audit trail

Every actual send is observable in the user's local data:

- iMessage / SMS: `~/Library/Messages/chat.db`
- Mail: `~/Library/Mail/V*/MailData/Envelope Index` and the Sent mailbox `.emlx` files

To review what you (the agent) have sent on the user's behalf in the last day:

```bash
sqlite3 -readonly ~/Library/Messages/chat.db \
  "SELECT datetime(date/1000000000+978307200,'unixepoch','localtime') AS ts, text
   FROM message WHERE is_from_me=1 AND date/1000000000 + 978307200 > strftime('%s','now','-1 day')
   ORDER BY date DESC;"
```

The user can audit you any time. Make sure the trail tells a story they're proud of.
