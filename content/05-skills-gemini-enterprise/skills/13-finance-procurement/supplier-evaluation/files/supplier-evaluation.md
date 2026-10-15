---
name: supplier-evaluation
description: "Evaluates and compares suppliers with a weighted scorecard: knock-out criteria first (social compliance, mandatory certifications, sanctions), then quality, total cost of ownership, delivery and lead time, capacity, social and environmental performance, innovation and risk (financial, concentration, geopolitical), each scored 1-5 on written anchors with evidence, plus weight sensitivity, risk view and development actions. Use whenever a buyer or category team selects, reviews, renews or compares suppliers or service providers, even if they only ask 'which supplier is best'. Triggers - supplier evaluation, supplier scorecard, vendor comparison, supplier selection, supplier performance review, vendor rating, évaluation fournisseur, comparer des fournisseurs, notation fournisseur, sélection fournisseur, revue de performance fournisseur, grille de cotation."
---

# Supplier evaluation

Gives a buyer a fair, documented comparison of suppliers where every score has evidence, the non-negotiables are
checked before price, and the result does not flip when a weight moves by a few points.

## When to use
- Selecting a supplier after an RFQ / RFP, or shortlisting candidates.
- Annual or quarterly performance review of current suppliers (quality, delivery, compliance).
- Renewal decision, dual-sourcing or de-risking a single-source category.
- Not for: writing the RFQ itself (use `supplier-rfq-builder`), justifying one purchase (use
  `purchase-request-justification`), summarizing a supplier contract (use `contract-summary`), or collecting CSR data
  from suppliers (use `csr-data-request`).

## Inputs
- Category, need and supplier list (required).
- Evidence per supplier: offers, quality data, delivery performance, audit results, certificates (required; searched
  in Drive, Databricks, Airtable and Gmail before asking).
- Criteria and weights (optional; reuse the procurement team's grid if found in Drive or Confluence; else propose
  defaults labeled *proposal — buyer to validate before scoring*).
- Evaluation type: selection (new) or performance review (existing) (optional, default: inferred).

## Sources
1. **Drive and Confluence**: procurement policy and evaluation grids, RFQ and published weights, offers, audit
   reports, certificates, supplier code of conduct.
2. **Databricks (SQL or Polco) and Tableau**: on-time-in-full (OTIF), lead time, defect / return rates, quality
   incidents per supplier, spend and share of spend.
3. **Airtable**: supplier registers or trackers (status, audit dates, contacts) if the team uses one.
4. **Gmail and Chat / Slack**: offers, clarifications, incident exchanges (cite, do not paste contents).
5. **Jira**: quality or supply incidents linked to the supplier.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Fix the grid before looking at scores**: criteria, weights summing to 100 and 1–5 anchors. For a selection after
   an RFQ, use exactly the grid announced to bidders.
2. **Knock-out gate** (pass / fail, not weighted): valid social compliance audit or code-of-conduct acceptance,
   mandatory certifications or product safety conformity, no sanctions or legal exclusion, minimum financial
   viability. A fail removes the supplier from scoring or makes it conditional, stated explicitly.
3. Default weighted criteria (*proposal*): Quality 25 (defect rate, certifications, process capability), Total cost of
   ownership 25 (price + logistics + duties + payment terms + quality cost, not unit price alone), Delivery 15 (OTIF,
   lead time, flexibility), Social and environmental 15 (audit grade and corrective actions, environmental data,
   chemical compliance), Risk 10 (financial health, single-site or country concentration, dependency = our share of
   their turnover), Capacity and innovation 10.
4. **Score 1–5** with anchors per criterion: 1 = does not meet requirement, 2 = partially, 3 = meets, 4 = exceeds
   with evidence, 5 = best-in-class with measured evidence. Every score needs an evidence line; no evidence =
   score "n/a" and flagged, not a guess.
5. **Weighted total** = Σ (weight × score) / 5 → out of 100. Show the per-criterion contribution.
6. **Sensitivity**: move each weight ±5 points (rebalance the others proportionally) and report whether the ranking
   changes. If the top two are within 5 points, call it a tie and say what would separate them.
7. **Risk view**: supply risk vs spend impact (Kraljic: strategic, bottleneck, leverage, non-critical) to recommend
   single, dual or multi-sourcing.
8. For performance reviews: trend vs last period, and a **development plan** (corrective actions, dates, KPI).

## Output format
```markdown
# Supplier evaluation — <category> · <selection / review> · <date>
_Grid: <source or *proposal*> · evaluators: <roles> · sources: <links>_
**Outcome:** <leader> at <score>/100, <gap> pts ahead · ranking <robust / sensitive to …> · knock-out fails: <…>

## Knock-out gate
| Supplier | Social compliance | Certifications / safety | Sanctions / legal | Financial viability | Result |
|----------|-------------------|-------------------------|-------------------|---------------------|--------|

## Weighted scorecard
| Criterion (weight) | Supplier A | Supplier B | Supplier C |
|--------------------|-----------|-----------|-----------|
| Quality (25) | 4 — <evidence> | | |
| **Total /100** | | | |

## Total cost of ownership
| Cost element | A | B | C |
|--------------|---|---|---|

## Sensitivity
| Weight change | Ranking | Changed? |
|---------------|---------|----------|

## Risk and sourcing strategy
- Kraljic position: … → <single / dual / multi-sourcing>
- Key risks: …

## Recommendation and next steps
- <decision for the buyer / committee> · conditions · development actions with dates
- Missing evidence (n/a scores): …
```

## Quality checks
- Weights sum to 100; each total equals Σ (weight × score) / 5 and is recomputable from the table.
- Every score has an evidence line with a source; missing evidence is "n/a", never a default 3.
- Knock-out criteria were applied before scoring, and failures are explained.
- TCO includes at least price, logistics and quality cost, with the same scope for all suppliers.
- Sensitivity result is stated; ties within 5 points are called ties.

## Guardrails
- Procurement fairness: same grid, same evidence requests and same scoring rules for every supplier; never change
  weights after seeing offers; record any conflict of interest the user mentions.
- Supplier offers, prices and audit results are confidential: never share one supplier's data with another, and keep
  the scorecard to the evaluation team.
- Do not invent audit grades, certifications, financial ratios or prices; social and environmental claims need a
  document.
- The skill supports the buyer's decision; it does not award contracts or notify suppliers. Draft any supplier
  message for explicit confirmation first.
