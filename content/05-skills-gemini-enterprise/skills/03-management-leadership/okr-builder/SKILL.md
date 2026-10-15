---
name: okr-builder
description: "Drafts OKRs for a team, store, department or project from strategy documents and the parent OKRs: 1-3 inspiring objectives, 2-4 measurable outcome key results each with baseline, target, data source and owner, a committed vs aspirational tag, an alignment map to the level above and an anti-pattern check (tasks disguised as KRs, sandbagging, unmeasurable targets). Use whenever someone sets quarterly, semester or yearly goals, cascades strategy to a team, or reviews draft OKRs, even if they say 'objectives' or 'priorities'. Triggers - write OKRs, set objectives, key results, quarterly goals, review my OKRs, cascade OKRs, rédiger nos OKR, définir les objectifs, résultats clés, objectifs du trimestre, fixer les objectifs de l'équipe, mes OKR sont-ils bons."
---

# OKR builder

Turns strategy into a few clear objectives and measurable key results that a team can own and track, and catches the
common mistakes before they are locked in.

## When to use
- A new quarter, semester or year starts and the team must set OKRs.
- A manager needs to cascade the level above (country, business unit, sport, store) into team OKRs.
- Draft OKRs exist and need a critical review.
- Not for: scoring progress during the period (use `okr-progress-review`), defining one KPI in depth (use
  `kpi-definition-card`), or a project's scope and milestones (use `project-charter`).

## Inputs
- Team or scope and the period (required).
- Strategy or parent OKRs (required; search Drive and Confluence before asking). If they cannot be read, say so in
  one line, ask the user to paste the 3–5 parent priorities, and still deliver the output with
  `[parent priority 1 — to confirm]` links, drafted objectives and `<baseline>` / `<target>` placeholders.
- Current baselines for candidate metrics (optional, default: pulled from Databricks/Tableau or marked "baseline
  to measure").
- Existing draft OKRs to review (optional).

## Sources
1. **Drive and Confluence**: the parent OKRs, strategy or plan documents for the period, last period's OKRs and their
   final scores, any internal OKR guide (follow its scale and rules if found, and cite it).
2. **Databricks (SQL MCP or Polco)**: baselines for candidate KRs — e.g. last 4 quarters of the metric at the right
   grain (store, sport, channel). Show the query or the Polco question used.
3. **Tableau**: existing dashboards that already track candidate metrics (prefer KRs that are already measured).
4. **Jira**: big initiatives planned for the period, to link KRs to the work that should move them.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Extract the **3–5 priorities** of the level above with citations. Every objective you draft must link to one of
   them, or be explicitly flagged as "team-specific".
2. Write **1–3 objectives**: qualitative, motivating, time-bound by the period, in plain words a store teammate
   would understand. Example: « Faire de notre rayon randonnée la référence locale du conseil ».
3. For each objective write **2–4 key results**: outcome metrics (a change in customer or business behavior), not
   activities. Formula: *from baseline X to target Y by date, measured in source Z*. Mix leading and lagging
   indicators, and add one counter-metric when a KR can be gamed (e.g. conversion up + return rate not up).
4. Tag each KR **committed** (expected 1.0) or **aspirational** (≈0.7 is a success), and say so explicitly.
5. List the **initiatives** (projects, Jira epics) under each KR, separate from the KRs.
6. Run the **anti-pattern check** on every line:
   - Task as KR ("launch the new display") → rewrite to the outcome it should cause.
   - No baseline or no data source → add one or mark "measure in week 1".
   - Binary KR (done/not done) → only acceptable if committed and truly binary.
   - Too many (> 3 objectives or > 4 KRs per objective) → cut.
   - Business-as-usual KR copied from a KPI with no ambition → raise or drop.
   - KR the team does not influence → move to "watch metrics".
7. Build the **alignment map** (parent priority → objective → KRs → owner) and list cross-team dependencies.

## Output format
```markdown
# OKRs — <Team>, <period>
_Parent strategy: <link(s)>. Scale: <internal scale if found, else 0.0–1.0, 0.7 = good for aspirational>._

## O1 — <objective> (links to: <parent priority>)
| KR | Baseline | Target | Source | Owner | Type |
|----|----------|--------|--------|-------|------|
| KR1.1 <metric from → to> | <value, date> | <value> | <table/dashboard> | <role> | committed / aspirational |
Counter-metric: … · Initiatives: <epic links>

## Alignment map
| Parent priority | Objective | KRs | Dependencies |
|-----------------|-----------|-----|--------------|

## Anti-pattern check
| Line | Issue | Fix applied |
|------|-------|-------------|

## Open points
- <baselines to measure, owners to confirm>
```

## Quality checks
- Each objective links to a cited parent priority or is flagged "team-specific".
- Every KR has a number, a baseline (or "measure in week 1"), a target, a source and a type.
- No KR is an activity; initiatives are listed separately.
- At most 3 objectives and 4 KRs per objective.
- Every baseline value comes from a query, a dashboard or the user, with the reference shown.

## Guardrails
- Never invent baselines or targets; when no data is found, use a placeholder like "<baseline>" and say where to get it.
- Do not make individual OKRs a disguised performance rating; if the user asks to tie OKRs to pay or rating, point
  them to the internal HR policy and HR.
- Do not publish OKRs in Confluence or create Jira epics without the user's confirmation.
