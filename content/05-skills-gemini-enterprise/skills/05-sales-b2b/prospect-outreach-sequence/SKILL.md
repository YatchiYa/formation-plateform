---
name: prospect-outreach-sequence
description: "Writes a personalised multi-touch B2B outreach sequence (emails, call scripts with voicemail, LinkedIn connection and message texts) for a prospect or a segment such as sports clubs, schools, companies or local authorities, with a cadence, one clear ask per touch and GDPR-compliant B2B prospecting (lawful basis, opt-out, source of data). Use whenever a seller wants to contact new prospects, relaunch a cold account, write a cold email or build a campaign for a segment, even if they only ask for 'one email'. Triggers - outreach sequence, cold email, prospecting emails, follow-up cadence, LinkedIn message, séquence de prospection, mail de prospection, relance prospect, message LinkedIn, campagne de prospection B2B, premier contact."
---

# Prospect outreach sequence

Produces a short, relevant and compliant sequence of touches that earns a first conversation with a Company Pro
prospect, built on a real reason to talk rather than a product catalogue.

## When to use
- A seller targets a named organisation or a list of the same segment (e.g. 30 football clubs in a region).
- A dormant customer must be reactivated before the season.
- A cold email is getting no answers and needs a rewrite.
- Not for: researching the account first (use `account-research`), replying to an inbound request or a live thread
  (use `email-reply-drafter`), or answering a public tender (use `tender-response-builder`).

## Inputs
- Target: one organisation with a contact role, or a segment description (required).
- Offer or angle to open with (optional, default: derived from the segment's main pain and season).
- Sender name, role and signature (optional, default: placeholders).
- Country of the recipients (required for the GDPR rule; ask if unknown).
- Number of touches and duration (optional, default: 6 touches over ~3 weeks).

## Sources
1. **Airtable**: account and contact records, consent or opt-out fields, past campaigns and their status. Exclude
   anyone flagged opt-out or do-not-contact.
2. **Gmail**: previous exchanges with the organisation (never pitch as if the relationship were new).
3. **Drive and Confluence**: segment playbooks, approved offer descriptions, reference cases, legal or DPO guidance on
   prospecting, email templates and signatures.
4. **Slack or Chat**: what worked recently for colleagues on the same segment, if the user points to a channel.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Compliance gate first.** Check country and contact type:
   - Generic addresses (contact@, secretariat@) are company data; personal professional addresses are personal data.
   - France (CNIL guidance): B2B email prospecting on an opt-out basis is allowed if the message relates to the
     recipient's professional role; every message must identify the sender and offer an easy opt-out.
   - Several countries (e.g. Germany) generally require prior consent even in B2B. If the country is not France or the
     rule is unclear, say so and point to legal or the DPO guidance found in Drive; do not assume.
   - If contact data came from a third party or public source, the first message must say where it came from
     (GDPR art. 14), or the user must have another way of informing.
2. **Find the reason to talk now** (one per sequence): season start, a trigger event from `account-research`, a new
   facility, a school year, a CSR or wellbeing initiative, an expiring supplier contract. No reason = generic spam;
   ask the user for one.
3. **Write a commercial insight** (Challenger style): one thing the prospect may not have considered, tied to their
   cost or outcome. Example for a club: "Most clubs re-order kits mid-season because size runs were guessed; collecting
   sizes per team before ordering avoids it." Label it as a suggestion, never as data, unless a source backs a number.
4. **Build the cadence** (default 6 touches, 3 weeks), each with ONE ask:
   - D1 email: insight + relevance + low-friction ask (15-minute call, or a yes/no question).
   - D3 LinkedIn connection note (≤ 300 characters, no pitch).
   - D6 call + 20-second voicemail referring to the email.
   - D10 email: proof (a sourced reference case or a useful resource), new angle.
   - D15 call or LinkedIn message: a question about their timing.
   - D21 break-up email: polite close, leaves the door open, repeats the opt-out.
5. **Personalise** with tokens only where real data exists: {first_name}, {club_or_org}, {trigger}, {team_count}.
   Segment variants change the pain and the vocabulary: president or treasurer of a club (budget, volunteers' time),
   PE teacher (durability, safety, class sizes), HR or CSR lead (participation, inclusion, employer brand), sports
   department of a town (public rules, facilities, events).
6. **Tighten**: emails ≤ 120 words, subject ≤ 6 words and not salesy, no attachments in the first touch, one link max,
   plain text, mobile-readable.

## Output format
```markdown
# Outreach sequence — <target or segment> (<country>)
**Reason to talk now:** <trigger, source> · **Insight:** <one line> · **Compliance:** <rule applied + opt-out wording>

| # | Day | Channel | Goal | Ask |
|---|-----|---------|------|-----|
| 1 | D1 | Email | … | … |

### Touch 1 — Email (D1)
**Subject:** …
<body ≤ 120 words>
<signature>
<opt-out line>

### Touch 2 — LinkedIn connection note (D3)
…

### Touch 3 — Call script + voicemail (D6)
- Opener (10 s): …
- Permission question: …
- 2 discovery questions: …
- Voicemail (≤ 20 s): …

… (touches 4–6)

### Personalisation fields
| Token | Where it comes from |
|-------|---------------------|

_Exclusions applied: <N contacts opt-out / already in active deal>_
```

## Quality checks
- Every email has the sender identity and a working opt-out line; the break-up email repeats it.
- Each touch has exactly one ask, and no two consecutive touches repeat the same angle.
- No price, discount, lead time, stock claim, statistic or percentage appears unless the user or an approved Drive
  document provides it (cite it); otherwise rephrase without the number.
- Emails are ≤ 120 words; LinkedIn notes ≤ 300 characters; subjects ≤ 6 words.
- The compliance line names the country rule applied, or states that legal must confirm it.

## Guardrails
- Draft, don't act: never send emails, InMails or connection requests, or enrol contacts in a tool. The user sends.
- No scraping of LinkedIn or websites for personal emails, no guessed email patterns (firstname.lastname@) without a
  lawful source, no purchased lists unless the user confirms their origin and consent status.
- Do not target individuals' private addresses or phones; professional channels only.
- No fake urgency, fake personalisation ("I saw your post…" without a real post) or misleading subject lines (no
  fake "Re:" or "Fwd:").
- For a public body with an ongoing tender on the subject, do not prospect; route to `tender-response-builder`.
