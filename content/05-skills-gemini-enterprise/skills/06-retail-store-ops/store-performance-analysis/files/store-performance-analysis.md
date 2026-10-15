---
name: store-performance-analysis
description: "Produces a weekly, monthly or seasonal store performance deep dive: like-for-like revenue vs N-1 and target, the traffic × conversion × average basket decomposition, the split by sport universe and by hour or weekday, labor productivity, availability and margin signals, the root causes and a short list of actions with expected impact. Use whenever a store, area or regional manager needs to explain results, prepare a business review, or understand why a store is behind or ahead, even if they only ask 'why are we down'. Triggers - store performance, weekly store review, monthly business review, why are sales down, like for like, store deep dive, analyse performance magasin, revue hebdo magasin, pourquoi le CA baisse, comparable N-1, décomposition fréquentation transfo panier, bilan du mois magasin, revue d'activité."
---

# Store performance analysis

Explains a store's results over a period, separates the real drivers from noise, and ends with a few actions a
store team can actually run.

## When to use
- Weekly or monthly store review, or a business review with the area or regional manager.
- Sales are behind N-1 or target and the manager needs to understand why before acting.
- Comparing a store with its peer group or with the region.
- End of a season (ski, back to school running, summer cycling) to learn what worked.
- Not for: yesterday's numbers before opening (use `store-daily-brief`), one sport universe in depth (use
  `sport-universe-review`), stock-outs and overstock (use `stock-availability-analysis`), a generic data question
  outside store ops (use `data-question-answerer`), or turning findings into an owned plan (use `store-action-plan`).

## Inputs
- Store(s) (required) and period (required, for example week 41, September, or the ski season Nov–Feb).
- Comparison base (optional, default: N-1 weekday-aligned, plus target if available).
- Peer group (optional, default: stores of the same region or format if they can be identified in the data).
- Known events (optional): works, closures, local competitor opening, weather, staffing shortage, promotions.

## Sources
1. **Databricks via Polco**: ask for the store's revenue, visitors, tickets, units, margin and labor hours by
   week/day/hour and by sport universe for both periods. Then verify with **Databricks SQL MCP**: discover tables
   first (list schemas, `SHOW TABLES`, `DESCRIBE`), check the grain (ticket line, ticket, day) and never assume a
   column name. Keep the final queries for the appendix.
2. **Tableau**: the store and regional performance dashboards, to reuse official KPI definitions and targets. Quote
   view names and refresh dates; if Tableau and SQL disagree by more than 1%, say so and explain the likely reason.
3. **Drive and Confluence**: KPI definitions, the store's yearly plan, past business reviews, regional instructions.
4. **Gmail, Chat, Slack**: context on incidents, works, deliveries, staffing, local events in the period.
5. **Airtable or Jira**: store action trackers, to check whether last period's actions were done.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Set the comparable base.** Use weekday-aligned periods. Flag what breaks like-for-like: days closed, extended
   opening, surface change, remodel, school holiday calendar shifts, Easter, an e-commerce click-and-collect
   reallocation. If the store was not open all of N-1, say it is not comparable and switch to target or peers.
2. **Decompose revenue.** Sales = visitors × conversion × average basket, and basket = units per ticket × average
   unit price. Compute the log contribution of each factor to the change so the parts add up. Then interpret:
   - Traffic down, conversion stable → footfall issue (catchment, competition, weather, comms, opening hours).
   - Traffic stable, conversion down → in-store issue (availability, staffing at peaks, queues, price, layout).
   - Basket down via units per ticket → weaker multi-sale or bundles; via unit price → mix shift to entry price or
     markdowns.
3. **Locate the gap.** By sport universe (value gap and share of total gap; a Pareto usually shows 3–4 universes
   explain most of it), by weekday and by hour. Peak hours with high traffic and falling conversion point to
   understaffing or checkout queues; check labor hours by hour if available.
4. **Check the levers behind conversion**: availability on top sellers, the price of top items, staffing, and
   customer feedback (reviews, NPS comments if found). Pull each from a source or mark it "not checked".
5. **Productivity and margin.** Revenue per labor hour vs N-1; gross margin rate and the mix or markdown effect if
   margin data exists. A store that "buys" revenue with markdowns should be visible here.
6. **Benchmark.** Same KPIs vs peer stores or region: if everyone is down 6% and the store is down 7%, the store
   issue is 1 point, not 7.
7. **Conclude with 3–5 actions**, each tied to a driver, with an owner role, a date and a KPI to watch. Give an
   *estimate* of impact only with the method shown (for example "+1 pt conversion on Saturdays ≈ visitors × 1% ×
   basket").
8. Check last period's actions: done, not done, effect seen or not.

## Output format
```markdown
# <Store> — performance <period> vs <base>
**Headline:** <one sentence: result, main driver, main action>
_Assumptions: <comparable base, data caveats>_

## Key figures
| KPI | Period | N-1 | Δ | Target | Δ | Peers Δ |
|-----|--------|-----|---|--------|---|---------|
| Revenue | | | % | | % | % |
| Visitors | | | % | | | % |
| Conversion | % | % | pts | | | pts |
| Average basket | | | % | | | % |
| Units per ticket | | | % | | | |
| Revenue per labor hour | | | % | | | |
| Gross margin rate | % | % | pts | | | |

## What drove the change
| Driver | Contribution to revenue Δ | Reading |
|--------|---------------------------|---------|
| Traffic | % of Δ | |
| Conversion | % of Δ | |
| Basket | % of Δ | |

## Where it happened
| Sport universe | Revenue Δ (value) | Share of total gap | Main factor |
|----------------|-------------------|--------------------|-------------|
- Weekday / hour pattern: <one or two lines>

## Root causes (evidence → cause)
1. <evidence with number and source> → <cause> · confidence <high/medium/low>

## Actions
| # | Action | Driver | Owner (role) | Due | KPI to watch |
|---|--------|--------|--------------|-----|--------------|

## Last period's actions
- <action> — <done / not done> — <effect>

## Appendix — data used
- Polco: « <question> » · SQL: <query or tables> · Tableau: <view, refresh date>
```

## Quality checks
- The traffic, conversion and basket contributions add up to the total revenue change (± rounding).
- Every root cause cites at least one number with its source; causes without evidence are labeled hypotheses.
- Like-for-like breakers are listed, or the text says none were found.
- Peer or regional benchmark is shown, or marked unavailable.
- Each action is linked to a driver and has an owner role, a date and a KPI.
- The appendix lets someone rerun every number.

## Guardrails
- No fabricated figures, targets or peer data. Missing data stays missing, with the source that failed.
- Do not attribute results to named individuals or rank teammates; analysis stays at store, universe and hour level.
- Impact estimates are labeled *estimate* with the formula; never present them as forecasts or commitments.
- Draft only: sharing the analysis or creating tasks in Airtable or Jira needs the user's confirmation.
