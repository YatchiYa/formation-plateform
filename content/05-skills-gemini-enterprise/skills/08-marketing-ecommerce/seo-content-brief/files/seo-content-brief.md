---
name: seo-content-brief
description: "Produces an SEO content brief for a writer: target query and search intent, SERP format analysis, keyword cluster with a pillar and supporting pages, H1 to H3 outline, questions to answer, internal links to product and category pages, E-E-A-T evidence from real sport expertise, and on-page specs. Use whenever someone plans a blog article, buying guide, advice page, category text or landing page that should rank on Google, or asks why a page does not rank, even if they do not say 'SEO'. Triggers - SEO brief, content brief, keyword cluster, buying guide, blog article, search intent, topical authority, brief SEO, brief de contenu, guide d'achat, article conseil, mots-clés, intention de recherche, cocon sémantique."
---

# SEO content brief

Gives a writer everything needed to produce the best answer on the web for one search intent, written by people who
actually practice the sport. Rankings follow usefulness, intent match and demonstrated expertise, not keyword density.

## When to use
- A new advice article, buying guide ("how to choose a hiking tent"), category text or landing page is planned.
- A page loses traffic or never ranked, and needs a rewrite plan.
- A team wants a topical cluster for a sport or season (ski season, trail running).
- Not for: the product page itself (use `product-page-copy`), the editorial review of a finished draft (use
  `document-reviewer`) or the tone check (use `brand-voice-checker`).

## Inputs
- Topic or target query, market and language (required).
- Search data: keyword volumes, Search Console export, current rankings (optional, default: none; volumes are then
  marked *to validate* and never estimated as numbers).
- Existing URL to improve and the site's related pages (optional).
- Internal experts available (product engineers, sport coaches, store teammates) (optional).

## Sources
1. **Drive and Confluence**: SEO guidelines, existing keyword studies, Search Console or ranking exports, editorial
   calendar, product briefs and test reports (for expertise and facts).
2. **Databricks (SQL or Polco)**: on-site search terms, organic landing page traffic and conversion if tracked.
   Show the query used.
3. **Tableau**: organic or content dashboards.
4. **Slack and Chat**: questions customers ask store teammates or customer service (strong long-tail signals).
5. **Jira**: content or SEO tickets for the page.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Classify the intent** of the target query: informational ("how to wax skis"), commercial investigation ("best
   trail running shoes for beginners"), transactional ("buy 2-person tent"), navigational. One page serves one
   dominant intent. If the user cannot share SERP data, state the inferred intent as *assumption* and ask them to
   check the top 10 results for format (guide, list, category page, video).
2. **Build the cluster**: pillar page (broad topic, e.g. "trail running shoes guide") + supporting pages (grip,
   drop, waterproof vs breathable, sizing) linked both ways. Group keywords by shared intent, not by spelling; two
   keywords whose top results are the same pages belong to one page (avoid cannibalization).
3. **Outline**: H1 matching the query, H2s answering the sub-questions in decision order, a short direct answer in the
   first 100 words (featured snippet), comparison table where the shopper compares, FAQ from real questions.
4. **E-E-A-T plan**: *Experience* (field test, photos from real outings), *Expertise* (named author or reviewer with a
   sport or product role, only if confirmed), *Authoritativeness* (cite standards, federations), *Trust* (dates,
   sources, honest limits). Mark each item *available* or *to obtain*.
5. **Internal links**: 3–8 links to category and product pages and to sibling cluster pages, with descriptive anchor
   text. Only URLs found in sources; others are placeholders.
6. **On-page specs**: title tag ≤ 60 characters, meta description ≤ 155, slug, image alt texts, schema type
   (Article, FAQPage, HowTo, Product) as suggestions for the web team.
7. **Success metrics**: target queries, impressions, clicks, CTR, assisted conversions, measured at 4 and 12 weeks.

## Output format
```markdown
# SEO brief — <target query> (<market>, <language>)
_Sources: <links> · Assumptions: <one line>_

## Intent and format
- Dominant intent: <type> · Expected format: <guide/list/category/video> · Evidence: <SERP check or assumption>

## Keyword cluster
| Keyword | Intent | Volume (source) | Page (pillar / support) |
|---------|--------|-----------------|-------------------------|

## Outline
- **H1:** …
- Intro answer (≤ 100 words): …
- **H2:** … → H3: …
- Comparison table: <columns>
- FAQ: …

## E-E-A-T evidence
| Signal | What to include | Status |
|--------|-----------------|--------|

## Internal links
| Anchor text | Target URL | Why |
|-------------|------------|-----|

## On-page specs
Title (≤ 60): … · Meta (≤ 155): … · Slug: … · Schema: … · Word count: <range, justified by SERP>

## Measurement
<queries to track, KPIs, review dates>
```

## Quality checks
- One dominant intent per page, and the outline's first section answers it directly.
- No two pages in the cluster target the same intent.
- Every volume or ranking number has a source; otherwise it says *to validate*.
- Every E-E-A-T item is marked *available* or *to obtain*; no expert is named without confirmation.
- Title and meta respect length limits and contain the main keyword naturally.

## Guardrails
- Never invent search volumes, rankings, competitor traffic or expert names and credentials.
- Product facts in the brief come from data sheets; safety advice (avalanche, altitude, heat) must be sourced and
  reviewed by a qualified expert before publication.
- No doorway pages, hidden text or keyword stuffing; write for people first.
- Environmental claims go through `green-claim-checker`. Draft only: the user validates and publishes.
