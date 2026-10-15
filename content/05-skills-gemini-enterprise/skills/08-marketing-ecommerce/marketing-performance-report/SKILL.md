---
name: marketing-performance-report
description: "Builds a campaign or channel performance report from Tableau and Databricks: KPIs vs target and vs last year, funnel breakdown (reach, clicks, conversion, revenue), cost efficiency (CPM, CPC, CPA, ROAS), attribution caveats, incrementality evidence, three insights and next actions. Use whenever someone asks how a campaign, a channel, a newsletter or a season performed, needs a marketing weekly or a post-campaign review, or must justify a marketing budget, even if they only ask 'did it work?'. Triggers - campaign results, marketing report, channel performance, ROAS, post-campaign review, marketing weekly, bilan de campagne, performance marketing, résultats campagne, reporting marketing, ça a marché, retour sur investissement pub."
---

# Marketing performance report

Tells a marketing team what a campaign or channel really delivered, what can and cannot be attributed to it, and what
to do next. Numbers come from Tableau or Databricks, never from memory.

## When to use
- After a campaign or a season (ski season, back to school, Black Friday) to review results.
- Weekly or monthly channel reporting (paid search, paid social, CRM, affiliation, SEO).
- Before a budget discussion, to show efficiency and incrementality.
- Not for: one A/B test result (use `ab-test-readout`), an unexplained metric drop (use
  `metric-anomaly-investigator`), defining a KPI (use `kpi-definition-card`) or explaining a dashboard (use
  `tableau-dashboard-explainer`).

## Inputs
- Campaign or channel, period, market (required).
- Targets and the comparison period (optional, default: same period N-1, aligned on weekdays and on season
  timing, for example Easter or first snowfall).
- KPI definitions (optional, default: from the dashboard or the data dictionary, cited).
- Spend data (optional; without it, cost KPIs are omitted, never estimated).

## Sources
1. **Tableau**: campaign, CRM, acquisition and e-commerce dashboards. Cite the view and filters used.
2. **Databricks (SQL MCP or Polco)**: sessions, orders, revenue, new customers, store sales of the promoted range,
   spend tables. Show every query or Polco question, its date range and filters.
3. **Drive and Confluence**: campaign brief (objective, primary KPI, target), media plan, previous reports, KPI
   definitions.
4. **Airtable and Jira**: campaign calendar, incidents (site outage, stock-out) that explain anomalies.
5. **Gmail, Slack and Chat**: agency reports, context from the team.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Anchor on the brief**: the objective and primary KPI decide the verdict. An awareness campaign is not judged on
   last-click ROAS.
2. **Pull the data** per funnel stage: delivery (impressions, reach, frequency), engagement (clicks, CTR, video
   completion), conversion (sessions, conversion rate, orders, revenue, new customers), cost (CPM, CPC, CPA, ROAS)
   and guardrails (margin, return rate, unsubscribes).
3. **Validate before interpreting**: data freshness, tracking breaks, missing days, tag changes, currency and
   VAT treatment (revenue incl. or excl. VAT). Flag any doubt next to the number.
4. **Compare** against target and N-1. Decompose revenue as sessions × conversion × average order value to show which
   lever moved.
5. **Attribution caveats**: name the model behind each number (last click, data-driven, platform-reported).
   Platform numbers overlap and over-count; never sum them. Online campaigns also drive store sales (ROPO) that
   last-click misses; say whether store sales of the range were checked.
6. **Incrementality**: prefer evidence from holdouts, geo tests or matched-market comparisons. Without them, say
   "correlation, not proven lift".
7. **Insights**: 3 at most, each = finding + number + so-what. Example: "Paid social drove 40 % of new customers but at
   2× the CPA of search → keep for acquisition, cap frequency".
8. **Next actions** with owner and date, and what to test next.

## Output format
```markdown
# <Campaign/channel> — performance <period> (<market>)
**Verdict:** <on target / below / above> on <primary KPI>: <value> vs target <…> (<±%>) and N-1 <…>

## KPIs
| Stage | KPI | Actual | Target | N-1 | Δ vs N-1 | Source |
|-------|-----|--------|--------|-----|----------|--------|

## What drove it
- Revenue = sessions <Δ> × conversion <Δ> × AOV <Δ> → <main lever>

## Insights
1. <finding + number> → <so-what>
2. …
3. …

## Caveats
- Attribution: <model per number> · Store impact: <checked / not checked>
- Data quality: <freshness, gaps, tracking changes>

## Next actions
| Action | Owner | Date | Expected effect |
|--------|-------|------|-----------------|

_Queries and views used: <list>_
```

## Quality checks
- Every number cites its Tableau view or Databricks query, with period and filters.
- The verdict uses the primary KPI from the brief.
- No sum of platform-reported conversions across channels.
- The attribution model is named for every conversion or ROAS figure.
- At most 3 insights, each with a number and a so-what; every action has an owner.

## Guardrails
- Never fabricate or extrapolate numbers. Missing data stays "not available" with the reason.
- Do not claim causality without an experiment or a holdout; write "associated with".
- Report at aggregate level only; no individual customer data in the report.
- Read only: do not change budgets, bids or campaigns; recommend, and the user decides.
