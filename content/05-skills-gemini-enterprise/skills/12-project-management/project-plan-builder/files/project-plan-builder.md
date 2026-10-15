---
name: project-plan-builder
description: "Builds a project plan from a scope or charter: a deliverable-oriented WBS that respects the 100% rule, work packages with owners and duration estimates, milestones, dependencies (finish-to-start etc.), a forward / backward pass to find the critical path and float, and a timeline table ready for Google Sheets or Jira. Use whenever someone needs to plan a project, build a retro-planning, sequence tasks, estimate an end date or find what drives the deadline, even if they only ask for 'a timeline' or 'a Gantt'. Triggers - project plan, WBS, work breakdown, Gantt, timeline, critical path, retro-planning, schedule, planning projet, rétroplanning, découpage du projet, chemin critique, jalons, planning détaillé."
---

# Project plan builder

Turns a scope into a plan a team can execute: what has to be produced, in which order, by whom, and which chain of
tasks actually sets the end date.

## When to use
- After the charter is agreed, to build the baseline plan.
- A fixed date is imposed (season start, store opening, trade show) and a retro-planning is needed.
- The plan exists but nobody knows which tasks drive the deadline, or the date moved and the impact must be traced.
- Not for: the charter itself (use `project-charter`), seasonal store operations planning (use
  `seasonal-operation-planner`), sprint-level planning of a backlog (use `sprint-planning-assistant`), or the risk
  register (use `raid-log-builder`).

## Inputs
- Scope and deliverables, or the charter (required; search Drive and Confluence first).
- Start date or imposed end date (required).
- Team members or roles available, and known constraints (holidays, freeze periods, supplier lead times)
  (optional, default: estimates labeled as *to validate with owner*).
- Working calendar (optional, default: Monday–Friday, no public holidays assumed; say so).

## Sources
1. **Drive and Confluence**: charter, previous plans for similar projects (reuse real durations as reference,
   cited), templates, supplier lead-time documents.
2. **Jira**: existing epics, issues and their links ("blocks / is blocked by"), fix versions and dates, team
   velocity if the work is agile.
3. **Calendar**: fixed events (steering dates, peak trading periods, team absences visible in shared calendars).
4. **Gmail, Chat and Slack**: supplier or partner commitments on dates.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **WBS**: decompose the scope into deliverables (nouns), not activities, 2–3 levels deep. Apply the **100 % rule**:
   the children of each node add up to exactly 100 % of the parent's work, nothing outside scope is included, nothing
   in scope is missing. Include project management, testing, training, communication and hand-over to operations,
   the usual forgotten work.
2. Break leaves into **work packages** of roughly 8–80 hours of effort or ≤ 2 weeks of duration, each with a single
   owner and a "done" criterion.
3. **Estimate** durations: use sourced history first; else three-point estimates (optimistic O, most likely M,
   pessimistic P) with PERT expected = (O + 4M + P) / 6. Label every estimate as *estimate*.
4. **Dependencies**: finish-to-start by default; use start-to-start or finish-to-finish with lag where real (e.g.
   "training can start 5 days after configuration starts"). Mark external dependencies (supplier delivery, other
   team) and hard constraints (must finish before Black Friday freeze).
5. **Critical path**: forward pass (earliest start ES, earliest finish EF = ES + duration), backward pass (latest
   finish LF, latest start LS = LF − duration), **total float = LS − ES**. Tasks with the lowest float
   (0 when the end date is not imposed) form the critical path; show the chain and its total duration. With an imposed end date, negative float means the plan is infeasible:
   say so and give options (crash: add resources or overtime on critical tasks at extra cost; fast-track by
   overlapping tasks; cut scope; move the date).
   Compute it from the Schedule table, never by listing tasks in WBS order: the critical path duration = EF of the
   last task; the computed end date = start + that many working days in the stated calendar; tasks that can run in
   parallel (permits, storage prep, later zones overlapping earlier ones) are on the path only if their float is 0.
   Feasibility = imposed date − (computed end + buffer); « OK » only if that is ≥ 0.
6. Place **milestones** (zero-duration events) at gates: design validated, pilot live, go / no-go, go-live,
   hand-over. Add a buffer before the imposed date (suggest 10–15 % of critical path duration, labeled *proposal*).
7. Output a timeline table that can be pasted into Google Sheets (one row per task, ISO dates) and list the Jira
   epics / issues that would be created if the user wants them.

## Output format
```markdown
# Project plan — <Project> · baseline <v1> · <date>
**End date:** <date> (critical path <N> working days, buffer <N> days) · **Calendar:** <assumption>
**Critical path:** 1.1 → 1.3 → 2.2 → 3.1 → M4
**Feasibility:** <OK / negative float of N days → options>

## WBS
- 1 <Deliverable>
  - 1.1 <Work package> — owner, done when …
- 2 …

## Schedule
| ID | Task / milestone | Owner | Duration (d) | Predecessors | ES | EF | LS | LF | Float | Critical |
|----|------------------|-------|--------------|--------------|----|----|----|----|-------|----------|

## Milestones
| Milestone | Date | Gate criterion |
|-----------|------|----------------|

## External dependencies and constraints
- <dependency> — need-by <date> — if late: <impact on end date>

## Assumptions to validate
- <estimate / calendar / resource assumption> — with <owner>
```

## Quality checks
- WBS passes the 100 % rule: every scope item appears once, nothing out of scope appears, PM / test / training /
  hand-over are present.
- For every row EF = ES + duration and float = LS − ES; critical tasks have the lowest float (0 unless the end date is
  imposed) and form a continuous chain from start to end.
- Every task has one owner and every milestone a verifiable criterion.
- Every duration is either sourced or labeled *estimate*; PERT formula shown where used.
- With an imposed date, feasibility is stated explicitly, with options if float is negative.
- The header end date, critical path days and buffer match the Schedule table (last EF, sum of chain durations),
  and the buffer is > 0 or its absence is flagged as a risk.

## Guardrails
- Do not present estimates as commitments; owners validate their durations.
- Never assume people's availability, holidays or contract hours; use shared calendars or ask.
- Draft only: do not create Jira issues, change dates or send the plan without explicit confirmation of the final
  version.

## Example
Input: « Rétroplanning pour l'ouverture d'un atelier vélo dans le magasin de Lyon le 1er mars »
→ Output in French. WBS: 1 Local aménagé, 2 Équipement et outillage, 3 Équipe formée, 4 Offre et prix de service
affichés, 5 Outils de prise de rendez-vous, 6 Communication locale, 7 Pilotage projet. Critical path through
« commande de l'outillage (délai fournisseur 6 semaines, *estimate*) → installation → formation ». Negative float
of 4 days → options: commande anticipée, formation en parallèle de l'installation, ouverture partielle.
