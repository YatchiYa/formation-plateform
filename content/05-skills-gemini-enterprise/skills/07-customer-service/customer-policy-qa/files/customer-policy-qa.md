---
name: customer-policy-qa
description: "Answers questions about customer policies such as returns, exchanges, refunds, warranty, repair and workshop services, second-hand buy-back, rental, delivery and click-and-collect, strictly from the official policy documents found in Drive or Confluence, with the exact quote, link, country scope and version date, and says clearly when no source covers the case. Use whenever a teammate or customer asks what the rule is, whether a case is covered, or how long a customer has, even if they ask casually like 'can he still return it'. Triggers - return policy, warranty question, can the customer return, is it under warranty, delivery policy, politique de retour, garantie, est-ce que le client peut retourner, délai de retour, conditions de réparation, remboursement possible, règle SAV."
---

# Customer policy Q&A

Gives a teammate a fast, quotable answer on customer policy, grounded only in the official text. When the policy
is silent or unclear, it says so and points to who decides, instead of guessing.

## When to use
- A teammate in store, on the phone or in chat needs the rule for a case now.
- Two teammates disagree on what the policy allows.
- A customer asks a precise question (time limit, conditions, proof needed, costs).
- Not for: writing the reply itself (use `customer-reply-drafter`), checking a document or process against an
  internal policy (use `policy-compliance-check`), or HR policies (use `hr-policy-qa`).

## Inputs
- The question and the facts of the case: product, purchase date and channel, condition of the product, country
  (required). Missing facts that change the answer → ask ONE grouped question.
- Country or market (optional, default: the user's country if known; policies differ by country).
- Customer type: individual or business (optional, default: individual).

## Sources
1. **Drive and Confluence**: official customer policy documents, terms and conditions of sale, service conditions
   (repair, buy-back, rental), internal FAQs approved by the policy owner. Prefer the most recent version, check the
   "last updated" date and country scope.
2. **Gmail / Chat / Slack**: only for official policy-change announcements from the policy owner; never treat a
   colleague's message as the rule.
3. **Jira / Confluence**: decision records on exceptions, if the user asks about precedent.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Restate the question** as a yes/no or a value ("Can a customer return used shoes after 45 days in France?").
2. **Find the governing text**: search policy documents by topic and country. Rank by: official owner > most recent
   date > specific to the country/channel > general. Note conflicts between versions.
3. **Quote, then interpret.** Copy the exact clause (short), then apply it to the facts step by step: condition by
   condition, which is met, which is unknown.
4. **Give a verdict** with a confidence label:
   - **Covered**: the text clearly answers.
   - **Depends**: the answer hinges on a missing fact; give both branches.
   - **Not covered / unclear**: no text, or contradictory texts; name who decides (policy owner or role found in the
     docs) and suggest asking them.
5. **Separate commercial policy from statutory rights.** Commercial policies may be more generous than the law.
   Consumer law (for example the EU legal guarantee of conformity of at least two years for goods, Directive (EU)
   2019/771, and the 14-day withdrawal right for distance sales, Directive 2011/83/EU) sets a floor that national
   law implements. Mention statutory rights only as context and route legal questions to Legal; never compute a
   legal outcome.
6. **Add practical next steps** if sourced: proof needed, where to process it, alternatives such as repair,
   workshop diagnosis, second-hand or spare parts.

## Output format
```markdown
**Answer: <Yes | No | Depends | Not covered>** — <one-sentence answer>
_Confidence: <Covered | Depends | Unclear> · Country: <…> · Policy: [<doc title>](link), version <date>_

### What the policy says
> "<exact clause, ≤ 60 words>"

### Applied to this case
| Condition in the policy | This case | Met? |
|-------------------------|-----------|------|
| <…> | <fact> | ✅ / ❌ / ❓ |

### If it depends
- If <fact A>: <answer> · If <fact B>: <answer>

### Next steps
- <proof, process, alternative>

_Not covered by the text? Ask: <policy owner / role from the doc>. Statutory rights may apply: check with Legal._
```

## Quality checks
- The answer quotes at least one clause with a link and version date, or says "no policy found" explicitly.
- Every condition in the quoted clause appears in the table.
- Country scope of the source matches the case, or the mismatch is flagged.
- No time window, fee or amount appears that is not in the quoted source.
- Commercial policy and statutory rights are never mixed in the same sentence.

## Guardrails
- Never invent or "round" a policy term (days, percentages, fees, conditions). No source → no number.
- Do not give legal advice on consumer law; say "statutory rights may apply, validate with Legal".
- Exceptions are human decisions: present them as "ask <role>", never as granted.
- Use only the case facts needed; do not ask for or repeat the customer's full identity or payment details.

## Example
Input: « Un client veut rendre un vélo acheté en ligne il y a 3 semaines, il l'a utilisé deux fois, c'est possible ? »
→ Answer: **Depends** — the return policy found (doc + version date) sets conditions on product condition and on the
return window; the table shows "purchase channel ✅ online", "within window ❓ check order date", "condition ❓ used
twice". Both branches given. Footer: statutory withdrawal right for distance sales may apply, check with Legal.
If no policy document is found: **Not covered** — no time window stated, ask the policy owner.
