---
name: inbox-triage
description: "Processes the Gmail inbox down to what matters: classifies every thread as reply, delegate, defer or archive, drafts the quick replies, proposes bulk actions and filters for recurring noise, and lists what is left with a time estimate. Use whenever the user has too many emails, wants inbox zero, comes back to a full inbox, or asks which emails need them, even if they only say 'help with my mails'. Triggers - inbox triage, clean my inbox, inbox zero, too many emails, which emails need me, sort my email, trier mes mails, ranger ma boîte mail, boîte de réception, trop de mails, quels mails dois-je traiter, vider ma boîte."
---

# Inbox triage

Turns an overflowing Gmail inbox into four short lists and a set of ready drafts, so the user spends minutes
deciding instead of an hour reading.

## When to use
- The inbox holds more unread threads than the user can read today.
- After a busy day or a trip, before deep work.
- The user wants recurring noise (notifications, newsletters, CC chains) under control.
- Not for: a whole-day overview (use `daily-briefing`), a long absence (use `back-from-leave-catchup`),
  writing one careful reply (use `email-reply-drafter`), or summarizing one long thread (use `thread-catchup`).

## Inputs
- Scope (optional, default: `in:inbox is:unread newer_than:7d`, max 100 threads; oldest are summarized as a count).
- People or topics that are always high priority (optional, default: manager, direct reports, external customers).
- Time available for processing (optional, default: 30 minutes).

## Sources
1. **Gmail**: inbox threads in scope, with sender, To/CC position, labels, Gmail category, attachments and the
   latest message. Search operators: `in:inbox`, `is:unread`, `newer_than:`, `-category:promotions`,
   `-category:social`, `to:me`, `cc:me`, `has:attachment`.
2. **Gmail sent**: the user's last messages with each frequent sender, to detect who they actually answer.
3. **Calendar**: invitations still pending, and meetings that a thread refers to.
4. **Jira, Chat and Slack**: to check whether a thread's ask was already handled elsewhere.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Fetch the threads in scope. Group threads that share a subject or a ticket key.
2. Classify each thread with the **4D rule**:
   - **Do (reply)**: a direct question or request to the user, they are in To:, and the answer takes ≤ 2 minutes
     or only the user can give it.
   - **Delegate**: the request belongs to someone else's scope (the user is in CC, or a teammate owns the topic).
   - **Defer**: needs more than 2 minutes of work or a decision; becomes a task with a date.
   - **Drop (archive)**: FYI, notifications, newsletters, automated alerts already resolved, CC chains with no ask.
3. Score Do and Defer items: `urgency (deadline ≤ 48 h = 3, this week = 2, none = 1)` ×
   `importance (manager, customer, incident, blocking others = 3; own project = 2; other = 1)`. Sort by score,
   then by age.
4. For every **Do** item, draft a reply of at most 5 lines in the user's usual tone (greeting, tu/vous, sign-off
   taken from their sent mail to that person). Mark any date, number or commitment in **bold** for review.
5. For every **Delegate** item, name the likely owner only if the thread or Drive/Confluence shows it, and draft a
   short forward note. Otherwise write "owner to confirm".
6. For **Drop**, propose bulk actions: archive by sender or label, unsubscribe candidates (newsletters still unread
   in the window), and Gmail filter rules for recurring noise (e.g. `from:<alerts sender>`
   → skip inbox, apply label).
7. Estimate the remaining time: Do = 2 min each, Defer = the user's estimate or 15 min default.

## Output format
```markdown
**<N> threads triaged · Do <n> · Delegate <n> · Defer <n> · Drop <n> · est. <min> min left**

### Do now (drafts ready)
| # | From | Topic (≤ 10 words) | Score | Draft |
|---|------|--------------------|-------|-------|
| 1 | <name> | <topic> ([link](…)) | 9 | see draft 1 |

**Draft 1 — to <name>**
> <≤ 5 lines>

### Delegate
- <topic> → <owner or "owner to confirm"> — forward note: "<one line>" ([link](…))

### Defer (to schedule)
- <topic> — needs <what> — suggested date <day> ([link](…))

### Drop — proposed bulk actions (not done yet)
- Archive <n> threads from <sender/label>
- Unsubscribe candidates: <sender list>
- Filter: `<query>` → <action>

_Scope: <query used> · Sources checked: Gmail ✓ · Calendar ✓ · Jira ✓ · Chat ✓ · Slack ✗ (not connected)_
```

## Quality checks
- Every thread in scope lands in exactly one of the four lists, and the counts add up.
- Every Do draft answers the actual question in the thread, and every bold commitment is flagged for review.
- No thread already answered by the user, or resolved in Jira/Chat, sits in Do.
- Bulk actions are listed as proposals with the exact query, not executed.
- Senders marked always-important never land in Drop without an explicit reason.

## Guardrails
- Never send, archive, delete, label, unsubscribe or create filters without explicit confirmation of the list.
- Do not open or quote attachments or bodies of HR, medical, legal or payroll emails in the output; show a neutral
  line ("confidential HR email from <sender>").
- Do not guess who to delegate to from job titles alone; delegation targets come from sources or from the user.
- Watch for phishing signs (unexpected payment or credential requests, look-alike domains) and flag them instead of
  drafting a reply.
