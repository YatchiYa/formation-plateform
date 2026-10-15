---
name: meeting-agenda-builder
description: "Builds a meeting agenda that produces results: purpose and target outcomes, items typed inform, discuss or decide with an owner and a timebox, pre-reads, roles, the right attendee list, and the invite text ready to paste in Google Calendar. Also tests whether the meeting should be an email. Use whenever the user organizes a meeting, a recurring ritual, a kick-off or a review and needs an agenda or invite, even if they only say 'set up a meeting about X'. Triggers - meeting agenda, build an agenda, prepare the invite, kick-off agenda, organize a meeting, ordre du jour, construire l'ordre du jour, préparer une invitation, organiser une réunion, agenda de réunion, trame de réunion."
---

# Meeting agenda builder

Designs a meeting around the outcomes it must produce, then writes the agenda and the invite so attendees arrive
prepared and leave with decisions.

## When to use
- The user organizes a meeting and needs an agenda and invite text.
- A recurring meeting (weekly team, store managers' call, project sync) has drifted and needs a new structure.
- A kick-off or review where several teams must decide something.
- Not for: preparing as an attendee (use `meeting-prep`), a half-day or longer workshop with activities (use
  `workshop-designer`), a steering committee deck (use `steering-committee-pack`), or a retro (use
  `team-retrospective`).

## Inputs
- Topic and what must come out of the meeting (required).
- Duration and date (optional, default: the shortest format that fits the items; 25 or 50 minutes).
- Attendees (optional, default: proposed from the topic's threads and docs, then confirmed by the user).
- Format (optional, default: Google Meet; hybrid if attendees span sites).

## Sources
1. **Drive and Confluence**: the docs on the topic (to pick pre-reads), notes of previous occurrences and their open
   actions, team rituals or meeting rules if the team has written any.
2. **Gmail, Chat and Slack**: recent threads on the topic, to find the open questions and the people involved.
3. **Jira**: open issues or epics to review, with status.
4. **Google Calendar**: attendees' availability for the proposed slot and the previous occurrence's invite.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Email test.** If every item is *inform* and no discussion is needed, recommend an email or a Chat post instead
   and draft it. Otherwise continue.
2. **Purpose and outcomes.** One purpose sentence, then 1–3 outcomes written as artifacts ("decision on…",
   "list of…", "owner and date for…").
3. **Items.** For each item: type (**Inform** / **Discuss** / **Decide**), owner, question to answer, timebox.
   Drop items without an owner or an expected outcome. Turn pure updates into pre-reads.
4. **Order.** Quick check-in (≤ 5% of time) → the most important decision early, while energy is high → discussion
   items → recap of decisions and actions (≥ 5 minutes, never cut) → buffer (10% of the duration, its own row). No
   "AOB" / « Questions diverses » item: late topics go to the recap as parking-lot items.
5. **Timeboxes.** Decide items need at least 10 minutes; discuss items 10–20 minutes. Total of timeboxes plus
   buffer equals the duration. A 30- or 60-minute request (« 1h ») is planned as 25 or 50 minutes, said in one line
   at the top; if that leaves no room for every Decide/Discuss item at its minimum, drop or merge items, never go
   below the minimums.
6. **Decision rule.** For each Decide item, name the decider and the method (decider after consultation, consent,
   vote). Unknown → flag for the user.
7. **Roles.** Facilitator, timekeeper, note-taker (who also records actions), decider(s).
8. **Attendees.** Required = owns an item, decides, or has knowledge needed for a decision. Everyone else is
   optional and gets the notes. Flag only when required attendees, organizer included, are 9 or more.
9. **Pre-reads.** Max 3, each with why it matters and reading time; ask that they are sent ≥ 24 h before.
10. Write the invite text: purpose, outcomes, agenda, pre-reads, roles, "come prepared to…", in the user's language.

## Output format
```markdown
**<Meeting title> · <duration> min · <format> · <N> required / <N> optional**
**Purpose:** <one sentence>
**Outcomes:** 1. <artifact> 2. <artifact>

| Time | Item | Type | Owner | Question to answer | Decider / method |
|------|------|------|-------|--------------------|------------------|
| 0:00–0:03 | Check-in | — | <facilitator> | — | — |
| 0:03–0:18 | <item> | Decide | <name> | <question> | <name> after consultation |
| … | Recap: decisions & actions | — | <note-taker> | — | — |
| … | Buffer (10%) | — | — | — | — |

**Roles:** facilitator <name> · timekeeper <name> · note-taker <name>
**Pre-reads (send by <date>):** <doc> — <why> — <min> min ([link](…))
**Attendees:** required <names> · optional <names> — ⚠️ <flags>

### Invite text (ready to paste)
<Title>
<Purpose + outcomes>
<Agenda lines>
<Pre-reads and "come prepared to…">
```

## Quality checks
- Every item has a type, an owner and a timebox, and every Decide item has a decider and a method.
- Timeboxes plus buffer add up exactly to the duration (25/50 for a 30/60 request), the buffer row is ~10%, the
  recap slot is at least 5 minutes, and every Decide/Discuss item is at least 10 minutes.
- Each outcome is an artifact that can be checked at the end of the meeting.
- Every required attendee owns, decides or contributes to at least one item.
- No pre-read is longer than about 15 minutes of reading without a pointer to the section that matters.

## Guardrails
- Do not create or send the invite, or book rooms, until the user confirms the final version.
- Do not assign roles or decision rights to people as fact; propose them and mark "to confirm" unless the user or a
  source states them.
- Keep confidential items (HR, salary, restructuring) out of the invite text; suggest a separate restricted meeting.
