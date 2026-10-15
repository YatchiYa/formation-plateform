---
name: project-charter
description: "Drafts a one-page-to-three-page project charter in a PMI / PRINCE2-lite structure: business justification, SMART objectives, scope in and out, deliverables, stakeholders and roles, milestones, budget envelope, top risks, tolerances and governance, with every gap flagged instead of invented. Use whenever someone launches, frames or re-baselines a project, needs a sponsor sign-off, or says a project has no clear scope, even if they only ask to 'put the idea on paper'. Triggers - project charter, project brief, project initiation document, PID, kick off a project, define scope, charte projet, note de cadrage, cadrage projet, fiche projet, lancer un projet, définir le périmètre."
---

# Project charter

Turns a project idea into a charter a sponsor can sign: why it exists, what it will and will not deliver, who decides,
and the limits (tolerances) within which the project manager can act without escalating.

## When to use
- A new project or initiative needs a mandate before work starts (store roll-out, new tool, product range launch,
  warehouse process change).
- A running project drifts and needs its scope and governance written down (re-baseline).
- A sponsor asks "what exactly are we signing up for?".
- Not for: the detailed WBS and timeline (use `project-plan-builder`), the full risk register (use `raid-log-builder`),
  the investment justification with NPV (use `business-case-builder`), or the stakeholder engagement plan
  (use `stakeholder-map`).

## Inputs
- Project name and the problem or opportunity it addresses (required).
- Sponsor and project manager (required; search Drive, Confluence and the email thread before asking).
- Target dates, budget envelope, known constraints (optional, default: left as `[to confirm]`, never estimated).
- Existing material: idea note, email thread, workshop notes, business case (optional).
- Ask ONE grouped question if the problem or the sponsor is missing; otherwise proceed and state assumptions in one line.

## Sources
1. **Drive and Confluence**: idea notes, business case, previous charters (reuse the internal template and its
   section names if one exists, and cite it), the strategy or OKR document the project links to.
2. **Gmail and Chat / Slack**: the thread where the project was requested; sponsor statements on goals and limits.
3. **Calendar and Meet transcripts in Drive**: kick-off or framing meetings and their decisions.
4. **Jira / Confluence**: an existing epic or project space, to align names, keys and dates.
5. **Databricks / Tableau**: baseline values for the success metrics (e.g. current stock accuracy, current lead time).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Collect what is known and tag each statement with its source. Separate facts from wishes.
2. Write the **business justification** in 3 lines: problem today (with a baseline number if sourced), consequence of
   doing nothing, link to a strategic objective.
3. Turn goals into 2–4 **SMART objectives** (specific, measurable with baseline → target, achievable, relevant,
   time-bound). Reject vague ones ("improve customer experience") and propose a measurable rewrite.
4. Define **scope**: in scope, explicitly out of scope (at least 3 items, the main source of later conflict),
   deliverables with an acceptance criterion each, and assumptions and constraints.
5. Map **roles** (PRINCE2-lite): sponsor (owns the business case, final decision), senior user (represents those who
   use the result, e.g. store managers), senior supplier (who builds: IT, supplier, logistics), project manager,
   project assurance if any. Add a RACI line for the 4–6 key decisions.
6. List 4–7 **milestones** with dates or `[to confirm]`, each one a verifiable event ("pilot live in 3 stores"),
   not an activity.
7. State the **budget envelope** exactly as given, split CAPEX/OPEX if known. Never compute or guess an amount.
8. List the **top 5 risks** with probability × impact (1–5 each) and one response each; point to `raid-log-builder`
   for the full log.
9. Set **tolerances** (management by exception): time (e.g. ±2 weeks), cost (e.g. ±5 %), scope (must-haves fixed).
   If the user gave none, propose values and mark them *proposal, sponsor to set*. Any forecast beyond tolerance is
   escalated to the sponsor or steering committee.
10. Define **governance**: steering cadence, status report cadence, decision forum, change control rule
    (who approves a change to scope, date or cost).
11. Close with an **open points** list: every `[to confirm]` with the person who can answer.

## Output format
```markdown
# Project charter — <Project name>
_Version <0.x draft> · <date> · Sponsor: <name> · PM: <name> · Sources: <links>_

## 1. Why this project
<Problem + baseline> · <Cost of doing nothing> · <Strategic link>

## 2. Objectives (SMART)
| # | Objective | Baseline | Target | By | Measured in |
|---|-----------|----------|--------|----|-------------|

## 3. Scope
**In scope:** …
**Out of scope:** …
**Deliverables:**
| Deliverable | Acceptance criterion | Owner |
|-------------|----------------------|-------|
**Assumptions / constraints:** …

## 4. Organization and roles
| Role | Name | Accountable for |
|------|------|-----------------|
**Key decisions (RACI):** <decision — R / A / C / I>

## 5. Milestones
| Milestone (verifiable event) | Target date | Status |
|------------------------------|-------------|--------|

## 6. Budget envelope
<as provided, CAPEX / OPEX, source> or `[to confirm with <person>]`

## 7. Top risks
| Risk (cause → event → effect) | P (1–5) | I (1–5) | Score | Response | Owner |
|-------------------------------|---------|---------|-------|----------|-------|

## 8. Tolerances and governance
- Tolerances: time ±…, cost ±…, scope … → beyond: escalate to <forum>.
- Cadence: steering <…>, status report <…>. Change control: <who approves what>.

## 9. Open points before sign-off
- [ ] <question> — <who can answer>

**Sign-off:** Sponsor ______ Date ______
```

## Quality checks
- Every objective has a baseline (or `[baseline to measure]`), a target and a date.
- Out of scope has at least 3 explicit items.
- Each milestone is an event that can be checked as done or not done, not an activity.
- Every risk score equals P × I, and the list is sorted by score.
- No amount, date or name appears that is not in the inputs or a cited source; the rest is `[to confirm]`.
- Tolerances and the change-control rule are present (proposed values are labeled as proposals).

## Guardrails
- Never invent budgets, headcount, approval thresholds or internal governance bodies; look for them in Drive or
  Confluence or leave a placeholder.
- The charter is a draft until the sponsor signs. Do not share it, post it or create Jira epics without the
  user's explicit confirmation of the final version.
- Keep confidential financials and HR impacts (e.g. job changes) at the level of detail the user provided; flag
  "confidential — limited distribution" when the project touches headcount or supplier contracts.

## Example
Input: « Cadrage du projet de déploiement des caisses libre-service dans 12 magasins Île-de-France »
→ Output in French. Objective example: « Réduire le temps d'attente moyen en caisse le samedi de [baseline à mesurer]
à [cible à confirmer] d'ici fin juin dans les 12 magasins ». Out of scope: refonte du parcours retour, magasins hors IDF,
changement de prestataire TPE. Tolerances proposed: délai ±2 semaines, coût ±5 % — *à valider par le sponsor*.
