---
name: csr-data-request
description: "Builds a sustainability or CSRD-related data request for internal teams, stores, warehouses or suppliers: the indicator list mapped to ESRS topics or GHG Protocol scopes and categories, precise definitions, units, reporting period and boundary, calculation method, evidence required, data quality flags, owners, deadline, a ready-to-fill template and the cover email, plus a check of returned data. Use whenever someone must collect environmental, social or governance data, prepare a CSR or carbon reporting campaign, send a supplier questionnaire or chase missing ESG data, even if they say 'just a quick Excel'. Triggers - CSRD data collection, ESG data request, carbon data, supplier sustainability questionnaire, ESRS datapoints, scope 3 data, collecte de données RSE, demande de données CSRD, questionnaire fournisseur RSE, bilan carbone données, reporting extra-financier, campagne de collecte ESG."
---

# CSR data request

Produces a data request that people can answer correctly the first time: every indicator defined, unit and scope
fixed, evidence asked, owners and deadline set — then checks what comes back.

## When to use
- A CSR, carbon footprint or CSRD reporting campaign needs data from teams (stores, logistics, HR, purchasing).
- A buyer or sustainability team sends a questionnaire to suppliers or production partners.
- Returned data must be checked for gaps, unit errors and inconsistencies before consolidation.
- Not for: checking a marketing claim (use `green-claim-checker`), a buyer-side tender document (use
  `supplier-rfq-builder`), or assessing a supplier overall (use `supplier-evaluation`).

## Inputs
- Purpose: CSRD report, carbon footprint, supplier assessment, internal steering (required).
- Respondents: internal teams, sites, or suppliers (required); how many (optional, default: `[n]`).
- Indicators wanted, or the topics (optional, default: proposed from the purpose and the materiality assessment
  if one is found).
- Reporting period and deadline (optional, default: last closed fiscal year; deadline `[deadline — to confirm]`).
  With purpose and respondent type known, produce the full request now; do not ask for count or deadline first.

## Sources
1. **Drive and Confluence**: the double materiality assessment, the reporting methodology or protocol, the previous
   year's data request and its returns (reuse definitions for year-on-year comparability), emission factor sources
   used internally — cite them; never invent internal methodology.
2. **Databricks (SQL MCP or Polco)**: data already available centrally (energy invoices, sales volumes, purchase
   volumes, headcount aggregates) — do not ask respondents for what already exists; show queries used.
3. **Airtable**: supplier or site lists with contacts, if the user points to them.
4. **Gmail and Jira**: last campaign's questions and issues raised by respondents (to fix ambiguous definitions).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Frame the scope**: purpose, reporting period, organizational boundary (which entities, sites, suppliers),
   and the consolidation approach if it is a carbon footprint (operational or financial control, per GHG Protocol).
2. **Select indicators**: start from material topics. Map each to its frame — ESRS topical standards (E1 climate,
   E2 pollution, E3 water, E4 biodiversity, E5 resource use and circular economy, S1 own workforce, S2 value-chain
   workers, S3 affected communities, S4 consumers, G1 business conduct) or GHG Protocol scope 1, 2 (location and
   market based) and scope 3 category. Remove anything already available centrally (Sources, item 2). Keep the
   request short: every extra question lowers the response rate.
3. **Define each indicator** in a card: name, definition (what is included and excluded), unit (kWh, m³, t,
   tCO2e, %, headcount — never mixed), period, boundary, calculation method, accepted estimation method if no
   measurement, evidence (invoice, meter reading, certificate, audit report), and owner.
   Example: "Electricity consumption — kWh, 1 Jan–31 Dec, all meters of the site including warehouse areas, from
   supplier invoices; if invoices are missing, extrapolate from available months and flag 'estimated'."
4. **Add data quality fields** for each answer: source type (measured / calculated / estimated / supplier-specific
   / industry average), evidence attached (Y/N), comment. These feed the quality score in step 7.
5. **Build the template**: one row per indicator per site or supplier, locked units, drop-downs for categorical
   answers, a contact column, and instructions in the respondents' language.
6. **Write the cover email**: why it matters, deadline, time needed, contact, confidentiality of the data, how it
   will be used, and a reminder plan (D-7, D-2, D+1).
7. **Check returns** (when provided): completeness %, unit errors (e.g. MWh entered as kWh: value 1,000× off vs
   N-1), outliers vs N-1 (± 30 % flagged) or vs peers (intensity per m² or per unit), estimated share, missing evidence.

## Output format
```markdown
**Data request — <purpose>, <period> · respondents: <who, n> · deadline: <date>**

## Indicators
| # | Indicator | Framework mapping | Definition (in / out) | Unit | Method & estimation rule | Evidence | Owner |
|---|-----------|-------------------|-----------------------|------|--------------------------|----------|-------|

## Template columns
<Site/Supplier | Indicator # | Value | Unit (locked) | Source type | Evidence link | Comment>

## Cover email (ready to send)
Subject: …
<text>

## Reminder plan
- D-7 · D-2 · D+1 (escalation to <role>)

## Return check (if data provided)
| Respondent | Completeness | Issues (unit, outlier, missing evidence) | Action |
|------------|--------------|-----------------------------------------|--------|
```

## Quality checks
- Every indicator has exactly one unit, a period, a boundary and an evidence type.
- Every framework mapping is to a real ESRS standard code or GHG Protocol scope/category, or is marked "internal".
- No indicator asks for data already available centrally (or the reason is given).
- The template can be filled without reading any other document.
- Outlier and unit checks state the rule used (e.g. ± 30 % vs N-1).

## Guardrails
- Regulation moves: CSRD is directive (EU) 2022/2464 and ESRS are in delegated regulation (EU) 2023/2772; their
  timelines and scope were changed by the 2025 Omnibus package (including directive (EU) 2025/794). Do not state
  who is in scope or by when — validate with Legal or the reporting team. Not legal advice.
- Social data (S1) is requested only as aggregates; never collect names, health, union or individual pay data in
  the request. Supplier contact data is used only for this campaign (GDPR).
- Do not invent emission factors, thresholds or internal targets; reference the methodology doc or leave a placeholder.
- Do not send the request or reminders without the user's confirmation.
