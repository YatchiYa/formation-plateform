---
name: databricks-sql-builder
description: "Writes, explains and optimizes read-only Databricks SQL on Unity Catalog from a business question: discovers the right catalog, schema and tables, checks columns with DESCRIBE, builds a commented query with CTEs, adds validation queries (row counts, duplicates, totals) and explains every assumption. Use whenever someone needs a SQL query, wants to fix or speed up an existing one, or asks how to get a number out of Databricks, even if they only paste a broken query or say 'how do I pull this'. Triggers - write a SQL query, Databricks query, optimize my SQL, fix this query, which table has, SQL for, écris-moi une requête SQL, requête Databricks, optimiser ma requête, corriger ma requête SQL, dans quelle table trouver, comment extraire."
---

# Databricks SQL builder

Turns a business question into a correct, readable and cheap Databricks SQL query on Unity Catalog, with the
discovery steps and validation queries that prove it returns what the user thinks it returns.

## When to use
- The user has a question ("weekly sales by sport for my country since January") and needs the query.
- The user pastes a query that fails, is slow, or returns suspicious numbers.
- The user does not know which catalog, schema or table holds the data.
- The user wants to learn: an explained query they can reuse in a notebook, SQL editor or dashboard.
- Not for: getting the answer itself with numbers and caveats (use `data-question-answerer`), defining a KPI
  formally (use `kpi-definition-card`), auditing a table's quality (use `data-quality-check`) or documenting
  tables (use `data-dictionary-builder`).

## Inputs
- The business question or the existing query (required).
- Scope (optional, default: ask once if the grain is ambiguous): period, perimeter (country, store, channel,
  sport), grain (day, ISO week, month), metric definitions.
- Known table names or a catalog to start from (optional, default: discover with the steps below).
- If the metric definition is ambiguous (e.g. sales with or without VAT, returns netted or not), ask ONE grouped
  question; otherwise proceed and state assumptions in one line.

## Sources
1. **Databricks SQL MCP**: catalog discovery and query execution on Unity Catalog (read-only statements only).
2. **Polco (Genie-style MCP)**: ask which tables or certified datasets answer the question; reuse its generated SQL
   as a starting point, never as proof.
3. **Confluence and Drive**: data catalog pages, KPI definitions, data product documentation, example queries.
4. **GitHub**: existing dbt models, notebooks or SQL files that already compute the metric (search table names).
5. **Slack and Chat**: data team channels for known caveats on a table (late loads, deprecated columns).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Restate the question as a spec**: metric(s), formula, grain, filters, period, expected output columns.
2. **Discover** (only what is needed, each with `LIMIT`):
   - `SHOW CATALOGS;` → `SHOW SCHEMAS IN <catalog>;` → `SHOW TABLES IN <catalog>.<schema>;`
   - Keyword search: `SELECT table_catalog, table_schema, table_name, comment FROM system.information_schema.tables
     WHERE lower(table_name) LIKE '%sale%' OR lower(comment) LIKE '%vente%' LIMIT 50;`
   - `DESCRIBE TABLE EXTENDED <catalog>.<schema>.<table>;` for columns, types, comments, partition columns, owner.
   - Prefer certified, gold or documented tables over raw or bronze ones; say which one you picked and why.
3. **Profile before trusting**: min/max of the date column, row count on a small period, and the grain check
   `SELECT key, count(*) FROM t GROUP BY key HAVING count(*) > 1 LIMIT 20;`.
4. **Write the query** with these rules:
   - Always three-level names `catalog.schema.table`; one CTE per logical step, each commented.
   - Explicit column lists, never `SELECT *` (except `LIMIT 10` previews).
   - Filter on partition or date columns first, with a literal range (`sale_date >= '2026-01-01' AND sale_date < '2026-02-01'`), so
     pruning works; no functions wrapped around the partition column.
   - Time buckets with `date_trunc('WEEK', d)` (ISO weeks start Monday) or `date_trunc('MONTH', d)`.
   - Deduplicate with `QUALIFY row_number() OVER (PARTITION BY key ORDER BY updated_at DESC) = 1`.
   - Use `approx_count_distinct` for exploration on large tables, exact `count(DISTINCT)` for reported figures.
   - Ratios with `try_divide(a, b)` or `NULLIF` to avoid divide-by-zero; ratio of sums, not average of ratios.
   - Joins: state the join key and expected cardinality (1:1, n:1); check for fan-out after each join.
   - `LIMIT` on every exploratory query; aggregate PII away (no customer-level rows unless strictly needed).
5. **Validate** with 2–3 queries: total vs a known reference (dashboard, finance figure), row count per period,
   duplicate check after joins, NULL share in key columns.
6. **Optimize** if asked or if slow: prune partitions, filter before joining, pre-aggregate in CTEs, avoid
   `DISTINCT` to hide fan-out, broadcast small dimensions, replace correlated subqueries with joins or windows.
7. **Run** only if the user asks and the SQL MCP is connected; show the run date and row count.

## Output format
````markdown
**Query for:** <question restated in one line>
_Assumptions: <metric definition, grain, period, time zone>_

### Tables used
| Table (catalog.schema.table) | Why | Grain | Key columns | Caveat |
|------------------------------|-----|-------|-------------|--------|

### Query
```sql
-- Purpose: <one line> | Author: drafted with Gemini, review before reuse
WITH base AS ( -- step 1: <what>
  ...
)
SELECT ...
```

### How it works
1. <CTE name> — <what it does, in plain language>

### Validation queries
```sql
-- V1 duplicates after join
-- V2 total vs reference
```

### Performance notes
- <partition filter used / what to change if slow>

_Discovery: <tables inspected> · Run: <not executed | executed YYYY-MM-DD, N rows>_
````

## Quality checks
- Every table is referenced with three-level names and was seen in discovery or provided by the user.
- Every column used appears in a `DESCRIBE` result or user input; none is guessed.
- The query contains no DDL or DML (no CREATE, INSERT, UPDATE, DELETE, MERGE, DROP, ALTER, GRANT).
- Exploratory queries have `LIMIT`; no `SELECT *` in the final query.
- The date filter is on the partition or date column with literal bounds.
- At least one validation query covers duplicates or totals.

## Guardrails
- Read-only. Never write, alter or drop tables, even if asked; propose the statement for a data engineer instead.
- Only query what the user can access; if access is denied, say so and name the table owner from
  `DESCRIBE TABLE EXTENDED` rather than looking for a workaround.
- Minimize personal data: aggregate, avoid selecting names, emails, phone numbers or loyalty IDs unless the task
  requires it and the user is entitled to it.
- Never present Polco or generated SQL results as verified until the validation queries pass.
- Do not invent table or column names; if discovery finds nothing, say so and ask for the data owner.
