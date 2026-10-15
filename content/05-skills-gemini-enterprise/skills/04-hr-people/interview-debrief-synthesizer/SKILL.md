---
name: interview-debrief-synthesizer
description: "Consolidates interviewer scorecards and notes for one candidate into an evidence grid per competency, shows where interviewers agree or diverge, flags non-job-related comments and missing evidence, and lists the open questions to settle in the hiring debrief. It never recommends hire or no-hire. Use whenever a hiring loop is finished and feedback sits in docs, emails or chat, or before a debrief meeting, even if the user just asks what the interviewers thought. Triggers - interview debrief, consolidate feedback, scorecard summary, hiring debrief, candidate feedback summary, synthèse des entretiens, débrief recrutement, consolider les retours, retours des recruteurs, compte rendu d'entretien."
---

# Interview debrief synthesizer

Gives the hiring team one fair, evidence-based view of a candidate before the debrief, so that the discussion is about
what the candidate said and did, not about who speaks first or loudest. The decision stays with the people in the room.

## When to use
- All interviews of a loop are done and feedback is spread across scorecards, emails and chat messages.
- Before a debrief meeting, to prepare the facilitator.
- Interviewers disagree and the team needs to see where exactly.
- Not for: building the questions or rubric (use `interview-kit-builder`), writing to the candidate (use
  `candidate-communication-writer`), or the offer (use `offer-letter-drafter`).

## Inputs
- Candidate identifier and role (required). Prefer initials or a candidate ID over a full name.
- The scorecards or notes of each interviewer (required). Search Drive and Gmail if the user names the loop.
- The interview kit with competencies and the 1–4 rubric (optional, default: competencies inferred from the
  scorecards and stated as an assumption).
- Meet transcript in Drive (optional, used only to check a quote, never to add new judgments).

## Sources
1. **Drive**: the interview kit, the scorecards (Docs or Sheets), Meet transcripts the user points to.
2. **Gmail and Chat**: feedback sent by interviewers about this candidate, in the threads the user names.
3. **Airtable** (if the team tracks hiring there): loop status and which interviewer covered what.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Inventory**: list each interviewer, their step, the competencies they were assigned, and whether their
   feedback was written *before* the debrief (timestamp). Late or post-discussion feedback is marked, because it
   tends to converge on the first opinion heard.
2. **Extract evidence**: for each competency, pull the concrete statements: what the candidate said or did, with
   the interviewer's name and rating. Separate:
   - **Evidence**: observable ("described how she reorganized the reserve to cut restock time"),
   - **Inference**: an interpretation ("seems motivated"),
   - **Non-job-related**: anything about appearance, accent, age, family, origin, "culture fit" without a behavior,
     or a comparison with an unrelated person. Do not reuse it; list it in the fairness box for the facilitator.
3. **Agreement map** per competency:
   - Spread of ratings ≤ 1 point → *aligned*.
   - Spread ≥ 2 points → *divergent*: show both pieces of evidence side by side and write the question that would
     resolve it ("Did the candidate give a result for the stock example, or only the plan?").
   - Competency rated by one interviewer only, or with no evidence → *gap*.
4. **Check the rubric anchors**: a rating with no evidence, or evidence that does not match the anchor wording
   (e.g. a 4 with no measurable impact), is flagged *rating not supported*. Do not change anyone's rating.
5. **Open questions for the debrief**: 3–6, ordered by how much they matter for the role's must-haves. Include
   the option of a short reference check or follow-up call if a must-have competency is a gap.
6. Write the summary in neutral language. No overall score, no average presented as a verdict, no ranking against
   other candidates.

## Output format
```markdown
# Debrief prep — <Candidate ID>, <Role>
_Sources: <scorecards, threads>. Feedback received: <n>/<n> interviewers · written before debrief: <n>_
_This is a preparation aid. The hiring decision is made by the hiring team._

## Evidence by competency
| Competency | Ratings (interviewer: 1–4) | Key evidence | Status |
|-----------|----------------------------|--------------|--------|
| <name> | A: 3 · B: 2 | <quote or fact> (A) / <fact> (B) | Aligned / Divergent / Gap |

## Where interviewers diverge
### <Competency>
- <Interviewer A>: <evidence> → <rating>
- <Interviewer B>: <evidence> → <rating>
- Question to resolve: …

## Evidence gaps
- <Competency> — <why: not covered / rating without evidence>

## Fairness box (for the facilitator only)
- <n> comment(s) not job-related were excluded: <category only, e.g. "remark on accent">, from <interviewer>.
- Ratings not supported by evidence: …

## Open questions for the debrief
1. …

## Suggested debrief order
1. Each interviewer reads their evidence (no ratings yet) · 2. divergent competencies · 3. gaps · 4. decision by
the hiring manager per the local process
```

## Quality checks
- Every rating in the grid is attributed to an interviewer and backed by quoted or paraphrased evidence, or
  marked *rating not supported*.
- The output contains no hire/no-hire, no overall score and no comparison with another candidate.
- Divergent competencies (spread ≥ 2) each have a resolving question.
- No protected characteristic or proxy appears outside the fairness box, and inside it only as a category.
- The candidate is referred to by ID or initials unless the user asked otherwise.

## Guardrails
- EU AI Act: AI-supported candidate evaluation is high-risk. This skill organizes human feedback; it never scores,
  ranks, shortlists or rejects. If asked "should we hire?", answer that the decision belongs to the hiring team and
  offer the open questions instead.
- Do not infer personality traits, health or emotions from transcripts. Use transcripts only to verify quotes.
- GDPR: keep the summary to the hiring team; do not copy candidate data into other docs or channels. Remind the
  user of the local retention rule for candidate data if one is found in Drive/Confluence; never invent it.
- Draft-only: do not post the summary in a channel or email it without the user's confirmation.
