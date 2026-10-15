---
name: promo-calendar-planner
description: "Plans a promotional and commercial calendar for a season or a year: sport seasonality peaks, sport events and school holidays, regulated sales periods, promo sequencing with cooling-off gaps, cannibalization and conflict checks, stock and margin guardrails, and a retro-planning per operation. Use whenever someone builds a promo plan, a commercial calendar, a seasonal activation plan, decides when to run an offer, or wonders if two promotions overlap, even if they only ask 'when should we do our next promo?'. Triggers - promo calendar, promotional plan, commercial calendar, trade calendar, when to run a promotion, Black Friday plan, calendrier promo, plan promotionnel, calendrier commercial, temps forts, planning des opérations, quand faire une promo."
---

# Promo calendar planner

Builds a calendar where every promotion has a reason, a sport moment, a stock plan and room to breathe, so that offers
create incremental sales instead of training customers to wait for discounts.

## When to use
- Building the commercial calendar for a season (winter sports, spring outdoor, back to school) or a year.
- Deciding when to run an offer, or checking whether a new promotion collides with existing ones.
- Aligning marketing, category, e-commerce and stores on the key moments ("temps forts").
- Not for: executing one operation in stores (use `seasonal-operation-planner`), briefing one campaign (use
  `campaign-brief`), a local store event (use `local-sport-event-planner`) or reading a past promo's results (use
  `marketing-performance-report`).

## Inputs
- Scope: market, channels (online, stores), categories or sports, period (required).
- Existing operations already committed (optional, default: searched in Drive, Airtable and Calendar).
- Business objectives: traffic, clearance, new customers, margin (optional, default: ask which one ranks first).
- Constraints: promo budget, margin floors, stock positions, legal sales dates for the country (optional, default:
  flagged *to confirm with legal*).

## Sources
1. **Drive and Confluence**: previous calendars and their post-mortems, commercial policy and promo rules, range
   plans and launch dates, country legal notes on sales periods.
2. **Databricks (SQL or Polco)**: weekly sales by category N-1 and N-2 (seasonality curve), promo vs non-promo weeks,
   stock and sell-through, margin rate. Show the queries used.
3. **Tableau**: commercial or category dashboards.
4. **Airtable and Calendar**: the current campaign tracker and the team's planning milestones.
5. **Gmail, Slack and Chat**: stakeholder requests and supplier or stock constraints.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Map demand** week by week: seasonality curve per category from N-1/N-2 data (for example ski equipment peaks
   before February school holidays, hiking tents from May to August, running in January and before spring races).
   Mark the source; if no data, mark the curve *assumption*.
2. **Map moments**: school holidays per zone, sport events (major marathons, Tour de France, ski season opening,
   football seasons), regulated sales periods, Black Friday, back to school. Dates come from sources or the user.
3. **Place operations on purpose**: each operation gets one objective (acquire, sell-in at the start of the season,
   clear end-of-season stock) and one mechanic (price cut, bundle, gift, loyalty points, service). Full price
   during the demand peak, promotions to pull demand forward or to clear at the end.
4. **Check conflicts and cannibalization**:
   - Overlapping offers on the same category or audience.
   - Promo depth vs frequency: fewer than ~4 weeks between two promos on the same category trains customers to wait
     (flag as a rule of thumb, not a law).
   - Pull-forward: a promo just before the peak shifts demand rather than adding it; check post-promo dips in N-1.
   - Halo and cannibalization across own brands and ranges (a tent promo vs the sleeping bag bundle).
5. **Guardrails per operation**: stock coverage for the promo weeks, margin floor, price-reduction display rule (EU
   Omnibus: the reference price is the lowest price of the previous 30 days).
6. **Retro-planning** per operation: brief, assets, stock allocation, price loading, store briefing, go-live, review.
7. **Measurement**: incremental sales vs a baseline (N-1 adjusted or a control group of stores), not raw promo sales.

## Output format
```markdown
# Promo calendar — <scope> · <period>
_Objectives: <ranked> · Sources: <links> · Assumptions: <one line>_

## Calendar
| Week | Demand (N-1 index) | Moment | Operation | Objective | Mechanic | Channels | Status |
|------|--------------------|--------|-----------|-----------|----------|----------|--------|

## Conflicts and risks
| Weeks | Issue (overlap / pull-forward / cannibalization / stock) | Recommendation |
|-------|----------------------------------------------------------|----------------|

## Operation sheets
### <Operation name> (<dates>)
- Objective / KPI / baseline: …
- Scope and mechanic: … · Margin floor: … · Stock coverage: …
- Retro-planning: <milestone – date – owner>

## Open decisions
- …
```

## Quality checks
- Every operation has one objective, one mechanic and one KPI with a baseline method.
- Every date (holidays, legal sales, events) cites a source or is marked *to confirm*.
- No two operations overlap on the same category and audience without a flagged decision.
- Demand indices cite the query or are labeled *assumption*.
- Each operation has a retro-planning that ends before go-live with a store and site readiness step.

## Guardrails
- Never invent discount levels, margins, stock or prices; leave placeholders for the category team.
- Price reductions must follow the local rules on reference prices and sales periods; flag doubts to legal.
- No fake scarcity or "last chance" claims for operations that will repeat.
- Green-themed operations (repair, second-hand, take-back) route their claims through `green-claim-checker`.
- Draft only: do not book slots in Airtable or Calendar until the user confirms.
