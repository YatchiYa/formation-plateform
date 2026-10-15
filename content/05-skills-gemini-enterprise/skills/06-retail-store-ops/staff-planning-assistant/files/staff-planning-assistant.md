---
name: staff-planning-assistant
description: "Drafts a store staffing proposal from traffic and ticket curves and the team's constraints: hour-by-hour need for the floor, checkouts, workshop and logistics tasks, coverage gaps against the current schedule, labor productivity, and a draft rota by role, with a checklist of labor-law and contract points for a human to verify. Use whenever a store or department manager builds or adjusts a schedule, prepares a peak week, or feels the team is in the wrong place at the wrong time, even if they only ask 'how many people do I need Saturday'. Triggers - staff planning, schedule, rota, staffing for Saturday, peak staffing, labor hours, planning équipe, planning magasin, combien de personnes samedi, besoin en effectif, courbe de fréquentation, heures travaillées, productivité horaire, renfort saisonnier, couverture des pics."
---

# Staff planning assistant

Helps a store manager put the right number of teammates in the right place at the right hour, as a draft that people
check and decide on.

## When to use
- Building next week's or next month's schedule, or a peak period (ski season Saturdays, back to school, sales).
- Conversion drops at peak hours and the manager suspects under-staffing on the floor or at checkout.
- Deciding how many seasonal reinforcements or extra hours to request, and when.
- Not for: legal answers on working time or contracts (use `hr-policy-qa`, then HR), the skills coverage of the team
  (use `team-skills-matrix`), the full plan of a seasonal operation (use `seasonal-operation-planner`), or onboarding
  seasonal hires (use `onboarding-plan-builder`).

## Inputs
- Store and period to plan (required).
- Available team: number of teammates per role or skill (floor by universe, checkout, workshop, logistics), contract
  hours, known absences and availability (required; ask once if not found). Names are optional; roles are enough.
- Opening hours and fixed tasks: deliveries (days, pallets), pre-opening replenishment, events (optional, default:
  from Calendar and mail).
- Service standard (optional, default: none assumed): for example visitors per floor teammate at peak, minimum people
  present at opening and closing. If the store has no standard, the skill derives a reference from the store's own data.

## Sources
1. **Databricks via Polco**: visitors and tickets per hour and weekday for the last 8 weeks and the same weeks N-1;
   labor hours per hour if they exist. Verify with **Databricks SQL MCP** after discovering the tables (`SHOW TABLES`,
   `DESCRIBE`); never assume column names; show the query.
2. **Tableau**: traffic-curve or staffing views if they exist, for official definitions.
3. **Drive and Confluence**: the current schedule export, the store's staffing rules, internal working-time guidance.
   Quote the rules found; never supply rules from memory.
4. **Calendar, Gmail, Chat**: deliveries, events, trainings, visits, absences already announced to the manager.
5. **Airtable**: workshop bookings or event registrations, if the store tracks them there.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Build the demand curve**: average visitors and tickets per hour and weekday over comparable weeks. Adjust for the
   period ahead with the N-1 ratio of the same weeks (seasonality) and known events. Show the method.
2. **Translate demand into need per role and hour**:
   - Floor: visitors per hour / service standard. Without a standard, use the store's own reference: the
     visitors-per-floor-teammate ratio observed in the hours with the best conversion (label it *derived estimate*).
   - Checkout: tickets per hour / tickets one checkout handles per hour (from data or the manager), plus queue buffer
     at peaks.
   - Workshop: bookings and walk-ins per slot × standard job times given by the workshop.
   - Logistics: pallets or parcels × minutes per unit, placed before opening or in low-traffic hours.
3. **Compare with the current schedule** if one is provided: hour-by-hour coverage = scheduled − need. Mark under
   coverage (red), over coverage (amber) and balanced. Typical traps: lunch breaks taken at the lunchtime peak, and
   reception scheduled during the Saturday afternoon peak. Always use the store's real curve, not a generic one.
4. **Draft the rota by role**, filling peaks first, then fixed tasks, then the remaining hours. Prefer moving tasks
   (reception, facing) to troughs over adding hours. Respect each contract's hours and stated availability.
5. **Compute productivity**: planned revenue per labor hour vs N-1 (if revenue forecast or N-1 exists) and the share
   of hours on the floor during peaks.
6. **List the human checks** (see the template). Do not state legal limits; list what to verify against local law,
   the collective agreement and internal rules.
7. Give 2–3 options when hours are short: shift a delivery, split a shift, request reinforcement on named slots.

## Output format
```markdown
# Staffing proposal — <store> — <period> (DRAFT for manager decision)
_Method: <weeks used, adjustment, service standard or derived estimate>_

## Demand vs coverage — <peak day>
| Hour | Visitors (exp.) | Tickets (exp.) | Need floor | Need checkout | Need workshop | Scheduled | Gap |
|------|-----------------|----------------|------------|---------------|---------------|-----------|-----|

## Weekly summary
| Day | Need (h) | Scheduled (h) | Gap (h) | Revenue per labor hour (plan) | Main issue |
|-----|----------|---------------|---------|-------------------------------|------------|

## Draft rota by role
| Role | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|------|-----|-----|-----|-----|-----|-----|-----|

## Options if hours are short
1. <option> — effect on coverage — trade-off

## To verify by a human before publishing
- [ ] Daily and weekly working-time limits, rest periods and breaks under local law and the collective agreement
- [ ] Contract hours, part-time rules, overtime or extra hours approval
- [ ] Sunday, night and public holiday rules
- [ ] Minors, apprentices, medical or accessibility restrictions (manager knowledge only, not stored here)
- [ ] Notice period for schedule changes
- [ ] Minimum presence and safety rules at opening and closing

_Data used: <Polco question, SQL, Tableau view, schedule file>_
```

## Quality checks
- The need per hour is computed from a stated method and data window, and the formula is visible.
- Every under-covered peak hour appears in the gap table.
- The draft rota never exceeds the contract hours or availability the user provided.
- The human-checks list is present and unchanged in substance, even if the user did not ask for it.
- Any derived service standard is labeled *estimate* with how it was derived.

## Guardrails
- Labor-law compliance is not guaranteed by this skill: the manager and HR validate every schedule before it is
  published. Never state a legal limit as fact unless quoted from a source found in Drive or Confluence.
- Task allocation to people is a human decision (high-risk under the EU AI Act). Work by role; if names are given,
  mark assignments as a draft and never use health, family situation or other personal criteria to place people.
- Do not store or repeat sensitive reasons for absence or restrictions.
- Draft only: no schedule is sent, published or changed in a tool without explicit confirmation.
