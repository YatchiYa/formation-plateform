---
name: weekly-review
description: "Runs an end-of-week review: what got done (Jira, GitHub, Calendar, Drive), what slipped and why, what carries over, and a plan for next week with a Big 3, a calendar health check and the focus blocks to protect. Use whenever the user wraps up their week, prepares Monday, asks what they achieved or what is coming next week, or needs material for a weekly update to their manager, even if they do not say 'review'. Triggers - weekly review, wrap up my week, what did I do this week, plan next week, Friday review, week recap, bilan de la semaine, revue hebdo, ma semaine, préparer la semaine prochaine, qu'est-ce que j'ai fait cette semaine, planifier lundi."
---

# Weekly review

Closes the week with an honest record of what was delivered and what slipped, and opens the next one with three
committed outcomes and a calendar that can actually hold them.

## When to use
- Friday afternoon or Monday morning, to close one week and set up the next.
- The user needs facts for a weekly update to a manager or a team ritual.
- The user feels busy but cannot say what moved forward.
- Not for: today only (use `daily-briefing`), sorting a long task list (use `prioritization-coach`), placing tasks
  into time blocks in detail (use `focus-time-planner`), or a project RAG report (use `project-status-report`).

## Inputs
- Week to review (optional, default: the current ISO week, Monday 00:00 to now).
- Last week's plan or Big 3 (optional, default: search Drive for the previous weekly review, else skip the
  planned-vs-done ratio and say so).
- Goals or OKRs to weigh against (optional, default: search Drive/Confluence for the user's team OKRs).

## Sources
1. **Jira**: issues the user resolved this week (`assignee = currentUser() AND resolved >= startOfWeek()`), issues
   that moved status, and open issues assigned to the user with a due date before the end of next week.
2. **GitHub**: PRs the user merged, reviewed or opened this week; PRs still waiting for their review.
3. **Google Calendar**: this week's events (to count meeting load) and next week's events, with attendees and docs.
4. **Drive**: docs the user created or edited this week; last week's review doc; team OKR doc.
5. **Gmail, Chat and Slack**: threads where the user committed to something with a date this week or next week.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Get clear (done).** List deliverables, not activity. Merge a Jira issue, its PR and its doc into one line.
   Keep only items with an outcome (shipped, decided, sent, validated). Tag each with the goal or OKR it serves, or
   "unaligned".
2. **Planned vs done.** If last week's plan exists, compute `done / planned` on the Big 3 and on all planned
   items. Below 50% two weeks in a row means the plan is too big or the week is too interrupted. Say which.
3. **Slip analysis.** For every planned item not done, assign one cause: *underestimated*, *interrupted*
   (unplanned work took the time), *blocked* (waiting on someone; name the dependency), *deprioritized* (a
   conscious choice) or *avoided* (no blocker, not started). Count causes; the dominant one drives next week's fix.
4. **Carry-over rule.** An item that slipped twice is not carried over silently. Propose one of: break it down
   (first step ≤ 2 h), renegotiate the date with the requester, delegate, or drop it.
5. **Measure the week.** Meeting hours / working hours (flag above 60%), the longest uninterrupted block, and
   unplanned work found in step 3.
6. **Next week's Big 3.** Pick three outcomes (not tasks) that are due, tied to a goal, or unblock others. Phrase
   them as "<deliverable> <state> by <day>", e.g. "Kalenji trail-shoe range review sent to the buyer by Thursday".
7. **Calendar check for next week.** Flag: double bookings; deadlines with no work time before them; meetings with
   no agenda that the user organizes; days with no 90-minute block; recurring meetings that clash with a Big 3.
   Propose focus blocks for each Big 3 item (draft only).
8. Write two short lines the user can paste in a manager update: highlight and help needed.

## Output format
```markdown
**Week <ISO week> · <N> deliverables · planned vs done <x/y> · meetings <h>h (<pct>%)**

### Done
| Deliverable | Goal / OKR | Evidence |
|-------------|-----------|----------|
| <outcome> | <goal or "unaligned"> | [Jira](…) · [PR](…) · [doc](…) |

### Slipped
| Item | Cause | Proposal |
|------|-------|----------|
| <item> | blocked by <who/what> | <break down / renegotiate / delegate / drop> |
Dominant cause: <cause> → fix for next week: <one sentence>

### Carry-over
- <item> — first step: <≤ 2 h action>

### Next week — Big 3
1. <deliverable> <state> by <day> — why: <due / goal / unblocks>
2. …
3. …

### Calendar check
- ⚠️ <issue> — <proposed change>
- Proposed focus blocks: <Day HH:MM–HH:MM> → <Big 3 item>

### For your manager update
- Highlight: <one line>
- Help needed: <one line or "none">

_Sources checked: Jira ✓ · GitHub ✓ · Calendar ✓ · Drive ✓ · Gmail ✓ · Chat ✓ · Slack ✗ (not connected)_
```

## Quality checks
- Every "Done" line is an outcome with at least one source link; no line describes only activity ("worked on…").
- Every slipped item has exactly one cause from the list and one proposal.
- No item slipped twice is carried over without a break-down, renegotiation, delegation or drop.
- The Big 3 are outcomes with a day, and each one has a focus block or a flagged reason why not.
- Meeting load and planned-vs-done figures show how they were computed, or say they are unavailable.

## Guardrails
- Read only. Creating focus blocks, declining meetings or messaging requesters happens only after confirmation.
- The review is for the user. Do not judge colleagues; name a blocker as a dependency, not a person's failing.
- Leave out confidential items (HR cases, health, salary) except as a neutral line such as "confidential HR topic".
