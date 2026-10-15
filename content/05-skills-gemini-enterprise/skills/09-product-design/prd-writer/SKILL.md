---
name: prd-writer
description: "Writes a product requirements document for a digital feature (Company app, e-commerce site, store or teammate tool): problem and evidence, target users and jobs, goals with metrics, non-goals, user stories, functional and non-functional requirements with priorities, UX notes, analytics events, dependencies, risks, rollout and open questions. Use whenever a product manager or owner needs to specify a feature, align design and engineering, or turn an idea or discovery output into something buildable, even if they ask for 'a quick spec'. Triggers - PRD, product requirements, feature spec, product spec, one-pager for a feature, spécifications fonctionnelles, rédiger une spec, cahier des charges fonctionnel, expression de besoin, fiche fonctionnalité, cadrage d'une feature."
---

# PRD writer

Produces a PRD that a designer, an engineering lead and a stakeholder can each read in five minutes and agree on:
why this feature, for whom, how success is measured, what is out of scope and what is still open.

## When to use
- A discovered opportunity must become a buildable feature for the app, the website or an internal tool.
- Engineering asks "what exactly do you want?" or stakeholders disagree on scope.
- An existing PRD needs a review for gaps before a planning event.
- Not for: physical product framing (use `product-brief`), splitting the PRD into Jira stories (use
  `user-story-writer`), the technical design (use `tech-spec-writer`), designing the A/B test (use
  `experiment-design`) or a project charter with budget and governance (use `project-charter`).

## Inputs
- Feature idea and the problem it solves (required).
- Target users and channel: app, web, store tool, back-office (required; infer from context if obvious).
- Evidence: research synthesis, data, tickets, reviews (optional, default: search sources).
- Target metric or OKR, deadline, team (optional, default: *to confirm*).
- Existing PRD to review (optional; then output a gap list plus the corrected sections).

## Sources
1. **Drive and Confluence**: PRD template of the team (use it if found), research syntheses, OKRs, design docs,
   related PRDs to avoid overlaps.
2. **Jira**: the epic or discovery ticket, linked bugs and customer-facing issues, existing stories in scope.
3. **Databricks (SQL or Polco) and Tableau**: baseline for the success metric (e.g. "checkout conversion on app,
   last 8 weeks"), segment sizes; show the query or dashboard link.
4. **GitHub**: existing code areas or feature flags touched, if the user names a repo.
5. **Slack, Chat and Gmail**: decisions and constraints from stakeholders, legal or security threads.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **State the problem** without the solution: who struggles, when, and the evidence (with strength). If evidence is
   only internal opinion, say so and add a discovery step to the open questions.
2. **Set goals and measures**: 1 primary metric (with baseline, source and target or *to confirm*), 1–2 secondary
   metrics, and 1–3 **guardrail metrics** that must not degrade (e.g. page load time, return rate, support contacts).
3. **Write non-goals** explicitly: tempting adjacent scope the team agrees not to do now.
4. **List users and jobs** (When…, I want…, so I can…) and the main user stories at epic level (story slicing is
   left to `user-story-writer`).
5. **Specify requirements** in a numbered table: ID, requirement as a testable statement ("The system shall…"),
   priority (MoSCoW: Must / Should / Could / Won't this time), linked story, notes. Cover edge cases: empty states,
   errors, offline, multiple countries and languages, accessibility (WCAG 2.2 AA), consent for tracking.
6. **Add non-functional requirements**: performance, availability, security and privacy (personal data processed
   → route to `gdpr-processing-check`), localization, accessibility, analytics events (name, trigger, properties).
7. **Map dependencies, risks and rollout**: teams and systems, risk with mitigation, release strategy (feature flag,
   % rollout, pilot country or stores), and the success review date.
8. **List open questions** with an owner each. A PRD with no open questions usually hides assumptions.

## Output format
```markdown
# PRD — <feature name>
_Status: draft v<N> · PM: <name> · Team: <team> · Epic: <Jira link> · Last update: <date>_

## TL;DR
<3 sentences: problem, solution direction, success measure>

## 1. Problem & evidence
| Evidence | Source | Strength |
|----------|--------|----------|

## 2. Goals & metrics
| Type | Metric | Baseline (source) | Target |
|------|--------|-------------------|--------|
| Primary | | | |
| Guardrail | | | |

## 3. Non-goals
- …

## 4. Users & jobs
- When …, I want …, so I can …

## 5. Requirements
| ID | Requirement | Priority | Story | Notes / edge cases |
|----|-------------|----------|-------|--------------------|
| R1 | The system shall … | Must | | |

## 6. Non-functional requirements
- Performance · Security & privacy · Accessibility · Localization · Analytics events

## 7. UX notes
- Key flows, states (empty, loading, error), links to designs

## 8. Dependencies & risks
| Item | Type | Owner | Mitigation |
|------|------|-------|-----------|

## 9. Rollout & review
- Release strategy · Pilot scope · Success review on <date>

## 10. Open questions
| Question | Owner | Due |
|----------|-------|-----|
```

## Quality checks
- The problem section contains no solution words; every evidence row has a source.
- Each metric has a baseline with source or is marked *to confirm*; at least one guardrail metric exists.
- Every requirement is testable (a tester could say pass/fail) and has a MoSCoW priority.
- Non-goals list at least two items.
- Edge cases cover errors, empty state, accessibility and multi-country/language when the feature is customer-facing.
- Every open question has an owner.

## Guardrails
- Never invent baselines, targets, traffic or revenue figures; cite or mark *to confirm*.
- Flag any processing of personal data, payment, minors' data or tracking for privacy review; the PRD does not
  conclude on legal compliance.
- Do not create Jira epics or stories; offer drafts and create them only after explicit confirmation.
- Keep customer quotes anonymized.
