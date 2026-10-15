---
name: b2b-proposal-builder
description: "Builds a B2B commercial proposal for sports equipment and services, such as team kits with customisation, school or company equipment, wellbeing programmes or event supplies: executive summary in the customer's words, solution by need, implementation plan (size collection, proofs, delivery, after-sales), options, a pricing table filled only from user or source data, assumptions and terms to confirm. Use whenever a seller must write a quote cover, an offer, a proposal or a 'proposition commerciale' for a club, school, company or association, even if they only ask to 'put together an offer'. Triggers - proposal, commercial offer, quote, sales proposal, team kit offer, pricing table, proposition commerciale, offre commerciale, devis, chiffrage, offre équipement club, proposition pour une école ou une entreprise."
---

# B2B proposal builder

Produces a proposal a buyer can say yes to: it restates their problem, shows how each need is covered, makes
implementation risk-free, and prices only what the seller has actually confirmed.

## When to use
- After discovery, when the customer asked for an offer (e.g. kits for 12 teams of a football club, PE equipment for a
  school, a sport challenge kit for a company's wellbeing week, equipment for a town's summer camps).
- An existing quote needs a proper cover document or options.
- A proposal must be reworked after negotiation.
- Not for: a formal public tender with specifications (use `tender-response-builder`), answering a single objection
  (use `objection-handler`), or the internal investment justification (use `business-case-builder`).

## Inputs
- Customer and their needs, ideally the discovery notes or recap (required; search Drive and Gmail first). A need
  stated in the request is enough: draft the full proposal now with `[to confirm]` for the customer name, items,
  prices and dates, then ask for the price list and gaps in one grouped question after the draft.
- Products or services with quantities, unit prices, discounts, customisation and delivery terms (required for the
  pricing table; if missing, the table keeps placeholders and the gaps are listed).
- Customer's decision criteria and deadline (optional, default: from the recap).
- Proposal template or brand guidelines (optional, default: search Drive; else the structure below).

## Sources
1. **Drive**: the official proposal or quote template, approved offer descriptions, general terms of sale, past
   proposals to similar customers, reference cases with customer permission.
2. **Gmail and Drive notes**: the customer's request, the recap of the last call, exact words describing their needs.
3. **Airtable**: opportunity record (needs, decision criteria, budget signal, decision date).
4. **Confluence**: product, customisation and service rules (minimum quantities, proof process, delivery options),
   if documented. Cite the page; never fill a gap from memory.
5. **Databricks (SQL or Polco)**: the customer's past orders, to anchor quantities on real history.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Restate the need** in the buyer's own words (quotes from the recap) and their success measure, e.g. "every licensed
   player equipped before the first league match on 6 September".
2. **Map need → solution → proof** for each need. Proof is a sourced fact: product feature from an official sheet, a
   reference customer from Drive, a service rule from Confluence. No proof found = say "to confirm".
3. **Design options** (good / better / best, or base + add-ons) so the buyer chooses between our options instead of
   between us and a competitor. Example for a club: A = match kit only; B = match + training kit; C = B + bags and
   balls with club crest. Options differ by scope, never by hidden quality cuts.
4. **Build the pricing table** strictly from inputs: line, reference, quantity, unit price, discount, total, VAT basis.
   Compute totals and show the arithmetic. Any missing unit price, discount or fee stays as `[to confirm]` and goes to
   the gaps list. State the offer validity date only if given.
5. **Write the implementation plan** that removes buyer effort and risk: size collection method and deadline, proof or
   sample approval (e.g. crest and sponsor logo placement), production and delivery dates **only if confirmed**,
   delivery mode (one drop or per team), after-sales and reorder process for late sign-ups.
6. **Write the executive summary last** (≤ 120 words): their goal, our recommended option, why it fits their criteria,
   the total for the recommended option, the decision needed and by when.
7. **Value framing**: express the price per player per season or per pupil when the inputs allow it, and name the cost
   of the status quo using the customer's own numbers. Never invent savings.
8. List **assumptions and points to confirm** internally before sending (pricing approval, lead time, stock, minimums).

## Output format
```markdown
# Proposal — <Customer> · <offer name> · v<n> · <date>

## Executive summary
<≤ 120 words: goal → recommendation → fit → total → decision needed by <date>>

## Your needs
| # | Need (your words) | Success measure |
|---|-------------------|-----------------|

## Our solution
| Need | Solution | Proof |
|------|----------|-------|

## Options
| | Option A | Option B (recommended) | Option C |
|---|---|---|---|
| Scope | … | … | … |
| Total excl. VAT | … | … | … |

## Pricing — Option <X>
| Line | Ref | Qty | Unit price | Discount | Total |
|------|-----|-----|-----------:|---------:|------:|
| … | … | … | [to confirm] | … | … |
| **Total excl. VAT** | | | | | **…** |
_Validity: <date or [to confirm]> · Terms: <link to terms of sale>_

## Implementation
| Step | Who | When |
|------|-----|------|
| Size collection | Club team managers | <date> |

## After-sales and reorders
…

## Next step
<one decision + date + contact>

---
**Internal — remove before sending:** assumptions · items [to confirm] · approvals needed
```

## Quality checks
- Every price, discount, quantity, lead time and date comes from the user or a cited source; otherwise it shows `[to confirm]`.
- Line totals and grand totals are arithmetically correct; VAT basis is stated.
- Every customer need from the recap is covered by a solution row, or explicitly out of scope.
- The executive summary names one recommended option and one dated decision.
- The internal block lists every `[to confirm]` item, and no internal note remains in the customer part.

## Guardrails
- Never invent prices, discounts, lead times, stock, minimum quantities, warranties or certifications. A missing value
  is a placeholder, not an estimate.
- Use the official template and general terms of sale if found; do not draft legal terms yourself.
- References and logos of other customers only if Drive shows they agreed to be cited.
- For a public buyer above the purchasing thresholds or under a formal procedure, stop and route to
  `tender-response-builder`.
- Draft only: do not send the proposal or share the Drive file outside the organisation without user confirmation.
