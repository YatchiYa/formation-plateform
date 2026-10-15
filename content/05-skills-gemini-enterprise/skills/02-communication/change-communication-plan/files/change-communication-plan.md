---
name: change-communication-plan
description: "Builds a communication plan for a change (new tool, process, organization, store concept, policy): impact map by audience, ADKAR stage per audience, key messages, channel and messenger choice, a week-by-week timeline from pre-announcement to reinforcement, manager toolkit, feedback loops and adoption indicators. Use whenever a change will affect teammates in stores, warehouses or offices and someone must plan how and when to communicate it, even if they only ask 'how do we announce this' or 'who should we tell first'. Triggers - change communication plan, comms plan, change management, rollout communication, ADKAR, how to announce a change, stakeholder communication, plan de communication, conduite du changement, accompagnement du changement, plan de comm, comment annoncer ce changement, déploiement auprès des équipes."
---

# Change communication plan

Plans who hears what, from whom, when and through which channel, so that a change is understood, accepted and
actually adopted rather than just announced.

## When to use
- A new tool, process, rule or organization rolls out to several teams, stores or countries.
- A sensitive change (reorganization, schedule change, closure, new way of working) needs careful sequencing.
- A rollout is underway but adoption is low, and the comms must be re-planned.
- Not for: writing a single announcement (use `internal-announcement-writer`), mapping stakeholders' power and
  interest for a project (use `stakeholder-map`), writing the FAQ only (use `faq-builder`), or a training program
  design (use `learning-path-designer`).

## Inputs
- The change: what, why, scope, go-live date or phases (required).
- Affected populations: e.g. store teammates, store managers, warehouse, HQ functions, customers, partners (required).
- Sponsor and project owner (optional; placeholders if unknown).
- Constraints: embargo, employee-representative consultation, peak seasons to avoid (optional).

## Sources
1. **Drive / Confluence**: project charter, decision record, rollout plan, previous change plans and their
   lessons learned, comms templates.
2. **Jira**: rollout milestones, phases and pilot sites.
3. **Calendar**: existing rituals usable as channels (team meetings, store huddles, management committees, town halls).
4. **Gmail / Chat / Slack**: early reactions, questions and concerns already expressed about the change.
5. **Databricks / Tableau**: adoption data if a tool already exists (logins, usage), to set indicators.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Map impact per audience.** For each population: what changes for them concretely (tasks, tools, schedule,
   role), impact level (high / medium / low), likely concerns ("more work during the peak?", "is my job changing?").
2. **Set the ADKAR target per audience** and the comms objective for each stage:
   - Awareness (why change, why now) → Desire (what's in it for me, what happens if we don't) →
     Knowledge (how to do it) → Ability (practice, support) → Reinforcement (recognition, results, fixing issues).
   Comms mainly serves Awareness and Desire; Knowledge and Ability need training and support, Reinforcement needs
   follow-up.
3. **Write the message house**: one umbrella message (≤ 20 words), 3 pillars with proof points, and the "what it
   means for you" line per audience. Prepare honest answers for the hard questions.
4. **Choose messenger and channel by impact**: high-impact news comes from the direct manager, face to face first
   (huddle, team meeting), then written; sponsor carries the "why"; peers and champions carry the "how". Email,
   Chat/Slack and intranet support but do not replace conversations.
5. **Sequence the timeline** (T = go-live): leaders and managers first (T-4 to T-3 weeks, with toolkit) →
   affected teams (T-3 to T-2) → wider organization (T-2 to T-1) → go-live day messages → reinforcement at T+2
   and T+6 weeks. Avoid peak commercial periods for store teams when possible.
6. **Build the manager toolkit**: briefing note, 5 talking points, FAQ, what they can and cannot say, escalation contact.
7. **Design feedback loops**: question channel, pulse question after 2 weeks, champions network, issue log; and
   **adoption indicators** (usage, completion of training, ticket volume, pulse score) with owners.
8. List risks (rumor, leak, overloaded period, inconsistent manager messages) with mitigations.

## Output format
```markdown
# Change communication plan — <change>
_Go-live: <date> · Sponsor: <name/placeholder> · Owner: <…>_

## Impact by audience
| Audience | What changes for them | Impact | Main concerns | ADKAR focus |
|----------|----------------------|--------|---------------|-------------|

## Message house
**Umbrella:** …
| Pillar | Proof point | Source |
|--------|-------------|--------|
**What it means for you:** <audience → one line each>

## Timeline
| When (T±) | Audience | Message / objective | Channel | Messenger | Material | Status |
|-----------|----------|---------------------|---------|-----------|----------|--------|

## Manager toolkit
- Briefing note · talking points · FAQ · escalation contact

## Feedback & adoption
| Indicator | Target | Source | Owner | Check date |
|-----------|--------|--------|-------|------------|

## Risks
- <risk> → <mitigation>
```

## Quality checks
- Every affected audience appears in the impact table and in the timeline at least once.
- Managers receive the information before their teams for every high-impact audience.
- Each message has one channel, one messenger and one date; nothing is "to be communicated" without a slot.
- The plan includes at least one feedback loop and one adoption indicator with an owner.
- Facts (dates, scope, figures) come from cited sources; unknowns are placeholders.

## Guardrails
- For changes affecting jobs, schedules or working conditions, flag that HR and, depending on the country, employee
  representatives may need to be informed or consulted before any announcement; do not decide this sequence alone.
- No promises that the sources do not support ("no job will change", "no extra workload").
- Keep embargoed information out of drafts meant for wider audiences.
- Draft only: sending messages or booking sessions requires the user's confirmation.
