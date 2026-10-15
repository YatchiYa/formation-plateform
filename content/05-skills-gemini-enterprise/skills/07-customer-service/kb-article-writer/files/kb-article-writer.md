---
name: kb-article-writer
description: "Writes a knowledge base or help-center article from resolved cases, tickets, workshop notes or product documentation, following Knowledge-Centered Service (KCS): issue in the customer's words, environment, step-by-step resolution, cause, edge cases and when to contact support, in an internal agent version and a customer-facing version. Use whenever a question or fix keeps coming back, a ticket was solved in a way others should reuse, or someone asks to document a solution or update a help article, even if they say 'can you write this down'. Triggers - KB article, help article, knowledge base, document this fix, how-to for customers, article de base de connaissances, fiche d'aide, article FAQ, documenter une solution, fiche SAV, article centre d'aide."
---

# KB article writer

Captures a solution once, in a reusable form, so the next customer finds the answer alone and the next agent
solves the case in minutes. Follows KCS: write in the requester's words, structure for findability, improve on reuse.

## When to use
- The same question or fix appears in several tickets.
- An agent or workshop technician found a solution worth sharing.
- An existing article is outdated, unclear or contradicted by recent cases.
- Not for: a page of many short Q&As (use `faq-builder`), an internal step-by-step procedure for teammates (use
  `sop-writer`), or a policy answer to one question (use `customer-policy-qa`).

## Inputs
- The resolved cases, ticket links, thread, or notes describing the fix (required).
- Product name and reference or service concerned (required if product-related).
- Audience: internal agents, customers, or both (optional, default: both).
- Existing article to update (optional; search Confluence/Drive first).

## Sources
1. **Jira** (service desk projects) and **Gmail / Chat / Slack**: the resolved cases, the exact words customers used,
   what the agent did, and what worked.
2. **Confluence and Drive**: existing KB articles (avoid duplicates), product user manuals or technical sheets,
   policy documents, style guide for help content.
3. **GitHub**: release notes or issues, only for website or app problems.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Search before writing.** Look for an existing article on the same issue in Confluence/Drive. If one exists,
   propose an update (diff of sections) instead of a new article.
2. **Capture the issue in the customer's words.** Collect 3–5 real phrasings from tickets (anonymized). They become
   the title and the search keywords, e.g. "zip stuck on tent door" rather than "closure system malfunction".
3. **Structure with the KCS template**: Issue · Environment (product, model, size, version, channel) · Resolution
   (numbered steps, one action per step, expected result) · Cause (if known and confirmed) · Edge cases.
4. **Check facts against sources.** Steps that involve product handling must match the user manual or technical
   sheet. Policy elements (return windows, warranty) must link to the official policy; otherwise keep a placeholder.
5. **Add safety and limits**: when to stop and contact support or the workshop (risk of damage, injury, warranty
   void). Never suggest a fix that could alter safety equipment (helmets, harnesses, child seats, brakes, etc.):
   route these to a qualified workshop.
6. **Write two versions** when the audience is "both": customer version (plain words, no internal tools, ≤ 300 words)
   and agent version (adds diagnosis questions, internal routing, macro to use, linked tickets).
7. **Set KCS metadata**: confidence state (KCS v6: Work in Progress / Not Validated / Validated by a licensed owner), owner,
   review date, linked tickets. Suggest the reviewer (product or workshop expert) for approval.

## Output format
```markdown
# <Title in the customer's words>
_Applies to: <product / reference / version> · Audience: <customer | agent> · State: Not Validated · Owner: <role>_
_Search keywords: <5–8 phrasings>_

### Issue
<1–2 sentences, as the customer would describe it>

### Environment
- Product / model / size / app version: <…>

### Resolution
1. <action> → <expected result>
2. …

### Cause
<confirmed cause with source | "not confirmed">

### Edge cases and when to contact us
- If <condition>, <what to do / contact the workshop>

### Agent notes (agent version only)
- Diagnosis questions: <…>
- Route / macro: <…>
- Linked tickets: [#…](…)

_Sources: <manual, policy, tickets> · Review by: <date>_
```

## Quality checks
- The title uses words found in at least one real ticket.
- Each resolution step has a single action and an observable result.
- Every technical instruction is traceable to a manual, technical sheet or resolved case; policy items have a link
  or a placeholder.
- Customer version has no internal tool names, ticket ids or teammate names.
- The article says when to stop and contact support.

## Guardrails
- No customer personal data in the article: phrasings are anonymized, no names, orders or photos of people.
- Do not invent product specifications, compatible spare parts or warranty terms.
- Safety-critical equipment: no do-it-yourself repair steps unless the manufacturer's manual provides them.
- Draft only. Publishing in Confluence or the help center happens after the owner approves.

## Example
Input: 6 Jira tickets about a stuck zip on a tent door, plus the workshop technician's notes.
→ Search finds no existing article. Title: « Fermeture éclair de la porte bloquée ». Keywords from tickets: « zip
coincé », « fermeture ne glisse plus », « curseur bloqué ». Resolution steps checked against the user manual; one step
from the technician's notes not in the manual is kept in the agent version only, flagged for product validation.
"When to contact us": if the slider is open or teeth are missing, go to the workshop. State: Not Validated, owner: product team.
