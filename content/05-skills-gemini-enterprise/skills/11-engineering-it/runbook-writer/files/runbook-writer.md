---
name: runbook-writer
description: "Writes an operational runbook for a service, alert or recurring operation: when it applies (alert names, symptoms), prerequisites and access, fast triage, diagnosis branches, numbered remediation steps each with an expected result and a verification, rollback, escalation path and communication hooks, built from code, configs, past incidents and team docs. Use whenever an on-call engineer or ops team needs a procedure for an alert, a failure mode, a deploy, a failover or a manual fix, or when a postmortem action says 'add a runbook', even if they only say 'how do we handle X when it breaks'. Triggers - runbook, procedure for when a system, feed or interface fails, playbook, on-call procedure, alert response, how to fix when, operational procedure, procédure d'exploitation, procédure quand le flux ou l'interface plante, runbook astreinte, que faire quand l'alerte, fiche réflexe, mode opératoire incident."
---

# Runbook writer

Produces a runbook that a tired on-call engineer, new to the service, can follow at 3 a.m. without guessing.

## When to use
- A new alert exists and needs a linked response procedure.
- A postmortem action requires documenting a manual fix or failover.
- A recurring operation (cache flush, replaying failed stock events, rotating a certificate) lives only in one
  person's head.
- Not for: a business process procedure (use `sop-writer`), the design of the system (use `tech-spec-writer`), or
  analyzing a past incident (use `incident-postmortem`).

## Inputs
- Service and the scenario: alert name, failure mode or operation (required).
- Audience (optional, default: on-call engineer with production access but not an expert in this service).
- Existing notes, scripts or past incident threads (optional, default: searched in sources).
- Platform specifics (optional, default: discovered; never invented): how deploys, rollbacks, feature flags and
  dashboards work in this team.

## Sources
1. **GitHub**: the service repo: README, deploy and CI config, infrastructure as code, alert rule definitions, health
   endpoints, scripts in tools/ or ops/ folders, feature flag definitions.
2. **Confluence and Drive**: existing runbooks (format to reuse), on-call and escalation pages, architecture docs.
3. **Jira**: past incidents and postmortem actions for this service — the real failure modes and fixes that worked.
4. **Slack and Google Chat**: incident channels where this scenario was handled; the exact commands or clicks used.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Define the **trigger**: alert names exactly as defined in the repo, plus human-visible symptoms ("stores report
   prices not updating on handheld terminals").
2. List **prerequisites**: access roles, tools, VPN, dashboards (links from sources), and who can approve risky
   actions. Missing items become questions, never invented names.
3. Write **triage in under 5 minutes**: is it real (check dashboard X), how big (one store, one country, all), is a
   deploy or change in progress (check the deploy history), what severity to declare.
4. Write **diagnosis branches** as if/then: symptom → check → likely cause → go to step N. Order by likelihood and by
   cost of the check (cheap checks first).
5. Write **remediation steps**: one action per step, the exact command or UI path in a code block when the sources
   give it (with placeholders for environment and IDs), the **expected result**, how to **verify** it worked, and
   what to do if it did not. Mark destructive or irreversible steps with ⚠️ and a confirmation requirement.
6. Write **rollback** for every change-making step, and the **stop and escalate** conditions (time box per step,
   e.g. "not resolved in 15 min → escalate").
7. Add **escalation** (roles and channels found in sources; ask if missing) and **communication** hooks (when to open
   an incident and post updates).
8. Add **post-actions**: data to capture for the postmortem, follow-up tickets, and a "last validated" date with an
   owner to review the runbook.

## Output format
```markdown
# Runbook — <service>: <scenario>
**Owner:** <team> · **Last validated:** <date or "never — validate in a game day"> · **Severity hint:** <…>

## When to use
- Alerts: <exact alert names>
- Symptoms: …

## Prerequisites
- Access: … · Tools: … · Dashboards: <links>

## Triage (≤ 5 min)
1. …

## Diagnosis
| If you see… | Check | Likely cause | Go to |
|-------------|-------|--------------|-------|

## Remediation
### Step 1 — <action>
<command or UI path with <placeholders>>
- Expected: …
- Verify: …
- If it fails: …
- Rollback: …

## Stop and escalate when
- …
## Escalation
| Level | Who (role) | How to reach | When |
|-------|-----------|--------------|------|

## After the incident
- Capture: … · Follow-up: …
```

## Quality checks
- Every command, alert name, dashboard and tool comes from a source or is a clearly marked placeholder.
- Every change-making step has expected result, verification and rollback.
- Destructive steps are marked ⚠️ and require explicit confirmation or a second person.
- Each diagnosis branch ends in a step or an escalation; there are no dead ends.
- A newcomer can follow it without reading the code (no unexplained acronyms).

## Guardrails
- Never put secrets, passwords, tokens or connection strings in a runbook; reference the secret manager or vault
  location by name only if found in sources.
- The model cannot run or test commands. Mark the runbook "not yet validated" until the team rehearses it.
- Do not invent escalation contacts, on-call rotations or internal tools; leave placeholders and ask.
- Draft only. Do not publish to Confluence or commit to the repo until the user confirms.
