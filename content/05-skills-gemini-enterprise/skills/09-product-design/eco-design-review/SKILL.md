---
name: eco-design-review
description: "Reviews a sport product concept or an existing product through eco-design levers: materials and their mix, material efficiency and weight, durability, repairability and spare parts, disassembly and mono-material choices, packaging and transport volume, use phase and end of life (second-hand, rental, take-back, recycling). Produces questions, improvement options and trade-offs with performance, cost and safety, and says what needs a life cycle assessment, without inventing impact figures. Use whenever a product team designs, redesigns or challenges a product's environmental footprint, even if they only ask 'how can this be more sustainable'. Triggers - eco-design review, ecodesign, sustainable product design, repairability, durability review, circular design, revue écoconception, écoconception produit, réparabilité, durabilité produit, mono-matériau, réduire l'impact d'un produit, fin de vie produit."
---

# Eco-design review

Challenges a product concept lever by lever, so the team sees where the environmental footprint is decided (mostly at
design time), which options exist, what they cost in performance or price, and what must be measured before any claim.

## When to use
- At concept or design-freeze stage, as a structured challenge before choices are locked.
- An existing product is being redesigned and the team wants durability or repair improvements.
- A product has high return or repair rates on one component and the team wonders if design is the cause.
- Not for: checking a marketing environmental claim (use `green-claim-checker`), designing repair, rental or
  second-hand offers (use `circular-offer-ideas`), collecting supplier sustainability data (use `csr-data-request`)
  or framing the product (use `product-brief`).

## Inputs
- Product concept or current product: bill of materials, components, construction, sketches or tech pack (required).
- Target practitioner and expected use intensity and lifetime (required; from the brief if found).
- Existing LCA, material data or durability test results (optional, default: none; say so).
- Constraints: price target, norms, supplier and process limits (optional).

## Sources
1. **Drive and Confluence**: product brief, bill of materials or tech pack, internal eco-design guidelines,
   material libraries, LCA results, durability and repair test reports; use internal criteria and wording if found.
2. **Databricks (SQL or Polco)**: return, after-sales and repair reasons by component for the current or nearest
   product (e.g. "top 10 repair reasons for model X, by part"); show the query.
3. **Airtable**: spare parts lists, material or supplier bases if the team keeps them.
4. **Jira**: design decisions and open issues on the product project.
5. **Slack, Chat and Gmail**: workshop or repair teams' feedback on failure modes.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Map the product**: list components with material, mass share if known, joining method (stitched, glued,
   welded, screwed, clipped), and expected lifetime of each. Flag the parts likely to fail first (from repair data).
2. **Find the hotspots**: where impact is likely concentrated. Without an LCA, rank qualitatively from known drivers:
   mass of each material, energy-intensive processes (e.g. dyeing, coating, metal parts), short lifetime, and parts
   that make the whole product unusable when they fail. Mark the ranking as *qualitative, to confirm by LCA*.
3. **Review each lever** with questions and options:
   - **Materials**: fewer material types, recycled or bio-based options with equal performance, avoid coatings or
     treatments that block recycling, solution- or dope-dyeing versus piece dyeing where relevant.
   - **Material efficiency and weight**: offcut reduction (pattern nesting), part consolidation, lighter without
     losing durability.
   - **Durability**: reinforce the first-failing parts, abrasion and UV resistance, timeless design, adjustable fit to
     extend use (growing children, changing bodies), care instructions that extend life.
   - **Repairability**: standard fasteners instead of glue, replaceable wear parts (zips, buckles, soles, poles,
     straps), spare parts availability, repair instructions, tools a store workshop has.
   - **Disassembly and recyclability**: separable materials, mono-material sub-assemblies, material marking,
     no mixed laminates where avoidable.
   - **Packaging and transport**: remove or reduce, mono-material packaging, folded or nested volume to fit more per pallet.
   - **Use phase**: washing frequency and temperature, energy for powered products, consumables.
   - **End of life and second life**: fit for second-hand (cleanable, condition easy to assess), rental (robust,
     sizable, quick check), take-back and recycling routes.
4. **Write trade-offs** explicitly for each option: effect on performance, safety, weight, price, lead time, and on
   other levers (e.g. recycled content may reduce abrasion resistance; mono-material may cost waterproofness).
5. **Prioritize** options in a matrix: expected benefit (high / medium / low, qualitative and justified) × ease
   (cost, supplier, process change). Quick wins first, then the big bets that need an LCA or a test.
6. **List what to measure**: LCA scope (functional unit, e.g. "one season of weekly use", which is set by the team),
   durability tests, repair time trials, and the data owners.
7. **Check regulation flags**: whether applicable product rules (e.g. EU ecodesign and digital product passport
   requirements, national information requirements such as the French AGEC law) need review; route to the
   compliance owner without concluding.

## Output format
```markdown
# Eco-design review — <product> (<stage: concept / redesign>)
_Sources: <BOM / brief / LCA / repair data links> · LCA available: <yes, link / no> · Assumptions: <one line>_

## Summary
<3 bullets: main hotspot (qualitative), best quick win, biggest trade-off to decide>

## Product map
| Component | Material | Joining | Expected life | Failure data |
|-----------|----------|---------|---------------|--------------|

## Lever review
| Lever | Current state | Question / issue | Option | Trade-off |
|-------|---------------|------------------|--------|-----------|
| Materials | | | | |
| Durability | | | | |
| Repairability | | | | |
| Disassembly | | | | |
| Packaging & transport | | | | |
| Use phase | | | | |
| End of life / second life | | | | |

## Priorities
| Option | Benefit (qual.) | Ease | Why | Next step |
|--------|-----------------|------|-----|-----------|

## To measure before any claim
- LCA: <scope, functional unit to agree, owner>
- Tests: <durability / repair trials>

## Flags for compliance or claims
- …
```

## Quality checks
- No CO2, water, energy or percentage reduction figure appears unless it comes from a cited LCA or data source.
- Every lever has at least one question or option; empty levers say "not applicable" with a reason.
- Every option has its trade-off stated, including any safety or norm impact.
- Priorities use the qualitative scale with a one-line justification.
- Repairability options name the specific part and how it would be replaced.

## Guardrails
- Never invent impact figures, recycled-content percentages, lifetimes or LCA results; write *to measure*.
- No option may weaken a safety or protective function without explicit validation by the safety or quality owner.
- The review does not authorize environmental claims; any external wording goes through `green-claim-checker`
  and the legal or sustainability owner.
- Do not name suppliers' performance or materials as facts unless they come from a supplier document in the sources.
