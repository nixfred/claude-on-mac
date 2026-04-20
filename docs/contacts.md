# Contacts

**Status: read shipped (`~/bin/contacts`). Write TODO via AppleScript.**

## Where the data lives

```
~/Library/Application Support/AddressBook/
├── AddressBook-v22.abcddb            ← root metadata (small)
└── Sources/
    ├── <UUID-1>/AddressBook-v22.abcddb   ← iCloud account (largest)
    └── <UUID-2>/AddressBook-v22.abcddb   ← e.g., CardDAV / local
```

Each Contacts source (iCloud, CardDAV, on-device) has its own SQLite DB. The `~/bin/contacts` helper reads ALL of them and merges, deduping on `(name, phone-suffix)`.

## Key tables

- `ZABCDRECORD`, one row per contact. Useful columns:
  - `Z_PK`, primary key (referenced by phones/emails)
  - `ZFIRSTNAME`, `ZLASTNAME`, `ZNICKNAME`, `ZORGANIZATION`, `ZJOBTITLE`
  - `ZMODIFICATIONDATE`, `ZCREATIONDATE`
  - `ZBIRTHDAY`, `ZNOTE`
- `ZABCDPHONENUMBER`, `ZOWNER` → record PK, `ZFULLNUMBER`, `ZLABEL`
- `ZABCDEMAILADDRESS`, `ZOWNER`, `ZADDRESS`, `ZLABEL`
- `ZABCDPOSTALADDRESS`, `ZABCDURLADDRESS`, `ZABCDSOCIALPROFILE`, etc.
- `ZABCDRELATEDNAME`, relationships (spouse, mom, etc.)

## Phone matching

Phone numbers in Contacts come in many shapes (`+15555550100`, `(404) 555-1212`, `404.555.1212`, `4045551212`). To match against Messages handles, normalize both sides:

> **Useful workflow:** `imsg from <substring>` only matches against the raw `handle.id` column (phone or email string). It does NOT search by contact name. So `imsg from alice` will only find rows where the *handle* string contains "alice" (e.g., her email), not where Alice's *contact name* is associated. To get a thread by contact name: `contacts find alice` to grab her phone number, then `imsg from <number>`.


```python
import re
def norm(s): 
    digits = re.sub(r"\D", "", s or "")
    return digits[-10:] if len(digits) >= 10 else digits
```

Suffix matching by last 10 digits handles US numbers correctly. For international numbers, strip the leading `+` and match full digit string.

## Helper: `~/bin/contacts`

```
contacts sources              # list all source DBs and record counts
contacts list [N]             # most-recently-modified, default 50
contacts find <query> [N]     # substring across name/org/phone/email
contacts lookup <h>           # phone-or-email → name (exit 1 if no match)
contacts dump [--json]        # everything
```

Handy combos:
```bash
contacts lookup +15555550103          # → "Carol Example"
contacts find acme | head -5          # everyone at Acme
imsg contacts | head -20              # auto-resolves via this CLI's logic
```

## Write (TODO)

For now, write via AppleScript:

```applescript
tell application "Contacts"
  set p to make new person with properties {first name:"Jane", last name:"Doe"}
  make new phone at end of phones of p with properties {label:"mobile", value:"+15555550100"}
  save
end tell
```

The `save` is critical, without it, changes don't persist. Note that AppleScript writes are picked up by iCloud sync.

Long-term, a Swift CLI using the Contacts framework is more reliable than AppleScript (no `save`-forgetting bugs, faster). See `FradSer/mcp-server-apple-events` for a model.

## Performance

Reading 10K contacts across 3 source DBs takes ~150ms on a recent Apple-Silicon Mac. The `~/bin/imsg` helper builds a phone/email → name index lazily on first lookup and caches it for the process lifetime.

## Edge cases

- **Multiple sources, same person**: dedupes by `(name, sorted phone suffixes)`, usually correct, occasionally splits a contact who only has email in iCloud and only has phone in CardDAV.
- **Records with no name**: filtered out (would clutter results).
- **"Me" card**: appears as a normal record with `Z_22_ME = 1`. Currently treated like any other contact.
- **Linked contacts**: iCloud links several source records into one display contact. The helper sees the source records, not the linked union, minor cosmetic issue.
