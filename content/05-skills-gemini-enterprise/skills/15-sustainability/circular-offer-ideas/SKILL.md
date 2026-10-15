---
name: circular-offer-ideas
description: "Generates and screens circular economy offers for a product category, sport, store or B2B segment: repair and maintenance, second-hand buyback and resale, rental and subscription, take-back and recycling, durability and spare parts. Scores each idea on customer value, circularity (R-ladder), unit economics (rental rotations to break even, buyback margin, repair price vs new price), operational feasibility and safety, then shortlists 3 with a test plan. Use whenever someone looks for repair, rental, second-hand or take-back ideas, wants to extend product life or reduce waste in a range or store, even if they say 'more sustainable services'. Triggers - circular economy ideas, rental offer, second-hand offer, repair service ideas, take-back program, product as a service, idées économie circulaire, offre de location, seconde main, réparation, reprise des produits, allonger la durée de vie."
---

# Circular offer ideas

Helps a store, sport or product team find circular offers that customers want, that make economic sense and that
operations can run — and tests them small before scaling.

## When to use
- A sport or category team wants to extend product life (repair, spare parts, maintenance) or reduce waste.
- A store or region wants a local rental, second-hand or repair offer.
- A B2B team (clubs, schools, companies) wants a circular proposal such as rental fleets or kit take-back.
- Not for: checking how the offer will be advertised (use `green-claim-checker`), reviewing the product's own
  eco-design (use `eco-design-review`), running the repair workshop day to day (use `workshop-service-review`),
  or building the full financial business case (use `business-case-builder`).

## Inputs
- Scope: product category or sport, store or region, B2C or B2B (required).
- Goal: customer acquisition, margin, waste reduction, compliance, image (optional, default: balanced).
- Constraints: space, staff skills, budget, timeline (optional).
- Data on prices, costs, volumes, returns (optional; never invented).

## Sources
1. **Confluence and Drive**: existing circular services (second-hand, repair, rental) and their rules, results of
   previous pilots, spare parts catalogs, repairability or durability studies — reuse what exists before inventing;
   cite each document.
2. **Databricks (SQL MCP or Polco)**: sales volumes and average prices for the category, return and after-sales
   reasons (to find repair needs), seasonality (low-frequency use favors rental), size churn (kids' products).
3. **Tableau**: after-sales or workshop dashboards (repair volumes, turnaround), second-hand performance if tracked.
4. **Jira and Slack**: customer feedback or store requests mentioning repair, rental or resale.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Profile the category** on fit drivers: price point (higher → resale and rental more viable), use frequency
   (occasional → rental: e.g. ski touring, a camping trip), durability and wear, size churn (kids' bikes, ski boots),
   ease of grading and cleaning, hygiene (swimwear, mouthguards → exclude resale), safety criticality (helmets,
   climbing harnesses and ropes → PPE, no resale without a manufacturer inspection protocol), spare parts availability.
2. **Generate ideas** across the R-ladder (refuse, rethink, reduce, reuse, repair, refurbish, remanufacture,
   repurpose, recycle, recover) and five models: product-life extension (repair, maintenance, spare parts, DIY
   tutorials), resale (buyback, trade-in, refurbished), access (rental, subscription, B2B fleets), take-back and
   recycling, durability upgrades. Aim for 8–12 ideas, at least one per model where relevant.
3. **Rough unit economics** with user or source data only, otherwise mark *estimate* and show the formula:
   - Rental rotations to break even = (purchase cost − residual value) ÷ (rental price per rotation − handling,
     cleaning and inspection cost per rotation).
   - Buyback viability: buyback value + refurbishment + logistics ≤ resale price × (1 − target margin).
   - Repair attractiveness: repair price ÷ new product price; the lower, the higher uptake (state the ratio, do not
     invent an acceptance threshold).
4. **Score** each idea 1–5 on: customer value, circularity (higher on the R-ladder = better), economics,
   operational feasibility (space, skills, logistics, IT), risk (safety, brand, cannibalization). Show the total
   and the weakest criterion.
5. **Regulatory flags** (not legal advice — validate with Legal): right to repair directive (EU) 2024/1799;
   ecodesign regulation (EU) 2024/1781, including the ban on destroying unsold apparel and footwear for large
   companies; product safety (regulation (EU) 2023/988) also applies to second-hand products placed on the market;
   PPE regulation (EU) 2016/425 for protective equipment. National schemes (e.g. repair bonuses, EPR) to check locally.
6. **Shortlist 3** and write a **test plan** for each: hypothesis, pilot scope (one store or one sport, 8–12 weeks),
   success metrics (uptake rate, margin per transaction, NPS, items diverted), go/no-go threshold set by the user.

## Output format
```markdown
**Circular offers — <scope>** · goal: <goal> · data: <what was found / estimates>

### Category fit profile
| Driver | Reading | Effect |
|--------|---------|--------|

### Ideas
| # | Idea | Model | R-level | Customer value | Circularity | Economics | Feasibility | Risk | Total |
|---|------|-------|---------|----------------|-------------|-----------|-------------|------|-------|

### Unit economics (shortlist)
- <idea>: <formula with numbers> → <result> (<source or *estimate*>)

### Shortlist & test plans
#### 1. <idea>
- Hypothesis: … · Pilot: … · Metrics: … · Go/no-go: <user-set threshold> · Owner: …

### Regulatory and safety flags (validate with Legal)
- …

### Already existing internally
- <service/pilot> ([link](…))
```

## Quality checks
- Ideas cover at least 3 of the 5 models, and at least one idea sits at repair level or higher on the R-ladder.
- Every number comes from the user or a cited source, or is labeled *estimate* with its formula.
- Safety-critical and hygiene-sensitive products are excluded from resale or carry an inspection condition.
- Each shortlisted idea has a measurable go/no-go criterion.
- Existing internal services found in sources are listed so ideas do not duplicate them.

## Guardrails
- Never invent internal service names, prices, volumes or pilot results; search Confluence and Drive or ask.
- Regulatory points are flags, not legal advice; cite only the texts listed above and route questions to Legal.
- Do not describe the environmental benefit as a marketing claim; any external wording goes through
  `green-claim-checker`.
- Do not commit budgets, contact partners or launch pilots; this skill produces options for a human decision.
