---
name: competitor-watch
description: "Produces a dated competitive watch digest from the sources the user provides or that exist in Drive, Gmail, Slack and Confluence: competitor moves (launches, prices and promotions, campaigns, store openings, services, partnerships), each with date, source and confidence, ranked by impact, with implications and suggested responses for marketing and category teams. Use whenever someone asks what competitors are doing, wants a weekly or monthly market watch, spotted a competitor campaign or price move, or prepares a season review, even if they just paste a few links. Triggers - competitor watch, competitive intelligence, market watch, what are competitors doing, competitor news, veille concurrentielle, veille marché, que font les concurrents, actu concurrents, benchmark concurrent, revue concurrence."
---

# Competitor watch

Turns scattered competitor signals into a short, dated digest: what moved, how sure we are, why it matters to us and
what we could do. Facts are sourced; interpretation is labeled as such.

## When to use
- Weekly or monthly market watch for a sport category, a country or e-commerce.
- A competitor launched a product, a campaign or a promotion and the team wants a quick read.
- Before a season (ski, running, back to school) or a promo calendar review.
- Not for: a sales battlecard (use `competitive-battlecard`), a feature-by-feature product comparison (use
  `competitive-product-teardown`), a price index study (use `price-positioning-analysis`) or regulatory news (use
  `regulatory-watch-digest`).

## Inputs
- Scope: competitors, categories or sports, markets (required).
- Period (optional, default: last 7 days for weekly, last 30 days for monthly).
- Sources to read: links, newsletters, reports, screenshots, store visit notes (optional, default: what is found in
  connected sources).
- Audience of the digest (optional, default: marketing and category managers).

## Sources
1. **Gmail**: market newsletters, agency or panel reports, forwarded competitor emails within the period.
2. **Slack and Chat**: market-watch or field channels where teammates post competitor sightings (store visits,
   screenshots, ads).
3. **Drive and Confluence**: previous digests (to spot what is new), market studies, competitor price surveys,
   store visit reports.
4. **Databricks or Tableau**: own sales of the impacted categories over the same weeks, only to size the stake, not
   to prove a competitor effect.
5. Links the user provides. Web content outside these sources is used only if the user supplies it.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Collect signals** in the period: competitor, move type (product, price/promo, campaign, channel/store, service,
   partnership, corporate), date, source link, quote or screenshot reference.
2. **Deduplicate** against previous digests; keep only new moves or real changes.
3. **Rate confidence** for each signal: *confirmed* (official source: press release, competitor site, ad seen),
   *reported* (trade press, panel, newsletter), *unverified* (one field sighting, social rumor).
4. **Score impact** = relevance (core category for us = 3, adjacent = 2, other = 1) × scale (national or online = 3,
   regional = 2, single store = 1). Keep the top 5–8 for the digest; list the rest in one line each.
5. **Implications**: for each top signal, one line of *so-what* labeled as interpretation (threat, opportunity,
   nothing to do) and a suggested response: monitor, adjust message, check price position, accelerate a launch,
   brief stores. Do not recommend matching a price without a margin check.
6. **Patterns**: 1–3 trends across signals (for example several players pushing rental or second-hand in winter
   sports, or trail running launches moving earlier in the year).
7. **Questions** to verify next period.

## Output format
```markdown
# Competitor watch — <scope> · <period>
_Sources checked: <list> · Signals reviewed: <N> · New: <N>_

## Headlines
1. <Competitor> — <move in one line> · <date> · <confidence> ([source](…))
   → So-what (interpretation): … · Suggested response: …
2. …

## All signals
| Date | Competitor | Type | Move | Confidence | Impact | Source |
|------|-----------|------|------|------------|--------|--------|

## Patterns
- …

## To verify next time
- …
```

## Quality checks
- Every signal has a date, a source link or reference, and a confidence level.
- Interpretation lines are labeled and kept separate from facts.
- No signal outside the period unless it is labeled as background.
- Headlines are ranked by the impact score.
- Each suggested response is something a Company team could do, and none commits to a price change.

## Guardrails
- Never invent competitor facts, prices, sales figures or strategies. Unknowns are written as questions.
- Use only legitimate public or provided information; no confidential competitor documents, no information obtained
  by misrepresentation, no scraping instructions.
- Competition law: never suggest coordinating prices or sharing sensitive information with competitors; price
  decisions stay independent.
- Do not name individual competitor employees unless they are public spokespeople quoted in a public source.
