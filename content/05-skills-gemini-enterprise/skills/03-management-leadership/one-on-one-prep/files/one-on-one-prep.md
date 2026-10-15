---
name: one-on-one-prep
description: "Prepares a manager's 1:1 with a direct report: what changed since the last 1:1 (past notes in Drive, Jira, GitHub, Calendar, threads), open commitments on both sides, a prioritized agenda that leaves the report's topics first, coaching questions (GROW) and a running-notes block ready to paste. Use whenever a manager has a 1:1, check-in or point individuel coming up, wants to know what to discuss with someone, or feels their 1:1s have become status updates, even if they only say 'I see Marie tomorrow'. Triggers - prep my 1:1, one-on-one with, check-in with my report, what should I discuss with, coaching questions, préparer mon one-to-one, point individuel avec, entretien hebdo avec, préparer mon 1:1, de quoi parler avec mon coéquipier."
---

# One-on-one prep

Gives a manager a 5-minute read before a 1:1 so the meeting is about the teammate (growth, blockers, wellbeing,
feedback), not a status report that a dashboard could give.

## When to use
- A recurring or ad hoc 1:1 with a direct report is on the calendar today or tomorrow.
- The manager wants to restart 1:1s that have drifted into status updates.
- A teammate seems disengaged or overloaded and the manager wants a careful way in.
- Not for: a planned hard conversation about performance or behavior (use `difficult-conversation-prep`), writing a
  piece of feedback (use `feedback-sbi-writer`), the annual review (use `performance-review-writer`), or the
  teammate's own development plan (use `career-development-plan`).

## Inputs
- The direct report's name (required).
- Date of the 1:1 (optional, default: the next calendar event with that person).
- Running 1:1 notes doc (optional, default: search Drive for a doc whose title has both names or "1:1"/"one-to-one").
- Topics the manager already wants to raise (optional).

## Sources
1. **Calendar**: the next and the previous 1:1 with this person (date, duration, attached doc), and their calendar
   load this week (meeting hours, out-of-office) as an overload signal.
2. **Drive**: the shared 1:1 notes doc — last 2–3 entries, open action items, topics marked "next time"; goals or
   development plan docs shared with the manager.
3. **Jira**: issues assigned to the person, resolved since the last 1:1, blocked or overdue, and long-running ones
   (in progress > 10 working days).
4. **GitHub** (tech teams): PRs merged, PRs waiting for review > 3 days, reviews they gave.
5. **Gmail, Chat and Slack**: threads between the manager and the person since the last 1:1 with an open question,
   a promise made by the manager ("I'll check with…"), or visible recognition from others.
6. **Confluence**: pages the person authored or updated recently (contributions worth recognizing).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Set the window = since the previous 1:1 (max 30 days). State it at the top.
2. Build **What changed**: max 5 facts with links — shipped, unblocked, new responsibilities, absences coming.
   Work is context, not the agenda: do not list every ticket.
3. Build **Open loops** in two columns: what the manager owes (promises in notes and threads) and what the teammate
   owes. The manager's own unkept promises go first — closing them builds trust fastest.
4. Detect **signals** worth a gentle question, never a diagnosis: meeting load > 60 % of the week, blocked items
   > 5 days, several late-evening messages sent to the manager, recurring blocker in several 1:1s. Phrase them
   as observations ("I noticed several evening messages to me this week") — never as conclusions about the person.
5. Draft the **agenda** with the classic split: their topics first (≈50 %), then the manager's (≈30 %), then
   development or the future (≈20 %). If the notes doc has topics from the teammate, put them at the top verbatim.
6. Pick **3 coaching questions** fitted to the situation, using GROW:
   - Goal: "What would make this week a success for you?"
   - Reality: "What's taking more energy than it should?"
   - Options: "What have you already tried? What else could work?"
   - Will: "What's your next step, and what do you need from me?"
   Add one wellbeing question that is open and optional ("How are you doing, really — workload-wise?").
7. Pick **one piece of recognition** with a concrete example (from step 2), in SBI form if possible.
8. If the person has an absence soon, a review cycle, or a role change, add a one-line reminder.

## Output format
```markdown
**1:1 with <Name> · <date, time> · window: since <last 1:1 date>**

### In 30 seconds
<2 sentences: what is going well, what deserves attention>

### What changed
- <fact> ([link](…))

### Open loops
| I owe <Name> | <Name> owes |
|--------------|-------------|
| <promise> — since <date> | <item> — due <date> |

### Proposed agenda (<duration> min)
1. Their topics (~<n> min): <from notes doc, or "ask: what's on your mind?">
2. My topics (~<n> min): <max 2>
3. Growth / future (~<n> min): <one theme>

### Coaching questions
- …
- …
- …
- Wellbeing (optional): …

### Recognition to give
<specific example, Situation-Behavior-Impact>

### Notes block (paste into the 1:1 doc)
**<date>** — Topics: · Decisions: · Actions (owner, date): · Next time:
```

## Quality checks
- The agenda puts the teammate's topics first and has no more than 2 manager topics.
- Every fact in "What changed" and "Open loops" has a link or a named source.
- Signals are written as neutral observations with a question, with no label on the person (no "burned out",
  "demotivated").
- No more than 25 rows in total; readable in under 5 minutes.
- Coaching questions are open (cannot be answered with yes/no).

## Guardrails
- Do not surface health, family, union, salary or disciplinary details found in sources; if a thread looks
  sensitive, write "Confidential thread — open it yourself" instead of summarizing it.
- Activity signals (timestamps, commit counts) are prompts for a conversation, never a performance measure.
  Do not compare the person with teammates.
- Do not write into the shared 1:1 doc or send anything; the notes block is a draft for the manager.
- If signals suggest a serious wellbeing or safety issue, suggest involving HR or the occupational health service
  per local process (search Confluence for it) rather than handling it alone.
