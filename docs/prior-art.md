# Prior art: existing macOS / Apple ecosystem MCP servers and CLIs

Snapshot as of 2026-04-19.

## "If you only read one project"

**`mattt/iMCP`**, https://github.com/mattt/iMCP
Swift-native MCP server covering Calendar, Contacts, Reminders, Messages, Maps, Weather. Uses real EventKit (not AppleScript). v1.4.0 as of January 2026. Requires macOS 15.3+. The reference architecture for "do this right." Use it directly if you want a turnkey MCP server; read its source if you're rolling your own.

## MCP servers

| Project | Stars | Last active | License | Apps | Write? |
|---------|------:|-------------|---------|------|--------|
| `supermemoryai/apple-mcp` | 3.1k | **ARCHIVED Jan 2026** | MIT | Messages, Notes, Contacts, Mail, Reminders, Calendar | yes |
| `mattt/iMCP` | 1.4k | Jan 2026 | MIT | Calendar, Contacts, Reminders, Messages, Maps, Weather | yes |
| `joshrutkowski/applescript-mcp` | 376 | active | MIT | Calendar, Messages, Mail, Notes, Pages, Finder, system | yes |
| `FradSer/mcp-server-apple-events` | 92 | March 2026 | MIT | Calendar, Reminders | full CRUD |
| `griches/apple-mcp` | 83 | active | MIT | Notes, Messages, Contacts, Mail, Reminders, Calendar | yes |

⚠️ `supermemoryai/apple-mcp` was the most-starred but is archived. Use `mattt/iMCP`, `FradSer/mcp-server-apple-events`, or `joshrutkowski/applescript-mcp` instead.

## Per-app top picks

| App | Best existing project | Why |
|-----|----------------------|-----|
| Calendar | `FradSer/mcp-server-apple-events` | EventKit, full CRUD, recurrence + alarms |
| Reminders | `FradSer/mcp-server-apple-events` | Same server; geofences + subtasks |
| Contacts | `joshrutkowski/applescript-mcp` | AppleScript path, simplest setup |
| Notes | `joshrutkowski/applescript-mcp` | AppleScript only, never touch SQLite for writes |
| Mail | `joshrutkowski/applescript-mcp` | Compose + send + search |
| Messages (read) | this repo's `~/bin/imsg` | Direct SQLite + name resolution |
| Messages (send) | AppleScript via any of the above | `tell app "Messages" to send …` |
| Photos | `RhetTbull/osxphotos` (Python, 3.5k stars) | Deep API; known macOS 26 Tahoe issues to test |
| Safari | direct SQLite read of `History.db` + FDA | No write API; read-only |
| Health | `shortcuts run` bridging | Best available headless path |
| Journal | **none** | No write API exists. Use Day One. |

## What's NOT out there

- A solid Apple **Journal** writer. (Doesn't exist; see `journal.md`.)
- A clean **Health** CLI. Best you can do is craft a Shortcut and `shortcuts run` it.
- Anything for **Apple Intelligence** outputs (summaries, priority, suggestions). These live in scattered plists and Bundle CoreData stores.

## When to graft from prior art vs build your own

**Graft from prior art when:** you need a complex feature (recurring events with attendees, contact CRUD, message attachments). Don't reinvent EventKit code.

**Build your own when:** the feature is a simple read of a documented SQLite store. The total LOC of `~/bin/imsg` and `~/bin/contacts` (~250 each) is less than the dependency-resolution cost of pulling in an MCP server.

## Specifically NOT recommended

- **`supermemoryai/apple-mcp`**, archived, do not depend on it.
- **Direct writes to any Apple SQLite store**, corrupts data and breaks iCloud sync.
- **Any project that "scrapes" Apple Intelligence output by polling notifications**, fragile and likely to break with each macOS update.
