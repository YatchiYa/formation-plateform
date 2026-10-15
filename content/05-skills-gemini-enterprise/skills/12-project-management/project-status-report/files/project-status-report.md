---
name: project-status-report
description: "Writes a weekly or bi-weekly project status report with an evidence-based RAG rating per dimension (schedule, scope, cost, risks), using explicit thresholds rather than gut feeling: progress vs plan from Jira, milestone forecast, top risks and issues, decisions and help needed, next steps. Use whenever a project manager, product owner or lead has to report project progress to a sponsor, a manager or a steering group, even if they just say 'where are we on this project'. Triggers - status report, project update, weekly status, RAG status, flash report, progress report, point d'avancement, reporting projet, météo projet, statut hebdo, rapport d'avancement, où en est le projet."
---

# Project status report

Gives a sponsor a two-minute read of a project: the overall RAG with its reason, what moved, what is at risk, and the
decisions they need to take. RAG is computed from thresholds, so green means green.

## When to use
- Weekly or bi-weekly reporting to a sponsor, manager or programme office.
- Before a 1:1 with a sponsor or a steering meeting, to have the facts ready.
- When the team says "it's fine" but dates keep moving and a factual view is needed.
- Not for: the full steering deck with options (use `steering-committee-pack`), a team standup (use
  `engineering-standup-summary`), building the risk register (use `raid-log-builder`), or a roadmap narrative for
  stakeholders (use `roadmap-update`).

## Inputs
- Project name, or Jira project / epic key (required).
- Reporting period (optional, default: last 7 days) and audience (optional, default: sponsor).
- Baseline plan: milestones with baseline dates, budget and tolerances (optional; search the charter and plan in
  Drive / Confluence first; if absent, the cost dimension is rated "not reported").
- Previous status report (optional; found in Drive or Confluence to show the trend).

## Sources
1. **Jira**: issues in the epic or project — done vs planned this period, status changes, overdue items, blocked
   issues, issues flagged or labeled risk / blocker, fix versions and their dates.
2. **Drive and Confluence**: charter and plan (baseline dates, tolerances), previous status report, RAID log,
   budget tracker sheet.
3. **Gmail, Chat and Slack**: escalations, decisions made in threads, supplier or partner delays in the period.
4. **Calendar and Meet transcripts in Drive**: decisions and actions from project meetings this period.
5. **Databricks or Tableau**: the project's outcome KPI if one is tracked (e.g. pilot store adoption rate).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Set the period and pull the baseline (milestones, tolerances) and the previous RAG for trend arrows (↑ ↓ →).
2. Measure **progress**: items done vs planned in the period; % of scope done (story points or count, say which);
   overdue items; items blocked > 5 working days.
3. **Forecast each milestone**: forecast date = baseline unless evidence of slip (dependency late, critical item
   overdue, team statement). Slip = forecast − baseline in working days.
4. Rate each dimension with these default thresholds (replace them with the project's tolerances if found, and
   cite them):
   - **Schedule**: Green = all milestones forecast within baseline; Amber = a milestone slips but within tolerance
     (default ≤ 10 working days) or is recoverable with a plan; Red = slip beyond tolerance or a go-live date at risk.
   - **Cost**: Green = forecast at completion ≤ budget + 0 %; Amber = 0 to +5 % or within tolerance; Red = beyond
     tolerance. Only with sourced figures; otherwise "not reported".
   - **Scope**: Green = no unapproved change; Amber = change requests pending decision; Red = must-have deliverable
     dropped or uncontrolled scope growth > 10 % of items.
   - **Risks / issues**: Green = no risk scored ≥ 15 (P × I); Amber = a risk ≥ 15 with a response in progress;
     Red = an open issue blocking the critical path or a risk ≥ 15 without a response.
5. **Overall RAG** = the worst dimension, unless the PM explicitly overrides with a written reason (show both).
   Red always comes with a recovery plan and a decision or help request.
6. Write **highlights** (max 5, outcomes not activities), **next period** (max 5), **top 3 risks/issues** with owner
   and due date, and **decisions needed** framed as a question, options, recommendation, deadline.
7. Keep it to one screen. Put details (issue lists) in an appendix with links.

## Output format
```markdown
# <Project> — status <DD/MM> (period <from–to>)
**Overall: 🟢/🟠/🔴 <one-line reason>** · trend <↑/↓/→ vs last report>

| Dimension | RAG | Trend | Why (evidence) |
|-----------|-----|-------|----------------|
| Schedule | | | <milestone X forecast +N days> ([link](…)) |
| Scope | | | |
| Cost | | | <or "not reported — no budget tracker found"> |
| Risks / issues | | | |

### Milestones
| Milestone | Baseline | Forecast | Slip (wd) | Status |
|-----------|----------|----------|-----------|--------|

### Done this period
- <outcome> ([link](…))

### Next period
- <outcome> — owner

### Top risks and issues
| # | Risk/Issue | Score (P×I) | Response | Owner | Due |
|---|------------|-------------|----------|-------|-----|

### Decisions / help needed
- **<Question>?** Options: A / B. Recommended: A because … Needed by <date> from <who>.

_Progress basis: <story points / issue count>. Sources: <list with status>._
```

## Quality checks
- Each RAG cell cites the rule applied and a piece of evidence; no RAG without a reason.
- Overall RAG equals the worst dimension, or the override reason is written.
- Every red or amber has a recovery action with an owner and a date.
- Milestone slip = forecast − baseline, computed in working days and consistent with the table.
- Highlights are outcomes ("pilot live in 3 stores"), not activity ("worked on pilot").
- Fits on one screen above the appendix.

## Guardrails
- No watermelon reporting: if the evidence says amber, do not write green because the team feels confident; show the
  evidence and let the PM override in writing.
- Never invent costs, percentages of completion or dates; unknowns are shown as unknown.
- Name people only as owners of actions; never blame individuals for delays.
- Draft only: do not send the report, post it in Chat / Slack or change Jira statuses without explicit confirmation.
