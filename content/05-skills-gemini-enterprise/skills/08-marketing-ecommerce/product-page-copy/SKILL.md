---
name: product-page-copy
description: "Writes e-commerce product page copy from the product data sheet: SEO title, short pitch, benefit bullets by sport usage, technical specifications copied only from the source, usage and care tips, FAQ and meta title and description. Use whenever someone needs a product page, product description, PDP copy, bullet points or marketplace listing for a sport product, or wants to improve a page that converts badly, even if they only paste a spec sheet and say 'make it sell'. Triggers - product page, product description, PDP copy, product bullets, listing copy, rewrite product page, fiche produit, description produit, texte fiche produit, rédiger une fiche produit, page produit, argumentaire produit, bullet points produit."
---

# Product page copy

Turns a product data sheet into a page that answers the shopper's real question: "will this work for *my* practice?"
Benefits lead, features prove them, and every technical fact is traceable to the data sheet.

## When to use
- A new product needs its page before launch, or a page has a low conversion or high return rate.
- A data sheet must be adapted for a marketplace or a new country.
- Reviews show recurring questions the page does not answer.
- Not for: translating an existing page (use `translation-localizer`), the full SEO article around a topic (use
  `seo-content-brief`), mining reviews in depth (use `product-review-insights`) or checking tone only (use
  `brand-voice-checker`).

## Inputs
- Product data sheet or reference: name, brand (for example Quechua, Kalenji, Kiprun), specs, materials, sizes,
  weight, care (required). Search Drive and Confluence before asking. If it is announced (« jointe ») but absent,
  say so in one line, ask for it, and still return the full Output format with the title, pitch structure, SEO
  keyword proposals and `[TO CONFIRM: …]` in every spec slot; never answer with the question alone.
- Target practice and level (optional, default: from the data sheet's intended use).
- Market and language, page template and character limits (optional, default: the template found in Drive, else
  title ≤ 70 characters, meta description ≤ 155 characters).
- Target keywords (optional, default: proposed and marked *to validate with search data*).

## Sources
1. **Drive and Confluence**: product data sheet, product brief, test reports, size guide, care instructions,
   brand and copy guidelines, page templates.
2. **Databricks (SQL or Polco)**: page metrics if available (conversion, return rate and return reasons, on-site
   search terms that lead to the product). Show the query used.
3. **Airtable**: product information or content tracker with the validated attributes.
4. **Slack, Chat, Jira**: open questions from the product team, content tickets.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Extract a fact table** from the data sheet: attribute, value, unit, source. Anything missing stays
   *missing*. This table is the only source for specs in the copy.
2. **Define the usage context**: sport, terrain, weather, level, duration (for example "2-person hiking tent for
   summer treks, 2–3 nights, valley campsites"). Write it from the data sheet's intended use, not from imagination.
3. **Translate features into benefits** with *feature → so that → for whom/when*: "Fresh&Black fabric → keeps the tent
   darker and cooler → sleep after sunrise on a summer trek" (only if the feature exists in the sheet). Limit to
   4–6 bullets, ordered by the shopper's top decision criteria.
4. **Title**: brand + product type + key differentiator + main use (for example "Kiprun trail running shoes – grip on
   wet rock – men"). Put the main keyword at the start; no keyword stuffing.
5. **Answer objections** found in reviews or return reasons (sizing, waterproofness, weight) inside the bullets or the
   FAQ. Each FAQ answer cites the fact table.
6. **Limits of use**: say what the product is not designed for (for example "not for winter mountaineering"). Honest
   limits reduce returns.
7. **SEO and accessibility**: meta title, meta description with a reason to click, image alt text that describes the
   picture (not keywords).
8. Run the claims check (Guardrails) and list the facts to confirm with the product team.

## Output format
```markdown
**<Product name> · <market/language> · template: <found link or default>**
_Assumptions: <one line>_

### Title (≤ 70 char)
<title>

### Pitch (2 sentences)
<who it is for + main benefit>

### Why you'll like it
- **<Benefit>** — <feature that proves it>
- … (4–6)

### Technical specifications
| Attribute | Value | Source |
|-----------|-------|--------|

### Designed for / not designed for
- ✅ … · ❌ …

### Use and care
- …

### FAQ
**<Question from reviews or search>** — <answer> _(source: …)_

### SEO
- Meta title: … · Meta description (≤ 155 char): …
- Main keyword: … · Secondary: … _(to validate with search data)_
- Image alt texts: 1. … 2. …

### Facts to confirm
- …
```

## Quality checks
- Every number, material, certification or rating in the copy appears in the fact table with its source.
- Each benefit bullet is tied to a feature present in the data sheet.
- The title and meta description respect the character limits.
- At least one "not designed for" line exists.
- No superlative or comparison ("best", "lightest", "warmest") without a cited proof.

## Guardrails
- Never invent specs, ratings (waterproof column, temperature comfort, weight), prices, certifications or awards.
  Missing data stays a placeholder: `[TO CONFIRM: weight]`.
- Safety-related products (helmets, climbing gear, life jackets, child seats): quote standards and warnings exactly
  as in the source, never paraphrase them.
- Environmental claims ("recycled", "eco-designed", "lower impact") go through `green-claim-checker`.
- Do not copy competitor product copy. Do not publish; the user validates and publishes.
