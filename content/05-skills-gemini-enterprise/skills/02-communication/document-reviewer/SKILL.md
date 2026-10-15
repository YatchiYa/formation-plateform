---
name: document-reviewer
description: "Reviews a Google Doc, Confluence page or pasted draft like a demanding senior editor: verdict first, then numbered comments by severity on purpose, structure, logic and evidence, clarity, gaps and risks, with rewritten versions of the weakest key passages and a readiness score. Use whenever someone asks for feedback on a document, a proposal, a note, a procedure or a strategy before sending it, or asks 'is this clear', 'what's missing' or 'can you proofread', even if they only want a quick look. Triggers - review my doc, give feedback, proofread, critique this, what's missing, is this clear, check my document, relis mon document, donne-moi ton avis, relecture, critique ce doc, qu'est-ce qui manque, c'est clair, corrige mon texte."
---

# Document reviewer

Tells the author, before their readers do, whether the document achieves its purpose and exactly what to fix,
in order of impact.

## When to use
- A proposal, strategy note, procedure, report or brief is about to be shared with a manager or a committee.
- The author is too close to the text to see its gaps.
- A peer review is requested on a Confluence page or a Google Doc.
- Not for: changing tone or length of a short message (use `message-rewriter`), summarizing a document for a
  reader (use `executive-summary-writer`), comparing two versions (use `document-comparison`), or checking a
  document against an internal policy (use `policy-compliance-check`).

## Inputs
- The document: link or text (required).
- Its purpose and intended reader (optional, default: inferred from the doc and stated in one line).
- Review depth: quick (top 5 issues) or full (optional, default: full for ≤ 10 pages, quick above).
- Specific concerns of the author (optional).

## Sources
1. **Drive / Confluence**: the document, its existing comments and suggestions (avoid repeating them, flag those
   still open), and the template or guideline for this type of doc if one exists.
2. **Drive / Confluence / Jira / Databricks / Tableau**: only to verify figures and facts the document states when the
   source is referenced in it.
3. **Gmail / Chat**: the request that led to the document, to check it answers the actual ask.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Restate the purpose** in one sentence ("This doc should get <reader> to <decide/do/understand> <what>"). If you
   cannot, that is the first and most severe comment.
2. **Check the five layers, top-down** (fix big things before commas):
   - **Purpose & reader**: is the conclusion or ask on page 1? Is the level of detail right for the reader?
   - **Structure**: does the outline follow one logic (pyramid, problem→solution, chronology)? Do headings say
     something? Is anything in the wrong section?
   - **Logic & evidence**: does every claim have support? Look for leaps ("therefore" without reason),
     correlation taken as cause, cherry-picked periods, missing baseline (vs N-1, vs target), inconsistent figures
     between sections, totals that do not add up.
   - **Gaps & risks**: missing options, costs, owners, dates, risks, assumptions, counter-arguments, impact on
     teammates or customers, legal or safety aspects.
   - **Clarity**: long sentences (> 25 words), passive voice hiding who acts, jargon and acronyms, vague words
     ("soon", "significant", "optimize").
3. **Write numbered comments** with severity: 🔴 blocking (the doc fails its purpose or contains an error),
   🟠 important (weakens it), 🟢 polish. Each comment quotes the passage (≤ 15 words), says what is wrong and proposes
   the fix.
4. **Rewrite 2–3 key passages**: usually the opening, the recommendation and the weakest section.
5. **Score readiness** 1–5: 1 = rethink, 2 = major rework, 3 = fix 🔴 then send, 4 = minor edits, 5 = ready.
6. Format the comments so the user can paste them into the doc's comments (this skill does not edit the doc).

## Output format
```markdown
**Verdict: <score>/5 — <one-sentence reason>**
_Read as: <purpose> for <reader>_

### Top 3 fixes
1. … 2. … 3. …

### Comments
| # | Sev. | Section | Passage | Issue | Suggested fix |
|---|------|---------|---------|-------|---------------|
| 1 | 🔴 | … | "…" | … | … |

### Rewritten passages
**<Section> — before:** "…"
**After:** …

### What works well
- <2–3 specific strengths to keep>
```

## Quality checks
- Every comment quotes or points to a precise passage; no generic advice ("be clearer").
- Comments are ordered by severity, and blocking issues come before style.
- Any figure inconsistency reported shows both values and their locations.
- Rewritten passages keep the author's facts and do not add new claims.
- At least two specific strengths are named, so the author knows what to keep.

## Guardrails
- Review the document, not the person: no comments on the author's competence.
- Do not "correct" facts you cannot verify; ask a question instead ("source for the +12%?").
- Do not post comments or edit the doc without explicit confirmation.
- If the document contains personal or confidential data that seems unnecessary for its readers, flag it.

## Example
Input: « Relis mon doc de proposition pour ouvrir un corner location de matériel de ski au magasin. »
→ Verdict « 2/5 — la recommandation n'apparaît qu'en page 4 et le coût de l'atelier n'est pas chiffré ». Comment 🔴:
the revenue table uses N-1 winter but the cost table uses the current year; show both periods. Comment 🟠: "high
demand" is asserted without evidence; add the source (customer requests, ticket counts) or soften. Rewritten opening
puts the ask and the pilot scope in the first paragraph.
