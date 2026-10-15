---
name: tech-spec-writer
description: "Writes a Google-style technical design document for a feature or system change: context and scope, goals and non-goals, the proposed design with APIs, data model and sequence, alternatives considered with trade-offs, cross-cutting concerns (security, privacy, reliability with SLOs, cost, observability), migration and rollout plan, and open questions for reviewers. Use whenever an engineer must design something before coding, prepare a design review, or turn a PRD or epic into a technical plan, even if they ask for 'a quick doc'. Triggers - tech spec, design doc, technical design, RFC, solution design, system design for, spec technique, document de conception, dossier d'architecture, conception technique, RFC technique."
---

# Tech spec writer

Produces a design doc that lets reviewers challenge the important decisions before code exists, when changing them
is still cheap.

## When to use
- A feature or migration is big enough that two engineers could build it in very different ways.
- A design review is scheduled and the doc is not written yet.
- A PRD, epic or incident action needs a technical answer (for example "make the stock API survive Black Friday").
- Not for: the product problem and requirements (use `prd-writer`), recording one already-taken decision (use
  `architecture-decision-record`), or the operational procedure once live (use `runbook-writer`).

## Inputs
- The problem or feature, with any PRD, epic or ticket (required).
- Known constraints (optional, default: discovered from sources or asked): deadline, team, existing systems, budget,
  compliance.
- Design ideas already on the table (optional) — the doc will compare them.
- Template (optional, default: the team's design doc template in Drive/Confluence, else the one below).

## Sources
1. **Confluence and Drive**: PRD, existing design docs and ADRs for the systems involved, architecture overviews,
   the team template, SLO pages, platform or security standards.
2. **Jira**: the epic and stories, linked incidents (they reveal real failure modes), dependencies on other teams.
3. **GitHub**: the current code of the affected services (entry points, data model, API definitions like OpenAPI or
   proto files, infrastructure config) to describe "as is" accurately.
4. **Gmail, Slack and Google Chat**: threads where the approach was already debated, to capture constraints and
   rejected ideas.
5. **Databricks or Tableau**: volumes and peaks (orders per minute, catalog size, stores) if reachable; show the query.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Write **Context** from sources: what exists today, what hurts, who is affected. Cite the documents and code.
2. Write **Goals** (measurable where possible: "p99 stock lookup < 200 ms at 3x last peak") and **Non-goals**
   (explicitly out of scope, to prevent scope creep). Numbers come from sources or are labeled targets to validate.
3. Describe the **Design** at the level a reviewer needs: component diagram described in text (or Mermaid), API
   contracts (endpoints, events, payload sketches), data model changes, the main sequence (happy path), and failure
   handling (timeouts, retries with backoff, idempotency keys, fallback when a dependency is down — for example selling
   in store when the central stock service is unreachable).
4. List **Alternatives considered** (at least two, including "do nothing" or "buy/reuse"), compared on the same
   criteria, with the reason each was not chosen.
5. Cover **cross-cutting concerns**: security (authn/z, secrets, OWASP risks for new endpoints), privacy (personal
   data, retention, GDPR — flag for a privacy review if new personal data), reliability (SLI/SLO, error budget impact,
   capacity), observability (logs, metrics, traces, alerts), cost (order of magnitude, labeled estimate), accessibility
   if UI.
6. Write the **Rollout plan**: feature flags, migration steps (expand → migrate → contract), backward compatibility,
   canary or pilot (one country, a few stores), success criteria, rollback at each step.
7. List **Open questions** with an owner to answer each, and the **Decisions needed** from reviewers.
8. Keep it reviewable: main body ≤ 6 pages equivalent; details go to an appendix.

## Output format
```markdown
# <Title> — Design doc
**Author(s):** <…> · **Reviewers:** <…> · **Status:** Draft · **Last updated:** <date> · **Links:** <PRD, epic, ADRs>

## TL;DR
<3 sentences: problem, proposed design, main trade-off>

## Context
## Goals
- …
## Non-goals
- …
## Design
### Overview
### APIs and events
### Data model
### Main flows and failure handling
## Alternatives considered
| Option | Pros | Cons | Why not |
|--------|------|------|---------|
## Cross-cutting concerns
- **Security:** … · **Privacy:** … · **Reliability/SLO:** … · **Observability:** … · **Cost:** …
## Rollout and migration
| Step | What | Success criteria | Rollback |
|------|------|------------------|----------|
## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
## Open questions
- <question> — owner: <…>
## Decisions requested from reviewers
- …
```

## Quality checks
- Every "as is" statement about existing systems cites a doc, ticket or file; unknowns are open questions.
- Goals are testable; at least one non-goal is listed.
- At least two real alternatives, compared on the same criteria.
- Every rollout step has a rollback; any irreversible step is flagged in bold.
- Each cross-cutting concern has content or an explicit "not applicable because…".
- No invented SLO, volume, cost or system name; targets are labeled as proposals.

## Guardrails
- Do not invent internal platforms, standards or SLOs; search Confluence/Drive or ask.
- New processing of personal data or a new AI component must be flagged for privacy or AI risk review (point to
  `gdpr-processing-check` or `ai-use-case-risk-screen`).
- Never include credentials, internal hostnames with secrets, or real customer data in examples.
- The doc proposes; reviewers decide. Do not mark it Approved.
