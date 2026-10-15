---
name: monthly-finance-commentary
description: "Writes the monthly financial commentary for management on a P&L (company, country, region, store, sport or business unit): headline, KPI table vs budget, forecast and last year for the month and year to date, sales and margin bridge, cost and operating result drivers, one-offs and timing effects, cash and stock if available, outlook, risks and opportunities, and the asks. Use whenever a controller, finance business partner or manager prepares month-end reporting, a monthly business review or the finance section of a management pack, even if they only say 'write the comments on the P&L'. Triggers - monthly commentary, finance commentary, month-end report, P&L commentary, management report, MBR, flash report, commentaire financier, commentaires du mois, clôture mensuelle, reporting mensuel, analyse du compte de résultat, revue mensuelle."
---

# Monthly finance commentary

Gives management the story behind the monthly numbers in one page: how we landed, why, what is one-off, what it
means for the year, and what decision or help is needed.

## When to use
- Month-end close: commentary for a management pack, a country or region review, a store or sport P&L.
- Preparing the finance part of a monthly business review.
- Rewriting raw controlling notes into a concise narrative for leaders.
- Not for: the detailed line-by-line variance and PVM work (use `budget-variance-analysis`, then feed it here),
  a sales-only forecast narrative (use `sales-forecast-commentary`), or a generic executive summary of any document
  (use `executive-summary-writer`).

## Inputs
- Scope and month (required).
- P&L actuals with comparisons: budget, latest forecast, N-1, for month and year to date (required; Databricks,
  Tableau or Drive pack, else pasted).
- Known explanations from controllers or business owners (optional, strongly recommended).
- Audience and length (optional, default: executive, one page) and the company's P&L line names (optional; reuse
  those found in the pack, do not rename lines).

## Sources
1. **Databricks (SQL or Polco)**: P&L by line, scope and month; sales units, like-for-like flags, stock and cash
   indicators if available. Show queries.
2. **Tableau**: the official finance dashboard, to reconcile totals with what management sees.
3. **Drive**: last month's commentary (style, recurring topics), the reporting pack, forecast files, closing notes,
   accrual and one-off lists.
4. **Gmail, Chat and Slack**: explanations from controllers and business owners, known events (weather, sport
   events, supplier price increases, store openings or closures).
5. **Confluence**: KPI definitions (e.g. like-for-like scope rule, gross margin definition) to use the right
   formulas.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Reconcile first**: totals from the data equal the official dashboard or pack; if not, stop and report the gap
   before writing.
2. Build the **KPI table**: net sales, like-for-like sales growth (if the definition is found), gross margin amount
   and rate, operating costs, operating result (use the pack's names), stock, cash or working capital if provided.
   Month and YTD, vs budget, forecast and N-1, in amount and %.
3. Write the **headline** (2 lines): result vs the main reference and the one or two drivers that explain most of it.
4. **Sales bridge**: N-1 or budget → actual, split into volume, price, mix, scope (openings / closures), FX and
   calendar (trading days, holiday shifts); reuse a `budget-variance-analysis` output if available.
5. **Margin and costs**: gross margin rate change in basis points with its drivers (mix, promotions, purchase price,
   logistics, markdowns); cost lines above materiality with rate vs volume explanation.
6. Tag **one-offs and timing** explicitly and give the underlying (normalized) view when they are material; never
   bury a one-off inside "performance".
7. **Outlook**: full-year landing vs budget based on the latest forecast if provided, and what changed vs last month.
   Risks and opportunities with an amount only if sourced, else qualitative.
8. **Asks**: decisions or support needed from management (max 3).
9. Style: numbers first, active voice, one idea per bullet, no adjectives without numbers ("strong" → "+6.2 % vs
   N-1"), consistent units (k€ or M€, one decimal), and basis points for rates.

## Output format
```markdown
# <Scope> — financial commentary <Month YYYY>
_Units <k€ / M€> · references: budget <version>, forecast <version>, N-1 · reconciled with <dashboard / pack> ✓ · sources: <links>_

**Headline:** <operating result vs budget and N-1 + main drivers, 2 lines>

## Key figures
| KPI | Month | vs Bud | vs Fcst | vs N-1 | YTD | YTD vs Bud | YTD vs N-1 |
|-----|-------|--------|---------|--------|-----|------------|------------|

## Sales
- <bridge: volume / price / mix / scope / FX / calendar, with amounts>
## Gross margin
- <rate change in bp and drivers>
## Costs and operating result
- <material lines, rate vs volume>
## One-offs and timing
| Item | Amount | Line | Reverses when |
|------|--------|------|---------------|
Underlying operating result: …
## Cash and stock (if available)
## Outlook
- Full-year landing: … (vs budget …) · change vs last month: …
- Risks: … · Opportunities: …
## Asks to management
1. …
```

## Quality checks
- Totals reconcile with the official dashboard or pack, and the reconciliation status is shown.
- Every number in the text matches the KPI table; variances are recomputable (actual − reference).
- Margin rate changes are in basis points and computed on the same definition as the pack.
- One-offs are listed with amounts, and the underlying view is shown when they are material.
- No adjective stands without a number; the text fits one page.
- Forward-looking amounts come from the forecast file or are left qualitative.

## Guardrails
- Financial results are confidential and may be price-sensitive: keep the commentary to its intended audience, and
  never post it in open channels.
- Never invent figures, explanations, forecasts or KPI definitions; unexplained variances are written as "under
  analysis with <owner>".
- Do not name individual teammates as the cause of results; refer to scopes, decisions and events.
- Draft only: do not email or publish the commentary, or update any reporting file, without explicit confirmation.
