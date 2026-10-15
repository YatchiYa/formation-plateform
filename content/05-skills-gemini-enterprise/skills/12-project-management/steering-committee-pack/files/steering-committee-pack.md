---
name: steering-committee-pack
description: "Prepares the content of a steering committee (COPIL) pack: one-slide executive status with RAG, progress against milestones and budget, the decisions required framed as question, options with trade-offs, recommendation and deadline, top risks and escalations, and a pre-read email plus the minutes template. Use whenever a project or programme lead prepares a steering committee, a sponsor review, a gate or go / no-go meeting, even if they just say 'I have a COPIL next week'. Triggers - steering committee, steerco, sponsor review, project board, go no-go, gate review, decision pack, COPIL, comité de pilotage, préparer le copil, support de comité, arbitrages, revue de projet, dossier de décision."
---

# Steering committee pack

Gives a project lead a steering pack built around decisions, not activity: the committee leaves with every decision
taken, owned and dated.

## When to use
- A steering committee, sponsor review, programme board or phase gate is coming.
- A project is red or amber and needs an arbitration (scope, date, budget, resources).
- A go / no-go decision must be prepared with explicit criteria.
- Not for: the weekly status for the team or sponsor (use `project-status-report`), a standalone decision document
  outside a committee (use `decision-memo`), or designing the slides visually (use `presentation-storyline`).

## Inputs
- Project and committee date, members and duration (required; Calendar first).
- Latest status, plan, budget tracker, RAID log (required; search Drive, Confluence and Jira before asking).
- The decisions the lead wants (optional; the skill proposes them from red / amber items and pending changes).
- Previous committee minutes (optional, used to check actions and earlier decisions).

## Sources
1. **Calendar**: the committee event, attendees, attached documents.
2. **Drive and Confluence**: previous pack and minutes, charter (tolerances, governance), plan, budget tracker,
   RAID log, change requests.
3. **Jira**: milestone and epic status, blocked items, delivered scope since last committee.
4. **Gmail, Chat and Slack**: escalations and pending arbitrations raised since the last committee.
5. **Databricks or Tableau**: outcome KPIs of the project (e.g. pilot results), with query or dashboard link.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Check the **actions and decisions from the last committee**: done, late, or reopened. Reopened decisions need a
   stated new fact, otherwise flag them.
2. Build the **executive status**: overall RAG (thresholds from `project-status-report` or the charter tolerances),
   3 achievements, milestone table baseline vs forecast, budget: approved, committed, actuals, forecast at completion
   and variance (only sourced numbers).
3. Identify **decisions required**: anything beyond tolerance (management by exception), change requests, resource
   conflicts, go / no-go. Each decision follows: **question** (closed, answerable in the meeting) → **context** (2
   lines, numbers) → **options** (2–3, always including "do nothing / status quo" where meaningful) with impact on
   time, cost, scope, risk, customers or teammates → **recommendation** with reason → **consequence of not deciding
   today** → **deadline**.
4. For a **go / no-go**, list the criteria agreed in advance (e.g. test pass rate, training completion, stock
   readiness, support ready), each with status met / not met / at risk and evidence; recommend go, go with conditions
   or no-go.
5. Select **top risks and escalations** (score ≥ 15 or needing committee help) with the specific ask.
6. Draft the **agenda** with timeboxes: decisions get at least 50 % of the time; information is in the pre-read.
7. Draft the **pre-read email** (send 48 h before) and a **minutes template** (decisions, owners, dates).

## Output format
```markdown
# Steering committee — <Project> · <date> · <duration>
**Decisions requested today: <N>** · Overall 🟢/🟠/🔴 <reason>

## Slide 1 — Executive summary
- Status: <RAG + reason> · Since last committee: <3 achievements>
- Decisions needed: D1 <short>, D2 <short>

## Slide 2 — Milestones and budget
| Milestone | Baseline | Forecast | Status |
|-----------|----------|----------|--------|

| Budget (<currency>) | Approved | Committed | Actuals | Forecast at completion | Variance |
|---------------------|----------|-----------|---------|------------------------|----------|

## Slide 3+ — Decision D<n>: <closed question>?
Context: …
| Option | Time | Cost | Scope | Risk | Customer / teammate impact |
|--------|------|------|-------|------|----------------------------|
**Recommendation:** <option> because … · **If no decision today:** … · **Deadline:** …

## Slide — Top risks and escalations
| Risk / issue | Score | Ask to the committee |
|--------------|-------|----------------------|

## Previous actions
| Action | Owner | Due | Status |
|--------|-------|-----|--------|

## Agenda
| Time | Item | Purpose (decide / inform) |
|------|------|---------------------------|

## Pre-read email (draft)
Subject: …

## Minutes template
| Decision | Option chosen | Owner | Date |
|----------|---------------|-------|------|
```

## Quality checks
- Every decision is a closed question with 2–3 options, a recommendation, the cost of not deciding and a deadline.
- Budget rows reconcile: variance = forecast at completion − approved budget, same currency and scope on every line.
- Every number and date has a source or is marked *to confirm*; no budget figure is estimated by the model.
- Previous actions are all listed with a status; reopened decisions are flagged.
- Decision items get at least half of the agenda time.

## Guardrails
- Present options fairly: the recommended option must not be the only one with its downsides hidden.
- Do not invent committee members, approval powers or financial thresholds; take them from the charter or ask.
- Financial and supplier details are confidential: keep the pack's distribution to the committee list.
- Draft only: do not send the pre-read, book the meeting or record decisions before the user confirms.
