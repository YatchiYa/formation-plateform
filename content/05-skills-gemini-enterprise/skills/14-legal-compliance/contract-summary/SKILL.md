---
name: contract-summary
description: "Summarizes a contract or amendment into a one-page brief: parties, purpose, term and renewal, obligations of each side, price and payment terms, service levels, liability caps and indemnities, IP, data protection, termination rights, governing law, key dates and a RAG list of clauses that deserve legal attention, every point cited to its clause number. Not legal advice. Use whenever someone shares a contract, agreement, terms, SOW or amendment and asks what it says, what they are committing to, or what to watch, even if they only say 'can you read this'. Triggers - summarize contract, contract summary, key terms, what does this agreement say, review this contract, résumé de contrat, synthèse du contrat, points clés du contrat, que dit ce contrat, fiche contrat, clauses importantes."
---

# Contract summary

Gives a business teammate a clear, cited one-page view of what a contract commits Company to, its key dates and
the clauses to raise with Legal. It is a reading aid, not legal advice: Legal validates any position.

## When to use
- Before signing, renewing or renegotiating a supplier, service, partnership, lease or event contract.
- A teammate inherits a contract and needs to know obligations and deadlines.
- Preparing a call with the counterparty or with Legal.
- Not for: NDAs (use `nda-triage`), comparing two versions of a contract (use `document-comparison`), checking a
  supplier overall (use `supplier-evaluation`), or answering a public tender (use `tender-response-builder`).

## Inputs
- The contract file or link, including annexes and amendments (required).
- Company's role: buyer, seller, partner, licensee, lessee (optional, default: inferred from the parties).
- What the user cares about: price, exit, liability, data, dates (optional, default: all).
- Internal contract playbook or standard positions (optional; search Drive/Confluence).

## Sources
1. **Drive**: the contract, annexes, amendments, previous versions, and any signed copy.
2. **Confluence / Drive**: Legal's contract playbook, standard terms, approval or signature rules.
3. **Gmail**: the negotiation thread, to see what was agreed but not yet in the text (flag, do not merge).
4. **Jira** (legal requests project, if any): the related request and Legal's comments.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Check completeness**: list the documents found (main body, annexes, amendments, order forms) and the order
   of precedence clause. Missing annex referenced in the text → flag it.
2. **Extract key terms** with clause numbers: parties (legal entities), effective date, term, renewal (automatic?
   notice period), scope and deliverables, exclusivity, price and revision, payment terms, penalties and service
   levels, liability cap and exclusions, indemnities, insurance, IP ownership and licences, confidentiality, personal
   data (processor terms), subcontracting, audit, termination for convenience and for cause, effects of termination,
   governing law and jurisdiction, assignment and change of control.
3. **List obligations by party** as actionable lines ("Company must send forecasts monthly, cl. 5.2").
4. **Build the key dates table**: start, end, renewal notice deadline (compute only from dates in the text and say
   how), price revision dates, reporting dates.
5. **Rate clauses RAG** against the Legal playbook if found, else against the generic checklist in Reference.
   Each Amber/Red needs a reason and a question to ask Legal or the counterparty.
6. **Spot inconsistencies**: definitions used but not defined, numbers that differ between body and annex,
   blanks, unsigned amendments.
7. Write the brief; keep exact wording in quotes for the riskiest clauses.

## Output format
```markdown
# Contract summary — <title> · <counterparty> · <version/date>
> Not legal advice. Reading aid to prepare a review with Legal.
**In one line:** <what the contract does, for how long, for how much>
_Documents read: <list> · Missing: <list or none> · Playbook: <link | generic checklist>_

### Key terms
| Topic | What it says | Clause |
|-------|-------------|--------|

### Obligations
- **Company:** <action> (cl. x)
- **<Counterparty>:** <action> (cl. y)

### Key dates
| Date | Event | Clause | How computed |
|------|-------|--------|-------------|

### Clauses to watch
| RAG | Clause | Issue | Question for Legal / counterparty |
|-----|--------|-------|-----------------------------------|

### Inconsistencies and gaps
- <…>
```

## Quality checks
- Every key term and obligation cites a clause number, or says "not found in the contract".
- Every computed date shows the source date and the rule applied.
- Every Amber or Red row has a concrete question.
- Quotes are exact; paraphrases are not inside quotation marks.
- The not-legal-advice line is present at the top.

## Guardrails
- Not legal advice. Never say a clause is "valid", "enforceable" or "legal"; say what it says and what to ask Legal.
- Do not suggest signing, accepting or rejecting; the decision belongs to the authorized signatory with Legal.
- Contracts are confidential: do not paste them into wide channels; share the summary only with the people the
  user names.
- Do not merge negotiation emails into the summary as if they were contract terms.

## Reference
Generic RAG checklist (used only when no internal playbook is found):
- **Red**: unlimited liability for Company; broad indemnity without cap; automatic renewal with long notice and no
  exit; IP in Company's developments assigned to the counterparty; personal data processing without processor
  terms (GDPR Art. 28); unilateral price change; exclusivity without volume commitment from the other side.
- **Amber**: liability cap not mutual; termination for convenience for one side only; foreign governing law;
  penalties without cap; vague service levels; subcontracting without consent; audit rights missing.
- **Green**: mutual, capped, clear, with notice periods both sides can meet.

## Example
Input: "Résume ce contrat de maintenance des caisses avant renouvellement."
→ In one line: 3-year maintenance contract, renews automatically unless notice is sent (cl. 12.2). Key dates: renewal
notice deadline computed from the end date (cl. 3.1) minus the notice period (cl. 12.2), computation shown. Red: price
revision at the supplier's discretion (cl. 8.4). Amber: liability cap applies to Company only (cl. 14.1). Gap: annex
"SLA" referenced but not found in Drive.
