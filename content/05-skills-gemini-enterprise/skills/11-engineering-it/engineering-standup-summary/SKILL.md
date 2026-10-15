---
name: engineering-standup-summary
description: "Builds an engineering team standup summary from real activity in Jira and GitHub (plus Slack or Chat): per person or per work item, what moved since the last standup, what is planned today, blockers and items waiting on someone, PRs waiting for review, aging work in progress, and risks to the sprint goal. Async-ready for posting or as a one-screen board for the live standup. Use whenever a team lead, scrum master or engineer prepares a daily standup, an async standup post or wants to know where the sprint stands today, even if they just ask 'what did the team do yesterday'. Triggers - standup summary, daily standup, async standup, what did the team do yesterday, sprint status today, blockers, résumé du daily, préparer le daily, point quotidien équipe, avancement du sprint, qui est bloqué."
---

# Engineering standup summary

Gives a team a factual, one-screen standup built from what actually moved in Jira and GitHub, so the meeting is spent
on blockers and coordination instead of status recitation.

## When to use
- Before the daily standup, to walk the board with real data.
- For an async standup in Slack or Chat when the team is distributed or the meeting is skipped.
- When a lead or scrum master wants to see if the sprint goal is at risk today.
- Not for: a weekly status for stakeholders (use `project-status-report`), the user's own weekly reflection (use
  `weekly-review`), or planning the next sprint (use `sprint-planning-assistant`).

## Inputs
- Team board, Jira project or JQL, and the GitHub repos (required; inferred from the user's recent activity if
  possible).
- Window (optional, default: since the previous workday standup; Monday covers Friday to now).
- Layout (optional, default: walk the board right to left by work item; per-person layout on request).
- Sprint goal (optional, default: read from the active Jira sprint).

## Sources
1. **Jira**: the active sprint: issues with status transitions in the window, assignee, flags or Blocked status,
   linked blockers, time in current status, sprint goal and end date; new issues added mid-sprint.
2. **GitHub**: PRs opened, merged, or with new reviews in the window; PRs waiting for review and for how long; failed
   CI on main as reported by GitHub; commits referencing sprint issue keys.
3. **Slack and Google Chat**: the team channel and async standup thread for blockers or help requests mentioned in
   words.
4. **Calendar**: team members' declared absences or out-of-office (only presence, never the reason).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Collect events in the window and attach each to a Jira issue (via key in branch, PR title or commit). Activity
   without a ticket goes into "Untracked work".
2. **Moved**: issues that changed status, PRs merged, reviews given. One line each, by issue, not by event.
3. **In progress**: issues In Progress or In Review with their age in that status. Flag aging WIP (default: in the
   same status for more than 2 working days, or longer than half the sprint for the story size).
4. **Waiting on someone**: PRs awaiting review over 1 working day, issues blocked by another team, questions
   unanswered in the channel. Name the item and the role it waits on.
5. **Blockers**: explicit (flag, Blocked status, linked blocker) and implicit (red CI on main, dependency ticket not
   started). Propose who could unblock.
6. **Today**: what each in-progress item needs next, inferred from status ("needs review", "ready to deploy");
   people's own plans only if they posted them.
7. **Sprint goal check**: days left, items remaining vs done, scope added mid-sprint; say "on track", "at risk" or
   "off track" with the reason. This is about the work, not about individuals.
8. Draft an async post version if requested, ≤ 15 lines.

## Output format
```markdown
**Standup — <team> · <date>** · Sprint <name>, day <d>/<D> · Goal: <goal> → **<on track | at risk | off track>**
_Window: <from> → <now> · Sources: Jira ✓ · GitHub ✓ · Slack ✗ (not connected)_

### Needs the team now
- 🔴 <blocker> — <KEY> · waiting on <role/team> since <date> · suggested unblock: …
- ⏳ <PR #n> waiting for review <age> — <KEY>

### Board (right to left)
| Item | Status | Age in status | Moved since last standup | Next |
|------|--------|---------------|--------------------------|------|

### Done since last standup
- <KEY> <summary> ([PR #n](link))

### Untracked work
- <PR or commit without ticket>

### Sprint risk
- <scope added, aging items, red CI on main>
```

## Quality checks
- Every line links to a Jira issue, PR or message; no activity is invented or extrapolated from silence.
- Ages are computed from timestamps and expressed in working days.
- Blockers and waiting items name the item and what it waits on, not who is "slow".
- The sprint goal verdict has a stated reason based on remaining work and days left.
- The output fits on one screen (≤ 25 rows).

## Guardrails
- Not a performance tool: no per-person activity counts, commit counts, rankings or "who did nothing" lines. Low
  visible activity can mean pairing, design, support or leave.
- Absences show as "away" only, never with a reason.
- Draft only. Do not post in Slack or Chat, move tickets or ping people until the user confirms.

## Example
Input: « Prépare le daily de l'équipe stock API »
→ Output in French. Top of the summary: « 🔴 STOCK-231 bloqué depuis 2 jours ouvrés, en attente du contrat d'API de
l'équipe POS — proposition : le PO relance l'équipe POS avant midi » and « ⏳ PR #418 (réservation au panier) en
attente de revue depuis 1,5 jour ». Sprint verdict: at risk, because 3 of 8 goal items are still in progress with
2 days left and one item was added mid-sprint.
