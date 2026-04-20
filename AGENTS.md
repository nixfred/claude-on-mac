# AGENTS.md — instructions for the Claude Code agent installing claude-on-mac

> **You are the agent.** A human just pasted a one-line instruction into their Claude Code session pointing at this repo. Your job is to get them set up safely. Read this file top to bottom before doing anything else. Do not skip steps. Do not assume.

## What this repo gives the user

It teaches you (the agent) how to read and write the macOS Apple ecosystem on the user's behalf:

- 💬 **Messages** — read iMessage / SMS / RCS history (`bin/imsg`); send iMessages (`bin/imsg-send`)
- 📇 **Contacts** — search and resolve all contacts (`bin/contacts`)
- 📧 **Mail** — read envelope + bodies; send and reply via the user's configured accounts (`bin/mail-send`)
- 📅 **Calendar** — read events; create events (AppleScript patterns documented)
- ✅ **Reminders** — list, create, complete (AppleScript patterns documented)
- 📝 **Notes** — list and read titles; create / append (AppleScript patterns documented)

What it does NOT give you:

- 📔 Apple Journal write — no programmatic API exists. See `docs/journal.md` for the workaround.
- 🩺 Health — only reachable via the user's authored Shortcuts.

## The single most important rule

🛑 **Read `CONSENT.md` before touching any send helper.** You are NEVER allowed to send an iMessage or email on the user's behalf without explicit per-message authorization for that specific send. Auto modes do NOT override this. Pre-discussed plans do NOT override this. Each send stands alone.

If you violate this, you have failed the install. Re-read `CONSENT.md` and apologize.

## Install protocol — follow this exactly

### Step 1: Introduce yourself and the plan

Tell the user, in your own voice but covering all of these points:

> "I'm about to install the claude-on-mac toolkit. This will give me, your AI agent, the ability to:
>
> - **Read** your Messages, Contacts, Calendar, Notes, Mail, and Reminders.
> - **Send** iMessages on your behalf (only with your explicit per-message permission).
> - **Send** emails via your configured Mail accounts (only with your explicit per-message permission).
>
> Before I install anything, I want you to tell me which capabilities you want and which to skip. You can opt out of any of them, and I'll honor that for the rest of our work together. The send capabilities are gated by a hard rule: I will never send a real message without you explicitly authorizing that exact message."

Then ASK:

1. "Which read capabilities do you want enabled?" (Messages, Contacts, Mail, Calendar, Notes, Reminders — list each, default all yes.)
2. "Do you want me to be able to send iMessages on your behalf?" (Default no until they say yes.)
3. "Do you want me to be able to send email on your behalf?" (Default no until they say yes.)
4. "Any specific apps you want me to NEVER touch, even read-only?"

WAIT for answers. Save the answers to your memory system (e.g., a project memory titled `claude_on_mac_consent_profile`).

### Step 2: Clone the repo

```bash
git clone https://github.com/nixfred/claude-on-mac.git ~/claude-on-mac
```

If `~/claude-on-mac` already exists, `cd` into it and `git pull`. Tell the user.

### Step 3: Symlink only the helpers the user opted in to

For each helper, only create the symlink if the user said yes to its capability:

```bash
mkdir -p ~/bin

# Read-only helpers (default install if user said yes to that capability):
ln -sf ~/claude-on-mac/bin/imsg      ~/bin/imsg       # Messages read
ln -sf ~/claude-on-mac/bin/contacts  ~/bin/contacts   # Contacts read
ln -sf ~/claude-on-mac/bin/cal       ~/bin/cal        # Calendar list/find
ln -sf ~/claude-on-mac/bin/rem       ~/bin/rem        # Reminders list/find
ln -sf ~/claude-on-mac/bin/note      ~/bin/note       # Notes list/find/show
ln -sf ~/claude-on-mac/bin/mail      ~/bin/mail       # Mail read
ln -sf ~/claude-on-mac/bin/tcc-check ~/bin/tcc-check  # always install (verifier)

# SEND helpers (only if the user explicitly said yes in step 1):
ln -sf ~/claude-on-mac/bin/imsg-send ~/bin/imsg-send   # only if they want iMessage send
ln -sf ~/claude-on-mac/bin/mail-send ~/bin/mail-send   # only if they want Mail send

# Calendar/Reminders/Notes WRITE is bundled into cal/rem/note above; the
# `add` / `new` / `append` subcommands still default to dry-run and require
# --yes per individual call. If the user opted out of writes for one of
# these apps, you do NOT need to skip the symlink; just verbally tell
# them you will not invoke the write subcommands.
```

If the user opted out of, say, iMessage sending, do NOT symlink `imsg-send`. Tell them: "I'm not installing imsg-send because you opted out. If you change your mind later, I can add it."

Make sure `~/bin` is in their `PATH`. If it isn't, tell them how to add it (e.g., `echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc`).

### Step 4: Walk through TCC permissions

Run the verifier:

```bash
~/bin/tcc-check
```

It tries each access path and prints ✅ / ❌ for each one. For every ❌:

- If it's a SQLite read failure → user needs to grant **Full Disk Access** to their terminal app or to Claude Code itself. Walk them through System Settings → Privacy & Security → Full Disk Access. They must quit and relaunch the terminal after granting.
- If it's an AppleScript failure → first AppleScript call to that app pops a TCC dialog automatically. Run a benign read once (e.g., `osascript -e 'tell application "Calendar" to get name of every calendar'`) so the dialog appears, and tell the user to click "OK".

Do NOT skip a failing check. Re-run `tcc-check` after each grant until everything is green (within the user's opted-in capabilities).

### Step 5: Smoke-test each enabled capability

For each enabled capability, run a tiny command and show the user the output:

| Capability | Smoke test |
|------------|-----------|
| Messages read | `imsg recent 3` |
| Contacts | `contacts find <a-name-the-user-suggests>` |
| Calendar | `cal calendars` then `cal week` |
| Reminders | `rem lists` (note: Reminders.app via AppleScript is slow, 30s+ is normal) |
| Notes | `note folders` then `note list 5` |
| Mail read | `mail accounts` then `mail inbox 5` |
| iMessage send (if enabled) | `imsg-send --self "claude install proof of life"` (DRY RUN only) |
| Mail send (if enabled) | `mail-send compose --from <hint> --to <user's-other-address> --subject "claude install proof of life" --body "proof"` (DRY RUN only) |

For the send smoke tests, ASK the user: "Want me to actually send the proof-of-life from this dry run? It'll go to your own address." Only run with `--yes` if they say yes.

### Step 6: Build user-context memory

Now run the protocol in `docs/memory-init.md`. That file walks you through:

- Discovering the user's top conversation partners (`imsg contacts 20`, `mail domains 15`)
- Asking the user to classify those contacts (spouse / family / friend / work / service)
- Capturing editorial preferences (drafting style, words to avoid)
- Capturing account routing preferences (which Mail account is personal vs work)
- Capturing default destinations (which Notes folder is the daily journal, which Reminders list is for work, etc.)
- Capturing do-not-touch zones (folders / contacts / calendars to skip)

Save the answers as separate memory entries. Do NOT skip this step. Without it, every future session starts from zero context and the agent feels generic.

ALSO save a memory entry titled `consent_rule_imessage_mail` reinforcing the hard rule from `CONSENT.md`: NEVER send without explicit per-send authorization. This rule survives auto modes and pre-discussed plans.

### Step 7: Confirm and stand down

Tell the user:

> "Install done. Read capabilities enabled: [list]. Send capabilities enabled: [list]. Skipped: [list]. The send helpers default to dry-run; I will always show you the exact text and recipient before you authorize each send. Use `tcc-check` any time to re-verify access. Use `imsg`, `contacts`, `mail-send accounts`, etc., to start using the toolkit. Anything else you want me to do right now?"

DO NOT proactively send anything, read anything, or make recommendations. Wait for their next instruction.

## Conventions you should follow forever after the install

1. **Every send is a deliberate act.** Draft → show dry-run → wait for "yes" → send → report delivery proof. Never batch-prompt for permissions.
2. **Auto-resolve names.** When showing Messages, always use Contacts to put names on numbers (the `imsg` helper does this automatically). Never make the user wonder "who is +15555550100?"
3. **Honor opt-outs.** If they said "don't touch Mail," don't reach for Mail even if a workflow seems to call for it. Ask first.
4. **Surface what you can't do.** Apple Journal write is impossible (see `docs/journal.md`). Don't promise; offer Day One or markdown alternatives.
5. **Use the strategy decision tree.** Read `docs/strategy.md` once. SQLite for reads (no daemon), AppleScript for writes. Never write to Apple's SQLite stores directly — corrupts iCloud sync.
6. **No em/en dashes in drafted messages.** The send helpers auto-scrub. Don't fight them.

## Recommended reading after the install

In this order:

1. **`docs/agent-workflows.md`** — how to actually USE the toolkit. The synthesis patterns for "how am I doing", relationship analysis, inbox triage, send protocol. THIS IS THE FILE THAT TURNS DATA INTO USEFUL HELP. Read it once and refer back when the user makes a high-level ask.
2. **`docs/memory-init.md`** — already covered in Step 6. Re-read when the user adds a new account or relationship.
3. **`docs/strategy.md`** — when to use each mechanism (SQLite vs AppleScript vs EventKit vs Shortcuts).
4. **`docs/cookbook.md`** — copy-pasteable SQL recipes for ad-hoc queries.
5. **`docs/messages.md`** — fully worked example. Other per-app docs follow the same shape.
6. **`docs/sqlite-wal-gotcha.md`** — five-minute read that prevents a class of bugs.
7. **`docs/prior-art.md`** — other OSS projects in this space (some great, some archived).

## Failure modes to watch for

- "permission denied" or empty SQLite reads → user needs Full Disk Access on the terminal/IDE that launched Claude Code. NOT on `node` or `python` themselves.
- AppleScript error -1743 → Automation grant missing for the target app. First call to that app should have prompted; if they dismissed it, fix in System Settings → Privacy & Security → Automation.
- AppleScript error -1728 / -10000 — "Can't get name of every account" / "AppleEvent handler failed" — some Messages.app properties are unreliable on Tahoe. Use service ID iteration (the helpers already do this).
- `osascript` returning success ≠ message delivered. Always verify `is_delivered=1` in chat.db (Messages) or check the Sent mailbox `.emlx` (Mail) before claiming success to the user.

## When you're stuck

Read the relevant `docs/*.md` page. The whole repo is designed so that any future you, or any other Claude Code instance, can pick up where you left off without re-discovering the gotchas.

Now go make the user's life easier. Carefully.
