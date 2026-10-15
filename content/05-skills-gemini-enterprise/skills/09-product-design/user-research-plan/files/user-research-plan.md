---
name: user-research-plan
description: "Plans a user research study for a sport product or a digital product: decision to inform, research questions, the right method for the question (interviews, contextual inquiry in the practice place, diary study, usability test, survey, data analysis), sample and recruiting screener, discussion guide, consent and data handling, timeline and roles. Use whenever someone wants to talk to users, understand practitioners, validate a concept, test a prototype or prepare interviews, even if they just say 'I want to ask some runners a few questions'. Triggers - research plan, user interviews, discussion guide, recruiting screener, usability test plan, plan d'étude utilisateur, entretiens utilisateurs, guide d'entretien, recrutement de testeurs, étude terrain, tests utilisateurs, comprendre les pratiquants."
---

# User research plan

Turns "we should talk to users" into a study that answers a real decision: the right method, the right people, a
neutral guide and clean consent. Most failed research asks the wrong question or uses the wrong method; this skill
fixes both before any field time is spent.

## When to use
- A product or feature team has open questions about practitioners, needs or a concept.
- A prototype (physical or digital) is ready for a first exposure to users.
- Someone drafted interview questions and wants them checked for bias.
- Not for: synthesizing notes already collected (use `research-synthesis`), testing a physical product's
  performance in use (use `field-test-protocol`), a quantitative A/B test (use `experiment-design`) or mining
  existing reviews (use `product-review-insights`).

## Inputs
- The decision this research must inform and its deadline (required).
- Product or concept, and target practitioners (required).
- What is already known: previous studies, data, reviews (optional, default: search sources).
- Constraints: budget, countries, languages, prototype availability, researchers (optional).

## Sources
1. **Drive and Confluence**: previous research plans, syntheses and personas on the same sport or product, the
   internal consent template and research ops guidelines (use them verbatim if found), the product brief.
2. **Airtable**: tester or panel bases and past recruitment criteria (only count profiles; do not export personal data).
3. **Databricks (SQL or Polco)** and **Tableau**: behavioural data that can narrow the questions (e.g. app funnel
   drop-off, return reasons), so research explains the *why* rather than re-measuring the *what*.
4. **Jira**: the epic or discovery ticket and its open questions.
5. **Calendar**: sessions already booked, availability of observers.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Start from the decision.** Write: "We will decide <X> by <date>; we need to know <Y>." Drop any question that
   would not change the decision.
2. **Write 3–5 research questions** (what the team needs to learn), distinct from interview questions (what you ask
   people). Tag each: *generative* (understand the practice) or *evaluative* (judge a solution).
3. **Pick the method per question** with this grid:
   | Need | Method |
   |------|--------|
   | Understand a practice, context, workarounds | Contextual inquiry on site (trail, gym, pool, club) or in-depth interview |
   | Behaviour over time (wear, habits, motivation) | Diary study, 1–4 weeks, photo/voice entries |
   | Can people use this concept or interface? | Moderated usability test, 5–8 participants per segment and iteration |
   | How many people share a need, preference ranking | Survey (after qualitative work, not instead of it) |
   | What people actually do at scale | Data analysis (Databricks), reviews, after-sales data |
   Say what each method cannot tell (e.g. interviews do not predict purchase; surveys do not explain why).
4. **Define the sample**: segments that matter for the decision (level, practice, conditions, not demographics by
   default), 5–8 per segment for qualitative work, include 1–2 *extreme users* (expert, beginner, adaptive athlete)
   because they reveal needs others hide. Write a screener with disqualifying questions (works for a competitor,
   recent participation, does not actually practise).
5. **Write the discussion guide**: warm-up, practice story ("tell me about your last outing"), deep dive per
   research question, concept exposure last (to avoid priming), wrap-up. Use open, past-behaviour questions; ban
   leading ("Wouldn't it be great if…"), hypothetical ("Would you buy…") and double questions.
6. **Consent and data**: purpose, what is recorded, retention, withdrawal at any time, incentive, who sees raw data.
   Use the internal template if found; otherwise draft one and mark it *to validate with the DPO / legal*.
7. **Plan logistics**: timeline (recruit, sessions, synthesis, share-out), roles (moderator, note-taker, observers
   max 2 in the room), note template aligned to research questions, and the share-out date before the decision date.

## Output format
```markdown
# Research plan — <topic> (<product / team>)
_Decision informed: <decision> by <date> · Owner: <name> · Sources: <links>_

## Research questions
| # | Question | Type | Method | Why this method |
|---|----------|------|--------|-----------------|

## What we already know
- <finding> — <source>

## Participants
| Segment | Criteria | N | Recruiting channel |
|---------|----------|---|--------------------|
**Screener:** 1. … (disqualify if …) 2. …

## Discussion guide (<duration> min)
1. Warm-up (5 min): …
2. Last practice story (10 min): …
3. <Research question 1> (… min): main question + 2 probes
4. Concept / prototype exposure (… min): tasks, think-aloud prompts
5. Wrap-up (5 min): …

## Consent & data handling
- Purpose · Recording · Retention · Withdrawal · Incentive · Access

## Logistics
| Step | Dates | Owner |
|------|-------|-------|
**Note template:** <columns aligned to research questions>

## Risks & limits
- …
```

## Quality checks
- Every research question maps to the decision; every method is justified against its question.
- No interview question is leading, hypothetical about future buying, or double-barrelled.
- Concept exposure comes after the practice story in the guide.
- Sample criteria describe practice and conditions; any demographic criterion has a stated reason.
- Consent covers purpose, recording, retention, withdrawal and contact for questions.
- The share-out date is before the decision date.

## Guardrails
- Minors, health conditions or adaptive sport participants need specific consent (parental consent for minors) and
  are flagged for review by the research or legal owner before recruiting.
- Collect only the personal data the study needs; no recordings shared outside the study team; plan anonymization
  before synthesis.
- Do not contact participants or send invitations; produce drafts and let the user send them after confirming.
- Never present the plan's expected findings as results.
