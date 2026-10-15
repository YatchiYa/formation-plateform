---
name: offer-letter-drafter
description: "Drafts an offer letter or promise of employment from the official company template found in Drive, filling only facts provided by the user or approved sources, with visible placeholders for anything missing, a consistency check across title, dates, pay, working time and contract type, and a cover email. It never invents compensation, benefits or clauses. Use whenever a candidate has been selected and someone must prepare the offer, update an offer after negotiation, or check an offer draft before signature, even if they only say 'prepare the paperwork'. Triggers - offer letter, job offer, draft the offer, promise of employment, offer email, lettre d'offre, proposition d'embauche, promesse d'embauche, rédiger l'offre, courrier d'offre, proposition de contrat."
---

# Offer letter drafter

Prepares an accurate, consistent offer from the approved template, so that HR and the hiring manager only have to
check and sign, and nothing in it was guessed.

## When to use
- The hiring team has selected a candidate and the offer must be drafted.
- An offer must be updated after a negotiation (start date, hours, pay agreed by the approver).
- Someone wants a second pair of eyes on an offer draft before it goes out.
- Not for: rejection or scheduling messages (use `candidate-communication-writer`), the employment contract
  itself or clause interpretation (use `contract-summary` and HR/legal), or the welcome plan (use
  `onboarding-plan-builder`).

## Inputs
- Candidate name, role title, level, team, location, country (required).
- Contract type, working time, start date, probation or trial period (required, or placeholders).
- Compensation elements approved by the approver: base, variable, allowances, benefits (required, or
  placeholders; never estimated).
- The offer template for the country and contract type (required; search Drive first).
- Offer validity date, reporting line, signatory (optional, default: placeholders).

## Sources
1. **Drive**: the official offer template for the country/entity (search "offer letter", « promesse
   d'embauche », « proposition d'embauche » + country), the approved job description, any approval email or
   form attached to the requisition.
2. **Gmail**: the approval thread (pay, start date) and the negotiation thread with the candidate.
3. **Confluence**: the HR page that explains which template applies to which contract type, if any.
4. **Airtable** (if hiring is tracked there): requisition ID, approved title and band label.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Find the template.** Use the most recent version for the right country, entity and contract type. If Drive is
   not connected or none is found, say so in one line and ask for the template; do not write a letter from scratch,
   because legal mentions differ by country. Still deliver the fact sheet (step 2) with the given values and
   `[[placeholders]]` for the rest, instead of asking for each missing field.
2. **Build the fact sheet** before writing: one row per field with value and source (approval email, JD,
   user). Missing → `[[FIELD — to be provided by HR]]`.
3. **Fill the template** without changing its legal wording. Only replace fields and the optional personal
   welcome paragraph (≤ 60 words, about the role and the team's sport or mission; no promises).
4. **Consistency check** (each line pass/fail):
   - Title, level and team match the approved requisition and JD.
   - Working time × pay basis is coherent (e.g. part-time hours with a pro-rated base if the template uses
     full-time equivalents; mark *to confirm* if unclear).
   - Start date is a working day, after the offer validity date, and compatible with the notice period the
     candidate mentioned.
   - Trial/probation period length is filled from the template or HR, not assumed.
   - Currency, gross/net wording, pay frequency are consistent everywhere.
   - Every number in the letter appears in the fact sheet with a source.
   - Diff vs previous version (if an update): list each changed field.
5. **Cover email**: short, warm, summarizes what is attached, how to accept, the validity date and the contact
   person. No figures in the email body unless HR asks.
6. Provide the reviewer checklist and stop. The letter is a draft for HR and the signatory.

## Output format
```markdown
# Offer draft — <Candidate>, <Role>, <Entity/Country>
_Template: <link, version/date>. Status: DRAFT — not sent._

## Fact sheet
| Field | Value | Source |
|-------|-------|--------|
| Base pay | [[BASE PAY — to be provided by HR]] | — |

## Consistency check
| Check | Result | Note |
|-------|--------|------|
| Title vs requisition | ✓ / ⚠️ | … |

## Letter (template filled)
<full text, template wording unchanged, fields filled or [[PLACEHOLDER]]>

## Cover email
**Subject:** …
<body>

## Before sending
- [ ] All [[placeholders]] replaced · [ ] approved by <approver> · [ ] signed by <signatory>
- [ ] Legal mentions checked by HR for <country> · [ ] candidate data stored per HR process
```

## Quality checks
- Zero numbers, benefits or clauses without a source in the fact sheet; all gaps are `[[PLACEHOLDER]]`.
- Template legal wording is unchanged (only fields and the optional welcome paragraph differ).
- Every consistency check has a result; any ⚠️ is repeated in "Before sending".
- For an update, every changed field is listed with old → new value.
- The status line says DRAFT and the letter is not sent.

## Guardrails
- Never invent or estimate compensation, bands, bonuses, benefits, notice or probation periods, or local legal
  mentions. If asked "what should we offer?", say that pay decisions belong to the approver and HR, and point to
  the internal pay policy if one is found in Drive/Confluence.
- Pay must be set on job-related grounds only; do not use the candidate's previous salary, gender, age or origin
  as inputs (some jurisdictions ban salary-history use).
- Salary data is confidential: keep it out of chats and channels; share the draft only with the user.
- Draft only. Do not email the candidate or upload the letter to a shared folder without explicit confirmation.
- This is not legal advice; contract terms are validated by HR or legal for the country.
