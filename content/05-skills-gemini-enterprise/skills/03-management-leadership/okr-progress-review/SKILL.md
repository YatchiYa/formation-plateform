---
name: okr-progress-review
description: "Scores progress on a team's OKRs mid-period or at period end: pulls current KR values from Databricks, Tableau, Jira and status updates, computes linear progress vs expected pace, sets a confidence level (on track, at risk, off track) with the reason, names the blockers and the decisions or help needed, and drafts the update for the next level up. Use whenever someone prepares an OKR check-in, a quarterly business review, a monthly goals update, or asks 'are we on track', even if they don't say OKR. Triggers - OKR check-in, OKR progress, are we on track, score our OKRs, quarterly review, goals update, point d'avancement OKR, où en sont nos OKR, revue trimestrielle, bilan des objectifs, est-ce qu'on est dans les clous, scoring des OKR."
---

# OKR progress review

Tells a team, in one page, where each key result stands against the expected pace, how confident they are, and what
they need to get back on track.

## When to use
- Weekly, monthly or mid-quarter OKR check-ins.
- End of period scoring and preparing the next cycle.
- A leader asks for a short status of goals for a business review.
- Not for: writing new OKRs (use `okr-builder`), investigating why one metric dropped (use
  `metric-anomaly-investigator`), or a project's RAG status report (use `project-status-report`).

## Inputs
- The OKR set: doc link or text (required; search Drive and Confluence for the team's current OKRs before asking).
- Review date (optional, default: today) and period start/end (optional, default: current calendar quarter).
- Audience of the update (optional, default: the next management level).

## Sources
1. **Drive and Confluence**: the OKR doc with baselines, targets and owners; previous check-ins (to show trend in
   confidence); the internal scoring scale if one exists.
2. **Databricks (SQL MCP or Polco)**: current values of metric KRs, at the same grain and definition as the baseline
   (same filters, same calendar: week-to-date vs N-1 comparable days). Show each query or Polco question.
3. **Tableau**: dashboards already tracking the KR; take the value and the dashboard link and its refresh date.
4. **Jira**: progress of initiative epics linked to KRs (done/total issues, blocked issues, slipped due dates).
5. **Slack, Chat, Gmail**: owners' latest status messages and blockers mentioned.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. For each KR, get the **current value**, its source and its as-of date. If the source definition differs from the
   OKR's (different scope or filter), say so instead of mixing numbers.
2. Compute **progress** = (current − baseline) / (target − baseline), capped 0–1.2. For decrease KRs the formula
   still works (negative denominators). Binary KRs: 0 or 1.
3. Compute **expected pace** = elapsed share of the period (e.g. week 7 of 13 → 0.54). For seasonal metrics
   (ski, back to school, Christmas peaks), compare with the N-1 cumulative share at the same date instead of a
   straight line, and say which method was used.
4. Set **status** per KR: on track if progress ≥ 0.9 × expected; at risk between 0.7 and 0.9 × expected; off track
   below 0.7 × expected. Let the owner's latest statement adjust **confidence** (high/medium/low) with the reason.
   For aspirational KRs, read 0.7 at period end as success.
5. Roll up per objective as the average of its KRs (unweighted unless the OKR doc says otherwise) and show it next
   to the KRs — never alone.
6. For each at-risk or off-track KR: the main driver (data, not opinion), the blocker, and one **ask** (decision,
   resource, dependency) with who can give it.
7. Write the **headline**: one sentence on overall state, then the 3 most important facts.
8. At period end, add the **learning** per KR: was the target well set, what to keep, stop or change next cycle.

## Output format
```markdown
**OKR check-in — <Team>, <period> · week <n>/<N> · expected pace <x>**
<Headline sentence>

| KR | Baseline | Current (as of) | Target | Progress | Expected | Status | Confidence |
|----|----------|-----------------|--------|----------|----------|--------|------------|
| KR1.1 … | … | … ([source](…)) | … | 0.42 | 0.54 | 🟠 at risk | medium — <reason> |

### Objective roll-up
- O1 <name>: <avg> (<n> KRs on track / at risk / off track)

### What needs attention
| KR | Driver | Blocker | Ask (to whom) |
|----|--------|---------|---------------|

### Update for <audience> (≤ 120 words, ready to paste)
<text>

_Method: linear pace | N-1 seasonal pace · Values not found: <list>_
```

## Quality checks
- Every current value has a source link or query and an as-of date; missing values are shown as "not found",
  never estimated silently.
- Progress and expected pace figures are recomputable from the table.
- Each at-risk or off-track KR has a driver and an ask.
- The update for the audience contains no number that is not in the table.
- The pace method (linear or seasonal) is stated.

## Guardrails
- Never fabricate or round up KR values to look on track; if data is late or inconsistent, say so.
- OKR status is about team goals, not individual performance: do not rank owners or comment on people.
- Do not post the update or change the OKR doc without explicit confirmation.
