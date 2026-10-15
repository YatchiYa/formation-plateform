---
name: calibration-prep
description: "Prepares a talent or performance calibration session for a group of teammates: one-page evidence summaries per person from the managers' reviews, a distribution view of the proposed ratings by manager and team, consistency flags (rating vs evidence, leniency or severity by manager, recency), a bias checklist for the facilitator and an agenda. Humans make every rating decision. Use whenever HR or a group of managers prepares a calibration, people review, talent review or promotion committee, even if they only ask to 'put the ratings in a table'. Triggers - calibration, calibration session, talent review, people review, promotion committee, rating consistency, session de calibrage, calibration des évaluations, revue des talents, people review, comité promotion, harmonisation des notes."
---

# Calibration prep

Gets a calibration session ready so that managers discuss evidence, apply the same standard across teams and
catch bias before ratings are final. The committee decides; this skill never proposes a rating.

## When to use
- Before a calibration or talent review where several managers compare proposed ratings.
- Before a promotion committee, to check that nominations rest on comparable evidence.
- After the session, to record changes and the rationale given by the committee.
- Not for: writing one review (use `performance-review-writer`), analyzing survey data (use
  `engagement-survey-analyzer`), or a skills inventory of a team (use `team-skills-matrix`).

## Inputs
- Population: who is calibrated, by which group of managers, for which period (required).
- Proposed ratings and review drafts or evidence per person (required; from the HR export or Drive).
- Rating scale with its official definitions (required; searched in Confluence/Drive, otherwise asked).
- Any guideline on distribution or promotion criteria (optional; used only if found in an official source).

## Sources
1. **Drive**: the calibration sheet or export, review drafts, promotion cases, last year's ratings if the user
   provides them for trend.
2. **Confluence**: rating definitions, calibration guide, promotion criteria for the job family.
3. **Calendar**: session date and attendees, to size the agenda (time per person).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Normalize the data**: one row per person: ID or initials, role, level, manager, team, proposed rating,
   evidence summary, review date, time in role. Mark missing reviews.
2. **Evidence summary per person** (≤ 6 lines): top 2 results against goals, 1–2 behaviors, growth area, each with
   source. Written in neutral language, no adjectives about personality.
3. **Consistency flags** (facts, not judgments):
   - *Rating vs evidence*: proposed rating language vs official definition (e.g. "exceeds" with no result above
     the goal) → flag `evidence thin`.
   - *Manager pattern*: a manager whose average proposed rating differs by ≥ 0.5 point (on a 5-point scale) from
     the group average with ≥ 5 people → `possible leniency/severity, discuss`.
   - *Recency*: evidence mostly from the last quarter.
   - *Comparable roles*: same role and level with similar evidence but different ratings → pair for discussion.
   - *Change vs last year* of ≥ 2 levels without a documented reason.
4. **Distribution view**: counts per rating, overall and per manager; if ≥ 5 people, per team. Show the official
   guideline next to it only if one exists. Never force a curve.
5. **Equity check (aggregate only)**: if HR provides group-level demographic data under its own authorization,
   compare rating distributions by group for groups ≥ 5 people and flag gaps for HR. Never infer gender, age or
   origin from names or photos.
6. **Bias checklist** for the facilitator: halo/horns, recency, similarity ("reminds me of me"), central tendency,
   leniency, visibility bias (HQ vs remote or night-shift warehouse teams, part-time teammates), leave
   periods treated as gaps, loudest-voice effect in the room.
7. **Agenda**: flagged cases first, time-box (≈ 3 min per non-flagged person, 8 per flagged one), decision log.

## Output format
```markdown
# Calibration prep — <population>, <period> · session <date>
_Sources: <export, definitions>. People: <n> · managers: <n> · missing reviews: <n>_
_The committee decides every rating. Flags are prompts for discussion, not conclusions._

## Distribution
| Rating | Overall | <Manager A> | <Manager B> | Guideline (if official) |
|--------|---------|-------------|-------------|-------------------------|

## Cases to discuss first
| Person | Manager | Proposed | Flag | Evidence pointer |
|--------|---------|----------|------|------------------|

## Evidence summaries
### <ID> — <role, level> · manager <X> · proposed <rating>
- Results: … · Behaviors: … · Growth: … ([source](…))

## Facilitator bias checklist
- [ ] …

## Agenda (<duration>)
1. Rules and definitions (5 min) · 2. Flagged cases · 3. Others · 4. Decision log review

## Decision log (to fill in session)
| Person | Proposed | Final | Rationale (evidence) | Decided by |
|--------|----------|-------|----------------------|-----------|
```

## Quality checks
- Every person has an evidence summary with at least one source, or is marked *review missing*.
- Every flag cites the rule that raised it and the data behind it.
- No final rating, recommendation or ranking appears anywhere outside the empty decision log.
- No group below 5 people is shown in a demographic or team-level breakdown.
- No protected characteristic is inferred; demographic analysis appears only if HR supplied the data.

## Guardrails
- EU AI Act high-risk: decisions on promotion, pay or termination are made by the committee. The skill organizes
  evidence and never scores, ranks or recommends.
- Ratings and reviews are confidential: share the pack only with the session's authorized participants, as the user
  confirms. No copy in open channels.
- Never invent a distribution guideline, promotion criterion or rating definition.
- Leave, part-time and accommodated work are not performance gaps; flag any summary that implies otherwise.
- Works council or local consultation rules may apply to the process; refer to HR, do not assume.
