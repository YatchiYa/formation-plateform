---
title: "Le standard d'écriture d'un skill"
description: "Les règles que suit chaque skill de la bibliothèque."
tags: ["skills", "gemini-enterprise"]
authors: ["Youcef"]
---

Every skill in this library follows these rules. `scripts/validate.py` enforces the mechanical ones;
the rest are checked during review.

## 1. Format (Agent Skills spec + Gemini Enterprise)

- One folder per skill: `skills/<NN-domain>/<skill-name>/SKILL.md`. **Single file only.** Gemini Enterprise
  documents that skills "work best with Canvas when a skill has only one `SKILL.md` file", and single files can be
  uploaded as `.md` directly.
- Frontmatter has exactly two keys: `name` and `description`. No other keys. This is the safest subset for every
  Agent Skills client.
- `name`: 1–64 chars, `a-z 0-9 -`, no leading, trailing or double hyphen, **equal to the folder name**, and unique
  across the library.
- `description`: ≤ 1024 chars, one paragraph, **always wrapped in double quotes**, with no double quotes inside
  (use single quotes or « » instead). It says **what** the skill produces, then **when** to use it ("Use when …"). It ends with
  trigger phrases in English **and French** (most Company users write in French). It is slightly "pushy"
  ("Use whenever …, even if the user doesn't say X"), because models under-trigger skills.
- The body stays under 250 lines (spec maximum 500) and reads as ~1,500–3,500 tokens.

## 2. Body structure (in this order, these exact H2 titles)

```
# <Human title>
<One sentence: the outcome this skill delivers, for whom.>

## When to use
- 3–5 bullets of situations. Then one "Not for:" line that routes to sibling skills by name.

## Inputs
- What the skill needs. Mark each item (required) or (optional, default: …).
- Rule: if a required input is missing and cannot be found in connected sources, ask ONE grouped question.
  Otherwise proceed and state the assumptions in one line at the top of the answer.

## Sources
- Which connected sources to use, in priority order, and what to look for in each one: Gmail, Calendar, Drive,
  Chat, Jira, Confluence, Slack, GitHub, Airtable, Tableau, Databricks (SQL / Genie-style MCP).
- Always end with: "If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples."
  (Found in evals: without that rule, models announced "I'll check your apps" and stopped, or filled gaps with invented examples.)

## Workflow
1. Numbered, concrete steps. Every step is something the model can actually do in Gemini Enterprise chat.
   Include the method (framework, scoring rule, query pattern), not just "analyze".

## Output format
- An exact Markdown template inside a fenced block, with the real section names, tables and lengths.

## Quality checks
- 4–7 checks the model runs on its own draft before answering. Each one can be tested, e.g. "every number has a source
  link or is marked as an estimate".

## Guardrails
- The skill-specific risks (privacy, legal, HR fairness, financial claims, irreversible actions).
```

You may add a short `## Example` (input → output excerpt) or a `## Reference` section (frameworks, checklists)
when it makes the skill better. Keep them tight.

## 3. Library-wide rules that every skill must follow

1. **Never invent facts.** Names, numbers, dates, prices, policies, quotes and links come from the user or from a
   connected source, and each one is cited (link or "source: <doc/ticket/thread>"). Anything else is labeled
   *assumption* or *estimate*.
2. **Draft, don't act.** Sending emails, posting messages, creating or updating Jira issues, booking meetings and
   editing records happen only after the user explicitly confirms the final draft.
3. **Answer in the user's language** (French if they write French). Keep proper nouns and product names as written.
4. **Privacy by default (GDPR).** Use only the personal data the task needs. Never put health, union, salary or
   disciplinary details about named people into output unless the user's role and request clearly require it. No
   profiling of individuals.
5. **Company context, no fabrication.** Company is a sports retailer and designer of its own brands, and its
   purpose is "Move people through the wonders of sport". Employees are "teammates" (coéquipiers). Do not invent
   internal tool names, policies, org charts or figures. Look for them in Drive and Confluence, or ask.
6. **Concise first.** Lead with the answer or the decision. Put details after it. No filler.

## 4. HR and people skills (extra rules)

AI used for recruitment, promotion, termination or task allocation is **high-risk under the EU AI Act (Annex III)**.
People skills therefore:
- support human decisions and never rank, score or reject candidates or employees on their own;
- base every judgment on job-related evidence, and never on age, gender, origin, health, family status or other
  protected characteristics (also not on proxies such as gaps, names or photos);
- tell the user that a human makes the final decision.
