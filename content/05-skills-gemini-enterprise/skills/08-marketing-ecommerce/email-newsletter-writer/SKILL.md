---
name: email-newsletter-writer
description: "Writes a customer email or newsletter ready for the CRM team: goal and segment, 3 to 5 subject lines with an A/B test plan, preheader, scannable structure with one primary CTA, plain-text version, alt text, and a compliance and deliverability checklist (consent, unsubscribe link, sender identity, spam triggers). Use whenever someone needs a marketing email, a newsletter, a member or loyalty email, a launch or event email, or better subject lines, even if they only ask 'write me an email to our customers'. Triggers - newsletter, marketing email, CRM email, subject lines, email campaign, preheader, loyalty email, newsletter client, emailing, objet d'email, e-mail marketing, campagne CRM, mail adhérents."
---

# Email newsletter writer

Produces a customer email that gets opened, read in 10 seconds and clicked, and that respects consent rules and inbox
deliverability. One email, one goal, one primary CTA.

## When to use
- A newsletter, a launch email, a seasonal email (first snow, back to school) or a store event invitation.
- Subject lines underperform and need variants to test.
- A loyalty or member email (welcome, post-purchase care tips, repair or second-hand offer).
- Not for: internal teammate emails (use `internal-announcement-writer`), replies to one customer (use
  `customer-reply-drafter`), B2B prospecting sequences (use `prospect-outreach-sequence`) or test results analysis
  (use `ab-test-readout`).

## Inputs
- Goal and the one action expected (required).
- Segment and its consent basis (required; ask if unknown, never assume opt-in).
- Content: products, offer conditions, event details, links (required for anything factual).
- Sender name, template and brand guidelines (optional, default: searched in Drive).
- Send date and market/language (optional).

## Sources
1. **Drive and Confluence**: email templates, brand and CRM guidelines, legal mentions per country, past email
   results, product data sheets, offer terms.
2. **Databricks (SQL or Polco)**: past email KPIs by segment (delivered, unique clicks, click-to-open, conversion,
   unsubscribes, spam complaints) and segment sizes. Show the query used.
3. **Tableau**: CRM dashboards with the official KPI definitions.
4. **Airtable and Jira**: CRM calendar, campaign request, send slots already booked.
5. **Gmail and Slack**: the request and stakeholder constraints.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Goal → metric**: define the success metric (click rate, conversion, store visits) and a guardrail
   (unsubscribe rate, spam complaints). Open rate is a weak metric since Apple Mail Privacy Protection inflates opens;
   prefer clicks and conversions.
2. **Segment fit**: check the content is relevant for the segment (a ski email to members who bought ski gear or
   live near mountains, not to everyone). Irrelevant sends hurt engagement and sender reputation.
3. **Subject lines (3–5)**, each ≤ 45 characters for mobile, built on different levers: benefit, curiosity with
   payoff, urgency only if true, personalization, question. Avoid ALL CAPS, "!!!", "free" bait and misleading "RE:".
4. **Preheader** (40–90 characters) that completes the subject, never repeats it.
5. **A/B plan**: test one variable (subject lever), each arm ≥ the minimum sample per arm from `experiment-design` or
   past data, decide on clicks or conversion, not opens; define the winner rule before sending.
6. **Body** with the inverted pyramid: hero message + one primary CTA above the fold, 2–3 supporting blocks, one
   secondary link at most. Copy uses AIDA (attention, interest, desire, action) in ≤ 150 words. CTA buttons say the
   action ("Choose my tent"), not "Click here".
7. **Accessibility**: alt text on every image, real text (not text baked into images), contrast, a plain-text
   version, logical reading order, link text that makes sense alone.
8. **Compliance and deliverability**: consent basis per segment (opt-in, or soft opt-in for similar products for
   existing customers where the country allows it), visible unsubscribe link and List-Unsubscribe header, sender
   identity and address, offer conditions next to the offer, image-to-text balance, tracking links with UTMs.

## Output format
```markdown
**Email — <name> · segment: <…> · goal: <…> · send: <date>**
_Assumptions: <one line>_

### Subject lines
| # | Subject (≤ 45 char) | Lever | Preheader |
|---|---------------------|-------|-----------|

**A/B plan:** variable <…> · split <…> · winner metric <clicks/conversion> · decision rule <…>

### Body
**Hero:** <headline> — <1–2 lines>
[Primary CTA: <verb + object>]
**Block 2:** …
**Block 3:** …
**Footer:** <legal mentions from source>, unsubscribe link, sender identity

### Plain-text version
…

### Alt texts
1. …

### Compliance and deliverability checklist
- [ ] Consent basis confirmed for every segment: <…>
- [ ] Unsubscribe link + List-Unsubscribe header
- [ ] Offer conditions (dates, scope, stock limits) next to the offer
- [ ] No misleading subject or false urgency
- [ ] Links with UTMs tested · seed test sent

### Facts to confirm
- …
```

## Quality checks
- Exactly one primary CTA; the hero and the CTA are visible without scrolling on mobile.
- Subject lines differ by lever, not just by wording, and are ≤ 45 characters.
- Every price, discount, date and product fact has a source or a `[TO CONFIRM]` placeholder.
- Every image has alt text and the plain-text version contains every link.
- The checklist states the consent basis for the segment, or flags it as unknown.

## Guardrails
- GDPR and ePrivacy: marketing emails go only to people with valid consent (or soft opt-in where legal). Never
  suggest buying lists or emailing contacts without a documented basis; route doubts to `gdpr-processing-check`.
- No false urgency, fake countdowns, invented "only 3 left" or reference prices that do not follow the EU Omnibus
  price-reduction rule (prior price = lowest of the last 30 days, check the source).
- Green or durability claims go through `green-claim-checker`.
- Do not invent brand guidelines. Draft only: never schedule or send from the CRM tool.
