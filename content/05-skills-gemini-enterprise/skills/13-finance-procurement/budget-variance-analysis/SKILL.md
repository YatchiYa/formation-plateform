---
name: budget-variance-analysis
description: "Analyzes actuals vs budget, forecast or last year for a P&L, cost center, store, sport or project: variance table with favorable / unfavorable signs, materiality filter, price / volume / mix decomposition for sales and margin, rate vs volume for costs, timing vs permanent split, root-cause explanations and corrective actions with owners. Use whenever someone must explain a gap to budget, prepare a month-end or quarter review, answer 'why are we off', or comment a cost overrun, even if they only paste a table of numbers. Triggers - budget variance, actual vs budget, variance analysis, PVM, price volume mix, cost overrun, explain the gap, analyse des écarts, écart budget, réel vs budget, écart prix volume mix, dépassement budgétaire, expliquer l'écart."
---

# Budget variance analysis

Explains why actuals differ from plan, in numbers that reconcile to the cent, and separates what management can act on
from what is timing, one-off or outside its control.

## When to use
- Month-end, quarter-end or forecast review of a P&L, cost center, store, sport universe or project budget.
- A manager is asked "why are you 8 % below budget?" and needs a defensible answer.
- A cost line overruns and the cause (price or consumption) must be found.
- Not for: writing the monthly management narrative for the whole P&L (use `monthly-finance-commentary`), store
  sales decomposition into traffic × conversion × basket (use `store-performance-analysis`), or investigating a data
  anomaly (use `metric-anomaly-investigator`).

## Inputs
- Actual and comparison figures (budget, latest forecast or N-1) for the same scope and period (required; Databricks,
  Tableau or a Drive sheet, else pasted by the user).
- For PVM: quantities and prices or margins per product, family or channel (optional; without them only total
  variances are computed, and the analysis says so).
- Materiality threshold (optional, default: |variance| ≥ 5 % of the line AND among the lines that explain 80 % of
  the total variance; labeled *default — replace with your finance rule*).
- Currency, units and sign convention (optional, default: as in the source; state it).

## Sources
1. **Databricks (SQL MCP or Polco)**: actuals and budget by account, cost center, store, sport, product family and
   month; quantities and unit prices for PVM. Show every query and the table names used.
2. **Tableau**: the finance or controlling dashboard used by the team, to reconcile totals.
3. **Drive**: budget files, forecast versions, controlling packs, accruals schedules, materiality rules from finance.
4. **Gmail, Chat and Slack**: known explanations (late invoice, one-off, price increase announced by a supplier,
   promotion moved), always cited.
5. **Confluence and Jira**: projects or events that explain cost timing (e.g. a store opening postponed).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Check comparability** before any analysis: same scope (stores, entities), same period and calendar (number of
   trading days, Easter or sales period shifts), same currency and FX rate, same accounting treatment. List any
   difference as a reconciling item.
2. Build the **variance table**: variance = actual − comparison, % = variance / |comparison|. Mark F (favorable) or
   U (unfavorable): for revenue and margin, above plan is F; for costs, above plan is U.
3. Apply **materiality** to select lines to explain; aggregate the rest as "other, not material".
4. **Decompose sales or margin variance (PVM)** per item i, with AQ / BQ = actual / budget quantity, AP / BP =
   actual / budget unit price (or unit margin), AQt / BQt = totals, budget mix bmᵢ = BQᵢ / BQt:
   - **Price** = Σ (APᵢ − BPᵢ) × AQᵢ
   - **Volume** = (AQt − BQt) × (Σ BPᵢ × BQᵢ / BQt)
   - **Mix** = Σ (AQᵢ − AQt × bmᵢ) × BPᵢ
   - Check: price + volume + mix = total variance (to rounding).
5. **Decompose cost variances**: rate (price per unit of resource) vs volume (consumption): rate = (AR − BR) × AV,
   volume = (AV − BV) × BR. Example: freight cost = rate per pallet × number of pallets.
6. Classify each material variance: **timing** (will reverse: late invoice, phasing, accrual), **one-off**
   (non-recurring), **permanent / run-rate**, **scope or FX**. Only permanent variances change the full-year forecast.
7. Explain each material variance with a **sourced cause**; if none is found, write "cause not identified — ask
   <owner>" rather than guessing.
8. Propose **actions** for controllable, permanent, unfavorable variances: owner, date, expected effect (labeled
   *estimate*) and impact on the full-year landing.

## Output format
```markdown
# Variance analysis — <scope> · <period> · vs <budget / forecast / N-1>
_Currency <…> · units <k€> · variance = actual − comparison, F/U column gives the direction · materiality: <rule> · sources: <links / queries>_
**Bottom line:** <total variance, F/U, % — main 2 drivers — timing vs permanent split>

## Variance table
| Line | Actual | Comparison | Variance | % | F/U | Material? |
|------|--------|-----------|----------|---|-----|-----------|
| **Total** | | | | | | |

## Sales / margin bridge (PVM)
| Effect | Amount | Formula | Main contributors |
|--------|--------|---------|-------------------|
| Price | | Σ (AP − BP) × AQ | |
| Volume | | (AQt − BQt) × budget avg | |
| Mix | | Σ (AQ − AQt × bm) × BP | |
| **Total** | = variance | | |

## Material variances explained
| Line | Variance | Type (timing / one-off / permanent / scope-FX) | Cause (source) | Controllable? |
|------|----------|------------------------------------------------|----------------|---------------|

## Actions and full-year impact
| Action | Owner | Due | Expected effect (*estimate*) |
|--------|-------|-----|------------------------------|
Full-year landing impact of permanent variances: …

## Comparability notes and open questions
- …
```

## Quality checks
- Totals reconcile: Σ line variances = total variance, and price + volume + mix = total PVM variance.
- Every figure comes from a cited query, dashboard or file, or from the user; no number is estimated silently.
- F/U signs follow the stated convention for both revenue and cost lines.
- Every material variance has a type and a sourced cause, or "cause not identified" with an owner to ask.
- Timing variances are not used to change the full-year forecast.
- Formulas are shown for every decomposition.

## Guardrails
- Financial data is confidential: keep the analysis to the scope the user is entitled to see; do not paste store or
  entity results into wide channels.
- Never invent budget figures, thresholds or explanations; label assumptions and estimates.
- Explain variances by drivers and decisions, not by blaming named teammates.
- Draft only: no posting, emailing or forecast update in any system without explicit confirmation.

## Example (illustrative numbers)
Running shoes, budget: A 1,000 × 50 € + B 500 × 100 € = 100,000 €. Actual: A 1,300 × 48 € + B 400 × 105 € = 104,400 €.
Variance +4,400 € F = price −600 € (A −2,600, B +2,000) + volume +13,333 € (200 × 66.67 €) + mix −8,333 € (shift to the
cheaper model A). Reading: volume is strong, but customers traded down; the price cut on A did not pay for itself.
