---
name: back-from-leave-catchup
description: "Gets the user back on track after an absence: what changed while they were away (decisions, docs, tickets, org news), what still needs them versus what was already handled by others, the threads that can be archived in bulk, and a plan for the first three days, starting with a sync with their backup. Use whenever the user returns from holidays, leave, a trip or training, faces hundreds of unread messages, or asks what they missed, even if they only say 'I'm back'. Triggers - back from holidays, back from leave, what did I miss, catch up after vacation, hundreds of emails, je reviens de vacances, retour de congés, qu'est-ce que j'ai raté, rattraper mes mails, reprise après absence, je suis de retour."
---

# Back-from-leave catch-up

Turns a pile of unread messages into a short list of what really needs the user, what changed, and a calm plan for
the first days back.

## When to use
- First morning after an absence of 3 working days or more.
- After a business trip, a training week or a store opening that kept the user off email.
- The inbox shows more unread threads than can be read in a morning.
- Not for: a normal morning (use `daily-briefing`), a normal inbox backlog (use `inbox-triage`), or one project's
  history (use `topic-digest`).

## Inputs
- Absence period (optional, default: from the user's last sent email or Calendar out-of-office event to now).
- Handover doc or backup names (optional, default: search Drive for the user's handover doc).
- Topics that matter most now (optional).

## Sources
1. **Gmail**: threads received during the absence, `after:<start>`, with whether someone else already answered,
   and the out-of-office replies sent.
2. **Google Chat and Slack**: mentions and DMs during the absence; announcements in team spaces and channels.
3. **Jira**: issues assigned to the user or watched by them that changed status, got comments mentioning them, or
   became due; new issues assigned to them.
4. **Drive and Confluence**: the handover doc; docs the user owns or follows that were edited, with new comments or
   approval requests; new pages in team spaces.
5. **Google Calendar**: meetings that happened (notes and transcripts linked in Drive) and the next 3 working days.
6. **GitHub**: PRs that need the user's review or were merged on their repos.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Cluster by topic, not by message.** Group threads, tickets and docs that share a subject, project or ticket key.
   Read only the latest state of each cluster.
2. **Resolved without me?** For each cluster, check if a backup or colleague answered, a decision was posted, or the
   ticket is closed. If yes → "handled", one line, archive candidate.
3. **Still needs me.** Direct asks to the user with no answer, approvals waiting, decisions that need their input,
   deadlines in the next 5 working days. Score `urgency (overdue or ≤ 2 days = 3, this week = 2, later = 1)` ×
   `importance (manager, customer, blocks others = 3; own project = 2; other = 1)`.
4. **What changed.** Decisions taken, priority or scope changes, organizational news, new people on the team, new
   docs or processes. Each with the source link. Facts only.
5. **Handover check.** Compare with the handover doc: for each delegated topic, its status now and what the backup
   needs to hand back.
6. **Bulk clean-up.** Propose archive queries for notifications, newsletters and handled clusters
   (e.g. `after:<start> category:updates`), as proposals only.
7. **First-three-days plan.** Day 1 morning: sync with backup(s) (30 min) and top-scored asks. Day 1–2: reply to
   overdue asks, then prepare this week's meetings. Day 3: the remaining "needs me" items and the follow-ups to send.
   Keep one 90-minute block per day free.
8. Draft short replies for the top asks ("back today, I'll answer by <date>" is acceptable when the real answer
   needs work).

## Output format
```markdown
**Welcome back · away <start> → <end> · <N> threads, <N> mentions, <N> tickets changed · <N> need you**

### Needs you (by priority)
| # | Topic | Ask / deadline | Score | Link |
|---|-------|----------------|-------|------|

### What changed while you were away
- <decision / news> — <date> ([source](…))

### Handled without you (no action)
- <topic> — handled by <name> ([link](…))

### Handover status
| Topic | Backup | Status now | To hand back |
|-------|--------|------------|--------------|

### First three days
- **Day 1:** <…>
- **Day 2:** <…>
- **Day 3:** <…>

### Bulk clean-up (proposals, not done)
- Archive: `<query>` (<n> threads)

### Quick replies (drafts)
> <to name>: <≤ 3 lines>
```

## Quality checks
- Every "Needs you" item is still open at the time of the check (no later answer in the thread or ticket).
- Every "What changed" line has a source link and a date.
- Counts in the header match the lists.
- The plan starts with a sync with the backup(s) when a handover doc or backup exists.
- No more than 10 items in "Needs you"; the rest are summarized as a count with the archive or defer proposal.

## Guardrails
- Read only: no archiving, replying, accepting or commenting without the user's confirmation.
- Do not judge how backups handled topics; report status and open points factually.
- Keep sensitive content out of the summary (HR cases, health, salary); list them as "confidential thread from
  <sender>".
- Do not mention the reason for the user's absence in any draft.
