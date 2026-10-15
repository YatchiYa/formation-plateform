---
name: handover-before-leave
description: "Prepares the user's absence: inventories open work, deadlines and meetings that fall during the leave, builds a handover doc with a delegate map and the decision rights of each backup, proposes what to decline or reschedule in Calendar, and drafts a bilingual out-of-office reply. Use whenever the user goes on holiday, training, parental or any leave, or will be offline for several days, even if they only say 'I'm off next week'. Triggers - handover, going on leave, before my holidays, out of office, OOO message, who covers for me, delegate while away, passation, avant mes congés, je pars en vacances, message d'absence, réponse automatique, qui me remplace, préparer mon absence."
---

# Handover before leave

Lets the user leave without loose ends: every open topic has a backup who knows what they may decide, partners know
whom to contact, and the calendar is clean.

## When to use
- One to three working days before an absence of 3 days or more.
- The user needs an out-of-office reply or a handover note for a backup.
- A teammate covers the user's topics and needs a briefing.
- Not for: catching up after the absence (use `back-from-leave-catchup`), a permanent role transfer or onboarding a
  successor (use `onboarding-plan-builder`), or just listing open loops (use `follow-up-tracker`).

## Inputs
- Absence dates (required) and whether the user will be reachable at all (optional, default: not reachable).
- Backups (optional, default: proposed per topic from co-owners found in sources, to confirm by the user).
- Languages for the out-of-office (optional, default: French and English).

## Sources
1. **Google Calendar**: events during the absence (organized by the user or not), deadlines and recurring rituals
   the user runs.
2. **Jira**: issues assigned to the user that are open, due during the absence or within 3 working days after.
3. **Gmail, Chat and Slack**: threads from the last 14 days where the user owes an answer or is the main contact,
   and external partners (suppliers, customers, clubs) who write to the user regularly.
4. **Drive and Confluence**: docs the user owns with pending comments or approvals; the team's absence or backup
   rules if they exist.
5. **GitHub**: open PRs authored by the user or awaiting their review.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Inventory.** List every open topic: deliverables, pending decisions, approvals, recurring duties (weekly report,
   store ritual, supplier call), and external contacts. Merge duplicates across tools.
2. **Triage each topic**: *close before leaving* (≤ 2 h and due during the absence), *hand over*, *pause* (can wait;
   tell stakeholders), or *cancel*.
3. **Delegate map.** For each handed-over topic: backup, context in 3 lines, next step, deadline, key contacts and
   links, and the **decision right**: *can decide*, *can decide within <limit stated by the user>*, or *must wait /
   escalate to <name>*. Max 2 topics per backup per day of absence unless the user says otherwise.
4. **Emergency rule.** Define what justifies contacting the user (if anything), and how; default: nothing, escalate
   to the user's manager.
5. **Calendar.** For each event during the absence: organizer → cancel, move or hand over hosting; attendee →
   decline with a note naming the backup, or keep if a delegate attends. Draft the decline notes.
6. **Out-of-office.** Short, bilingual, no reason for the absence, return date, one contact per main topic (only with
   their agreement), no promise of reply date beyond "after my return".
7. **Handover meeting.** Propose a 30-minute slot with the backups before departure; the handover doc is the agenda.
8. List what the user must do before leaving, in order, with time estimates.

## Output format
```markdown
**Absence <start> → <end> (<n> working days) · <n> topics · <n> backups · <n> events to handle**

### Before you leave (checklist)
- [ ] <action> — <min> min

### Delegate map
| Topic | Backup | Next step & deadline | Decision right | Links |
|-------|--------|----------------------|----------------|-------|
| <topic> | <name (to confirm)> | <…> by <date> | can decide within <limit> | [doc](…) · [Jira](…) |

### Paused (stakeholders informed)
- <topic> — resumes <date> — message to <name>: "<one line>"

### Calendar during absence
| Event | Date | Action | Note (draft) |
|-------|------|--------|--------------|

### Emergency rule
<when and how, or "do not contact; escalate to <manager>">

### Out-of-office (FR / EN)
> <French text>
> <English text>
```

## Quality checks
- Every topic from the inventory appears exactly once: closed, handed over, paused or cancelled.
- Every handed-over topic has a backup, a next step with a date and an explicit decision right.
- Every event during the absence has an action, and every organizer-owned meeting has a host or is moved.
- The out-of-office has the return date, a contact per main topic, and no reason for the absence.
- Backups proposed from sources are marked "to confirm" until the user validates them.

## Guardrails
- Never state the reason for the absence (sick leave, parental leave, personal matters) in any output shared with
  others; health and family data are sensitive under GDPR.
- Do not name a backup in the out-of-office or decline notes before that person has agreed (the user confirms).
- No auto-reply, decline, delegation or Jira reassignment is applied without explicit confirmation.
- Do not hand over access credentials or passwords in the doc; point to the official access request process.
