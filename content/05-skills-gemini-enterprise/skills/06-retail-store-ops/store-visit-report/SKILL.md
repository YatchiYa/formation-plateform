---
name: store-visit-report
description: "Prepares and writes a store visit report for an area, regional or store manager: a pre-visit data pack, a customer-path checklist (outside, entrance, sport universes, checkout, workshop, stock room, safety, team), then a structured report with strengths, gaps rated by impact, photos referenced, and an action plan with owners and dates, plus a follow-up email draft. Use whenever someone prepares, does or writes up a store visit, tour or audit, even if they only paste raw notes from their phone. Triggers - store visit, visit report, store tour, store audit, area manager visit, compte rendu de visite magasin, visite magasin, tour de magasin, rapport de visite, check-list visite, visite du directeur régional, audit magasin, CR visite."
---

# Store visit report

Makes a store visit useful: arrive with the right numbers, look at the store through the customer's eyes, and leave
with an agreed action plan rather than a list of remarks.

## When to use
- Before a visit: prepare the data pack and the checklist.
- During or right after a visit: turn raw notes, voice-memo transcripts or photo captions into a clear report.
- Visits by area or regional managers, store managers walking their own store, or peer visits between stores.
- Not for: the numbers analysis alone (use `store-performance-analysis`), a safety or theft event (use
  `store-incident-report`), or managing the follow-up of many actions across visits (use `store-action-plan`).

## Inputs
- Store, date and visitor role (required).
- Raw notes, checklist answers or a Meet/voice transcript in Drive (required for the report; not needed for prep).
- Visit focus (optional, default: full tour), for example ski readiness, back to school, workshop, safety.
- Previous visit report (optional, default: searched in Drive).
- If the user gives notes, write the full report now: "this morning"/"ce matin" means today's date, companions
  default to "none stated", focus to full tour, and the data pack and last-visit actions show [not available]. Never
  ask for optional items before drafting; list any open point under the report.

## Sources
1. **Drive**: previous visit reports for this store, the internal visit checklist or standards if one exists (use it
   instead of the generic one below and cite it), photos and notes uploaded by the user.
2. **Databricks via Polco / Tableau**: for the pre-visit pack: last 4 weeks revenue, visitors, conversion, basket vs
   N-1 and target, top gaps by sport universe, availability of top sellers. Discover tables or views first; never
   assume column names; show what was queried.
3. **Airtable or Jira**: open actions from the last visit and their status.
4. **Gmail, Chat, Slack**: recent topics with the store (incidents, works, staffing, customer complaints).
5. **Calendar**: the visit slot and attendees.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Pre-visit pack** (if before the visit): 5 KPIs with trend, the 3 biggest gaps by universe, last visit's open
   actions, 3 hypotheses to check on the floor (« transfo en baisse le samedi : vérifier présence en rayon ski et
   attente en caisse »).
2. **Checklist, following the customer path** (use the internal checklist if found):
   - Outside and entrance: signage, cleanliness, entrance offer matching the season, opening hours displayed.
   - Sport universes: seasonal universe in the hot zone, implantation respected, shelves full on top sellers, size
     runs complete, price labels correct and visible, endcaps on season priorities, services (workshop, rental,
     second-hand) visible where relevant.
   - Customer service: greeting, teammates available in the busiest universes, advice quality, try-on/test areas.
   - Checkout: queue length at peak, open lanes vs traffic, self-checkout support.
   - Workshop: waiting time, backlog, promised dates displayed or kept.
   - Stock room and reception: flow, pallets waiting, safety of storage at height.
   - Safety: fire exits and extinguishers free, aisle clutter, ladder use, first aid kit, incident register.
   - Team: atmosphere, rituals, training needs, questions raised by teammates.
3. **Rate each observation**: strength, minor gap, major gap (affects sales, safety or customer trust). Safety gaps
   are always major and are fixed the same day when possible.
4. **Link to numbers**: tie each major gap to a KPI from the pack (a broken size run in running shoes ↔ the running
   universe at -12%).
5. **Action plan**: max 7 actions, owner role, due date, how it will be checked. Agree them with the store manager
   rather than impose; mark "to agree" if not yet discussed.
6. **Follow-up email draft** to the store manager: thanks, 3 strengths, 3 priorities, the plan, next check date.

## Output format
```markdown
# Store visit — <store> — <date>
**Visitor:** <role> · **With:** <roles> · **Focus:** <focus>
**In one line:** <overall impression + top priority>

## Context (data pack)
| KPI (last 4 weeks) | Value | Δ N-1 | Δ target |
|--------------------|-------|-------|----------|
- Open actions from last visit: <n done / n open>

## Observations
| Area | Observation | Rating | Evidence (photo / data) |
|------|-------------|--------|-------------------------|

## Strengths
- …

## Priorities
1. <gap> → <impact, linked KPI>

## Action plan
| # | Action | Owner (role) | Due | How we check | Status |
|---|--------|--------------|-----|--------------|--------|

## Next visit / check-in
<date and what will be reviewed>

---
**Follow-up email (draft)**
Subject: <…>
<body ≤ 150 words>
```

## Quality checks
- Every rated observation comes from the user's notes or photos; nothing is added that was not observed.
- Every major gap has an action, and every safety gap is rated major.
- Every strength listed traces to the notes or photos; no strength is invented to balance the report.
- KPIs in the pack cite their source, and the last visit's actions are reconciled.
- The action plan has ≤ 7 lines, each with owner role, date and a check method.

## Guardrails
- Report on the store and processes, not on named individuals; no judgment of a teammate's personality or competence
  in the report (route individual feedback to a private conversation).
- No customer faces, names or identifying details in photos referenced or notes.
- Do not invent internal standards or scores; use the internal checklist only when it is found and cited.
- Draft only: the email and any tracker updates are sent or saved only after the user confirms.
