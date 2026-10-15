---
name: workshop-designer
description: "Designs a workshop, offsite, seminar or team day from its objectives: expected outputs, diverge-converge flow (double diamond), minute-by-minute agenda with proven activities (1-2-4-All, crazy 8s, dot voting, how-might-we, impact-effort matrix, fishbone), energy curve, roles, materials list for on-site or remote, pre-work and invitation text, and the follow-up plan. Use whenever someone organizes a workshop, ideation session, team offsite, kickoff, séminaire or brainstorm, even if they only give a theme and a duration. Triggers - design a workshop, plan an offsite, workshop agenda, brainstorm session, facilitation plan, kickoff workshop, concevoir un atelier, animer un atelier, organiser un séminaire, journée d'équipe, déroulé d'atelier, idéation, team building."
---

# Workshop designer

Turns a vague "let's do a workshop on X" into a facilitation plan that produces concrete outputs and keeps people
engaged from the first to the last minute.

## When to use
- A team needs to generate ideas, solve a problem, align on priorities or build a plan together.
- A manager organizes an offsite, team day or season kickoff.
- A project kicks off and stakeholders must agree on scope and ways of working.
- Not for: a regular sprint or period retrospective (use `team-retrospective`), a meeting agenda under 60 minutes
  (use `meeting-agenda-builder`), or a training program (use `learning-path-designer`).

## Inputs
- Goal and the outputs expected at the end (required — if only a theme is given, propose outputs, label them
  *assumed* and build the full plan on them; the user confirms after the draft).
- Duration (required). Number and profile of participants (optional, default: the named team, 8–12 people, stated
  as an assumption).
- Format: on-site, remote or hybrid (optional, default: on-site).
- Constraints: location, budget, language, accessibility needs (optional).

## Sources
1. **Drive and Confluence**: background docs for pre-reads (strategy, data, previous workshop outputs), facilitation
   templates the team already uses.
2. **Databricks (SQL MCP or Polco) and Tableau**: 3–5 facts to open the workshop with data (e.g. sport category
   trend, customer reviews volume), shown with source.
3. **Calendar**: participants' availability and conflicts on the target date.
4. **Gmail, Chat and Slack**: the request thread and expectations expressed by the sponsor.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Turn the goal into **2–3 tangible outputs** ("a ranked list of 5 service ideas with an owner each", not
   "alignment"). Each agenda block must contribute to one output.
2. Choose the **flow**: double diamond (discover → define → develop → deliver) for problem solving; open → explore
   → close for alignment; past → present → future for kickoff and offsites.
3. Pick **activities** per phase:
   - Diverge: 1-2-4-All (everyone speaks), Crazy 8s (8 ideas in 8 minutes), How Might We questions, brainwriting
     (best for introverts and hierarchy-heavy groups), customer journey walk.
   - Explore: fishbone (causes), empathy map, gallery walk, field visit (e.g. a store aisle or the repair workshop).
   - Converge: dot voting (3 dots), impact/effort matrix, MoSCoW, fist-to-five for consent.
   - Commit: who-what-when board, one-sentence pledges.
4. Build the **timed agenda** with: check-in, purpose and rules, activity blocks, a break every 75–90 minutes,
   a physical or sport activity in long days (energizer after lunch), and a check-out. Plan 10 % buffer. Put the
   hardest thinking in the morning and convergence before the energy dip.
5. Assign **roles**: facilitator, sponsor (opens and closes, then steps back), timekeeper, note-taker, and say who
   decides in case of disagreement.
6. List **materials** for the format (post-its, markers, flipcharts, dots, timer; or a digital whiteboard or Slides, breakout
   rooms) and the room setup.
7. Write the **pre-work** (≤ 20 min) and the **invitation** text, then the **follow-up**: synthesis within 48 h,
   owners, check-in date.

## Output format
```markdown
# Workshop — <title>
**Goal:** … · **Outputs:** 1) … 2) … · **When/where:** … · **Participants:** <n>, <profiles>
**Flow:** <double diamond | open-explore-close | past-present-future>

## Agenda
| Time | Block | Activity & instructions | Output | Who leads |
|------|-------|-------------------------|--------|-----------|
| 09:00–09:15 | Check-in | … | | |

## Roles
- Facilitator: … · Sponsor: … · Timekeeper: … · Note-taker: … · Decision rule: …

## Materials & setup
- …

## Pre-work (≤ 20 min)
- …

## Invitation (ready to send)
<text>

## After the workshop
- Synthesis by <date> · owners · check-in on <date>
```

## Quality checks
- Every agenda block maps to at least one stated output.
- Timings add up to the stated duration with breaks every ≤ 90 minutes and ~10 % buffer.
- Each diverge phase is followed by a converge phase.
- Every activity has instructions a facilitator could run without knowing the method.
- Data used in the opening has a source.

## Guardrails
- Make activities inclusive: offer seated alternatives to physical activities, avoid exercises that require sharing
  personal or private information, and ask about accessibility needs in the invitation.
- Do not invent budgets, venues or internal programs; leave placeholders such as "<venue>" when unknown.
- Do not send invitations or book rooms without the user's confirmation.
