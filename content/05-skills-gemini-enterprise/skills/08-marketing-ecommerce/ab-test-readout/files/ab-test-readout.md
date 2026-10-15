---
name: ab-test-readout
description: "Reads out a completed A/B test on a site, app, email or campaign: validity checks first (sample ratio mismatch, test duration and full weeks, pre-registered metric, peeking, novelty), then effect size with confidence interval and p-value on the primary metric, guardrail metrics, segment results flagged as exploratory, and a ship, iterate or stop decision with its risk. Use whenever someone shares A/B or split test results, asks if a variant won, whether a result is significant, or wants to roll out a winner, even if they just paste two conversion rates. Triggers - A/B test results, test readout, is it significant, did variant B win, split test, experiment results, résultats test A/B, test AB significatif, analyse de test, la variante a gagné, lecture de test, résultat d'expérimentation."
---

# A/B test readout

Turns raw test results into a trustworthy decision. Validity first, then the size of the effect and its uncertainty,
then the decision. A significant result on a broken test is still a broken test.

## When to use
- A test on the website or app (checkout, product page, search), an email or an ad has ended.
- Someone asks whether variant B "won" or if a difference is significant.
- Before rolling out a winner or writing a test result into a report.
- Not for: designing a new test or computing sample size (use `experiment-design`), campaign performance without a
  control group (use `marketing-performance-report`) or an unexplained KPI change (use
  `metric-anomaly-investigator`).

## Inputs
- Test plan: hypothesis, primary metric, guardrails, planned sample size or duration, MDE (required; search Jira,
  Confluence and Drive first; if absent, say the readout is post-hoc and weaker).
- Results per variant: units assigned (users or sessions), conversions or metric sums, and variance for continuous
  metrics such as revenue per visitor (required, or a Databricks table to query).
- Dates, traffic split and the randomization unit (required).
- Segments of interest (optional; exploratory only).

## Sources
1. **Jira and Confluence**: the test ticket or experiment page with hypothesis, pre-registered metric, MDE,
   duration and launch notes.
2. **Databricks (SQL MCP or Polco)**: assignment and outcome tables per variant per day. Show every query.
3. **Tableau**: the experiment or funnel dashboard used by the team.
4. **Slack, Chat and GitHub**: incidents during the test (bugs, releases, tracking changes, campaigns that hit one
   variant).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Validity checks** (any fail → result is *not trustworthy* until explained):
   - **SRM**: chi-square test of observed vs planned split; p < 0.001 = sample ratio mismatch (assignment, redirect
     or tracking bug).
   - **Duration**: at least one full week (better two) to cover weekday and weekend behavior; not ended on a
     sport-specific spike (first snow, sales launch) unless both arms saw it equally.
   - **Peeking**: was the test stopped when it first looked significant? If yes and no sequential method was used,
     the p-value is overstated.
   - **Sample**: reached the planned size? If not, report as underpowered.
   - **Metric**: primary metric equals the pre-registered one; otherwise label as post-hoc.
   - **Incidents and novelty**: bugs, releases, tracking changes; compare first-week vs later effect for novelty.
2. **Primary metric**: rate per arm, absolute and relative difference, 95 % confidence interval and p-value.
   Proportions: two-proportion z-test. Continuous, skewed metrics (revenue per visitor, AOV): Welch's t-test or
   bootstrap, with outlier rules stated. Show the computation; if variance data is missing, say which number cannot
   be computed.
3. **Practical significance**: compare the CI with the MDE and with the business threshold. "Significant but smaller
   than the MDE" and "not significant but CI includes a meaningful gain" are different findings.
4. **Guardrails**: margin, return rate, page speed, unsubscribe, error rates. A guardrail degradation can block a
   win.
5. **Multiple comparisons**: with several variants or metrics, apply Bonferroni or Holm, or mark secondary results
   exploratory.
6. **Segments** (device, new vs returning, country): exploratory only; a segment win needs its own confirmation
   test.
7. **Decision**: *ship* (valid, primary CI above zero, guardrails safe), *iterate* (promising, inconclusive),
   *stop* (no effect or harm). Give the expected impact as a range from the CI, not a single number, and note that
   winners tend to shrink after rollout.

## Output format
```markdown
# Test readout — <test name> (<dates>)
**Decision:** <ship / iterate / stop> — <one-line reason>
_Hypothesis: <…> · Primary metric: <…> (pre-registered: yes/no) · Unit: <users/sessions>_

## Validity
| Check | Result | Status |
|-------|--------|--------|
| SRM (planned <x/y>) | observed <…>, χ² p = <…> | ✅/⚠️ |
| Duration / full weeks | <…> | |
| Planned sample reached | <…> | |
| Peeking / stopping rule | <…> | |
| Incidents / novelty | <…> | |

## Primary metric
| Arm | Units | Conversions / mean | Rate |
|-----|-------|--------------------|------|
Difference: <abs> (<rel %>) · 95 % CI [<low>, <high>] · p = <…> · MDE: <…>

## Guardrail metrics
| Metric | Control | Variant | Δ (CI) | Status |
|--------|---------|---------|--------|--------|

## Exploratory segments (not for decision)
- …

## Expected impact if shipped
<range from CI × traffic, labeled estimate>

## Next step
- …
_Queries / sources: <list>_
```

## Quality checks
- The SRM check is computed and shown before any effect is reported.
- The primary metric has a confidence interval, not only a p-value.
- Statistical and practical significance are both stated, with the MDE.
- Segment results are labeled exploratory and never drive the decision alone.
- Every number cites a query or a user-provided source; the computation method is named.

## Guardrails
- Never invent data, variances or sample sizes to "complete" a test. Missing inputs are listed.
- Do not declare a winner on an invalid or underpowered test; say "inconclusive".
- Do not equate p < 0.05 with "95 % chance B is better"; explain the CI in plain words.
- Draft only: do not change feature flags, campaigns or Jira status; the team decides and acts.
