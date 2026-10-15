---
name: business-case-builder
description: "Builds an investment or project business case from the user's own figures: problem and strategic fit, options including do-nothing, cost (CAPEX, OPEX, one-off, run) and benefit model per year, NPV, IRR, payback and discounted payback with formulas shown, sensitivity and break-even on the key drivers, scenarios, non-financial benefits, risks and a recommendation. Use whenever someone needs to justify an investment, compare options financially, get budget approval for a project, tool, store equipment or new service, even if they only ask 'is it worth it'. Triggers - business case, ROI, NPV, IRR, payback, investment case, cost benefit analysis, is it worth it, dossier d'investissement, cas d'affaires, retour sur investissement, VAN, TRI, délai de récupération, rentabilité du projet."
---

# Business case builder

Gives a sponsor an honest, reproducible investment case: every number traceable to an input, every formula visible,
and a clear view of what would have to be true for the investment to pay back.

## When to use
- Requesting funding for a project, tool, equipment or new service (e.g. rental offer, repair workshop, store
  refit, warehouse automation, software licence).
- Comparing two or more options (build vs buy, lease vs buy, in-house vs outsourced).
- A steering committee or finance asks for NPV, payback or a sensitivity analysis.
- Not for: a single purchase request with an approval path (use `purchase-request-justification`), the project's
  mandate and governance (use `project-charter`), a qualitative decision without financials (use `decision-memo`).

## Inputs
- Problem or opportunity and the options considered (required).
- Costs per option: one-off (CAPEX, implementation), recurring (OPEX, licences, staff time), with timing (required;
  from quotes, files or the user — never estimated by the model).
- Benefits per year with their driver logic (e.g. extra rentals × price × margin rate; hours saved × loaded hourly
  cost) (required, same rule).
- Discount rate, analysis horizon, tax and depreciation treatment (optional; look for the finance rule in Drive or
  Confluence; if absent ask; if the user says to proceed, compute at a user-chosen rate and label it).
- Currency, inflation assumption (optional, default: constant prices, stated).

## Sources
1. **Drive and Confluence**: business case template and finance guidelines (discount rate, horizon, hurdle rates),
   supplier quotes, previous comparable cases and their actual results.
2. **Databricks (SQL or Polco) and Tableau**: baseline volumes and rates the benefits depend on (e.g. current
   footfall, workshop jobs per week, return rates), with queries shown.
3. **Gmail, Chat and Slack**: supplier offers, sponsor expectations, constraints.
4. **Jira and Confluence**: effort estimates from the delivery team.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Write the **problem** and **strategic fit** (3 lines) and list **options**, always including **do nothing /
   minimum** as the base for incremental cash flows.
2. Build the **driver-based model**: each cost and benefit line = driver × rate, with source per input. Use
   **incremental cash flows** vs do-nothing only; exclude sunk costs; include run costs, maintenance, training,
   decommissioning and teammate time.
3. Lay out yearly cash flows CF₀…CFₙ (year 0 = investment) per option.
4. Compute and show formulas:
   - **NPV** = Σₜ₌₀ⁿ CFₜ / (1 + r)ᵗ
   - **IRR** = the rate where NPV = 0 (state it is found by iteration)
   - **Payback** = years until cumulative undiscounted CF ≥ 0 (interpolate within the year)
   - **Discounted payback** = same on discounted CF
   - Optional: **ROI** = (Σ benefits − Σ costs) / Σ costs over the horizon, flagged as ignoring time value.
5. **Sensitivity**: vary each key driver ±10 % and ±20 % one at a time and show the NPV change (tornado table,
   biggest swing first). Compute **break-even** values (the driver value at which NPV = 0).
6. **Scenarios**: pessimistic / base / optimistic with explicit driver sets; never assign probabilities unless the
   user provides them.
7. Add **non-financial benefits** (customer experience, teammate safety, sustainability, e.g. product lifetime
   extension) with a measurable indicator, and **risks** with mitigations.
8. **Recommend** an option with the 2–3 conditions that must hold (from the break-even analysis) and the KPIs to track
   after approval.

## Output format
```markdown
# Business case — <Project> · <date> · v<0.x>
_Horizon <n> years · discount rate <r> (source: …) · currency <…> · constant prices · sources: <links>_
**Recommendation:** <option> — NPV <…>, IRR <…>, payback <…> · holds if <break-even conditions>

## 1. Problem and strategic fit
## 2. Options
| Option | Description | Main pros | Main cons |
|--------|-------------|-----------|-----------|

## 3. Assumptions
| Driver | Value | Unit | Source / *estimate by user* |
|--------|-------|------|-----------------------------|

## 4. Cash flows — <option> (incremental vs do nothing)
| Year | 0 | 1 | 2 | … | n |
|------|---|---|---|---|---|
| Costs | | | | | |
| Benefits | | | | | |
| Net CF | | | | | |
| Discount factor 1/(1+r)ᵗ | | | | | |
| Discounted CF | | | | | |
| Cumulative CF | | | | | |

## 5. Financial summary
| Option | NPV | IRR | Payback | Discounted payback |
|--------|-----|-----|---------|--------------------|

## 6. Sensitivity and break-even
| Driver | −20 % | −10 % | +10 % | +20 % | Break-even value |
|--------|-------|-------|-------|-------|------------------|
Scenarios: pessimistic … / base … / optimistic …

## 7. Non-financial benefits and risks
## 8. KPIs to track after approval
```

## Quality checks
- Every input in the assumptions table has a source or is labeled as provided by the user; none is created by the model.
- Discounted CF rows multiply correctly, NPV equals their sum, and cumulative CF matches the payback stated.
- IRR is consistent with NPV: NPV > 0 at r implies IRR > r.
- Cash flows are incremental vs do-nothing and exclude sunk costs.
- Sensitivity ranks drivers by NPV swing; break-even values are shown for the top 3.

## Guardrails
- Never invent costs, benefits, discount rates, hurdle rates or approval thresholds; ask, or compute only with values
  the user explicitly chose, labeled as such.
- No optimism bias: show the pessimistic scenario as prominently as the base case.
- Supplier quotes and internal financials are confidential; keep them out of widely shared versions.
- This is decision support, not an accounting or tax opinion; depreciation and tax treatment follow finance.

## Example (illustrative numbers)
Investment 100,000 € at year 0, net benefit 40,000 €/year for 3 years, r = 8 % (user-chosen): discount factors
0.926 / 0.857 / 0.794 → PV benefits 103,084 € → NPV +3,084 €; IRR ≈ 9.7 %; payback 2.5 years. Break-even: benefits
must stay ≥ 38,803 €/year (−3 %), so the case is fragile and depends on hitting the volume assumption.
