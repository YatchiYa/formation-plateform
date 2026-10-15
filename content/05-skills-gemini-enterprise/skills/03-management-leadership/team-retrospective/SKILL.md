---
name: team-retrospective
description: "Prepares and synthesizes team retrospectives: picks the right format for the moment (Start-Stop-Continue, 4L, Sailboat, Mad-Sad-Glad, Starfish, timeline), writes the facilitation plan with prompts and timings, pre-fills the period's facts from Jira, GitHub and Calendar, then turns retro notes or a Meet transcript into themes, root causes and 1-3 owned actions with a check on last retro's actions. Use whenever a team closes a sprint, project, season or busy period, or someone pastes retro post-its or notes, even if they say 'debrief' or 'bilan'. Triggers - retro, retrospective, sprint retro, run a retro, retro notes, what went well, rétrospective, rétro d'équipe, bilan d'équipe, faire le bilan, débrief de fin de saison, animer une rétro."
---

# Team retrospective

Makes retros useful again: the right format for the team's mood, facts on the table, and a short list of actions that
actually get done.

## When to use
- End of a sprint, project phase, store operation (sales period, inventory, back to school) or season.
- The team's retros feel repetitive and the facilitator wants a new format.
- Raw retro output (post-its, digital board export, notes, Meet transcript) needs to become actions.
- Not for: a formal project lessons-learned report for a sponsor (use `lessons-learned`), a blameless incident
  analysis (use `incident-postmortem`), or a multi-session workshop or offsite (use `workshop-designer`).

## Inputs
- Mode: prepare a retro, or synthesize one (required; infer from what the user gives).
- Team, period covered and duration available (required for prepare; default 60 min).
- Retro notes, board export or transcript (required for synthesize).
- Team mood or known tension (optional) and remote/on-site setup (optional, default: on-site).

## Sources
1. **Drive**: previous retro notes for this team (the last 2–3) and their action lists; Meet transcripts of the
   retro if it was recorded.
2. **Jira**: sprint or period report — committed vs done, carry-over, bugs created, blocked time, scope added
   mid-sprint.
3. **GitHub**: PR cycle time, PRs open > 5 days, incidents or reverts in the period (tech teams).
4. **Calendar**: meeting load of the team in the period, key events (launch, peak days, absences).
5. **Slack and Chat**: the team channel's notable moments (incidents, celebrations) to build the timeline.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
**Prepare**
1. Choose the format with this rule, and say why:
   - New team or first retro → Start-Stop-Continue (simple, safe).
   - Routine sprint, neutral mood → 4L (Liked, Learned, Lacked, Longed for).
   - Big goal ahead, risks visible → Sailboat (wind, anchors, rocks, island).
   - Tension or tiring period → Mad-Sad-Glad (lets emotions out before solutions).
   - Mature team, fine-tuning → Starfish (keep, more, less, start, stop).
   - Long project or season → Timeline (high/low points on a curve, then patterns).
2. Build the agenda on the five phases (Derby & Larsen): set the stage (5–10 %), gather data (30 %), generate
   insights (25 %), decide what to do (25 %), close (10 %). Open with the Prime Directive (Norm Kerth), in the
   team's language.
3. Pre-fill **facts of the period** (max 8) from sources, and **last retro's actions** with status — reviewing them
   first keeps the team accountable for the new ones.
4. Add facilitation prompts, a check-in question, the voting method (3 dots per person) and the safety rule:
   ideas are about the system, not about people.

**Synthesize**
5. Cluster notes into themes (affinity grouping); count items per theme and keep the dot votes if present.
6. For the top 2–3 themes, ask "why" until the cause is something the team controls (max 5 whys); mark causes
   outside the team's control as "escalate".
7. Write 1–3 **actions**: verb + specific change + owner + due date + how we will know it worked. Reject vague
   actions ("communicate better") and rewrite them ("Post blocking issues in #team-channel before 10:00 daily").
8. Record what goes to the next retro and what is escalated to whom.

## Output format
```markdown
## Retro plan — <Team>, <period> · <duration> min · format: <format> (why: …)
| Time | Phase | Activity & prompt | Output |
|------|-------|-------------------|--------|
_Facts of the period:_ … · _Last actions:_ <action — done/partly/not done>
_Check-in question:_ …

## Retro synthesis — <Team>, <date>
### Themes
| Theme | Items | Votes | Example (verbatim, unattributed) |
|-------|-------|-------|----------------------------------|
### Root causes
- <theme> → <cause> (team-controlled | escalate to <role>)
### Actions (max 3)
| Action | Owner | Due | Success signal |
|--------|-------|-----|----------------|
### Last retro's actions
- <action> — <status>
### Escalations
- …
```

## Quality checks
- Format choice is justified by the stated rule, and the agenda timings add up to the duration.
- No more than 3 actions; each has an owner, a date and an observable success signal.
- Every theme cites its count of items; nothing appears in the synthesis that is not in the notes.
- Verbatims are unattributed and contain no names of people being criticized.
- Last retro's actions are reviewed, or the absence of previous notes is stated.

## Guardrails
- Retros are psychologically safe spaces: do not attribute quotes to individuals, and do not turn retro content into
  individual performance evidence.
- If the notes reveal harassment, discrimination or safety issues, take them out of the retro synthesis and advise
  the user to handle them with HR privately.
- Do not create Jira issues or post the synthesis until the user confirms; offer Jira drafts for the actions.
