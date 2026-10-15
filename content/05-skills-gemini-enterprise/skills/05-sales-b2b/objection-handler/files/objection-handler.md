---
name: objection-handler
description: "Prepares answers to B2B sales objections such as price too high, lead time, quality or durability doubts, happy with the current supplier, no budget, must go through a tender or need to think about it: diagnoses the real objection, gives exploring questions, a sourced response with proof, a reframe in total cost or value per player, and the next step, for calls and written replies. Use whenever a seller faces pushback from a club, school, company or local authority, gets a 'no' or a 'too expensive', or asks how to answer a customer's concern, even if they only paste the customer's email. Triggers - handle objection, customer says too expensive, pushback, how do I answer, price objection, competitor is cheaper, traiter une objection, le client trouve ça trop cher, répondre à une objection, délai trop long, ils ont déjà un fournisseur."
---

# Objection handler

Helps a seller treat an objection as information: find what is really behind it, answer with proof instead of
pressure, and move the deal to a concrete next step or an honest no.

## When to use
- A customer pushes back in a call, an email or after receiving a proposal.
- The seller prepares a negotiation or a renewal and expects resistance.
- A team wants a shared set of answers for the most frequent objections of a segment.
- Not for: a full comparison with one competitor (use `competitive-battlecard`), rewriting the whole offer (use
  `b2b-proposal-builder`), or a generic email reply with no objection (use `email-reply-drafter`).

## Inputs
- The objection, verbatim if possible, and its context (required): customer, stage, channel, what was proposed.
- The offer details concerned (optional, default: from Drive or Airtable).
- What room the seller has: approved concessions, alternatives, trade-offs (optional, default: none, so no concession
  is proposed).

## Sources
1. **Gmail**: the customer's message and thread history, to answer in context.
2. **Drive**: the proposal sent, product data sheets, test or durability documentation, reference cases, approved
   pricing or concession rules.
3. **Airtable**: deal record: stage, decision criteria, competitors noted, previous objections.
4. **Confluence**: segment playbooks, approved answers to frequent objections, service rules (delivery, after-sales).
5. **Databricks (SQL or Polco)**: the customer's history (reorders, returns) that can serve as proof.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Classify the objection** and its likely real meaning:
   - Price ("too expensive") → often a value gap, a budget-timing issue or a negotiating move.
   - Timing ("too early", "next season") → no urgency or a budget cycle.
   - Lead time / availability → a fixed event date at risk (first match, school year, company event).
   - Quality / durability / fit → past bad experience or a competitor's claim.
   - Status quo ("we have a supplier", "the coach's friend runs the local shop") → relationship or switching cost.
   - Authority ("I need to ask the board / the council") → we are not talking to the economic buyer.
   - Process ("it must go through a tender") → a public procurement rule, not an objection to treat.
   - Smoke screen ("send me some info") → no pain identified.
2. **Use LAER**: Listen (restate the objection in their words), Acknowledge (without agreeing or arguing), Explore
   (2–3 questions), Respond (only after exploring). Write the exploring questions first. Examples: "Too expensive
   compared to what?", "If price were aligned, would we be your choice?" (isolates the objection), "What happens if the
   kits arrive after the first match?"
3. **Respond with proof, not adjectives**: a data sheet fact, a reference customer, the customer's own history, a
   service rule. If no proof exists in the sources, say "to confirm" and propose a way to prove it (sample, trial, visit).
4. **Reframe value** when relevant: total cost per player per season, durability and reorder cost, volunteer time
   saved by a single order and size collection, cost of a missed event date. Use only the customer's or sourced numbers;
   otherwise show the formula with blanks.
5. **Trade, never give**: if a concession is in the user's approved room, pair it with something in return (larger
   scope, earlier order, multi-season commitment, single delivery point). No room given = no concession proposed.
6. **Close on a next step** proportional to the objection: a sample, a call with the economic buyer, a revised option,
   or a clear agreement to stop.
7. Produce both a **spoken version** (for a call, ≤ 60 seconds) and a **written version** (email, ≤ 150 words).

## Output format
```markdown
**Objection:** "<verbatim>" · **Type:** <type> · **Likely real issue:** <hypothesis>

### Explore first (ask before answering)
1. …
2. …

### Response
- **Acknowledge:** …
- **Answer:** … — proof: <source link or "to confirm">
- **Reframe:** <value per player / cost of status quo, with formula>
- **Trade (if approved):** <we give X if you give Y> · or "No concession proposed"

### Spoken version (≤ 60 s)
> …

### Written version (≤ 150 words)
<email draft>

### Next step to propose
- …

### If the answer is still no
- <what to learn and how to leave the door open>
```

## Quality checks
- At least two exploring questions come before any answer.
- Each proof points to a source or is explicitly "to confirm".
- No price, discount, lead time, stock or warranty claim is invented; concessions only within the user's stated room.
- The written version is ≤ 150 words and the spoken version can be read in about 60 seconds.
- No negative claim about a named competitor that is not sourced and dated.

## Guardrails
- No pressure tactics: no fake deadlines, fake scarcity or misleading comparisons.
- A "we must go through a tender" objection is a legal rule: respect it, and route to `tender-response-builder`;
  never suggest splitting orders to stay under procurement thresholds.
- Do not disparage competitors or local partners; compare facts only.
- Draft only: the seller decides what to say and sends any email.
