---
name: stock-availability-analysis
description: "Analyzes store stock health from Databricks: out-of-stock rate on the active range weighted by sales, estimated lost sales, broken size runs, phantom stock suspects, overstock and weeks of cover, sell-through, then classifies root causes (forecast, replenishment, supply, receiving, shelf filling, data accuracy) and proposes actions per item group. Use whenever a store, department or supply teammate sees empty shelves, too much stock, or asks why a product is never available, even if they only name one item. Triggers - out of stock, OOS analysis, availability, overstock, weeks of cover, phantom stock, stock health, ruptures, taux de rupture, disponibilité rayon, surstock, couverture de stock, stock fantôme, pourquoi ce produit est toujours en rupture, réassort, sell-through."
---

# Stock availability analysis

Shows where a store is losing sales because of empty shelves or tying up cash in excess stock, why it happens, and
what to fix first.

## When to use
- Customers or teammates report frequent empty shelves on top sellers.
- A season is starting (ski, running back to school, spring cycling) and the manager wants to check readiness.
- Stock value is high, the stock room is full, or the season is ending with heavy leftovers.
- A specific item « is always out of stock » and someone needs to know why.
- Not for: a whole department review including sales and customers (use `sport-universe-review`), store-level
  sales drivers (use `store-performance-analysis`), or writing the SQL in depth for data teams (use
  `databricks-sql-builder`).

## Inputs
- Store(s) and scope: whole store, sport universe or list of items (required).
- Period (optional, default: last 4 weeks, daily grain).
- Active range definition (optional, default: items with stock or sales in the last 8 weeks and not flagged as
  discontinued, if such a flag exists in the data).
- Thresholds (optional, default: overstock > 12 weeks of cover for in-season items; adjust per category and say so).

## Sources
1. **Databricks via Polco**: « stock en fin de journée, ventes, réceptions et commandes par article et par jour pour
   le magasin X sur 4 semaines ». Then **Databricks SQL MCP**: discover stock, sales, receipts, orders and item
   master tables (`SHOW TABLES`, `DESCRIBE`, sample 10 rows); confirm the grain (item vs model vs size) and units;
   never assume column names. Show every query used.
2. **Tableau**: availability or stock dashboards, to align with the official OOS definition. If the official
   definition differs from yours, use the official one and cite it.
3. **Drive and Confluence**: replenishment rules, range lists, implantation plans, the KPI definitions.
4. **Gmail, Chat, Slack**: supplier delays, warehouse issues, recalls, transport incidents in the period.
5. **Jira or Airtable**: supply or IT tickets about stock data or replenishment.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Define the base**: active items × days. An OOS day = an active item with stock ≤ 0 at day end (or the official
   definition). Compute:
   - OOS rate (count) = OOS item-days / active item-days;
   - OOS rate weighted by sales = Σ (OOS days × average daily units) / Σ (all days × average daily units). The
     weighted rate is the one that matters: one top running shoe out for a week costs more than 50 slow items.
   - Lost sales *estimate* = average daily units when in stock × OOS days × average price. Label it *estimate*.
2. **Size runs** (footwear, textile, ski boots): for key models, share of core sizes in stock. A model at 60% of its
   sizes is « available » in counts but loses most customers.
3. **Phantom stock suspects**: items with positive system stock, usual daily sales ≥ 1, and zero sales for N days
   (N ≈ 3 × usual interval between sales). These need a physical count, not an order.
4. **Overstock**: weeks of cover = stock / average weekly units (forward forecast if available); sell-through =
   units sold / (opening stock + receipts). Flag in-season items above the threshold and end-of-season items with low
   sell-through.
5. **Root-cause each priority item** with the evidence pattern:
   | Pattern | Likely cause |
   |---------|--------------|
   | Ordered on time, not received | supply / warehouse / transport |
   | Received, still empty on shelf, stock in the back | shelf filling / receiving process |
   | Stock > 0 in system, nothing on shelf, no sales | phantom stock / data accuracy |
   | Never ordered enough before a peak | forecast or replenishment parameters |
   | Sudden demand spike (weather, event, influencer) | forecast, one-off |
   | Supplier shortage across stores | supply, not store-controllable |
6. **Prioritize** by value at stake (lost sales or stock value), then by controllability by the store.
7. **Actions** by cause: count and correct stock, fill from the back, adjust a parameter (proposal for the owner),
   transfer between stores, markdown or second-life proposal for overstock, alert to supply.

## Output format
```markdown
# Stock health — <store / scope> — <period>
**In one line:** <weighted OOS rate, lost sales estimate, main cause, first action>
_Definitions: <OOS definition and source>, cover method: <forecast / last 4 weeks>_

## Key figures
| KPI | Value | N-1 or previous period | Comment |
|-----|-------|------------------------|---------|
| OOS rate (count) | % | % | |
| OOS rate (sales-weighted) | % | % | |
| Lost sales (estimate) | | | |
| Models with broken size runs | n | | |
| Phantom stock suspects | n | | |
| Stock value > threshold cover | | | |
| Season sell-through | % | % | |

## Top 10 availability issues
| Item / model | Universe | OOS days | Lost sales (est.) | Pattern | Likely cause | Action |
|--------------|----------|----------|-------------------|---------|--------------|--------|

## Overstock
| Item / model | Stock | Weeks of cover | Sell-through | Proposed action |
|--------------|-------|----------------|--------------|-----------------|

## Causes overview
| Cause | Items | Value at stake | Store-controllable? |
|-------|-------|----------------|---------------------|

## Actions this week
1. <verb + items + owner role + date>

## Appendix — queries
<Polco questions and SQL used>
```

## Quality checks
- The weighted OOS rate is shown next to the count rate, with the formula.
- Every lost-sales or value figure is labeled *estimate* and the inputs are visible.
- Grain is stated (item, size or model) and consistent across tables.
- Phantom stock suspects are routed to a count, never to an order.
- Each top issue has a pattern → cause → action chain, not just a number.

## Guardrails
- Never invent stock levels, orders or supplier dates; if order data is missing, the cause stays « unknown ».
- Parameter changes, transfers and markdowns are proposals for the people who own them; nothing is ordered or changed.
- Do not blame named teammates or suppliers; describe process failures.
- Draft only: alerts to supply or other stores are sent after the user confirms.
