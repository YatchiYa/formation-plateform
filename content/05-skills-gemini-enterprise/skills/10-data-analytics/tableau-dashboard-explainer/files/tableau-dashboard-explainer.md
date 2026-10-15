---
name: tableau-dashboard-explainer
description: "Explains a Tableau dashboard or view in plain language: what question it answers, what each chart, KPI tile, color and filter means, how the metrics are defined, how to read it correctly, the three to five takeaways visible right now, and the caveats (data freshness, filters applied, definitions, small bases). Use whenever someone shares a Tableau link or screenshot, asks what a dashboard shows, how to read it, or what to conclude from it, even if they only say 'can you look at this dashboard'. Triggers - explain this dashboard, how do I read this, what does this chart show, Tableau view, dashboard walkthrough, explique-moi ce dashboard, comment lire ce tableau de bord, que montre ce graphique, lecture du dashboard, décrypter ce reporting."
---

# Tableau dashboard explainer

Helps a teammate read a Tableau dashboard correctly and quickly: what it measures, how to use it, and what it says
today, without over-reading the charts.

## When to use
- A teammate receives a dashboard link and does not know how to read it.
- A manager wants the key takeaways of a dashboard before a meeting.
- A newcomer needs a walkthrough of the team's standard reporting.
- Someone suspects a dashboard is misleading and wants its logic made explicit.
- Not for: designing a new dashboard (use `dashboard-spec-writer`), investigating why a number moved (use
  `metric-anomaly-investigator`), or defining one metric formally (use `kpi-definition-card`).

## Inputs
- The dashboard or view: Tableau link, name, or a screenshot (required).
- What the user needs (optional, default: walkthrough + current takeaways).
- Filters to apply (optional, default: the view's saved defaults, stated in the answer).

## Sources
1. **Tableau**: the workbook and views (title, sheets, data source, last refresh, filters, parameters, calculated
   field formulas, tooltips), and the current values if accessible.
2. **Confluence and Drive**: dashboard documentation, user guide, KPI definitions, release notes of the workbook.
3. **Databricks SQL MCP or Polco**: only to check a definition or a value behind a tile (read-only, aggregated,
   with `LIMIT` on exploration).
4. **Slack and Chat**: the dashboard's support channel for known issues or recent changes.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify**: workbook, view, owner, data source, last refresh time, default filters and parameters.
2. **Purpose**: state the question the dashboard answers and for whom (e.g. store managers, weekly ritual).
3. **Walk the layout** top-left to bottom-right: for each zone give chart type, measure, dimension, encoding
   (color = what, size = what), comparison base (N-1, target, previous period) and interaction (filter actions,
   drill-downs, tooltips).
4. **Define the metrics** from calculated field formulas or documentation; flag any metric whose definition is
   not found as *definition not documented*.
5. **Reading rules**: how to read deltas (% vs percentage points), what colors mean (red = below target or
   below N-1?), whether N-1 is aligned by week, whether totals are like-for-like, what the axis starts at.
6. **Takeaways now** (if values are visible): 3–5 facts, each with the value and its location in the dashboard.
   Separate *what the chart shows* from *interpretation*; avoid causal claims the data cannot support.
7. **Caveats**: freshness, incomplete current period, filters silently applied, small bases, mix effects (a total
   can move because the mix of stores or sports changed), truncated axes, dual axes.
8. **Next questions** worth asking, each mapped to the right skill or dashboard.

## Output format
```markdown
**<Dashboard name>** — answers: <question> · for: <audience>
_View: [link](…) · Data source: <name> · Last refresh: <date time> · Filters: <defaults applied>_

### How it is built
| Zone | Shows | Measure / dimension | Comparison | How to use |
|------|-------|---------------------|-----------|------------|

### Metric definitions
- **<Metric>**: <formula in words> (source: <calculated field / doc link> or _not documented_)

### How to read it
- <reading rule 1>
- <reading rule 2>

### What it says today
1. <fact with value> — <zone>
2. …
_Interpretation (not proven by the dashboard): <one line, optional>_

### Caveats
- <freshness / filters / small base / mix effect>

### Next questions
- <question> → <skill or view>
```

## Quality checks
- Last refresh time and the active filters are stated.
- Each zone of the dashboard appears once in the table.
- Every takeaway quotes a value visible in the dashboard and where it is.
- Facts and interpretations are visibly separated.
- Any metric without a found definition is labeled *not documented*.

## Guardrails
- Describe only what the user can see with their own Tableau permissions; do not pull data from views they cannot
  open.
- Never invent values for zones that could not be read (screenshot cropped, view not accessible): say so.
- Do not attribute causes to movements without evidence; route causal questions to analysis skills.
- Dashboards showing teammate-level data: summarize at team level and avoid singling out individuals.

## Example
Input: « Explique-moi ce dashboard de pilotage hebdo magasin » + link
→ Output in French. Zones: KPI tiles (CA, fréquentation, taux de transformation, panier moyen vs N-1), weekly trend,
breakdown by sport. Reading rule flagged: the conversion delta is in points, not %. Caveat: the current week is
incomplete until the refresh time shown. Next question routed to `metric-anomaly-investigator`.
