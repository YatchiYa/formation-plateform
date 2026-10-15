---
name: lessons-learned
description: "Produces a project lessons-learned report at a phase end or project close: objectives achieved vs planned (scope, time, cost, outcome KPIs), what worked to repeat, what did not with its root cause, and actionable recommendations owned by a process or a team, plus a facilitation guide for the review session and a reusable summary for future projects. Use whenever a project ends, a phase closes, a go-live has happened or someone wants to capitalize on experience, even if they only say 'let's do a debrief'. Triggers - lessons learned, project retrospective, post-project review, project closure, close-out report, after action review, retour d'expérience, REX, bilan de projet, clôture projet, capitalisation, leçons apprises."
---

# Lessons learned

Turns the end of a project into knowledge the next project will actually use: measured results, causes rather than
symptoms, and recommendations that change a template, a checklist or a habit.

## When to use
- Project closure or the end of a major phase (pilot, roll-out wave, season).
- After a go-live, an important supplier launch or a major event, good or bad.
- A sponsor asks for a closure report, or a new similar project starts and wants past lessons.
- Not for: a sprint or team retro (use `team-retrospective`), a production incident analysis (use
  `incident-postmortem`), or documenting a single decision (use `knowledge-capture-page`).

## Inputs
- Project name and period (required).
- Baseline: charter, plan, budget, KPIs (optional; searched in Drive and Confluence).
- Input from the team: retro notes, survey answers or a session to prepare (optional, default: the skill also
  produces the session guide).

## Sources
1. **Drive and Confluence**: charter (objectives, tolerances), baseline and final plan, status reports, steering
   minutes, RAID log, change requests, retro notes, previous lessons-learned pages (to check whether known lessons
   were applied).
2. **Jira**: planned vs delivered scope, cycle times, re-opened issues, items added after baseline.
3. **Databricks or Tableau**: outcome KPIs vs targets (e.g. adoption, sales uplift in pilot stores), with source.
4. **Gmail, Chat, Slack and Meet transcripts in Drive**: escalations, key decisions and turning points.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Build the **results scorecard**: each SMART objective baseline → target → actual; schedule (baseline vs actual
   end, slip); cost (budget vs actual, only sourced); scope (planned vs delivered, added, dropped).
2. Reconstruct a **timeline** of 6–10 turning points (decisions, changes, incidents) from status reports and
   minutes; it anchors the discussion on facts.
3. If a session is needed, provide a **facilitation guide** (60–90 min): set safety ("we look at the system, not at
   people"), timeline walk-through, silent writing, cluster, vote, root cause on the top 3 items, action design.
   Formats: Start / Stop / Continue or the 4Ls (Liked, Learned, Lacked, Longed for).
4. Cluster inputs into themes: scope and requirements, planning and estimates, governance and decisions,
   stakeholders and communication, suppliers and partners, people and skills, tools and data, change and adoption.
5. For each "did not work" theme, find the root cause with **5 whys** (stop at a cause the organization can act on)
   and separate symptom ("late delivery") from cause ("no supplier capacity check before committing to the date").
6. Write **recommendations** as: "For <type of project>, <do X> at <moment>, because <evidence>", each with an owner
   (process, template or team, not a person to blame) and a vehicle: update a template, add a checklist item, change a
   gate criterion, train. Max 7, prioritized by impact.
7. Check **previous lessons**: which past recommendations were applied, which were ignored and recurred.
8. Produce a 5-line **reusable summary** for a Confluence lessons library, with tags (project type, domain).

## Output format
```markdown
# Lessons learned — <Project> · <period>
**In one line:** <did it deliver its purpose, and the single most important lesson>

## Results vs plan
| Dimension | Planned | Actual | Gap | Source |
|-----------|---------|--------|-----|--------|
| Objective 1 | | | | |
| End date | | | | |
| Cost | | | | |
| Scope | | | | |

## Timeline of turning points
- <date> — <event> → <consequence>

## What worked (repeat)
- <practice> — evidence: …

## What did not work (fix)
| Theme | Symptom | Root cause (5 whys) | Evidence |
|-------|---------|---------------------|----------|

## Recommendations
| # | Recommendation (for … do … at … because …) | Owner (process / team) | Vehicle | Priority |
|---|--------------------------------------------|------------------------|---------|----------|

## Previous lessons — applied?
- <lesson from project X> — applied / not applied → <effect>

## Library summary (5 lines, tags: …)
```

## Quality checks
- Every result row has planned and actual values with a source, or is marked *not measured*.
- Each "did not work" item has a root cause that is not a restatement of the symptom.
- Each recommendation is specific, owned by a process or team and has a vehicle; none is "communicate better".
- "What worked" is not empty; balance successes and failures.
- No sentence attributes failure to a named individual.

## Guardrails
- Blameless: describe systems, decisions and conditions, never personal fault; remove names from criticism.
- Anonymize team survey or retro quotes; do not report individual performance or HR matters.
- Do not invent KPIs, costs or dates; missing data is stated as a lesson in itself ("outcome KPI was never
  measured").
- Draft only: do not publish to Confluence or share with the wider organization without explicit confirmation.
