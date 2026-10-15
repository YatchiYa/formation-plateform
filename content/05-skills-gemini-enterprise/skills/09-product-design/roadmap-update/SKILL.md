---
name: roadmap-update
description: "Prepares a product roadmap update for stakeholders in now, next, later format: outcomes rather than feature lists, what shipped and what it changed, what moved and why, confidence per item, dependencies, risks and explicit asks, adapted to the audience (leadership, business teams, stores, partner teams). Pulls status from Jira, Confluence, Slack and dashboards. Works for digital products and physical product ranges. Use whenever a product manager has to present, refresh or explain a roadmap or a change of plan, even if they only ask 'what do I tell stakeholders this month'. Triggers - roadmap update, now next later, roadmap review, product roadmap for stakeholders, change of plans, mise à jour de la roadmap, feuille de route produit, point roadmap, présenter la roadmap, glissement de planning, arbitrages roadmap."
---

# Roadmap update

Gives stakeholders a roadmap they can trust: organized by the problems being solved, honest about confidence, and
clear about what changed since last time and what the team needs from them.

## When to use
- Monthly or quarterly roadmap communication to leadership, business or store networks.
- A priority shift, a delay or a new constraint must be explained without losing trust.
- Preparing a roadmap review or a quarterly planning session.
- Not for: a weekly project status with RAG (use `project-status-report`), a steering committee pack with budget
  decisions (use `steering-committee-pack`), setting OKRs (use `okr-builder`) or user-facing release notes (use
  `release-notes-writer`).

## Inputs
- Product or range and the period covered (required).
- Previous roadmap version (optional, default: search Drive/Confluence for the latest one; needed to show changes).
- Audience (optional, default: leadership; also: business teams, stores, engineering, partners).
- Strategy or OKRs the roadmap serves (optional, default: search sources).

## Sources
1. **Confluence and Drive**: last roadmap version, strategy, OKRs, decision records; keep the team's format if one exists.
2. **Jira**: epics and their status, fix versions, target dates, recently done epics, blocked issues and
   cross-team links (dependencies).
3. **Databricks (SQL or Polco) and Tableau**: outcome metrics for shipped items (before/after, with the query or
   dashboard link), so "shipped" says what it changed.
4. **Slack, Chat and Gmail**: decisions, escalations and requests from stakeholders since the last update.
5. **GitHub**: releases if Jira is not up to date for a digital product.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Anchor on outcomes**: list the 2–4 product outcomes or OKRs. Every roadmap item must serve one; items that serve
   none go to a "parked" list or need a justification.
2. **Classify items** by horizon, not by date:
   - **Now**: in delivery, committed, high confidence; may carry dates.
   - **Next**: discovery done or in progress, intended, medium confidence; quarter at most.
   - **Later**: problems worth solving, low confidence; no dates.
   Phrase items as problems or outcomes ("Help beginners choose the right running shoe size online"), with the
   solution in a sub-line if known.
3. **Diff with the previous version**: added, removed, moved (horizon or date), shipped. For every move, give the
   reason category (new evidence, dependency, capacity, strategy change, technical discovery, supplier or industrial
   constraint) and the source.
4. **Report shipped items with impact**: metric movement with source, or "too early to measure, review on <date>".
5. **Set confidence** per Now/Next item: high, medium, low, with one line on what drives it.
6. **List dependencies and risks** that could move the Now items, with owner.
7. **Write explicit asks**: decisions, resources, data, feedback, each with a deadline.
8. **Adapt to the audience**: leadership gets outcomes, changes and asks on one screen; business and store
   audiences get what changes for them and when; engineering gets dependencies and sequencing.

## Output format
```markdown
# Roadmap update — <product / range>, <period>
_Audience: <…> · Previous version: <link> · Sources: <links>_

## Headline
<2–3 sentences: progress on outcomes, biggest change, main ask>

## Outcomes we serve
1. <outcome / OKR> — <status in one line>

## Now / Next / Later
| Horizon | Item (problem or outcome) | Serves | Confidence | Note |
|---------|---------------------------|--------|-----------|------|
| Now | | O1 | high | <date if committed> |
| Next | | O2 | medium | |
| Later | | O1 | low | |

## What changed since <last update>
| Item | Change | Why | Source |
|------|--------|-----|--------|
| | moved Now → Next | dependency on <team> | <link> |

## Shipped & impact
- <item> — <metric movement (source) / review on <date>>

## Dependencies & risks
| Item | Risk / dependency | Owner | Mitigation |
|------|-------------------|-------|-----------|

## Asks
- <decision / resource / input> — from <whom> — by <date>
```

## Quality checks
- Every item maps to an outcome; nothing in Later has a date.
- Every change since the last version has a reason and a source.
- Shipped items show an impact with source or an explicit review date, never an assumed effect.
- Confidence is stated for every Now and Next item.
- Asks name who and by when.
- The headline reads on its own in under 30 seconds.

## Guardrails
- Never promise dates the team has not committed to; dates only for Now items with a Jira or plan source.
- Do not invent metric movements or attribute a business result to a release without data.
- Keep confidential items (unannounced products, supplier names, partner negotiations) out of versions meant for
  wide audiences; ask the user which items are confidential when the audience is broad.
- Do not post or send the update; give drafts for each channel on request and send only after confirmation.
