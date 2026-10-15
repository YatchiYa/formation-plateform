---
name: kpi-definition-card
description: "Produces a KPI definition card that removes ambiguity: business question, exact formula with numerator and denominator, grain, filters and exclusions, source table in Unity Catalog, reference SQL, owner, refresh, edge cases, known pitfalls and related metrics, checked against existing definitions in Confluence, Drive and Tableau. Use whenever a team argues about what a number means, two dashboards disagree, a new metric is introduced, or someone asks how a KPI is calculated, even if they just ask 'what is conversion rate here'. Triggers - define this KPI, KPI definition, how is this metric calculated, metric card, single source of truth, définir un KPI, fiche KPI, définition de l'indicateur, comment est calculé, formule du KPI, indicateur clé."
---

# KPI definition card

Gives a team one written, testable definition of a metric, so that every dashboard, query and meeting means the same
thing by the same word.

## When to use
- Two reports show different values for the "same" KPI.
- A new KPI enters a dashboard, an OKR or a store ritual.
- A newcomer asks how a metric is computed.
- Before an A/B test or a target-setting exercise, to fix the metric precisely.
- Not for: answering what the KPI's value is today (use `data-question-answerer`), documenting all columns of a
  table (use `data-dictionary-builder`), or specifying a whole dashboard (use `dashboard-spec-writer`).

## Inputs
- KPI name and the business question it serves (required).
- Existing definitions, dashboards or queries (optional, default: search the sources below).
- Audience and decision it supports (optional, default: inferred and stated).
- If no internal definition exists and the business meaning is unclear (e.g. conversion = tickets / visitors or
  orders / sessions?), ask ONE grouped question.

## Sources
1. **Confluence and Drive**: KPI glossaries, data product docs, finance or controlling definitions, OKR documents.
2. **Tableau**: calculated fields and data sources of the dashboards that display the KPI.
3. **Databricks SQL MCP**: `DESCRIBE TABLE EXTENDED`, `information_schema.columns` and column comments of the
   candidate source table; small profiling queries with `LIMIT`.
4. **Polco**: ask how it computes the metric; capture its SQL as one candidate definition.
5. **GitHub**: dbt models or SQL files computing the metric (search the KPI name and its column names).
6. **Slack and Chat**: past disagreements about the metric, to list as pitfalls.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Collect every existing definition** found, each with its link. If they conflict, build a comparison table
   (formula, filters, source) before proposing anything.
2. **Decompose the formula**: numerator, denominator, unit, aggregation (sum, distinct count, ratio of sums), grain
   (transaction, day, store-week), time basis (order date vs invoice date vs delivery date).
3. **Fix the scope rules**: VAT included or not, returns and cancellations, channels (store, online, B2B),
   currency conversion and rate date, test/internal transactions, closed or new stores (like-for-like rule).
4. **Write the reference SQL** (read-only): three-level table names, explicit columns, `date_trunc` grain,
   `try_divide` for ratios, aggregation as ratio of sums. Run it on a small period with `LIMIT` if the SQL MCP is
   connected, and compare to the dashboard value.
   If no table was seen in Databricks or a document, the Source table row reads « [to confirm — no table found] »,
   the SQL uses angle-bracket placeholders (`<catalog.schema.repairs_table>`, `<start_ts>`, `<end_ts>`) with a
   comment saying so, and Refresh is « [to confirm] »; never write a plausible-looking table or column name.
5. **List edge cases**: zero denominators, partial days, late-arriving data, duplicates, mixed currencies, store
   openings, week 53.
6. **Pitfalls**: averaging ratios across stores, mix effects (a KPI can fall in every segment while the total
   rises: Simpson's paradox), comparing non-aligned weeks, using approximate counts in official reporting.
7. **Governance**: owner (named only if found in a source, else "to confirm"), refresh frequency, where it is
   certified, related KPIs and the decomposition tree (e.g. sales = traffic × conversion × average basket).

## Output format
````markdown
# KPI — <Name> (<FR name / EN name>)
_Status: draft for validation · Sources: <links>_

| Field | Definition |
|-------|-----------|
| Business question | <what decision it supports> |
| Formula | <numerator> / <denominator> (<unit>) |
| Aggregation | <ratio of sums / sum / distinct count> |
| Grain | <e.g. store × ISO week> |
| Time basis | <order / invoice / delivery date, time zone> |
| Included | <…> |
| Excluded | <…> |
| Source table | <catalog.schema.table> (columns: …) |
| Refresh | <frequency, latency> |
| Owner | <name from source / to confirm> |
| Certified in | <Tableau view / data product link / none> |

### Reference SQL
```sql
-- read-only reference implementation
```

### Edge cases
- <case> → <rule>

### Pitfalls
- <pitfall> → <how to avoid>

### Existing definitions found
| Where | Formula | Differs on | Link |
|-------|---------|-----------|------|

### Related KPIs
- <parent / child metrics in the tree>
````

## Quality checks
- The formula names both numerator and denominator, with units and aggregation method.
- Included/excluded rules cover VAT, returns, channels and like-for-like where relevant.
- Every existing definition found is listed with a link; conflicts are not silently resolved.
- The source table and columns were seen in Databricks or a document; none is invented.
- The owner is either sourced or marked "to confirm".

## Guardrails
- Propose, do not certify: the card is a draft until the data owner validates it; say so.
- Read-only SQL only.
- Do not invent internal targets, thresholds or owners.
- If the KPI measures people (productivity per teammate, absence rate), add an aggregation floor (no group < 5)
  and warn against individual ranking.
