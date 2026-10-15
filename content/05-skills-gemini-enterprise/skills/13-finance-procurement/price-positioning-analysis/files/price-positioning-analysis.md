---
name: price-positioning-analysis
description: "Analyzes price positioning against competitors from provided or connected price data: like-for-like product matching with match quality, price index per product (own price / competitor price × 100), weighted index per family and sport, gap distribution, regular vs promotional prices, key value items, price ladder coherence, and recommendations for the pricing team. Use whenever someone asks whether a range is well priced, how prices compare with a competitor, where the price gaps are, or prepares a pricing review, even if they only paste a price list. Triggers - price index, price positioning, price comparison, competitor prices, price gap, price check, KVI, pricing review, indice de prix, positionnement prix, comparaison de prix, relevé de prix concurrents, écart de prix, sommes-nous bien placés en prix."
---

# Price positioning analysis

Tells a pricing, category or sport team where its prices stand against competitors on comparable products, which
gaps matter for customers and sales, and what to look at first.

## When to use
- Periodic price-positioning review of a sport, family or range against named competitors.
- A competitor price move, or a sales drop where price is suspected.
- Building or checking the price ladder (entry, mid, premium) of a range.
- Not for: a general competitor watch on launches and news (use `competitor-watch`), a feature-by-feature product
  comparison (use `competitive-product-teardown`), or a B2B customer quotation (use `b2b-proposal-builder`).

## Inputs
- Scope: sport, family or product list, country or channel (required).
- Own prices and competitor prices with capture date and source (required; from Databricks, Drive or pasted data;
  never collected by the model from memory).
- Sales weights: units or revenue per product for the weighted index (optional, default: unweighted, stated).
- Target index or positioning rule (optional; look for it in Drive or Confluence; never assumed).

## Sources
1. **Databricks (SQL or Polco)**: own regular and promotional prices, sales units and revenue by product, competitor
   price tables if the company has them. Show queries and the price capture date.
2. **Drive**: competitor price surveys (relevés de prix), pricing rules or positioning guidelines, product data sheets
   for matching specs.
3. **Tableau**: existing pricing or competitiveness dashboards, to reconcile.
4. **Confluence and Chat / Slack**: pricing team methodology notes, recent competitor moves reported by stores.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Match products like for like**: same use, key specs (e.g. waterproofing in mm, weight, capacity, material),
   size or pack. Grade each match: **A exact / equivalent** (same use and specs within tolerance), **B close**
   (one meaningful spec differs), **C indicative** (same price tier only). Compute indices on A and B only; report C
   separately.
2. Normalize prices: same currency, VAT included or excluded consistently, per unit when pack sizes differ, same
   capture date window (state it), regular vs promotional price kept separate.
3. **Price index per product** = own price / competitor price × 100 (100 = parity; < 100 = cheaper). Gap = own −
   competitor in currency and in %.
4. **Aggregate index** per family, sport or competitor: weighted = Σ (own priceᵢ × qᵢ) / Σ (competitor priceᵢ × qᵢ)
   × 100 with qᵢ = own units sold (state the weighting). Also show the unweighted median of product indices and the
   coverage (% of revenue matched).
5. **Distribution**: count of products by band (< 90, 90–97, 97–103, 103–110, > 110). A family average near 100 can
   hide strong outliers on key items.
6. Identify **key value items (KVI)**: high-volume, high-visibility products customers use to judge prices (from sales
   ranks or a list in Drive). Positioning on KVIs matters more than on the long tail.
7. Check the **price ladder** of the own range: entry / mid / premium steps are coherent (each step brings visible
   benefits) and do not overlap competitor tiers in confusing ways.
8. Write **recommendations** as items to review, not price changes: products above the target band on KVIs,
   products far below with potential margin room, missing entry price points, ladder gaps; quantify revenue at stake
   only from sourced sales.

## Output format
```markdown
# Price positioning — <scope> vs <competitors> · prices captured <dates>
_Prices <incl. / excl. VAT>, <currency> · weighting <units / none> · coverage <x % of revenue matched> · sources: <links>_
**Headline:** weighted index <…> vs <competitor> (<cheaper / parity / more expensive>) · KVIs: <…> · <n> items to review

## Index by family / competitor
| Family | Competitor | Weighted index | Median index | Matched products (A/B) | Coverage % |
|--------|-----------|----------------|--------------|------------------------|------------|

## Distribution of product indices
| Band | < 90 | 90–97 | 97–103 | 103–110 | > 110 |
|------|------|-------|--------|---------|-------|

## Key value items
| Product | Own price | Competitor product (match grade) | Comp. price | Index | Gap |
|---------|-----------|----------------------------------|-------------|-------|-----|

## Price ladder
| Tier | Own products / price points | Competitor price points | Comment |
|------|-----------------------------|------------------------|---------|

## Items to review
| Product | Issue | Evidence | Revenue at stake (sourced) | Suggested review |
|---------|-------|----------|---------------------------|------------------|

## Method and limits
- Matching rules, excluded C matches, promo handling, capture dates.
```

## Quality checks
- Every index can be recomputed from the two prices shown (own / competitor × 100).
- Weighted indices state the weights used and coverage; C-grade matches are excluded from indices.
- All prices in one comparison share currency, VAT basis, unit and capture window.
- Promotional and regular prices are never mixed in the same index.
- Every recommendation cites the products and figures it rests on.

## Guardrails
- Competition law: use only public or legitimately obtained competitor prices; never suggest contacting competitors,
  exchanging price information or aligning prices with them.
- Never invent competitor prices, own prices or positioning targets; missing data stays missing.
- Pricing decisions belong to the pricing owners; output recommendations to review, not new prices.
- Margin, cost and sales data are confidential; keep them out of anything that could leave the company.
