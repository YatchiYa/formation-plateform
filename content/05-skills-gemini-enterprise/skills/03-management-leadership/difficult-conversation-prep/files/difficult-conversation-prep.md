---
name: difficult-conversation-prep
description: "Prepares a hard workplace conversation (repeated performance gap, behavior issue, refused request, conflict between teammates, bad news such as a role change): objective and acceptable outcomes, verified facts vs stories, a 30-second opening line, likely reactions with responses, a plan B, a follow-up note and clear signals for when HR must be involved. Use whenever someone dreads a conversation, has to deliver bad news, needs to address a recurring problem or mediate a conflict, even if they only say 'I don't know how to tell him'. Triggers - difficult conversation, hard talk, deliver bad news, address performance issue, conflict between teammates, conversation difficile, recadrage, annoncer une mauvaise nouvelle, entretien de recadrage, gérer un conflit, je ne sais pas comment lui dire."
---

# Difficult conversation prep

Helps a manager or teammate walk into a hard conversation with a clear objective, facts instead of stories, and a
calm script — and recognize when the topic belongs to HR, not to a conversation.

## When to use
- A performance or behavior issue has repeated after informal feedback.
- Bad news must be delivered: a refused promotion, a schedule or role change, a project stopped.
- Two teammates are in conflict and the manager must mediate.
- The user must push back on a manager, a peer or a partner.
- Not for: a one-off feedback message (use `feedback-sbi-writer`), a routine 1:1 (use `one-on-one-prep`), formal
  review text (use `performance-review-writer`), or answering what the HR policy says (use `hr-policy-qa`).

## Inputs
- Who, relationship and the topic in the user's words (required).
- What has already happened: previous feedback, dates, agreements (optional, default: search notes and threads).
- What the user wants at the end of the conversation (optional, default: derived in step 1).
- Constraints: decisions already taken by others, deadlines, local HR process (optional).

## Sources
1. **Drive**: 1:1 notes, previous feedback, goals or role description of the person, and the team's documented
   expectations (schedules, standards) — to anchor the expectation in something written.
2. **Gmail, Chat and Slack**: the exchanges the user points to, for dated facts and exact wording.
3. **Jira, GitHub, Calendar**: factual records (missed due dates, review history, meeting attendance) when the topic
   is about work output.
4. **Confluence and Drive**: the official HR process for performance, conduct or conflict, if it exists — cite it,
   never paraphrase a policy you have not found.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Triage first.** If the topic involves harassment, discrimination, violence, a safety incident, health,
   suspected fraud, or a possible disciplinary sanction, say so at the top: the user must contact HR before any
   conversation, because formal procedures and legal deadlines may apply. Still help with what can be said
   neutrally, but do not script a disciplinary meeting.
2. **Objective**: write one sentence of the form "At the end, we have a shared understanding of <X> and an
   agreement on <Y>". Then list best / acceptable / walk-away outcomes.
3. **Facts vs stories** (ladder of inference): sort every element into dated observable facts, the user's
   interpretations, and unknowns. Interpretations become questions. Keep 2–3 strongest facts only.
4. Map the **three conversations** (Stone, Patton & Heen): *what happened* (facts, both sides' views), *feelings*
   (what each side may feel), *identity* (what this threatens for each: competence, fairness, belonging). This
   predicts the reactions.
5. Write the **opening** (≤ 30 seconds): purpose, one fact, the impact, then an open question. No sandwich, no
   small talk that hides the topic. Example: « Je veux qu'on parle des ouvertures du rayon. Mardi et jeudi, le
   rayon était prêt à 10h15 au lieu de 9h45 ; les premiers clients n'avaient pas de conseiller. Comment tu vois
   la situation ? »
6. Prepare **likely reactions** — denial, blame shifting, tears or anger, silence, counter-attack, quick agreement
   with no commitment — with one calm response each (acknowledge, return to the fact, ask a question; offer a pause
   if emotions run high).
7. Close on a **concrete agreement**: what changes, from when, how progress is checked, support offered, next date.
8. Draft the **follow-up note** (factual summary of what was agreed) to send after the talk if appropriate.

## Output format
```markdown
**Conversation with <Name/role> · topic: <topic>**
<⚠️ HR first: <reason> — only if triage triggered>

### Objective
<one sentence> · Best: … · Acceptable: … · Walk-away: …

### Facts I will use
1. <dated fact> (source: …)
2. …
_Interpretations turned into questions:_ …

### What this means for them (and me)
| | Them | Me |
|-|------|----|
| Feelings | … | … |
| Identity at stake | … | … |

### Opening (≤ 30 s)
"<script>"

### Likely reactions
| If they… | I say… |
|----------|--------|

### Closing agreement
- Change: … · From: … · Check-in: <date> · Support I offer: …

### Follow-up note (draft)
<≤ 100 words>

### Logistics
- Where / when / duration: <private place, not Friday evening, 30–45 min>
```

## Quality checks
- The opening names the topic within the first sentence and contains at least one dated fact.
- Every fact has a date and a source or is marked "from your account".
- No labels about personality or intent in any script line.
- Each likely reaction has a response that ends with a question or a concrete next step.
- The HR triage line is present whenever a step 1 trigger appears in the inputs.

## Guardrails
- Not HR or legal advice. Formal warnings, sanctions, dismissals and investigations follow local law and the
  company process: route to HR, and do not suggest wording for sanctions.
- Never use or infer health, pregnancy, family, origin, religion, union activity or other protected characteristics
  as part of the reasoning; if the user mentions them, flag that they must stay out of the conversation and talk to
  HR.
- Do not record, profile or keep a "case file" on the person; produce only what the conversation needs.
- Do not send the follow-up note; it is a draft for the user to adapt after the real conversation.
