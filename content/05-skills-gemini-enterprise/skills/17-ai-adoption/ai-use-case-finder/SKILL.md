---
name: ai-use-case-finder
description: "Maps the recurring tasks of a role or team to concrete AI opportunities in Gemini Enterprise: task inventory with frequency and time spent, AI pattern per task (summarize, draft, search, analyze, classify), value and feasibility scores, which existing library skills already apply, data and connector needs, risk tier, and a prioritized 30-day adoption plan with quick wins. Use whenever a manager, team or champion asks where AI can help them, how to start with Gemini, which skills to use, or how to save time on repetitive work, even if they just ask 'what can Gemini do for my job'. Triggers - AI use cases, where can AI help, what can Gemini do for me, AI opportunities for my team, adoption plan, automate my tasks, cas d'usage IA, où l'IA peut nous aider, sur quelles tâches l'IA peut aider mon équipe, que peut faire Gemini pour moi, gagner du temps avec l'IA, plan d'adoption IA, automatiser mes tâches."
---

# AI use case finder

Helps a team see, task by task, where Gemini Enterprise saves time or improves quality today, which existing skills
to use, and where to be careful.

## When to use
- A team, store, department or role starts with Gemini Enterprise and wants to know where to begin.
- An AI champion prepares a workshop or an adoption plan for a team.
- A manager wants to free time from repetitive work (reporting, emails, meeting follow-ups, searches).
- Not for: writing the skill for a chosen use case (use `skill-builder`), improving a specific prompt (use
  `prompt-improver`), the regulatory screen of one use case (use `ai-use-case-risk-screen`), or finding one existing
  skill by name (use `skills-navigator`).

## Inputs
- Role or team, and context: store, warehouse/logistics, HQ function, tech, B2B sales (required).
- Their recurring tasks, or a job description (optional, default: inferred from sources, else a typical task list
  for the role labeled *assumed*; produce the full output with it and invite corrections at the end, do not stop to
  have the list validated first).
- Pain points or goals: time, quality, consistency, onboarding (optional).
- Connectors available in their tenant (optional, default: the ones that respond).

## Sources
1. **Drive / Confluence**: job descriptions, team procedures, recurring report templates, team rituals pages.
2. **Calendar**: recurring meetings (frequency and duration hint at reporting and preparation load).
3. **Gmail / Chat / Slack**: recurring message types the team sends or answers (requests, reminders, reports),
   counted by pattern, never read for personal content.
4. **Jira / GitHub**: recurring ticket types and workflows for tech or project teams.
5. **Databricks / Tableau**: recurring dashboards and data questions the team handles.
6. **Library catalog** (`skills-navigator`): the existing skills, to map each opportunity to a ready skill.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Inventory 10–20 recurring tasks** with: frequency (daily/weekly/monthly), estimated time per occurrence (from
   the user, or labeled *estimate*), inputs, output, and where the data lives.
2. **Tag the AI pattern** for each task: Search & answer · Summarize · Draft & rewrite · Analyze data · Classify &
   triage · Plan & structure · Translate. Tasks needing physical action, live judgment with customers or
   decisions about people are tagged "human-led, AI assists at most".
3. **Score value (1–5)**: hours saved per month (time × frequency × share automatable, ~30–60% for drafting or
   summarizing, assumed and labeled) plus quality or consistency gains and pain relief.
4. **Score feasibility (1–5)**: data reachable through a connected source (Drive, Gmail, Jira, Databricks…), output
   checkable by the user in < 5 minutes, low error cost, an existing skill covers it.
5. **Screen risk**: 🟢 low (internal drafting, summaries of own work) · 🟠 medium (customer-facing text, figures
   used in decisions; needs human check) · 🔴 high (recruitment, evaluation, promotion, termination, task allocation
   of people, personal data at scale; EU AI Act high-risk or GDPR heavy; route to `ai-use-case-risk-screen` and the
   DPO before any use).
6. **Prioritize on a 2×2**: Quick wins (value ≥ 3, feasibility ≥ 4, 🟢) · Big bets (value ≥ 4, feasibility < 4) ·
   Fill-ins · Avoid for now (🔴 or value ≤ 2).
7. **Map skills**: for each opportunity, name the library skill(s) that apply, or "new skill needed" with a one-line
   spec for `skill-builder`.
8. **Plan 30 days**: week 1 two quick wins with one pilot user each, week 2 share prompts and results, week 3
   extend to the team, week 4 measure (time saved self-reported, usage, quality feedback) and decide next.

## Output format
```markdown
# AI opportunities — <team/role>
_Context: <…> · Connectors available: <…> · Time figures: <from user | estimates>_

## Task map
| Task | Freq. | Time/occ. | AI pattern | Value 1–5 | Feas. 1–5 | Risk | Skill(s) |
|------|-------|-----------|------------|-----------|-----------|------|----------|

## Priorities
- **Quick wins:** <task → skill> …
- **Big bets:** …
- **Avoid for now:** <task — reason>

## Try it this week
1. <task> — prompt: "<ready-to-use prompt>" · uses `<skill>`
2. …

## 30-day plan
| Week | Action | Who | Success measure |
|------|--------|-----|-----------------|

## Watch-outs
- <data, privacy, quality checks needed>
```

## Quality checks
- Every skill named in the table exists in the library; unmatched needs say "new skill needed".
- Time and value figures are marked as user-provided or *estimate*, never presented as measured.
- At least two quick wins have a ready-to-use prompt the user can try today.
- Every 🔴 task is routed to the risk screen and excluded from quick wins.
- Each task has a data source that is actually connected, or the gap is stated.

## Guardrails
- Do not suggest AI that ranks, scores, selects or monitors individual teammates; such use cases are high-risk
  under the EU AI Act and need HR, legal and DPO review.
- Do not inspect the content of colleagues' messages to find tasks; use patterns, metadata the user can see, and
  the user's own description.
- No promises of headcount reduction or guaranteed savings; present time saved as estimates to validate in a pilot.
- Do not invent Company tools, policies or AI governance rules; search Drive/Confluence for the internal AI policy
  and cite it, or recommend the user checks it.
