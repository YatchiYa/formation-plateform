---
name: complaint-escalation-brief
description: "Builds a one-page escalation brief for a serious customer complaint: verified facts, timeline, customer impact, severity rating, applicable policy with sources, resolution options with cost and risk, a recommended resolution for a human decision-maker, and a holding reply to the customer. Use whenever a complaint involves injury or product safety, a legal or media threat, a vulnerable customer, repeated failed contacts, or a request beyond standard policy, even if the user only says 'this one is getting messy'. Triggers - escalate complaint, escalation brief, serious complaint, angry customer escalation, customer threatens, réclamation grave, escalader une réclamation, dossier client sensible, client mécontent, litige client, note d'escalade."
---

# Complaint escalation brief

Gives the person who must decide (store manager, customer service lead, legal, product safety) one page with the
facts, the stakes and clear options, so that a sensitive complaint is solved fast and consistently.

## When to use
- A customer was injured, or a product may be unsafe (breakage, burn, fall, allergic reaction).
- The customer threatens legal action, a regulator complaint, social media or press exposure.
- The case has bounced between channels or teammates without resolution (3+ contacts).
- The fair solution goes beyond what the teammate is allowed to offer.
- Not for: a routine reply (use `customer-reply-drafter`), an on-site incident report in a store (use
  `store-incident-report`), or a trend across many complaints (use `voice-of-customer-report`).

## Inputs
- The complaint thread, ticket or case notes (required).
- Who the brief is for and their decision rights (optional, default: customer service lead).
- What has already been offered or refused (optional, extracted from the thread if present).
- Order or product reference (optional).

## Sources
1. **Gmail / Google Chat / Slack**: every message with the customer and internal exchanges about the case.
2. **Jira** (service desk or quality projects): the ticket, linked defects, similar reports on the same product.
3. **Drive and Confluence**: customer policies, escalation procedure and contact list, product safety or quality
   alert process. Use the internal escalation path if one exists; otherwise say none was found.
4. **Databricks (SQL or Polco)**: optional, count of similar returns or complaints on the same product reference
   in the last 90 days, if a returns/complaints table is identified. Show the query or the Polco question.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Build the timeline** from all sources: date, channel, who, what was said or done. Mark each line as
   *fact* (from a source) or *customer claim* (stated by the customer, not verified).
2. **Rate severity** with the matrix in Reference. The highest triggered level wins. Safety always means S1.
3. **Identify the real ask**: what the customer wants (refund, replacement, apology, explanation, compensation)
   and what they need (to be safe, to practise their sport on a date, to be taken seriously).
4. **Map policy**: quote the applicable rule from Drive/Confluence with its link. If no rule covers the case, say so.
   Note the legal floor only as "statutory rights apply, check with Legal", never as a computed amount.
5. **Draft 2–3 options**, e.g. within policy / goodwill gesture / exceptional measure. For each: what the customer
   gets, cost (only if known from data or the user, else "cost to confirm"), precedent risk, reputational risk,
   time to resolve.
6. **Recommend one option** with a two-line rationale, and name who must approve it. The decision stays human.
7. **List parallel actions**: product safety or quality alert, keep the product for analysis, legal informed,
   reply deadline. Add a holding reply that acknowledges, sets a date for the answer and promises nothing else.

## Output format
```markdown
**Escalation — <case ref> · Severity <S1–S4> · Decision needed by <date/time> · For: <role>**
**Bottom line:** <one sentence: what happened and what we recommend>

### Facts and timeline
| Date | Channel | Event | Fact / Claim | Source |
|------|---------|-------|--------------|--------|

### Customer impact and ask
- Impact: <safety / financial / sport plans / trust>
- Asks for: <…> · Needs: <…>

### Policy
- <rule> — <doc link> | ⚠️ no policy covers this case

### Options
| Option | Customer gets | Cost | Precedent risk | Reputation risk | Time |
|--------|---------------|------|----------------|-----------------|------|

### Recommendation
<option> — <rationale in 2 lines>. Approver: <role>.

### Parallel actions
- [ ] <action> — owner <role> — by <date>

### Holding reply (draft, not sent)
<≤ 80 words>
```

## Quality checks
- Every timeline row has a source; customer statements are labeled *Claim*.
- Severity matches the matrix and the triggered criterion is named.
- No option contains an amount or commitment that is not from the user, a policy or data.
- The recommendation names an approver and a decision deadline.
- The holding reply promises only a date for the next contact.

## Guardrails
- Do not judge fault, defect or liability. Write "reported", "alleged", "to be analysed".
- Health and injury details: include only what the decision needs, never in the customer reply or in wide channels.
- Legal threats and injuries: recommend informing Legal and the product safety contact found in Drive/Confluence.
  This brief is not legal advice.
- Draft only. No message to the customer, no ticket update, no alert is sent without the user's confirmation.

## Reference
Severity matrix (highest level wins):
| Level | Criteria | Target first reply |
|-------|----------|--------------------|
| S1 | Injury or safety risk, legal or regulator threat, data breach, media exposure | same day |
| S2 | Vulnerable customer, 3+ failed contacts, high-value order, viral review risk | 24 h |
| S3 | Request beyond policy, disputed decision, repeated product issue | 48 h |
| S4 | Dissatisfied but within standard process | standard SLA |
Target times are defaults; replace them with the internal SLA if one is found in Drive/Confluence.
