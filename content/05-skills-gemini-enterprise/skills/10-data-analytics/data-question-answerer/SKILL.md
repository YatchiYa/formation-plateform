---
name: data-question-answerer
description: "Answers a business question with real data from Databricks (SQL MCP or the Polco natural-language data assistant) or Tableau: finds the right source, runs read-only queries, and returns the number with its definition, comparison base (N-1, target, previous period), the query or view used, the date the data was pulled and the caveats. Use whenever someone asks how much, how many, what share, what trend or which top items, about sales, stock, traffic, customers or any business metric, even if they do not mention Databricks, SQL or a dashboard. Never guesses a figure. Triggers - how much did we sell, what are the numbers, give me the figures, top 10 products, trend of, data question, combien a-t-on vendu, quels sont les chiffres, donne-moi les données, évolution de, top produits, part de, quel est le CA."
---

# Data question answerer

Gives a Company teammate a trustworthy answer to a data question: the number, what it means, how it was computed
and how far to trust it, with every figure traceable to a query or a dashboard.

## When to use
- A quick factual question: "How many tents did we sell in France last week vs last year?"
- A ranking or share: "Top 10 products by revenue in running this month", "share of online sales".
- A trend: "How did the average basket evolve over the last 12 months?"
- A number someone needs for an email, a meeting or a decision, today.
- Not for: explaining an unexpected drop or spike (use `metric-anomaly-investigator`), writing a reusable query
  only (use `databricks-sql-builder`), store deep dives (use `store-performance-analysis`), or turning results into
  a narrative for leadership (use `insight-storyteller`).

## Inputs
- The question (required).
- Perimeter and period (required; default if unstated: last complete ISO week, user's country if known, all
  channels; state it).
- Comparison base (optional, default: same period N-1 with aligned weeks, plus target if a target table exists).
- Metric definition (optional, default: the documented definition found in Confluence/Drive; ask ONE grouped
  question if several conflicting definitions exist).

## Sources
1. **Polco (Genie-style MCP)**: first attempt for natural-language questions on curated datasets; capture the SQL
   it generated.
2. **Databricks SQL MCP**: run or re-run the query on Unity Catalog to verify Polco's answer or when Polco cannot
   answer; discovery with `SHOW TABLES`, `DESCRIBE TABLE`, `information_schema`.
3. **Tableau**: the official dashboard that already reports the metric; use it as the reference value and link it.
4. **Confluence and Drive**: KPI definitions and data documentation, to make sure the metric means what the user
   thinks.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Pin the question**: metric, formula, perimeter, period, grain, comparison. Write it in one line.
2. **Find the reference**: if a Tableau view or a certified table reports this metric, start there.
3. **Get the number**:
   - Ask Polco in plain language; keep its SQL.
   - Check or write the SQL yourself: three-level names, explicit columns, date or partition filter with literal
     bounds, `date_trunc` for periods, `LIMIT` on any exploration, aggregated output only.
   - N-1 comparison: compare aligned ISO weeks (week 41 vs week 41, same number of days and same weekdays), not
     calendar dates; flag moving holidays (Easter, Ascension), sales periods and calendar shifts.
4. **Cross-check** with a second route when the number will be shared: Tableau vs SQL, or total vs sum of parts.
   Differences > 1 % are explained (definition, refresh time, VAT, returns, perimeter) or flagged.
5. **Sanity checks**: magnitude plausible vs history, no fan-out (row count before/after joins), period complete
   (last day loaded? check `max(date)`), small bases flagged (n < 30 or < 100 orders → unstable ratio).
6. **Answer**: lead with the number and the comparison, then definition, source, caveats. Use relative change
   with absolute values (never a % alone), and percentage points for changes in rates.
7. If no source can answer, say so plainly and propose who owns the data or which table to request. Still return
   the Output format: the pinned question (step 1, defaults stated, e.g. September = last completed one), Value
   « [not available] », the draft SQL with `<catalog.schema.table>` placeholders, Confidence Low, and one grouped
   question for any ambiguity (year, product definition, store list).

## Output format
````markdown
**<Answer in one sentence: metric = value, vs comparison (+x % / +y pts)>**
_Perimeter: <…> · Period: <…> · Data pulled: <YYYY-MM-DD HH:MM> · Freshness: data up to <date>_

| Metric | Value | Comparison base | Δ abs | Δ % |
|--------|-------|-----------------|-------|-----|

**Definition used:** <formula in words> ([definition source](…) or _assumption_)

**Caveats**
- <incomplete period / definition gap / small base / one-off event>

**Confidence:** High | Medium | Low — <why in one line>

<details><summary>How this was computed</summary>

Source: <Polco / Databricks SQL / Tableau view link>
```sql
<the exact query run>
```
Cross-check: <second route and its result, or "not done">
</details>
````

## Quality checks
- Every figure in the answer comes from a query result or a dashboard shown in the "How this was computed" block.
- The data pull date and the data freshness (max date loaded) are both stated.
- Changes in rates are in percentage points; every % change is shown next to its absolute values.
- N-1 comparisons use aligned weeks or say explicitly that calendar dates were used and why.
- Confidence is Low whenever the cross-check failed, the period is incomplete or the base is small.

## Guardrails
- Never fabricate, round to look nicer or extrapolate a figure without labeling it *estimate* with its method.
- Read-only SQL only; no DDL or DML.
- Return aggregates; never list individual customers or teammates. Suppress groups smaller than 5 people when the
  metric is about people.
- Show only data the user can access through their own permissions; do not relay figures from someone else's
  restricted dashboard.
- Financial results not yet published externally are confidential: remind the user not to share outside
  Company when the question touches group revenue or margin.
