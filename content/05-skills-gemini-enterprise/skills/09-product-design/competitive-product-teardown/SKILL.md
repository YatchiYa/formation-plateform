---
name: competitive-product-teardown
description: "Compares competitor products with our own, feature by feature and benefit by benefit, using only the sources provided or found (product pages, data sheets, lab or field test reports, team teardown notes, reviews, app screenshots): claimed versus measured specs, price observed with date, design and construction choices, user experience, durability and repair signals, then table stakes, differentiators, gaps and opportunities. Works for physical sport products and digital products. Use whenever a team benchmarks a competitor product or app, even if they just ask 'how does ours compare to X'. Triggers - competitive teardown, product benchmark, compare with competitor product, feature comparison, competitor analysis product, benchmark concurrent, comparatif produit, analyse produit concurrent, démontage produit concurrent, benchmark fonctionnel, comparer notre produit."
---

# Competitive product teardown

Puts our product next to competitors on what matters to the practitioner, separates what brands claim from what was
measured or observed, and ends with the gaps and opportunities a product team can act on. Every cell has a source.

## When to use
- A new product or app feature is being framed and the team needs the competitive reference.
- A competitor launched a product that customers or stores mention.
- A teardown session happened (physical disassembly, app walkthrough) and the notes need structuring.
- Not for: a market-level competitor news digest (use `competitor-watch`), a sales battlecard (use
  `competitive-battlecard`), price index analysis across a range (use `price-positioning-analysis`) or mining our own
  reviews (use `product-review-insights`).

## Inputs
- Our product (model or app feature) and the competitor products to compare, max 5 (required).
- Sources: links, PDFs, teardown notes, test reports, screenshots (required; also search Drive and Confluence).
- Comparison criteria (optional, default: derived from the target practitioner's jobs in the product brief).
- Market and date of observation (optional, default: country of the user, today).

## Sources
1. **Drive and Confluence**: the product brief, internal lab and field test reports on competitor products, teardown
   notes and photos, previous benchmarks (to show what changed).
2. **User-provided links and files**: competitor product pages, data sheets, manuals, app store pages, screenshots.
3. **Databricks (SQL or Polco)**: our product's sales, ratings, return and repair reasons, for the "our product" column.
4. **Slack, Chat and Gmail**: store or customer feedback mentioning the competitor product.
5. **Airtable**: benchmark bases the team may keep.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Define criteria from the practitioner**, not from the spec sheet: take the main jobs and benefits from the
   brief (e.g. for a trail shoe: grip on wet rock, protection, fit, weight, durability of the outsole, repairability,
   price). Add 2–3 hygiene criteria (availability of sizes, warranty, after-sales).
2. **Collect evidence per cell** and tag its type:
   - *Claimed*: brand statement or data sheet.
   - *Measured*: our lab or field test, with protocol reference.
   - *Observed*: teardown, hands-on, app walkthrough by the team.
   - *Reported*: reviews or customer feedback (cite volume and period).
   Never upgrade a claim to a fact. If no source, write "no data".
3. **Teardown lens** for physical products (when notes or photos exist): materials and their combinations, assembly
   methods (glued, stitched, welded, screwed, clipped), number of components, replaceable parts, visible weak points,
   packaging. For digital products: key flows step count, onboarding, personalization, accessibility, offline use,
   paywalls or account walls.
4. **Classify each criterion**: *table stakes* (everyone does it, missing it hurts), *differentiator* (one player
   stands out, practitioners value it), *irrelevant* (no evidence users care). Use our research or reviews to justify.
5. **Write gaps and opportunities**: where we are behind on a table stake (fix), where nobody serves a strong pain
   (opportunity), where we lead (protect and communicate, subject to `green-claim-checker` for any environmental
   claim). Each one links to evidence.
6. **State limits**: products not tested in the same conditions, prices from different dates or channels, sample sizes.

## Output format
```markdown
# Teardown — <our product> vs <competitors> (<market>, observed <date>)
_Sources: <links> · Criteria from: <brief link / assumption>_

## Verdict
<3 bullets: where we win, where we lose, the biggest opportunity>

## Comparison
| Criterion | Our product | Competitor A | Competitor B | Class |
|-----------|-------------|--------------|--------------|-------|
| <criterion> | <value> (measured, [src]) | <value> (claimed, [src]) | no data | table stakes |
| Price observed | <price, channel, date> | | | |

## Construction / experience notes
- <Competitor A>: <materials, assembly, repairable parts / key flow notes> — <source>

## Gaps & opportunities
| Type | Description | Evidence | Suggested next step |
|------|-------------|----------|---------------------|
| Gap to fix | | | |
| Opportunity | | | |
| Lead to protect | | | |

## Limits of this comparison
- …
```

## Quality checks
- Every cell has an evidence type (claimed, measured, observed, reported) and a source, or says "no data".
- Prices show channel and observation date.
- Criteria trace back to practitioner jobs; at least one durability or repair criterion for physical products.
- Every gap or opportunity links to evidence in the table.
- The limits section names at least one comparability issue.

## Guardrails
- Use only sources that are public or legitimately held by the team; never suggest obtaining confidential competitor
  information or contacting competitor employees for it.
- Do not present claimed specs as measured, and never invent test results, prices or materials.
- No disparaging wording about competitors; the teardown is internal and factual. External comparative claims need
  legal review.
- Do not copy competitor designs, logos or text into recommendations; opportunities describe user needs, not imitations.
