---
name: experiment-design
description: "Designs an A/B test or controlled experiment before launch: hypothesis, primary metric and guardrail metrics, unit of randomization, minimum detectable effect, sample size per arm (two-proportion formula, alpha 0.05, power 0.8, with the 16·p(1−p)/δ² rule of thumb) and duration from real baseline traffic, assignment and exposure rules, pre-registered decision rule and pitfalls (peeking, novelty, sample ratio mismatch). Covers website, app, CRM and in-store tests (store pairs, difference-in-differences). Use whenever someone wants to test a change, run an A/B test, pilot something in a few stores or asks how long a test must run, even if they say 'let's just try it'. Triggers - design an A/B test, sample size, how long should the test run, MDE, pilot in stores, concevoir un test A/B, taille d'échantillon, durée du test, tester en magasin, expérimentation, magasins pilotes."
---

# Experiment design

Gives a team a test plan that can actually answer its question: enough sample, the right metric, and a decision rule
written down before the data comes in.

## When to use
- Before launching a website, app, email or pricing test.
- When a team wants to pilot a new service or layout in a few stores and "see if it works".
- When someone asks how long a test must run or how many users or stores it needs.
- When a past test was inconclusive and needs a better design.
- Not for: reading results of a finished test (use `ab-test-readout`), qualitative research (use
  `user-research-plan`), or field-testing a physical product with testers (use `field-test-protocol`).

## Inputs
- The change to test and the business question (required).
- Primary metric and its current baseline (required; default: pulled from Databricks for the last 4–8 aligned
  weeks if the user does not give it).
- Minimum detectable effect that would matter for the business (optional, default: propose 2–3 options with the
  resulting duration).
- Channel and unit: user, session, customer, email recipient, store (optional, default: inferred and stated).
- Eligible traffic per week (optional, default: queried).

## Sources
1. **Databricks SQL MCP and Polco**: baseline rate or mean, its variance, weekly eligible volume, weekday and
   seasonal pattern, for the target population (read-only, aggregated, last full aligned weeks).
2. **Confluence and Drive**: the experimentation guidelines or platform docs if they exist, past test readouts on
   similar changes (realistic effect sizes), metric definitions.
3. **Jira and GitHub**: the feature ticket, feature-flag or experimentation configuration.
4. **Tableau**: dashboards for the metric's history, to sanity-check baselines.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Hypothesis**: "Because <insight>, changing <X> for <population> will increase <metric> by ≥ <MDE>." One
   primary metric only; 2–4 guardrail metrics (e.g. returns rate, margin, page load, unsubscribe rate).
2. **Unit and assignment**: randomize at the level where the change acts and interference is limited (user rather
   than session for logged-in flows; store or region for in-store changes). Analysis unit = randomization unit.
   The primary metric's denominator is that unit: user randomization → « share of exposed users who purchase »
   (users who converted / exposed users), not purchases / page views; baseline, n and eligible volume are counted
   in the same unit (users per week, not page views).
3. **Baseline**: pull p (proportion) or mean and standard deviation from aligned recent weeks; show the query.
4. **Sample size per arm**, two-sided alpha 0.05, power 0.8 (z = 1.96 and 0.84):
   - proportions: n = (1.96 + 0.84)² · [p1(1−p1) + p2(1−p2)] / δ², where δ = p2 − p1 (absolute);
     rule of thumb n ≈ 16 · p(1−p) / δ².
   - means: n ≈ 16 · σ² / δ².
   - Example: p = 3 %, relative MDE 10 % → δ = 0.3 pt → n ≈ 16 × 0.03 × 0.97 / 0.003² ≈ 51,700 per arm.
   - More than 2 arms: apply a Bonferroni correction (alpha / number of comparisons) and recompute.
5. **Duration** = n per arm × arms / eligible weekly units, rounded **up to whole weeks**, minimum 2 full weeks to
   cover weekday cycles; avoid windows with sales periods or holidays unless that is the target context.
6. **Store experiments** (few units, high variance): matched pairs or stratified randomization on size, region
   and N-1 trend; analysis by difference-in-differences vs control stores on pre-period trend; state that with
   < 20 stores per arm only large effects are detectable; compute with store-week variance if possible.
7. **Validity checks**: sample ratio mismatch test (chi-square on assignment counts), exposure logging, A/A test
   if the setup is new, no overlap with conflicting tests.
8. **Decision rule, pre-registered**: ship if primary metric CI excludes 0 in the expected direction and no
   guardrail degrades beyond its threshold; otherwise iterate or stop. No peeking: fixed horizon, or a sequential
   method declared in advance.
9. **Risks**: novelty effect, seasonality, carry-over, contamination between arms, Simpson's paradox when traffic
   mix shifts between arms.

## Output format
```markdown
# Experiment plan — <name>
_Owner: <name> · Status: draft · Baseline pulled: <YYYY-MM-DD> from <source>_

**Hypothesis:** Because <…>, <change> for <population> will <increase/decrease> <metric> by ≥ <MDE>.

| Item | Value |
|------|-------|
| Primary metric | <definition, unit> |
| Guardrails | <metric — max acceptable degradation> |
| Randomization unit | <…> · split <50/50> |
| Baseline | p = <…> (or mean <…>, σ <…>) |
| MDE | <absolute> (<relative>) |
| Alpha / power | 0.05 two-sided / 0.8 |
| Sample size per arm | <n> |
| Eligible volume per week | <…> |
| Duration | <N weeks>, <start> → <end> |

### MDE options
| Relative MDE | δ | n per arm | Duration |
|--------------|---|-----------|----------|

### Assignment and exposure
- <how users/stores are assigned, logged, excluded>

### Decision rule (pre-registered)
- Ship if …, iterate if …, stop if …

### Validity checks
- [ ] SRM test · [ ] exposure logging · [ ] no conflicting test · [ ] A/A if new setup

### Risks and mitigations
- <risk> → <mitigation>

<details><summary>Baseline query and calculation</summary>
<SQL + arithmetic>
</details>
```

## Quality checks
- Exactly one primary metric; guardrails each have a threshold.
- The sample size arithmetic is shown and reproducible from p, δ, alpha and power.
- Duration is whole weeks, at least 2, and avoids or names atypical periods.
- The randomization unit equals the analysis unit, and the primary metric's denominator, baseline, n and weekly
  volume are all counted in that unit (same definition in the table and in the SQL).
- Baselines come from a cited query or source, or are labeled *assumption*.

## Guardrails
- Do not launch, configure flags or change prices; the plan is a draft for the owner.
- Price tests and personalized offers can raise consumer-law and fairness issues; flag them for legal review.
- Tests on teammates (scheduling, incentives) need HR involvement and are out of scope here.
- Use aggregated data only for baselines; no customer-level extracts.
- Never present the rule of thumb as exact when the precise formula gives a different n; show both.
