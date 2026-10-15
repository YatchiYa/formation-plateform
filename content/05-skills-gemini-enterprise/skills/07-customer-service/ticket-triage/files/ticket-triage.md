---
name: ticket-triage
description: "Triages a batch of customer tickets or messages: assigns a contact reason, a priority from an impact x urgency matrix, a routing team, flags duplicates and safety or legal cases, and detects emerging issues such as a spike on one product or delivery zone, then outputs a sorted queue and proposed field updates. Use whenever someone has a backlog of tickets, emails or chats to sort, wants to know what to handle first, or suspects a new recurring problem, even if they just say 'my queue is a mess'. Triggers - triage tickets, sort my queue, prioritize tickets, backlog of customer emails, emerging issue, trier les tickets, prioriser les demandes clients, file d'attente SAV, tri des réclamations, backlog service client, nouvelles tendances tickets."
---

# Ticket triage

Turns an unsorted pile of customer contacts into a prioritized, routed queue, and spots the problem that is
starting to repeat before it becomes a crisis.

## When to use
- Monday morning backlog, post-sale-period peak, or after an outage.
- A team lead wants to rebalance the queue between agents or teams.
- Several customers seem to report the same thing (product, delivery zone, app bug).
- Not for: answering one ticket (use `customer-reply-drafter`), a full monthly analysis of contact reasons (use
  `voice-of-customer-report`), or a single severe case (use `complaint-escalation-brief`).

## Inputs
- The tickets: a Jira filter or project, a Gmail label, a Slack/Chat channel, an Airtable view or a pasted export
  (required).
- Contact-reason taxonomy and routing table (optional, default: search Drive/Confluence, else the taxonomy below).
- Team SLAs (optional, default: none stated; priorities only).
- Time window (optional, default: all open items).

## Sources
1. **Jira** (service desk projects): open issues with summary, description, created date, reporter type, labels,
   components. Query with JQL such as `statusCategory != Done ORDER BY created ASC` scoped to the project.
2. **Gmail**: threads in the support label or shared inbox the user names, unanswered first.
3. **Slack / Google Chat**: support or store escalation channels, messages without a reply.
4. **Airtable**: case-tracking bases, if used.
5. **Drive / Confluence**: the official contact-reason taxonomy, routing matrix and SLAs.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Normalize** each item: id, link, date, channel, product or order mention, one-line summary.
2. **Flag first** (overrides everything): safety or injury, legal threat, data/privacy request (access, deletion),
   payment or fraud, media exposure. Flagged items get P1 and a named route.
3. **Classify the contact reason** with the internal taxonomy if found, else: Order & delivery · Returns &
   refunds · Product defect / quality · Product use & advice · Repair & workshop · Store experience · Website/app
   bug · Account & loyalty · Other. One primary reason per ticket; low confidence → mark "?".
4. **Prioritize** with impact × urgency:
   - Impact: high = safety, money already taken with no product, blocks sport use on a known date, many customers;
     medium = one customer, workaround exists; low = information.
   - Urgency: high = deadline ≤ 48 h, waiting > SLA, or 2+ follow-ups; medium = this week; low = no deadline.
   - P1 = high/high or any flag · P2 = one high · P3 = medium/medium · P4 = rest.
5. **Deduplicate**: same customer, same order or same thread → merge, keep the oldest id as master.
6. **Detect emerging issues**: group by product reference, reason, delivery zone or app version. A cluster of
   ≥ 3 tickets in the window that share a cause is an *emerging issue*; give count, first seen, example links.
7. **Route** each ticket to a team from the internal routing table, or say "routing to confirm".
8. **Propose updates** (priority, labels, assignee) as a list. Apply nothing without confirmation.

## Output format
```markdown
**Triage — <N> items · <N> P1 · <N> duplicates · <N> emerging issues · window <dates>**

### Act now (P1)
| Ticket | Summary | Flag / reason | Route | Why P1 |
|--------|---------|---------------|-------|--------|

### Emerging issues
- **<pattern>** — <count> tickets since <date> · e.g. [#1](…), [#2](…) · suggested owner: <team>

### Queue
| Priority | Ticket | Reason | Summary (≤ 12 words) | Age | Route |
|----------|--------|--------|----------------------|-----|-------|

### Duplicates merged
- <master> ← <dup1>, <dup2>

### Proposed updates (not applied)
- <ticket>: priority → <Px>, label → <reason>, assignee → <team>

_Taxonomy: <internal doc link | default library taxonomy> · Sources checked: <list with status>_
```

## Quality checks
- Every ticket in the input appears exactly once (queue or duplicates); totals in the header add up.
- Every P1 has a named reason from step 2 or step 4.
- Each emerging issue has ≥ 3 linked tickets and a first-seen date.
- Reasons marked "?" are listed, not hidden.
- No proposed update is presented as already done.

## Guardrails
- Summaries carry no personal data beyond what routing needs: no addresses, phone numbers, payment details or
  health descriptions in the table.
- Data-protection requests (access, erasure) route to the privacy process found in Drive/Confluence; do not answer
  them here.
- Do not close, merge or reassign tickets in Jira or any tool until the user confirms the proposed updates.
- An emerging issue is a hypothesis to verify, not a confirmed defect; word it that way.

## Example
Input: "Trie la file Jira SAV de ce matin" (42 open issues).
→ Header: 42 items · 3 P1 · 4 duplicates · 1 emerging issue. P1: a customer reports a helmet strap that broke during a
fall (safety flag → product safety route), a GDPR erasure request (privacy route), a payment taken twice. Emerging
issue: « 5 tickets since Monday about orders stuck 'in preparation' in one delivery zone » with links, owner
suggestion: logistics. Proposed label and priority updates listed, none applied.
