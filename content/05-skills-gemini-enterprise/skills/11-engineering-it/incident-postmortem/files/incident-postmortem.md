---
name: incident-postmortem
description: "Writes a blameless SRE-style incident postmortem from the incident channel, tickets, alerts and meeting notes: summary, customer and business impact, SLO and error budget consumed, minute-by-minute timeline with detection and mitigation times, root cause through 5 whys, contributing factors, what went well, where we got lucky, and prioritized action items with owners. Use whenever an incident is resolved and needs a review, a retro doc or a post-incident report, for production outages, degraded checkout, data issues or store system failures, even if the user just says 'write up what happened'. Triggers - postmortem, post-mortem, incident review, RCA, root cause analysis, incident report, write up the outage, retour d'incident, post-mortem, analyse de cause racine, rapport d'incident, REX incident."
---

# Incident postmortem

Turns the raw trail of an incident into a blameless postmortem that explains what happened, why the system allowed
it, and what will make it less likely or less painful next time.

## When to use
- A production incident is resolved (outage, degraded performance, data corruption, security event, failed release).
- A near-miss deserves learning even with no customer impact.
- A postmortem meeting is scheduled and the draft is needed beforehand.
- Not for: updates while the incident is still ongoing (use `incident-status-update`), a physical store incident
  such as an injury or theft (use `store-incident-report`), or a project retrospective (use `lessons-learned`).

## Inputs
- The incident: Jira key, Slack or Chat channel, or a description with dates (required).
- Severity level and the team's postmortem template (optional, default: discovered in Confluence/Drive, else the
  template below).
- SLO definitions for the affected service (optional, default: searched in Confluence; if none, impact is described
  without error budget math).

## Sources
1. **Slack and Google Chat**: the incident channel or thread, for timestamps of detection, escalation, hypotheses,
   mitigation and resolution.
2. **Jira**: the incident ticket, linked bugs, changes or releases deployed before the start time.
3. **GitHub**: PRs merged and deployments in the hours before the incident, the fixing PR or revert.
4. **Gmail and Calendar**: incident communications sent, bridge calls; Meet transcripts or notes in **Drive**.
5. **Confluence and Drive**: the postmortem template, severity definitions, SLO pages, runbooks used, prior
   postmortems for the same service (repeat incidents).
6. **Databricks or Tableau**: impact numbers (failed orders, affected stores, error rate) if reachable; show the
   query or view.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Build the **timeline** in UTC and local time: first bad change or trigger, start of impact, detection (alert or
   human report), acknowledgment, escalation, key hypotheses, mitigation, full recovery, all-clear. Each line cites a
   message, ticket or commit.
2. Compute **durations**: time to detect (start → detection), time to mitigate (detection → impact stopped), total
   impact duration. Note if detection came from customers or stores instead of monitoring — that is a finding.
3. Quantify **impact** only from sources: users, orders, revenue at risk, stores, countries, data affected. Else
   describe qualitatively and mark "to quantify — owner".
4. **SLO and error budget**: if an SLO exists, compute budget consumed (bad minutes or bad requests ÷ allowed in the
   window). Example: 99.9% monthly availability allows ~43 min; a 30-min checkout outage consumes ~70% of it.
5. **Root cause with 5 whys**: start from the symptom, ask why until reaching a systemic cause (a missing safeguard,
   process or design property), not a person. Stop when the answer is something the organization can change. Branch
   when there are several causes.
6. **Contributing factors**: list separately — detection gaps, missing runbook, alert noise, risky deploy timing,
   config without validation, dependency without timeout, unclear ownership, capacity.
7. Record **what went well** and **where we got lucky** (luck is a hidden risk).
8. **Action items**: each one SMART, typed (prevent / detect / mitigate / process), prioritized, with a proposed
   owner role and a Jira key placeholder. Prefer fewer, high-leverage actions over long wish lists. Flag repeat
   actions from previous postmortems.

## Output format
```markdown
# Postmortem — <incident title> (<date>)
**Severity:** <…> · **Status:** Draft for review · **Incident lead:** <role/name from sources> · **Ticket:** <link>

## Summary
<3–4 sentences: what broke, impact, duration, root cause, main fix>

## Impact
| Dimension | Value | Source |
|-----------|-------|--------|
| Duration of impact | … | … |
| Users / orders / stores affected | … | … |
| SLO / error budget consumed | … | … |

## Timeline (<TZ>)
| Time | Event | Source |
|------|-------|--------|
**Time to detect:** … · **Time to mitigate:** … · **Detected by:** <alert | customer | store | teammate>

## Root cause (5 whys)
1. Why …? Because …
…
**Root cause:** <systemic statement>

## Contributing factors
- …

## What went well
- …
## Where we got lucky
- …

## Action items
| # | Action | Type | Priority | Owner (proposed) | Ticket |
|---|--------|------|----------|------------------|--------|

## Open questions for the review meeting
- …
```

## Quality checks
- Every timeline entry has a source; gaps longer than 15 minutes during the incident are flagged as "unknown".
- The root cause is a system or process property, never "human error" or a person's name.
- Each why follows logically from the previous answer; branches are shown when causes are multiple.
- Every action item is specific, testable and typed; at least one addresses detection if detection was slow.
- Impact numbers all have a source or are marked "to quantify".

## Guardrails
- **Blameless**: describe actions and decisions in context ("the deploy was run during peak because the pipeline
  allowed it"), never fault individuals. Use roles rather than names in the narrative unless the team's norm says
  otherwise.
- Do not paste secrets, tokens, internal credentials or customer personal data from logs or channels.
- Security incidents and personal data breaches have legal notification duties (GDPR 72 h to the authority): flag to
  the user to involve security and the DPO; do not decide notification.
- Draft only. Do not publish, share or create Jira actions until the user confirms.
