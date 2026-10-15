---
name: field-test-protocol
description: "Designs a field or user test protocol for a physical sport product or prototype: testable hypotheses with pass criteria, tester profiles and screener, test conditions and the conditions log, objective and subjective measures with scales, comparison and blinding design, safety risk assessment with stop rules, informed consent, logistics and a ready-to-print test sheet. Use whenever a product team plans to put a prototype or product in the hands of testers (on the trail, in the water, in the gym, on the pitch), even if they only ask for 'a feedback form for testers'. Triggers - field test protocol, user test plan, tester feedback form, wear test, prototype test, protocole de test terrain, test utilisateurs produit, fiche testeur, test en conditions réelles, campagne de tests, questionnaire testeur, test de port."
---

# Field test protocol

Produces a protocol that turns "let's give it to a few testers" into evidence a product team can decide on: clear
hypotheses, the right testers, controlled conditions, comparable measures and, first of all, safe and consenting
testers.

## When to use
- A prototype or pre-series product is ready for testing in real practice conditions.
- The team must compare a new solution with the current product or a reference product.
- A product has an in-use issue (returns, reviews) to reproduce and understand.
- Not for: exploratory interviews about the practice (use `user-research-plan`), synthesizing the test results'
  qualitative feedback (use `research-synthesis`), framing the product (use `product-brief`) or a digital A/B test
  (use `experiment-design`).

## Inputs
- Product or prototype, its intended use and the product brief (required; search Drive first).
- What the test must decide (go / iterate / choose between options) and the deadline (required).
- Reference product to compare with (optional, default: the current model of the range if one exists; if its name
  is not given or found, write « [current reference model] », never a made-up model name).
- Available testers, sites, season, test duration, budget (optional, default: proposed, marked *to confirm*).
- Lab test results already available (optional; field tests complement lab tests, they do not replace them).

## Sources
1. **Drive and Confluence**: product brief, previous test protocols and reports for the product family, the
   internal test and safety procedures and consent templates (follow them if found and cite them), norm summaries.
2. **Airtable**: tester panels and past campaigns (profile counts and criteria only; no personal data export).
3. **Databricks (SQL or Polco)**: return, repair and review reasons on the current product, to target hypotheses
   (e.g. "main defects reported on model X after 6 months"). Show the query.
4. **Jira**: the product development epic, open issues on the prototype.
5. **Gmail and Chat/Slack**: engineering notes on known prototype limits that affect safety.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Write hypotheses**, each tied to the brief and to the decision: *For <tester profile> in <conditions>, <product>
   <expected effect> compared with <reference>, measured by <measure>, pass if <criterion>.* Max 5. Pass criteria
   come from the brief or the user; if none exist, write « [to define with the product owner] » in the Pass criterion
   cell and « none found » as its source; never invent a threshold (no « mean > 5.5 »), and « product team / user
   expectation » is not a source.
2. **Choose the design**:
   - *Paired comparison* (each tester uses new and reference product) beats separate groups when testers are few.
   - *Randomize order* (half start with A, half with B) to cancel learning and fatigue effects.
   - *Blind* where possible: cover logos and visible differences; tell testers only what safety requires.
   - Separate *lab* measures (abrasion, waterproofness, load) from *field* measures (comfort, ease of use, durability
     in real use). Field results never certify a norm.
3. **Define tester profiles** from the target practitioner: practice, level, frequency, body or size ranges needed
   for fit, conditions they can access. Include a share of demanding users who push the product. Write a screener
   with exclusion criteria (no actual practice, injury preventing the activity, conflict of interest).
4. **Fix and log the conditions**: place and terrain, weather, temperature, humidity, duration, distance or number of
   sessions, intensity, care and washing between uses. Uncontrolled conditions are logged on every sheet so results
   can be segmented later.
5. **Select measures**:
   - *Objective*: time to set up, weight carried, wear observed (photo at fixed points and intervals), failure mode
     and moment, sensor data if available.
   - *Subjective*: 5- or 7-point anchored scales (e.g. thermal comfort from 1 = too cold to 7 = too hot, 4 = neutral),
     preference between A and B, and *why* in free text. Ask right after use, not days later.
   - *Incidents*: any discomfort, injury, failure, with time and conditions.
6. **Assess safety** for the activity and the prototype: hazards (fall, cold, drowning, overheating, structural
   failure, allergy to new materials), mitigation (supervision, buddy system, weather limits, protective equipment,
   briefing), **stop rules** (tester or supervisor stops at any pain, failure or unsafe condition), incident reporting
   path and emergency contacts. Flag high-risk tests (height, water, speed, load-bearing, children) for sign-off by
   the safety or quality owner before start.
7. **Write consent and data handling**: purpose, what testers do and for how long, risks and how they are reduced,
   right to stop at any time without justification, what data and photos are collected, retention, prototype return
   and confidentiality. Use the internal template if found; otherwise mark *to validate with legal / DPO*.
8. **Plan analysis**: per hypothesis, how results are compared (paired difference, preference count with reasons,
   failure count per hours of use), how conditions are segmented, and who decides.

## Output format
```markdown
# Field test protocol — <product / prototype> v<N>
_Decision: <go / iterate / choose> by <date> · Owner: <name> · Brief: <link> · Status: draft, safety sign-off <pending/done>_

## Hypotheses
| # | Hypothesis | Measure | Pass criterion | Source of criterion |
|---|-----------|---------|----------------|---------------------|

## Design
- Comparison: <paired A/B · single product · vs reference X> · Order: <randomized> · Blinding: <how>
- Testers: N=<n> per profile (*to confirm*) · Duration: <…> · Sites & season: <…>

## Tester profiles & screener
| Profile | Practice & level | Sizes / fit needs | N |
|---------|------------------|-------------------|---|
Exclusion: …

## Conditions to log
<place · terrain · weather · temperature · humidity · duration · intensity · care>

## Safety
| Hazard | Mitigation | Stop rule |
|--------|-----------|-----------|
Incident path: … · Emergency contacts: <placeholder> · Sign-off required: <yes/no, by whom>

## Consent (summary; full form attached)
- Purpose · Activities & duration · Risks · Right to stop · Data & photos · Retention · Confidentiality

## Analysis plan
| Hypothesis | Comparison method | Decision rule |
|-----------|-------------------|---------------|

## Test sheet (one per session)
Tester ID: ___ · Date: ___ · Product: A / B (coded) · Session #: ___
Conditions: place ___ · temp ___ °C · weather ___ · duration ___ · intensity ___
| Question | Scale | Answer | Why? |
|----------|-------|--------|------|
| <Q tied to H1> | 1 = … 7 = … | | |
Incidents (discomfort, injury, failure): ___ · Photos taken at: ___
```

## Quality checks
- Every hypothesis has a measure and a pass criterion that is either sourced or explicitly *to define*.
- Every test sheet question maps to a hypothesis; no question that nothing will use.
- Each scale has written anchors at both ends and the midpoint.
- The safety table covers the main hazards of this sport and of the prototype state, and every test has a stop rule.
- Consent includes the right to stop at any time and what happens to data and photos.
- The design states order randomization and blinding, or why they are not possible.

## Guardrails
- Never invent test results, pass thresholds, norm references or safety approvals. Results come only from completed sheets.
- Tester safety outranks test completion: no protocol asks a tester to continue after pain, injury or a structural
  failure. Prototypes with structural or protective functions are not tested in real risk conditions before lab
  validation and safety sign-off.
- Minors need parental consent and specific supervision; flag any test with minors or vulnerable people for review.
- Testers are identified by code on sheets; names and contacts stay in a separate, access-restricted file.
- Draft only: do not send invitations or create Airtable/Jira records without the user's confirmation.
