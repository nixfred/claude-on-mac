# Changelog

## v1.2.2 , 2026-04-20

Second round of fixes from the cross-host install feedback. The v1.2.1 fixes all landed, but verifying them on the second Mac surfaced THREE more real UX issues, all addressed here.

### Fixed
- **`bin/tcc-check` now probes Mail.app too**. v1.2.1 probed Calendar / Reminders / Notes, but Mail was missing from the probe list — so Mail's TCC Automation dialog was firing silently on first use of `mail accounts` or `mail-send`, with no 60s warning and no install-time ceremony around it. Adding Mail to the probe set means all four writer apps (Calendar, Reminders, Notes, Mail) get their grants captured during install.
- **`bin/tcc-check` prints a loud upfront banner** when it starts: "macOS will show you up to FOUR Allow dialogs in the next minute, WATCH YOUR SCREEN, click Allow on each." This is the single biggest UX fix in the whole install flow. The root cause of almost every "install looks broken" symptom was "the human didn't know dialogs were coming and had context-switched away." The banner + the per-probe 60s warning together solve it.
- **`AGENTS.md` Step 4 preamble strengthened** with the verbatim user-facing warning the agent should say BEFORE firing tcc-check. No more hoping the agent figures out the right expectation-setting language.
- **`AGENTS.md` Step 3.5 PATH remediation is now shell-aware**. v1.2.1 suggested `echo ... >> ~/.zshrc`, which silently fails for the ~half of macOS users who use bash (Apple shipped bash as default until macOS 10.15, plenty of users still running it). Now detects `$SHELL` and picks `~/.zshrc` or `~/.bashrc` accordingly. Also notes the `~/.bash_profile` gotcha (login shells source it AFTER `.bashrc`, so PATH manipulations there can override earlier work) and suggests auditing existing `export PATH` lines before adding a third.

### Retracted (from the v1.2.1 feedback)
- The `imsg recent doesn't exist` item was a false positive caused by the brew-installed Rust `imsg` CLI shadowing our helper in PATH. Our `imsg` does have `recent`; the nixf agent was invoking the wrong binary. Step 3.5 (PATH collision check) is the right fix, already in v1.2.1. Retraction captured in the nixf install feedback addendum.

## v1.2.1 , 2026-04-20

Fixes from a real cross-host install on a second Mac. A separate Claude Code instance ran the one-paste install on another machine and logged 5 concrete issues. All addressed here.

### Fixed
- **`tcc-check` osascript timeout bumped from 15s to 60s** on each AppleScript probe, with a "⏳ approve any system dialog within 60s" prompt printed before each one. Previously, on a clean machine with no prior Automation grants, the install looked like failure because the human couldn't click the TCC dialog within the 15-second shot clock.
- **`bin/mail accounts`** now uses AppleScript to list configured Mail.app accounts with display name and primary addresses, same format as `mail-send accounts`. Previously it scraped the envelope SQLite `mailboxes` table and emitted one line per IMAP folder URL, which was useless for figuring out what to pass to `mail-send --from`.
- **`bin/note list`** no longer shows "(unknown)" timestamps. Apple has ~6 date-ish columns on `ZICCLOUDSYNCINGOBJECT` (ZMODIFICATIONDATE, ZMODIFICATIONDATE1, ZMODIFIEDDATE, ZCREATIONDATE, ZCREATIONDATE1, ZCREATIONDATE2) and which are populated varies by note origin. We now `COALESCE` across all six.
- **`AGENTS.md` Step 3.5 added**: explicit `imsg` namespace-collision check. A pre-existing Rust `imsg` CLI (version 0.5.x, installed via brew/cargo on some Macs) can shadow our helper if it's earlier in PATH. Protocol now runs `command -v imsg` and `imsg --help` to verify our helper is the one being invoked before smoke-testing.
- **`AGENTS.md` Reminders slowness caveat softened**: "can be slow on machines where Reminders CloudKit is cold; usually 2-5s, sometimes 30s+" instead of the blanket "30s+ is normal" claim, which was host-specific to the build machine.
- **`AGENTS.md` Step 4 text**: explicit user-facing prompt ("I'm about to run tcc-check. You'll see up to three dialogs. Click OK on each within 60 seconds.") so the agent can set expectations before firing the probes.

## v1.2.0 , 2026-04-20

### Added
- **`~/bin/cal`** Calendar helper: `calendars`, `today`, `tomorrow`, `week`, `month`, `range`, `find`, `add` (write requires `--yes` and `--calendar`).
- **`~/bin/rem`** Reminders helper: `lists`, `open [<list>]`, `due`, `find`, `add`, `done` (write requires `--yes`). Note: Reminders.app via AppleScript is fundamentally slow on modern macOS (CloudKit round-trips per list); 5+ second reads are normal, the helper bumps timeout to 300s.
- **`~/bin/note`** Notes helper: `list`, `folders`, `find`, `show` (body via AppleScript), `new`, `append` (writes require `--yes`). Reads use SQLite metadata for speed; never writes to NoteStore.sqlite.
- **`~/bin/mail`** Mail read helper: `accounts`, `inbox`, `unread`, `search`, `from`, `today`, `domains`, `show <ROWID>`, `show-id <Message-ID>`. Walks `.emlx` files for body retrieval.
- **`docs/agent-workflows.md`**: synthesis patterns for the agent. Workflows for "how am I doing", relationship analysis, inbox triage, send protocol, internal-write protocol, recall queries. THIS IS THE FILE THAT TURNS DATA INTO USEFUL HELP.
- **`docs/memory-init.md`**: first-run protocol for the agent to build user-context memory (top contacts classification, account routing, default destinations, do-not-touch zones).

### Changed
- **`AGENTS.md`** install protocol now installs all 9 helpers (was 5), walks the new memory-init step, references the new agent-workflows doc.
- **`README.md`** capability table shows all six Apple apps as ✅ shipped.

### Net effect
The toolkit is now functionally complete enough that any Claude Code on any Mac can replicate the analyses we did to validate it on the build host: read all surfaces, send with consent, run a relationship-arc analysis, do an emotional/life-state read, triage an inbox. Synthesis quality still depends on the model on the other end, but the data layer and the workflow patterns are both shipped.

## v1.1.0 , 2026-04-19

### Added
- **`imsg analyze <handle>`**: relationship-arc analysis for one handle. Lifetime totals, monthly cadence, hour-of-day histogram (ASCII), initiation balance, late-night percentage, average message length per side. JSON output with `--json`.
- **`docs/cookbook.md`**: real query recipes from actual use (top contacts, daily cadence, initiation balance, late-night talks, mail sender domains, mail recipient join with corrected schema, notes by folder, calendar events).

### Fixed
- **`imsg --chrono` arg parsing**: previously failed with "unrecognized arguments" when placed after the subcommand. Now works in both positions (`imsg --chrono from <h>` and `imsg from <h> --chrono`). Same fix applied to `--json` and `--no-names`.
- **`imsg-send --list-self`**: strips the `tel:` prefix that the RCS service prepends to phone numbers.
- **`docs/mail.md`**: corrected the recipients-table join example. The columns are `recipients.message` and `recipients.address` (NOT `message_id`/`address_id` as some older blog posts state).
- **`docs/sqlite-wal-gotcha.md`**: documented the silent landmine where `strftime('%s', ...)` returns TEXT and SQLite returns zero rows when comparing against numeric date columns. Always `CAST(... AS INTEGER)`.
- **`docs/messages.md`**: documented the `account` and `destination_caller_id` columns used for self-handle detection.
- **Sanitization sweep**: removed all incidental personal-identifier leakage (one machine-specific iMessage service UUID, one phone number example, one email example, one calendar name) that slipped through the v1.0.0 commit. Working tree and (rewritten) git history both contain only generic placeholders.

### Note
- v1.0.0 commit history was rewritten via force-push. Anyone who cloned within the first hour after release should re-clone. Zero forks at the time of rewrite.

## v1.0.0 — 2026-04-19

First public release.

### Shipped helpers (in `bin/`)

- **`imsg`** — read iMessage / SMS / RCS from `~/Library/Messages/chat.db`. Decodes the `attributedBody` typedstream (macOS Ventura+ moved message text out of the `text` column). Auto-resolves handles to Contacts names.
- **`contacts`** — read 10K+ contacts across all configured Contacts source DBs (iCloud, CardDAV). Phone-number suffix matching. Lookup by phone or email.
- **`imsg-send`** — send iMessage / SMS / RCS via Messages.app AppleScript. Defaults to dry-run; requires `--yes` per send. Auto-scrubs em/en dashes. Auto-detects own self-handles from chat.db.
- **`mail-send`** — send / reply via Apple Mail.app, account-aware. Routes via the right account by setting `sender` on the outgoing message. Defaults to dry-run; requires `--yes` per send.
- **`tcc-check`** — verify all TCC permissions and access paths in one shot.

### Shipped docs (in `docs/`)

`strategy.md`, `tcc-permissions.md`, `consent.md`, `messages.md`, `contacts.md`, `calendar.md`, `reminders.md`, `notes.md`, `mail.md`, `journal.md`, `prior-art.md`, `sqlite-wal-gotcha.md`.

### Top-level

- `README.md` — human-facing flashy intro + the magic copy-paste line for Claude Code.
- `AGENTS.md` — what Claude Code reads and follows when you paste the magic line.
- `CONSENT.md` — the load-bearing send-consent rule.
- `LICENSE` — MIT.

### Known limitations (documented, not bugs)

- **Apple Journal**: no programmatic write path exists. Use Day One via URL scheme or markdown daily notes. See `docs/journal.md`.
- **Health**: only reachable via the `shortcuts` CLI bridge. Not yet wired here.
- **Photos**: prior art is `RhetTbull/osxphotos`. Not yet wired here.
- **Calendar / Reminders / Notes write helpers**: documented patterns in their respective docs, but no CLI helper shipped yet. Patterns work today via direct `osascript`.

### Verified on

macOS Tahoe (26.x), Apple Silicon. Should work on macOS Sonoma (14.x) and Sequoia (15.x); the SQLite schemas and AppleScript shapes have been stable in those releases.
