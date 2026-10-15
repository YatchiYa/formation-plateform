---
name: dashboard-spec-writer
description: "Writes a build-ready specification for a new or redesigned dashboard (Tableau or other): audience and decisions, the questions it must answer, KPI list with definitions and source tables, layout wireframe in text, filters and drill-downs, comparison bases, refresh and freshness rules, access and row-level security, acceptance tests. Use whenever someone asks for a dashboard, a report, a reporting request or a 'cockpit', or wants to brief a data analyst or BI developer, even if they only describe what they want to see. Triggers - dashboard spec, I need a dashboard, reporting request, BI brief, design a report, KPI cockpit, cahier des charges dashboard, besoin d'un tableau de bord, spécifier un reporting, maquette de dashboard, demande de reporting, brief BI."
---

# Dashboard spec writer

Turns a reporting wish into a specification a BI developer can build without guessing, and that end users will
actually use for decisions.

## When to use
- A team wants a new dashboard or a redesign of an unused one.
- A manager asks for "a reporting" and the request needs structure before it reaches the data team.
- Several existing dashboards overlap and should be merged.
- Not for: explaining an existing dashboard (use `tableau-dashboard-explainer`), defining one KPI in depth (use
  `kpi-definition-card`), or answering a one-off question (use `data-question-answerer`).

## Inputs
- Audience and the decisions they make with it (required).
- The questions they want answered (required; if missing, derive 3–5 from the audience and ask to confirm).
- Usage rhythm (optional, default: weekly ritual) and device (optional, default: desktop; mobile for store floor).
- Known data sources or existing dashboards (optional, default: search the sources below).

## Sources
1. **Tableau**: existing dashboards on the same topic (to reuse, merge or retire), their data sources and
   calculated fields.
2. **Confluence and Drive**: KPI definitions, previous reporting requests, ritual documents (weekly business
   review templates), brand or BI style guidelines if they exist.
3. **Databricks SQL MCP and Polco**: candidate tables (`SHOW TABLES`, `DESCRIBE TABLE`, `information_schema`),
   grain, history depth and freshness (`max(date)`), all read-only with `LIMIT`.
4. **Jira**: existing BI or data tickets for the same need, to avoid duplicates.
5. **Gmail, Chat and Slack**: the original request thread and stakeholder expectations.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Decisions first**: for each audience, list the decisions and the rhythm (daily huddle, weekly review,
   monthly business review). Drop any question that drives no decision.
2. **Questions → KPIs**: map each question to 1–2 KPIs. Use a metric tree where possible (e.g. sales = traffic ×
   conversion × average basket) so the dashboard supports top-down diagnosis.
3. **KPI table**: formula, grain, source table (three-level name), comparison base (N-1 aligned weeks, target,
   previous period), owner. Mark KPIs without a found definition as *to define* and route to `kpi-definition-card`.
   A table not seen in Databricks/Tableau or given by the user is written « [to confirm: <subject> table] » (e.g.
   « [to confirm: footfall table] »), never a plausible three-level name; its definition status is *to define*.
4. **Layout** (text wireframe, F-pattern): top band = 3–6 headline KPI tiles with comparison; middle = trend over
   time; bottom = breakdown by segment and a detail table. One question per zone. Chart choice rule: trend → line,
   compare categories → sorted bar, part-to-whole with ≤ 5 parts → stacked bar, distribution → histogram; avoid
   pies, dual axes and 3D.
5. **Interactivity**: global filters (period, perimeter), drill path (country → region → store → sport),
   tooltips with definitions, default view = the most common use.
6. **Data & refresh**: refresh frequency vs data latency, freshness indicator on the dashboard, history depth,
   expected volume, performance target (load < 10 s as a working assumption to confirm).
   Latency, refresh and history come from a source; otherwise write the *requirement* (« needed: daily by 08:00 »)
   and « actual: [to confirm] », never an asserted current latency.
7. **Access**: who sees what, row-level security rule (e.g. store manager sees own store), PII excluded or
   aggregated, small groups suppressed for people metrics.
8. **Acceptance tests**: values reconciled with a reference for 2–3 KPIs, filters tested, freshness visible,
   RLS tested with two profiles.
9. **Adoption**: owner, where it is linked (ritual agenda, intranet), retirement of the dashboards it replaces.

## Output format
````markdown
# Dashboard spec — <Name>
_Requester: <name> · Audience: <…> · Rhythm: <…> · Status: draft · Sources: <links>_

## Decisions and questions
| Audience | Decision | Question | KPI(s) |
|----------|----------|----------|--------|

## KPIs
| KPI | Formula | Grain | Source table | Comparison | Definition status |
|-----|---------|-------|--------------|------------|-------------------|

## Layout (wireframe)
```text
[ KPI tile ] [ KPI tile ] [ KPI tile ] [ KPI tile ]
[ Trend: <metric> by week, N vs N-1                ]
[ Breakdown: <metric> by <dimension> ] [ Detail table ]
```

## Filters and interactions
- Global filters: … · Default: … · Drill path: … · Tooltips: …

## Data and refresh
| Source | Latency | Refresh | History | Notes |
|--------|---------|---------|---------|-------|

## Access and privacy
- RLS rule: … · Personal data: … · Minimum group size: …

## Acceptance tests
- [ ] <test>

## Existing dashboards to reuse or retire
- <link> — <reuse / merge / retire>

## Open questions
- <question> — <who decides>
````

## Quality checks
- Every zone in the layout answers a question listed in the decisions table.
- Every KPI has a formula, grain, source and comparison base, or is marked *to define*.
- Source tables were found in Databricks or provided; none is invented.
- Access rules and refresh frequency are stated.
- At least three acceptance tests are testable by someone other than the author.

## Guardrails
- This is a draft spec; do not create Jira tickets or contact the BI team unless the user confirms.
- Read-only exploration of data; no DDL or DML.
- Avoid dashboards that rank individual teammates; if requested, flag the HR and privacy implications and propose
  team-level views.
- Do not promise delivery dates or capacity on behalf of the data team.
