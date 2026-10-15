---
name: customer-reply-drafter
description: "Drafts a reply to one customer message (email, chat, marketplace message, app or store review, social comment) that acknowledges the emotion, states only policy that is sourced, proposes a concrete solution and next step, and adapts length and tone to the channel, with a short and a full variant. Use whenever a teammate has to answer a customer, an unhappy review or a complaint, or asks how to phrase a reply, even if they only paste the message and say 'help'. Triggers - reply to customer, answer this review, customer email, respond to complaint, draft a response, répondre à un client, réponse à un avis, répondre à une réclamation, mail client, que répondre à ce client, réponse avis Google."
---

# Customer reply drafter

Turns one customer message into a reply a teammate can send after a quick check: human, accurate on policy, and
ending with a clear next step. The customer should feel heard and know exactly what happens next.

## When to use
- A customer email, chat or marketplace message needs an answer.
- A public review (store page, app store, product page, social) needs a response.
- A teammate is unsure how to say "no" politely or how to calm an angry customer.
- Not for: a serious case that needs management arbitration (use `complaint-escalation-brief`), a question about
  what the policy actually says (use `customer-policy-qa`), building reusable macros (use
  `response-template-library`), or internal emails (use `email-reply-drafter`).

## Inputs
- The customer message, or a link to the thread or ticket (required).
- What the teammate can offer: decision already taken, options allowed, limits (optional, default: no commitment,
  the reply proposes the next step only).
- Order, product or case reference (optional). Use it to look up context, never paste more of it than needed.
- Channel and brand voice (optional, default: inferred from the source; public reviews are always short).
If the message or the allowed outcome is unclear and cannot be found, ask ONE grouped question.

## Sources
1. **Gmail / Google Chat / Slack**: the full thread, previous replies, internal notes on the case.
2. **Jira** (service desk projects, if used): ticket history, status, linked issues (known defect, delivery incident).
3. **Drive and Confluence**: the official customer policy (returns, warranty, repair, delivery), approved macros and
   tone-of-voice guidelines. Quote policy only from these, with the document name.
4. **Airtable**: case or order tracking bases, if the team uses one.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Read the message twice.** Extract: the facts (product, dates, what happened), the request (refund, repair,
   exchange, information, apology), the emotion (frustrated, worried, angry, disappointed) and any risk flag:
   injury or safety issue, legal threat, media or influencer, data or privacy request, repeated contact.
   A risk flag → stop drafting a resolution and recommend `complaint-escalation-brief`; still offer a holding reply.
2. **Check the policy.** Find the rule that applies in Drive/Confluence. No source → do not state any time window,
   amount or condition, and do not paraphrase a supposed rule (« our policy generally covers defects only »); write
   a placeholder `[check policy: …]` where the rule goes and say so above the draft.
3. **Structure the reply with HEARD** (Hear, Empathize, Apologize, Resolve, Diagnose):
   - Hear: restate the issue in one sentence so the customer knows it was read.
   - Empathize: name the impact on their sport or plans ("your trip this weekend"), not a generic "we understand".
   - Apologize: for the experience, without admitting legal fault or defect before diagnosis.
   - Resolve: the concrete option(s) the teammate is allowed to offer, or the next step and who does it by when.
   - Diagnose: internally, note the likely root cause for the team (one line, not sent to the customer).
4. **Say no well** when the answer is no: reason in plain words + the policy source + at least one alternative
   (repair service, second-hand, spare part, workshop diagnosis) if one exists in the sources.
5. **Adapt to the channel**:
   - Chat: ≤ 60 words, one question at a time.
   - Email: ≤ 150 words, greeting by name, one paragraph per idea, signature placeholder.
   - Public review: ≤ 80 words, thank first, no order number or personal data, move details to a private channel.
6. **Write two variants**: Short (send as is) and Full (more explanation). Same facts, same commitments.
7. Run the quality checks, then list what the teammate must verify before sending.

## Output format
```markdown
**Reply to <customer first name or 'reviewer'> · <channel> · emotion: <label> · risk flags: <none | list>**
_Policy basis: <doc name + link> | ⚠️ no policy source found, placeholders left_

### Short version
<reply text>

### Full version
<reply text>

### Before sending
- [ ] <verify item, e.g. stock of replacement size, order date vs policy window>
- [ ] Replace placeholders: <list or 'none'>

### Internal note (not for the customer)
Likely root cause: <product | usage | information | delivery | store service | policy> — <one line>
```

## Quality checks
- Every policy element (time window, condition, amount) is linked to a source doc, or is a visible placeholder.
- The reply answers the customer's actual request, in the first or second sentence.
- It ends with one clear next step: who does what, by when.
- Word counts respect the channel limits in step 5.
- « Replace placeholders » lists exactly the `[…]` placeholders present in both versions (never « none » when any remain).
- A public review reply contains no order number, address, phone or health detail.
- The reply is in the customer's language, and the notes around it are in the teammate's language.

## Guardrails
- Never invent or promise refunds, vouchers, compensation amounts, delivery dates or warranty terms. Only offer
  what the teammate or a sourced policy allows.
- Do not admit liability or a product defect, and do not comment on injuries beyond empathy. Safety cases go to
  escalation.
- Minimize personal data: first name only, no full address or payment details in the draft.
- Draft only. Nothing is sent or posted until the teammate confirms the final text.

## Example
Input: « Ma tente a un arceau cassé après 2 nuits, on part en rando samedi, c'est inadmissible !! » (email, FR)
→ Header: emotion *angry*, risk flags *none*, policy: ⚠️ none found for this country, placeholders left.
→ Short version (FR): « Bonjour Julie, un arceau cassé à quelques jours de votre rando de samedi, je comprends votre
colère et je suis désolé de cette expérience. Pour que vous puissiez partir, je vous propose [check policy: échange /
pièce détachée / diagnostic atelier]. Pouvez-vous m'envoyer une photo de l'arceau ? Je reviens vers vous sous 24 h. »
→ Internal note: likely root cause *product* (to diagnose), consider spare-part availability before replying.
