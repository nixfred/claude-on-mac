# Cookbook: real query recipes you'll want

These are the queries that get used over and over once you start actually working with the data. All examples use generic placeholders; substitute your own handles, dates, accounts.

## Messages

### Hour-of-day distribution (sleep / activity rhythm)

```sql
SELECT strftime('%H', date/1000000000+978307200, 'unixepoch','localtime') AS hr,
       SUM(CASE WHEN is_from_me=1 THEN 1 ELSE 0 END) AS sent,
       SUM(CASE WHEN is_from_me=0 THEN 1 ELSE 0 END) AS received
FROM message
WHERE date/1000000000+978307200 > CAST(strftime('%s','now','-30 day') AS INTEGER)
GROUP BY hr ORDER BY hr;
```

### Top contacts by message volume in the last N days

```sql
SELECT h.id, COUNT(*) AS n,
       SUM(CASE WHEN m.is_from_me=1 THEN 1 ELSE 0 END) AS sent,
       SUM(CASE WHEN m.is_from_me=0 THEN 1 ELSE 0 END) AS received,
       MAX(datetime(m.date/1000000000+978307200,'unixepoch','localtime')) AS last_msg
FROM message m JOIN handle h ON h.ROWID=m.handle_id
WHERE m.date/1000000000+978307200 > CAST(strftime('%s','now','-30 day') AS INTEGER)
GROUP BY h.id ORDER BY n DESC LIMIT 20;
```

Pipe through `~/bin/contacts lookup` to put names on each row.

### Daily cadence with one specific person

```sql
SELECT date(date/1000000000+978307200,'unixepoch','localtime') AS day,
       SUM(CASE WHEN is_from_me=1 THEN 1 ELSE 0 END) AS to_them,
       SUM(CASE WHEN is_from_me=0 THEN 1 ELSE 0 END) AS from_them
FROM message m JOIN handle h ON h.ROWID=m.handle_id
WHERE h.id LIKE '%<their-handle-substring>%'
GROUP BY day ORDER BY day DESC LIMIT 60;
```

### Initiation balance (who texts first per day)

```sql
WITH daily AS (
  SELECT date(m.date/1000000000+978307200,'unixepoch','localtime') AS day,
         m.is_from_me, m.date
  FROM message m JOIN handle h ON h.ROWID=m.handle_id
  WHERE h.id LIKE '%<their-handle-substring>%'),
first_per_day AS (
  SELECT day, is_from_me,
         ROW_NUMBER() OVER (PARTITION BY day ORDER BY date ASC) rn
  FROM daily)
SELECT SUM(CASE WHEN is_from_me=1 THEN 1 ELSE 0 END) AS me_first,
       SUM(CASE WHEN is_from_me=0 THEN 1 ELSE 0 END) AS them_first,
       COUNT(*) AS active_days
FROM first_per_day WHERE rn=1;
```

`imsg analyze <handle>` runs this for you with the histogram, monthly cadence, late-night percentage, and average message length all in one shot.

### Late-night talks with one person (the "real friend" signal)

```sql
SELECT strftime('%Y-%m', date/1000000000+978307200,'unixepoch','localtime') AS mo,
       COUNT(*) AS late_night_msgs
FROM message m JOIN handle h ON h.ROWID=m.handle_id
WHERE h.id LIKE '%<their-handle-substring>%'
  AND CAST(strftime('%H', m.date/1000000000+978307200,'unixepoch','localtime') AS INT)
      IN (22, 23, 0, 1, 2, 3)
GROUP BY mo ORDER BY mo;
```

### Find all handles for one person (some contacts have multiple)

```sql
SELECT DISTINCT h.id, h.service, COUNT(m.ROWID) AS n,
       date(MAX(m.date)/1000000000+978307200,'unixepoch','localtime') AS last
FROM handle h JOIN message m ON m.handle_id = h.ROWID
WHERE h.id LIKE '%<phone-suffix-or-email-fragment>%'
GROUP BY h.id, h.service ORDER BY n DESC;
```

## Mail

### Top sender domains in the last N days

```sql
SELECT
  CASE WHEN instr(a.address,'@') > 0
       THEN substr(a.address, instr(a.address,'@')+1)
       ELSE a.address END AS domain,
  COUNT(*) AS n
FROM messages m
JOIN addresses a ON a.ROWID = m.sender
WHERE m.date_received > CAST(strftime('%s','now','-30 day') AS INTEGER)
GROUP BY domain ORDER BY n DESC LIMIT 20;
```

### Recent personal mail (filter out the alerts/marketing noise)

```sql
SELECT date(m.date_received,'unixepoch','localtime'), s.subject, a.address
FROM messages m
JOIN subjects s ON s.ROWID = m.subject
JOIN addresses a ON a.ROWID = m.sender
WHERE m.date_received > CAST(strftime('%s','now','-14 day') AS INTEGER)
  AND a.address NOT LIKE '%noreply%'
  AND a.address NOT LIKE '%no-reply%'
  AND a.address NOT LIKE '%@e.%'
  AND a.address NOT LIKE '%@email.%'
  AND a.address NOT LIKE '%@news.%'
  AND s.subject NOT LIKE '%Google Alert%'
ORDER BY m.date_received DESC LIMIT 20;
```

Add filters for the specific marketing domains that clutter your inbox.

### Sender + recipient join (recipients table real schema)

```sql
SELECT
  datetime(m.date_received,'unixepoch','localtime') AS ts,
  s.subject,
  af.address AS from_addr,
  ar.address AS to_addr
FROM messages m
LEFT JOIN subjects   s  ON s.ROWID  = m.subject
LEFT JOIN addresses  af ON af.ROWID = m.sender
LEFT JOIN recipients r  ON r.message = m.ROWID AND r.type = 0
LEFT JOIN addresses  ar ON ar.ROWID = r.address
ORDER BY m.date_received DESC LIMIT 20;
```

`recipients.type`: 0 = To, 1 = Cc, 2 = Bcc.

## Notes

### 20 most-recently-modified notes (titles + folder)

```sql
SELECT
  datetime(o.ZMODIFICATIONDATE+978307200,'unixepoch','localtime') AS modified,
  o.ZTITLE1 AS title,
  f.ZTITLE2 AS folder
FROM ZICCLOUDSYNCINGOBJECT o
LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON f.Z_PK = o.ZFOLDER
WHERE o.ZTITLE1 IS NOT NULL
ORDER BY o.ZMODIFICATIONDATE DESC LIMIT 20;
```

Note: `ZICCLOUDSYNCINGOBJECT` is one giant table for both notes and folders; the self-join on `Z_PK` is how you correlate them.

### Most-active folders

```sql
SELECT f.ZTITLE2 AS folder, COUNT(*) AS notes
FROM ZICCLOUDSYNCINGOBJECT o
LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON f.Z_PK = o.ZFOLDER
WHERE o.ZTITLE1 IS NOT NULL AND f.ZTITLE2 IS NOT NULL
GROUP BY folder ORDER BY notes DESC LIMIT 15;
```

## Calendar (via AppleScript)

### Events in the next 14 days

```bash
osascript <<'OSA'
tell application "Calendar"
  set t0 to current date
  set t1 to t0 + 14 * days
  set out to ""
  repeat with c in calendars
    try
      set evs to (every event of c whose start date >= t0 and start date < t1)
      repeat with e in evs
        set out to out & (start date of e as text) & " | " & (summary of e) & " | " & (name of c) & linefeed
      end repeat
    end try
  end repeat
  return out
end tell
OSA
```

## Reminders (via AppleScript)

### Open count by list

```bash
osascript <<'OSA'
tell application "Reminders"
  set out to ""
  repeat with l in lists
    try
      set openN to (count of (reminders of l whose completed is false))
      set out to out & (name of l) & ": " & openN & linefeed
    end try
  end repeat
  return out
end tell
OSA
```

## Cross-source recipes

### Resolve all top-of-month Messages contacts to names

```bash
for h in $(sqlite3 -readonly ~/Library/Messages/chat.db "
  SELECT h.id FROM message m JOIN handle h ON h.ROWID=m.handle_id
  WHERE m.date/1000000000+978307200 > CAST(strftime('%s','now','-30 day') AS INTEGER)
  GROUP BY h.id ORDER BY COUNT(*) DESC LIMIT 20;"); do
    name=$(~/bin/contacts lookup "$h" 2>/dev/null || echo "(no match)")
    printf "  %-30s %s\n" "$h" "$name"
done
```

## The two type-coercion landmines that bite everyone

1. **`strftime('%s', ...)` returns TEXT.** Wrap in `CAST(... AS INTEGER)` before comparing to a numeric date column. Otherwise the query "succeeds" with zero rows. See `sqlite-wal-gotcha.md`.

2. **Apple Cocoa nanoseconds vs UNIX epoch.** Messages and Notes use Cocoa nanoseconds since 2001-01-01: divide by 1e9, add 978307200. Mail's `date_received` is plain UNIX epoch (no division, no offset).

If your query returns "no rows" and your eyes say "but the data is right there", check these two before anything else.
