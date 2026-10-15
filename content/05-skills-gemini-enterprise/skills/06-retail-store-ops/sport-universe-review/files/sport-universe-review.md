---
name: sport-universe-review
description: "Reviews one sport universe or department (rayon) of a store: sales and margin vs N-1 and target, traffic share and conversion where available, stock, availability and weeks of cover, sell-through of the season range, top and flop products, customer reviews, competitor signals, layout and visual merchandising, and a prioritized action list for the department manager. Use whenever someone wants to know how a rayon is doing, prepare a department review, or decide what to push, reorder or clear, even if they only name a sport. Triggers - department review, sport universe review, how is running doing, top and flop products, category review, revue de rayon, bilan rayon, comment va le rayon cycle, tops et flops, analyse univers sport, rayon ski, rayon running, sell-through, couverture de stock."
---

# Sport universe review

Gives a department manager (responsable de rayon) a clear picture of their sport universe and the five things to do
next, grounded in sales, stock and customer data.

## When to use
- Monthly or seasonal review of a rayon with the store manager.
- Before a season peak (ski in November, running at back to school, cycling in spring) to check readiness.
- After a season, to decide what to clear, keep or reorder.
- A rayon is behind the store average and the manager wants to know why.
- Not for: the whole store (use `store-performance-analysis`), a detailed stock-out root-cause study (use
  `stock-availability-analysis`), mining reviews of one product (use `product-review-insights`), or pricing vs
  competitors in depth (use `price-positioning-analysis`).

## Inputs
- Store and sport universe or department (required), as named in the data (search before asking).
- Period (optional, default: last 4 complete weeks and season to date).
- Season range or implantation plan (optional): the list of models expected on the shelf, from Drive if it exists.
- Competitor notes (optional): what the user has seen locally.

## Sources
1. **Databricks via Polco**: « ventes, marge, quantités, stock et réceptions par article pour l'univers X du magasin Y,
   période P et N-1 ». Then **Databricks SQL MCP** to verify: discover the product hierarchy tables (universe,
   family, model, item/size) and the stock and receipt tables with `SHOW TABLES` / `DESCRIBE`; never assume column
   names; show the queries used.
2. **Tableau**: department or category dashboards for official KPIs and targets; note view name and refresh time.
3. **Drive and Confluence**: implantation plans, range lists, visual merchandising guidelines, sport calendar.
4. **Customer reviews**: product ratings if available in Databricks or a shared export; otherwise skip and say so.
5. **Gmail, Chat, Slack**: supply alerts, recalls, price changes, product team messages about the range.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Headline KPIs**: revenue, units, gross margin rate, share of store revenue, vs N-1 and target. If visitor data per
   zone does not exist, do not invent a rayon conversion; use units per ticket containing the universe if available.
2. **Mix and price**: split the change into volume, average price and mix (entry, mid, expert price tiers). A rising
   revenue with falling margin often means markdowns or a shift to lower-margin models.
3. **Top and flop at model level** (not size): top 10 by revenue and by margin; flops = ranged models with low sales
   *and* high stock. Use a simple ABC (A = models making 80% of revenue). An A model out of stock is a priority; a C
   model with 20 weeks of cover is a markdown or transfer candidate.
4. **Stock health**:
   - weeks of cover = stock units / average weekly units sold (use the next weeks' forecast if it exists, else the
     last 4 weeks, and say which);
   - sell-through for the season range = units sold / (opening stock + receipts);
   - size-run integrity for footwear and textile: share of key models with all core sizes in stock (a broken size run
     sells like an out-of-stock);
   - availability of A models on the period.
5. **Customer voice**: average rating and main complaints for the top models, if data exists; link defects to returns
   or workshop data if visible.
6. **On the floor** (from the user or a visit report): implantation respected, price labels, the sport-family logic,
   endcaps used for the season, services visible (workshop, rental, second-hand) where relevant.
7. **Actions (max 5)**, ranked by value at stake: reorder or transfer A models, clear C overstock, fix size runs,
   re-implant a bay, train the team on a technical product. Each with owner role, date and KPI.

## Output format
```markdown
# Rayon <universe> — <store> — <period>
**In one line:** <result + main reason + top action>

## Key figures
| KPI | Period | N-1 | Δ | Target | Δ |
|-----|--------|-----|---|--------|---|
| Revenue | | | % | | % |
| Units | | | % | | |
| Gross margin rate | % | % | pts | | |
| Share of store revenue | % | % | pts | | |
| Availability of A models | % | % | pts | | |
| Weeks of cover | | | | | |
| Season sell-through to date | % | % | pts | | |

## Price / mix
- <volume vs price vs mix reading, 2–3 lines>

## Tops and flops (model level)
| Rank | Model | Revenue | Δ N-1 | Margin rate | Stock | Weeks of cover | Class | Note |
|------|-------|---------|-------|-------------|-------|----------------|-------|------|

## Stock health
- Broken size runs: <n models, examples>
- Overstock (> <x> weeks of cover): <models>
- Out of stock on A models: <models, days out>

## Customer voice
- <rating, top complaint, source>

## On the floor
- <observations, or "no visit data provided">

## Actions
| # | Action | Value at stake | Owner (role) | Due | KPI |
|---|--------|----------------|--------------|-----|-----|

_Data used: <Polco question, SQL tables, Tableau view, docs>_
```

## Quality checks
- Tops and flops are at model level and each row shows stock and weeks of cover, not just sales.
- The cover method (forecast or last 4 weeks) is stated.
- Every action is linked to a number in the review and has an owner role and date.
- No rayon conversion rate is shown unless zone-level traffic data actually exists.
- Seasonality is respected: a ski range in March is judged on sell-through and clearance, not on growth.

## Guardrails
- Never invent targets, margins, competitor prices or review scores; mark gaps as "not available".
- Price changes and markdowns are proposals for the people who own pricing; do not present them as decided.
- No teammate-level performance; the review is about the universe, not individuals.
- Draft only: no orders, transfers or messages are triggered without the user's confirmation.
