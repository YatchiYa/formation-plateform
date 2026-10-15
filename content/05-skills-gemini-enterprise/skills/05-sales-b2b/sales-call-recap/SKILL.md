---
name: sales-call-recap
description: "Turns B2B sales call or meeting notes, or a Google Meet transcript in Drive, into three drafts: a recap email to the customer confirming needs, agreements and dated next steps; an Airtable CRM update mapped to the base's real fields with qualification status; and an internal action list. Use whenever a seller finishes a call or visit with a club, school, company or local authority, pastes notes, or asks to update the CRM or follow up with a customer, even if they only say 'here are my notes'. Triggers - call recap, meeting follow-up, recap email, update the CRM, log this call, next steps email, compte rendu de rendez-vous client, mail de suivi, récap d'appel, mettre à jour le CRM, Airtable, prochaines étapes client."
---

# Sales call recap

Converts a customer conversation into a confirmed written record: the customer sees what was agreed, the CRM reflects
reality, and every next step has an owner and a date.

## When to use
- Right after a discovery call, demo, visit, kit-fitting or negotiation meeting.
- The user has rough notes, a voice-memo transcript or a Meet transcript and wants a clean follow-up.
- The Airtable record is stale and needs to match what was said.
- Not for: internal meetings without a customer (use `meeting-notes-to-actions`), preparing the call (use
  `discovery-call-prep`), or writing the full commercial offer (use `b2b-proposal-builder`).

## Inputs
- Notes or transcript (required). Search Drive for the Meet transcript of the matching Calendar event before asking.
- Customer organisation and attendees (optional, default: from the Calendar event).
- Tone and language of the customer email (optional, default: language of the meeting, formal-friendly).

## Sources
1. **Drive**: the Meet transcript or notes doc attached to the Calendar event; the account brief or discovery prep.
2. **Calendar**: the event (attendees, date) to anchor the recap.
3. **Airtable**: the account and opportunity records and the **base schema** (field names, single-select options,
   linked tables). The update must use these exact names and options.
4. **Gmail**: the previous thread with the customer, to reply in-thread and keep commitments consistent.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Extract facts**, each tagged with who said it: needs (with quantities, sports, age groups, sizes, sites),
   pains and their impact, budget signals, decision process and dates, competitors mentioned, objections, and every
   commitment ("we will send…", "they will check…").
2. **Separate commitments** into ours and theirs. Ours get an owner and a date; theirs get a date and are written as
   gentle confirmations ("As agreed, you will send the list of teams by 10 March").
3. **Update qualification**: for each MEDDICC-lite item (metrics, economic buyer, decision criteria, decision process,
   paper process, pain, champion, competition) mark what moved during the call. Propose a stage change only if the
   base's stage exit criteria are met (read them in Confluence or Drive if they exist; otherwise state the criterion
   you used).
4. **Draft the customer email** (≤ 180 words): thanks in one line, "what we heard" in their words (3 bullets), what
   was agreed, next steps with dates, one question that still needs an answer. Nothing that was not said in the call.
5. **Draft the Airtable update** as a field → old value → new value table, using the schema. If a field does not exist,
   list it under "Suggested fields" instead of inventing it. Notes field: 3–5 factual lines, dated. If the schema
   could not be read, say so above the table and write every field as `<plain label> [field name to confirm]`.
6. **List internal actions** (e.g. ask the customisation team for a proof, check a quote with the manager, book the
   size-collection session) with owner and date.
7. Flag **risks** heard: unclear economic buyer, competitor already shortlisted, a deadline we may not meet, a public
   procurement requirement that changes the process.

## Output format
````markdown
**Recap — <Organisation> · <date> · <attendees>** _(source: <transcript/notes link>)_

### 1. Email to the customer (draft)
**To:** … · **Subject:** <Organisation> — summary and next steps
```
<body ≤ 180 words>
```

### 2. Airtable update (draft — not applied)
| Field | Current | Proposed | Why (quote or note) |
|-------|---------|----------|---------------------|
| <real field name> | … | … | "…" |
Suggested fields (not in the base): …

### 3. Qualification after the call
| Item | Before | After | Evidence |
|------|--------|-------|----------|

### 4. Internal actions
| Action | Owner | Due |
|--------|-------|-----|

### Risks
- …

Reply "send" / "apply" to confirm each draft separately.
````

## Quality checks
- Every need, number and commitment in the email traces to a line in the notes or transcript.
- Each next step has an owner and a date; customer-side steps are phrased as confirmations, not orders.
- Airtable fields and select options match the schema exactly; unknown fields are only suggested.
- No price, discount, delivery date or stock statement appears unless it was actually stated in the call.
- The customer email is ≤ 180 words and contains no internal remarks (margins, competitor opinions, risk notes).

## Guardrails
- Draft, don't act: never send the email or write to Airtable until the user confirms each draft separately.
- Keep internal judgements (champion strength, risks, competitor views) out of the customer email.
- Record only professional information in the CRM; drop personal remarks from the notes (health, family, opinions
  about a person).
- If the transcript includes people who did not consent to recording, do not quote them verbatim; summarise neutrally.
- If something said in the call may be a commitment we cannot keep (a delivery date, a price), flag it for the user
  instead of confirming it in writing.
