---
name: team-health-check
description: "Designs a short team pulse survey (8-12 items on psychological safety, clarity, workload, dependability, meaning, impact, recognition, growth) as a Google Form outline, then analyzes the answers with strict anonymity (no result for groups under 5), favorability scores, trend vs last pulse, comment themes and 2-3 actions to co-build with the team. Use whenever a manager wants to take the team's temperature, run a pulse, check morale or wellbeing, or has the raw answers of a pulse they ran with their own team to read, even if they say 'how is my team doing'. Triggers - team health check, pulse survey, team morale, team temperature, psychological safety, analyze pulse results, baromètre d'équipe, météo d'équipe, prendre la température de l'équipe, sondage d'équipe, moral de l'équipe, climat d'équipe."
---

# Team health check

Helps a manager ask the team the right few questions and read the answers honestly, without breaking anyone's
anonymity, then turn them into actions the team chooses.

## When to use
- A manager wants a quick, recurring pulse (monthly or quarterly) for one team.
- After a change (reorganization, new manager, peak season), to see how the team is doing.
- Pulse results (Google Forms export, sheet) need analysis and an action plan.
- Not for: company-wide engagement survey results with many teams and drivers (use `engagement-survey-analyzer`),
  running a retrospective on a period's work (use `team-retrospective`), or exit feedback (use
  `exit-interview-synthesizer`).

## Inputs
- Mode: design a pulse, or analyze results (required; infer from what the user gives).
- Team size and context: store, warehouse, HQ, tech (required for design).
- Results file or link and the previous pulse if any (required for analyze).
- Topics of concern (optional, default: the standard 8 dimensions below).

## Sources
1. **Drive**: the results sheet or Forms export, previous pulses for trend, any internal survey guidelines or
   company engagement survey item wording (reuse internal items if found, for comparability, and cite them).
2. **Confluence**: the company's rules for surveys and anonymity, if documented.
3. **Calendar and Jira**: only for context of the period (peak days, launches, incidents) — never to link answers to
   people.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
**Design**
1. Pick 8–12 items on a 5-point agreement scale, at least one per dimension (inspired by Google's Project Aristotle
   and Edmondson's psychological safety work), written for the team's context:
   - Psychological safety: "If I make a mistake in this team, it is not held against me."
   - Dependability: "I can count on my teammates to do what they say."
   - Clarity: "I know what is expected of me this month."
   - Workload: "My workload is manageable most weeks."
   - Meaning: "My work here matters to me."
   - Impact: "I see how my work helps our customers or the business."
   - Recognition: "In the last month I received recognition for good work."
   - Growth: "I am learning things that help me grow."
2. Add 2 open questions: "What should we keep doing?" and "What one thing would make your work better?"
3. Anonymity design: no name, no email collection, no demographic or role question in a team under 15 people;
   minimum 5 respondents to show any result; announce this in the intro text.
4. Draft the invitation message (purpose, anonymity, 3 minutes, what happens after) and the Forms outline.

**Analyze**
5. Check the **anonymity threshold**: if fewer than 5 responses (for the team or any sub-group), show no result for
   it and say why. Never split by sub-group below 5.
6. Compute per item: **favorability** = % of 4–5 answers, **unfavorable** = % of 1–2, and the response rate. Flag
   items with favorable < 60 % or unfavorable ≥ 20 % as attention points; flag a change ≥ 10 points vs last pulse
   as a meaningful move (for small teams, one person = up to 20 points: say so).
7. Theme the comments (affinity grouping), count each theme, quote short paraphrases only, and remove any detail
   that could identify the author (names, specific events, writing style tics).
8. Choose the 2–3 **priority topics** = lowest favorability × importance to the team's goals. For each, prepare a
   question to discuss with the team, not a ready-made solution — actions are co-built in a team meeting.

## Output format
```markdown
## Pulse design — <Team> (<n> people)
Intro: <text, mentions anonymity threshold of 5>
| # | Dimension | Item (1–5 agree) |
|---|-----------|------------------|
Open questions: …

## Pulse results — <Team>, <date> · <n> responses / <N> (<rate> %)
| Item | Favorable | Unfavorable | Δ vs last | Flag |
|------|-----------|-------------|-----------|------|

### What the team says (themes)
| Theme | Comments | Paraphrase |
|-------|----------|------------|

### Priorities to discuss with the team
1. <topic> — question to the team: "…"

### Next steps
- Share back on <date> · co-build actions · next pulse <date>
```

## Quality checks
- No result is shown for any group under 5 respondents.
- Favorability figures match the counts (recomputable) and the response rate is shown.
- No comment is quoted verbatim if it contains a name, a dated event or a detail that could identify its author.
- Each priority comes from data in the table or themes, and ends in a question for the team.
- Small-team volatility is mentioned when n < 10.

## Guardrails
- Never try to infer who wrote a comment or answered an item, even if asked; refuse and explain why.
- Do not ask health, family, origin or other sensitive questions in the pulse; wellbeing is asked only through
  workload and support items.
- If comments mention harassment, discrimination or safety risks, do not summarize details in the report: advise the
  manager to contact HR and use the official reporting channels.
- Results are for team improvement, never for evaluating individuals or the manager's rating unless the official HR
  process says so.
- Do not create or send the Form without confirmation.
