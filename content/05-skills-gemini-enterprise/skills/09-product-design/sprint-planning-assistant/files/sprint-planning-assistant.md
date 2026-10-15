---
name: sprint-planning-assistant
description: "Prepares a Scrum sprint planning from the Jira backlog: capacity from availability (absences, ceremonies, run and support load) and past velocity, a proposed sprint goal, a selection of ready stories that fits the forecast, readiness gaps, dependencies and risks, and the questions for the team. Drafts only, never moves Jira issues without confirmation. Use whenever a product owner, Scrum master or team lead prepares a sprint, checks if a sprint is overloaded, or needs a sprint goal, even if they just ask 'what can we take next sprint'. Triggers - sprint planning, plan next sprint, sprint capacity, velocity, sprint goal, sprint backlog, planification de sprint, préparer le sprint, capacité de l'équipe, vélocité, objectif de sprint, que prendre dans le prochain sprint."
---

# Sprint planning assistant

Gives the team a realistic starting point for sprint planning: how much it can take based on real availability and
past velocity, a goal that makes the sprint coherent, and a ready-to-discuss selection. The team still decides.

## When to use
- Before a sprint planning meeting, to prepare capacity, goal and candidate stories.
- During planning, to check whether the selection fits capacity.
- Mid-sprint, to check whether scope added since day 1 still fits.
- Not for: writing or splitting stories (use `user-story-writer`), cleaning the backlog (use `backlog-grooming`),
  the daily standup summary (use `engineering-standup-summary`) or the sprint retrospective (use `team-retrospective`).

## Inputs
- Jira board or project and the sprint (required).
- Sprint length and dates (optional, default: read from Jira).
- Availability per member: absences, part time, on-call or support duty (optional, default: Calendar
  out-of-office events plus the user's input; ask in one grouped question if unknown).
- Priorities or a product goal from the product owner (optional, default: backlog rank order and the roadmap).
- Jira not connected: do not ask for a board name or access. Compute capacity now from what the user gave (default
  10-day sprint, *to confirm*: 5 devs × 10 − 3 days = 47 of 50, ratio 0.94), fill the Output format with
  [to confirm] where velocity and backlog go, and ask in one question to paste the ranked backlog (key, summary,
  points) and the last 3 sprints' completed points.

## Sources
1. **Jira**: sprint reports of the last 3–5 closed sprints (committed versus completed points), ranked backlog,
   issue status, estimates, ready flags or labels, blockers and links, carry-over from the current sprint.
2. **Calendar**: team members' out-of-office and holidays during the sprint, recurring ceremonies, public holidays.
3. **Confluence and Drive**: definition of ready and done, roadmap, release dates, team working agreements.
4. **GitHub**: open PRs that will spill over, if the team tracks code work there.
5. **Slack and Chat**: dependency or support requests from other teams.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Velocity**: take completed points of the last 3–5 sprints; give the average and the range (min–max). Exclude
   anomalies (team change, sprint cut short) and say so. With fewer than 3 sprints, flag low confidence.
2. **Capacity** in person-days:
   `available days = Σ(member sprint days − absences − public holidays)`, then subtract ceremonies (planning,
   review, retro, refinement) and run or support load. `capacity ratio = available days this sprint ÷ available days
   in a typical sprint`. Forecast = average velocity × capacity ratio, shown as a range using min and average velocity.
   Example: 6 people × 10 days = 60; minus 7 absence days = 53; typical sprint 57 → ratio 0.93; average velocity 40
   (range 34–44) → forecast about 32–37 points.
3. **Carry-over**: deduct remaining work of unfinished items that roll over, re-estimated by the team if needed.
4. **Sprint goal**: one sentence on the outcome, not a list ("Customers can book a bike repair slot online in
   pilot stores"). Derived from the top of the backlog and the roadmap Now items; propose 2 options if priorities compete.
5. **Select**: take ranked, ready items that serve the goal until about 80 % of the forecast's low end, then add
   stretch items explicitly marked as such. Keep room for unplanned work if history shows it.
6. **Check readiness and risks** for each selected item: acceptance criteria present, estimate present, design and
   dependencies resolved, no blocker; skills concentration (one person on the critical path), external dependencies
   with dates.
7. **Prepare questions** for the planning meeting: items needing a decision, splits, estimates to revisit.
8. **Offer Jira changes** (move to sprint, set goal) as a list and apply nothing before explicit confirmation.

## Output format
```markdown
# Sprint planning — <team>, Sprint <n> (<start>–<end>)
_Sources: <board link>, <sprint reports>, Calendar · Assumptions: <one line>_

## Proposed sprint goal
<one sentence> (alternative: <…>)

## Capacity
| Item | Value |
|------|-------|
| Velocity last <n> sprints | avg <x> (range <min>–<max>) |
| Available person-days | <x> of <typical> (ratio <r>) |
| Carry-over | <x> pts |
| **Forecast** | **<low>–<high> pts** |

Availability notes: <absences, holidays, support duty, without personal reasons>

## Proposed selection (<total> pts committed, <total> pts stretch)
| Rank | Key | Summary | Pts | Serves goal | Ready? | Risk / dependency |
|------|-----|---------|-----|-------------|--------|-------------------|

## Not ready / excluded
- <key> — <reason and what is missing>

## Risks
- …

## Questions for the team
- …

## Jira changes to apply after confirmation
- Move <keys> to Sprint <n> · Set sprint goal
```

## Quality checks
- The capacity math is shown step by step and its numbers trace to Jira, Calendar or the user.
- Committed points do not exceed the low end of the forecast; stretch items are labelled.
- Every selected item is ready or its gap is stated.
- The sprint goal is one outcome sentence and most committed items serve it.
- No Jira change has been applied; the last section lists them for confirmation.

## Guardrails
- Show availability as days only; never mention reasons for absence (health, family, leave type).
- Velocity is a team planning tool, never a measure of individual performance; do not compute or compare points
  per person.
- Do not assign estimates or owners on the team's behalf; propose and let the team decide.
- Draft, don't act: move issues, change sprints or set goals in Jira only after explicit confirmation.
