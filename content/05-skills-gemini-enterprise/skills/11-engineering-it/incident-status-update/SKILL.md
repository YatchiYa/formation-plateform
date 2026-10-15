---
name: incident-status-update
description: "Drafts incident status updates during an ongoing outage or degradation, in three versions from the same facts: technical update for the incident channel, plain-language update for business and store teams, and a customer-facing status message for approval, each with severity, impact, current status, next steps and the time of the next update, at a cadence matched to severity. Use whenever an incident is in progress and someone needs to inform people, send an update, an all-clear or a status page message, even if they only ask 'what do I tell the stores'. Triggers - incident update, status update, outage communication, status page message, all clear, inform stores about the outage, communication d'incident, point de situation incident, message aux magasins panne, mise à jour statut incident, fin d'incident."
---

# Incident status update

Keeps everyone who depends on a broken service informed with accurate, calm, regular updates, so the responders can
keep working and nobody fills the silence with rumors.

## When to use
- An incident is open and the incident lead or comms lead must post the first or next update.
- Business teams, stores or customer service ask what is happening and what to do.
- The incident is resolved and an all-clear message is needed.
- Not for: the after-action review (use `incident-postmortem`), a planned maintenance announcement (use
  `internal-announcement-writer`), or answering one customer (use `customer-reply-drafter`).

## Inputs
- What is known now: symptom, affected service, start time, current status (required). Extracted from the incident
  channel if the user points to it.
- Severity level (optional, default: proposed from impact using the team's definitions, else the Reference section).
- Audiences needed (optional, default: technical + business; customer-facing only if customers are visibly affected).
- Update number and previous updates (optional, default: read from the channel).

## Sources
1. **Slack and Google Chat**: the incident channel or thread: latest confirmed facts, mitigation in progress, ETA
   given by responders, previous updates (to stay consistent).
2. **Jira**: the incident ticket and its severity, linked releases.
3. **Confluence and Drive**: incident communication guidelines, severity matrix, approved customer status wording,
   contact lists and who approves external messages.
4. **Gmail**: previous incident emails to business distribution lists, for format and recipients.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Separate **confirmed facts** from **hypotheses** in the latest channel messages. Only confirmed facts go into
   business and customer versions; hypotheses may appear in the technical version, labeled as such.
2. Set or confirm **severity** and the **cadence** (default: SEV1 every 30 min, SEV2 every 60 min, SEV3 at
   milestones). Always state the time of the next update, even if nothing changes ("no change" is an update).
3. Write the **technical update**: status (Investigating / Identified / Mitigating / Monitoring / Resolved), impact,
   what is being tried, who leads, next update time, links.
4. Write the **business update**: what does not work for whom, in user terms ("click-and-collect orders cannot be
   placed on the website; in-store sales and card payment work"); the **workaround** and what teams should do or tell
   customers; next update time. No jargon, no internal hostnames, no blame.
5. Write the **customer-facing message** only if customers are affected: acknowledge, impact in their words, what to
   do meanwhile, apology, no technical cause, no ETA unless responders committed to one. Mark it "Requires approval".
6. For **all-clear**: what was affected, duration, confirmed recovery, any customer follow-up (orders to check,
   duplicate charges), and that a postmortem will follow (internal versions only).
7. Check consistency with previous updates; if the picture changed (impact larger than announced), say so
   explicitly rather than silently correcting.

## Output format
```markdown
**Update #<n> · <SEV> · <status> · <HH:MM TZ>** — next update by <HH:MM TZ>
_Facts used: <source links> · Hypotheses excluded from business/customer versions_

### 1. Technical channel
**[<SEV>] <service> — <status>**
- Impact: …
- Current action: … (lead: <role/name>)
- Hypotheses (unconfirmed): …
- Next update: <time> · Ticket: <link>

### 2. Business and stores (email / Chat / Slack)
**Subject:** [<status>] <what is affected> — update <n>
- What is affected: …
- What still works: …
- What to do / tell customers: …
- Next update: <time>

### 3. Customer-facing (requires approval before publishing)
<≤ 60 words, plain, apologetic, actionable>
```

## Quality checks
- Every version states the time of the next update in an explicit time zone.
- Business and customer versions contain no unconfirmed cause, no internal system names, no blame.
- "What still works" is stated, to prevent unnecessary panic (for example card payments in store).
- No ETA appears unless the responders gave it in the sources, and it is worded as an estimate.
- The update number and status are consistent with the previous updates.

## Guardrails
- Draft only. Do not post in channels, email lists or the status page; the incident or comms lead sends.
- Customer-facing and press-sensitive messages always need human approval (comms or legal as per the team's
  guidelines); never present them as ready to publish.
- If the incident involves personal data or security, keep details out of every broad message and tell the user to
  involve security and the DPO before communicating.
- Do not speculate on cause, compensation or refunds; those are decided by people.

## Reference — default severity levels
- **SEV1**: critical customer flow down or data at risk at scale (online checkout, payment, POS sales in many stores).
- **SEV2**: major degradation or one critical flow down for a subset (one country, one channel), workaround exists.
- **SEV3**: minor or internal impact, limited users, no customer-visible effect.
Use the team's own matrix if Confluence has one; these defaults are only a fallback.

## Example
Input: « Le paiement CB en ligne échoue depuis 14h10, l'équipe a identifié un souci chez le PSP, que dit-on aux magasins ? »
→ Output in French, update #2, SEV1, status Identified. Business version: « Les paiements par carte sur le site
échouent depuis 14h10. Les ventes en magasin et le paiement en caisse fonctionnent normalement. Si un client appelle :
proposer de réessayer plus tard ou de commander en magasin. Prochain point à 15h00. » Customer version marked
"Requires approval", with no mention of the payment provider.
