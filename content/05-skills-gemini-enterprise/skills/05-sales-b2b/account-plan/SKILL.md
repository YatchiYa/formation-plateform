---
name: account-plan
description: "Builds a strategic plan for a key B2B account such as a large club or league, a school network, a multi-site company or a local authority: account snapshot from real history, customer goals, whitespace matrix of sites and offers, stakeholder map with relationship coverage, 12-month objectives, action plan with owners and dates, risks and a review rhythm. Use whenever a seller or key account manager must plan growth, retention or renewal on an important customer, prepare a business review with them or take over a big account, even if they only ask how to grow this customer. Triggers - account plan, key account plan, strategic account, grow this customer, whitespace, QBR prep, plan de compte, plan d'action compte clé, développer ce client, grand compte, revue d'affaires client, fidéliser un client B2B."
---

# Account plan

Gives a key account manager a one-document strategy for an important customer: where we stand, where the customer is
going, where the untapped potential is, who we must know, and what we do in the next 12 months.

## When to use
- Annual or seasonal planning for the top accounts of a portfolio.
- Before a business review (QBR) with a customer, or a contract or framework renewal.
- A new seller inherits a big account.
- Not for: a first look at an unknown organisation (use `account-research`), one specific offer (use
  `b2b-proposal-builder`), or the whole pipeline (use `pipeline-review`).

## Inputs
- Account name (required).
- Planning horizon and revenue or volume goal if one exists (optional, default: 12 months, no target assumed).
- Offers available to propose (optional, default: from Confluence or Drive offer descriptions).
- Internal team on the account (optional, default: from Airtable owner fields).

## Sources
1. **Databricks (SQL or Polco)**: order history by site, category and season for the account; trends year over year.
   Show the query or Polco question.
2. **Airtable**: account, contacts, open and closed opportunities, notes, contract or framework end dates.
3. **Gmail and Calendar**: relationship activity: who we talk to, how often, last meeting with each stakeholder.
4. **Drive**: contracts, framework agreements, previous plans and business reviews, satisfaction feedback.
5. **Tableau**: an existing customer dashboard, if any.
6. **Confluence**: offer catalogue and segment playbooks (what we can propose).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Snapshot**: revenue or volume by season and category, trend, share of the customer's total spend if a source
   gives it (otherwise "unknown"), open opportunities, contract end dates, service issues. Facts only, sourced.
2. **Customer goals**: what the customer is trying to achieve, in their terms, from documents and notes. Examples: a
   club aims for more licensed youth players and a girls' section; a company's HR wants more employees active in its
   wellbeing programme; a town opens a new multi-sport facility; a school network renews PE equipment over three years.
   Each goal links to a source or is marked *to validate with the customer*.
3. **Whitespace matrix**: rows = customer units (sites, teams, schools, departments), columns = offer families. Cell =
   Buying (B), Buying elsewhere (E), Not buying (–), Unknown (?). The ? and E cells are the plan's opportunities; size
   them only with sourced numbers (e.g. number of teams × players), otherwise leave unsized.
4. **Stakeholder map**: for each known role, influence (High/Med/Low), stance toward us (Champion, Supporter, Neutral,
   Sceptic), last contact date, and who owns the relationship internally. Coverage rule: every High-influence
   stakeholder needs a named internal owner and a contact in the last 90 days; single-threaded accounts (one contact)
   are a risk.
5. **Objectives** (3 max, SMART): one retention, one growth, one relationship, each tied to a customer goal. Example:
   "Equip the new girls' U13–U18 teams (4 teams) before the September season start."
6. **Action plan**: per objective, 2–4 actions with owner, date and the customer value. Include the review rhythm (e.g.
   season-start check, mid-season reorder point, end-of-season review).
7. **Risks and mitigations**: renewal or tender date, competitor present (E cells), single-threading, service issues,
   budget changes after elections or board changes.

## Output format
```markdown
# Account plan — <Account> · <horizon> · v<date>
**Ambition in one line:** <where we want this account to be, for the customer's benefit>

### Snapshot
| Season | Revenue/volume | Main categories | Trend | Source |
|--------|---------------:|-----------------|-------|--------|
Open issues: … · Contract/framework end: …

### Customer goals
1. <goal> — <source or "to validate">

### Whitespace
| Unit \ Offer | <offer 1> | <offer 2> | <offer 3> |
|--------------|:---:|:---:|:---:|
| <site/team> | B | E | ? |
Top opportunities: …

### Stakeholders
| Role | Name | Influence | Stance | Last contact | Internal owner |
|------|------|-----------|--------|--------------|----------------|

### Objectives (12 months)
1. … (customer goal served: …)

### Action plan
| Objective | Action | Owner | Date | Customer value |
|-----------|--------|-------|------|----------------|

### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|

### Review rhythm
- …
```

## Quality checks
- Every snapshot figure has a source; unknown share of wallet is written "unknown", not estimated silently.
- Each objective links to at least one customer goal and has at least two dated actions with owners.
- Every High-influence stakeholder has an internal owner, or the gap is listed as a risk.
- Whitespace cells marked B or E are supported by data or notes; the rest are ? or –.
- The plan names the next renewal, tender or budget date if one exists.

## Guardrails
- Stakeholder notes stay professional (role, priorities, stance on the offer); no personal profiling, private life or
  political opinions, including for elected officials.
- Never invent revenue, targets, prices, discounts or contract terms.
- If the customer is a public body, growth must go through the applicable procurement rules; no plan to split orders
  or bypass a tender.
- Internal document: do not share the stakeholder map or risks with the customer. Draft only; no Airtable edits
  without confirmation.
