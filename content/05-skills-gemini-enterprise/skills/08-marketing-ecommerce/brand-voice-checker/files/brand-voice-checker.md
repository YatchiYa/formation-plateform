---
name: brand-voice-checker
description: "Checks marketing or product copy against the brand and tone guidelines found in Drive or Confluence, never invented ones: scores each guideline rule pass or fail with the exact passage, flags risky claims (superlatives, unproven performance, green claims, health promises), readability and inclusive language, and returns a rewritten version with changes explained. Use whenever someone asks to proofread, review, polish or validate copy before publication, wants to know if a text 'sounds like us', or adapts copy for a product brand, even if they do not mention guidelines. Triggers - brand voice, tone of voice, check my copy, on-brand, proofread marketing text, ton de marque, charte éditoriale, relire mon texte, est-ce que ça sonne marque, valider un wording, plateforme de marque."
---

# Brand voice checker

Reviews copy against the brand's own written rules, shows each issue with the exact passage, and returns a rewrite
that keeps the meaning. The rules come from the guidelines document, not from the model's idea of the brand.

## When to use
- Before publishing a product page, an email, a social post, an ad or in-store signage.
- When copy comes from an agency, a freelancer, a translation or an AI draft.
- When the same message must fit a product brand voice (for example Quechua vs Domyos) and the guidelines differ.
- Not for: writing the copy from scratch (use `product-page-copy`, `social-media-post-pack` or
  `email-newsletter-writer`), a deep review of a long internal document (use `document-reviewer`), translating (use
  `translation-localizer`) or a legal check of sustainability claims (use `green-claim-checker`).

## Inputs
- The copy, with its channel and audience (required).
- Brand or product brand concerned (required if several guidelines exist).
- Guidelines document (required; search Drive and Confluence first; ask for the link if nothing is found).
- Market and language (optional, default: the language of the copy).

## Sources
1. **Drive and Confluence**: brand platform, tone of voice and editorial guidelines, glossary and forbidden words,
   legal mentions, product data sheets (to verify facts in the copy). Use the latest version and cite it.
2. **Slack and Chat**: brand or content team channels for recent rule updates, only if cited.
3. **Airtable or Jira**: the content request, to know the channel and constraints.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Find the guidelines.** If none are found, stop the brand scoring and say so; run only the generic checks
   (claims, clarity, inclusion, accessibility) and label them *generic, not brand rules*.
2. **Turn the guidelines into a rule list**: each rule as a testable statement with its citation (section or page),
   for example "<rule as written in the guide> (Guidelines §<n>)". Do not add rules the document does not
   contain.
3. **Check each rule** against the copy: pass / fail / not applicable, with the exact failing passage.
4. **Claims scan** (applies always):
   - Superlatives and comparatives ("the best", "the lightest", "n°1") → need cited proof.
   - Performance or safety promises ("100 % waterproof", "never get cold") → must match the data sheet wording.
   - Health promises ("burns fat", "heals back pain") → remove or route to legal.
   - Environmental wording ("eco-friendly", "green", "responsible") → `green-claim-checker`.
5. **Clarity**: sentence length (aim ≤ 20 words), active voice, jargon explained for beginners, one idea per
   sentence, a clear call to action.
6. **Inclusion and accessibility**: gender-inclusive wording per the guidelines' convention, no stereotypes about who
   practices a sport, plain language, link text that makes sense alone.
7. **Rewrite**: minimal edits that fix the fails; keep facts, length and structure. Explain each change in one line.

## Output format
```markdown
**Brand check — <brand> · <channel> · guidelines: <link, version/date>**
**Verdict:** <ready / minor edits / rework> · <N> fails out of <N> rules

### Rule check
| Rule (source §) | Status | Passage | Fix |
|-----------------|--------|---------|-----|

### Claims to prove or remove
| Passage | Risk | Needed proof / route |
|---------|------|----------------------|

### Clarity and inclusion
- …

### Rewritten copy
<full text, changes in **bold**>

### Changes explained
1. <change> — <rule or reason>
```

## Quality checks
- Every rule in the table cites a section or page of the guidelines document.
- No rule appears that the guidelines do not contain; generic checks are labeled as such.
- Every fail quotes the exact passage.
- The rewrite keeps every fact of the original and adds none.
- Every superlative, performance, health or green claim is listed in "Claims to prove or remove".

## Guardrails
- Never invent brand guidelines, brand values, taglines or forbidden-word lists. If no document is found, say so.
- Never add product facts or numbers in the rewrite; missing proof stays a flag, not an invention.
- Consumer law: misleading claims and unproven comparisons are flagged even if they are "on brand".
- This is an editorial check, not legal approval; legal or regulatory doubts go to the legal team.
