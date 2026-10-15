---
name: metric-anomaly-investigator
description: "Investigates an unexpected drop or spike in a business metric with a disciplined method: first rules out data issues (freshness, duplicates, definition or tracking changes), then checks calendar and seasonality against aligned N-1 weeks, decomposes the metric into its drivers (e.g. traffic × conversion × basket), splits by segment to separate rate effects from mix effects (Simpson's paradox), and tests a hypothesis tree with read-only Databricks queries, ending with findings ranked by evidence and next actions. Use whenever a number looks wrong or suspicious, two metrics disagree (e.g. the traffic counter drops while sales stay flat), or a metric falls, jumps or diverges from target, even if the user only says 'sales are down, why?'. Triggers - number looks wrong, metrics do not match, counter bug, why did sales drop, metric spike, KPI anomaly, explain this drop, root cause of the decrease, pourquoi les ventes baissent, chute du KPI, pic anormal, expliquer la baisse, analyse d'écart, que s'est-il passé sur."
---

# Metric anomaly investigator

Finds out why a metric moved, in the right order: is the data right, is it the calendar, which driver moved, which
segment moved, and what evidence supports each explanation.

## When to use
- A KPI dropped or spiked versus N-1, target or the previous period, and someone needs to know why.
- A dashboard tile turned red before a weekly review.
- An alert fired on a metric (orders, traffic, conversion, returns, stock-outs).
- Not for: a plain "what is the value" question (use `data-question-answerer`), routine store reviews (use
  `store-performance-analysis`), budget gaps (use `budget-variance-analysis`), stock-outs specifically (use
  `stock-availability-analysis`), or a completed A/B test (use `ab-test-readout`).

## Inputs
- Metric, perimeter, the period where it moved and the comparison base (required; default comparison: aligned N-1
  weeks plus the previous 4 weeks).
- Size of the move and where it was seen (optional; dashboard link helps).
- Known events: promotions, price changes, stock issues, weather, site releases, store works (optional, default:
  searched in sources).

## Sources
1. **Databricks SQL MCP**: the fact and dimension tables behind the metric (discover with `SHOW TABLES`,
   `DESCRIBE TABLE EXTENDED`, `information_schema`); all hypothesis-testing queries, read-only.
2. **Polco**: fast first cuts by segment in natural language; verify any number used in findings with SQL.
3. **Tableau**: the dashboard where the anomaly was seen, to reproduce the exact number and filters.
4. **Jira and GitHub**: releases, incidents, tracking or pipeline changes in the window (search "tracking",
   "tag", "pipeline", "migration", the table name).
5. **Slack, Chat, Gmail and Confluence**: data incident channels, commercial calendar, promotion plans, store
   events, known outages.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Reproduce the number** exactly (same filters, same definition). If you cannot, stop and explain the gap.
2. **Rule out data issues first** (most anomalies are data):
   - Freshness: `SELECT max(<date_col>) FROM <catalog.schema.table>` vs expected; partial last day?
   - Volume per day/store/source for the window: missing partitions, a store or channel with zero rows.
   - Duplicates: `GROUP BY <key> HAVING count(*) > 1 LIMIT 20`.
   - Definition, tracking or pipeline changes in Jira/GitHub/Slack during the window.
3. **Calendar and seasonality**: compare aligned ISO weeks (same weekday mix), and check moving holidays, school
   holidays by zone, sales periods, weather, week 53, store openings/closures (use like-for-like). Show the last
   8–12 weeks N vs N-1 so a one-week dip is seen against its trend.
4. **Decompose the metric** into multiplicative or additive drivers, e.g. sales = traffic × conversion ×
   average basket; average basket = items per ticket × average item price; online = sessions × conversion × AOV.
   For a product of drivers, contribution of driver i ≈ Δln(driver i) / Δln(total) (log decomposition sums to 100 %).
5. **Segment split, rate vs mix**: split by the 2–3 most plausible dimensions (channel, region/store, sport,
   product family, new vs returning customers). For each, separate:
   - rate effect = Σ (rate_N − rate_N-1) × weight_N-1
   - mix effect = Σ (weight_N − weight_N-1) × rate_N
   Check for Simpson's paradox: the total can fall while every segment rises (or the reverse) because weights moved.
6. **Hypothesis tree**: list candidate causes (data, calendar, demand, price/promo, availability, competition,
   operations, product/site change). For each: expected signature, test query, result, verdict
   (confirmed / rejected / open).
7. **Quantify**: attribute the move to confirmed causes in absolute and %; keep an "unexplained" line rather than
   forcing 100 %.
8. **Next actions**: who should act, what to monitor, what additional data would close the open hypotheses.

## Output format
````markdown
**<Metric> <fell/rose> <x %> (<abs>) vs <base> on <perimeter, period>. Main driver: <one line>. Confidence: <H/M/L>.**
_Data pulled: <YYYY-MM-DD> · Freshness: data up to <date> · Comparison: <aligned weeks / calendar>_

### 1. Data checks
| Check | Result | OK? |
|-------|--------|-----|
| Freshness | … | ✓/✗ |
| Volumes by day/source | … | |
| Duplicates | … | |
| Definition/tracking changes | … | |

### 2. Calendar and trend
- <aligned-week comparison, 8–12 week trend, events>

### 3. Driver decomposition
| Driver | N | N-1 | Δ % | Contribution to total Δ |
|--------|---|-----|-----|------------------------|

### 4. Segments (rate vs mix)
| Segment | Weight N-1 → N | Rate N-1 → N | Rate effect | Mix effect |
|---------|----------------|--------------|-------------|-----------|
_Simpson check: <yes/no + one line>_

### 5. Hypotheses
| Hypothesis | Test | Result | Verdict |
|-----------|------|--------|---------|

### Findings (ranked by evidence)
1. <cause> — <quantified impact> — evidence: <query / link>
- Unexplained: <abs / %>

### Next actions
- <owner role> — <action> — <by when>

<details><summary>Queries</summary>

```sql
-- one block per check, read-only
```
</details>
````

## Quality checks
- Data checks were run and reported before any business explanation.
- N-1 comparison uses aligned weeks or explicitly states why not.
- Driver contributions and rate/mix effects add up to the total change, with any residual shown as unexplained.
- Every confirmed cause cites a query result or a sourced event; rejected hypotheses stay visible.
- Confidence is Low if the number could not be reproduced or a data check failed.

## Guardrails
- Read-only SQL only; no DDL or DML, no fixes to pipelines.
- Never blame a team, store or person; describe causes as mechanisms and events.
- Aggregate: no customer-level or teammate-level rows in the output; suppress groups below 5 people.
- Correlation is not causation: label causal claims without a test as *hypothesis*.
- Do not fabricate events (promotions, outages, weather); cite them or mark them as questions to check.
