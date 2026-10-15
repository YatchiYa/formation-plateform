---
name: win-loss-analysis
description: "Analyses won and lost B2B deals and tenders over a period, from Airtable, Databricks, tender score sheets and deal emails: win rate by segment, size and source, decision-reason coding with evidence, the share of 'no decision', patterns by stage of loss, lessons and concrete actions, with sample-size caveats. Use whenever a sales team wants to know why it wins or loses, prepares a season or quarterly review, received tender results, or wants to improve its win rate, even if they only ask why we lost this deal. Triggers - win loss analysis, why did we lose, lost deals review, win rate, tender debrief, post-mortem on a deal, analyse des affaires gagnées perdues, pourquoi on a perdu, taux de transformation, retour d'appel d'offres, bilan commercial."
---

# Win-loss analysis

Finds the repeatable reasons behind won and lost B2B deals, separates real causes from excuses, and turns them into
a few actions that change the next season's results.

## When to use
- End of a season, quarter or year for a sales team.
- After a run of losses on a segment (e.g. several club kit deals lost to local shops, or school tenders lost on price).
- After a tender result, with or without the buyer's score sheet.
- Not for: open deals (use `pipeline-review`), a single competitor profile (use `competitive-battlecard`), or the
  forecast narrative (use `sales-forecast-commentary`).

## Inputs
- Scope and period (required).
- Deal list with outcome and close date (optional, default: Airtable closed deals in the period).
- Tender results and score sheets (optional, default: search Gmail and Drive).
- Any buyer interviews or feedback notes (optional).

## Sources
1. **Airtable**: closed won and closed lost opportunities: segment, amount, source, stage reached, loss reason,
   competitor, cycle length, owner.
2. **Databricks (SQL or Polco)**: won deals for amounts and repeat orders; history to compute win rate and cycle time.
3. **Gmail**: the last threads of lost deals (the buyer's own words), and tender award notices and rejection letters.
4. **Drive**: tender score sheets and evaluation reports, call recaps, feedback interview notes, proposals sent.
5. **Slack or Chat**: team discussions about specific losses, if the user points to them.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Build the dataset**: one row per closed deal with outcome, segment, size band, source (inbound, outbound, tender,
   renewal), stage at loss, cycle days, competitor, stated reason, evidence link. Count deals with no reason recorded.
2. **Quantify**: win rate overall and by segment, size band and source, by count and by value. Show n for every cell;
   below 10 deals, write "indicative only" and do not draw conclusions from percentages.
3. **Code the reasons** with a fixed list, using evidence rather than the CRM reason alone: price, product fit,
   customisation, lead time or availability, service or after-sales, relationship or incumbent, process (tender
   criteria, compliance gap, late or incomplete submission), budget lost, **no decision** (the customer did nothing).
   Mark the stated reason vs the evidenced reason when they differ ("price" in the CRM, but the email says the kits
   could not arrive before the first match = lead time).
4. **Tender lens**: for public tenders, compare our score to the winner's by criterion when the score sheet is
   available. Losing on technical value with a good price is a different fix than losing on price.
5. **Find patterns**: where losses cluster (segment, stage, competitor, size), how cycle time differs between wins and
   losses (long cycles often end in no decision), what wins have in common (champion identified, economic buyer met,
   size collection done early, reference visit).
6. **Lessons → actions**: 3–5 actions, each with owner, date and the metric to watch next period. Examples: qualify
   the decision date before quoting; build a standard technical answer for school tenders; offer a size-collection
   session to every club before quoting.
7. Propose a **buyer interview guide** (5 questions) for future losses, to improve evidence quality.

## Output format
```markdown
# Win-loss — <scope> · <period>
**Headline:** <one sentence: main reason we win, main reason we lose, the action that matters most>

| Cut | Deals (n) | Win rate (count) | Win rate (value) | Note |
|-----|---------:|-----------------:|-----------------:|------|
| All | … | … | … | |
| <segment> | … | … | … | indicative if n < 10 |

### Why we lose (evidenced)
| Reason | Deals | Value | Example (link) | Stated vs evidenced |
|--------|------:|------:|----------------|---------------------|

### Why we win
- … ([example](…))

### Tender scores (if available)
| Tender | Criterion | Us | Winner | Gap |
|--------|-----------|---:|-------:|----:|

### Patterns
1. …

### Actions
| Action | Owner | Due | Metric next period |
|--------|-------|-----|--------------------|

### Data quality
- <n> deals without a loss reason · <n> without competitor · recommendation: …

### Buyer interview guide (for next losses)
1. …
```

## Quality checks
- Every percentage shows its n; cuts with n < 10 are marked indicative.
- Each loss reason category has at least one linked example.
- "No decision" is counted separately from losses to a competitor.
- Stated and evidenced reasons are compared, and differences are shown.
- Each action has an owner, a date and a metric.

## Guardrails
- Analyse deals and processes, not individual sellers; no personal performance ranking.
- Never invent competitor prices or scores; use only the score sheet or sourced documents.
- Quote buyers minimally and only from professional exchanges; anonymise them in material shared beyond the team.
- Do not use non-public information obtained about competitors' bids; flag it if found.
- Read only: CRM reason corrections are proposed, not applied, until the user confirms.
