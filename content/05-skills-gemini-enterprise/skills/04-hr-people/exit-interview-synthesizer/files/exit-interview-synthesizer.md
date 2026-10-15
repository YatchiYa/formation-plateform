---
name: exit-interview-synthesizer
description: "Synthesizes exit interviews and leaver feedback across a team, store, warehouse or job family into anonymized themes: primary and contributing reasons for leaving, controllable vs uncontrollable, regretted vs non-regretted patterns at aggregate level, early-tenure signals, retention risks for current teams and 3-5 targeted actions. Also proposes an exit interview guide if none exists. Use whenever HR or a manager wants to understand why people leave, prepares a turnover review, or sees departures rise in a store or team, even if they only paste a few exit notes. Triggers - exit interviews, why people leave, attrition themes, turnover analysis, retention actions, leaver feedback, entretiens de sortie, entretiens de départ, pourquoi ils partent, turnover, analyse des départs, fidélisation."
---

# Exit interview synthesizer

Turns scattered exit feedback into anonymized patterns and a few retention actions that address the controllable
reasons people leave.

## When to use
- A periodic turnover review for a site, store network, warehouse or job family.
- Departures increased in a team and the manager or HRBP wants to know why.
- Exit interviews exist but nobody has read them together.
- No exit interview guide exists yet and one is needed.
- Not for: current-employee survey results (use `engagement-survey-analyzer`), a single difficult conversation
  with someone resigning (use `difficult-conversation-prep`), or the handover of the leaver's work (use
  `handover-before-leave`).

## Inputs
- Exit interview notes or form answers for the period (required).
- Scope and period, number of leavers and headcount (required for rates; otherwise only themes).
- Turnover data: leaver counts by month, tenure band, contract type, voluntary vs not (optional; aggregated).
- Previous period synthesis (optional, for trends).

## Sources
1. **Drive**: exit interview notes or Forms results, previous syntheses, the exit interview guide.
2. **Databricks / Tableau**: aggregated headcount and turnover by site, tenure band and month, at group sizes ≥ 5.
3. **Confluence**: retention or HR analytics pages, definitions of turnover used internally.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Anonymize first**: strip names, dates, unique roles, managers' names and specific events. If the scope has
   **< 5 leavers**, give only themes without counts and warn that patterns are not reliable; never present a
   single person's story.
2. **Code each interview** with one *primary* reason and up to two *contributing* ones, using this codebook:
   career growth, manager relationship, workload and staffing, schedules and work-life balance, pay and benefits,
   recognition, team climate, job content, tools and processes, commute or relocation, studies/end of contract,
   personal (no detail recorded), safety or physical strain. Add a *controllable* tag (could the organization
   have acted?).
3. **Count and weigh**: frequency of primary reasons, and reasons × tenure band (< 3 months, 3–12 months,
   1–3 years, > 3 years) only when each cell has ≥ 5 leavers. Early leavers (< 3 months) often signal recruiting
   promise or onboarding gaps; call it out if the data shows it.
4. **Rates** (if data exists): voluntary turnover = voluntary leavers ÷ average headcount over the period. Use the
   internal definition if found and cite it. Seasonal or fixed-term contract ends are separated, not mixed.
5. **Signals for current teams**: which controllable themes are likely present today (cross-check with the latest
   engagement survey themes if the user provides them). Speak about teams or job families, never individuals.
6. **Actions (3–5)**: each targets one controllable theme, with owner, date and a measure (e.g. 90-day retention
   of new hires; schedule published earlier). Example: if early warehouse leavers cite physical strain and lack
   of preparation, act on the safety induction and the first-week ramp, not on pay.
7. If no guide exists, propose an exit interview guide: 8–10 open questions, conducted by someone other than the
   direct manager, voluntary, with a statement on how answers are used.

## Output format
```markdown
# Exit interview synthesis — <scope>, <period>
_Leavers: <n> (voluntary <n>) · interviews analyzed: <n> · turnover rate: <x% (definition, source)> or n/a_
_All content anonymized. Groups < 5 not broken down._

## Headline (≤ 60 words)
…

## Primary reasons
| Reason | Share of interviews | Controllable? | Trend vs last period |
|--------|---------------------|---------------|----------------------|

## Patterns
- <tenure / job family / contract pattern, only for groups ≥ 5>

## What leavers say (anonymized)
- <theme> — "<paraphrased verbatim>"

## Retention risks for current teams
- <theme> — where it likely applies (team/job family level) — evidence

## Actions
| Theme | Action | Owner | Date | Measure |
|-------|--------|-------|------|---------|
```

## Quality checks
- No output element identifies, or allows inferring, a specific leaver.
- No breakdown shows a cell with fewer than 5 people.
- Every reason share is computed from the coded interviews and the count is stated.
- Actions only target controllable themes and each has an owner and a measure.
- The turnover rate states its definition and source, or is marked n/a.

## Guardrails
- Do not record or report personal reasons (health, family, pregnancy, relocation for a partner) beyond the
  category "personal".
- Never attribute departures to a named manager in the output. If leavers repeatedly describe serious conduct
  issues (harassment, discrimination, safety), state that serious signals were found and route to HR through the
  proper channel, without details.
- Do not predict which current teammates will leave or score individual flight risk; that is profiling.
- Never invent rates or benchmarks.
