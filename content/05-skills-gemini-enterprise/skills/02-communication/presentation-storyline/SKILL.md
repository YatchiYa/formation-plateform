---
name: presentation-storyline
description: "Builds the storyline of a presentation before anyone opens Google Slides: governing message, SCQA opening, a slide-by-slide outline where each slide title is a full-sentence takeaway, the evidence and chart type per slide, speaker notes and timing, and a horizontal-logic check that the titles alone tell the story. Use whenever someone prepares a deck, a pitch, a business review, a steering committee, a training or a kickoff presentation, even if they ask for 'a few slides' or a 'plan de présentation'. Triggers - presentation outline, storyline, slide structure, deck plan, pitch deck, build my slides, what should my slides say, structurer une présentation, plan de présentation, storyline de deck, préparer des slides, trame de présentation, construire mon support."
---

# Presentation storyline

Gives the user a deck that convinces: one message, a logical flow, and slides whose titles alone tell the story,
ready to be built in Google Slides.

## When to use
- A presentation to management, a committee, a store team, a supplier or a partner is being prepared.
- An existing deck feels like a list of slides with no thread.
- The user has data or a document and must turn it into slides.
- Not for: the written one-page version (use `executive-summary-writer`), a steering committee pack with
  decisions and budget (use `steering-committee-pack`), turning analysis results into a data story only (use
  `insight-storyteller`), or a speech without slides (use `talking-points-writer`).

## Inputs
- Topic and objective: what the audience should think or do at the end (required).
- Audience and their prior knowledge or position (required; ask if unknown, in the same question as the objective).
- Duration and format: live, remote, read-alone (optional, default: 20 minutes live, ~1 slide per 2 minutes).
- Source material: docs, data, previous decks (optional, default: searched in Drive).

## Sources
1. **Drive**: the source documents, previous decks on the same topic or for the same audience, the official slide
   template if one exists (to reuse its section names).
2. **Databricks / Tableau**: the figures the user points to, with the view or query name for citation.
3. **Confluence / Jira**: project pages, epic status and milestones, when the deck covers a project.
4. **Gmail / Calendar**: the meeting invite (audience, slot length) and the request that triggered the deck.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Write the governing message** in one sentence (≤ 25 words): the conclusion the audience must leave with.
2. **Draft the SCQA opening**: Situation (shared context, uncontroversial) → Complication (what changed or is at
   risk) → Question (what we must answer) → Answer (= the governing message). It becomes slides 1–3.
3. **Pick the body structure** that fits the objective:
   - Recommendation: answer → 3 reasons → plan → ask.
   - Review (season, store, project): headline result → drivers → issues → actions.
   - Problem solving: problem → root causes → options with criteria → recommendation.
   - Training or onboarding: why it matters → concepts → practice → recap.
4. **Write the slide list.** For each slide: an **action title** (full sentence with the takeaway, ≤ 15 words, e.g.
   "Running shoe sales grew in all stores except the two without a fitting area", not "Running sales"), the
   evidence (figure, quote, example, with source), the visual (bar for comparison, line for trend, waterfall for
   bridge, table for exact values, photo for field reality), and one speaker-note line.
5. **Respect the budget**: count slides from duration; one message per slide; move details to appendix.
6. **Test the horizontal logic**: read only the titles in order. They must form a coherent paragraph that ends
   with the ask. Fix any title that is a topic or that does not follow from the previous one.
7. **Test the vertical logic**: each slide's evidence proves its title, no more, no less.
8. **Plan the close**: the explicit ask (decision, budget, support, behavior), next steps, and 3 likely questions
   from this audience with short answers.

## Output format
```markdown
**Governing message:** <one sentence>
**Audience:** <who> · **Goal:** <think/do> · **Duration:** <min> → <N> slides + appendix

### SCQA
- S: … · C: … · Q: … · A: …

### Slide-by-slide
| # | Action title | Evidence (source) | Visual | Speaker note | Time |
|---|--------------|-------------------|--------|--------------|------|
| 1 | … | … | … | … | 1 min |

### Titles only (horizontal logic test)
1. … 2. … 3. …

### Close
- Ask: … · Next steps: …
- Likely questions: Q → short answer

### Appendix
- <backup slides>
_Missing data to collect: <list or "none">_
```

## Quality checks
- Every slide title is a full sentence with a takeaway, not a topic label.
- Reading the titles alone tells the whole story and ends with the ask.
- The slide count fits the duration (about 1 slide per 2 minutes, appendix excluded).
- Every figure has a source; figures not yet available are listed under "Missing data", never invented.
- Each slide has exactly one message and one suggested visual.

## Guardrails
- Do not fabricate figures, quotes or benchmarks to fill a slide; leave a marked gap.
- Keep confidential data (individual performance, salaries, non-public financials) out of decks meant for wide
  audiences; flag it if the source contains it.
- This skill outlines; it does not create or share the Google Slides file unless the user asks and confirms.

## Example
Input: "20-minute deck for the regional managers on why we should extend the bike repair workshop opening hours."
→ Governing message: "Extending workshop hours on Saturdays would absorb the repair backlog without new hires."
Titles test: 1. Repair demand peaks on Saturdays, when the workshop closes earliest → 2. The backlog doubles turnaround
in spring → 3. Customers who wait long buy elsewhere → 4. A rota change covers Saturday afternoons → 5. We ask approval
for a 3-store pilot from March. Figures marked as "Missing data" where the user has not yet pulled them.
