# The `immutable=1` SQLite gotcha

**Symptom:** You query Messages / Notes / Mail and the most recent rows are missing, sometimes by minutes, sometimes by days.

**Cause:** You opened the SQLite file with `?mode=ro&immutable=1`, which tells SQLite "trust me, this file will not change, you can skip the WAL." Apple's apps keep the most recent writes in the WAL until a checkpoint, so `immutable=1` causes you to read a stale snapshot.

## Right way

```python
con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)   # ✅
```

```bash
sqlite3 -readonly /path/to/db                              # ✅ (does not set immutable)
```

## Wrong way

```python
con = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)   # ❌ misses WAL
```

## Why anyone would set `immutable=1`

The flag is a real performance win when you actually have a frozen DB file (e.g., a checkpointed backup), because SQLite skips locking entirely. Tutorials sometimes recommend it as a "safer" read-only option without explaining the tradeoff.

For LIVE Apple stores while their app is running and writing, never use it.

## How to detect this bug in the wild

If a script "worked yesterday" but now misses recent rows:

1. Check the WAL file size: `ls -la <db>-wal`. If it's hundreds of KB or more, there's pending uncommitted data.
2. Force a checkpoint to see if the missing rows appear after: `sqlite3 <db> "PRAGMA wal_checkpoint(TRUNCATE);"`, but only if no app is writing. **Don't do this on Apple's stores while their apps are open.**

In short: don't set `immutable=1` on Apple stores. Live with the slightly slower locking-aware reads, it's the price of seeing the truth.
