# Notes

**Status: documented, helper TODO. Read-only via SQLite is safe; writes MUST go through AppleScript.**

## Where the data lives

```
~/Library/Group Containers/group.com.apple.notes/
├── NoteStore.sqlite          ← metadata + ZICNOTEDATA blobs
├── NoteStore.sqlite-wal
└── NoteStore.sqlite-shm
```

This Mac has 406 notes across 20 folders. Read-only SQLite works (no FDA needed if you have Notes-app permission, but FDA is the universal grant).

## ⚠️ Hard rule: NEVER write to NoteStore.sqlite directly

The body of each note is stored in the `ZICNOTEDATA.ZDATA` BLOB as **gzipped proprietary protobuf** (Apple's internal format). Direct SQL writes will corrupt notes and Apple's iCloud sync. Reads are fine; writes go through AppleScript.

## Reading metadata

```bash
sqlite3 -readonly "$HOME/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite" <<'SQL'
SELECT
  o.ZTITLE1                                            AS title,
  datetime(o.ZMODIFICATIONDATE+978307200,'unixepoch','localtime') AS modified,
  f.ZTITLE2                                            AS folder
FROM ZICCLOUDSYNCINGOBJECT o
LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON f.Z_PK = o.ZFOLDER
WHERE o.ZTITLE1 IS NOT NULL
ORDER BY o.ZMODIFICATIONDATE DESC
LIMIT 20;
SQL
```

This gives you titles, folders, and modification dates, enough to find the note you want and then open it in Notes.app or fetch its body via AppleScript.

## Reading note bodies

Two options:

**A) Decompress the protobuf yourself** (community libraries exist, e.g., `apple-notes-liberator`, `applenotesextractor`). Risky, format changes between macOS versions, and the protobuf is undocumented.

**B) AppleScript** (recommended):
```applescript
tell application "Notes"
  set theBody to body of note "Daily 2026-04-19" of folder "Personal"
end tell
```

The body comes back as HTML. Strip tags or convert to markdown as needed.

## Writing notes

```applescript
tell application "Notes"
  tell folder "AI"
    make new note with properties {name:"the agent's daily summary 2026-04-19", body:"<h1>Today</h1><p>...</p>"}
  end tell
end tell
```

Notes app accepts HTML in the `body` parameter and renders rich text. This is also how you'd append to a daily note (read body, concatenate, set body).

## TCC

- **Full Disk Access**, for SQLite reads.
- **Automation → Notes.app**, for AppleScript reads/writes.

## Planned helper: `~/bin/note`

```
note list [N]                       # most-recently-modified
note folders                        # list folders
note find <query>                   # title substring search
note show <title>                   # print body (via AppleScript)
note new "<title>" --folder X       # create
note append <title> --body "<html>" # append HTML to existing
```

## Pitfalls

- `Recently Deleted` folder shows up as a normal folder; filter explicitly.
- Locked notes have empty `ZTITLE1` from SQLite's view; AppleScript can read them after unlock.
- Drawings, scans, and embedded images are stored as separate `ZICCLOUDSYNCINGOBJECT` rows of different `Z_ENT` types.
- Apple Intelligence summaries are stored in `ZSUMMARY*` columns (newer macOS).
