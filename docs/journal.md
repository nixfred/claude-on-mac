# Apple Journal

**Status: ⚠️ writing is not possible. This page documents why, and the workaround.**

## TL;DR

- Apple Journal (introduced iOS 17.2, late 2023; macOS 15) has **no AppleScript dictionary**.
- Apple's `JournalingSuggestions` framework is **read-only from third-party apps' perspective**, it surfaces workouts, music, photos, and calendar events for *other* apps to consume as journaling prompts. It does not let any code write to Apple Journal.
- The `JournalingSuggestionsPicker` SwiftUI view is the only sanctioned way to interact with the framework, and it requires a UI session.
- There is **no Shortcuts action** to create a Journal entry.
- Journal's local store path is undocumented and not exposed via TCC.
- Day One (the leading third-party journal app) confirmed publicly: they consume the suggestions API, they cannot write Apple Journal entries.

So if the agent needs to "write a journal entry for me," it cannot land in Apple Journal.

## Workaround: Day One

Day One has a programmatic write path:

### URL scheme (simple)
```bash
open "dayone://post?entry=$(printf 'My great day' | python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.stdin.read()))')&tags=agent,daily"
```

This opens Day One with the entry pre-filled. Add `&isQuickEntry=true` to bypass the editor and post directly.

### Day One CLI (full control)
Day One ships a `dayone2` CLI:
```bash
dayone2 -j "Personal" --tags agent daily new "Today the agent noticed I texted Alice 3x and Bob once. Reflective day."
```

Install via Day One Mac app preferences → Advanced → "Install Command Line Tools."

## Workaround: plain markdown

A simpler alternative is a daily markdown file under `~/Documents/Journal/2026-04-19.md` that the agent appends to. Searchable, portable, no app dependency. Then the agent can also surface it in Obsidian (already set up, see `obsidian` MCP).

## What the agent CAN do with Apple Journal

Read its prompts/suggestions out of the JournalingSuggestions framework, but only from a SwiftUI app with the `JournalingSuggestionsPicker` view, and only what the user explicitly approves. Not useful from a CLI agent context.

## When this might change

Apple has a track record of opening AppleScript dictionaries 1, 2 macOS releases after launch. Watch for a `Journal.sdef` to appear in `/System/Applications/Journal.app/Contents/Resources/`, if it does, this whole page can be rewritten. As of macOS Tahoe (26.x), no such dictionary exists.

## Recommendation for our agent

For "the agent writes me a journal entry":
1. Default to **Day One** via CLI or URL scheme. Tag entries `agent-authored` so they're searchable.
2. Mirror to a plain markdown daily note for grep-ability and longevity.
3. Skip Apple Journal until/unless an API appears.

the user has expressed a strong preference for Apple Journal as the destination. If/when that changes, swap in Day One. The agent's *content generation* is identical regardless of destination, only the final write step differs.
