---
name: bug-report-writer
description: "Turns a vague problem report, Slack thread, support ticket, screenshot description or log excerpt into a Jira-ready bug report: clear title, reproducible steps, expected versus actual, environment, impact, severity separated from priority, evidence links, a duplicate check and open questions. Use whenever someone reports that something is broken, not working, wrong or slow in an app, site, API or store system and wants a ticket, even if they just paste a message from a colleague. Triggers - write a bug report, create a bug ticket, log this bug, file a Jira bug, it doesn't work, something is broken, rédige un ticket de bug, créer un bug Jira, ça ne marche pas, remonter une anomalie, déclarer un bug."
---

# Bug report writer

Turns "it doesn't work" into a bug report an engineer can reproduce, size and prioritize without a follow-up meeting.

## When to use
- A teammate, store or customer service agent reports a problem in Slack, Chat, email or a support ticket.
- A tester or product owner found a defect and wants a clean Jira ticket.
- An existing bug ticket is too vague to act on and needs to be rewritten.
- Not for: an ongoing production outage (use `incident-status-update`, then `incident-postmortem`), triaging many
  customer tickets at once (use `ticket-triage`), or a feature request (use `user-story-writer`).

## Inputs
- The problem description, thread, ticket or logs (required).
- Product, app or service concerned (required; inferred from the thread or Jira project if possible).
- Environment (optional, default: asked as an open question): production, staging; web, iOS, Android, store POS,
  handheld terminal; browser or app version; country or store.
- Target Jira project and issue type (optional, default: the project where similar bugs live).

## Sources
1. **Slack, Google Chat and Gmail**: the original report and replies, for exact wording, time, who saw it, and
   workarounds tried.
2. **Jira**: possible duplicates (search the key error message, component and summary words in open and recently
   closed bugs), the project's bug template and its severity and priority fields.
3. **GitHub**: recent merged PRs or releases touching the affected area (a likely regression window), open issues
   with the same error.
4. **Confluence**: known issues pages, the team's bug triage or severity definitions.
5. **Databricks or Tableau**: only if the user asks to size the impact (failed orders, affected stores) and the data
   is reachable; show the query or view used.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Extract facts from the report: what the user did, what they expected, what happened, when, where, how often.
   Separate facts from interpretations ("the API is down" is an interpretation; "checkout shows error 502 at payment
   step" is a fact).
2. Write the **title** as <Where> — <what is wrong> — <condition>, ≤ 90 characters. Example: "Checkout — card payment
   returns 502 — when basket contains a click-and-collect item".
3. Write **steps to reproduce** as numbered, minimal, deterministic steps with test data placeholders (never real
   customer data). If steps are unknown, write what is known and list the gaps.
4. Fill **expected vs actual**. Expected must cite a source (spec, acceptance criteria, previous behavior) or be
   marked as assumption.
5. Assess **severity** (technical impact) and suggest **priority** (business urgency) separately, using the team's
   definitions if Confluence has them, otherwise the defaults in the Reference section. Explain both in one line.
6. Run the **duplicate check** in Jira; list candidates with key and why they may match. Do not merge or link.
   Write « None found » only after a real Jira search; if Jira is not connected, write « not checked (Jira not
   connected) ». Same rule for recent changes (GitHub) and for the Evidence line (cite only what the user gave).
7. Note the **regression window**: the last release or merged PR in the area, if any, as a lead, not a conclusion.
8. List **open questions** for the reporter and a **reporter reply** asking only for what is missing.

## Output format
```markdown
**Summary:** <Where — what is wrong — condition>
**Type:** Bug · **Project:** <KEY> · **Component:** <…> · **Severity:** <S1–S4> · **Suggested priority:** <P1–P4>
_Severity because: <…> · Priority because: <…>_

### Environment
- Env: <prod/staging> · Platform: <web/iOS/Android/POS> · Version: <…> · Country/store: <…> · First seen: <date time TZ>

### Steps to reproduce
1. …
**Reproducibility:** <always | intermittent (x/y) | once | unknown>

### Expected
<… (source: …)>

### Actual
<… including exact error message or code>

### Impact
<who, how many, workaround yes/no — numbers only with source>

### Evidence
- <link to thread / log excerpt with secrets redacted / screenshot location>

### Leads (not conclusions)
- Possible duplicates: <KEY — reason>
- Recent changes in the area: <PR or release link>

### Open questions for the reporter
- …
```

## Quality checks
- Steps start from a known state and could be followed by someone who never saw the thread.
- Expected and actual are different and each is one observable statement.
- Severity and priority are both present and justified separately.
- No real customer name, email, phone, address, order tied to a person, or card data appears; IDs are replaced by
  placeholders unless the user confirms an internal-only order reference is needed.
- Every impact number has a source; otherwise impact is described qualitatively.

## Guardrails
- Draft only. Create, link or comment on Jira issues only after the user confirms the final text.
- Redact tokens, cookies, session IDs, API keys and passwords from pasted logs before quoting them.
- If the report suggests a security vulnerability or a personal data leak, do not put details in a broadly visible
  ticket: tell the user to follow the security reporting channel (ask them which one; do not invent it).
- If it looks like an active production outage, say so first and route to incident handling.

## Reference — default severity and priority
- **Severity** (impact): S1 critical = core flow down or data loss/corruption or security breach, no workaround
  (checkout, payment, POS sale); S2 major = core flow degraded or a feature broken for many, workaround painful;
  S3 moderate = feature partly wrong, reasonable workaround; S4 minor = cosmetic, typo, layout.
- **Priority** (urgency): P1 now, P2 this sprint, P3 planned, P4 when convenient. A cosmetic bug on the homepage
  during Black Friday can be S4/P1; a crash in an internal tool used once a year can be S2/P3.
