---
name: seasonal-operation-planner
description: "Plans a store seasonal operation such as winter sports, back to school, spring cycling, summer outdoor, sales period or Black Friday: objectives from N-1 data, a retro-planning from J-90 to J+14, stock and implantation readiness, staffing and training needs, visual merchandising, services (workshop, rental, second-hand), local communication, risks and a debrief plan. Use whenever a store or area manager prepares a season peak or a commercial operation, even if they only ask 'when should we start preparing ski'. Triggers - seasonal operation, season launch, back to school plan, ski season prep, Black Friday plan, retro-planning, opération commerciale, lancement de saison, rentrée sportive, préparation saison ski, plan soldes, rétroplanning, temps fort, implantation saison, opé magasin."
---

# Seasonal operation planner

Builds a store-level plan for a season peak so that stock, team, layout and services are ready the day customers
arrive, not two weeks later.

## When to use
- Preparing a season peak: winter sports, back to school (running, team sports, swimming), spring cycling, summer
  outdoor, or a sales or Black Friday period.
- The N-1 operation went badly (stock-outs, queues at the workshop, late implantation) and the manager wants to do
  better.
- An area manager wants the same retro-planning across several stores.
- Not for: the company-wide promotional calendar (use `promo-calendar-planner`), the marketing campaign itself (use
  `campaign-brief`), a one-day community event (use `local-sport-event-planner`), or the hour-by-hour schedule (use
  `staff-planning-assistant`).

## Inputs
- Store(s), operation and dates (required), including the peak window (for example ski: first snow weekend to the end
  of the February school holidays).
- Objectives (optional, default: N-1 result + target if found).
- National or regional operation brief (optional, default: searched in Drive, Confluence and mail).
- Constraints (optional): surface, stock room capacity, team size, works, local competition.

## Sources
1. **Drive, Confluence, Gmail**: the operation brief from HQ or the region, implantation plans, visual merchandising
   guidelines, N-1 debrief, deadlines for orders or signage. Quote them; never invent a date or a rule.
2. **Databricks via Polco**: N-1 weekly sales, visitors, conversion, workshop and rental volumes and stock-outs over
   the same weeks, by sport universe. Verify with **Databricks SQL MCP** after discovering tables; never assume
   columns; show the queries.
3. **Tableau**: season or category dashboards for targets and official KPIs.
4. **Calendar**: school holiday dates and local events only if present in calendars or docs; otherwise ask.
5. **Airtable or Jira**: operation trackers, signage or works requests.
6. **Chat, Slack**: N-1 lessons shared by teams, supply alerts.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Learn from N-1**: weekly curve of revenue and visitors over the season (when did the peak start, how high, how
   long), the top 20 models, OOS rate in peak weeks, workshop backlog peak, staffing gaps mentioned in the debrief.
   Write the 3 lessons that change this year's plan.
2. **Objectives**: revenue and key KPIs per peak week (target if found, else N-1 + stated assumption), plus 1–2
   service KPIs (workshop turnaround, availability of top models).
3. **Retro-planning** from the opening date D (adapt timings to the brief found):
   | When | Stream | Typical milestones |
   |------|--------|--------------------|
   | D-90 to D-60 | Stock | range validated, pre-orders and allocations checked, stock room space freed |
   | D-60 to D-30 | Team | reinforcement needs, recruiting and onboarding, product trainings (boot fitting, bike sizing, ski prep) |
   | D-45 to D-21 | Services | workshop capacity, rental fleet checked, second-hand intake prepared |
   | D-30 to D-14 | Layout | implantation plan, hot zone and endcaps, signage ordered, mannequins and test areas |
   | D-14 to D-1 | Execution | receipts, implantation done, price checks, team briefing, dry run of the checkout and workshop flow |
   | D to D+14 | Run | daily KPI check, replenishment rhythm, staffing adjustment, quick fixes |
   | D+14 / end | Debrief | results vs objectives, lessons, actions for N+1 |
4. **Stock readiness**: expected weeks of cover at D for the top models vs the N-1 peak sales rate; size runs on
   footwear and boots; plan for replenishment frequency during the peak.
5. **Staffing and skills**: peak hours from N-1 traffic, number of reinforcement hours needed (rough estimate, refined
   with `staff-planning-assistant`), skills to train before D.
6. **Layout and visual merchandising**: the season universe in the hot zone, family-to-product logic (practice →
   equipment → accessories → services), price clarity, multi-sale bundles (skis + bindings + waxing).
7. **Local communication**: in-store signage, local partners or clubs, store social accounts if the store has them;
   align with the national campaign.
8. **Risks** (weather, supply delay, recruitment, IT) with mitigation and owner; then the debrief plan.

## Output format
```markdown
# <Operation> — <store> — <D date>
**Objective:** <headline KPI target> · **Peak window:** <dates> · **Owner:** <role>

## Lessons from N-1
1. <lesson + number + source>

## Objectives by week
| Week | Revenue obj. | N-1 | Visitors N-1 | Service KPI |
|------|--------------|-----|--------------|-------------|

## Retro-planning
| Date | Milestone | Stream | Owner (role) | Status |
|------|-----------|--------|--------------|--------|

## Readiness checklist
- [ ] Stock: <top models covered for x weeks at D>
- [ ] Team: <reinforcement hours, trainings>
- [ ] Services: <workshop / rental / second-hand>
- [ ] Layout: <implantation, signage>
- [ ] Communication: <local actions>

## Risks
| Risk | Likelihood | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|

## Debrief plan
<date, KPIs, who>

_Sources: <brief link, N-1 data queries, Tableau view>_
```

## Quality checks
- Every milestone has a date, an owner role and a stream; nothing important happens « at D ».
- Lessons from N-1 are backed by data or the N-1 debrief, or marked as the user's view.
- Objectives state whether they come from an official target or from N-1 + assumption.
- Stock readiness compares cover at D with the N-1 peak sales rate, not the average rate.
- Dates from HQ briefs are quoted with the link; no invented deadline.

## Guardrails
- No invented targets, budgets, order deadlines or HQ rules; mark them « to confirm ».
- Staffing numbers are estimates for planning; schedules and contracts follow `staff-planning-assistant` and human
  validation of labor-law points.
- Local communication using customer data must follow the company's consent rules; do not plan direct messaging to
  customers without that check.
- Draft only: no orders, signage requests, tickets or messages are created without the user's confirmation.

## Example
Input: « Prépare la saison ski du magasin d'Annecy, ouverture de l'univers mi-novembre »
→ French plan. Illustration: if N-1 data shows the peak started with the first snowfall weekend and the boot-fitting zone was the bottleneck
on Saturdays; milestones include boot-fitting training at D-30, ski-prep workshop capacity at D-21, rental fleet check
at D-21, implantation at D-10; risk « late snow » mitigated by keeping a cross-country and hiking offer visible.
