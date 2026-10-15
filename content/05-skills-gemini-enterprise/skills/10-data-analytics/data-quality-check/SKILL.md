---
name: data-quality-check
description: "Audits a Databricks table or dataset on the six data-quality dimensions (completeness, uniqueness, validity, consistency, freshness, accuracy against a reference) with ready-to-run read-only SQL checks, thresholds, results, a severity per finding and a fix owner, plus reusable monitoring queries. Use whenever someone doubts a table, onboards a new data source, sees strange numbers, or wants to know if a dataset is safe to use for a dashboard or decision, even if they only ask 'can I trust this table'. Triggers - data quality check, is this table reliable, check this dataset, duplicates, missing values, data freshness, contrôle qualité des données, la table est-elle fiable, vérifier ce jeu de données, doublons, valeurs manquantes, fraîcheur des données."
---

# Data quality check

Tells a teammate whether a table can be trusted for their use, with evidence: which checks passed, which failed,
how bad it is, and what to do.

## When to use
- Before building a dashboard, KPI or model on a table.
- When numbers from a table look strange or disagree with another source.
- When a new source or pipeline lands in Unity Catalog.
- To set up recurring checks for a critical table.
- Not for: explaining a business metric move (use `metric-anomaly-investigator`), documenting the table's columns
  (use `data-dictionary-builder`), or writing a general query (use `databricks-sql-builder`).

## Inputs
- Table name as `catalog.schema.table` (required; if only a topic is given, discover candidates and ask to
  confirm).
- Intended use (optional, default: reporting), which sets thresholds.
- Primary key and expected grain (optional, default: inferred from `DESCRIBE` and profiling, then stated).
- Reference figure for accuracy (optional: dashboard, finance closing, source system count).

## Sources
1. **Databricks SQL MCP**: `DESCRIBE TABLE EXTENDED` (columns, partitioning, owner, last modified),
   `DESCRIBE HISTORY` if Delta history is visible, `information_schema.columns`, and the check queries.
2. **Confluence and Drive**: data contracts, table documentation, expected grain, SLA and known limitations.
3. **Tableau**: dashboards built on the table, as references and to list impacted assets.
4. **Jira, GitHub, Slack**: open data incidents, pipeline code and recent schema changes.
5. **Polco**: optional quick profiling in natural language; confirm with SQL.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Profile** with `LIMIT` and aggregates only: row count, partition range, `max(<date_col>)`, per-column NULL
   share, distinct counts (`approx_count_distinct` on big tables), min/max for numerics and dates.
2. **Run the dimension checks** (adapt names from DESCRIBE; never guess columns):
   - **Completeness**: NULL share per key column; missing days/stores/partitions vs a calendar or dimension.
   - **Uniqueness**: `SELECT <pk>, count(*) c FROM t GROUP BY <pk> HAVING count(*) > 1 ORDER BY c DESC LIMIT 20`.
   - **Validity**: domain rules (negative quantities without return flag, future dates, unknown codes not in the
     dimension, malformed emails or country codes, out-of-range prices).
   - **Consistency**: referential integrity (orphans via LEFT ANTI JOIN to dimension tables), totals equal sum of
     lines, same metric equal across two tables.
   - **Freshness**: latest load vs expected SLA; daily volume over the last 30 days to spot drops.
   - **Accuracy**: reconcile a total for a closed period vs a reference figure; report the gap in % and abs.
3. **Set thresholds** by use (state them): e.g. reporting: duplicates 0 on PK, NULL < 1 % on keys, freshness
   within SLA, reconciliation gap < 0.5 %. These are defaults to adapt, not internal standards.
4. **Score severity**: Critical (wrong totals or PK broken), Major (bias in a segment, stale), Minor (cosmetic).
5. **Impact**: which dashboards, KPIs or users rely on the table (from Tableau and docs).
6. **Recommend**: owner to contact (from `DESCRIBE TABLE EXTENDED` owner or docs), workaround for the user (filter,
   dedup with `QUALIFY`), and checks to schedule.

## Output format
````markdown
**Verdict: <Fit for use / Use with caution / Do not use> for <intended use>** — <one-line reason>
_Table: <catalog.schema.table> · Owner: <from metadata / unknown> · Checked: <YYYY-MM-DD HH:MM> · Rows: <n>_

| Dimension | Check | Result | Threshold | Status |
|-----------|-------|--------|-----------|--------|
| Completeness | NULL share in <col> | … | < 1 % | ✓/⚠/✗ |
| Uniqueness | duplicates on <pk> | … | 0 | |
| Validity | … | | | |
| Consistency | orphans vs <dim table> | | | |
| Freshness | max(<date>) | | ≤ SLA | |
| Accuracy | total vs <reference> | | < 0.5 % gap | |

### Findings
1. **<Severity>** — <issue> — impact: <who/what> — evidence: query Qn

### Workarounds for now
- <filter / dedup pattern>

### Recommended monitoring
```sql
-- daily checks to schedule (read-only)
```

<details><summary>Queries run</summary>

```sql
-- Q1 …
```
</details>
````

## Quality checks
- All six dimensions appear in the table, with "not tested" and a reason where a check was impossible.
- Every result comes from a query shown in "Queries run".
- Thresholds are stated and labeled as defaults when no data contract was found.
- The verdict follows from the worst finding (any Critical → Do not use or Use with caution).
- No query selects raw personal data; PII columns are only counted or checked for format.

## Guardrails
- Read-only: never delete duplicates, fix rows or alter the table; describe the fix for the owner.
- PII columns: check NULL share and format with aggregates; never print values.
- Do not run full scans of very large tables without a partition filter; sample recent partitions first and say so.
- Do not contact the table owner or open tickets without the user's confirmation.
