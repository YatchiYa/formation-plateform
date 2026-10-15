---
name: decision-memo
description: "Writes a decision memo that gets a clear yes or no: context and the exact question, 2-4 real options including do-nothing, weighted criteria and a scored comparison, recommendation with the trade-off accepted, DACI roles, reversibility (one-way vs two-way door), risks with mitigations and the date by which the decision is needed. Use whenever someone must get a decision from a manager, committee or peers, choose between options, or document why a choice was made, even if they just say 'I need to convince my boss'. Triggers - decision memo, decision doc, options paper, recommend an option, DACI, choose between, note de décision, note d'arbitrage, aide à la décision, demander un arbitrage, comparer des options, documenter une décision."
---

# Decision memo

Produces a one-to-two-page memo that frames the choice fairly, makes the recommendation explicit and tells the
decider exactly what is expected of them and by when.

## When to use
- An arbitration is needed: budget, supplier, tool, organization, product range, store layout, launch date.
- Several stakeholders disagree and the options must be laid out neutrally.
- A decision was taken and must be documented for later (why we chose X).
- Not for: a full financial business case with NPV (use `business-case-builder`), a software architecture decision
  record (use `architecture-decision-record`), or decisions to request from a steering committee as a full deck (use
  `steering-committee-pack`).

## Inputs
- The decision to make, in one sentence (required).
- The options known so far and the constraints (optional, default: derived from sources plus a do-nothing option).
- Decider and deadline (optional, default: asked once if not found).
- Data on costs, impacts or risks (optional; never invented).

## Sources
1. **Drive and Confluence**: background docs, previous related decisions, strategy or policy that constrains the
   choice, quotes or estimates.
2. **Gmail, Chat and Slack**: the discussion threads where options and objections were raised — capture each
   stakeholder's position with a link.
3. **Jira**: the epic or tickets affected, dependencies, effort estimates.
4. **Databricks (SQL MCP or Polco) and Tableau**: the data supporting impact estimates (volumes, sales, costs).
5. **Calendar**: the decision meeting or forum and its date.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Write the **decision question** as a choice: "Should we <A> or <B> by <date>?" — not a topic.
2. Write the **context** in ≤ 5 sentences: why now, what happens if we do not decide, the constraints.
3. List **2–4 options**, always including do-nothing or status quo, and only real options (no strawmen). Give each a
   one-line description, cost, benefit, effort, time to impact.
4. Agree **criteria** (3–6) with weights summing to 100 %, derived from the stated goals (e.g. customer impact,
   cost, time to market, risk, sustainability, team load). Score each option 1–5 per criterion with a one-line
   justification; show the weighted total. Note the most sensitive criterion: would a 10-point weight change flip
   the winner?
5. Classify **reversibility**: two-way door (cheap to undo → decide fast, at lower level) vs one-way door (costly or
   impossible to undo → more data, higher level). Say what would trigger a reversal.
6. Write the **recommendation** with the trade-off explicitly accepted ("we accept higher cost for 6 weeks faster
   launch"). Recommend the option with the highest weighted total; if you recommend another one, revise the weights
   or scores openly or state in the recommendation which criterion overrides the total and why.
7. Set **DACI** roles: Driver, Approver (one person), Contributors, Informed. If the approver is unknown, ask.
8. Add **risks** (top 3, with mitigation), **dissenting views** with links, and **next steps** if approved.

## Output format
```markdown
# Decision: <question>
**Needed by:** <date> · **Approver:** <name/role> · **Reversibility:** one-way | two-way door
**Recommendation:** <option> — <one sentence why + trade-off accepted>

## Context
…

## Options
| | Option A | Option B | Do nothing |
|-|----------|----------|------------|
| Description | | | |
| Cost | | | |
| Benefit | | | |
| Time to impact | | | |

## Comparison
| Criterion (weight) | A | B | Do nothing |
|--------------------|---|---|------------|
| … (30 %) | 4 — <why> | | |
| **Weighted total** | | | |
_Sensitivity: …_

## Risks & mitigations
- …

## Dissenting views
- <stakeholder>: <position> ([link](…))

## DACI
Driver: … · Approver: … · Contributors: … · Informed: …

## If approved — next steps
1. …
```

## Quality checks
- The recommendation is stated in the first 5 lines, with the trade-off.
- At least 2 options plus do-nothing; each has the same rows filled in.
- Weights sum to 100 % and the weighted totals are arithmetically correct.
- The recommended option has the highest weighted total, or the override is explained in the recommendation line.
- The whole memo, including option names, table labels and headings, is in the user's language.
- Every cost, figure and stakeholder position has a source or is labeled *estimate* / *assumption*.
- Exactly one Approver is named, or a question asks for one.
- The memo body fits in about 2 pages (≤ 900 words).

## Guardrails
- Present dissent fairly and do not drop inconvenient options or data to make the recommendation look stronger.
- The memo supports a human decision; the model does not decide.
- For decisions affecting people's jobs, pay or contracts, add a line that HR and, where required, employee
  representatives must be involved per local law.
- Do not send the memo or schedule the meeting without the user's confirmation.
