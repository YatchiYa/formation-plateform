---
name: performance-review-writer
description: "Helps a manager write a fair, evidence-based performance review for one teammate: gathers work evidence from goals, Jira, GitHub, Drive and feedback received, maps it to goals and competencies, drafts strengths and growth areas with concrete examples, checks the wording for bias and vague labels, and prepares the review conversation. It never sets the rating. Use whenever a manager prepares an annual or mid-year review, a probation review or written feedback for a file, even if they only ask to 'polish my comments'. Triggers - performance review, annual review, write a review, review comments, manager evaluation, mid-year review, entretien annuel, évaluation annuelle, bilan de performance, rédiger l'évaluation, entretien de mi-année, commentaires manager."
---

# Performance review writer

Turns a year of work into a specific, balanced and bias-checked review that the teammate can recognize and act on.
The manager owns the judgment and any rating; this skill supplies the evidence and the words.

## When to use
- Annual or mid-year review season; the manager has a blank form or rough notes.
- A probation or trial-period review needs a written, factual summary.
- The manager wants to check that a draft is fair, specific and free of biased wording.
- Not for: the teammate's own self-assessment (use `self-assessment-coach`), cross-team consistency of ratings
  (use `calibration-prep`), one piece of feedback in the moment (use `feedback-sbi-writer`), or the development
  plan that follows (use `career-development-plan`).

## Inputs
- Teammate name or initials, role, review period (required).
- Goals or objectives set for the period (required; searched in Drive if not given).
- The review template or form and the competency framework (optional, searched in Drive/Confluence).
- Manager's notes, 1:1 notes, feedback received from peers or customers (optional).
- Teammate's self-assessment (optional, used to compare, never copied as the manager's view).

## Sources
1. **Drive**: goal docs, 1:1 notes, previous review, self-assessment, project docs the teammate authored.
2. **Confluence**: competency or career framework for the role, review guide and rating definitions.
3. **Jira**: issues and epics the teammate owned or closed in the period, with dates (tech, product, projects).
4. **GitHub**: merged PRs, reviews given, incidents handled (tech roles).
5. **Databricks / Tableau**: only team- or department-level KPIs the teammate owned (e.g. a department's
   availability rate), never individual surveillance metrics.
6. **Gmail and Chat**: thank-you or recognition messages, escalations, only those the manager points to.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Evidence log**: for each goal and competency, list facts with date and source: deliverable, result,
   behavior observed. Cover the **whole period** month by month; flag if > 60% of evidence comes from the last
   3 months (*recency bias*).
2. **Goal results**: for each goal, `expected → achieved → evidence → context` (resources, scope changes,
   dependencies). Distinguish what the teammate controlled from external factors.
3. **"What" and "how"**: results against goals, and behaviors against the framework (e.g. cooperation, customer
   focus, autonomy) using the internal wording if found.
4. **Strengths (2–3)** and **growth areas (1–2)**, each in SBI form: Situation, Behavior, Impact, plus one
   example. A growth area always comes with a concrete next step and the support offered.
5. **Bias and wording scan** — rewrite, then report:
   - Personality labels ("abrasive", "emotional", "not a natural leader", « manque de charisme ») → observed
     behavior and impact.
   - Double standards: would the same sentence be written for a teammate of another gender, age or origin?
   - Halo/horns: one event coloring the whole review → rebalance with the evidence log.
   - Absence-related content: periods of leave (parental, sick, part-time) are neither negatives nor gaps;
     assess performance on time worked and say so neutrally if needed.
   - Vague praise ("great job") → specific contribution and impact.
6. **Rating support** (if the form has ratings): quote the internal rating definitions next to the evidence and
   leave the rating field for the manager. Do not suggest a level.
7. **Conversation prep**: opening line, 3 messages to land, 2 questions to ask the teammate, how to handle
   disagreement (listen, note, review evidence together).

## Output format
```markdown
# Review draft — <Teammate>, <Role> · <period>
_Sources: <goals, framework, Jira/GitHub/Drive>. Evidence spread: <% per quarter> <⚠️ if recency>_
_Draft for the manager. Rating and final wording are the manager's decision._

## Summary (≤ 80 words)
…

## Goals
| Goal | Expected | Achieved | Evidence | Context |
|------|----------|----------|----------|---------|

## Strengths
- **<Strength>** — <Situation, Behavior, Impact> ([source](…))

## Growth areas
- **<Area>** — <SBI> → Next step: … · Support: …

## Rating (manager to fill)
| Dimension | Internal definition | Evidence pointer | Manager rating |
|-----------|--------------------|------------------|----------------|

## Wording changes made
| Original | Issue | Rewritten |
|----------|-------|-----------|

## Conversation prep
- Opening: … · Messages: 1… 2… 3… · Questions: …
```

## Quality checks
- Every strength and growth area has at least one dated, sourced example.
- Evidence covers each quarter of the period, or the recency warning is shown.
- No personality label, protected characteristic or leave-related negative remains in the draft.
- No rating is proposed; rating cells are empty for the manager.
- Growth areas each have a next step and support.

## Guardrails
- EU AI Act: performance evaluation that affects promotion or termination is high-risk. This skill drafts text
  from evidence; it never rates, ranks or recommends promotion, pay or dismissal. The manager decides.
- Do not mention health, disability, pregnancy, union activity, family situation or any protected characteristic.
- Do not use individual productivity monitoring data unless it is an agreed, documented goal metric.
- Never invent achievements, figures or feedback; unknown → ask the manager.
- Keep the draft private to the manager; do not post or share it without explicit confirmation. Local rules may
  require works council consultation on review processes; do not assume the form, use the official template.
