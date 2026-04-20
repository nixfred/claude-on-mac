# Strategy: which mechanism to use per app

There are five fundamentally different ways to talk to an Apple app from a CLI on macOS. Picking the right one per app is the single most important decision you'll make.

## The five mechanisms

### 1. Direct SQLite read
**When:** The app's local store is a documented (or community-reverse-engineered) SQLite file, AND you only need to read.

**Examples:** Messages (`chat.db`), Contacts (`AddressBook-v22.abcddb`), Notes (`NoteStore.sqlite` for metadata), Safari (`History.db`).

**Pros:** Fastest. No app needs to be running. Plain `sqlite3 -readonly` works. Survives across logins.

**Cons:**
- Schema can change between macOS versions.
- WAL gotcha: opening with `immutable=1` makes you miss the most recent writes (see `sqlite-wal-gotcha.md`).
- Requires Full Disk Access for protected stores (Messages, Notes, Mail).
- Some columns are encoded blobs (Messages `attributedBody`, Notes `ZICNOTEDATA`).

**NEVER write directly.** You will corrupt iCloud-syncable data.

### 2. AppleScript (`osascript`)
**When:** You need to write, OR the local SQLite is encrypted/protobuf-encoded.

**Examples:** Sending iMessages, creating Reminders, creating/editing Notes, sending Mail, creating Calendar events (alternative to EventKit).

**Pros:**
- The only sanctioned way to *write* to most Apple apps.
- Stable across macOS versions (Apple maintains the dictionaries).
- One-liners: `osascript -e 'tell app "Reminders" to make new reminder ...'`.

**Cons:**
- The target app usually has to be running (Apple may launch it for you, slow).
- Quoting hell. Build commands programmatically with care.
- Requires Automation permission per (controlling app, target app) pair.
- Slow: 100 to 500ms per call.

### 3. EventKit / Contacts / similar Swift frameworks
**When:** You need write access AND want a fast, robust API (no AppleScript fragility).

**Examples:** Calendar events with recurrence rules, Reminders with geofences, contact CRUD.

**Pros:** Native. Fast. Handles CloudKit-only data correctly (data not cached in local SQLite).

**Cons:** Requires you to write/build a Swift CLI binary, code-sign it (ad-hoc is fine), and embed entitlements in `Info.plist`. We don't do this yet, `FradSer/mcp-server-apple-events` is the model to copy when we want to.

### 4. Shortcuts CLI (`shortcuts run …`)
**When:** You need cross-app actions, OR you need data only Apple exposes via Shortcuts (e.g., HealthKit), OR you want the user to maintain the action graphically.

**Pros:** Cross-app. User-editable. The only reasonable Health bridge.

**Cons:** User has to author the shortcut. Output is whatever the shortcut returns (often awkward). Slower than direct SQLite.

### 5. Direct file read of unprotected stores
**When:** Files like Mail's `.mbox`, Calendar's `.ics` exports, the Photos library's metadata sidecars.

Use sparingly; usually #1 or #2 is better.

## Decision tree

```
Need to WRITE?
├── Yes
│   ├── App has AppleScript dictionary?
│   │   ├── Yes → AppleScript (`osascript`)
│   │   └── No  → EventKit/Contacts Swift CLI; or, for Health, Shortcuts CLI
│   └── (Apple Journal: nothing exists. Use Day One via URL scheme.)
└── No (read only)
    ├── Documented SQLite at known path?
    │   ├── Yes → direct SQLite (`sqlite3 -readonly`)
    │   └── No  → AppleScript read, or Shortcuts CLI
    └── Need cross-app data (Health, etc.)?
        └── Shortcuts CLI
```

## Why we lean SQLite-first

Three reasons:
1. **No daemon.** No app launch latency. No "is Notes.app running?" checks.
2. **Diff-able.** A SQL query is easy to inspect, log, and re-run. AppleScript output is opaque.
3. **Composable.** Output flows into pipes. AppleScript output usually doesn't.

But never write directly. AppleScript handles writes; SQLite handles reads.

## Hybrid pattern for read-then-write

```
imsg from alice --json | jq -r '.[0].handle' | xargs -I{} osascript -e 'tell app "Messages" to send "On my way" to buddy "{}" of service ...'
```

We read with `imsg` (fast, no app launch) and write with AppleScript (the only safe way). This pattern repeats across Reminders ("show what's due, then add a new one"), Notes ("find the daily note, then append"), and Mail ("show last from boss, then reply").
