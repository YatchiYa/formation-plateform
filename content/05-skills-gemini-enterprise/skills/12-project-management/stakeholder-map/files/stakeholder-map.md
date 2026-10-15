---
name: stakeholder-map
description: "Maps the stakeholders of a project or change on a power / interest grid, assesses current vs desired engagement level (unaware, resistant, neutral, supportive, leading), and builds an engagement plan per stakeholder: what they care about, key message, channel, frequency, owner and next touchpoint. Use whenever someone starts a project, prepares a change, struggles to get buy-in, or asks who to involve or inform, even if they only ask 'who should I talk to'. Triggers - stakeholder map, stakeholder analysis, power interest grid, engagement plan, who to involve, buy-in, cartographie des parties prenantes, analyse des parties prenantes, matrice pouvoir intérêt, qui impliquer, plan d'engagement, embarquer les équipes."
---

# Stakeholder map

Shows a project lead who matters, where each person stands today, where they need to be, and the concrete next move
to close that gap.

## When to use
- Project or change kick-off: identify everyone affected or able to influence the outcome.
- Buy-in is stalling, a key person resists or a decision keeps being reopened.
- Before a steering committee or a roll-out, to check nobody important is surprised.
- Not for: the communication calendar and messages of a change (use `change-communication-plan`), the charter roles
  (use `project-charter`), or preparing a single meeting with one stakeholder (use `meeting-prep`).

## Inputs
- Project or change, with its scope and goal (required).
- Known stakeholders (optional; the skill proposes more from sources).
- Sensitivities the user already knows (optional).

## Sources
1. **Drive and Confluence**: charter, org charts or team pages that are published internally, previous stakeholder
   maps, RACI, steering committee membership.
2. **Gmail, Chat and Slack**: who requested, challenged, approved or asked about the project; tone of their messages
   (quote facts, not interpretations).
3. **Calendar and Meet transcripts in Drive**: who attended project meetings, who declined, positions expressed.
4. **Jira**: teams that own dependent work (assignees, components), approvers in workflows.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify** stakeholders by category so none is missed: sponsor and decision makers; impacted users (e.g. store
   teammates, warehouse operators, customers); delivering teams (IT, logistics, suppliers); support functions
   (finance, legal, HR, data protection, works council or employee representatives where the change affects working
   conditions — check local rules); external (partners, clubs, authorities). Group individuals into a segment when
   they share interests (e.g. "store managers of region X").
2. **Score Power** (ability to affect the outcome: budget, decision rights, veto, expertise, network) and
   **Interest** (how much the outcome affects them or they care), each High / Low with a one-line evidence.
3. Place them on the **grid** and set the strategy:
   High power + high interest → **Manage closely** (co-design, regular 1:1); high power + low interest → **Keep
   satisfied** (short, decision-focused updates, no detail overload); low power + high interest → **Keep informed**
   (regular updates, feedback channel, often future champions); low / low → **Monitor**.
4. Assess **engagement** current (C) and desired (D) on the 5 levels: Unaware, Resistant, Neutral, Supportive,
   Leading. Base C on observable evidence; mark it *hypothesis* when it is not.
5. Prioritize the gaps: high power with C below D first, especially Resistant or Unaware.
6. For each priority stakeholder write: what they care about (their win, their fear), key message, the ask, channel
   (1:1, steering, Chat space, store visit, newsletter), frequency, owner on the project team, next touchpoint date.
7. Flag **risks**: a resistant high-power person, a missing voice (e.g. no store representative), conflicting
   interests between two stakeholders; suggest adding them to the RAID log.

## Output format
```markdown
# Stakeholder map — <Project> · <date>
**Key insight:** <one or two lines: the biggest engagement gap and the move that closes it>

## Power / interest grid
| | Low interest | High interest |
|---|---|---|
| **High power** | Keep satisfied: … | Manage closely: … |
| **Low power** | Monitor: … | Keep informed: … |

## Stakeholder register
| Stakeholder (role / segment) | Power | Interest | Current | Desired | Gap | Evidence |
|------------------------------|-------|----------|---------|---------|-----|----------|

## Engagement plan (priority stakeholders)
| Stakeholder | Cares about (win / fear) | Key message | Ask | Channel · frequency | Owner | Next touchpoint |
|-------------|--------------------------|-------------|-----|---------------------|-------|-----------------|

## Watch-outs
- <missing voice / conflict / resistant high-power stakeholder> → <action>
```

## Quality checks
- Every category in step 1 was considered; missing ones are stated ("no customer representative identified").
- Each power and interest rating and each current engagement level has evidence or is marked *hypothesis*.
- Every stakeholder with a gap (C below D) and high power has a plan row with an owner and a dated next touchpoint.
- Grid placement and strategy are consistent with the register.
- Segments are used for large groups; individuals are named only when they hold a role in the project.

## Guardrails
- Describe positions and interests at work, based on what people said or did; no personality judgments, no
  speculation about private life or motives, no profiling (GDPR).
- The map is sensitive: label it "internal — project team only" and suggest keeping engagement levels out of widely
  shared documents.
- Do not invent org charts or reporting lines; use published ones or ask.
- Draft only: do not send messages or book meetings with stakeholders without explicit confirmation.
