# Changelog

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
