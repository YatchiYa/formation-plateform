---
name: follow-up-tracker
description: "Finds the user's open loops across Gmail, Chat, Slack and Jira: sent emails still waiting for an answer, promises the user made and has not delivered, and what others owe the user, then drafts tactful nudges graded by age and importance. Use whenever the user asks what they are waiting for, what they forgot, who has not answered, what they promised, or wants to chase people, even if they only say 'did I forget anything'. Triggers - follow up, waiting for reply, who hasn't answered, open loops, what did I promise, chase, nudge, relance, relancer, en attente de réponse, qui ne m'a pas répondu, qu'est-ce que j'ai promis, sujets en suspens, j'ai oublié quelque chose."
---

# Follow-up tracker

Surfaces every loop the user opened and never closed, in both directions, and gives them the right nudge for each
one.

## When to use
- Weekly, to make sure nothing the user sent or promised is falling through.
- Before a deadline that depends on answers from others.
- When the user suspects they forgot to send something they promised.
- Not for: processing incoming mail (use `inbox-triage`), the absence handover (use `handover-before-leave`), or
  tracking a project's action log (use `raid-log-builder`).

## Inputs
- Look-back window (optional, default: last 30 days).
- Minimum waiting time before a nudge (optional, default: 3 working days internal, 5 external).
- People or topics to focus on (optional).

## Sources
1. **Gmail sent**: messages the user sent in the window that contain a question or a request (`in:sent
   newer_than:30d`), and whether any recipient replied later in the thread.
2. **Gmail, Chat and Slack**: the user's own commitments ("I'll send", "je te reviens", "je vous envoie",
   "d'ici vendredi", "let me check") and others' commitments to the user ("I'll get back to you", "je regarde").
3. **Jira**: issues the user reported or is watching that wait on someone else (status unchanged for 5+ working
   days), and issues assigned to the user that someone asked about.
4. **Drive**: comments assigned to the user or by the user that are still open.
5. **Calendar**: meetings that happened since, to detect loops closed orally.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Waiting on others.** Sent messages with an ask and no reply from the addressee after the waiting threshold.
   Skip FYIs, thank-yous and messages answered in another channel (search Chat/Slack/Jira for the topic).
2. **I owe.** Commitments by the user with no sign of delivery (no later message with the attachment, link or answer,
   no Jira update). Convert vague deadlines: "tomorrow" = message date + 1 working day; no date → 5 working days.
3. **Others owe me.** Commitments made to the user that are past due.
4. **Check closure.** Drop a loop if a later meeting, message or ticket shows it was resolved; if unsure, keep it and
   mark "maybe closed".
5. **Prioritize** by `importance (manager, customer, blocks a deadline = 3; own project = 2; other = 1)` ×
   `age (≥ 2× threshold = 3, ≥ threshold = 2, else 1)`.
6. **Nudge ladder.** Draft according to how many times the user already chased:
   - **Nudge 1** (soft): restate the ask in one line, add value (a link, a simpler option), no blame.
   - **Nudge 2** (specific): give the date you need it by and why ("to finalize the Domyos order by Friday").
   - **Nudge 3** (alternative): offer a 10-minute call, propose a default ("without news by Tuesday, I will
     proceed with option A"), or suggest who else can answer. Escalation to a manager is only suggested, never drafted
     without the user's request.
7. For "I owe" items, draft either the delivery message or an honest new-date message.

## Output format
```markdown
**Open loops · <window> · waiting on others <n> · I owe <n> · others owe me <n>**

### I owe (deal with these first)
| Promise | To | Promised on | Due | Proposed message |
|---------|----|-------------|-----|------------------|
| <deliverable> | <name> | <date> ([link](…)) | <date> | deliver / new date: "<draft>" |

### Waiting on others
| Ask | From | Sent | Waiting | Nudge # | Draft |
|-----|------|------|---------|---------|-------|
| <ask> | <name> | <date> ([link](…)) | <n> working days | 1 | "<draft>" |

### Others owe me (past due)
- <name> — <what> — due <date> ([link](…)) → nudge <n>: "<draft>"

### Maybe closed (check)
- <topic> — <why uncertain>
```

## Quality checks
- Every loop links to the message, comment or ticket that opened it.
- No loop is listed whose ask was already answered in the same thread or another connected channel.
- Waiting times are counted in working days and respect the thresholds.
- Each draft matches the nudge level, fits in 4 lines, and stays in the thread's language and register.
- "I owe" items appear before "Waiting on others".

## Guardrails
- Draft only: no message is sent, no ticket commented, without the user's confirmation.
- Tone stays courteous and blame-free; never imply bad faith or mention the other person's workload or absence.
- Do not track colleagues' responsiveness as a metric or produce rankings of who answers slowly.
- If a loop concerns a sensitive matter (HR, health, legal), list it as "sensitive loop with <name>" and let the
  user handle it personally.
