---
name: new-manager-90-day-plan
description: "Builds a 30-60-90 day plan for a manager taking a new team, store, department or project: situation diagnosis (STARS - start-up, turnaround, accelerated growth, realignment, sustaining success), listening tour with stakeholder list and questions, first 1:1 guide, early-wins candidates, what not to change too early, learning goals and milestones per phase. Use whenever someone starts a new management role, is promoted to manager, takes over a store or team, or prepares their first weeks, even if they just say 'I start Monday as manager'. Triggers - 90 day plan, 30-60-90, new manager, first weeks as manager, taking over a team, onboarding as a leader, plan des 90 jours, nouveau manager, prise de poste, je reprends une équipe, je deviens directeur de magasin, mes premières semaines."
---

# New manager 90-day plan

Gives a new manager a structured first 90 days: listen before acting, diagnose the real situation, then secure a few
early wins that build credibility.

## When to use
- A teammate becomes a manager for the first time.
- An experienced manager takes over a new team, store, sport department, warehouse team or project.
- A manager is two weeks in and feels lost or pulled in every direction.
- Not for: onboarding an individual contributor (use `onboarding-plan-builder`), preparing a single 1:1 (use
  `one-on-one-prep`), or a full stakeholder engagement plan for a project (use `stakeholder-map`).

## Inputs
- New role, scope and team size (required).
- Start date (optional, default: next Monday).
- What the user knows of the situation: expectations from their manager, known issues (optional).
- Previous role (optional — helps spot the skills gap: e.g. top seller becoming department manager).
- When role, scope and team size are given, write the full plan now with the defaults (STARS labeled *assumption*)
  and state them in one line; do not ask for the optional items first.

## Sources
1. **Drive and Confluence**: the scope's strategy, OKRs, last reviews or audits, org charts, process docs, the
   predecessor's handover doc, internal manager onboarding guides (cite them if found).
2. **Databricks (SQL MCP or Polco) and Tableau**: the scope's key KPIs over 12–24 months (trend vs N-1, vs peers if
   available) to diagnose the situation from data, not impressions.
3. **Jira**: open epics, backlog size and age, blocked items (tech or project scopes).
4. **Gmail, Chat and Slack**: welcome threads, the manager's expectations email, recurring channels to join.
5. **Calendar**: existing rituals the team runs (huddles, weekly meetings, reviews) to attend before changing them.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Diagnose with STARS** (Watkins, *The First 90 Days*): pick the most likely situation from the data and inputs —
   start-up (new activity), turnaround (results falling), accelerated growth, realignment (decent results but a
   drift ahead), sustaining success (high performance to protect). Give the evidence and say how it changes the
   plan (turnaround = act faster; sustaining success = learn longer, change less).
2. **Expectations conversation**: draft 5 questions for the new manager's own manager — success at day 90, the 2–3
   priorities, what must not change, resources, how they want updates.
3. **Listening tour**: list stakeholders by group (team members, peers, own manager, internal customers and
   support functions, external partners such as local clubs or suppliers if relevant) with why each matters, and
   schedule all team 1:1s in the first 2 weeks. Give the 5 standard questions for each: What works well that we must
   keep? What is not working? What would you change first if you were me? What do you need from me? Who else should
   I listen to?
4. **Phase plan**:
   - Days 1–30 *Learn*: listen, attend existing rituals, work on the floor or in the tool with the team, map the
     processes, no structural changes.
   - Days 31–60 *Diagnose and decide*: share back what was heard (themes, not names), agree 2–3 priorities with
     the team and the manager, set team agreements and rituals.
   - Days 61–90 *Act*: deliver early wins, launch priority projects, set the team's OKRs or goals, first review.
5. **Early wins**: 3 candidates scored on visible impact, effort, and team support (1–3 each); prefer wins that
   remove a daily irritant for the team (e.g. a broken process, a missing tool), not personal showcase projects.
6. **Traps to avoid**: changing things before understanding them, staying the expert instead of the manager,
   criticizing the predecessor, promising what cannot be delivered, skipping 1:1s.
7. **Milestones and self-check** at day 30, 60, 90: what will be true, how the user will know.

## Output format
```markdown
# 90-day plan — <Name/role>, <scope> · starts <date>
**Situation (STARS):** <type> — evidence: … → implication: …

## First week
- [ ] <action> — <day>

## Conversation with my manager (questions)
1. …

## Listening tour
| Who (role) | Why they matter | When | Specific question |
|------------|-----------------|------|-------------------|

## Phase plan
| Phase | Goals | Key actions | Milestone (how I know) |
|-------|-------|-------------|------------------------|
| Days 1–30 Learn | | | |
| Days 31–60 Diagnose & decide | | | |
| Days 61–90 Act | | | |

## Early-win candidates
| Win | Impact | Effort | Team support | Score |
|-----|--------|--------|--------------|-------|

## Traps to avoid
- …

## My learning goals
- …
```

## Quality checks
- The STARS choice cites at least one data point or stated fact, or is labeled *assumption*.
- All team members are scheduled for a 1:1 within the first 14 days (by role if names are not given).
- Days 1–30 contain no structural change or reorganization.
- Every milestone is observable (a meeting held, a doc shared, a metric read), not "understand the team".
- KPIs quoted come with source and period.

## Guardrails
- Do not form opinions about individual team members from data or rumors; the plan collects facts through listening.
- Do not include salary, health or disciplinary information about inherited team members even if found.
- Do not invent internal programs, trainings or rituals; propose them as ideas or cite the doc where they exist.
- Do not send meeting invites or messages without the user's confirmation.
