---
name: architecture-decision-record
description: "Writes an Architecture Decision Record in Nygard or MADR format: context and forces, decision drivers, options considered with honest pros and cons, the decision and its rationale, positive and negative consequences, reversibility and a revisit trigger, and links to the decisions it supersedes. Use whenever a team has made or is about to make a significant technical choice (framework, database, build vs buy, API style, cloud service, event versus sync call) and needs it recorded, even if they only say 'note why we chose X'. Triggers - write an ADR, architecture decision record, record this decision, why did we choose, document technical decision, rédige un ADR, décision d'architecture, documenter un choix technique, pourquoi on a choisi, trace de décision."
---

# Architecture decision record

Records one significant technical decision so that a future engineer knows what was decided, why, what was traded
away and when to reconsider it, without rereading months of threads.

## When to use
- A technical choice was just made in a meeting, design review or Slack debate and must be written down.
- A team is choosing between options and wants the trade-offs laid out before deciding.
- An old decision is being reversed and the new ADR must supersede the old one.
- Not for: the full design of a feature (use `tech-spec-writer`), a non-technical business decision (use
  `decision-memo`), or a general how-to page (use `knowledge-capture-page`).

## Inputs
- The decision or the question being decided (required).
- Options considered and the outcome, if already decided (optional, default: extracted from sources; if no decision
  yet, status is Proposed).
- Format (optional, default: the team's existing ADR format found in GitHub or Confluence, else MADR).
- ADR number and location (optional, default: next number in the repo's ADR folder, e.g. docs/adr).

## Sources
1. **GitHub**: the repo's existing ADR folder (docs/adr, doc/architecture/decisions, adr) for numbering, format and
   related decisions; the PR or issue where the choice was debated.
2. **Confluence and Drive**: design docs, review notes, meeting notes or Meet transcripts where the decision was
   discussed; architecture principles or tech radar if the organization has one.
3. **Slack, Google Chat and Gmail**: the debate thread, for the real forces and rejected options.
4. **Jira**: the epic or spike that triggered the decision.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. State the **decision question** in one sentence ("How do store POS terminals get stock updates?"). One ADR = one
   decision. If several are tangled, propose splitting.
2. Write **Context**: the situation and the forces in tension (latency vs consistency, team skills, cost, vendor
   lock-in, regulatory, deadline). Value-neutral, factual, cited.
3. List **decision drivers** (3–6), ranked if the sources show priorities.
4. List **options** (at least two, including the status quo when relevant). For each: short description, pros, cons,
   scored against each driver (++ / + / 0 / − / −−). Steelman rejected options; an ADR that makes alternatives look
   stupid is not credible.
5. Write the **Decision** in active voice ("We will publish stock changes as events on the existing bus; POS
   terminals keep a local cache"). If no decision is in the sources, set status Proposed and write "Recommended
   option" with reasoning, clearly labeled.
6. Write **Consequences**: what becomes easier, what becomes harder, new risks, follow-up work (with Jira keys if
   they exist), cost of reversal. Include at least one negative consequence.
7. Add **reversibility** (one-way or two-way door) and a **revisit trigger** (a measurable condition or date: "if
   event lag p95 exceeds 5 s in peak season").
8. Link related ADRs and mark superseded ones (status Superseded by ADR-NNNN).
9. **Header facts**: the date is the decision date from a source, else « [YYYY-MM-DD — to confirm] », never a
   guessed date; deciders and context forces not found in a source are « [to confirm] » or labeled *assumption*.
   If the user says the decision is made (« our decision »), status is Accepted.

## Output format
```markdown
# ADR-<NNNN>: <Decision in a short noun phrase>

- **Status:** <Proposed | Accepted | Superseded by ADR-NNNN | Deprecated>
- **Date:** <YYYY-MM-DD> · **Deciders:** <names/roles from sources> · **Consulted:** <…>
- **Related:** <ADR links, design doc, Jira epic>

## Context and problem statement
<facts and forces, 5–10 lines, with source links>

## Decision drivers
1. …

## Considered options
| Option | <Driver 1> | <Driver 2> | <Driver 3> | Notes |
|--------|-----------|-----------|-----------|-------|

### Option A — <name>
- Pros: … · Cons: …

## Decision outcome
**Chosen option: <…>**, because <rationale tied to the drivers>.

### Consequences
- Positive: …
- Negative: …
- Follow-up: <work items>

### Reversibility and revisit
<one-way/two-way door> · Revisit if: <measurable trigger or date>
```
For Nygard format, use only: Title, Status, Context, Decision, Consequences.

## Quality checks
- Exactly one decision; the title names the decision, not the problem.
- At least two options; each has at least one pro and one con.
- The rationale references the drivers, and at least one negative consequence is stated.
- Deciders and date come from sources or are left as placeholders, never invented.
- The revisit trigger is measurable or dated.
- The draft fits on two screens; detail goes to linked design docs.

## Guardrails
- Do not mark a decision Accepted unless a source shows the deciders accepted it; otherwise Proposed.
- Do not attribute opinions to named people beyond what the sources show; record arguments, not who lost the debate.
- ADRs are immutable once accepted: to change one, write a new ADR that supersedes it.
- Draft only. Do not commit to the repo or publish on Confluence until the user confirms.
