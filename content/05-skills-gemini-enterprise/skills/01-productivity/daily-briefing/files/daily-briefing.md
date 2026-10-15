---
name: daily-briefing
description: "Builds a one-screen morning briefing from today's calendar, unread priority emails, Google Chat and Slack mentions, Jira issues assigned to the user and open GitHub review requests, with a ranked top-3 for the day and prep notes per meeting. Use whenever the user starts their day or asks what is on their plate, what they missed, or what to focus on today, even if they do not say 'briefing'. Triggers - morning brief, my day, what's on today, start my day, catch me up, mon briefing du matin, ma journée, qu'est-ce que j'ai aujourd'hui, quoi de neuf, par quoi je commence, résumé de ma journée."
---

# Daily briefing

Gives a Company teammate a one-screen view of their day: meetings, what needs a reply, what is due, and the three
things that matter most.

## When to use
- Start of the workday, or after a long meeting block ("what did I miss?").
- The user asks what to focus on today or what is urgent.
- Before a day of back-to-back meetings, to see which ones need preparation.
- Not for: a full week view (use `weekly-review`), deep inbox processing (use `inbox-triage`), or preparing one
  specific meeting (use `meeting-prep`).

## Inputs
- Date (optional, default: today in the user's time zone).
- Look-back window for messages (optional, default: since the end of the previous workday, max 72 h on Mondays).
- Focus areas or projects to weight higher (optional).

## Sources
1. **Google Calendar**: today's events, with attendees, description, attached docs, and whether the user organizes.
2. **Gmail**: unread or starred threads in the window, threads where the user is in To: and a question is
   addressed to them, and emails from their manager or direct reports.
3. **Google Chat and Slack**: direct messages and @mentions in the window that have no reply from the user yet.
4. **Jira**: issues assigned to the user that are due today or overdue, or set to Highest/High priority and updated in the window.
5. **GitHub**: pull requests where the user's review is requested, or their own PRs with new review comments.
6. **Drive**: docs shared with the user or commented on with a mention in the window.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Collect the items from each source above. Keep the title, sender or owner, timestamp and link.
2. Remove duplicates, so that one topic seen in email, chat and Jira becomes a single item with several links.
3. Classify each item:
   - **Reply needed**: a direct question or request to the user that has no answer yet.
   - **Due**: has a deadline today or is overdue.
   - **FYI**: useful context with no action.
4. Score the actionable items with `urgency (deadline ≤ today = 3, this week = 2, later = 1)` ×
   `importance (manager / customer / production incident / blocking others = 3, own project = 2, other = 1)`.
   Break ties by age, oldest first.
5. Choose the **Top 3** from the highest scores. Phrase each one as an action that starts with a verb.
6. For each meeting, add one prep line: its goal, if it can be inferred, the doc to read, and an open question
   linked to it from steps 1–3. Flag the meetings that have no agenda, and conflicts.
7. Find the free slots of 30 minutes or more and suggest which Top 3 item to place in each one.

## Output format
```markdown
**<Weekday DD Month> · <N> meetings · <N> replies waiting · <N> items due**

### Top 3 today
1. <Verb + object> — <why now> ([link](…))
2. …
3. …

### Agenda
| Time | Meeting | Prep |
|------|---------|------|
| 09:00–09:30 | <title> | <goal / doc to read / ⚠️ no agenda> |

### Replies waiting
- <Person> — <topic in ≤ 10 words> · <age> ([link](…))

### Due / overdue
- <Item> — due <date> · <source> ([link](…))

### FYI
- <one line each, max 5>

### Focus slots
- <HH:MM–HH:MM> → <Top-3 item>

_Sources checked: Calendar ✓ · Gmail ✓ · Chat ✓ · Slack ✗ (not connected) · Jira ✓ · GitHub ✓_
```

## Quality checks
- The whole briefing fits on one screen, with no more than 25 bullet or table rows in total.
- Every item has a link to its source. Nothing appears that has no source.
- Every Top 3 item starts with a verb and is something the user can do today.
- Meeting times are in the user's time zone, and conflicts are marked ⚠️.
- The "Sources checked" line lists every source and its real status.

## Guardrails
- Read only. Do not reply to, accept, decline or move anything unless the user asks, and then show the draft first.
- Do not quote sensitive content (HR cases, health, salary) in the briefing. Use a neutral line such as
  "Confidential HR thread from <sender>, open it to read".
