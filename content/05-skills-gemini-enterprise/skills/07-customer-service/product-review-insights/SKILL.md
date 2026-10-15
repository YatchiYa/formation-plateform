---
name: product-review-insights
description: "Mines customer ratings and reviews of a product or range to give product teams evidence they can act on: rating distribution and trend, pros and cons by sport usage and context, suspected defects with counts and first-seen dates, sizing and fit signals, information gaps on the product page, and prioritized actions for design, quality, product page and service. Use whenever someone asks what customers think of a product, why a rating dropped, or what to improve in the next version, even if they only paste a product name or reference. Triggers - product reviews, review analysis, why is the rating dropping, customer ratings, product feedback, avis produit, analyse des avis, note produit en baisse, retours clients produit, ce que les clients disent du produit, avis clients gamme."
---

# Product review insights

Turns hundreds of product reviews into a clear diagnosis for product, quality and e-commerce teams: what
practitioners love, what fails, in which conditions, and what to change first.

## When to use
- A product's average rating drops or a negative review wave appears.
- Preparing the brief or the next version of a product.
- A range review needs the customer view by product.
- Not for: feedback across all channels and services (use `voice-of-customer-report`), comparing with competitor
  products (use `competitive-product-teardown`), or a full sport universe review with sales and stock (use
  `sport-universe-review`).

## Inputs
- Product name and reference(s), or the range (required).
- Period (optional, default: last 12 months, with the last 3 months highlighted).
- Countries or languages (optional, default: all available, translated to the user's language).
- Version or launch date of the current model (optional, used to split old vs new version).

## Sources
1. **Databricks (SQL or Polco)**: product review and rating tables, if available. Ask Polco e.g. "ratings and review
   texts for product <reference> since <date>, with date, country and rating", or find the table in the catalog and
   query it. Show the table and query used.
2. **Tableau**: product quality or rating dashboards; reuse their definitions.
3. **Jira and Confluence**: known quality issues, corrective actions or product page changes on this reference.
4. **Drive**: product brief, technical sheet and field test reports (to compare promises with feedback).
5. **Gmail / Slack / Chat**: workshop or store feedback threads on the product, as qualitative support.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Profile the data**: N reviews, rating distribution (1–5), average and its trend by month, share with text,
   split by country and by product version. Below 30 reviews → say the insights are indicative.
2. **Tag each review** (or a sample of ≥ 150 if very large) on four axes:
   - Sentiment per aspect: comfort, fit/sizing, durability, performance, weight, ease of use, look, price/value.
   - Usage context: sport, level (beginner to expert), intensity, conditions (weather, terrain, frequency).
   - Defect signal: break, tear, leak, malfunction, with the part concerned and time to failure if stated.
   - Expectation gap: "smaller than expected", "not waterproof as stated", i.e. product page or label issue.
3. **Separate defect from misuse from mismatch.** Defect = fails in intended use; misuse = used outside the
   stated use; mismatch = product fine but the page or advice set the wrong expectation.
4. **Quantify themes**: count, share of negative reviews, average rating of reviews mentioning it, first-seen date.
   A defect theme with ≥ 3 mentions of the same part is a *suspected defect* for quality to investigate.
5. **Sizing signals**: share of "too small / true to size / too large" when mentioned.
6. **Prioritize actions** by impact (share of negatives × severity; safety-related = top) and effort, across four
   owners: Design (next version), Quality (investigation), Product page (information fix), Service (advice, repair,
   spare parts).
7. Compare with the product brief or technical sheet: list promises that reviews contradict or confirm.

## Output format
```markdown
# Review insights — <product> (<reference>) · <period>
**Bottom line:** <2 sentences: rating trend and the main fix>
_Data: <N> reviews (<n> with text) · avg <x.x>/5 · trend <↑↓→> · source: <table/query>_

### Rating trend
| Month | Reviews | Avg rating | % 1–2★ |
|-------|---------|-----------|--------|

### What practitioners love
| Aspect | Mentions | Typical context | Verbatim |
|--------|----------|-----------------|----------|

### What goes wrong
| Theme | Type (defect/misuse/mismatch) | Mentions | % of negatives | First seen | Verbatim |
|-------|-------------------------------|----------|----------------|-----------|----------|

### Sizing and fit
<too small x% · true y% · too large z% (n=…)>

### Promise vs reality
- <claim in brief/page> — <confirmed / contradicted> by <n> reviews

### Actions
| Priority | Owner | Action | Evidence |
|----------|-------|--------|----------|
```

## Quality checks
- Every count and average traces to the stated table, query or file.
- Each "suspected defect" has ≥ 3 mentions of the same part and a first-seen date.
- Defect, misuse and mismatch are not mixed in one theme.
- Verbatims are short, anonymized and translated with the original language noted.
- Insights from fewer than 30 reviews are labeled "indicative".

## Guardrails
- A suspected defect is not a confirmed defect; for safety-related signals (equipment that protects or carries a
  person), recommend immediate review by quality or product safety, without stating a cause.
- No reviewer names, usernames or locations in the output.
- Do not invent ratings, review counts or technical specifications. Missing data → "not available".
- Read only. Jira tickets or page changes are drafts until the user confirms.
