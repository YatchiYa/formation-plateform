---
name: workshop-service-review
description: "Reviews a store repair workshop and after-sales service: job volume by type, turnaround time vs promise, on-time rate, backlog in days of capacity, comebacks and rework, attach rate of services to product sales, customer satisfaction and complaints, seasonal peaks such as spring bike servicing or autumn ski prep, and a capacity and action plan. Use whenever a store or workshop manager asks how the workshop is doing, faces a growing backlog or complaints about repair delays, or prepares a season, even if they only ask 'why are bikes waiting two weeks'. Triggers - workshop review, repair service, after-sales, turnaround time, backlog, bike workshop, ski workshop, revue atelier, atelier cycle, délai de réparation, file d'attente atelier, SAV magasin, retard atelier, révision vélo, entretien ski, capacité atelier."
---

# Workshop service review

Gives a store and its workshop team a clear view of service level, capacity and quality, and a plan to keep promises
to customers during peaks.

## When to use
- Monthly workshop review with the store manager.
- Backlog or waiting time is growing, or complaints mention repair delays.
- Before a peak: spring cycling (servicing, punctures, e-bike checks), autumn and winter (ski and snowboard prep,
  boot fitting), back to school.
- Deciding whether to add workshop hours, cross-train teammates, or change the booking policy.
- Not for: drafting replies to an unhappy repair customer (use `customer-reply-drafter`), defect patterns of one
  product for product teams (use `product-review-insights`), new circular services ideas (use `circular-offer-ideas`),
  or a generic process redesign (use `process-improvement-kaizen`).

## Inputs
- Store and workshop (required).
- Period (optional, default: last 8 weeks + same weeks N-1).
- Service promise (optional, default: the promise found in Drive/Confluence or shown to customers; otherwise ask, never
  assume).
- Workshop team capacity: technician hours per week and skills (optional, default: derived from data if labor hours
  exist, otherwise asked).

## Sources
1. **Databricks via Polco**: « nombre d'interventions atelier par type, date de dépôt, date promise, date de fin et
   date de retrait pour le magasin X ». Then **Databricks SQL MCP**: discover the service or repair order tables and
   their statuses (`SHOW TABLES`, `DESCRIBE`, distinct values of status columns); never assume column names; show the
   query.
2. **Airtable**: if the workshop tracks jobs, bookings or parts orders there.
3. **Tableau**: service or after-sales dashboards for official definitions.
4. **Drive and Confluence**: the service catalog, standard job times, promise rules, workshop procedures.
5. **Gmail, Chat, Slack**: parts supply delays, customer complaints forwarded to the store, team messages.
6. **Customer feedback**: reviews or survey comments mentioning the workshop (anonymized).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Volume and mix**: jobs per week by type (quick fix, standard service, complex repair, assembly, ski prep), and vs
   N-1. Show the seasonal curve.
2. **Service level**:
   - turnaround time = completion − drop-off, median and 90th percentile (the 90th percentile is what angry customers
     experience);
   - on-time rate = jobs completed by the promised date / jobs completed;
   - collection time = pickup − completion (bikes waiting for collection use space and hide real capacity).
3. **Backlog and capacity**: backlog in jobs and in days of capacity = open jobs × average job time / technician hours
   per day. Check Little's law: average jobs in progress ≈ throughput per day × average turnaround in days; a big gap
   means status data is unreliable. Flag jobs waiting for parts separately: they are a supply problem, not capacity.
4. **Quality**: comeback rate (same customer and item back within 30 days for the same issue, if traceable),
   cancellations, complaints. Few comebacks with slow service is a capacity issue; many comebacks is a skills or
   process issue.
5. **Business link**: attach rate of services to product sales (for example servicing or assembly proposed with each
   bike sold), workshop revenue if available, and second-hand or rental activity linked to the workshop.
6. **Peak readiness**: compare the expected peak (N-1 same weeks × trend) with capacity; compute the gap in technician
   hours.
7. **Actions** by type: capacity (hours, cross-training, triage desk for quick fixes), flow (booking slots, promise rules
   by job type, pre-season campaigns to smooth demand), parts (stock of fast-moving parts), quality (checklists,
   final test), customer communication (status updates, ready-for-pickup reminders).

## Output format
```markdown
# Workshop review — <store> — <period>
**In one line:** <service level, main constraint, first action>
_Promise used: <source>; data: <tables / views>_

## Key figures
| KPI | Period | N-1 | Δ | Promise / target |
|-----|--------|-----|---|------------------|
| Jobs completed | | | % | |
| Turnaround median (days) | | | | |
| Turnaround 90th percentile (days) | | | | |
| On-time rate | % | % | pts | |
| Backlog (jobs / days of capacity) | | | | |
| Waiting for parts (jobs) | | | | |
| Comeback rate | % | % | pts | |
| Service attach rate | % | % | pts | |

## Mix and seasonality
| Job type | Volume | Share | Avg time | Δ N-1 |
|----------|--------|-------|----------|-------|

## Capacity vs demand (next <n> weeks)
| Week | Expected jobs | Capacity (jobs) | Gap | Comment |
|------|---------------|-----------------|-----|---------|

## Customer voice
- <themes, anonymized, with counts>

## Diagnosis
1. <constraint> — evidence — type (capacity / flow / parts / quality / communication)

## Actions
| # | Action | Type | Owner (role) | Due | KPI |
|---|--------|------|--------------|-----|-----|

## Appendix — data used
<queries, data quality notes>
```

## Quality checks
- Turnaround shows median and 90th percentile, not just the average.
- Jobs waiting for parts are separated from capacity backlog.
- The promise used for on-time rate is cited, or marked as not found.
- The capacity forecast shows its method (N-1 × trend, technician hours).
- Each action addresses a diagnosed constraint and has an owner role, date and KPI.

## Guardrails
- No technician-level productivity ranking; analysis stays at workshop and job-type level unless the manager asks for
  coaching support, and even then it is shared privately.
- Customer data stays anonymized: no names, phone numbers or bike serial numbers in the output.
- Never invent standard job times, prices or promises; use documented ones or ask.
- Safety-critical repairs (brakes, e-bike batteries, ski bindings) follow documented procedures; do not suggest
  skipping checks to gain capacity.
- Draft only: no booking-policy change, customer message or ticket is made without the user's confirmation.
