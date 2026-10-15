---
name: long-document-digest
description: "Digests a long document (report, study, strategy deck, standard, tender file, regulation, thesis, meeting transcript) into a navigable brief: a one-paragraph bottom line, a structure map with page or section references, key points per section, every number and date worth keeping with its location, defined terms, open questions and what it means for the reader's role. Use whenever someone shares a long PDF, Doc, Slides deck or Confluence page and asks for a summary, the key points or what they need to know, even if they say 'I don't have time to read this'. Triggers - summarize this document, key points, digest, TL;DR, what do I need to know from this report, résume ce document, points clés, synthèse du rapport, je n'ai pas le temps de lire, l'essentiel de ce doc, fiche de lecture."
---

# Long document digest

Turns a long document into a brief that a teammate can read in five minutes and trust, with references back to the
exact pages for anything they need to verify.

## When to use
- A report, study, strategy document or standard of 20+ pages lands before a meeting.
- A tender file or regulation must be understood before deciding whether to act.
- A long meeting transcript or workshop output needs to be made usable.
- Not for: a one-page executive summary for others to read (use `executive-summary-writer`), comparing two versions
  (use `document-comparison`), contract terms and risks (use `contract-summary`), or a full tender response (use
  `tender-response-builder`).

## Inputs
- The document: Drive link, attachment, Confluence page or pasted text (required).
- Reader's role and purpose (optional, default: general reader; e.g. "store manager", "deciding whether to bid").
- Depth (optional, default: standard; "short" = bottom line + 5 points; "deep" = every section).

## Sources
1. **Drive**: the document itself, its comments, owner and modified date; Meet transcripts if the document is one.
2. **Confluence**: the page and its child pages or attachments if the document spans several.
3. **Gmail and Chat or Slack**: the message the document came with, for context on why it was shared.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify**: title, author or issuer, date, version, length, type (report, standard, deck, transcript…).
2. **Map the structure**: sections and their page or slide ranges; spot the executive summary, conclusions,
   annexes and tables.
3. **Read in order of value**: executive summary and conclusions, then each section's first and last paragraphs,
   then figures and tables, then the rest. Do not skip annexes holding numbers or requirements.
4. **Extract per section**: 1–3 key points in plain language, with the page or section reference.
5. **Numbers and dates**: list every figure, threshold, deadline and amount that matters, quoted exactly with
   unit, scope and location. Do not round or recompute unless labeled.
6. **Defined terms and acronyms**: list them with the document's own definitions.
7. **Critical reading**: claims without evidence, internal contradictions, outdated data (date of the underlying
   data), methodology limits; keep these separate from the summary.
8. **So what for the reader**: implications and actions for the stated role; open questions to ask the author.

## Output format
```markdown
**Bottom line:** <3–4 sentences: what the document says and what it means for <role>>
_<Title> · <author/issuer> · <date, version> · <N pages> · [link](…)_

### Structure map
| Section | Pages | What it covers |
|---------|-------|----------------|

### Key points
1. <point> (p. <n>)
2. …

### Numbers and dates to keep
| Figure / date | Exactly as stated | Scope | Location |
|---------------|-------------------|-------|----------|

### Terms and acronyms
- **<term>**: <definition from the document> (p. <n>)

### Critical reading
- <limit / contradiction / outdated data> (p. <n>)

### What it means for <role>
- <implication or action>

### Questions for the author
- <question>
```

## Quality checks
- Every key point and every number carries a page, slide or section reference.
- Numbers are quoted exactly as in the document, with unit and scope.
- The critical reading section is separate from the summary and contains no new facts.
- The bottom line is understandable without reading the rest.
- If parts could not be read (scanned pages, images, access), the answer lists them.

## Guardrails
- Summarize only documents the user can access; respect confidentiality labels and remind the user when a document
  is marked confidential or restricted before they forward the digest.
- No fabrication: if the document does not cover something the user asks, say so rather than filling with general
  knowledge.
- Keep personal data out of the digest (names in annexes, contact lists) unless needed for the purpose.
- Quote briefly; do not reproduce large copyrighted passages from external publications.

## Example
Input: "Digest this 80-page market study for a sport-universe leader, short version"
→ Bottom line in 4 sentences, structure map, 5 key points with page numbers, a numbers table quoting market sizes
and growth rates exactly as written with their scope and year of data, a critical-reading line noting the age of the
underlying survey data, and 3 implications for the sport universe.
