---
name: team-skills-matrix
description: "Builds a skills matrix for a team from the role framework and teammates' self-declared levels: a people-by-skills grid on a 0-4 scale, coverage per skill against the target, bus-factor and single-point-of-failure alerts, cross-training pairs and a prioritized training plan. Use whenever a manager plans training, staffs shifts or projects, prepares for absences or turnover, opens a new department or service, or wants to know who can cover what, even if they only ask 'who knows how to do X'. Triggers - skills matrix, competency matrix, who can cover, bus factor, cross-training, training needs, matrice de compétences, polyvalence, tableau de polyvalence, cartographie des compétences, besoins de formation, qui sait faire."
---

# Team skills matrix

Shows a manager, at a glance, which critical skills the team covers, where one absence would break the operation,
and which cross-training pairs fix it fastest.

## When to use
- Planning training for the season or the year.
- A store team before peak season (e.g. winter sports, back to school), a warehouse before a new flow, a tech team
  before an on-call rotation.
- A key teammate is leaving or going on long leave.
- Not for: one person's development plan (use `career-development-plan`), designing the training itself (use
  `learning-path-designer`), or the weekly staff schedule (use `staff-planning-assistant`).

## Inputs
- Team members (names or initials) and roles (required).
- Skill list: from the role framework, or the tasks the team must cover (required; searched in Drive/Confluence,
  otherwise the skill proposes 8–15 skills for validation).
- Self-declared levels from each teammate, ideally validated with the manager (required for the grid; the skill
  can produce the survey form first).
- Target coverage per skill (optional, default: ≥ 3 people at level ≥ 3 for critical skills, ≥ 2 for others).

## Sources
1. **Drive and Confluence**: role frameworks, task lists, training catalog, existing polyvalence or skills sheets.
2. **Drive (Sheets / Forms results)**: self-declared levels collected from teammates.
3. **Jira and GitHub** (tech): which components each person has recently worked on, as a *hint* to discuss,
   never as an automatic level.
4. **Calendar**: planned absences the user shares at team level, to test coverage on specific weeks.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Skill list** (8–15): mix of job skills and operational tasks, each with one-line definition and a
   criticality tag: *critical* (operation stops or is unsafe without it), *important*, *nice*.
   Store example: till and returns, customer advice per sport, receiving deliveries, workshop repair
   (e.g. bike servicing), opening/closing procedure, merchandising. Tech example: deploy to production, on-call
   for payment API, data pipeline X.
2. **Scale 0–4** with anchors: 0 = never done; 1 = has seen it; 2 = does it with help; 3 = autonomous;
   4 = can teach others. If no levels exist yet, produce a short self-assessment form with this scale.
3. **Grid**: people × skills. Levels are self-declared and labelled as such; mark manager-validated ones.
4. **Coverage per skill**: count people at ≥ 3. Compare with target. Status: ✅ meets target, 🟠 below,
   🔴 bus factor = 1 (only one person at ≥ 3) or 0.
5. **Peak/absence test**: for given weeks or shifts, recompute coverage without absent people (team-level only).
6. **Cross-training pairs**: for each 🔴/🟠 skill, pair a level-4 or 3 person with a level-1–2 person; prefer
   people who expressed interest. Estimate effort as *short* (shadowing a few shifts), *medium*, *long*.
7. **Training plan**: priority = criticality × gap. Each line: skill, who, method (shadowing, internal training,
   external), by when. Trainings only from the catalog or marked *to find*.

## Output format
```markdown
# Skills matrix — <team>, <date>
_Scale: 0 never · 1 seen · 2 with help · 3 autonomous · 4 teaches. Levels: self-declared (✓ = manager-validated)._
_Sources: <framework, survey>. Target: <rule>_

## Grid
| Skill (criticality) | <P1> | <P2> | <P3> | … | People ≥3 | Status |
|---------------------|------|------|------|---|-----------|--------|

## Risks
- 🔴 <Skill> — bus factor 1 (<person>) · impact: …
- 🟠 …

## Cross-training pairs
| Skill | Trainer | Learner | Effort | By |
|-------|---------|---------|--------|----|

## Training plan
| Priority | Skill | Who | Method | Source | By |
|----------|-------|-----|--------|--------|----|

## Coverage test (<week / shift>)
| Skill | Normal | With absences | Status |
```

## Quality checks
- Every critical skill has a coverage status and, if below target, an action.
- Every 🔴 skill has at least one cross-training pair.
- Levels are labelled self-declared unless validated; none is inferred from Jira/GitHub activity alone.
- Trainings have a catalog source or are marked *to find*.
- The grid has no column or comment beyond skills and levels (no performance or personal notes).

## Guardrails
- The matrix maps skills for planning and development. It must not be used to rate, rank or select people for
  promotion, dismissal or task allocation decisions without human review (EU AI Act high-risk areas).
- Absences appear only as "unavailable" for a period, never with the reason (leave, sickness, training).
- Do not infer skill levels from age, seniority or background; use declared or observed evidence.
- Keep the grid visible to the team and its manager only, unless the team agrees to share it more widely.
