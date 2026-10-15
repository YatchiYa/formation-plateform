---
name: executive-summary-writer
description: "Turns a long document, email thread, Meet transcript, Jira epic or analysis into a one-page executive summary built on BLUF and the pyramid principle: the answer or ask first, three supporting points with evidence, risks, decisions needed and next steps, every figure sourced. Use whenever someone must brief a director, a steering committee or a busy stakeholder, or says a doc is too long to read, even if they only ask to 'shorten' or 'summarize for my boss'. Triggers - executive summary, exec summary, BLUF, one-pager, TL;DR for leadership, summarize for my manager, brief the director, synthèse pour la direction, résumé exécutif, note de synthèse, faire une synthèse, résumer pour mon N+1, une page pour le comité."
---

# Executive summary writer

Gives a decision-maker the answer, the reasons and the ask in one page they can read in two minutes, without
opening the source.

## When to use
- A long Google Doc, slide deck, analysis or Confluence page must be shared with a director or a committee.
- A long Gmail, Chat or Slack thread must be turned into a status the reader can act on.
- A Meet transcript or workshop output must be reported upward.
- The user asks for "the key points" for someone senior, or a TL;DR at the top of their own doc.
- Not for: a neutral digest of a long document for the user themself (use `long-document-digest`), a decision doc
  with options and criteria (use `decision-memo`), a weekly RAG project status (use `project-status-report`), or a
  thread catch-up with who-owes-what (use `thread-catchup`).

## Inputs
- The source material: a link, file or pasted text (required). Several sources are fine.
- The reader and what they must do with it: decide, approve, be informed, unblock (optional, default: inform,
  reader = the user's manager's level).
- Length (optional, default: one page, ≤ 350 words; "30-second version" = 5 lines).
- Tone and language (optional, default: the user's language, neutral and direct).

## Sources
1. **Drive / Confluence**: the source documents the user points to, plus the latest version and its comments
   (unresolved comments often hold the real disagreements).
2. **Gmail, Google Chat, Slack**: the thread(s) given, and replies after the doc's last edit date that change a fact.
3. **Drive (Meet transcripts)**: transcript or Gemini notes of the meeting, if the summary covers a meeting.
4. **Jira / Confluence**: epic status, due dates, blockers, when the topic is a project.
5. **Databricks / Tableau**: only to check a figure quoted in the source, never to add new analysis unasked.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify the governing thought.** Answer in one sentence: "What does the reader need to know or do?" It is a
   conclusion ("We should delay the launch to week 12"), never a topic ("Launch update"). If the source has no
   conclusion, say so and write a situation summary instead, flagged as such.
2. **Classify the ask** with BLUF: Decision needed / Approval needed / Information only / Help needed. Put it in the
   first line with the deadline if there is one.
3. **Build the pyramid (Minto).** Find the 3 (max 4) key points that support the governing thought. Check that they
   are MECE: no overlap, and together they justify the conclusion. Typical groupings: why / what / how, or
   options / trade-off / recommendation, or results / causes / next steps.
4. **Attach evidence to each point**: one number, fact or example, with its source. Prefer the "so what" form:
   "Sales -8% vs N-1 (source), driven by the late winter, so the season stock is at risk".
5. **Extract risks and open questions**: the top 1–3, each with owner and impact, and unresolved disagreements found
   in comments or replies.
6. **Write next steps**: action, owner, date. Only those stated in the sources; others go under "Proposed".
7. **Cut.** Remove method, history and anything the reader cannot act on. Apply the 3 tests: headline readable alone;
   each point readable in 10 seconds; no acronym without its expansion at first use.
8. Offer two optional extras: a 5-line "elevator" version and a ready-to-paste email body.

## Output format
```markdown
**<Governing thought in one sentence>**
**Ask:** <Decision | Approval | Information | Help> — <what exactly> by <date>

### Key points
1. **<Point as a conclusion>** — <evidence: number/fact> ([source](…))
2. **<Point>** — <evidence> ([source](…))
3. **<Point>** — <evidence> ([source](…))

### Risks & open questions
- <Risk / question> — impact: <…> · owner: <name or "unassigned">

### Next steps
| Action | Owner | Date |
|--------|-------|------|

_Proposed (not yet agreed): <optional>_
_Sources: <list of links> · Not covered: <what the source did not say, if relevant>_
```

## Quality checks
- The first line is a conclusion or an ask, not a topic title, and is understandable without the rest.
- The body is ≤ 350 words (or the length the user set) and has at most 4 key points.
- Every number and date comes from a cited source; nothing is rounded in a way that changes its meaning.
- The key points are MECE and each one supports the governing thought.
- Owners and dates in "Next steps" exist in the sources; anything else is under "Proposed".
- No acronym or internal code is left unexplained for a reader outside the team.

## Guardrails
- Do not strengthen or soften the source: keep its level of certainty ("likely", "not confirmed").
- If the sources disagree with each other, show both values and their sources rather than choosing one silently.
- Do not include personal data (HR cases, health, individual performance) unless the summary is for HR and the user
  asks; use neutral wording otherwise.
- Draft only: do not send or post the summary until the user confirms the final text and recipients.

## Example
Input: « Fais-moi une synthèse pour le directeur régional de ce doc de 15 pages sur le test de location de vélos. »
→ Output in French, first line: « **Le test de location est rentable dans 2 magasins sur 4 ; proposition : l'étendre
à 3 magasins au printemps.** Demande : validation avant le 30/11 », then 3 points (usage, rentabilité, contraintes
atelier) each with a figure cited from the doc.
