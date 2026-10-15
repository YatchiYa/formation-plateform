---
name: green-claim-checker
description: "Reviews environmental and sustainability claims in product pages, labels, packaging, ads, social posts or press releases against EU consumer law as amended by the Empowering Consumers for the Green Transition directive (EU) 2024/825: flags generic claims (eco-friendly, green, responsible), offset-based neutrality claims, whole-product claims based on one aspect, unverified labels and future pledges, rates each claim red, amber or green, lists the evidence needed and proposes compliant rewrites. Not legal advice. Use whenever someone writes or validates copy mentioning environment, recycled materials, carbon, durability or eco-design, even if they only ask to 'polish' it. Triggers - check green claim, greenwashing check, eco claim, is this claim compliant, carbon neutral claim, vérifier une allégation environnementale, greenwashing, allégation verte, mention écologique, wording éco-conçu, est-ce qu'on peut dire."
---

# Green claim checker

Screens every environmental claim in a piece of copy, says which ones are risky and why, and rewrites them so they
are specific, scoped and backed by evidence. A first-level screen, not legal advice — validate with Legal.

## When to use
- Product page, hangtag, packaging, catalog or campaign copy mentions environmental benefits.
- A press release, social post or store signage talks about recycled materials, CO2, durability or circularity.
- Someone asks whether a wording such as « éco-conçu », "low impact" or "climate neutral" can be used.
- Not for: assessing the eco-design of the product itself (use `eco-design-review`), general brand tone review
  (use `brand-voice-checker`), or writing the product page from scratch (use `product-page-copy`).

## Inputs
- The copy or link to it (required) and where it will appear: product, packaging, ad, B2B, corporate (required).
- Countries of publication (optional, default: EU-wide rules only, national rules flagged as "to check").
- Evidence available: data sheets, LCA, certificates, test reports (optional; searched in Drive/Confluence).

## Sources
1. **Drive and Confluence**: product data sheets (composition by weight), LCA or environmental footprint studies,
   certificates (with scope, holder and validity date), internal claims guidelines or approved-wording lists — if an
   internal guideline exists, apply it and cite it; never invent one.
2. **Airtable or Databricks (SQL MCP or Polco)**: product master data such as composition and recycled-content
   fields, if the user points to them.
3. **Jira and Gmail**: the request ticket or thread, previous Legal or CSR feedback on similar claims.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Extract every claim**: explicit words, implicit ones (leaf or globe icons, green color codes, « nature »
   imagery described in the brief), labels and logos, comparisons ("30 % less CO2"), and future pledges.
2. **Classify** each claim and rate it with these rules (generic-term examples in the Reference):
   - 🔴 **Red** — listed as always unfair after directive (EU) 2024/825 applies (from 27 September 2026):
     generic claim without recognized excellent environmental performance; claim on the whole product or the whole
     company when it concerns one aspect; neutral/reduced/positive GHG impact claim based on offsetting; a
     sustainability label not based on a certification scheme or not set by public authorities; presenting a legal
     requirement as a distinctive feature.
   - 🟠 **Amber** — allowed only if specific and substantiated: recycled content, reduced footprint, durability or
     repairability, future performance (needs a detailed, realistic implementation plan with verifiable targets,
     verified by an independent expert), comparisons (same method, same scope, same period).
   - 🟢 **Green** — specific, scoped, proven, and the proof is identified.
3. **Check substantiation** for amber claims: what exactly (component, % by weight), compared to what (baseline
   product, year), measured how (LCA to ISO 14040/14044, certificate), which scope (cradle-to-gate or full life
   cycle), and can the consumer access the details (link, QR code).
4. **Check labels**: is it a certification scheme with third-party verification, or a self-created logo? Is the
   certificate valid for this product and supplier? Watch for mismatches: a harmful-substances label (e.g. a textile
   chemical-safety test) is not an environmental performance claim.
5. **Rewrite** each red and amber claim: specific + scoped + quantified + evidence reference. Example:
   « Veste éco-responsable » → « Tissu extérieur en polyester <x %> recyclé (<y %> du poids de la veste) », figures from the data sheet.
   « Neutre en carbone grâce à la compensation » → remove the neutrality claim; if relevant, state real reductions
   and describe contributions separately, without implying a product impact.
6. **Flag national rules** to check with Legal for the target countries (for France, for example, the AGEC law bans
   « biodégradable » and « respectueux de l'environnement » or equivalent wording on products and packaging).
7. List the **evidence pack** to file before publication.

## Output format
```markdown
**Green claim check — <asset>, <channel>, <countries>** · Overall: 🔴 <n> · 🟠 <n> · 🟢 <n>
_Not legal advice — validate with Legal before publication._

| # | Claim (as written) | Type | Rating | Why | Evidence needed / found |
|---|--------------------|------|--------|-----|-------------------------|
| 1 | "…" | generic / aspect / offset / label / future / comparative / legal requirement | 🔴 | … | … |

### Compliant rewrites
| # | Before | After | Condition |
|---|--------|-------|-----------|

### Evidence pack to file
- [ ] <document> — <owner> — <status: found (link) / missing>

### To check with Legal
- <national rule or open question>
```

## Quality checks
- Every claim in the copy, including icons and labels, has a row.
- Every red rating cites which category of the directive's prohibited practices applies.
- Every rewrite contains a scope (component or life-cycle stage) and either a number or a named certificate.
- No rewrite adds a figure, certificate or percentage that is not in the sources or user input; missing data is
  shown as "<x %>" with a request.
- The "not legal advice" line is present.

## Guardrails
- Not legal advice. Do not state that a claim is "compliant" — say "lower risk, pending Legal validation".
- Only cite rules you are sure of: directive (EU) 2024/825 amending directives 2005/29/EC (unfair commercial
  practices) and 2011/83/EU (consumer rights). The separate Green Claims directive was only a Commission proposal
  (COM(2023) 166); do not treat it as law — check its status with Legal.
- Never invent environmental data, LCA results or certifications.
- Do not publish or edit the source asset; deliver rewrites as suggestions.

## Reference — typical generic terms (examples, not an exhaustive legal list)
eco-friendly, environmentally friendly, green, nature's friend, ecological, climate friendly, gentle on the
environment, eco, responsible, sustainable (when unqualified), « éco-responsable », « vert », « respectueux de la
planète ». Safer pattern: replace by the specific attribute and its proof.
