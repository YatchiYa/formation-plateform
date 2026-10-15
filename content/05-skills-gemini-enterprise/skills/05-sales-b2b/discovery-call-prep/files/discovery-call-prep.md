---
name: discovery-call-prep
description: "Prepares a B2B discovery call or first meeting with a club, school, company or local authority: call objective, hypotheses to test, a 30-minute agenda, SPIN questions in the right order, MEDDICC-lite qualification gaps, likely objections and the next step to secure. Use whenever a seller has a first call, a discovery meeting or a requalification meeting coming up, or asks what to ask a prospect, even if they only say 'I have a call with X tomorrow'. Triggers - discovery call, prep my sales call, first meeting with prospect, what should I ask, qualification questions, MEDDIC, SPIN, préparer un rendez-vous client, préparer mon appel de découverte, questions de découverte, qualifier un prospect, premier rendez-vous."
---

# Discovery call prep

Turns what we know about an account into a focused 30-minute discovery plan: what to learn, in what order, and which
next step to ask for, so the seller leaves the call qualified or disqualified, not just "it went well".

## When to use
- A first call or meeting with a prospect is booked.
- A deal has stalled and needs requalification ("do we really know who decides?").
- A new seller takes over an opportunity mid-cycle.
- Not for: background research alone (use `account-research`), a general internal meeting brief (use `meeting-prep`),
  or writing the recap after the call (use `sales-call-recap`).

## Inputs
- Organisation and the person or people attending, with roles (required).
- Call date and duration (optional, default: from Calendar; 30 minutes).
- Stage: first contact, requalification or handover (optional, default: first contact).
- What the user hopes to sell (optional, default: open).

## Sources
1. **Calendar**: the event, attendees, description, attached documents.
2. **Airtable**: account and opportunity record, stage, known qualification fields, last next step.
3. **Gmail**: the thread that led to the meeting; exact words the prospect used about their need.
4. **Drive**: past proposals, notes and `account-research` briefs on this organisation; segment playbooks.
5. **Databricks (SQL or Polco)**: past orders of this account, if a B2B sales table exists.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Set one call objective** and one minimum acceptable outcome. Example: objective "agree on a kit-fitting session for
   the 14 teams"; minimum "know who signs and the budget window".
2. **Write 3 hypotheses** about their situation and pain, each with its evidence and the question that tests it.
   Example for a club: "Kit orders are fragmented by team managers → costs and delays" (evidence: three separate
   emails from different coaches).
3. **Build the SPIN question path** (ask few Situation questions; the research already answers most of them):
   - Situation (2 max): only what research could not find (number of teams, current supplier, renewal timing).
   - Problem (3): "What happens when a size is missing at the start of the season?"
   - Implication (2–3): make the cost of the problem visible (volunteer hours, players without kit on match day,
     sponsor visibility, budget overrun, injury risk with worn equipment).
   - Need-payoff (2): let them say the value ("If every player had the right size on day one, what would it change?").
4. **Plan the MEDDICC-lite qualification** and mark each letter Known / Partial / Gap from the sources:
   Metrics (their success measure), Economic buyer (who releases the money: treasurer, bursar, HR director, elected
   official), Decision criteria (price, durability, customisation, delivery date, CSR), Decision process (steps, dates,
   vote of a board or council), Paper process (purchase order, quote validity, public procurement), Identify pain,
   Champion (who sells for us inside), Competition (incumbent supplier, local shop, do nothing). Each Gap gets one
   question in the agenda.
5. **Anticipate 3 objections** likely for this segment and stage (e.g. "we are happy with our supplier", "too early in
   the season", "we must go through a tender"), with an exploring question for each (see `objection-handler`).
6. **Design the agenda** for the duration: purpose and time check (2 min), their context (8), problems and impact (10),
   what good looks like and how they decide (6), next step (4). Keep 60 % of talk time for the prospect.
7. **Define the next step to ask for**, concrete and dated: site visit, size collection, sample or trial, meeting with
   the economic buyer, receipt of the specifications. A "send me a brochure" is not a next step.

## Output format
```markdown
# Discovery call — <Organisation> · <date, time> · <duration>
**Objective:** … · **Minimum outcome:** … · **Attendees:** <name — role — what they care about>

### What we know (3 lines max)
- … ([source](…))

### Hypotheses to test
| # | Hypothesis | Evidence | Test question |
|---|-----------|----------|---------------|

### Agenda
| Min | Block | Goal |
|-----|-------|------|

### Questions (in order)
**Situation:** 1. …
**Problem:** …
**Implication:** …
**Need-payoff:** …

### Qualification (MEDDICC-lite)
| Letter | Status | What we know | Question to ask |
|--------|--------|--------------|-----------------|
| M Metrics | Gap | — | … |

### Likely objections
- "<objection>" → explore with: "<question>"

### Next step to secure
- <dated action + who attends>; fallback: <smaller step>
```

## Quality checks
- No more than 2 Situation questions; at least 2 Implication questions.
- Every MEDDICC Gap has a matching question in the question list.
- Every hypothesis cites its evidence or is marked *assumption*.
- The next step is dated and involves a commitment from the prospect, not only from us.
- Agenda timings add up to the call duration.

## Guardrails
- Do not prepare promises: no prices, discounts, delivery dates or stock availability unless the user provides them.
- For a public buyer in a live tender, the call must not discuss the tender outside the official Q&A channel; warn the
  user and route to `tender-response-builder`.
- Attendee notes stay professional (role, priorities, stated preferences); no personal or sensitive details.
- Read only; Airtable updates are drafted in `sales-call-recap` and applied after user confirmation.
