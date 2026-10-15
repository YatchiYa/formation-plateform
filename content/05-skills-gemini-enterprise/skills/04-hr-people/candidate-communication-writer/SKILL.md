---
name: candidate-communication-writer
description: "Drafts clear, warm and legally careful emails and messages to candidates at every step: application acknowledgement, interview invitation and scheduling with Calendar slots, status update or delay notice, respectful rejection with optional job-related feedback, offer-call follow-up and talent-pool keep-in-touch. Use whenever a recruiter or manager has to write to a candidate, is late answering one, or must say no, even if they only ask for 'a quick reply'. Triggers - candidate email, rejection email, interview invitation, schedule interview, candidate update, offer follow-up, mail candidat, refus candidature, réponse négative candidat, convocation entretien, invitation entretien, relance candidat."
---

# Candidate communication writer

Gives every candidate a timely, respectful and accurate message, so that each one leaves the process with a good
image of Company, whatever the outcome.

## When to use
- Inviting a candidate to an interview and proposing slots.
- The process is late and the candidate has heard nothing for a week or more.
- Saying no after a screening or after interviews, with or without feedback.
- Following up after an offer call, or keeping a good runner-up in touch for a future role.
- Not for: the formal offer letter (use `offer-letter-drafter`), the internal debrief (use
  `interview-debrief-synthesizer`), or onboarding messages after acceptance (use `onboarding-plan-builder`).

## Inputs
- Message type and the candidate's first name and role (required).
- Stage reached and what was decided by the hiring team (required for updates and rejections).
- Interviewers, format, place or link, duration (required for invitations; Calendar is searched).
- Feedback points agreed by the hiring team (optional, default: no individual feedback, only a polite close).
- Language and channel: email, SMS, platform message (optional, default: the candidate's last message language, email).

## Sources
1. **Gmail**: the thread with the candidate, to match their language, answer their questions and keep the history.
2. **Calendar**: free slots of the interviewers for the next 10 working days, room or Meet link.
3. **Drive and Confluence**: approved recruitment email templates, the candidate privacy notice link, interview
   location guides (store address, warehouse access, HQ reception).
4. **Airtable** (if hiring is tracked there): stage and dates, to avoid contradicting the tracker.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Read the thread and the tracker. Note the last promise made to the candidate ("we will answer by Friday") and
   whether it was kept. If it was missed, the message opens with a short apology, no excuses.
2. Pick the template for the type, then apply the rules below.
   - **Invitation**: role, step purpose, interviewer names and roles, format, duration, address or link, what to
     bring or prepare, 3 slots across ≥ 2 different days and times, accommodation sentence, contact person.
     Warehouse or store: give the access details (entrance, parking, who to ask for); avoid peak store hours
     (e.g. Saturday afternoon) unless the role is about them.
   - **Update / delay**: where the process stands, the new date by when they will hear back, one line of
     appreciation. Never leave a date open.
   - **Rejection**: thank → clear decision in the first 3 lines → (optional) 1–2 job-related feedback points
     agreed by the team → door open only if true (talent pool, other openings) → good wishes. Keep it short:
     ≤ 120 words after screening, ≤ 180 after interviews. After a final-round interview, recommend a phone call
     first and give the email as the follow-up.
   - **Offer-call follow-up**: recap only what was said, next steps and deadline, point to the formal letter.
     No figures unless they are in the approved offer.
   - **Keep in touch**: why we want to stay in touch, what will happen, consent to keep their data (link to the
     privacy notice).
3. **Feedback filter** (rejections): keep only feedback that is about job-related evidence and phrased as
   observable ("the example did not show how you managed stock priorities"), never about personality, fit,
   appearance, accent, age, availability linked to family, or a comparison with the chosen candidate.
4. **Tone check**: "you" focused, no corporate filler, no false hope, one clear next step.
5. Produce a short variant for SMS or platform message when the channel needs it (≤ 300 characters).

## Output format
```markdown
**Type:** <invitation / update / rejection / offer follow-up / keep in touch> · **Language:** <lang>
_Context used: <thread link>, <tracker>, <template or "no template found">. Last promise: <… / kept ✓ or missed ⚠️>_

**Subject:** <≤ 8 words>

<email body>

---
**SMS / short version** (if needed): <≤ 300 characters>

**Before sending**
- [ ] Decision confirmed by the hiring team (rejections) · [ ] slots still free · [ ] feedback agreed by the team
- [ ] Privacy notice link · [ ] signature and contact person
```

## Quality checks
- The decision or the purpose is stated in the first 3 lines.
- Every date, slot, address and name comes from the thread, Calendar or the user; none is invented.
- Rejection feedback, if any, is job-related and observable, and was agreed by the hiring team.
- The message gives one clear next step and a date (or says there is none).
- Word counts respect the limits for the type.

## Guardrails
- Draft only. Never send, schedule or decline anything without the user's explicit confirmation of the final draft.
- No content about protected characteristics, and never explain a rejection with them or with proxies (gaps, age of
  diploma, distance to home, availability linked to family).
- Never state or promise salary, contract terms or start dates not present in an approved offer.
- Do not give the reasons of a rejection in more detail than the hiring team agreed; local law and policy may
  frame what can be said. When unsure, keep the polite generic close and suggest HR review.
- Do not use AI to decide who is rejected. This skill only words a decision already made by people.
