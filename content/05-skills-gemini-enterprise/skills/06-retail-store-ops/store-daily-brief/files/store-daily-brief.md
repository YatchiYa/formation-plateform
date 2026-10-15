---
name: store-daily-brief
description: "Builds a store manager's one-screen morning brief: yesterday's sales, traffic, conversion rate and average basket versus N-1 and target, the main driver of the gap, today's agenda, deliveries and the three priorities for the day, from Databricks, Tableau, Calendar and mail. Use whenever a store manager, department manager or duty manager opens the day or asks how yesterday went, even if they only ask 'how did we do'. Triggers - store brief, yesterday's sales, store KPIs this morning, how did the store do, morning store numbers, brief du matin magasin, CA d'hier, chiffres d'hier, comment s'est passée la journée, fréquentation hier, taux de transfo, panier moyen, point du matin, ouverture magasin."
---

# Store daily brief

Gives a store manager, before opening, the numbers that matter from yesterday, why they moved, and what the day holds,
on one screen.

## When to use
- Before opening, to prepare the team huddle and the day's priorities.
- The manager asks how yesterday or the weekend went, or why the till total looks low or high.
- A duty manager (manager d'ouverture) covers for the store manager and needs the context fast.
- Not for: a weekly or monthly deep dive (use `store-performance-analysis`), the 5-minute talk to the floor team
  (use `team-huddle-brief`), investigating one strange metric in depth (use `metric-anomaly-investigator`), or a
  personal non-store day plan (use `daily-briefing`).

## Inputs
- Store name or code (required). Infer from the user's profile, email signature or recent threads before asking.
- Date of the brief (optional, default: today, reporting on yesterday; on Monday, report Saturday and Sunday separately
  and the week to date).
- Target or budget for the day (optional, default: the target found in Databricks or Tableau, otherwise "no target found").
- Focus sport universes (optional, default: the 3 universes with the largest gap to N-1 in value).

## Sources
1. **Databricks via Polco (Genie-style MCP)**: ask in plain language first, for example « CA, nombre de tickets,
   fréquentation et quantité vendue du magasin X hier, même jour N-1 aligné, et objectif ». Then confirm with the
   **Databricks SQL MCP** if numbers look odd. Never assume table or column names: list catalogs/schemas/tables,
   `DESCRIBE` the candidate tables, and keep the final query to show in the brief.
2. **Tableau**: the store daily or weekly performance view, if one exists, to cross-check yesterday's totals and get
   the target. Quote the view name and its last refresh time.
3. **Google Calendar**: today's store meetings, visits (regional manager, auditors), events, trainings.
4. **Gmail and Google Chat / Slack**: overnight messages about deliveries, IT incidents, price changes, operations
   instructions from the region or HQ, and anything marked urgent.
5. **Jira or Airtable**: open store tickets (IT, maintenance, works) if the store tracks them there.
6. **Drive**: the day's operations checklist or rota if the user points to it.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Pull the four KPIs for yesterday** and the comparison day: revenue (CA), visitors (fréquentation, from door
   counters), transactions (tickets), units. Derive conversion = tickets / visitors, average basket = CA / tickets,
   units per ticket and average unit price. Compare with the **weekday-aligned N-1 day** (364 days earlier, same
   weekday), not the calendar date, and with the target if one exists.
2. **Sanity-check the data** before commenting: a conversion far outside the store's usual 8-week range (or above
   100%) or a visitor count near zero on an open day usually means a counter outage; a missing hour suggests a till or extraction gap; a public holiday or school
   holiday shift between N and N-1 distorts the comparison. Name the issue instead of explaining a fake swing.
3. **Decompose the gap to N-1**: sales = traffic × conversion × average basket. Use log shares so the parts add up:
   share of traffic = ln(T1/T0) / ln(S1/S0), and the same for conversion and basket. State the main driver in one
   sentence (« -8% de CA : la fréquentation explique l'essentiel, la transfo tient »).
4. **Find where it happened**: the 3 sport universes with the biggest value gap vs N-1, and the best and worst hour if
   hourly data exists (an hour with high traffic and low conversion often means too few teammates on the floor or a
   checkout queue).
5. **Read the day ahead**: meetings and visits, deliveries expected, events, staffing alerts mentioned in mail or chat,
   weather if the user gives it (rain on a Saturday moves cycling and outdoor sales).
6. **Choose the Top 3 priorities**: each one starts with a verb, is doable today, and links to a number or a message
   (for example « Remettre en rayon les 3 références de skis enfant en rupture avant 10 h »).
7. Fill the template. Add the "Data used" line with the query or the Polco question and the Tableau view.

## Output format
```markdown
**<Store> · <Weekday DD Month> · brief on <yesterday's date>**

### Yesterday in 4 numbers
| KPI | Yesterday | N-1 (same weekday) | Δ vs N-1 | Target | Δ vs target |
|-----|-----------|--------------------|----------|--------|-------------|
| Revenue (CA) | | | % | | % |
| Visitors (fréquentation) | | | % | — | — |
| Conversion (transfo) | % | % | pts | | pts |
| Average basket (panier moyen) | | | % | | % |

**Main driver:** <one sentence from the traffic × conversion × basket decomposition>
**Where:** <universe 1 Δ> · <universe 2 Δ> · <universe 3 Δ> · best hour <hh> / weakest hour <hh>
**Data caveats:** <counter outage / holiday shift / none found>

### Today
| Time | What | Who / prep |
|------|------|------------|

### Top 3 priorities
1. <Verb + action> — <why, with the number or message> ([link](…))
2. …
3. …

### Watch-outs
- <deliveries, IT, staffing, HQ instructions — one line each, max 4>

_Data used: Polco « <question> » · SQL: <tables queried> · Tableau: <view, refreshed hh:mm> · Calendar ✓ · Gmail ✓ · Chat ✓_
```

## Quality checks
- Every number traces to a named query, Polco answer or Tableau view; nothing is computed from guessed columns.
- N-1 is weekday-aligned, and any holiday or perimeter difference is stated.
- The three decomposition shares add up to roughly 100% of the revenue change.
- Conversion and basket are recomputed from CA, tickets and visitors, and match the dashboard within rounding.
- Each Top 3 item starts with a verb and is achievable today.
- The brief fits on one screen (≤ 25 table rows and bullets in total).

## Guardrails
- Never fabricate or "fill in" a missing KPI or target; write "not available" and say which source failed.
- No individual teammate's sales performance in the brief. Team-level only, unless the manager explicitly asks.
- Read only: do not reply to messages, change rotas or post in team channels without the user's confirmation.
- Do not quote confidential HR, health or disciplinary content from mail; use a neutral line pointing to the thread.
