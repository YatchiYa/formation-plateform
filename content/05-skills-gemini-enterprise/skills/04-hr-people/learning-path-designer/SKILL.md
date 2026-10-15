---
name: learning-path-designer
description: "Designs a training program or learning path for a group of teammates: needs analysis, learning objectives written with Bloom's verbs, modules sequenced from basics to practice, blended formats (on-the-job, e-learning, workshop, peer coaching) sized for store, warehouse, HQ or tech constraints, an assessment and Kirkpatrick 4-level evaluation plan, and a rollout timeline. Use whenever someone must train a team, launch a new process or tool, upskill a job family, build a training for a new store or season, or improve a course that does not work, even if they only ask for 'a training deck'. Triggers - learning path, training program, design a training, curriculum, upskilling, course outline, parcours de formation, programme de formation, concevoir une formation, plan de formation, montée en compétences, module de formation."
---

# Learning path designer

Designs training that changes what people do on the job, not just what they hear, and states how that change will
be measured.

## When to use
- A new tool, process or product range must be learned by many teammates (e.g. a new checkout flow, a new
  warehouse flow, a new sport department).
- A job family needs upskilling (e.g. sport advisors on technical advice, managers on feedback, developers on a
  new platform).
- An existing training gets poor results and needs a redesign.
- Not for: one person's development plan (use `career-development-plan`), finding who needs which skill (use
  `team-skills-matrix`), a one-off workshop agenda (use `workshop-designer`), or writing an operating procedure
  (use `sop-writer`).

## Inputs
- Audience: role, number of people, sites, current level (required).
- Business goal: what must change on the job and how it shows (required).
- Constraints: time available per person, shift patterns, languages, budget, deadline (optional, default: asked
  in one grouped question if they drive the design).
- Existing materials, internal training catalog, subject-matter experts (optional, searched in Drive/Confluence).

## Sources
1. **Drive and Confluence**: existing trainings, SOPs, product or process documentation, training catalog,
   competency framework.
2. **Jira and GitHub** (tech): docs, READMEs, frequent support tickets that reveal knowledge gaps.
3. **Databricks / Tableau**: operational KPIs the training should move (e.g. return rate errors, picking errors,
   incident counts), at team or site level.
4. **Calendar**: busy periods to avoid for rollout (e.g. store peak seasons) and trainers' availability.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Needs analysis**: is training the right answer? Check the three causes of a performance gap: *knowledge or
   skill* (training helps), *environment* (tools, process, time — training does not help), *motivation*.
   State which applies; recommend non-training fixes where relevant.
2. **Objectives** with Bloom's verbs at the right level, observable and measurable: Remember/Understand
   (list, explain) for foundations, Apply/Analyze (perform, diagnose) for job skills, Evaluate/Create for experts.
   Example: "Diagnose the right ski boot size from a foot measurement and a practice level, without help, for 5
   customers in a row." Max 5 objectives.
3. **Modules**: sequence from foundations to practice. For each: objective(s), content outline, format, duration,
   material source. Format rules of thumb:
   - Store and warehouse teams: micro-modules ≤ 15 min that fit a shift, practice on the floor with a buddy,
     visual job aids at the workstation.
   - HQ: 60–90 min live sessions max, cohort-based, with work between sessions.
   - Tech: hands-on labs in a sandbox, code reviews as learning loops.
   Keep ≥ 50% of the time on practice.
4. **Assessment** aligned to objectives: practical observation checklist for Apply-level objectives, short quiz
   only for Remember/Understand.
5. **Evaluation (Kirkpatrick)**: L1 reaction (short survey), L2 learning (assessment), L3 behavior on the job at
   30–60 days (observation by manager or KPI proxy), L4 results (the business KPI, compared with a baseline).
   Name the data source for each level.
6. **Rollout**: pilot with one site or team, adjust, then scale; trainers or champions; timeline avoiding peaks;
   accessibility and translation needs.
7. List gaps: content to create, experts to involve, budget items to confirm.

## Output format
```markdown
# Learning path — <topic>, for <audience>
_Goal on the job: <one sentence>. Sources: <docs>. Assumptions: <one line>_

## Is training the answer?
<knowledge / environment / motivation — 2–3 lines, with non-training fixes if any>

## Objectives
1. <Bloom verb + task + condition + standard>

## Modules
| # | Module | Objective | Format | Duration | Material (source / to create) |
|---|--------|-----------|--------|----------|-------------------------------|

## Assessment
| Objective | Method | Pass criterion |
|-----------|--------|----------------|

## Evaluation plan (Kirkpatrick)
| Level | What we measure | How / source | When |
|-------|-----------------|--------------|------|

## Rollout
| Phase | Scope | Dates | Owner |
|-------|-------|-------|-------|

## To create or confirm
- …
```

## Quality checks
- Every objective starts with a Bloom verb and is observable; none says "understand" alone for a job skill.
- Each module maps to at least one objective, and each objective is assessed.
- Practice time is ≥ 50% of total time, or the deviation is justified.
- Each Kirkpatrick level has a named data source and timing.
- Existing materials are cited; anything not found is listed under "To create".

## Guardrails
- Never invent internal courses, platforms, certifications or budgets; cite or mark as to create/confirm.
- Mandatory safety or regulatory trainings (e.g. equipment handling in warehouses) must follow the official
  content and certified trainers; this skill can structure, not replace, them.
- Assessment results serve learning. They must not be used alone to decide on a person's job, pay or contract;
  people decide, with other evidence.
- Accessibility: provide alternatives (captions, printable aids, languages) and keep accommodation requests
  confidential.
