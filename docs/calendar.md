# Calendar

**Status: documented, helper TODO.**

## Why no SQLite?

On this Mac, `~/Library/Calendars/` is empty, the user's calendars live entirely in iCloud and are accessed through EventKit (a managed cache, not a documented SQLite). Direct file access is not viable here. Use AppleScript or build a Swift CLI on EventKit.

## AppleScript path (no extra tooling)

List calendars:
```bash
osascript -e 'tell application "Calendar" to get name of every calendar'
```

Today's events:
```bash
osascript <<'OSA'
tell application "Calendar"
  set today to current date
  set t0 to (today - (time of today))                  -- midnight today
  set t1 to t0 + 24 * hours
  set out to ""
  repeat with c in calendars
    set evs to (every event of c whose start date >= t0 and start date < t1)
    repeat with e in evs
      set out to out & (start date of e) & " | " & (summary of e) & linefeed
    end repeat
  end repeat
  return out
end tell
OSA
```

Create an event:
```bash
osascript <<'OSA'
tell application "Calendar"
  tell calendar "Personal"
    make new event with properties {summary:"Test", start date:(current date), end date:(current date) + 1 * hours}
  end tell
end tell
OSA
```

## Swift / EventKit path (preferred long-term)

For anything more sophisticated (recurrence rules, attendees, alarms), build a Swift CLI:

- Reference: https://github.com/FradSer/mcp-server-apple-events (MIT, full CRUD)
- Reference: https://github.com/mattt/iMCP (MIT, Swift-native, EventKit)

Both link against `EventKit.framework`. Code-signed ad-hoc binaries with the right `Info.plist` entitlements work fine for personal use.

## TCC

- **Calendars** (read), auto-prompts on first AppleScript call.
- **Calendars (Write)**, separate grant on macOS 14+. If you can read but writes silently vanish, you're missing this one.

## Planned helper: `~/bin/cal`

```
cal today
cal tomorrow
cal week
cal month
cal find <query>
cal add "<title>" --at "tomorrow 3pm" --duration 1h --calendar Personal
cal --json today
```

Implementation will likely shell out to `osascript` for Phase 1 and migrate to a Swift binary for Phase 2 if AppleScript proves too slow.

## Pitfalls

- AppleScript `current date` is local time, no timezone. For ISO outputs, format explicitly.
- Recurring events return one event per occurrence in date-range queries, usually what you want, but watch out when bulk-editing.
- Subscription calendars (US Holidays, Birthdays) are read-only.
- Event UIDs are not stable across sync events; identify by `(summary, start date, calendar)` for AppleScript-driven workflows.
