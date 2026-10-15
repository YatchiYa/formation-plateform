---
name: response-template-library
description: "Builds or refreshes a library of reusable customer-service response macros for the top contact reasons: each macro has a usage rule, personalization fields, channel variants for email, chat and public review, a policy source link and an 'if not' branch, and the set comes with a naming convention and a review owner. Use whenever a team wants canned responses, saved replies or macros, needs to harmonize answers between agents or stores, or prepares for a peak period, even if they ask for 'a few standard answers'. Triggers - response templates, macros, canned responses, saved replies, standard answers, modèles de réponse, réponses types, macros SAV, réponses standard service client, bibliothèque de réponses, trames de réponse."
---

# Response template library

Gives a service team a consistent, policy-correct set of macros for its most frequent contact reasons, written to
sound human, with fields to personalize so customers never feel they got a copy-paste.

## When to use
- Setting up or cleaning up macros in a help desk, Gmail templates or a shared doc.
- Before a peak (sales period, season start, new service) where volumes will jump.
- Agents or stores answer the same question differently.
- Not for: answering one specific customer (use `customer-reply-drafter`), a help-center article (use
  `kb-article-writer`), or a public FAQ page (use `faq-builder`).

## Inputs
- Team scope: channel(s), country, language(s) (required).
- Contact reasons to cover (optional, default: top 10 reasons by volume from data, else asked).
- Existing macros (optional; search Drive/Confluence first, then improve rather than duplicate).
- Tone-of-voice guidelines (optional; search Drive/Confluence, never invent brand rules).

## Sources
1. **Databricks (SQL or Polco) / Tableau**: volume by contact reason over the last 3–6 months to pick the top reasons.
   Show the query or dashboard.
2. **Jira / Airtable / Gmail**: 5–10 resolved cases per reason, to capture real customer wording and good agent
   answers.
3. **Drive and Confluence**: official customer policies, existing macros, tone-of-voice and brand guidelines.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Pick the reasons**: top contact reasons by volume (cover ≥ 70% of volume if data allows). For each, collect
   the real variants of the question.
2. **Define the decision tree per reason**: what the agent checks first (order status, purchase date, product
   condition) and which answer applies. One macro per outcome, not one per reason.
3. **Write each macro with the LAST structure** (Listen, Apologize when relevant, Solve, Thank):
   - Opening that reflects the specific situation via a field, e.g. `{product_name}`, `{issue_summary}`.
   - The answer or the next step, with policy wording linked to its source.
   - An "if not" branch: what to offer when the standard answer does not fit (repair, workshop diagnosis, escalation).
   - Closing with a clear next step and thanks.
4. **Make channel variants**: email (≤ 150 words), chat (≤ 3 short messages), public review (≤ 80 words, no
   personal or order data, invite to a private channel).
5. **Mark mandatory personalization**: at least two fields per macro must be filled by the agent; unfilled braces
   must be visible so they cannot be sent by mistake.
6. **Name and govern**: naming convention `<REASON>-<OUTCOME>-<CHANNEL>-<LANG>`, a policy link per macro, an owner
   and a review date; flag macros that depend on a policy with no source found.
7. **Run a tone pass**: no blame on the customer, no jargon, no internal tool names, positive phrasing ("you can"
   rather than "you cannot unless").

## Output format
```markdown
# Response macros — <team / channel / country> · v<date>
_Coverage: <n> reasons ≈ <x>% of contacts (source: <query/dashboard>) · Policy sources: <links>_

### Index
| Macro name | Reason | Outcome | Use when | Policy source |
|------------|--------|---------|----------|---------------|

### <REASON>-<OUTCOME>
**Use when:** <conditions checked by the agent> · **Don't use when:** <…>
**Email**
<text with {fields}>
**Chat**
<text>
**Public review**
<text>
**If not:** <alternative / escalation route>
**Fields:** {customer_first_name} · {product_name} · {…}

### Governance
- Owner: <role> · Review: <date> · Macros with missing policy source: <list>
```

## Quality checks
- Every macro states its "Use when" and links a policy source, or is flagged "policy to confirm".
- Each macro has ≥ 2 mandatory fields and an "if not" branch.
- Channel length limits from step 4 are respected.
- Public review variants contain no order numbers or personal data.
- The index covers every macro, and names follow the convention.

## Guardrails
- Never write a time window, refund amount, fee or warranty duration that is not in an official source; use a
  `{policy_term}` field with a "to confirm" note instead.
- Safety, injury, legal threat and data-protection requests get no macro answer; they get a routing macro to the
  escalation or privacy process.
- Do not import or publish macros into any tool until the owner approves the library.

## Example
Input: "Macros for our French e-commerce chat team before the sales period."
→ Top reasons from the contact dashboard: order tracking, return request, refund delay, size exchange, product
availability. Macro names: DELIVERY-LATE-CHAT-FR, RETURN-WITHIN-POLICY-EMAIL-FR, REFUND-PENDING-CHAT-FR… Every return
and refund macro uses `{policy_term}` because no official policy doc for the French site was found, so terms stay 'to confirm'; a macro for "item
arrived damaged" routes to the product-safety check when injury is mentioned.
