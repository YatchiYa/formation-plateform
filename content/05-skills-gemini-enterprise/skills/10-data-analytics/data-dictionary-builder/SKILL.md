---
name: data-dictionary-builder
description: "Builds a data dictionary for one or more Databricks Unity Catalog tables: table purpose, grain, primary key, partitioning, owner and freshness, then for every column its type, business definition, example value pattern, allowed values or range, NULL share, PII flag and join keys, drawn from DESCRIBE, information_schema, column comments, profiling queries and existing documentation, with gaps marked to confirm. Use whenever someone needs to document a table, onboard a newcomer to a dataset, prepare a data product page, or asks what the columns of a table mean, even if they only say 'what is in this table'. Triggers - data dictionary, document this table, what do these columns mean, table documentation, schema description, dictionnaire de données, documenter cette table, que signifient ces colonnes, description du schéma, fiche table."
---

# Data dictionary builder

Produces the documentation a teammate needs to use a table correctly: what one row is, what each column means, which
ones are sensitive, and how to join it.

## When to use
- A table or data product has no documentation, or outdated docs.
- A newcomer or another team starts using a dataset.
- Before publishing a data product page in Confluence.
- To prepare a GDPR inventory of personal-data columns in a schema.
- Not for: defining one business KPI (use `kpi-definition-card`), auditing data quality in depth (use
  `data-quality-check`), or a team glossary of business terms (use `glossary-builder`).

## Inputs
- Table(s) as `catalog.schema.table`, or a schema to cover (required; if only a topic, discover and confirm).
- Audience (optional, default: analysts and business users).
- Output destination (optional, default: Markdown ready to paste in Confluence or a Doc).

## Sources
1. **Databricks SQL MCP**: `SHOW TABLES IN <catalog>.<schema>`, `DESCRIBE TABLE EXTENDED` (types, comments,
   partitioning, owner, created/modified), `information_schema.columns` and `information_schema.table_constraints`,
   `SHOW TBLPROPERTIES`, and profiling queries with aggregates and `LIMIT`.
2. **Confluence and Drive**: existing data product pages, data contracts, KPI glossaries, source-system docs.
3. **GitHub**: pipeline or dbt code producing the table (column derivations, filters, joins).
4. **Tableau**: data sources using the table (which columns are used downstream).
5. **Polco**: how it describes the dataset, as a hint only.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Table header**: purpose, grain ("one row = one ticket line"), primary key (from constraints or verified with a
   duplicate check), partition columns, owner, last modified, row count, date range, refresh pattern (daily volume
   over last 14 days).
2. **Column metadata**: name, type, nullable and comment from `information_schema.columns` (ordered by
   `ordinal_position`).
3. **Profile each column** with aggregates only: NULL share, `approx_count_distinct`, min/max for numbers and
   dates; for low-cardinality codes (< 50 distinct) list values with counts; for text, describe the pattern
   (e.g. "8-digit numeric code") rather than printing values.
4. **Business definition**: from the comment, docs or pipeline code (cite which). If none, propose one and mark it
   *to confirm*. Never guess the meaning of an opaque code.
5. **Classify sensitivity**: PII direct (name, email, phone, address), PII indirect (customer ID, loyalty card,
   device ID, precise location), sensitive (health, payment), business-confidential (cost, margin). Never print
   sample values for these.
6. **Relationships**: probable foreign keys (name match + orphan check via LEFT ANTI JOIN on a recent partition),
   with the target table.
7. **Usage notes**: recommended filters (partition column), known pitfalls (soft deletes, late data, currency,
   VAT), downstream dashboards.

## Output format
```markdown
# <catalog.schema.table>
_Purpose: <one line> · Grain: one row = <…> · PK: <cols> (verified: yes/no) · Partitioned by: <cols>_
_Owner: <from metadata> · Rows: <n> · Date range: <min → max> · Refreshed: <pattern> · Documented on <YYYY-MM-DD>_

## Columns
| Column | Type | Definition | Values / pattern | NULL % | Sensitivity | Source of definition |
|--------|------|-----------|------------------|--------|-------------|----------------------|

## Relationships
| Column | → Table.column | Cardinality | Orphans (recent partition) |
|--------|----------------|-------------|----------------------------|

## Usage notes
- Always filter on <partition col>.
- <pitfall>

## Downstream
- <dashboard / data product links>

## To confirm with the owner
- <column> — <question>
```

## Quality checks
- Every column from `information_schema.columns` appears exactly once in the table.
- Each definition names its source (comment, doc, code) or is marked *to confirm*.
- No sample values are printed for columns flagged PII or sensitive.
- The grain and primary key are verified by a duplicate check or labeled unverified.
- Profiling numbers come from queries run on the stated date.

## Guardrails
- Read-only queries only; do not add comments or tags to the table (propose `COMMENT ON` statements as text for the
  owner if useful, never run them).
- Profile with aggregates; never export rows containing personal data.
- Respect access rights: document only tables the user can describe; list inaccessible ones separately.
- Do not invent business meanings for columns; uncertain definitions stay *to confirm*.

## Example
Input: "Document the sales lines table in our sandbox schema for the new analysts"
→ Header with grain "one row = one ticket line", PK verified by duplicate check, partition on the sale date.
Customer identifier flagged *PII indirect* with no sample values shown; a status code column lists its 6 values with
counts; two columns whose meaning is not in comments, docs or code are in "To confirm with the owner".
