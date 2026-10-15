---
name: competitive-battlecard
description: "Creates a one-page sales battlecard against a named competitor in a B2B segment (team sport apparel brands, local sports shops, general office or wellbeing suppliers, distributors in public tenders): where they win, where we win, fair landmine questions, answers to their typical claims, proof points and quick wins, built only from sourced and dated facts. Use whenever a seller meets a competitor in a deal or tender, asks how to beat or position against someone, or a team wants to update its competitive material, even if they only name the competitor. Triggers - battlecard, competitor comparison, how to beat, positioning against, competitive intel, fiche concurrent, battle card, comment se positionner face à, argumentaire concurrentiel, on est en concurrence avec."
---

# Competitive battlecard

Gives sellers a single page they can use during a deal against one competitor: honest about where the competitor is
strong, precise about where we win, and grounded in facts a customer could verify.

## When to use
- A deal or tender has a known competitor and the seller needs positioning.
- Losses to the same competitor are piling up (see `win-loss-analysis` for the pattern).
- The team wants a quarterly refresh of its competitive cards.
- Not for: a market-wide watch digest (use `competitor-watch`), price index work (use `price-positioning-analysis`),
  or answering one objection (use `objection-handler`).

## Inputs
- Competitor name (required) and segment where we meet them (required, e.g. youth football clubs, company wellbeing,
  school tenders).
- Sources about the competitor the user can provide: their public catalogue, website pages, tender award notices,
  customer feedback (optional, default: search Drive, Gmail and Slack).
- Our offer for that segment (optional, default: from Confluence and Drive).

## Sources
1. **Drive**: existing battlecards, competitor documents shared by customers with permission, tender award reports
   and score sheets, product data sheets for our offer.
2. **Airtable**: deals where this competitor appeared: outcome, reason, segment.
3. **Gmail**: customer emails mentioning the competitor (what customers say they like about them).
4. **Slack and Chat**: field intel channels; treat as hearsay until confirmed, and date every item.
5. **Confluence**: approved positioning and offer descriptions.
6. **Public material pasted by the user**: website, catalogue, public tender award notices.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Collect facts** in a list with source, date and confidence (High = documented and recent, Medium = customer said
   it, Low = internal hearsay). Discard anything older than 18 months unless still confirmed. Never fill gaps from
   general knowledge.
2. **Where they win** (be honest; sellers lose trust in cards that pretend otherwise): e.g. a local shop's proximity and
   relationship with the club president; a specialist brand's prestige with senior teams; a distributor's tender
   experience.
3. **Where we win**, phrased as customer outcomes with proof: range breadth across sports for multi-sport
   organisations, our own brands designed for the sport (e.g. Kipsta for team sports, Domyos for fitness), store network
   for reorders and fittings — each only if a source documents it for this segment.
4. **Landmine questions**: neutral questions that make the customer check a decision criterion where we are strong,
   without naming the competitor. Example: "How will late sign-ups in October get the same kit?" "Who handles a
   defective item mid-season, and how fast?" They must be fair and true for any supplier.
5. **Their claims → our answer**: the 3–5 things their sellers say about themselves or us, with a factual response and
   proof.
6. **Win themes by segment and deal type**: which 2–3 messages to lead with, and which deals we should qualify out of
   early (where they are structurally stronger).
7. Stamp the card with an owner, a date and a refresh rule (90 days or after any lost tender).

## Output format
```markdown
# Battlecard — <Competitor> in <segment> · updated <date> · owner <name>
**In one line:** <how to position against them>

### Snapshot
| Item | Fact | Source · date | Confidence |
|------|------|---------------|-----------|

### Where they win
- … (source)

### Where we win
- <customer outcome> — proof: <source>

### Landmine questions (fair, competitor not named)
1. …

### Their claims → our answer
| They say | Our answer | Proof |
|----------|-----------|-------|

### Lead with / qualify out
- Lead with: …
- Qualify out when: …

### Recent deals vs <Competitor>
| Deal | Outcome | Reason | Link |
|------|---------|--------|------|

_Refresh by <date + 90 days> or after the next lost tender._
```

## Quality checks
- Every fact has a source, a date and a confidence level; no undated claim remains.
- "Where they win" has at least two honest entries.
- Each landmine question is true for any supplier and does not name or disparage the competitor.
- No competitor price, discount or margin appears unless sourced from a public document or the customer with permission.
- Our proof points cite our own documentation, not marketing adjectives.

## Guardrails
- Fair competition: no disparagement, no false or unverifiable comparisons (comparative advertising rules apply if
  material is shown to customers), no use of confidential documents of competitors or of another bidder's offer.
- Internal use: mark the card internal; customer-facing comparisons need marketing and legal approval.
- Do not invent Company facts (ranges, services, delivery promises); cite Confluence or Drive or mark "to confirm".
- Do not collect personal data on competitor employees beyond public roles.
