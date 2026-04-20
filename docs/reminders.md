# Reminders

**Status: documented, helper TODO.**

## No local SQLite

Reminders is fully CloudKit-backed; there is no `~/Library/Reminders/` SQLite to query. Use AppleScript or EventKit.

## AppleScript path

List reminder lists:
```bash
osascript -e 'tell application "Reminders" to get name of every list'
```

Open reminders in a list:
```bash
osascript <<'OSA'
tell application "Reminders"
  tell list "Reminders"
    set out to ""
    repeat with r in (every reminder whose completed is false)
      set out to out & name of r & " | " & (due date of r as text) & linefeed
    end repeat
    return out
  end tell
end tell
OSA
```

Add a reminder:
```bash
osascript <<'OSA'
tell application "Reminders"
  tell list "Reminders"
    make new reminder with properties {name:"Pick up Freya", due date:date "Sunday, April 20, 2026 5:00:00 PM"}
  end tell
end tell
OSA
```

Mark complete:
```applescript
tell application "Reminders"
  set r to first reminder of list "Reminders" whose name is "Pick up Freya"
  set completed of r to true
end tell
```

## EventKit path (faster, more reliable)

Same story as Calendar, `FradSer/mcp-server-apple-events` is the model. Reminders share the EventKit framework with Calendar; subtasks, geofences, and priorities are all available.

## TCC

- **Reminders**, auto-prompts on first AppleScript call. No separate write grant.

## Planned helper: `~/bin/rem`

```
rem lists                              # show all lists
rem open [<list>]                      # open reminders in list (default: all)
rem due                                # everything due today + overdue
rem add "<text>" [--list X] [--due "tomorrow 3pm"]
rem done <id-or-name>
rem --json open
```

## Pitfalls

- Times are local; AppleScript date strings are locale-sensitive, prefer constructing dates from components.
- `due date` vs `remind me date` are different fields. `due date` is for date-only reminders; `remind me date` is for time-specific.
- Subtasks via AppleScript are fiddly. EventKit handles them cleanly.
