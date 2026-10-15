---
name: self-assessment-coach
description: "Coaches a teammate through their own self-assessment for an annual, mid-year or promotion review: pulls their own work evidence from Jira, GitHub, Drive, Calendar and kudos in Gmail or Chat, turns it into STAR achievements tied to goals and competencies, helps name growth areas honestly, calibrates tone (no under-selling, no inflation) and prepares their questions for the review meeting. Use whenever someone must write about their own year, fill a self-review form or prepare for their review conversation, even if they say they have nothing to write. Triggers - self assessment, self review, my annual review, write my accomplishments, what did I do this year, auto-évaluation, autoévaluation, préparer mon entretien annuel, mes réalisations, bilan de mon année, mon entretien individuel."
---

# Self-assessment coach

Helps a teammate show their real contribution with specific, verifiable examples, and arrive at their review ready
for a two-way conversation.

## When to use
- Review season: the self-assessment form is open and blank.
- Preparing for a promotion or role-change discussion.
- The teammate feels they "did nothing special" and needs help seeing their impact.
- Not for: a manager writing a review of someone else (use `performance-review-writer`), building a development
  plan (use `career-development-plan`), or preparing a regular 1:1 (use `one-on-one-prep`).

## Inputs
- Review period and the form's questions or template (required; searched in Drive).
- The teammate's goals for the period (optional, searched in Drive; otherwise asked).
- Target competencies or the career framework for their role (optional, searched in Confluence/Drive).
- What they are proud of and what was hard (optional; the skill asks 3 short questions if absent).

## Sources
Only the user's own work, accessed with their permissions.
1. **Drive**: their goal doc, docs they authored or co-edited, previous review, their notes.
2. **Jira**: issues they owned, resolved or reported in the period; epics they drove.
3. **GitHub**: their merged PRs, reviews given, issues closed (tech roles).
4. **Calendar**: recurring rituals they led, trainings attended, events organized (e.g. a store sport event).
5. **Gmail, Chat and Slack**: thank-you messages and recognition they received, to recall wins.
6. **Tableau / Databricks**: KPIs of the scope they own, if the user asks (e.g. department sales or availability).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Recall**: build a month-by-month timeline of the period from the sources. Ask 3 questions to complete it:
   "What are you most proud of?", "What was harder than expected?", "Who did you help?".
2. **Pick 3–5 achievements** with the most impact, not the most effort. Impact test: who benefited (customers,
   teammates, the business), what changed, how do we know.
3. **Write each in STAR**, ≤ 80 words: Situation, Task, Action (*I* did, not *we*, while crediting the team),
   Result with a number or observable outcome. Store example: « Rayon cycle en rupture sur les chambres à air
   chaque week-end → j'ai ajusté le réassort avec la réserve le vendredi → plus de rupture signalée sur 6
   week-ends (source : suivi rayon) ».
4. **Map to goals and competencies**: each achievement tagged to a goal and to 1–2 framework competencies,
   using internal wording if found.
5. **Growth areas (1–2)**: honest and forward-looking: what you learned, what you will do differently, the support
   you need. Avoid fake weaknesses.
6. **Tone calibration**:
   - Under-selling signals: "just", "helped a bit", only "we", no numbers → rewrite with own role and result.
   - Over-selling signals: superlatives without evidence, team results claimed alone → add evidence or credit.
7. **Prepare the conversation**: 3 questions to ask the manager (expectations for next level, feedback on a
   specific project, support for development).

## Output format
```markdown
# My self-assessment — <period>
_Sources used: <Jira, GitHub, Drive, kudos…>. Form: <template link or "free format">_

## Highlights (STAR)
### 1. <Achievement title>
- **Situation/Task:** …
- **Action (my part):** …
- **Result:** … ([evidence](…))
- **Goal / competency:** …

## Goals recap
| Goal | Result | Evidence |
|------|--------|----------|

## What I learned and want to grow
- …

## Support I need
- …

## Questions for my manager
1. …

<If a form exists: answers pasted field by field, within the form's length limits>
```

## Quality checks
- Every achievement has a result and an evidence link or is marked *from memory — add proof*.
- Each STAR uses "I" for the user's actions and credits others where relevant.
- At least one growth area with a concrete next step.
- Answers fit the form's fields and length limits if a form was found.
- No superlative without evidence remains.

## Guardrails
- Use only the user's own data and work. Do not pull colleagues' performance details or compare the user with
  named colleagues.
- Do not suggest a rating, promotion or pay outcome; those are decided by people in the review process.
- Do not include health, family or other private situations unless the user explicitly wants to mention context;
  then suggest sharing it with the manager or HR directly rather than in the written form.
- Never invent achievements or numbers. Draft only; the user submits the form.
