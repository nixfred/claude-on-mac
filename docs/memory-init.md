# Memory init: building user-context after install

> This file is for the AI agent installed on the user's Mac. It teaches the agent how to build up a useful memory of WHO the user is and WHO their people are, post-install. Compensates for not having a pre-loaded TELOS / personal-context file.

After the install protocol in `AGENTS.md` finishes, you (the agent) have data access but no relational context. You don't yet know which contact is the user's spouse vs their plumber. You don't know which folder in Notes is the daily journal. You don't know which Mail account is work vs personal.

This file walks you through building that context once, on first run, and saving it to memory so you don't have to redo it next session.

## Step 1: Discover the user's communication topology

```bash
# Top 20 conversation partners last 30 days (with names auto-resolved via Contacts)
imsg contacts 20

# Also: the same data in their inbox
mail domains 15
```

Note the names that show up. You now know WHO is in the user's life by signal (volume) but not yet by ROLE (family vs friend vs work).

## Step 2: Ask the user to classify their top contacts

Take the top 10-15 contacts from step 1 and ASK the user to label them:

> "I see your top conversation partners over the last 30 days are: <list>. Can you tell me who each of these people is to you? Spouse, family, close friend, work, service, other?"

Save the user's answers as a single memory entry. Format suggestion:

```
name: People in <user>'s inner circle
type: reference

- Alice Example: spouse
- Bob Example: brother (lives in Atlanta)
- Carol Example: best friend, met at a meetup in 2025
- Dave Example: business partner, Acme Corp
- Eve Example: oldest son
- Frank Example: youngest son
- ... (only the ones the user shared; respect what they don't name)
```

Do NOT ask about contacts the user hasn't named or doesn't seem close to. Don't snoop.

## Step 3: Learn the user's editorial preferences

Ask once, save the answers:

> "If I'm drafting messages on your behalf, are there any style rules I should know about? Punctuation preferences, words you'd never use, signature line, anything else?"

Save as a feedback memory:

```
name: <user>'s drafting style
type: feedback

- Stylistic preferences: ...
- Words / phrases to avoid: ...
- Signature: ...
- Default tone: ...
```

## Step 4: Learn the user's account aliases

```bash
mail-send accounts
imsg-send --list-self
```

Ask the user to confirm which account is which:

> "I see Mail is configured with <list of accounts>. Which is your personal? Which is work? Which would you prefer I default to for replies?"

Save:

```
name: <user>'s outbound account routing
type: reference

- Personal email: <addr> (account name in Mail.app: <name>)
- Work email: <addr>
- Default outgoing iMessage: <handle>
- Sending rule: never assume; ASK if a recipient straddles personal/work.
```

## Step 5: Learn the user's app conventions

Run a quick scan of structure:

```bash
note folders          # which Notes folders exist
rem lists             # which Reminders lists exist
cal calendars         # which Calendars exist
```

Then ASK the user:

> "I see your Notes folders are <X>, Reminders lists are <Y>, Calendars are <Z>. If I'm creating something for you, where should I put each kind of thing by default?"

Save the routing rules:

```
name: <user>'s default destinations
type: reference

- Personal note → folder "Personal"
- Daily journal-ish note → folder "Daily"
- Work reminders → list "Work"
- Personal reminders → list "My List"
- Time-sensitive events → calendar "Personal"
- ... (only what the user specifies)
```

## Step 6: Learn what NOT to touch

Equally important. Ask:

> "Are there any folders, lists, contacts, or threads you'd prefer I never read or write to, even if you ask me to do something that might pull them in by accident?"

Save as a hard rule (a feedback memory, because it shapes future behavior):

```
name: <user>'s do-not-touch zones
type: feedback

- Notes folders to skip: <list>
- Contacts to never message on user's behalf: <list>
- Calendars that are read-only conceptually: <list>
- Mail folders to skip: <list>
```

## Step 7: Save the consent rule reminder

This one you should save automatically without asking, because it's not the user's preference, it's a hard system rule:

```
name: send consent gate (hard rule)
type: feedback

Never send any iMessage, SMS, RCS, or email on the user's behalf without
explicit per-message authorization for that specific send. Auto modes do
NOT override. Pre-discussed plans do NOT override. Each send stands alone.
See claude-on-mac/CONSENT.md for the full rule.
```

## What the user does NOT have to share

The user is allowed to:
- Skip step 2 entirely (you'll learn relationships organically)
- Decline to label any specific contact
- Refuse to set defaults for some apps (you'll prompt at use-time instead)
- Opt out of certain capabilities entirely (in which case skip the related memory steps)

Honor every decline without pushback.

## When to refresh memory

These memory entries should be updated, not appended-to, when:

- The user mentions a relationship change (a divorce, a new baby, a deceased relative). Update the inner-circle list with a date and short note. Be respectful: "Bob: brother, deceased 2026-XX" not "Bob: brother, dead".
- The user gets a new email account or phone number. Update the account routing.
- The user moves a folder, renames a list, or otherwise restructures.
- The user gives you new editorial feedback ("from now on, no exclamation marks"). Update the drafting style memory immediately.

## Why this matters

The agent's quality of future help is bounded by the context it has. The user's TELOS file (the deep personal context) is private and intentionally not in the public repo. This memory-init protocol is how you build the FUNCTIONAL EQUIVALENT of that file from the data the user has already given you access to, with the user's consent guiding what gets recorded.

Done well, after one session you'll know enough to give the user the kind of synthesis that feels like a thoughtful friend, not a generic AI. Done badly, you'll keep asking "who is Bob?" every conversation.

Don't be that agent.
