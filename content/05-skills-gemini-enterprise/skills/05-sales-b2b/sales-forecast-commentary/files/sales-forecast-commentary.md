---
name: sales-forecast-commentary
description: "Writes the narrative for a B2B sales forecast: forecast versus target and versus last period, commit, best case and pipeline categories, the drivers behind the gap by segment, the deals that move the number, risks and upside with probabilities, the call and the asks to leadership, built from Airtable, Databricks or Polco and Tableau numbers that are cited, never invented. Use whenever a seller or sales manager must submit or present a forecast, a monthly or quarterly sales update or a commit call, or explain a gap to target, even if they only paste the numbers. Triggers - forecast commentary, sales forecast, commit call, forecast vs target, explain the gap, monthly sales update, commentaire de prévision, prévision des ventes, atterrissage, écart à l'objectif, point mensuel commercial, forecast B2B."
---

# Sales forecast commentary

Turns forecast numbers into a short, honest story leadership can act on: where we will land, why, how confident we
are, and what we need from them.

## When to use
- Weekly or monthly forecast submission, commit call, quarterly business review.
- A gap to target must be explained to management.
- The forecast changed a lot since the last call and the change needs explaining.
- Not for: deal-by-deal hygiene and actions (use `pipeline-review`), analysis of closed deals (use
  `win-loss-analysis`), or a general finance commentary (use `monthly-finance-commentary`).

## Inputs
- Scope and period (required).
- Target, won to date, and the open deals with forecast category (commit, best case, pipeline) (required; search
  Airtable, Databricks and Drive before asking).
- Previous forecast call (optional, default: last forecast doc in Drive) to explain changes.
- Audience (optional, default: sales leadership; 1 page).

## Sources
1. **Airtable**: open deals with amount, close date, stage, forecast category, owner, next step.
2. **Databricks (SQL or Polco)**: won revenue to date, same period last year, run-rate for repeat business (club
   reorders, recurring company programmes). Show the query or Polco question.
3. **Tableau**: the official sales dashboard; the commentary must match its numbers or explain the difference.
4. **Drive**: target sheet, previous forecast commentary, leadership asks from last time.
5. **Gmail and Slack or Chat**: latest signals on the big deals (decision postponed, tender result announced).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Build the landing**: won to date + commit = commit forecast; + best case = upside scenario; pipeline is not in the
   call. Gap to target = target − forecast. Show the three numbers and the gap in value and %.
2. **Bridge from the last call**: start from the previous forecast, then list the movements: deals won, lost, slipped
   out, pulled in, amounts changed, new deals. The bridge must add up exactly.
3. **Drivers by segment** (clubs, schools, companies, public bodies, others): vs target and vs last year, with the
   reason in one line each (e.g. club orders shifted two weeks later because of a later league calendar — only if a
   source says so).
4. **Deals that move the number**: the 3–5 largest open deals in commit and best case, with the evidence for the
   category (economic buyer engaged, purchase order expected on a date, tender result date).
5. **Risks and upside** with probability (High/Med/Low) and value. Classic risks: a public tender result delayed, a
   board or council vote postponed, budget freeze, delivery capacity before an event date. Classic upside: reorders for
   late sign-ups, a framework agreement order.
6. **Forecast discipline**: flag commit deals without a dated next step or with 2+ close-date pushes; they should not
   be in commit. State the forecast accuracy of the last periods if data exists.
7. **The call and the asks**: one number you stand behind and why; asks to leadership that would change it (pricing
   approval on a deal, executive sponsor meeting, stock or capacity priority), each with a deadline.

## Output format
```markdown
# Forecast — <scope> · <period> · as of <date>
**Call:** <amount> (<x> % of target) · **Gap:** <amount> · **Range:** <commit> – <best case> · **Confidence:** <H/M/L>

### Landing
| | Amount | % of target |
|---|------:|-----------:|
| Won to date | … | … |
| + Commit | … | … |
| = Commit forecast | … | … |
| + Best case | … | … |
| Target | … | 100 % |

### Bridge from last call (<date>)
| Movement | Deal(s) | Amount |
|----------|---------|-------:|
| Previous forecast | | … |
| Won / lost / slipped / pulled in / new | … | ± … |
| **Current forecast** | | **…** |

### By segment
| Segment | Forecast | vs target | vs last year | Driver |
|---------|---------:|----------:|-------------:|--------|

### Deals that move the number
| Deal | Amount | Category | Close date | Evidence |
|------|-------:|----------|-----------|----------|

### Risks and upside
| Item | Value | Probability | Mitigation / action |
|------|------:|-------------|---------------------|

### Asks
1. <ask> — needed by <date> — impact <amount>

_Sources: <Airtable view> · <query / Polco question> · <Tableau view> · numbers as of <timestamp>_
```

## Quality checks
- Landing and bridge arithmetic add up exactly; any gap with Tableau is explained.
- Every commit deal has a dated next step and evidence; others are moved to best case in the text.
- Every number has a source and a timestamp; estimates are labeled.
- The call is one number with a confidence level, and the narrative fits on one page.
- Each ask has a deadline and a quantified impact.

## Guardrails
- Never invent targets, amounts, probabilities or last-year figures; missing data is stated, not estimated silently.
- No sandbagging or inflating: the call follows the evidence rules above, and the commentary says when the data is
  incomplete.
- Comment on deals and segments, not on individual sellers' performance.
- Internal financial information: no sharing outside the intended audience; draft only, the user submits.
