---
name: focus-time-planner
description: "Builds a realistic time-blocking plan for the day or the week from Google Calendar and the user's tasks: checks real capacity against estimates, places deep-work blocks where energy and gaps allow, protects buffers, and lists meetings to decline, shorten or delegate with ready-to-send messages. Use whenever the user has no time to do real work, wants to block focus time, asks how to fit their tasks into the week, or feels overbooked, even if they do not mention time blocking. Triggers - focus time, time blocking, plan my week, block time for, no time to work, too many meetings, bloquer du temps, planifier ma semaine, temps de concentration, trop de réunions, je n'ai pas le temps de travailler, organiser mon agenda."
---

# Focus time planner

Fits the work that matters into the calendar that exists, and makes the trade-offs explicit when it does not fit.

## When to use
- The week is full of meetings and the important work has no slot.
- The user has a list of tasks with deadlines and wants them placed in the calendar.
- The user wants to cut meeting load or set up recurring focus blocks.
- Not for: choosing which tasks matter (use `prioritization-coach` first), the Friday review (use `weekly-review`),
  or today's overview (use `daily-briefing`).

## Inputs
- Period (optional, default: the rest of the current week; "today" for a day plan).
- Tasks with estimates and deadlines (optional, default: Jira issues assigned and due in the period, plus the Big 3
  from the last weekly review in Drive; estimates asked in one grouped question if missing for top tasks).
- Working hours and preferences (optional, default: Calendar working hours; deep work in the morning; lunch kept).

## Sources
1. **Google Calendar**: events in the period with organizer, attendee count, the user's response, whether the user is
   optional, agenda presence, recurrence; working hours setting.
2. **Jira**: assigned issues with due dates, priority and estimates or story points.
3. **Drive**: last weekly review or task list; notes of recurring meetings (to check if they produce outcomes).
4. **Gmail, Chat and Slack**: deadlines promised by the user in the period.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Capacity.** `available = working hours − meetings − 15% overhead` (email, chat, transitions). Show it per day.
2. **Demand.** Sum task estimates × **1.3** (planning-fallacy correction). Tasks with no estimate default to 2 h.
3. **Fit test.** If demand > capacity, say by how many hours and go to step 6 before placing anything optional.
4. **Place blocks.** Deep work blocks of 90 minutes (min 60) in the longest gaps, mornings first unless the user says
   otherwise. One deep task per block. Deadline tasks are placed at least one working day before the deadline.
   Shallow work (email, approvals) is batched into 2 × 30 min per day. Keep a 15-minute buffer after meeting runs
   of 2 h or more.
5. **Protect.** Suggest one recurring focus block (e.g. Tuesday and Thursday 9:00–11:00) if the week has fewer than
   two blocks of 90 minutes.
6. **Meeting audit.** Score each meeting the user attends; 1 point each for: no agenda; user is optional; more than
   8 attendees and the user neither presents nor decides; recurring with no notes or actions in the last 4
   occurrences; overlaps a deadline block. **≥ 3 = decline candidate, 2 = shorten (60 → 45, 30 → 20) or send a
   delegate, ≤ 1 = keep.** Never mark meetings with the manager, a customer or an incident as decline.
7. Draft polite decline or shorten messages (one line of reason, offer async input).
8. If it still does not fit, list what to renegotiate (task, requester, new date proposal).

## Output format
```markdown
**<Period> · capacity <h> h · demand <h> h (×1.3) · <fits / short by h>**

### Plan
| Day | Block | Task / type | Why here |
|-----|-------|-------------|----------|
| Tue | 09:00–10:30 | <task> (deep) | longest gap, due Wed |
| Tue | 16:30–17:00 | email & approvals (shallow) | batch |

### Meetings to change
| Meeting | Score | Proposal | Message (draft) |
|---------|-------|----------|-----------------|
| <title, day> | 3 | decline | "<one-line draft>" |

### Doesn't fit — renegotiate
- <task> — ask <requester> for <new date> — draft: "<one line>"

### Recurring focus block (suggestion)
- <days, hours>
```

## Quality checks
- No proposed block overlaps an existing event, and none falls outside working hours.
- Every deadline task is placed at least one working day before its deadline, or listed under "Doesn't fit".
- Capacity and demand figures show their inputs, and the 1.3 factor is applied.
- Every meeting proposed for change has its score and the criteria that triggered it.
- No meeting with the manager, a customer or an active incident is proposed for decline.

## Guardrails
- Do not create events, decline or edit meetings, or send messages until the user confirms each change.
- Respect working hours, legal rest time and the right to disconnect: no blocks in the evening, weekends or
  holidays unless the user asks.
- Store teammates' schedules follow the store planning; do not propose changes to shifts here.
