---
name: pipeline-review
description: "Reviews B2B pipeline health from Airtable, Databricks (SQL or Polco) or Tableau: coverage versus target, stage conversion and aging against median cycle time, slipped close dates, deals without next step, concentration risk and data hygiene, then gives a ranked next action per deal at risk. Use whenever a seller or sales manager prepares a pipeline review, a weekly sales meeting or a one-to-one on deals, or asks which deals need attention or whether the pipe is enough to hit target, even if they only say 'look at my deals'. Triggers - pipeline review, deal review, pipe health, coverage ratio, stuck deals, which deals are at risk, revue de pipe, revue du pipeline, mes opportunités, affaires en retard, taux de couverture, deals bloqués."
---

# Pipeline review

Turns a list of open B2B deals into a diagnosis and a to-do list: is the pipe big enough, healthy enough and moving,
and what exactly should happen next on each deal at risk.

## When to use
- Weekly pipeline meeting, monthly business review or a manager-seller one-to-one.
- Before the start of a season peak (club kit orders, back to school) to check that enough deals are in motion.
- The user suspects the CRM no longer reflects reality.
- Not for: the narrative of the forecast for leadership (use `sales-forecast-commentary`), analysis of closed deals
  (use `win-loss-analysis`), or deep work on one strategic customer (use `account-plan`).

## Inputs
- Scope: seller, team, region or segment (required).
- Period and target for that period (required for coverage; ask if not found in Drive or Databricks).
- Stage definitions and probabilities (optional, default: read from Confluence or the base; otherwise ask, never assume).
- Snapshot date (optional, default: today).

## Sources
1. **Airtable**: the opportunities table: stage, amount, close date, owner, last activity, next step and its date,
   created date, segment. Read the schema; use real field names.
2. **Databricks (SQL or Polco)**: if pipeline history or B2B sales tables exist: stage-change history for aging and
   conversion, won deals for win rate and cycle time. Show each query or Polco question used.
3. **Tableau**: the existing pipeline or sales dashboard, to align numbers with what managers already see.
4. **Drive or Confluence**: targets, stage exit criteria, previous review notes and the actions promised last time.
5. **Gmail and Calendar**: for deals at risk, the date of the last real customer exchange and any upcoming meeting.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Hygiene check first** and list issues per deal: close date in the past, no amount, no next step or next step date
   passed, no activity for more than 30 days, stage inconsistent with notes. Bad data drives bad decisions, so show the
   count at the top.
2. **Coverage**: remaining target = target − won to date. Coverage = open pipeline closing in the period ÷ remaining
   target. Give both unweighted and weighted (amount × stage probability). Compare the unweighted coverage to the coverage the
   team's own win rate implies: needed coverage ≈ 1 ÷ win rate (weighted coverage should be ≈ 1× or more) (e.g. 25 % win rate → about 4×). If win rate is unknown, say so and
   show the formula.
3. **Velocity**: (number of open deals × win rate × average deal size) ÷ average cycle length in days = expected value
   closed per day. Use only computed inputs; mark estimates.
4. **Aging**: days in current stage vs the median time in that stage for won deals. Flag deals above 1.5× the median.
   Without history, flag deals older than the user's stated norm.
5. **Slippage**: count of close-date changes per deal; 2 or more pushes = high risk. Deals pushed into the next period
   are listed separately.
6. **Concentration**: share of the period's pipeline in the top 3 deals; above 50 % = concentration risk.
7. **Seasonality check**: for club and school segments, check that deals tied to a fixed date (season start, school
   year, a company event, a tender deadline) have a close date that leaves enough time for production and delivery.
   Use only lead times found in sources; otherwise flag "lead time to confirm".
8. **Rank deals at risk** by amount × risk signals, and give each one specific next action with owner and date: get
   access to the economic buyer, confirm the decision date, send the size-collection template, requalify or close-lost.
   Recommend removing dead deals: a smaller, true pipe beats a big, fake one.

## Output format
```markdown
# Pipeline review — <scope> · <period> · snapshot <date>
**Verdict:** <one line: on track / at risk / off track, and why>

| Metric | Value | Benchmark | Status |
|--------|------:|----------:|:------:|
| Remaining target | … | — | |
| Open pipe in period (unweighted / weighted) | … / … | — | |
| Coverage | …× | needed …× (1 ÷ win rate) | 🟢/🟠/🔴 |
| Deals with hygiene issues | n / N | 0 | |
| Top-3 concentration | … % | < 50 % | |

### Deals at risk (ranked)
| # | Deal | Amount | Stage (days / median) | Close date (pushes) | Risk signals | Next action · owner · date |
|---|------|-------:|-----------------------|---------------------|--------------|----------------------------|

### Pushed to next period
- …

### Data hygiene to fix
- <deal> — <issue> → <fix>

### Recommendations
1. <pipe generation, requalification or focus decision>

_Sources: <Airtable view link> · <Databricks query or Polco question> · <Tableau view>_
```

## Quality checks
- Every metric shows its formula inputs or source; estimates are labeled.
- Coverage uses only deals with a close date inside the period.
- Every deal at risk has one action with an owner and a date, starting with a verb.
- Numbers reconcile: sum of listed deals equals the open pipe total, or the difference is explained.
- Stage probabilities and targets are sourced, never assumed.

## Guardrails
- Review deals, not people: no judgement on a seller's performance or personal ranking; the manager draws conclusions.
- Never invent amounts, probabilities, targets or close dates; missing values are hygiene issues.
- Read only: Airtable changes (close-lost, new dates) are drafted as a table and applied only after user confirmation.
- Customer names and amounts stay internal; do not paste the review into external channels.
