---
name: store-action-plan
description: "Turns store findings from performance reviews, visits, audits, incidents, customer feedback or team ideas into a focused action plan: problem statements, root cause, prioritization by impact and effort, SMART actions with owner roles and deadlines, a KPI and check method per action, follow-up rituals, and an optional tracker draft for Airtable or Jira. Use whenever a store or area manager has a list of problems or remarks and needs to decide what to do and who does what, or wants to follow up an existing plan, even if they only paste a messy list. Triggers - store action plan, action plan, follow-up plan, what do we do now, priorities for the store, plan d'action magasin, plan d'actions, suivi des actions, qui fait quoi, priorités magasin, plan de progrès, relevé de décisions, actions correctives."
---

# Store action plan

Converts a pile of findings into a short plan the store team can own, run and check, instead of a long list nobody
follows.

## When to use
- After a store visit, a performance review, a safety or quality audit, or a customer feedback review.
- The store has too many open topics and the manager needs to choose 5–7 priorities.
- An existing plan needs a progress review: what is done, late, or not working.
- Not for: producing the findings themselves (use `store-performance-analysis`, `store-visit-report`,
  `stock-availability-analysis` or `workshop-service-review`), a multi-month cross-functional project (use
  `project-plan-builder`), or a team retrospective (use `team-retrospective`).

## Inputs
- Findings (required): pasted notes, a report in Drive, a visit report, or an analysis from another skill.
- Store and plan horizon (optional, default: 6 weeks).
- Team roles available (optional, default: store manager, department managers, workshop lead, logistics lead).
- Existing tracker (optional, default: searched in Airtable, Jira or Drive).

## Sources
1. **Drive**: visit reports, analyses, audit results, previous action plans for this store.
2. **Airtable or Jira**: existing store action trackers, to avoid duplicates and reuse their fields.
3. **Databricks via Polco / Tableau**: baseline values for the KPIs attached to actions. Discover tables or views first,
   never assume column names, and cite the query or view.
4. **Gmail, Chat, Slack**: commitments already made to the region or the team about these topics.
5. **Calendar**: upcoming rituals (weekly store meeting, area manager visit) to anchor follow-up dates.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Cluster the findings** into problems. Write each as a problem statement with a fact: « Les tailles 42–44 des
   chaussures trail sont en rupture 3 samedis sur 4 » rather than « problème de stock ».
   Use only the facts given: if the findings carry no figure, keep the user's wording (« ruptures fréquentes ») with
   « [à mesurer] » — never add a percentage, duration or count, even as « ex: ». A root cause not in the findings is
   labeled *hypothesis*.
2. **Find the root cause** with 5 whys or a quick fishbone (people, method, stock, layout, tools, data). Stop at a
   cause the store can act on, or note that it must be escalated.
3. **Prioritize** with impact (customers, sales, safety, team) × effort (hours, cost, dependencies), each scored 1–3:
   - Safety issues first, regardless of score.
   - Quick wins (high impact, low effort): do this week.
   - Big bets (high impact, high effort): plan with milestones.
   - Low impact: park or drop, and say so.
   Keep 5–7 active actions; more than that rarely gets done in a store's operating rhythm.
4. **Write SMART actions**: verb + object + standard to reach, one owner role (one name per action, not a team), due
   date, KPI with baseline and target, and how it will be checked (data, floor check, photo).
5. **Escalations**: what needs the region, supply, IT or HQ, with the specific ask.
6. **Follow-up rituals**: where the plan is reviewed (weekly store meeting, huddle), who updates the tracker, when the
   KPI is rechecked.
7. **Progress review mode** (if a plan exists): status of each action (done, on track, late, blocked), KPI moved or
   not, and a decision for each: close, continue, change approach, escalate.
8. Draft the tracker rows (Airtable fields or Jira issues) only if the user wants them.

## Output format
```markdown
# Action plan — <store> — <date> → <horizon end>
**Focus:** <the 2–3 themes> · **Owner of the plan:** <role> · **Review:** <ritual, day>

## Priorities
| # | Problem (fact) | Root cause | Impact | Effort | Type |
|---|----------------|------------|--------|--------|------|

## Actions
| # | Action (verb + standard) | Owner (role) | Due | KPI: baseline → target | Check method | Status |
|---|--------------------------|--------------|-----|------------------------|--------------|--------|

## Escalations
| Topic | Ask | To whom (role) | By |
|-------|-----|----------------|----|

## Parked
- <finding> — why parked

## Follow-up
- <ritual, cadence, who updates what>

## Progress review (if existing plan)
| # | Action | Status | KPI moved? | Decision |
|---|--------|--------|------------|----------|

_Sources: <findings docs, data queries, tracker>_
```

## Quality checks
- Every action starts with a verb, has exactly one owner role, a date and a KPI with baseline (or « baseline to
  measure »).
- Active actions are ≤ 7; anything beyond is parked with a reason.
- Every safety finding is either an action or explicitly escalated, never parked.
- Each action traces back to a problem statement with a fact; every number in a problem statement appears in the
  findings or a cited query.
- Baselines cite their source; targets are the user's or labeled *proposal*.

## Guardrails
- No invented baselines, targets or deadlines from HQ; mark unknowns « to confirm ».
- Owners are roles; assign named people only if the user provides them, and never use the plan to judge individuals.
- Draft, don't act: creating Airtable records, Jira issues or sending the plan happens only after explicit confirmation.
- Keep HR, disciplinary and health matters out of the plan; route them to the manager privately.
