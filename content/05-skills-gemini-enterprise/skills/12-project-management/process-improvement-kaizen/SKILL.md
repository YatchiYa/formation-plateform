---
name: process-improvement-kaizen
description: "Runs a Lean improvement of an operational or office process: SIPOC to frame it, current-state map with time and volume data, waste hunt with the 8 wastes (DOWNTIME), root-cause analysis with Ishikawa and 5 whys, future state, quick wins vs projects ranked by impact / effort, and a PDCA plan with before / after KPIs. Use whenever a process is slow, error-prone, costly or frustrating for teammates or customers, or someone prepares a kaizen workshop, even if they only say 'this takes too long' or 'there must be a better way'. Triggers - process improvement, kaizen, lean, waste, root cause, SIPOC, value stream, PDCA, streamline a process, amélioration continue, chantier kaizen, gaspillages, cause racine, optimiser un processus, simplifier une procédure."
---

# Process improvement (kaizen)

Helps a team see a process as it really runs, remove waste at its root and prove the gain with numbers, using the
Lean toolbox in the right order instead of jumping to solutions.

## When to use
- A process has long lead times, rework, errors or customer complaints (e.g. click-and-collect preparation, returns
  processing, supplier invoice approval, store reception, workshop repair turnaround).
- A team prepares a kaizen workshop or an improvement project.
- After an audit or incident shows a recurring failure.
- Not for: writing the standard once the new process is agreed (use `sop-writer`), a one-off incident analysis
  (use `incident-postmortem`), investigating a KPI drop in data (use `metric-anomaly-investigator`), or a full
  out-of-stock analysis (use `stock-availability-analysis`).

## Inputs
- Process name, boundaries (first and last step) and the problem felt (required).
- Data: volumes, lead times, error or rework rates, staff time (optional; searched in Databricks / Tableau; else
  marked *to measure*).
- Target or goal (optional, default: proposed from the gap, labeled *proposal*).

## Sources
1. **Databricks (SQL or Polco) and Tableau**: volumes per day, lead time distribution (median and 90th percentile,
   not only averages), error, return or rework rates. Show the query or the dashboard link.
2. **Drive and Confluence**: current procedures, process maps, audit reports, previous kaizen results.
3. **Jira**: tickets caused by the process (errors, requests, workarounds), with counts by category.
4. **Gmail, Chat, Slack and Meet transcripts**: recurring complaints, workarounds described by teammates, customer
   feedback forwarded.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Problem statement**: what, where, since when, how much (baseline), impact on customer or teammate. No cause or
   solution in the statement.
2. **SIPOC**: Suppliers, Inputs, Process (5–7 high-level steps), Outputs, Customers, plus the customer's critical
   requirement (CTQ) for each output.
3. **Current state**: list each step with actor, process time (hands-on work), waiting time, volume, error rate.
   Compute **lead time** = Σ (process + waiting) and **process cycle efficiency** = Σ process time / lead time.
   Flag each step as value-adding (customer would pay for it), necessary non-value-adding (legal, control), or
   waste.
4. **Waste hunt — DOWNTIME**: Defects, Overproduction, Waiting, Non-utilized talent, Transportation, Inventory,
   Motion, Extra-processing. For each step, name the waste with evidence (e.g. "Motion: preparer walks to the
   reserve 3 times per order").
5. **Root cause** for the top 2–3 problems: an **Ishikawa** (6M: Method, Machine, Material, Manpower → people and
   skills, Measurement, Milieu → environment), then **5 whys** on the most likely branch. Validate the cause with data
   where possible, otherwise label it *hypothesis to test*.
6. **Future state**: remove, combine, re-sequence, simplify, error-proof (poka-yoke), standardize. Show the new
   step list and the expected lead time (labeled *estimate*).
7. **Prioritize** improvements on an impact / effort grid: quick wins (high impact, low effort, < 30 days),
   projects, maybe later, drop.
8. **PDCA plan**: Plan (change, owner, KPI, target), Do (pilot scope, e.g. 2 stores, 4 weeks), Check (KPI before /
   after, same measure, same period length), Act (standardize via `sop-writer` or adjust).

## Output format
```markdown
# Kaizen — <Process> · <scope> · <date>
**Problem:** <what, where, how much, impact>
**Headline:** <lead time X → Y (*estimate*) by removing <top waste>; <N> quick wins>

## SIPOC
| Suppliers | Inputs | Process | Outputs | Customers | CTQ |
|-----------|--------|---------|---------|-----------|-----|

## Current state
| # | Step | Actor | Process time | Wait time | Volume | Error % | VA / NNVA / Waste |
|---|------|-------|--------------|-----------|--------|---------|-------------------|
Lead time: … · Process cycle efficiency: …% (Σ process / lead time)

## Wastes (DOWNTIME)
| Waste | Where | Evidence | Est. cost (time / errors) |
|-------|-------|----------|---------------------------|

## Root causes
- Ishikawa (6M) for <problem>: Method … · Machine … · Material … · Manpower … · Measurement … · Milieu …
- 5 whys: why 1 → … → why 5 = <actionable root cause> (*validated* / *hypothesis*)

## Future state
| # | Step | Change vs today | Expected time |
|---|------|-----------------|---------------|

## Improvement portfolio
| Improvement | Impact | Effort | Category | Owner | Due |
|-------------|--------|--------|----------|-------|-----|

## PDCA
| Plan | Do (pilot) | Check (KPI before → after) | Act |
|------|-----------|----------------------------|-----|
```

## Quality checks
- The problem statement contains a baseline number (or *to measure*) and no solution.
- Lead time equals the sum of the step times in the current-state table; efficiency is computed from them.
- Every waste cited has a concrete evidence line, and all 8 DOWNTIME categories were considered.
- Each root cause passes the "if we fix this, does the problem stop?" test and is marked validated or hypothesis.
- Each improvement has owner, due date and a KPI to check it; quick wins are ≤ 30 days.

## Guardrails
- Improve the process, never target people: no individual productivity ranking, no named teammate in waste lists.
- "Non-utilized talent" means ideas and skills the process ignores, not people to remove; headcount reductions are
  not a kaizen output and stay a management decision.
- Changes touching safety, labor rules or working time must be validated by the competent function before piloting.
- Do not invent volumes or times; estimates are labeled and the pilot measures the real effect.
- Draft only: no change to Jira, procedures or schedules without explicit confirmation.
