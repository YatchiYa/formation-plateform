---
name: prompt-improver
description: "Rewrites a user's prompt for Gemini Enterprise into a precise, reusable instruction: role, goal, context, which connected sources to search (Drive, Gmail, Calendar, Jira, Confluence, Slack, Databricks, Tableau…), constraints, output format and quality bar, with a diagnosis of what was missing and a short and a full version. Use whenever someone gets vague, generic or wrong answers from Gemini, wants a better prompt, or pastes a prompt and asks to improve it, even if they only say 'the AI doesn't understand me'. Triggers - improve my prompt, better prompt, rewrite this prompt, prompt engineering, why is the answer bad, optimize my request, améliore mon prompt, réécris mon prompt, meilleur prompt, l'IA ne me comprend pas, comment formuler ma demande, optimiser ma requête."
---

# Prompt improver

Shows the user why their prompt underperformed and gives them a better version they can reuse, so Gemini answers
from the right sources in the right format.

## When to use
- A prompt returns generic, too long, invented or off-target answers.
- The user is about to run an important request (analysis, document, email) and wants it right first time.
- A team shares prompts and wants a cleaner, reusable version.
- The user is learning how to write prompts and wants feedback.
- Not for: turning a recurring prompt into a permanent skill (use `skill-builder`), finding where AI can help a team
  (use `ai-use-case-finder`), or checking whether an AI use case is risky (use `ai-use-case-risk-screen`).

## Inputs
- The original prompt (required).
- The answer received and what was wrong with it (optional, default: diagnose from the prompt alone).
- The intended use: one-off or reusable template (optional, default: reusable, with [placeholders]).

## Sources
1. **Drive / Confluence**: documents or templates the prompt should point to (exact titles make retrieval reliable),
   and any team prompt library.
2. **Gmail / Calendar / Chat / Slack / Jira / GitHub / Databricks / Tableau**: only to check which source actually
   holds the data the prompt needs, so the improved prompt names it.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Diagnose** with the 7-part checklist, scoring each ✅ present / ⚠️ vague / ❌ missing:
   - **Goal**: the deliverable and its use ("to decide…", "to send to…").
   - **Context**: who the user is, the situation, what is already known.
   - **Sources**: where to look (named connector, doc title, Jira project, date range) and what to ignore.
   - **Audience & tone**: who reads the output.
   - **Format**: structure, length, table columns, language.
   - **Constraints**: must/must not (cite sources, no invented figures, period, scope, confidentiality).
   - **Quality bar**: an example, a definition of done, or "ask me if X is missing".
2. **Identify the failure mode** behind the bad answer: missing source scoping (generic web-like answer), no format
   (wall of text), ambiguous term (e.g. "sales" = revenue or units? "last month" = calendar or rolling?), several
   tasks in one prompt, or no permission to ask questions.
3. **Rewrite** with this order: Role (optional, one line) → Goal → Context → Sources → Steps (only if the method
   matters) → Output format → Constraints. Use explicit nouns, numbers and dates; replace "analyze" by what to
   compute or compare; turn multi-task prompts into a short chain (step 1 then step 2).
4. **Add reuse placeholders** in brackets for anything that changes each time: [store], [period], [Jira project].
5. **Produce two versions**: a short one (≤ 60 words, for daily use) and a full one (for important or reusable use).
6. **Explain the 3 biggest changes** in one line each, so the user learns the pattern.
7. If the prompt will be reused weekly or by a team, suggest turning it into a skill with `skill-builder`.

## Output format
```markdown
### Diagnosis
| Part | Status | Note |
|------|--------|------|
| Goal | ⚠️ | "a summary" — for whom, to do what? |
| Sources | ❌ | … |
_Likely cause of the bad answer: <one line>_

### Improved prompt — short
> <≤ 60 words>

### Improved prompt — full
> **Goal:** …
> **Context:** …
> **Sources:** Search <connector/doc/project> for <period>. Ignore …
> **Output:** <structure, length, language>
> **Constraints:** Cite a source for every figure. If <X> is missing, ask me before answering.

### What changed
1. … 2. … 3. …
```

## Quality checks
- The improved prompt names at least one concrete source or explicitly says to use only the given text.
- The output format is specified (structure and length) and the language is stated.
- Every ambiguous term from the original is defined or replaced.
- The short version is ≤ 60 words and still contains goal, source and format.
- The rewrite keeps the user's intent; nothing in scope was added or dropped silently.

## Guardrails
- Never add instructions that bypass security, access rights or company policy (e.g. "ignore restrictions", "search
  colleagues' private mailboxes").
- Remove personal or sensitive data from the prompt if the task does not need it; suggest placeholders instead.
- Do not run the improved prompt automatically on actions (send, post, create); it only reads and drafts unless the
  user confirms.
- Do not promise the prompt guarantees accuracy; recommend checking cited sources.

## Example
Original: « Fais-moi un résumé des ventes. »
→ Diagnosis: goal ⚠️, sources ❌, period ❌, format ❌, ambiguous "ventes" (revenue or units?). Short version: « Résume
le chiffre d'affaires de [magasin] sur [semaine N] vs N-1 et vs objectif, à partir de [tableau Tableau / table
Databricks]. Format : 5 puces max, chaque chiffre avec sa source. Si une donnée manque, dis-le. »
