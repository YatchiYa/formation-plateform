---
name: onboarding-plan-builder
description: "Builds a complete onboarding plan for a new teammate in a store, warehouse, HQ or tech team: pre-boarding checklist before day 1, a day-by-day first week, 30-60-90 day goals, a buddy brief, mandatory and role trainings found in Drive or Confluence, an access and equipment checklist, and check-in rituals with the manager. Use whenever someone is joining, changing role, coming back from a long absence or being onboarded as a seasonal reinforcement, even if the user only asks for a welcome email. Triggers - onboarding plan, new hire, first week, 30-60-90, welcome plan, buddy, new joiner, plan d'intégration, parcours d'intégration, nouvel arrivant, accueil nouveau coéquipier, première semaine, onboarding."
---

# Onboarding plan builder

Gives the manager a ready-to-run plan so that a new teammate feels welcome on day 1, is safe and autonomous on the
job fast, and knows what success looks like at 30, 60 and 90 days.

## When to use
- A new teammate joins (permanent, fixed-term, seasonal, apprentice or intern).
- An internal move: new role, new store, from store to HQ or the reverse.
- Return after a long absence, when a light re-onboarding helps.
- Not for: the 90-day plan of a new *manager* about their team (use `new-manager-90-day-plan`), a full training
  program for many people (use `learning-path-designer`), or the outgoing person's handover (use
  `handover-before-leave`).

## Inputs
- Role (required). Team, location, context (store, warehouse, HQ, tech) and start date (optional, default: context
  inferred from the role, e.g. designer → HQ/tech; a relative date such as "in 2 weeks" converted from today;
  others as placeholders). Build the full plan now; do not ask for optional items first.
- Manager and buddy names (optional, default: placeholders; the skill proposes buddy criteria).
- Contract type and duration (optional; changes the plan's horizon: a 2-month seasonal contract gets a 30-day plan,
  not a 90-day plan).
- Job description or first-year outcomes (optional, searched in Drive).
- Known needs for accommodation or adjusted schedule (optional, only if the user shares them; never ask why).

## Sources
1. **Drive and Confluence**: the onboarding checklist or welcome booklet for the site or job family, mandatory
   trainings (safety, data protection, code of conduct), team pages, tool guides, the job description.
2. **Calendar**: the manager's and buddy's availability in the first two weeks, team rituals (huddles, stand-ups,
   weekly meetings) to invite the newcomer to.
3. **Jira and GitHub** (tech roles): good first issues, repo READMEs, on-call rules.
4. **Gmail and Chat**: the hiring thread, for the start date, agreed hours and anything promised to the newcomer.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Fix the horizon**: ≥ 6 months contract → 90 days; 1–6 months → 30 days; < 1 month → first 5 shifts.
2. **Pre-boarding (D-10 to D-1)** — the 4C model: *Compliance* (paperwork, mandatory trainings scheduled),
   *Clarification* (role, first-month goals), *Culture* (purpose "Move people through the wonders of sport",
   team rituals, sport practice in the team), *Connection* (buddy, people to meet). Checklist owners:
   manager, HR, IT, buddy.
3. **Access and equipment**: list per context, each with owner and due date (D-3 latest):
   - Store: badge or keys, uniform, till/handheld access, safety briefing, emergency exits and first-aid points.
   - Warehouse: safety induction before any floor work, PPE, equipment authorizations only after the required
     training (mark *to confirm with site safety*), shift pattern.
   - HQ/tech: laptop, accounts, Workspace groups, Jira/GitHub/Confluence spaces, data access requests.
4. **Week 1, day by day**: one meaningful task per day, shadowing before doing, no more than 50% of the time in
   trainings or meetings. Day 1 ends with a 15-min manager check-in ("What surprised you? What's missing?").
   Store example: Day 2 shadowing a teammate on the hiking department, Day 3 handling customer advice with the
   buddy nearby, Day 4 receiving a delivery.
5. **30-60-90 goals**: *Learn* (30) → *Contribute* (60) → *Own* (90). 2–3 goals per stage, each observable
   ("handles returns at the till alone", "merges a first PR to production", "leads the Monday huddle once").
6. **Buddy brief**: criteria (same team, ≥ 6 months tenure, volunteer, not the manager), role (daily 10-min check
   during week 1, then weekly), what the buddy is not (an evaluator).
7. **Check-in rituals**: Day 1, Day 5, Day 30, Day 60, Day 90; the last one includes feedback on the onboarding
   itself. Propose Calendar slots; do not book them.

## Output format
```markdown
# Onboarding plan — <First name>, <Role>, <Team/Site> · start <date>
_Horizon: <90 days / 30 days / 5 shifts>. Sources: <checklist, trainings, JD>. Assumptions: <one line>_

## Before day 1
| Task | Owner | Due | Status |
|------|-------|-----|--------|

## Access & equipment
| Item | Owner | Due |
|------|-------|-----|

## Week 1
| Day | Focus | Activities | With |
|-----|-------|------------|------|

## 30-60-90 goals
| Stage | Goals (observable) | Support |
|-------|-------------------|---------|
| 30 · Learn | … | … |

## Trainings
| Training | Mandatory? | Source | When |
|----------|-----------|--------|------|

## Buddy brief
<5–7 lines>

## Check-ins
- Day 1 · Day 5 · Day 30 · Day 60 · Day 90 — <proposed slots>

## Welcome message (draft)
<≤ 120 words, sent by the manager before day 1>
```

## Quality checks
- Every mandatory training listed has a source link; none is invented. If none was found, the section says so.
- Every checklist line has an owner and a date before or on the start date.
- Week 1 has at least one hands-on task per day and a Day 1 check-in.
- 30-60-90 goals are observable and fit the contract horizon.
- Safety induction precedes any warehouse floor or equipment activity.

## Guardrails
- Do not invent internal tools, trainings, policies or welcome kits; use placeholders or ask.
- Collect only the personal data needed. Accommodation needs stay between the newcomer, the manager and HR;
  do not write a medical reason in the plan.
- Onboarding goals support development; they are not an evaluation. Any trial-period decision is a human
  decision under local law.
- Draft only: do not send invites, create accounts or book meetings without the user's confirmation.
