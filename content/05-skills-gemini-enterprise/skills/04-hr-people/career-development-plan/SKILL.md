---
name: career-development-plan
description: "Builds an individual development plan with a teammate or for themselves: aspirations and target role, a gap analysis against the role framework, 3 development goals, 70-20-10 actions (on-the-job stretch, mentoring and exposure, training), milestones with dates, support needed and a review rhythm. Use whenever someone talks about their career, wants to grow into a new role (store manager, department leader, product, tech, logistics), prepares a development conversation or follows up a review, even if they only ask 'how do I get promoted'. Triggers - development plan, IDP, career plan, career path, how to grow, next role, plan de développement, PDI, plan de carrière, évolution professionnelle, projet professionnel, entretien de développement, mobilité interne."
---

# Career development plan

Turns an aspiration into a concrete plan with real stretch work, people to learn from and dated milestones, owned by
the teammate and supported by the manager.

## When to use
- After a review, to convert growth areas into actions.
- A teammate wants to move: from sport advisor to department leader, store to HQ, warehouse to supply planning,
  developer to tech lead.
- A manager prepares a career or development conversation.
- Not for: writing the review itself (use `performance-review-writer` or `self-assessment-coach`), a training
  program for a group (use `learning-path-designer`), or a team-wide skills view (use `team-skills-matrix`).

## Inputs
- Current role and target role or direction (required; if unknown, the skill runs the aspiration questions).
- Role framework or job description of the target role (optional, searched in Drive/Confluence).
- Last review's growth areas and strengths (optional).
- Time horizon (optional, default: 12 months, reviewed quarterly).
- Constraints the person chooses to share: mobility, working time (optional; never asked for reasons).

## Sources
1. **Confluence and Drive**: career or competency frameworks, job descriptions of the target role, internal
   mobility guides, training catalogs.
2. **Drive**: last review, self-assessment, previous development plan (with the user's access).
3. **Jira and GitHub** (tech/product): evidence of current skill level from recent work.
4. **Calendar**: existing rituals to reuse for stretch (huddles, project meetings), and the next 1:1s for check-ins.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Aspirations** (if not given), 4 questions: What energizes you in your work? What do you want more/less of?
   Where do you see yourself in 2–3 years? What would make the next 12 months a success?
2. **Gap analysis**: list the target role's 5–7 key competencies (internal wording if found). For each:
   current level and target level on the framework scale (or 1 = aware, 2 = practicing with help, 3 = autonomous,
   4 = teaches others), with one evidence line for the current level. Keep the 2–3 biggest gaps that matter
   most for the target.
3. **3 development goals**, SMART, each linked to a gap. Example: "By March, lead the Monday store huddle alone
   4 times and run the weekly department review with the manager's feedback."
4. **Actions with 70-20-10**:
   - **70 on-the-job**: stretch assignment, project, temporary responsibility, shadowing a role (e.g. covering the
     department leader during holidays, owning a seasonal operation, leading a small Jira epic).
   - **20 social**: mentor, peer group, feedback loop, an expert to meet (suggest `expert-finder` to identify one).
   - **10 formal**: trainings found in the catalog; never invent a course name.
5. **Milestones**: one per quarter, observable. Add the evidence that will show progress.
6. **Support and agreements**: what the manager provides (time, exposure, feedback), what the person commits to.
7. **Review rhythm**: monthly 10 min in 1:1, quarterly review of the plan.

## Output format
```markdown
# Development plan — <Name>, <current role> → <target>
_Horizon: <12 months>. Sources: <framework, review>. Assumptions: <one line>_

## Aspiration
<2–3 sentences in the person's words>

## Gap analysis
| Competency (target role) | Current | Target | Evidence for current | Priority |
|--------------------------|---------|--------|----------------------|----------|

## Goals
1. <SMART goal> — gap: …

## Actions (70-20-10)
| Goal | 70 on-the-job | 20 with others | 10 training | By |
|------|---------------|----------------|-------------|----|

## Milestones
| Quarter | Milestone | Evidence of progress |
|---------|-----------|----------------------|

## Support & commitments
- Manager: … · Me: …

## Check-ins
- Monthly in 1:1 · quarterly plan review on <dates>
```

## Quality checks
- Each goal maps to a named gap and has at least one 70% action.
- Every training listed has a catalog source or is marked *to find in catalog*.
- Milestones are observable and dated.
- The plan contains no promise of promotion, title, pay or mobility.
- The aspiration is in the person's words, not the manager's.

## Guardrails
- A development plan is not a promotion promise. Say so if the user frames it that way; promotion decisions follow
  the official process and are made by people.
- No assumptions based on age, gender, family situation, health or origin about what someone can or wants to do.
  Mobility and time constraints are recorded only as the person states them.
- Do not use other teammates' reviews or data as comparison.
- Draft only; the plan is agreed in a conversation between the teammate and the manager.
