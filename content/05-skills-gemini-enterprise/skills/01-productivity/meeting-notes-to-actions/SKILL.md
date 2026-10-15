---
name: meeting-notes-to-actions
description: "Turns meeting notes or a Google Meet transcript from Drive into a clean record: decisions with who decided, actions with one owner and a date, open questions and parking lot, plus a recap email ready to send and optional Jira issue drafts. Use whenever a meeting just ended, the user has raw notes or a transcript, or asks who does what after a meeting, even if they only paste the notes or say 'the transcript is in Drive'. Triggers - meeting notes to actions, action items, meeting recap, follow-up email after meeting, transcript summary, minutes, compte rendu de réunion, CR de réunion, relevé de décisions, actions de la réunion, mail de récap, transcription Meet."
---

# Meeting notes to actions

Converts what was said into what was decided and what will be done, by whom and by when, and drafts the recap the
organizer sends within the hour.

## When to use
- Right after a meeting, from raw notes, a shared doc or a Meet transcript saved in Drive.
- The user has to send minutes or a recap and wants it fast.
- Actions from a meeting need to become Jira issues.
- Not for: preparing the meeting (use `meeting-prep` or `meeting-agenda-builder`), summarizing an email or chat
  thread (use `thread-catchup`), or turning decisions into a durable wiki page (use `knowledge-capture-page`).

## Inputs
- The notes or transcript (required): pasted text, a Drive doc, or the meeting name to look up in Calendar and Drive.
  If Drive is not connected, say so and ask the user to paste the transcript (not for a file name you cannot open),
  under the empty output skeleton.
- Recap audience (optional, default: all attendees).
- Jira project for action issues (optional, default: none; Jira drafts only on request).

## Sources
1. **Drive**: the transcript or notes doc linked to the Calendar event (Meet saves transcripts and notes to the
   organizer's Drive) and docs presented during the meeting.
2. **Google Calendar**: the event's attendee list (to correct transcribed names), date, agenda and organizer.
3. **Jira**: existing issues mentioned, to link actions to them instead of creating duplicates.
4. **Gmail, Chat and Slack**: pre-meeting threads, when the notes reference "what we said by email".
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Load the transcript or notes. Map speaker labels and misspelled names to the Calendar attendee list; anything
   that cannot be matched stays as written with a ⚠️.
2. Segment by agenda item (or by topic shift if no agenda).
3. **Decisions.** Keep only explicit agreements: "on valide", "go", "agreed", "let's do X", a decider stating a
   choice with no objection afterwards. Record the decider or "group" and the transcript timestamp. Ideas,
   preferences and "we should" are *not* decisions.
4. **Actions.** Extract commitments ("I'll…", "je m'en charge", "X will send…", or an assignment accepted by the
   person). Write each as **verb + deliverable**, **one owner** (a person, never a team), **due date** (absolute; a
   relative date is computed from the meeting date; none said → "date to set"). Merge duplicates.
5. **Unowned and fuzzy items.** Actions without an owner or deliverable go to a "to clarify" list, not silently
   assigned.
6. **Open questions and parking lot.** Questions not closed, topics deferred, and who will bring the answer.
7. **Recap email.** Subject "Recap — <meeting> — <date>". Body: 1-line purpose, decisions, actions table, open
   questions, next meeting. ≤ 25 lines. In the meeting's language.
8. **Jira drafts (on request).** One draft per action that is real work (> 1 h): summary = verb + deliverable,
   description with context and a link to the notes, assignee, due date, link to an existing issue if found. Short
   actions stay in the recap only.

## Output format
```markdown
**<Meeting> · <date> · <N> attendees · <N> decisions · <N> actions**

### Decisions
1. <decision> — decided by <name / group> (<timestamp or section>)

### Actions
| # | Action (verb + deliverable) | Owner | Due | Linked |
|---|-----------------------------|-------|-----|--------|
| 1 | <…> | <one person> | <YYYY-MM-DD / date to set> | <Jira key or —> |

### To clarify
- <item> — missing <owner / deliverable / date>

### Open questions & parking lot
- <question> — answer expected from <name> by <date>

### Recap email (draft)
Subject: Recap — <meeting> — <date>
<body ≤ 25 lines>

### Jira drafts (if requested)
- **<summary>** · assignee <name> · due <date> · <one-line description> · link <notes>
```

## Quality checks
- Every action has exactly one named person as owner and an absolute date or "date to set".
- Every decision traces back to a passage in the notes or transcript (section or timestamp).
- No idea, wish or "we should" is listed as a decision.
- Every name in the output matches the Calendar attendee list or carries a ⚠️.
- Actions that duplicate an existing Jira issue are linked to it, not drafted again.

## Guardrails
- Draft only: do not send the recap, create Jira issues or edit the notes doc until the user confirms.
- Do not quote people word for word in the recap unless it is a decision; no attribution of off-hand remarks.
- Leave out personal or sensitive remarks captured by the transcript (health, private life, HR cases, jokes about
  people), and tell the user they were left out.
- If the transcript is partial or low quality, say which parts are uncertain instead of filling gaps.
