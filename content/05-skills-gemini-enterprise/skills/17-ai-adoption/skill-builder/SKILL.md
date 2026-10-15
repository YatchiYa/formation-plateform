---
name: skill-builder
description: "Interviews the user about a recurring task and writes a new, ready-to-upload SKILL.md for Gemini Enterprise that follows this library's standard: valid frontmatter, a pushy description with English and French triggers, the seven required sections, concrete method, sources per connector, an exact output template, testable quality checks and guardrails, plus test prompts. Use whenever someone wants to create, turn a prompt into, or improve a skill or agent instruction, or says they keep giving Gemini the same instructions, even if they don't know the word 'skill'. Triggers - create a skill, write a SKILL.md, build an agent skill, turn this prompt into a skill, improve my skill, new skill for my team, créer une skill, écrire un skill, transformer mon prompt en skill, nouvelle compétence pour Gemini, améliorer ma skill, automatiser ma consigne."
---

# Skill builder

Turns a teammate's know-how on a recurring task into a SKILL.md that Gemini Enterprise triggers at the right time
and that produces the same quality output every time.

## When to use
- The user repeats the same long instructions to Gemini for a task (weekly report, reply template, analysis).
- A team wants to share its method (checklist, scoring rule, format) as a reusable skill.
- An existing SKILL.md under-triggers, over-triggers or gives uneven results and must be improved.
- Not for: improving a one-off prompt (use `prompt-improver`), finding which tasks are worth a skill (use
  `ai-use-case-finder`), or finding an existing skill in the library (use `skills-navigator`).

## Inputs
- The task: what it produces, for whom, how often (required).
- An example of a good output, or the instructions the user currently types (optional but strongly recommended).
- Connectors the task needs and where the data lives (optional, default: asked in the interview).
- An existing SKILL.md to improve (optional).

## Sources
1. **Drive / Confluence**: the user's existing prompts, templates, checklists, examples of good outputs, and the
   team's procedure for this task. These become the skill's method and output template.
2. **Gmail / Chat / Slack**: a sample of past outputs (reports, replies) to infer the real format, if the user
   points to them.
3. **Drive / Confluence / GitHub**: the library's own skills, to check that no existing skill already covers the task
   and to route "Not for:" to real sibling names.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Check for overlap.** If an existing skill covers ≥ 70% of the task, propose extending or using it instead.
2. **Interview in one grouped message** (max 7 questions; skip what the sources answer):
   what is produced and for whom · what triggers it (and 3 ways users would ask, in English and French) · which
   sources and fields · the method an expert applies (rules, thresholds, scoring, checklist) · the exact output
   shape · what a bad output looks like · risks (personal data, legal, irreversible actions).
3. **Name it**: lowercase, digits and hyphens only, ≤ 64 characters, verb-object or object-role
   ("supplier-delay-tracker"), unique in the library, identical to the folder name.
4. **Write the description** (one paragraph, ≤ 1024 characters, target 400–900, wrapped in double quotes, no double
   quote inside, use single quotes or « »): what it produces → "Use whenever …, even if the user doesn't say …"
   → "Triggers - " with 5–8 English and 5–8 French phrases users really type. Pushy wording fixes under-triggering.
5. **Write the body** with these H2 sections in this exact order: When to use (3–5 bullets + a "Not for:" line
   routing to sibling skills) · Inputs (each marked required or optional with default; rule: one grouped question if
   a required input is missing, else state assumptions in one line) · Sources (priority order, what to query in each
   connector, ending with the line « If a source is not connected or returns nothing, say so in one line and continue
   with what you have. ») · Workflow (numbered steps with the method: formulas, thresholds, frameworks, query
   patterns) · Output format (exact Markdown template in a fenced block) · Quality checks (4–7 testable checks) ·
   Guardrails (task-specific risks). Optional: Example, Reference.
6. **Embed the library rules**: never invent facts (cite or label *assumption*), draft don't act (send, post, create
   or update only after explicit confirmation), answer in the user's language, GDPR minimization, no invented
   Company tools, policies, org or figures. For HR or people tasks add: AI supports human decisions, never ranks or
   rejects people, uses only job-related evidence, and states that a human decides (EU AI Act Annex III).
7. **Tighten**: body ≤ 250 lines (target 90–170), one file only, no placeholder words, no vague steps such as
   "analyze the data" without saying how.
8. **Write 3 test prompts**: one obvious trigger, one indirect trigger (in French), one near-miss that should route
   to another skill. Explain how to upload (the SKILL.md as a .md file, or a .zip with SKILL.md at
   its root) and to test it in a new chat with no agent selected (skills and agents cannot be combined in one prompt).

## Output format
The SKILL.md skeleton is indented two spaces below for display only. Deliver it unindented, inside a four-backtick
fence (````markdown), so the skill's own ``` output-format block does not close it.
````markdown
**Skill:** <name> · <one-line purpose> · overlap check: <none | similar to …>

```markdown
  ---
  name: <name>
  description: "<what>. Use whenever <…>, even if <…>. Triggers - <EN phrases>, <FR phrases>."
  ---

  # <Human title>
  <One sentence: outcome, for whom.>

  ## When to use
  - …
  - Not for: … (use <sibling>)

  ## Inputs
  ## Sources
  ## Workflow
  ## Output format
  ## Quality checks
  ## Guardrails
```

### Test prompts
1. Direct: …  2. Indirect (FR): …  3. Near-miss → should use <other skill>: …

### Self-check
- [ ] name = folder, valid characters  - [ ] description ≤ 1024 chars, quoted, EN+FR triggers
- [ ] 7 sections in order  - [ ] Sources fallback line  - [ ] body ≤ 250 lines
````

## Quality checks
- The frontmatter has exactly two keys, `name` and `description`, and the name matches the proposed folder.
- The description is a single double-quoted line with no inner double quote, ≤ 1024 characters, with "Use when" or
  "Use whenever" and a "Triggers - " list in English and French.
- The seven H2 sections are present in the required order, and Sources ends with the fallback line.
- Every Workflow step names a concrete method (rule, threshold, formula, checklist), not just a verb.
- The output template is exact (real headings, tables, lengths), and every quality check is testable.
- Sibling skills in "Not for:" exist in the library; none are invented.

## Guardrails
- Do not encode internal facts (policies, thresholds, tool names, org) the user did not provide or a source did
  not show; leave a clearly marked placeholder to fill.
- A skill that sends, posts, books or edits records must include an explicit confirmation step.
- If the task involves recruitment, evaluation, promotion or termination, add the HR rules above and warn the user
  that the use case is high-risk under the EU AI Act and may need a compliance review (see `ai-use-case-risk-screen`).
- Do not upload or publish the skill; the user (or an admin) uploads it after review.
