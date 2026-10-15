---
name: email-reply-drafter
description: "Drafts a reply to a specific Gmail thread in the user's own voice: answers every question asked, in order, offers a short and a full version, and checks each date, number and commitment against Calendar, Drive and the thread before the user sends. Use whenever the user wants to answer an email, says 'reply to this', needs to say no politely, confirm, follow up or push back by email, even if they only paste the message. Triggers - reply to this email, draft a reply, answer this mail, help me respond, write back to, say no politely, répondre à ce mail, rédige une réponse, aide-moi à répondre, brouillon de réponse, comment lui répondre, refuser poliment."
---

# Email reply drafter

Writes the reply the user would write on a good day: every ask answered, nothing promised by accident, in their own
tone, ready to paste.

## When to use
- One thread needs a careful answer (customer, supplier, manager, cross-team request).
- The user has to decline, push back, renegotiate a deadline or deliver bad news.
- The user pastes an email and asks how to answer.
- Not for: many emails at once (use `inbox-triage`), summarizing a long thread before deciding (use
  `thread-catchup`), changing the tone of a text the user already wrote (use `message-rewriter`), or an external
  customer-service answer (use `customer-reply-drafter`).

## Inputs
- The thread (required): a Gmail link, subject or sender, or pasted text. Search Gmail before asking.
- The user's intent (optional, default: inferred from the thread and stated as an assumption): accept, decline,
  ask for info, propose a slot, delegate.
- Key facts to include (optional): a date, a figure, a decision.
- Language and register (optional, default: the thread's language and the register the user used before).

## Sources
1. **Gmail**: the full thread, including quoted history and attachments' names; the user's last 5–10 sent emails
   to the same recipient (or, if none, to people at the same level) to learn their greeting, tu/vous, length and
   sign-off.
2. **Calendar**: the user's real availability when the reply proposes or accepts a time.
3. **Drive and Confluence**: the doc, figure or policy the thread refers to, so facts in the reply are cited.
4. **Jira, Chat and Slack**: whether the question was already answered or the work is already tracked elsewhere.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **List the asks.** Extract every explicit question and request, plus implied ones ("let me know if Thursday
   works" = choose a time). Number them. Note who asked and any deadline.
2. **Decide the answer per ask**: yes, no, partial, need info, or "not mine → <owner>". If the user's intent is
   unclear on a blocking ask, ask one grouped question; otherwise proceed and state assumptions.
3. **Check every commitment.** For each date, slot, number, price, deliverable or promise:
   - slots: confirm free in Calendar, propose 2–3 options in the recipient's time zone;
   - figures and facts: take them from the thread or a Drive/Confluence source; otherwise write `[[à confirmer]]`;
   - deliverables: is the date realistic given the user's next 5 working days in Calendar? Flag if not.
4. **Match the voice.** Reuse the user's greeting and sign-off, sentence length and register. French: keep tu/vous as
   in the thread; "Bonjour <prénom>," and "Bonne journée," are safe defaults. English: plain, no stiff formulas.
5. **Structure (BLUF).** First line answers the main ask. Then one short paragraph or bullets per remaining ask, in
   the order they were asked. End with a clear next step (who does what by when).
6. **Hard messages.** To decline: thank → clear no → reason in one line → alternative or who can help. To push back
   on a deadline: what is possible, by when, and what it would take to meet the original date.
7. Write two variants: **short** (≤ 5 lines, mobile-friendly) and **full** (≤ 15 lines). Suggest CC changes only if
   the thread shows a missing owner or an unnecessary audience.

## Output format
```markdown
**Reply to <sender> — "<subject>"** · intent: <accept / decline / …> · assumptions: <one line or "none">

### Asks found
1. <ask> → <answer type>
2. …

### Short version
> <greeting>
> <≤ 5 lines>
> <sign-off>

### Full version
> <greeting>
> <BLUF line>
> <one block per ask, in order>
> <next step>
> <sign-off>

### To check before sending
- **<commitment>** — <verified in Calendar / source: <doc> / ⚠️ [[à confirmer]]>
- CC: <keep / add <name> because … / remove …>
```

## Quality checks
- Every numbered ask has an answer in both versions, or is explicitly parked with a reason.
- Every date, number and promise appears in "To check before sending" with its verification status.
- No proposed slot overlaps an event in the user's Calendar.
- The first sentence of the full version answers the main ask.
- Language, tu/vous and sign-off match the user's previous emails to that person.

## Guardrails
- Draft only. Never send, schedule-send or reply-all; the user copies or confirms the draft.
- Never commit the user to prices, discounts, contract terms, legal positions or HR decisions not stated by the user
  or a cited source; use `[[à confirmer]]` instead.
- If the thread contains personal data of others (health, salary, disciplinary), do not repeat it in the reply
  unless strictly needed; suggest moving sensitive topics to a call.
- If the email looks like phishing or an unusual payment change request, say so and do not draft a compliant reply.
