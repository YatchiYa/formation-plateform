---
name: supplier-rfq-builder
description: "Builds a buyer-side RFQ, RFP or RFI pack for goods or services: context and scope, functional and technical requirements (must vs should), indicative volumes, commercial terms and Incoterms, a cost breakdown template, quality and social and environmental requirements, the evaluation grid with weights announced upfront, timeline, Q&A and submission rules, plus the bidder list check and a fair-process checklist. Use whenever someone needs to consult suppliers, get quotes, launch a tender or compare offers fairly, even if they only ask to 'ask three suppliers for a price'. Triggers - RFQ, RFP, RFI, request for quotation, call for tenders, sourcing event, get quotes, supplier consultation, appel d'offres, demande de devis, cahier des charges achat, consultation fournisseurs, demande de prix, dossier de consultation."
---

# Supplier RFQ builder

Produces a consultation pack that gets comparable offers: suppliers know exactly what is asked and how they will be
judged, and the buyer can evaluate them line by line without bias.

## When to use
- Buying goods or services above a routine level (e.g. store fixtures, packaging, transport lanes, event services,
  maintenance contract, software).
- Renewing a contract or testing the market against an incumbent.
- Moving from an RFI (who can do it) to an RFQ (price for a defined spec) or RFP (solution and price).
- Not for: answering a customer's tender as a seller (use `tender-response-builder`), scoring received offers (use
  `supplier-evaluation`), or justifying a small purchase (use `purchase-request-justification`).

## Inputs
- What is bought, why, for whom, and the type: RFI, RFQ or RFP (required).
- Specifications or needs, volumes and locations (required; search Drive and Confluence for specs, past RFQs).
- Timeline constraints and contract duration (optional, default: proposed timeline labeled *proposal*).
- Procurement rules: number of bidders, thresholds, templates, legal clauses (optional; look for the internal
  procurement policy in Drive or Confluence; never assume).

## Sources
1. **Drive and Confluence**: procurement policy and templates, previous RFQs for the category, specifications,
   general purchasing conditions, supplier code of conduct, quality and product safety standards.
2. **Databricks (SQL or Polco) and Tableau**: historical consumption and volumes, current spend and prices for the
   baseline (internal use only, never disclosed to bidders).
3. **Airtable**: supplier lists or sourcing trackers if the team keeps one.
4. **Gmail and Chat / Slack**: stakeholder needs, incumbent issues, earlier supplier contacts.
5. **Jira**: requirements from IT or project teams for service or software purchases.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Choose the **event type**: RFI (market scan, no price), RFQ (spec fixed, compare price and terms), RFP (problem
   described, compare solutions). Say why.
2. Write **context and scope**: background the bidder needs, scope in / out, lots (allow bidding per lot when it
   widens competition), contract duration and renewal options.
3. Write **requirements** with IDs: each one testable, tagged **Must** (non-compliance = exclusion) or **Should**
   (scored), with the evidence expected. Prefer performance specs ("withstands 50 washes at 40 °C") over brand names;
   if a brand is cited, add "or equivalent".
4. Give **indicative volumes** per period and location, stated as non-binding forecasts unless the user says
   otherwise.
5. Commercial part: price validity, currency, **Incoterms 2020** rule and named place, payment terms per policy,
   price revision formula if multi-year, and a **cost breakdown template** (materials, labor, overhead, logistics,
   duties, margin) so offers are comparable and negotiable.
6. **Quality, social and environmental** requirements: code of conduct acceptance, social audit status, product
   safety and chemical compliance documentation, environmental data requested (e.g. materials, packaging,
   transport mode), sub-contracting disclosure.
7. **Evaluation grid published upfront**: criteria, weights summing to 100, scoring scale, knock-out criteria; price
   method stated (e.g. lowest price gets max points, others pro rata = lowest / offer × max).
8. **Timeline and rules**: issue date, intent-to-bid date, Q&A deadline, answers shared with all bidders anonymously,
   submission deadline and format, validity, clarification meetings, award target, confidentiality, no obligation to
   award, single point of contact.
9. **Bidder list check**: number of bidders vs policy, incumbent included on equal terms, no conflict of interest
   declared by the user.

## Output format
```markdown
# <RFI / RFQ / RFP> — <Subject> · ref <…> · draft v<0.x>
_Internal note (not for bidders): baseline spend <source>, policy <link>, bidders <n>_

## 1. Introduction and context
## 2. Scope and lots
## 3. Requirements
| ID | Requirement | Must / Should | Evidence to provide |
|----|-------------|---------------|---------------------|
## 4. Volumes (indicative, non-binding)
| Item / service | Unit | Volume per period | Location |
|----------------|------|-------------------|----------|
## 5. Commercial terms
- Currency · validity · Incoterms 2020 <rule + place> · payment terms <per policy> · price revision
## 6. Price and cost breakdown template
| Item | Unit price | Materials | Labor | Overhead | Logistics | Duties | Margin |
|------|-----------|-----------|-------|----------|-----------|--------|--------|
## 7. Quality, social and environmental requirements
## 8. Evaluation method
| Criterion | Weight | How scored |
|-----------|--------|-----------|
Knock-out criteria: … · Price scoring: …
## 9. Timeline
| Step | Date |
|------|------|
## 10. Rules of the consultation
Contact · Q&A · submission format · confidentiality · no obligation to award

---
**Fair-process checklist:** same documents to all ☐ · Q&A shared with all ☐ · grid frozen before opening ☐ ·
offers opened after deadline ☐ · conflicts declared ☐
```

## Quality checks
- Every requirement is testable, has an ID and is tagged Must or Should; Musts are few and truly eliminatory.
- Evaluation weights sum to 100 and every scored requirement maps to a criterion.
- The bidder-facing part contains no internal baseline price, budget or incumbent's price.
- Volumes are marked indicative or committed, consistently.
- Dates follow a logical order with realistic gaps (Q&A deadline before submission; answers circulated before it).

## Guardrails
- Fairness: identical information and deadlines for every bidder; questions and answers shared with all, anonymized;
  no criterion tailored to one supplier; no change to the grid after offers arrive.
- Confidentiality: never reveal one bidder's prices or solutions to another; never include internal budgets or
  target prices in the document.
- Do not invent legal clauses, payment terms or thresholds; use the internal templates or leave placeholders for
  procurement and legal.
- Draft only: do not send the RFQ or contact suppliers without explicit confirmation.
