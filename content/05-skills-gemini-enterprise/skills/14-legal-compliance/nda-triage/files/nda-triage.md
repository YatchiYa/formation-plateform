---
name: nda-triage
description: "Checks a non-disclosure agreement against a standard checklist and gives a green, amber or red verdict per clause and overall: mutual or one-way, definition of confidential information, carve-outs, permitted disclosures, term and survival, return or destruction, residuals, non-solicit or non-compete riders, remedies, governing law, with suggested fallback wording and the questions for Legal. Not legal advice. Use whenever someone receives or must send an NDA or confidentiality agreement, before a supplier, startup, partner or event discussion, even if they only ask 'can I sign this'. Triggers - NDA review, check this NDA, confidentiality agreement, can I sign this NDA, mutual NDA, accord de confidentialité, relire un NDA, vérifier un NDA, clause de confidentialité, puis-je signer ce NDA."
---

# NDA triage

Tells a teammate in a few minutes whether an NDA looks standard or needs Legal, clause by clause, with fallback
wording to propose. Green does not mean approved: signature follows the internal approval rules.

## When to use
- A supplier, startup, agency, club or partner sends an NDA before a discussion.
- A teammate needs to send an NDA and wants to check the counterparty's edits.
- A bundle of NDAs must be sorted into "standard" and "needs Legal".
- Not for: other contracts (use `contract-summary`), comparing two NDA versions in detail (use
  `document-comparison`), or a data-sharing set-up involving personal data (use `gdpr-processing-check`).

## Inputs
- The NDA file or text (required).
- Purpose of the exchange and what Company will share or receive (required: drives mutual vs one-way and scope).
- Company's NDA template or playbook (optional; search Drive/Confluence first).
- Country of the counterparty (optional).

## Sources
1. **Drive and Confluence**: Company's NDA template, Legal playbook or FAQ on NDAs, signature/approval rules.
2. **Gmail**: the thread with the counterparty (purpose, what was promised, deadline).
3. **Jira** (legal requests project, if any): earlier NDAs with the same counterparty.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify the frame**: parties (legal entities), direction (mutual / Company discloses / Company receives),
   purpose clause, effective date. A one-way NDA protecting only the counterparty while Company also shares
   information is at least Amber.
2. **Run the checklist** in Reference. For each item: what the NDA says (quote + clause), RAG, why.
   If an internal playbook exists, it overrides the generic thresholds; cite it.
3. **Look for riders** that do not belong in an NDA: non-compete, exclusivity, non-solicitation of employees,
   licence or IP assignment, obligation to negotiate or buy. Each is Red unless the playbook allows it.
4. **Overall verdict**: Green = all Green; Amber = Ambers only, fallback wording available; Red = any Red, or
   anything not understood. Red or Amber → route to Legal with the questions.
5. **Draft fallback wording** for each Amber/Red item, short, neutral, as a proposal to discuss with Legal.
6. **Prepare the reply** to the counterparty (draft only) if the user asks.

## Output format
```markdown
# NDA triage — <counterparty> · <date of draft>
> Not legal advice. Signature follows Company's approval rules; Legal validates Amber/Red items.
**Verdict: 🟢 / 🟠 / 🔴** — <one line why> · Direction: <mutual | one-way (who protects whom)>
_Benchmark: <internal template/playbook link | generic checklist>_

| # | Item | NDA says (clause) | RAG | Why | Fallback proposal |
|---|------|-------------------|-----|-----|-------------------|

### Questions for Legal
1. <…>

### Next step
<sign per approval rules | send to Legal with this summary | ask counterparty for changes>
```

## Quality checks
- Every checklist item in Reference has a row, even when the NDA is silent ("not addressed").
- Each RAG cites the clause or says "absent".
- The overall verdict follows the rule in step 4 exactly.
- Fallback wording is proposed for every Amber and Red row.
- The not-legal-advice line is present.


## Guardrails
- Never state that the NDA "can be signed" or is "approved"; state the triage result and the approval route.
- Do not share Company's internal playbook text with the counterparty.
- Draft only: no email to the counterparty and no e-signature action without the user's confirmation.

## Reference
Generic NDA checklist (Green → Amber → Red):
1. **Direction**: mutual or matches the real flow → one-way but limited sharing by Company → one-way against
   Company while it shares.
2. **Definition of confidential information**: marked or reasonably understood as confidential → very broad
   → includes information already public or independently developed.
3. **Standard carve-outs present**: public domain, already known, independently developed, received from a third
   party without duty → one missing → several missing.
4. **Permitted disclosures**: employees, affiliates and advisers with need to know, legal compulsion with notice →
   affiliates excluded → no disclosure to advisers or no legal-compulsion exception.
5. **Term**: defined disclosure period and survival (for example 2–5 years) → long survival → perpetual for all
   information (trade secrets may justify longer protection: ask Legal).
6. **Return or destruction**: on request, with backup and legal retention exceptions → no exceptions → impossible
   to comply.
7. **Residuals clause**: absent → limited → broad residuals for the receiving party.
8. **Riders**: none → non-solicit limited → non-compete, exclusivity, IP licence or assignment.
9. **Remedies**: injunctive relief allowed → liquidated damages capped → uncapped penalties.
10. **Governing law and jurisdiction**: law of the contracting Company entity or the playbook's choice → neutral → unusual or far jurisdiction.
11. **Personal data**: none exchanged → limited, with GDPR wording → personal data without processing terms.

## Example
Input: "A startup sent this NDA before a demo of their sizing app. We will share sample product data."
→ Verdict 🔴: one-way NDA protecting only the startup while Company shares data (row 1 Red), plus a clause granting
the startup a licence to "use feedback and data to improve its services" (row 8 Red). Fallback: make it mutual; limit
use to the stated purpose; delete the licence. Questions for Legal: is product sample data confidential under our
template? Next step: send to Legal with this summary.
