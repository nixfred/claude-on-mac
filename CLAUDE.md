# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Two distinct roles

This repo has a split personality, and it matters which mode you're in:

1. **Installer agent** (when a user pastes the magic line from README.md). Your contract is `AGENTS.md` — follow its install protocol exactly: introduce, ask opt-ins, clone, symlink only approved helpers, run `tcc-check`, smoke-test, build memory via `docs/memory-init.md`. Do not improvise.
2. **Maintainer** (working on the toolkit itself). Your contract is this file plus the repo conventions below. You are editing the helpers and docs that other Claude Code instances will consume.

If the current conversation is about *using* claude-on-mac on a user's Mac, you are role #1 and `AGENTS.md` overrides this file for the install flow. If the conversation is about *changing* the toolkit, you are role #2.

## THE load-bearing rule

`CONSENT.md` governs every send-side helper (`imsg-send`, `mail-send compose`, `mail-send reply`). Send nothing without explicit per-message authorization for that specific send. `--yes` is required per individual send; dry-run is the default. A `CONSENT-GATED SEND` banner prints to stderr right before any real transmit — seeing that banner without an explicit user "yes" for THIS send means something is wrong. Any change to a send helper must preserve this gate.

## Stack

- **Python 3** (stdlib only — no `pip install`, no `requirements.txt`, no virtualenv). Every helper starts with `#!/usr/bin/env python3`. If you're tempted to add a dependency, don't — find a stdlib path.
- **No build, no compile, no test runner.** There is no CI, no linter config, no pytest. Verification is `tcc-check` (functional probe) plus manual smoke tests per `AGENTS.md` Step 5.
- **No daemons, no MCP servers, no API keys.** Everything is `sqlite3 -readonly`, `osascript`, or direct file reads.

## The architecture decision that drives everything

**Read with SQLite. Write with AppleScript. Never write to Apple's SQLite stores directly — it corrupts iCloud sync.** Full decision tree in `docs/strategy.md`. This split explains why helpers that both read and write (e.g., `note`, `cal`, `rem`) are internally two-faced: SQLite code path for list/find/show, `osascript` code path for new/add/append.

Corollary: helpers that need the app to be *running* (AppleScript) are slower (100–500ms/call, Reminders can be 5s+ on cold CloudKit). Helpers that only read SQLite are fast and work even if the app is quit.

## Helpers (all in `bin/`, all on `$PATH` via `~/bin` symlinks after install)

| Helper | Mode | Key gotcha |
|--------|------|-----------|
| `imsg` | SQLite read | Decodes `attributedBody` typedstream blob; auto-resolves handles to contact names |
| `imsg-send` | AppleScript write | Consent-gated; dry-run default; auto-scrubs em/en-dashes unless `--keep-dashes` |
| `contacts` | SQLite read | Phone-suffix matching across iCloud + on-device sources |
| `cal` | SQLite read + AppleScript write | `add` requires `--yes` and `--calendar` |
| `rem` | AppleScript read+write | Reminders CloudKit can be slow on cold cache; helper bumps timeout to 300s |
| `note` | SQLite read + AppleScript write | Body is protobuf-encoded in SQLite, so `show`/`append` route through AppleScript |
| `mail` | SQLite read + `.emlx` parse | Envelope Index at `~/Library/Mail/V*/MailData/Envelope Index` |
| `mail-send` | AppleScript write | Account-aware; consent-gated; `--from` takes a hint matched against configured accounts |
| `tcc-check` | Probe | Functional verifier — run after any change that could affect access paths |

## Known gotchas you WILL trip on

- **`imsg` namespace collision.** A brew/cargo-installed Rust `imsg` (v0.5.x) shadows ours if earlier in `PATH`. `AGENTS.md` Step 3.5 has the detection-and-fix protocol; preserve it when editing the install flow.
- **WAL mode on Messages' chat.db.** Opening with `immutable=1` makes you miss recent writes. Details in `docs/sqlite-wal-gotcha.md`.
- **`strftime('%s', ...)` returns TEXT.** Comparing it against Apple's numeric date columns silently returns zero rows. Always `CAST(... AS INTEGER)`.
- **Notes date columns vary by origin.** `COALESCE` across `ZMODIFICATIONDATE`, `ZMODIFICATIONDATE1`, `ZMODIFIEDDATE`, `ZCREATIONDATE`, `ZCREATIONDATE1`, `ZCREATIONDATE2` on `ZICCLOUDSYNCINGOBJECT`.
- **AppleScript success ≠ delivery.** Verify `is_delivered=1` in `chat.db` (Messages) or Sent `.emlx` (Mail) before claiming a send succeeded.
- **TCC dialogs have a 60s window.** `tcc-check` prints an upfront banner; keep it. Users miss dialogs if they context-switch.

## Conventions for editing helpers

- **Match the existing shape.** Each helper has a top docstring listing its subcommands. Update it when you add one. `AGENTS.md`'s Step 5 smoke-test table is the canonical subcommand inventory — keep these in sync.
- **Dry-run is the default for any helper that writes something another human sees.** `--yes` opts into real execution. This is not a style preference; it's the consent contract.
- **No em/en-dashes in drafted message text.** Send helpers auto-scrub. Don't reintroduce them in templates or defaults.
- **Use `sqlite3 -readonly`** for all read queries, even when the DB isn't protected. Signals intent and prevents accidents.
- **When subcommand arg-parsing breaks**, check both positions — `--flag` before AND after the subcommand should work. See v1.1.0 changelog for the precedent.

## Docs are part of the product

`docs/` is what other Claude Code instances read to orient themselves on a user's Mac. Treat doc updates as first-class changes, not an afterthought. Entry points:
- `docs/strategy.md` — the decision tree for which mechanism to use
- `docs/agent-workflows.md` — synthesis patterns (the file that turns data into useful help)
- `docs/memory-init.md` — first-run user-context memory protocol
- `docs/cookbook.md` — copy-pasteable SQL recipes
- `docs/tcc-permissions.md` — permission-grant walkthrough
- Per-app: `messages.md`, `contacts.md`, `calendar.md`, `reminders.md`, `notes.md`, `mail.md`, `journal.md`
- `docs/sqlite-wal-gotcha.md` — five-minute read that prevents a bug class

## Releasing

Versioning is documented in `CHANGELOG.md` (currently v1.2.2). Bump there, mention the repo version in README badges if it shifts, commit with a changelog-shaped message. There is no tag automation; tags are cut manually if at all.

## This repo is PUBLIC

`github.com/nixfred/claude-on-mac`. Any real phone number, email, contact name, calendar name, or iMessage service UUID that lands in a commit leaks it forever. v1.1.0 already required a force-push to rewrite history after incidental leakage — don't make us do it again. Use generic placeholders (`+15555550100`, `alice@example.com`) in docs and examples. Run `git remote -v` before pushing.
