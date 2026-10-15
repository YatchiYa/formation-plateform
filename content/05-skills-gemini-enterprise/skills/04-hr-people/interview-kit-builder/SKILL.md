---
name: interview-kit-builder
description: "Creates a structured interview kit for a role: competencies from the job description, behavioral and situational questions with follow-ups, a 1-4 rating rubric with observable anchors per competency, an interviewer split across the loop and a candidate-facing agenda. Use whenever someone is preparing interviews, building an interview process, writing interview questions or a scorecard, for store, warehouse, office or tech roles, even if they only ask for 'a few questions'. Triggers - interview kit, interview questions, scorecard, interview guide, hiring loop, grille d'entretien, questions d'entretien, préparer un entretien, trame d'entretien, processus de recrutement."
---

# Interview kit builder

Turns a role into a fair, structured interview process. Every candidate gets the same questions and is rated against the
same observable anchors, which is one of the most reliable ways to predict job performance and to reduce bias.

## When to use
- A new opening needs an interview process, or an existing one feels inconsistent.
- A manager has to run an interview tomorrow and needs good questions.
- A loop must be split between several interviewers without overlap.
- Not for: writing the job ad (use `job-description-writer`), summarizing interviewer feedback after the interviews
  (use `interview-debrief-synthesizer`), or drafting the offer (use `offer-letter-drafter`).

## Inputs
- Role title and level (required).
- Job description or the main responsibilities (required). Search Drive and Confluence before asking.
- Context (optional, default: inferred from the role): store, logistics/warehouse, office/HQ, tech/digital, or
  production/sourcing; country; language of the interviews.
- Number of interview steps and the interviewers (optional, default: 3 steps).

## Sources
1. **Drive and Confluence**: the job description, the competency or career framework, and existing interview
   guides for the same job family. Reuse the internal competency names if they exist.
2. **Gmail and Chat**: the hiring manager's brief, if the user points to it.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Pull 4–6 **competencies** from the job description: 2–3 job skills and 2–3 behaviors. Use the internal framework
   wording if one was found, and cite it. Each competency needs a one-line definition of what "good" looks like in
   *this* role.
2. For each competency, write:
   - 1 **behavioral** question ("Tell me about a time…") and 2 STAR follow-ups (Situation, Task, Action, Result).
   - 1 **situational** question set in the real work context. For a store role, for example: "A customer brings back a
     tent used for two weeks and wants a refund…". For a tech role: "The checkout API latency doubles during
     a sale…".
   - For skill competencies, add a short **work-sample** exercise (≤ 20 min) if relevant.
3. Write the **rubric**, 1–4 per competency, with *observable* anchors:
   1 = no relevant example or contradicts the expectation; 2 = partial, needs guidance; 3 = solid, independent,
   relevant example with a result; 4 = exceptional, measurable impact, teaches others.
4. **Split the loop**: give each interviewer 2–3 competencies, so that every competency is covered at least once and
   at most twice, and say who covers motivation and practical questions.
5. Write the **candidate agenda**: the steps, how long each one takes, what to prepare, and how to ask for accommodations.
6. Run the fairness check below and rewrite any question that fails it.

## Output format
```markdown
# Interview kit — <Role>, <Level> (<Context>, <Country>)
_Sources: <JD link>, <framework link or "no internal framework found">_

## Competencies
| # | Competency | What good looks like in this role |
|---|-----------|-----------------------------------|

## Question bank
### <Competency 1>
- **Behavioral:** …
  - Follow-up: …
  - Follow-up: …
- **Situational:** …
- **Listen for:** <2–3 positive signals> · **Red flags:** <1–2>

## Rating rubric
| Competency | 1 | 2 | 3 | 4 |
|-----------|---|---|---|---|

## Interview loop
| Step | Interviewer | Duration | Competencies |
|------|-------------|----------|--------------|

## Scorecard (one per interviewer)
| Competency | Rating 1–4 | Evidence (what the candidate said or did) |
|-----------|-----------|--------------------------------------------|
Overall notes — evidence only, written before the debrief:

## Candidate agenda (ready to send)
<short message>
```

## Quality checks
- Each competency is covered by at least one question and has a full 1–4 rubric row.
- Every situational question is set in this role's real environment, not a generic office.
- Every question can be answered by a candidate without inside knowledge of Company.
- No question asks about, or invites, protected characteristics (see Guardrails).
- The scorecard asks for **evidence**, not just a number.

## Guardrails
- Never include questions about age, family plans or children, pregnancy, health or disability (describe the essential
  tasks instead and offer accommodations for the interview itself; medical fitness is assessed only by occupational
  health, e.g. the médecine du travail in France), religion, origin, nationality (only the legal right to
  work), sexual orientation, union membership or political views.
- Do not score or rank real candidates in this skill. It produces the kit. Hiring decisions are made by people, and the
  EU AI Act treats AI-led selection as high-risk.
- Adapt to local law if the country is known (for example, salary-history questions are banned in some jurisdictions).
  When unsure, leave the question out.

## Example
Input: "Kit d'entretien pour un vendeur sports d'hiver, magasin de Grenoble"
→ Output in French. Competencies such as *Partage de la passion du sport avec les clients*, *Conseil client*, *Esprit d'équipe*,
*Autonomie et sens des responsabilités*, *Gestion du stock et du rayon*. Situational question example: « Un samedi de
février, trois clients attendent pour du matériel de ski et un client revient avec des chaussures qui lui font mal… »
