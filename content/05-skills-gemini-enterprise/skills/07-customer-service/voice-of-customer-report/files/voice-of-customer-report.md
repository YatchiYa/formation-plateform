---
name: voice-of-customer-report
description: "Produces a Voice of the Customer report from tickets, reviews, survey verbatims and store feedback over a period: contact-reason volumes and trends, themes with representative anonymized verbatims, root-cause coding (product, information, process, delivery, store service, policy), impact sizing and an owner-assigned action list. Use whenever someone needs to know what customers complain about or praise, prepare a monthly customer review, or prioritise service improvements, even if they only ask 'what are customers saying'. Triggers - voice of customer, VOC report, customer feedback analysis, top complaints, contact reasons trend, voix du client, analyse des réclamations, retours clients du mois, motifs de contact, synthèse avis clients, irritants clients."
---

# Voice of the Customer report

Turns scattered customer feedback into a short report that says what hurts customers most, why, and who fixes it,
backed by counts and real (anonymized) verbatims.

## When to use
- Monthly or quarterly customer-service or store review.
- Before a product, service or process improvement workshop.
- After a peak (sales period, season start, new service launch) to see what went wrong or right.
- Not for: sorting today's queue (use `ticket-triage`), deep review mining on one product or range (use
  `product-review-insights`), or designing a new survey (use `user-research-plan`).

## Inputs
- Scope: country, store(s), channel(s), product range or service (required).
- Period and comparison period (optional, default: last full month vs previous month).
- Feedback sources to include (optional, default: all connected sources below).
- Internal contact-reason taxonomy (optional; search Drive/Confluence, else use the one in `ticket-triage`).

## Sources
1. **Databricks (SQL or Polco)**: ticket, review or survey tables if they exist. Ask Polco in plain words, e.g.
   "number of customer contacts by contact reason per week for <scope> over <period>", or write SQL after finding the
   table in the catalog. Always show the query or question used and the table name.
2. **Tableau**: existing customer-service or satisfaction dashboards; reuse their KPI definitions.
3. **Jira** (service desk projects) and **Airtable**: tickets or case logs with categories and text.
4. **Gmail / Slack / Google Chat**: store or agent escalation channels, for qualitative signals.
5. **Drive / Confluence**: survey exports, previous VOC reports (for trend and action follow-up), taxonomy.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Assemble the dataset** with source, date, channel, reason (if coded) and text. State the total N per source and
   any gaps (missing weeks, uncoded items).
2. **Quantify**: volume per contact reason, share of total, change vs comparison period. Flag changes > ±20% with
   N ≥ 30 as significant movers; smaller N is "watch".
3. **Find themes in the text**: read a sample of at least 50 items or all if fewer, cluster by underlying problem
   (not by wording), then count each theme across the dataset. Give each theme a neutral name.
4. **Code the root cause** of each theme: Product (design, quality, sizing) · Information (unclear page, label,
   manual) · Process (returns, refund, repair flow) · Delivery & logistics · Store service · Digital (site, app) ·
   Policy (rule perceived as unfair). One primary code per theme.
5. **Size impact** = volume × severity (safety 5, money/blocked use 3, inconvenience 1) and rank themes.
6. **Pick verbatims**: 1–2 per top theme, anonymized, short, representative (not the most extreme).
7. **Propose actions** for the top 5 themes: one action each, owner team, KPI to watch, quick win vs structural.
   Check the previous VOC report and report status of its actions if found.
8. **Note the positives**: top 3 praise themes, so teams know what to protect.

## Output format
```markdown
# Voice of the Customer — <scope> · <period>
**Bottom line:** <2 sentences: biggest pain, biggest change, top action>
_Data: <N> items · <sources with N each> · comparison: <period> · gaps: <…>_

### Contact reasons
| Reason | Volume | Share | vs prev. | Signal |
|--------|--------|-------|----------|--------|

### Top pain themes
| # | Theme | Root cause | Volume | Severity | Impact score | Verbatim |
|---|-------|-----------|--------|----------|--------------|----------|

### What customers love
- <theme> — <volume> — "<verbatim>"

### Actions
| Theme | Action | Owner | KPI | Type |
|-------|--------|-------|-----|------|

### Follow-up of previous actions
- <action> — <done / ongoing / no data>

_Method: themes coded on <n> read items; counts from <query/source>._
```

## Quality checks
- Every number cites its source (query, table, dashboard or file) and the totals reconcile with N.
- Movers are only called significant when N ≥ 30 and the change is > ±20%.
- Each top theme has a root-cause code, a volume and at least one verbatim.
- Verbatims contain no names, emails, order numbers, phone numbers or locations smaller than a city.
- Every action has an owner team and a KPI.

## Guardrails
- Anonymize all verbatims; never single out an individual teammate or store manager by name for blame.
- Do not invent volumes or satisfaction scores; if a source cannot be queried, mark the figure "not available".
- Themes are hypotheses from the sample; a product defect is "reported", not confirmed, until quality validates it.
- Read only. Sharing the report or creating Jira actions happens after the user confirms.

## Example
Input: « Voix du client du mois pour les magasins d'Île-de-France »
→ Bottom line in French. Data line lists Jira tickets (N), store survey verbatims (N), reviews (N) with the Polco
question used. Top pain: « attente en caisse le samedi » (Store service, high volume, low severity) and « remboursement
lent après retour en ligne » (Process, +35% vs previous month, N=120 → significant mover). Positives: advice from
sport-specialist teammates. Actions with owner teams, plus status of last month's actions.
