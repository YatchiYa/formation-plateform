---
name: purchase-request-justification
description: "Writes a short, approval-ready justification for a purchase request: the need and what happens without it, alternatives considered (reuse, rent, cheaper option, do nothing), quotes compared, total cost of ownership over the useful life, budget line and remaining budget, approval path and required documents found in the internal procurement policy, and the text to paste in the purchase request tool. Use whenever someone must request a purchase, get a quote approved, justify spend outside budget or answer an approver's questions, even if they only say 'I need to buy this'. Triggers - purchase request, justify a purchase, purchase justification, spend approval, buy request, PR approval, out of budget spend, demande d'achat, justifier un achat, justification d'achat, demande d'engagement, validation de dépense, achat hors budget."
---

# Purchase request justification

Gives the requester a justification an approver can accept in one read: why now, why this option, how much in total,
which budget, and who must sign.

## When to use
- Raising a purchase request for equipment, services, software, events or consumables.
- An approver asked "why this supplier?" or "why not cheaper?".
- Spend is outside budget or above a threshold that requires more quotes or a higher approval.
- Not for: a multi-year investment with NPV (use `business-case-builder`), consulting several suppliers (use
  `supplier-rfq-builder`), or comparing suppliers on a full grid (use `supplier-evaluation`).

## Inputs
- What to buy, quantity and the need behind it (required).
- Quote(s) or price source (required; search Gmail and Drive for quotes before asking).
- Cost center or budget line (optional; searched in budget files; else `[to confirm with controller]`).
- Urgency and needed-by date (optional).

## Sources
1. **Drive and Confluence**: procurement policy (number of quotes required, approval levels, preferred suppliers,
   framework contracts), budget file for the cost center, previous similar requests.
2. **Gmail**: supplier quotes and their validity dates, exchanges with the supplier.
3. **Databricks or Tableau**: usage data that proves the need (e.g. breakdown frequency of the current machine,
   workshop volume, rental demand).
4. **Jira and Chat / Slack**: incidents or requests that triggered the need.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. State the **need** in business terms: problem, who is affected, evidence (data, incidents), and the **cost of not
   buying** (downtime, lost sales, safety risk, workaround time).
2. Check **alternatives** in this order and say why each is or is not enough: do nothing / delay; reuse internally
   (another store, team or stock); repair; rent or lease; existing framework contract or preferred supplier; cheaper
   specification.
3. Compare **quotes**: same scope and specification, unit and total price, delivery time, warranty, validity date.
   Flag scope differences instead of comparing unlike offers.
4. Compute **TCO** over the useful life: purchase + delivery and installation + consumables + maintenance + training
   + disposal − residual value. Formula shown; every element sourced or `[to confirm]`.
5. Find the **budget line**: budgeted amount, already consumed, remaining, and whether this request fits; if not,
   state the offset proposed by the user (do not invent one).
6. Determine the **approval path and documents** from the policy found (number of quotes, approval level by amount,
   CAPEX vs OPEX classification). If no policy is found, say so and list the questions for procurement.
7. Write the **justification text** (≤ 120 words) for the purchase request tool's free-text field, and the short
   message to the approver.

## Output format
```markdown
# Purchase request — <item> · <amount, currency excl. VAT> · <cost center>
**Ask:** approve <item × qty> from <supplier> for <amount> by <date> · **Why now:** <one line>

## Need and cost of not buying
- Need: … (evidence: …)
- Without it: …

## Alternatives considered
| Alternative | Why not / why yes |
|-------------|-------------------|

## Quotes
| Supplier | Scope | Unit price | Total | Lead time | Warranty | Valid until | Source |
|----------|-------|-----------|-------|-----------|----------|-------------|--------|

## Total cost of ownership (<n> years)
| Element | Amount | Source |
|---------|--------|--------|
| **TCO** | | = purchase + install + run + maintenance + disposal − residual |

## Budget
Line <…> · budget <…> · consumed <…> · remaining <…> · this request <…> → fits / does not fit (<offset>)

## Approval path (source: <policy link> or "policy not found")
- Required quotes: … · approvers: … · documents: …

## Text for the purchase request tool (≤ 120 words)
<text>

## Message to approver (draft)
<3–5 lines>
```

## Quality checks
- Every amount (quote, budget, TCO element) has a source or is `[to confirm]`; TCO equals the sum of its elements.
- Quotes compared have the same scope, or differences are flagged.
- The approval path cites the policy found; nothing is assumed when no policy is found.
- At least three alternatives are addressed, including reuse or rental.
- The tool text is ≤ 120 words and states need, choice and amount.

## Guardrails
- Never invent approval thresholds, preferred suppliers, budget amounts or internal tool names.
- Do not split a purchase into smaller requests to stay under an approval threshold; flag it if the request looks
  like a split.
- Quotes are confidential; do not forward one supplier's price to another.
- Draft only: do not submit the request, email the approver or place an order without explicit confirmation.
