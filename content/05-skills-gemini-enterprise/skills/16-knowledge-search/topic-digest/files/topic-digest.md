---
name: topic-digest
description: "Builds a digest of everything that happened on a topic, project or initiative over a period across Gmail, Chat, Slack, Drive, Confluence, Jira, GitHub and Calendar: a dated timeline, decisions made and by whom, current status, open issues and risks, who owes what, and what to watch next, with a citation for every item. Use whenever someone needs to catch up on a project, prepare to join or take over a topic, report on what happened over the last weeks, or asks 'where are we on X', even if they only name the project. Triggers - what happened on, catch me up on the project, topic digest, project history, where are we on, recap of the last weeks, qu'est-ce qui s'est passé sur, où en est-on sur, résumé du projet, historique du sujet, point sur, récap des dernières semaines."
---

# Topic digest

Gives a teammate a dated, sourced picture of a topic over a period: what happened, what was decided, where it stands
now and what is still open.

## When to use
- Joining or taking over a project, or coming back to it after weeks.
- Preparing a steering meeting, a status email or a handover on a topic.
- A manager asks "where are we on X?" and the answer is spread across tools.
- Not for: a single thread summary (use `thread-catchup`), a one-question lookup (use `cross-source-search`), the
  user's whole inbox after leave (use `back-from-leave-catchup`), or a formal RAG status report (use
  `project-status-report`).

## Inputs
- Topic or project name, with aliases, code names, Jira project key or epic, repository, channel (required name;
  aliases optional, default: discovered from first results).
- Period (optional, default: last 30 days; up to 6 months).
- Audience (optional, default: the user; "for my manager" makes it shorter).

## Sources
1. **Jira**: epics and issues of the project (created, resolved, status changes, comments with decisions).
2. **Confluence and Drive**: pages and docs created or updated in the period, meeting notes and Meet transcripts,
   decision logs.
3. **Gmail, Google Chat and Slack**: threads and channel messages mentioning the topic or its aliases.
4. **GitHub**: merged PRs, releases and issues in the related repositories.
5. **Calendar**: meetings on the topic in the period (to anchor the timeline and find notes).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Map aliases**: search the name, then collect code names, Jira keys, channel names and FR/EN variants seen in
   the first results; re-search with them.
2. **Collect events** in the period, each with date, source, actor and link: decisions, milestones reached or
   missed, scope changes, incidents, new risks, people joining or leaving the topic.
3. **Deduplicate**: one event seen in email, chat and Jira becomes one line with several links; keep the most
   authoritative source first (decision record > ticket > email > chat).
4. **Detect decisions**: explicit wording ("we decided", « on part sur », « validé », approved, Jira resolution) plus
   who decided. An idea discussed without closure is an open question, not a decision.
5. **Status now**: the latest authoritative state per workstream; if sources disagree, show both with dates.
6. **Open items**: unresolved questions, blocked issues, overdue actions, with owner and age.
7. **What to watch**: upcoming milestones, meetings and deadlines in the next 2–4 weeks.

## Output format
```markdown
**<Topic> — <period>: <one-sentence state of play>**
_Aliases searched: <…> · Sources: <status line>_

### Key decisions
| Date | Decision | Decided by | Source |
|------|----------|-----------|--------|

### Timeline
- **<YYYY-MM-DD>** — <event> ([source](…))

### Status now
| Workstream | Status | As of | Source |
|-----------|--------|-------|--------|

### Open issues and risks
- <issue> — owner: <name or "unassigned"> — open since <date> ([link](…))

### Who owes what
- <person> → <action> — due <date>

### Coming up
- <date> — <milestone / meeting / deadline>

_Not found or uncertain: <gaps>_
```

## Quality checks
- Every timeline line, decision and open issue has a date and a link.
- Decisions name who decided, from the source; undecided topics are under open issues.
- Events are deduplicated across sources.
- The period stated matches the dates shown; nothing outside the period except "Coming up".
- Conflicting statuses are shown with their dates.

## Guardrails
- Only include content the user can access; do not surface messages from private channels or mailboxes they are not
  part of.
- Leave out personal or sensitive content (HR, health, conflicts between people); describe neutrally if it affects
  the project.
- Do not attribute decisions to people without a source that shows it.
- Read only: do not post the digest or update tickets unless the user confirms.

## Example
Input: « Où en est-on sur le projet de click & collect en casiers, depuis septembre ? »
→ Output in French. Aliases found: the Jira epic key and the project channel. 4 decisions with deciders and links,
a 12-line deduplicated timeline, status per workstream (pilot, IT integration, store rollout) with « au <date> »,
3 open issues with owners and ages, and the next steering date from Calendar.
