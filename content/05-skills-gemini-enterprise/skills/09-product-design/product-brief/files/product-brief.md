---
name: product-brief
description: "Writes a product brief for a physical sport product: the target practitioner and practice level, use conditions, jobs-to-be-done and pains with evidence, the benefits to deliver, hard constraints (norms, safety, price target, timing), success metrics and the open questions to close before design starts. Use whenever a product manager, designer or engineer starts or reframes a product (a tent, a shoe, a ball, a bike part, a fitness accessory), even if they only say 'help me frame this product' or 'write the spec'. Triggers - product brief, product framing, design brief, new product spec, target user for a product, brief produit, cahier des charges produit, fiche de cadrage produit, cadrage d'un nouveau produit, brief conception, besoin utilisateur produit."
---

# Product brief

Frames a sport product before anyone sketches it: who practises, where, what job they hire the product for, what
must be true for it to succeed, and what is still unknown. A good brief kills bad ideas early and gives design,
engineering and testing one shared target.

## When to use
- A new product or a new generation of an existing product is starting (kick-off, ideation gate).
- A team disagrees on the target user or the price point and needs one written reference.
- An existing product underperforms and needs reframing from user problems, not features.
- Not for: a digital feature spec (use `prd-writer`), building personas (use `customer-persona-builder`), planning
  the research that feeds the brief (use `user-research-plan`), the test protocol (use `field-test-protocol`) or
  the eco-design review of a concept (use `eco-design-review`).

## Inputs
- Product idea or category, and the brand/sport universe if known (required).
- Target practitioner and practice (required; if absent, propose 2 candidate targets and ask the user to pick).
- Evidence: research synthesis, reviews, after-sales returns, sales data (optional, default: search sources).
- Price target, launch season, volume ambition (optional, default: marked *to confirm*, never guessed).
- Known constraints: norms, materials, industrial process, supplier (optional).

## Sources
1. **Drive and Confluence**: previous briefs for the same product family, research syntheses, test reports,
   range strategy and positioning docs. Reuse the internal template and wording if one exists, and cite it.
2. **Databricks (SQL or Polco)**: sales, return and repair reasons for the current or nearest product (ask Polco
   e.g. "top return reasons for model X, last 12 months"). Show the query or the question asked.
3. **Tableau**: range or product performance dashboards, if the user points to one.
4. **Airtable**: idea or concept backlogs, test campaign bases.
5. **Jira and Gmail/Chat/Slack**: decisions and open questions from the project kick-off threads.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Pin the practitioner.** Sport, practice (e.g. hiking day trips vs multi-day trekking), level (beginner,
   regular, expert), frequency, environment (temperature, terrain, weather, indoor/outdoor), and what they use today.
   One primary target only; a secondary target must not change any hard requirement.
2. **Write the jobs-to-be-done.** Format: *When <situation>, I want to <motivation>, so I can <outcome>.* Separate the
   functional job (stay dry on a rainy ridge), the emotional job (feel safe, feel like a real runner) and the social
   job. 1 main job, 2–3 related jobs.
3. **List pains and gains with evidence strength**: *strong* (behaviour seen in tests, return data, repeated across
   ≥ 5 sources), *medium* (several interviews or reviews), *weak* (one anecdote, internal opinion). A weak pain can
   stay in the brief only as a hypothesis to test.
4. **Translate pains into benefits, not features.** "Pitch in under 5 minutes alone" is a benefit; "pre-attached
   poles" is a solution and belongs in design options. Rank benefits: must-have, performance (more is better),
   delighter (Kano).
5. **State constraints** as testable statements: safety and norms (cite the norm only if found in sources or given
   by the user), price target, weight or volume ceilings, timing, industrial or supplier limits, durability and
   repairability expectations (link to `eco-design-review`).
6. **Define success metrics** before design: in-use (test pass criteria), commercial (sell-through, rating, return
   rate) and lifecycle (repair rate, lifespan). Leave targets blank or *to confirm* when no source gives them.
7. **Close with the unknowns**: the 3–5 riskiest assumptions (desirability, feasibility, viability) and how to
   de-risk each one (interview, prototype, field test, cost quote).

## Output format
```markdown
# Product brief — <product / working name> (<brand or sport universe>)
_Status: draft v<N> · Owner: <name> · Sources: <links>_
_Assumptions: <one line>_

## 1. In one sentence
For <practitioner> who <job>, <product> delivers <key benefit>, unlike <current alternative>.

## 2. Target practitioner
| Item | Primary target | Secondary (optional) |
|------|----------------|----------------------|
| Sport & practice | | |
| Level & frequency | | |
| Use conditions | <terrain, temperature, weather, duration> | |
| Current solution | | |

## 3. Jobs, pains, gains
| Type | Statement | Evidence | Strength |
|------|-----------|----------|----------|
| Main job | When …, I want …, so I can … | <source> | strong / medium / weak |
| Pain | | | |
| Gain | | | |

## 4. Benefits to deliver
| Benefit (user words) | Kano class | Measured by |
|----------------------|-----------|-------------|

## 5. Constraints
- Safety / norms: …
- Price target: <value or *to confirm*>
- Weight / volume / sizes: …
- Timing & industrial: …
- Durability & repair: …

## 6. Success metrics
| Metric | Target | Source / owner |
|--------|--------|----------------|

## 7. Riskiest assumptions & next steps
| Assumption | Risk type | How to test | By when |
|-----------|-----------|-------------|---------|

## 8. Out of scope
- …
```

## Quality checks
- Exactly one primary practitioner, described by practice and conditions, not by demographics alone.
- Every pain has a source and an evidence strength; no pain is marked *strong* on a single source.
- Section 4 contains benefits, not component names or technologies.
- Every price, norm, weight or volume figure is cited or marked *to confirm*.
- Each riskiest assumption has a concrete test method that feeds `user-research-plan` or `field-test-protocol`.

## Guardrails
- Never invent technical specs, norm references, prices, margins or sales figures. Use a placeholder and list it in
  the open questions.
- Do not present competitor information that is not in the user's sources (route to `competitive-product-teardown`).
- Safety-related requirements (protection, load, child use, visibility) are flagged for the product safety or
  quality owner to validate; the brief never declares them compliant.
- Anonymize any customer verbatim; no names or contact details of testers or customers.

## Example
Input: « Brief pour une tente 2 places de randonnée itinérante, gamme Forclaz, retours clients : condensation »
→ Practitioner: hikers doing 2–5 day treks, spring to autumn, mountain terrain. Main job: « Quand j'arrive au bivouac
fatigué, je veux monter un abri sec seul rapidement, pour récupérer avant l'étape suivante. » Pain *condensation*:
strength from return reasons in Databricks + reviews. Price target and weight ceiling: *à confirmer*.
