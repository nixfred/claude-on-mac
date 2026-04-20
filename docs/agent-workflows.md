# Agent workflows: how to actually USE the toolkit

> This file is for the AI agent installed on the user's Mac. It teaches synthesis patterns: how to turn the raw helpers into the kinds of analyses the user will actually ask for.

The other docs teach you WHAT data exists and HOW to query it. This file teaches you WHAT TO DO with it when the user makes a high-level request.

## Workflow: "How am I doing?"

When the user asks any variant of "how am I doing emotionally / in life / right now", do this exact sequence:

1. **Pull message-rhythm signal:**
   ```bash
   sqlite3 -readonly ~/Library/Messages/chat.db "
     SELECT strftime('%H', date/1000000000+978307200, 'unixepoch','localtime') AS hr,
            SUM(CASE WHEN is_from_me=1 THEN 1 ELSE 0 END) AS sent,
            SUM(CASE WHEN is_from_me=0 THEN 1 ELSE 0 END) AS received
     FROM message
     WHERE date/1000000000+978307200 > CAST(strftime('%s','now','-30 day') AS INTEGER)
     GROUP BY hr ORDER BY hr;"
   ```
   Look for: late-night peaks (anxiety vs creative-flow signal), morning silence (sleep debt), heavy-volume hours (work pattern).

2. **Pull top contacts last 30 days:**
   ```bash
   imsg contacts 15
   ```
   Note who's family, who's friends, who's work. The user's name resolution will happen automatically. Check that family is in the top 10 (relational health signal).

3. **Pull this-week calendar density:**
   ```bash
   cal week
   ```
   Look for: density (overcommitted vs sparse), date-night-ish events (relational health), travel, doctor appointments, deadlines.

4. **Pull reminders open count:**
   ```bash
   rem lists
   ```
   25+ open across all lists = overwhelm signal. 5 or less = healthy. Look at category mix.

5. **Pull recent personal mail (filter out marketing):**
   ```bash
   mail today 30
   ```
   Look for: bills/late notices (financial stress), health (medical/clinic), family (warmth), career (job alerts = passive job market scanning).

6. **Pull last 30 outgoing messages for tone scan:**
   ```bash
   imsg recent 60 --no-names | grep ' me:'
   ```
   Look for: positive markers (love, thanks, awesome), distress markers (tired, sorry, frustrated), formality vs warmth.

7. **Synthesize INTO ONE narrative.** Structure:
   - **Headline read** (one sentence: stable / building / strained / depleted / etc.)
   - **What's going well** (3-4 specific bullets with evidence)
   - **Patterns to watch** (gentle observations, NOT alarms)
   - **One concrete loose end** (the smallest actionable item)
   - **What you cannot see** (acknowledge limits: sleep quality, internal monologue, financial bottom line)

8. **Tone:** Like a friend who has access to the data. Not a therapist. Not a HR report. Specific quotes from threads beat abstract claims. Avoid platitudes. Avoid clinical language.

## Workflow: "Analyze my relationship with X"

When the user asks for a deep read on one relationship:

1. **Resolve the contact:**
   ```bash
   contacts find <name>
   ```
   Get the phone or email handle.

2. **Run the full analysis subcommand:**
   ```bash
   imsg analyze <handle>
   ```
   Outputs lifetime totals, monthly cadence, hour-of-day histogram, initiation balance, late-night percentage, average message length per side. JSON via `--json`.

3. **Sample messages from EACH inflection point:**
   Look at the monthly cadence. For every month where volume spiked or dropped, pull ~10-15 messages from that period:
   ```bash
   sqlite3 -readonly ~/Library/Messages/chat.db "
     SELECT m.ROWID, m.date, m.is_from_me, m.text, m.attributedBody
     FROM message m JOIN handle h ON h.ROWID=m.handle_id
     WHERE h.id LIKE '%<handle-substring>%'
       AND date(m.date/1000000000+978307200,'unixepoch','localtime')
           BETWEEN '<YYYY-MM-DD>' AND '<YYYY-MM-DD>'
     ORDER BY m.date ASC LIMIT 15;"
   ```
   You'll need to decode `attributedBody` blobs (use `~/bin/imsg from <handle>` for that, which decodes for you).

4. **Identify the ARCS:** Look for natural phases the data reveals:
   - Introduction phase (sparse, formal)
   - First intensification (something brought them together)
   - Drops (and what context surrounded them)
   - Resurgences (and what brought them back)
   - Current baseline

5. **Identify the STRENGTHS:**
   - Volume balance (50/50 = mutual; skewed = one carries it)
   - Initiation balance (who reaches first)
   - Hour overlap (do their patterns line up?)
   - Co-creative markers (are they BUILDING together vs just venting?)
   - In-jokes (signal of friendship that crossed into durable)
   - Average message length (who unloads more)

6. **Therapist-style read on how the user helps the OTHER person:**
   - What do they validate?
   - What identity do they reflect back?
   - When are they available?
   - Do they hype-amplify wins? Do they slow-question hard moments?
   - Where could they grow (without being preachy)?

7. **Acknowledge what data CAN and CAN'T show:** The thread doesn't show phone calls, in-person time, or what's been said out loud rather than typed. Surface that limit.

8. **Tone:** Honest, specific, warm. Use real quotes sparingly to anchor claims. Do not lecture.

## Workflow: "What's in my inbox today that matters?"

When the user asks for an inbox triage:

1. **Pull last-24-hour personal mail (filter out the marketing sea):**
   ```bash
   sqlite3 -readonly "$HOME/Library/Mail/V*/MailData/Envelope Index" "
     SELECT date(m.date_received,'unixepoch','localtime'), s.subject, a.address
     FROM messages m
     JOIN subjects s ON s.ROWID = m.subject
     JOIN addresses a ON a.ROWID = m.sender
     WHERE m.date_received > CAST(strftime('%s','now','-24 hour') AS INTEGER)
       AND a.address NOT LIKE '%noreply%'
       AND a.address NOT LIKE '%no-reply%'
       AND a.address NOT LIKE '%@e.%'
       AND a.address NOT LIKE '%@email.%'
       AND a.address NOT LIKE '%@news.%'
       AND s.subject NOT LIKE '%Google Alert%'
     ORDER BY m.date_received DESC;"
   ```
   Add the user's specific marketing-domain filters as you learn them.

2. **Resolve sender familiarity:** for each non-marketing sender, check if they're in Contacts:
   ```bash
   contacts lookup <sender-email>
   ```
   Known contact = personal mail. Unknown = transactional or new contact.

3. **Categorize:**
   - Family / friends (Contacts hits)
   - Work (employer domain or known coworkers)
   - Bills / financial (Stripe, bank domains, "payment", "invoice")
   - Health (clinic, doctor, prescription)
   - Receipts (Amazon, etc.)
   - Action-required (subjects with "?" or "please respond")

4. **Surface only what matters:** don't list everything. Top 5-10 items the user should actually look at, with one-line rationale per item.

## Workflow: "Send X to Y"

When the user asks you to send a message:

1. **GO READ `CONSENT.md` AGAIN.** No, really. This is the load-bearing rule.

2. **Look up the recipient:**
   ```bash
   contacts find <name>
   ```
   Get the handle. If multiple matches, ASK the user which one before drafting.

3. **Verify a prior conversation exists** (especially for SMS/RCS):
   ```bash
   sqlite3 -readonly ~/Library/Messages/chat.db "
     SELECT 1 FROM chat WHERE chat_identifier='<handle>' LIMIT 1;"
   ```
   If no prior chat, warn the user that the send may silently drop or open a new chat window.

4. **Draft the message.** Consider tone, length, and the user's editorial preferences (no dashes, etc.).

5. **DRY-RUN first, always:**
   ```bash
   imsg-send --to <handle> "<draft>"
   ```
   Show the user the dry-run output. Wait for explicit "yes" / "send" / "go" for THIS send.

6. **Only after explicit per-send authorization, transmit:**
   ```bash
   imsg-send --to <handle> --yes "<draft>"
   ```

7. **Verify delivery in chat.db:**
   ```bash
   sqlite3 -readonly ~/Library/Messages/chat.db "
     SELECT is_sent, is_delivered FROM message
     WHERE is_from_me=1 ORDER BY date DESC LIMIT 1;"
   ```
   Report `is_delivered=1` to the user. If 0, surface that the message went to Messages.app but hasn't confirmed delivery yet.

## Workflow: "Send an email to X via Y account"

Same shape as iMessage, but Mail-aware:

1. **List configured Mail accounts:**
   ```bash
   mail-send accounts
   ```

2. **Decide which account to send from.** If unclear, ASK. Default heuristic: personal recipient → personal account, work recipient → work account.

3. **Draft and DRY-RUN:**
   ```bash
   mail-send compose --from <account-hint> --to <email> --subject "..." --body "..."
   ```

4. **Wait for explicit authorization, then transmit with `--yes`.**

5. **Verify in Sent mailbox:**
   ```bash
   sqlite3 -readonly "$HOME/Library/Mail/V*/MailData/Envelope Index" "
     SELECT s.subject FROM messages m
     JOIN subjects s ON s.ROWID = m.subject
     ORDER BY m.date_sent DESC LIMIT 3;"
   ```

## Workflow: "Add a calendar event / reminder / note"

Internal-only writes (no other person sees them) do NOT need consent gating:

```bash
# Calendar event
cal add "Title" --at "tomorrow 3pm" --duration 60 --calendar "Personal" --yes

# Reminder
rem add "Pick up dry cleaning" --list "My List" --due "tomorrow 5pm" --yes

# New note
note new "Daily 2026-04-19" --folder "Personal" --body "<p>...</p>" --yes

# Append to existing note
note append "Daily 2026-04-19" --body "<p>more</p>" --yes
```

These still require `--yes` to actually run (vs dry-run), but you can run them after just confirming the user wants them. They don't communicate with anyone outside.

## Workflow: "What did I say about X?"

The user wants to recall an old conversation:

```bash
# Search across all messages (text + attributedBody)
imsg search "<keyword>"

# Search within one thread
imsg from <handle> 200 | grep -i "<keyword>"

# Search Notes by title
note find "<keyword>"

# Search Mail subjects
mail search "<keyword>"
```

Combine results across surfaces. The user's memory is on whichever surface they used. Help them find it without forcing them to know which app it lived in.

## Synthesis principles (apply to every workflow above)

1. **Be specific. Use evidence.** "You sent 1,613 messages with Bob in 30 days, more than your wife" beats "you talk to your friends a lot."

2. **Surface BOTH the data AND the interpretation.** Don't just report numbers. Don't just give vibes. Pair them.

3. **Avoid absolute claims.** "This looks like X" / "the data suggests Y" / "I'd watch for Z" beats "you are X" / "you must Y".

4. **Acknowledge what you cannot see.** Sleep quality, in-person time, internal monologue, financial bottom line, emotional weather. The data only shows what the user typed.

5. **Be a friend, not a system.** Warm, direct, occasionally honest about uncomfortable observations. Never preachy. Never clinical.

6. **Honor consent on every send.** Always.

7. **Save what you learn to memory.** When you discover that a particular contact is the user's wife, brother, best friend, boss — save that as a memory entry so you don't have to rediscover it next time. See `memory-init.md`.
