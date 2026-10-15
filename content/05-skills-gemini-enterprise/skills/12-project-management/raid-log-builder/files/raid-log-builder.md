---
name: raid-log-builder
description: "Builds or refreshes a RAID log (risks, assumptions, issues, dependencies) for a project: each risk written as cause, event, effect, scored probability × impact on 1-5 scales with defined anchors, a response strategy (avoid, reduce, transfer, accept), owner, trigger and review date, plus assumptions to validate, open issues by severity and cross-team dependencies. Use whenever a project needs a risk register, a pre-mortem, a risk review before a gate, or when someone worries about what could go wrong, even if they only say 'list the risks'. Triggers - RAID log, risk register, risk assessment, pre-mortem, dependencies list, issue log, registre des risques, analyse de risques, matrice des risques, journal RAID, dépendances projet, qu'est-ce qui peut mal tourner."
---

# RAID log builder

Gives a project team a living register of what could go wrong, what they assume, what is already wrong and what they
depend on, scored the same way every time so the top of the list really is the top.

## When to use
- Project start, phase gate or go / no-go: build the first RAID log or run a pre-mortem.
- Monthly or pre-steering risk review: rescore, close, escalate.
- Many emails and tickets mention problems and nobody has a consolidated view.
- Not for: the weekly status (use `project-status-report`), a post-incident analysis (use `incident-postmortem`), the
  plan and critical path (use `project-plan-builder`), or screening an AI use case (use `ai-use-case-risk-screen`).

## Inputs
- Project name and scope summary, or the charter (required; search Drive and Confluence first).
- Existing RAID log to update (optional, default: build a new one).
- Key dates (go-live, peak season) that set proximity (optional).
- Project tolerances (optional, default: the impact anchors below).

## Sources
1. **Drive and Confluence**: charter, plan, previous RAID log or risk sheet, lessons learned of similar projects
   (a known risk from past projects is a strong candidate).
2. **Jira**: blocked and flagged issues, issues linked with "is blocked by" across projects (dependencies), bugs
   with High/Highest priority, overdue items on the critical path.
3. **Gmail, Chat and Slack**: threads with words like delay, blocked, risk, concern, escalation, retard, bloqué,
   inquiet; supplier delay notices.
4. **Meet transcripts in Drive**: risks raised in project meetings and not yet logged.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Harvest candidate items from the sources and the user. Classify each:
   **Risk** = uncertain future event; **Issue** = already happening; **Assumption** = believed true, not verified;
   **Dependency** = something the project needs from outside its control (team, supplier, other project).
2. Rewrite each risk as **cause → event → effect** ("Because the supplier has a single dyeing site, a production
   stop may occur, delaying the spring range in-store date"). Reject vague risks ("budget", "planning").
3. If building from scratch, run a quick **pre-mortem**: "It is go-live + 3 months and the project failed: why?"
   Cover people, process, technology, suppliers, legal / compliance, data, season / peak timing.
4. Score **Probability (P)** 1–5: 1 < 10 %, 2 = 10–30 %, 3 = 30–50 %, 4 = 50–80 %, 5 > 80 %.
   Score **Impact (I)** 1–5 on the worst of: schedule (1 = < 1 week, 3 = misses a milestone, 5 = misses go-live or
   season), cost (1 = negligible, 3 = uses the contingency, 5 = beyond tolerance), scope / quality (5 = must-have
   lost or safety issue), reputation / customers (5 = public or customer-safety exposure). Use project tolerances
   instead if sourced.
5. **Score = P × I** (1–25). Bands: 15–25 critical (escalate to sponsor), 8–14 high (active response, weekly review),
   4–7 medium (monitor), 1–3 low (accept). Show proximity (when could it happen) to break ties.
6. Give each risk a **response**: avoid (change plan), reduce (lower P or I), transfer (contract, insurance,
   partner), accept (with contingency); plus an early-warning **trigger** and a single named **owner** role.
7. Issues: severity (critical / major / minor), action, owner, due date. Assumptions: how and by when to validate;
   an invalidated assumption becomes a risk or an issue. Dependencies: provider, what is needed, need-by date,
   status, consequence if late.
8. When updating, show deltas: new, rescored (old → new), closed, escalated.

## Output format
```markdown
# RAID log — <Project> · <date> · v<N>
**Summary:** <N> risks (<n> critical) · <N> open issues · <N> assumptions to validate · <N> dependencies (<n> late)
**Escalate now:** <critical risks / blocking issues, one line each>

## Risks
| ID | Risk (cause → event → effect) | P | I | Score | Band | Proximity | Response (type: action) | Trigger | Owner | Review |
|----|-------------------------------|---|---|-------|------|-----------|-------------------------|---------|-------|--------|

## Heat map
| P \ I | 1 | 2 | 3 | 4 | 5 |
|-------|---|---|---|---|---|
| 5 | | | | | R3 |

## Issues
| ID | Issue | Severity | Impact | Action | Owner | Due | Source |
|----|-------|----------|--------|--------|-------|-----|--------|

## Assumptions
| ID | Assumption | Validation method | By | Owner | Status |
|----|-----------|-------------------|----|-------|--------|

## Dependencies
| ID | We need | From | Need-by | Status | If late |
|----|---------|------|---------|--------|---------|

## Changes since last version
- New: … · Rescored: R2 9 → 16 · Closed: … · Escalated: …
```

## Quality checks
- Every risk is written as cause → event → effect and has P, I, score, response, trigger and owner.
- Every score equals P × I and its band matches the thresholds; the table is sorted by score, then proximity.
- No item is both a risk and an issue; issues are things already happening, with a source.
- Every dependency has a need-by date; late ones are flagged in the summary.
- Items from sources carry a link; items from the pre-mortem are labeled *pre-mortem*.

## Guardrails
- Scores are a team judgment aid, not facts: say so, and invite the owner to challenge them.
- Owners are roles or named people agreed by the user; never assign blame for issues.
- Keep supplier-specific or legal risks factual and neutral; mark the log confidential if it names suppliers or
  contract terms.
- Draft only: do not create Jira issues, notify owners or edit the shared log without explicit confirmation.
