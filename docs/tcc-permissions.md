# TCC permissions checklist

macOS gates app-data access through TCC (Transparency, Consent, and Control). For the agent to read/write across the ecosystem, the **terminal app you launch Claude Code from** (or the Claude Code app itself) must be granted the relevant permissions.

> Important: TCC attributes the request to the *responsible process*. If you launch Claude Code from iTerm2, then iTerm2 needs the grant. If you run `claude` from VS Code's terminal, VS Code needs the grant. Each grant is per-app.

## Quick check (run this first)

```bash
this repo's bin/tcc-check
```

That script tries each access path and prints what's working / what isn't.

## Per-grant table

| Grant (System Settings → Privacy & Security → …) | Auto-prompts? | Required for | Symptom if missing |
|--------------------------------------------------|---------------|--------------|--------------------|
| **Full Disk Access**                             | ❌ no         | `~/Library/Messages/chat.db`, `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`, `~/Library/Mail/V10/.../Envelope Index`, Safari `History.db` | `sqlite3` reports `unable to open database file` |
| **Contacts**                                     | ✅ yes        | `~/bin/contacts` (the `AddressBook-v22.abcddb` files live under `~/Library/Application Support/AddressBook/`, which Contacts grant covers; FDA also works) | empty results / open error |
| **Calendars**                                    | ✅ yes (read) | AppleScript `tell app "Calendar"` reads | empty list of calendars |
| **Calendars (Write)**                            | ✅ yes (separate prompt on macOS 14+) | Creating/editing events from AppleScript or EventKit | events appear to create then vanish |
| **Reminders**                                    | ✅ yes        | AppleScript `tell app "Reminders"` | "not authorized" osascript error |
| **Photos**                                       | ✅ yes        | `osxphotos` queries | empty library |
| **Automation → (Messages / Notes / Calendar / Reminders / Mail / etc.)** | ✅ yes (per pair) | AppleScript writes from your terminal/Claude Code app | osascript hangs or errors `-1743` |

## Add yourself to FDA (the painful one)

1. **System Settings → Privacy & Security → Full Disk Access**.
2. Click `+`, navigate to `/Applications/`, pick the terminal/IDE you launch Claude Code from. Add `claude` itself if it's a standalone app.
3. Quit and relaunch the terminal. **The FDA grant only takes effect on next launch.**
4. Re-run `imsg recent 1`, should now return rows.

If you don't see the app in the picker, drag-drop it from Finder. If it still won't grant, fully `killall <appname>` then reopen.

## Add Contacts (the easy one)

The first time you run `contacts list`, macOS pops a dialog asking "Terminal would like to access your contacts." Click OK. Done.

If you accidentally clicked "Don't Allow":
- **System Settings → Privacy & Security → Contacts** → toggle your terminal app on.

## Add Automation (per app pair)

Each AppleScript `tell app "X"` triggers a one-time TCC dialog. Approve and you're set. To audit or revoke:

- **System Settings → Privacy & Security → Automation** → expand your terminal app → see the list of apps it can drive.

## Reset (nuclear option)

If TCC gets confused (dialogs not appearing, false errors), reset all grants for an app:

```bash
tccutil reset All com.apple.Terminal           # or your terminal's bundle id
tccutil reset AddressBook                       # just contacts grants
tccutil reset SystemPolicyAllFiles              # FDA grants
```

Then re-trigger the prompts. Use sparingly.

## Verifying programmatically

You can read the current TCC database (read-only, sudo needed):

```bash
sudo sqlite3 -readonly /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT client, service, auth_value FROM access ORDER BY client;"
```

`auth_value=2` means allowed. Use this to debug "why is my script silently failing."

## Special notes for Claude Code

When invoked via the `claude` CLI installed via npm, the responsible process is whatever shell launched it (typically iTerm2 / Terminal.app). Grant THAT app the permissions, not `node` or `claude` itself.

When using the Claude Code Mac app (claude.ai/code Desktop), grant `Claude.app` directly.
