---
name: tender-response-builder
description: "Builds the response pack for a public tender or private RFP (municipality, school, region, sports federation, large company): bid/no-bid check, requirement compliance matrix from the tender documents, draft answers for the technical proposal, award-criteria scoring logic, administrative and missing-documents checklist, Q&A questions for the buyer and a reverse schedule to the deadline. Use whenever a seller receives or finds a tender, RFP, RFQ, call for bids or procurement notice, or must fill a price schedule or technical memo, even if they only forward the files. Triggers - tender, RFP, public procurement, bid response, compliance matrix, technical proposal, appel d'offres, marché public, DCE, mémoire technique, règlement de consultation, BPU, DQE, répondre à un appel d'offres, MAPA."
---

# Tender response builder

Gives the bid team a complete, compliant and well-scored response plan for a public or private tender, from the
go/no-go decision to the last signed document, without missing a single mandatory requirement.

## When to use
- A tender file arrives (e.g. a town buys sports equipment for its gyms in lots; a region equips high schools; a
  federation or a company issues an RFP for team apparel).
- The team must decide whether to bid.
- The technical proposal or the compliance matrix must be drafted.
- Not for: a regular commercial offer without formal procedure (use `b2b-proposal-builder`), buyer-side RFQs that we
  issue to suppliers (use `supplier-rfq-builder`), or a legal review of contract clauses (use `contract-summary`).

## Inputs
- The tender documents (required): for French public tenders typically the consultation rules (RC), administrative
  and technical specifications (CCAP, CCTP), price schedules (BPU, DQE), the commitment form (AE), and candidacy forms
  (DC1, DC2 or the European DUME). Search Drive and Gmail for them first.
- Deadline and submission platform (required; read from the rules if not given).
- Lots targeted (optional, default: all lots analysed for fit).
- Our prices, lead times, certifications and references (required for the final answers; placeholders until provided).

## Sources
1. **Drive**: the tender files, previous responses to similar tenders, company administrative documents (registration,
   tax and social certificates, insurance), product data sheets, certificates, CSR documents, reference letters.
2. **Gmail**: the tender notice, platform notifications, questions and answers published by the buyer, amendments.
3. **Confluence**: internal bid process, approval rules for pricing, and who signs, if documented.
4. **Airtable**: past tenders tracker (won/lost, scores, winning price feedback) and the account history.
5. **Calendar**: internal review slots before the deadline.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Read the rules first** and extract: buyer, object, procedure type (adapted procedure or formal tender,
   framework agreement with purchase orders or not), lots, duration and renewals, estimated volumes, variants allowed,
   deadline for questions, submission deadline (date, hour, time zone), platform, signature requirements, award criteria
   with weights and sub-criteria. Quote clause numbers.
2. **Bid / no-bid** with a scored grid (0–2 each): fit with our offer per lot, ability to meet every mandatory
   requirement, capacity to deliver volumes and dates, price competitiveness (from past tender results, if any),
   relationship and references, effort vs deal value. Below half the points or one blocking mandatory gap → recommend
   no-bid or partial (some lots). The user decides.
3. **Build the compliance matrix**: one row per requirement from the specifications, with clause reference, type
   (mandatory / scored / informative), our answer (Compliant / Partial / Non-compliant / To confirm), evidence document,
   owner. Mandatory non-compliance = flag at top; never write "compliant" without evidence.
4. **Score-driven writing**: allocate effort to the technical proposal in proportion to criteria weights. For each
   scored sub-criterion, draft an answer structured as: requirement restated → our response → proof (data sheet,
   certificate, process, reference) → benefit for the buyer's users (pupils, players, municipal staff). Mirror the
   buyer's vocabulary and order, so evaluators find each answer in seconds.
5. **Price schedule**: map every line of the BPU or DQE to a product reference; leave prices as `[to fill]`. Check
   unit consistency (per item, per set, per size run) and that the DQE total equals quantities × unit prices.
6. **Administrative checklist**: every candidacy and offer document, its validity date, signature type and status
   (found in Drive / missing / expired).
7. **Questions to the buyer**: list ambiguities (sizes, customisation, delivery sites, samples) to submit through the
   official platform before the question deadline.
8. **Reverse schedule** from the submission deadline: question deadline, internal price approval, sample shipping if
   required, final review, upload at least 24 h before the deadline (platform uploads can be slow).

## Output format
```markdown
# Tender — <buyer> · <object> · ref <number>
**Deadline:** <date hh:mm, time zone> on <platform> · **Questions until:** <date> · **Procedure:** <type> · **Lots:** <list>
**Recommendation:** Bid / Partial bid (lots …) / No-bid — <score>/12 — <one-line reason> _(decision: user)_

### Award criteria
| Criterion | Weight | Sub-criteria | Where we answer |
|-----------|-------:|--------------|-----------------|

### ⚠️ Blocking points
- <mandatory requirement not met or unproven> (clause …)

### Compliance matrix
| Clause | Requirement | Type | Status | Evidence | Owner |
|--------|-------------|------|--------|----------|-------|

### Technical proposal — draft answers
#### <Sub-criterion> (<weight>)
- Requirement: … · Response: … · Proof: … · Benefit: …

### Price schedule mapping
| Line | Description | Unit | Qty | Our reference | Unit price |
|------|-------------|------|----:|---------------|-----------:|
| … | … | … | … | … | [to fill] |

### Administrative documents
| Document | Status | Valid until | Action |
|----------|--------|-------------|--------|

### Questions for the buyer (via the platform)
1. …

### Reverse schedule
| Date | Milestone | Owner |
|------|-----------|-------|
```

## Quality checks
- Every requirement in the specifications appears in the compliance matrix with a clause reference.
- No status "Compliant" without an evidence document; unknowns are "To confirm".
- Criteria weights add up to 100 % and match the consultation rules exactly (or, if the rules only rank criteria in
  decreasing order of importance, that order is reproduced and no weights are invented).
- Every price cell is `[to fill]` unless the user supplied the figure; DQE arithmetic is checked.
- The deadline, time zone and platform are quoted from the rules, with clause number.
- The upload milestone is at least 24 h before the deadline.

## Guardrails
- Procurement fairness: no contact with the buyer or evaluators outside the official Q&A channel during the procedure;
  no gifts or hospitality; never use non-public information about the buyer or competitors.
- Never invent prices, lead times, certifications, labels, test results, insurance or references; a missing proof is a
  gap to close, not a sentence to write.
- Do not advise abnormally low pricing or bid-rigging behaviours (coordinated bids, cover pricing).
- Legal clauses (penalties, liability, IP, data processing) go to legal review; summarise risks only (see
  `contract-summary`).
- Draft only: never upload, sign or submit; the authorised signatory submits.
