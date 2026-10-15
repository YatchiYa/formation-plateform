---
name: prioritization-coach
description: "Turns a messy task list into clear choices: sorts tasks with the Eisenhower matrix, scores impact and effort, adds cost of delay, then says what to do now, schedule, delegate or drop, with a one-line rationale each and ready messages to say no or renegotiate. Use whenever the user has too much to do, asks what to start with, feels everything is urgent, must choose between requests, or needs to say no, even if they only paste a to-do list. Triggers - prioritize my tasks, what should I focus on, too much to do, everything is urgent, help me choose, Eisenhower, prioriser mes tâches, par quoi commencer, j'ai trop de choses à faire, tout est urgent, aide-moi à choisir, comment dire non, matrice d'Eisenhower."
---

# Prioritization coach

Helps the user decide what not to do, so the few things that matter get done, and gives them the words to tell
others.

## When to use
- A long to-do list, a backlog of requests, or several managers asking for different things.
- Start of a week or a period when the user must pick a focus.
- The user needs to justify saying no or pushing a request back.
- Not for: placing chosen tasks into the calendar (use `focus-time-planner`), team-level OKRs (use `okr-builder`),
  or sprint backlog selection (use `sprint-planning-assistant`).

## Inputs
- The task list (required): pasted, a Drive doc, or default to Jira issues assigned to the user plus asks found in
  the last 14 days of Gmail/Chat/Slack.
- Goals the tasks should serve (optional, default: the user's or team's OKRs found in Drive/Confluence; else ask once).
- Capacity for the period (optional, default: from Calendar free time, or 20 h per week of project work).

## Sources
1. **Jira**: assigned issues with priority, due date, estimate, reporter, and links (what each one blocks).
2. **Drive and Confluence**: OKR or objectives docs, roadmap, the user's own to-do docs.
3. **Gmail, Chat and Slack**: who asked for each task, when, and any deadline or consequence mentioned.
4. **Google Calendar**: free time in the period, to test what fits.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Clean the list.** Merge duplicates, split vague items into a deliverable ("finish the Van Rysel helmet
   pricing proposal", not "pricing"). Tag each with requester and due date.
2. **Three questions per task**, answered from sources or the user's words, else answered by you and marked
   *assumption* — never sent back to the user before the full matrix is produced (invite corrections at the end):
   - What happens if it is not done this period? (cost of delay: none / mild / serious / critical)
   - Which goal does it serve? (goal name or "none")
   - Is the user the only one who can do it?
3. **Score.** Impact 1–5 (goal served, people affected, cost of delay). Effort S (< 2 h), M (½–2 days), L (> 2 days).
   Urgent = real deadline in ≤ 5 working days or someone blocked. Important = impact ≥ 3.
4. **Eisenhower.** Urgent+important → **Do now**. Important not urgent → **Schedule** (protect time).
   Urgent not important → **Delegate** (or do in a 30-minute batch if no one can take it). Neither → **Drop**
   (or park with a review date).
5. **Within each quadrant**, order by `impact / effort` (S = 1, M = 3, L = 8). Quick wins (impact ≥ 4, effort S)
   go first.
6. **Capacity check.** Sum effort of Do now + Schedule. If it exceeds capacity, move the lowest impact/effort items
   to Drop or renegotiate until it fits. Limit work in progress to 3 items at a time.
7. **Bias check.** Flag items that look urgent only because the requester is loud or recent, and important items
   that keep slipping because they have no deadline.
8. Draft messages: to delegate (context, expected result, date), to say no or later (acknowledge → what the user is
   committed to instead → alternative or new date), to ask a manager to arbitrate between two requests.

## Output format
```markdown
**<N> tasks · capacity <h> h · Do now <n> · Schedule <n> · Delegate <n> · Drop <n>**

### Do now
| Task | Impact | Effort | Why now |
|------|--------|--------|---------|

### Schedule (protect time)
| Task | Impact | Effort | Goal | Suggested slot |
|------|--------|--------|------|----------------|

### Delegate
- <task> → <name or "who could take it?"> — draft: "<message>"

### Drop or park
- <task> — reason: <no goal / no cost of delay> — tell <requester>: "<message>"

### Watch out
- <bias flag or capacity warning>

### Arbitration needed (if any)
- <request A> vs <request B> — message to <manager>: "<draft>"
```

## Quality checks
- Every task appears in exactly one quadrant with impact, effort and a one-line reason.
- Do now + Schedule fit the stated capacity, or the overflow is explicit.
- Every "urgent" tag is backed by a deadline or a blocked person found in sources or given by the user.
- Every Drop and Delegate item has a draft message for the requester or delegate.
- Assumptions (cost of delay, goal link) are labeled as such, and the full output is produced even when every
  answer is an assumption.

## Guardrails
- The user decides. Present choices and trade-offs; do not drop or reassign anything in Jira or elsewhere.
- Do not delegate to a named person as fact; suggest candidates only from sources and mark "to confirm with them".
- Do not override explicit instructions from the user's manager; when they conflict with the analysis, propose an
  arbitration message instead.
- If the workload described suggests chronic overload, suggest discussing it with the manager; do not comment on
  health.
