---
name: engagement-survey-analyzer
description: "Analyzes official company engagement survey results (HR-run waves such as the baromètre social, eNPS) and free-text comments for a team, store, warehouse or department: scores vs previous wave and benchmark, key drivers, themes and sentiment from comments with representative anonymized verbatims, anonymity protection (no group under 5 respondents, no re-identification), and a focused action plan with 2-3 commitments and a team feedback session. Use whenever a manager or HRBP receives survey results, prepares a results restitution, or must build an action plan, for a manager-run team pulse use team-health-check instead; use it even if they only paste comments and ask 'what do people say'. Triggers - engagement survey, company survey results, survey results, employee comments, eNPS, action plan from survey, baromètre social, enquête d'engagement, résultats d'enquête, commentaires collaborateurs, plan d'action enquête, restitution enquête."
---

# Engagement survey analyzer

Turns survey numbers and comments into a few clear messages and a short action plan the team co-owns, while fully
protecting respondents' anonymity.

## When to use
- Results of an engagement or pulse survey are out for a team, store, site or department.
- A manager prepares the restitution meeting with their team.
- An HRBP compares several teams to see where to support.
- Not for: designing a short team pulse from scratch (use `team-health-check`), exit interview themes (use
  `exit-interview-synthesizer`), or a broad people change communication (use `change-communication-plan`).

## Inputs
- Results export: question scores, response counts, comments (required).
- Scope and population size, response rate (required; if absent, the anonymity check uses response counts only).
- Previous wave and benchmark if available (optional).
- Question-to-driver mapping of the survey tool (optional, default: the skill groups questions into themes and
  says so).

## Sources
1. **Drive**: survey exports (Sheets, CSV, PDF), the previous wave, the survey methodology doc.
2. **Confluence**: survey guide, benchmark explanation, action-plan template.
3. **Tableau**: published survey dashboard views, if the organization uses one (read aggregated views only).
4. **Databricks**: aggregated survey tables, only at grouping levels ≥ 5 respondents.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Anonymity gate (first, always)**:
   - Any group (team, filter combination, demographic cut) with **< 5 respondents** is not shown; merge it into a
     larger group or drop it. Also block differencing (two overlapping cuts that reveal a small group).
   - Comments: remove names, roles that identify one person ("the only night-shift forklift driver"), specific
     events, dates; paraphrase anything identifying. Never try to guess who wrote a comment.
2. **Read the numbers**: response rate (flag < 50% as a reading limit), score per question and theme,
   favorable/neutral/unfavorable split, change vs last wave. Treat changes < 5 points or on < 20 respondents as
   *not meaningful* unless the tool states significance.
3. **Drivers**: if the tool provides driver/impact analysis, use it. Otherwise, rank themes by
   `importance proxy (correlation or tool impact, if available) × gap (100 − favorable %)` and state the method.
   Priority = high impact, low score.
4. **Comment analysis**: code each comment into themes (workload, management, recognition, career, tools,
   schedules and work-life balance, safety, customer and sport, pay — pay noted as a theme only). Count mentions,
   sentiment (+/−/mixed), and pick 1–2 representative anonymized verbatims per theme. Show both strengths and
   pain points.
5. **3 key messages**: one strength to protect, two priorities. Each backed by score + comment theme.
6. **Action plan**: 2–3 commitments max, co-built with the team. For each: problem, action, owner, date,
   how the team will see progress. Store example: "Planning published 3 weeks ahead instead of 1".
7. **Restitution meeting** outline (45–60 min): share results honestly, thank, ask "what is behind this?",
   choose actions together, date the follow-up.

## Output format
```markdown
# Survey readout — <scope>, <wave>
_Respondents: <n>/<population> (<rate>%). Groups < 5 hidden: <n>. Sources: <export, previous wave>_

## 3 key messages
1. 💪 <strength> — <score/trend> · <comment theme>
2. 🎯 <priority> — …
3. 🎯 <priority> — …

## Scores by theme
| Theme | Favorable % | Δ vs last wave | Benchmark | Reading |
|-------|-------------|----------------|-----------|---------|

## What comments say
| Theme | Mentions | Sentiment | Representative verbatim (anonymized) |
|-------|----------|-----------|--------------------------------------|

## Action plan (to co-build with the team)
| Problem | Commitment | Owner | Date | Visible sign of progress |
|---------|-----------|-------|------|--------------------------|

## Restitution meeting outline
1. …

_Method notes: <driver method, significance limits, hidden groups>_
```

## Quality checks
- No table row, verbatim or cut refers to a group of fewer than 5 respondents.
- No verbatim contains a name, unique role, date or detail that could identify its author.
- Every key message cites a score and a comment theme.
- Changes called meaningful meet the stated threshold or the tool's significance.
- Action plan has ≤ 3 commitments, each with owner and date.

## Guardrails
- Anonymity is absolute: refuse to identify respondents, to analyze one person's answers, or to slice data below
  5 respondents, even if the user asks.
- Survey results must not be used to evaluate or sanction a manager or teammate individually.
- Do not report health, union or other sensitive topics beyond the theme level; route serious signals
  (harassment, safety) to HR without trying to locate the author.
- Never invent benchmarks or company averages; use only those in the export or official docs.
- Draft only: do not send results to the team without the user's confirmation.
