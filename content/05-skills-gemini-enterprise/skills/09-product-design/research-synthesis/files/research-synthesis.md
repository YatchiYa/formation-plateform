---
name: research-synthesis
description: "Synthesizes user research material (interview notes, Meet transcripts, diary entries, usability test notes, field test sheets) into evidence-backed insights: coded observations, affinity clusters, insight statements with evidence strength and counter-evidence, then opportunities framed as an opportunity solution tree. Use whenever someone has a pile of interview notes, transcripts or test feedback and needs to know what it means, even if they only say 'summarize these interviews' or 'what did users say'. Triggers - research synthesis, synthesize interviews, affinity map, insights from user interviews, key learnings, synthèse d'entretiens, synthèse de recherche utilisateur, cartographie d'affinités, enseignements des tests, qu'ont dit les utilisateurs, résumé des retours testeurs."
---

# Research synthesis

Turns raw research into insights a product team can act on and defend: each insight says what people do and why,
how strong the evidence is, and which opportunity it opens. It separates what was observed from what was said and
from what the team interprets.

## When to use
- After a round of interviews, contextual visits, diary study or usability sessions.
- Field test sheets came back and the team needs the user-experience patterns (not the pass/fail measures).
- Several past studies on the same topic must be consolidated before a product brief.
- Not for: planning the study (use `user-research-plan`), analysing star ratings and reviews at scale (use
  `product-review-insights`), a voice-of-customer report from tickets (use `voice-of-customer-report`) or building
  personas (use `customer-persona-builder`).

## Inputs
- The research material: notes, transcripts or a Drive folder (required).
- The research questions or the decision the study serves (required; search the research plan first).
- Participant profiles, anonymized (optional, default: taken from notes; segment labels only).
- Output depth (optional, default: full synthesis; "quick" gives top 5 insights only).

## Sources
1. **Drive**: the research plan, session notes, Meet transcripts (Docs in the Meet Recordings folder), diary
   exports, field test sheets. Read every session, not a sample.
2. **Confluence**: earlier syntheses on the same practice, to flag what is confirmed, new or contradicted.
3. **Airtable**: research repositories or observation bases if the team keeps one (tags, participant segments).
4. **Databricks (Polco) or Tableau**: optional quantitative check of an insight's reach (e.g. share of returns citing
   the same issue); show the query.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Extract observations**, one per line, from each session: ID (P03-07), quote or behaviour, context, and its type:
   *seen* (observed behaviour or workaround), *said* (stated opinion), *measured* (task time, error, test value).
   Keep the participant's words; do not paraphrase into the team's vocabulary yet.
2. **Code bottom-up** (affinity mapping): group observations that share a meaning, not a keyword. Name each cluster
   with a sentence in the user's voice ("I never know if my shoes are still protective"), not a label ("Durability").
   Aim for 6–12 clusters; split any cluster with > 25 % of observations.
3. **Write insights** from clusters: *<who> <does/feels what> because <underlying reason>, which means <implication>.*
   An insight explains a why; a fact without a why stays a finding.
4. **Rate evidence strength** per insight:
   - *Strong*: ≥ 5 participants across ≥ 2 segments, includes *seen* behaviour, no strong counter-evidence.
   - *Medium*: 3–4 participants, or *said* only, or one segment.
   - *Weak*: 1–2 participants or one vivid anecdote. Keep it as a hypothesis.
   Always list counter-evidence (participants who did the opposite) and say who was *not* in the sample.
5. **Map to the research questions**: answered, partly answered, not answered. Unanswered questions go to next steps.
6. **Build the opportunity solution tree**: desired outcome (from the brief or OKR) → opportunities (unmet needs,
   pains, desires phrased from the user side) → solution ideas (2–3 per opportunity, clearly labelled ideas) →
   assumption tests. Prioritize opportunities by size (how many, how often), severity, and fit with the outcome.
7. **Select 3–5 verbatims** that carry the top insights, anonymized (segment + participant ID only).

## Output format
```markdown
# Research synthesis — <study> (<dates>, N=<participants>)
_Decision served: <decision> · Material: <links> · Sample: <segments>; not covered: <segments missing>_

## Top insights
| # | Insight | Strength | Evidence (IDs) | Counter-evidence |
|---|---------|----------|----------------|------------------|
| 1 | <who> <does/feels> because <why>, so <implication> | strong | P02, P05, P07 (seen), P09 (said) | P04 |

## Answers to research questions
| Question | Status | Short answer | Insights |
|----------|--------|--------------|----------|

## Affinity clusters
### <Cluster name in the user's voice> (<n> observations, <n> participants)
- "<verbatim>" — P03, <segment>
- <behaviour seen> — P06

## Opportunity solution tree
**Outcome:** <desired outcome>
- **Opportunity:** <unmet need> (size, severity)
  - Idea: … · Assumption to test: …
  - Idea: …

## Surprises & contradictions
- …

## Next steps
- <research gap / test to run / owner>
```

## Quality checks
- Every insight has a *because* and links to participant IDs; none is supported by a single quote only, unless rated weak.
- Strength ratings follow the rule in step 4; no insight is *strong* without observed behaviour.
- Each research question has a status; unanswered ones appear in next steps.
- Opportunities are phrased as user needs, not as features; solution ideas are labelled as ideas.
- Verbatims carry no names, employers, locations or other identifying details.
- The not-covered segments are stated so readers know the limits.

## Guardrails
- Pseudonymize before quoting: participant IDs and segment only. Do not copy health details beyond what the product
  question needs (e.g. "knee pain while descending" is fine; a medical history is not).
- Do not inflate: no percentages from qualitative samples ("4 of 9", not "44 %"), no market sizing from interviews.
- Never invent quotes or merge two participants into one quote.
- Do not file Jira tickets or post the synthesis; propose them as drafts for the user to confirm.
