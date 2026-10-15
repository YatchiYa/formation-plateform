---
name: backlog-grooming
description: "Grooms a Jira backlog before refinement: finds duplicates, stale and zombie tickets, vague stories without acceptance criteria, oversized items to split, missing dependencies and bugs without severity, scores each item against INVEST and a Definition of Ready, and produces a refinement agenda with sizing questions and proposed edits. Use whenever a team prepares a refinement or grooming session, the backlog feels messy or too long, or a product owner asks what is ready for the next sprint, even if they only say 'clean up my backlog'. Triggers - groom the backlog, backlog refinement, clean up Jira, what's ready for sprint, backlog health, affinage du backlog, nettoyer le backlog, préparer le refinement, tickets prêts pour le sprint, grooming Jira."
---

# Backlog grooming

Gives a product owner or tech lead a cleaned-up view of a Jira backlog and a focused refinement agenda, so the team
spends its refinement time on decisions, not on reading tickets.

## When to use
- Before a refinement session, to prepare which items to discuss and what to ask.
- The backlog has grown past what anyone reads (hundreds of items, old tickets nobody owns).
- The team keeps pulling items into the sprint that turn out not to be ready.
- Not for: choosing the sprint content against capacity (use `sprint-planning-assistant`), writing new stories from
  scratch (use `user-story-writer`), or rewriting one bug (use `bug-report-writer`).

## Inputs
- Jira project, board or JQL filter (required).
- Scope (optional, default: top 50 items by backlog rank, plus everything not updated for 180 days).
- Definition of Ready (optional, default: the team's DoR from Confluence, else the one in the Reference section).
- Upcoming sprint goal or roadmap priority (optional) to weight what to refine first.
- Jira not connected: never ask for permission or confirmation to proceed. Say « Jira not connected » in one line,
  ask once for a CSV/export or pasted list (key, summary, status, points, updated date, description), and show the
  Output format with [to confirm] counts plus the JQL the export should use.

## Sources
1. **Jira**: issues in scope with summary, description, type, status, rank, story points, labels, components, epic,
   fix version, assignee, reporter, created and updated dates, links and comment count. Suggested JQL:
   project = KEY AND statusCategory != Done ORDER BY Rank ASC.
2. **Confluence**: the team's Definition of Ready and Done, working agreements, roadmap page.
3. **GitHub**: open or merged PRs referencing backlog keys (work done but ticket still open, or work started on an
   unrefined item).
4. **Slack and Google Chat**: only for a specific ticket the user asks about, to recover missing context.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Pull the items and compute per item: age, days since update, has description, has acceptance criteria, estimated
   or not, linked epic, open blockers.
2. **Duplicates**: group items with near-identical summaries or the same error message, component and intent. Propose
   which one to keep (the most complete, or the oldest with history) and why.
3. **Stale and zombie**: not updated for 180+ days and not in the next two sprints of the roadmap. Propose close
   ("won't do, reopen if needed"), merge, or revive with a reason. Never propose closing an open bug with S1/S2
   severity without a human decision.
4. **Already done**: items whose work appears in merged PRs; propose verifying and closing.
5. **INVEST check** for the top items: Independent, Negotiable, Valuable, Estimable, Small, Testable. Record each
   failing letter with one line of evidence.
6. **Too big**: items estimated above the team's split threshold (default: more than half a sprint, or > 8 points)
   get a split proposal using a pattern: by workflow step, by business rule, by data variation, by platform (web /
   app / store POS), happy path first then edge cases, spike then build.
7. **Not ready**: missing acceptance criteria, unclear user or value, unknown dependency (another team's API, a
   legal or data privacy review, a design). Write the exact question to resolve each gap.
8. Build the **refinement agenda**: the 5–10 items with the highest rank or roadmap weight that are closest to ready,
   each with the question to answer and a timebox.

## Output format
```markdown
**Backlog health — <project/board> · <date>**
<N> items reviewed · <n> ready · <n> need refinement · <n> to close/merge · <n> too big
_Definition of Ready used: <link or "default">_

### Refinement agenda (<total minutes>)
| # | Key | Summary | Question to settle | Timebox |
|---|-----|---------|--------------------|---------|

### Not ready — what is missing
| Key | INVEST fails | Gap | Question / proposed edit |
|-----|--------------|-----|--------------------------|

### Split proposals
- **<KEY> <summary>** (<points>) → pattern: <…>
  1. <slice 1, valuable alone>
  2. <slice 2>

### Duplicates
| Keep | Close as duplicate | Reason |
|------|--------------------|--------|

### Stale / possibly done (proposals, human decides)
| Key | Last update | Signal | Proposal |
|-----|-------------|--------|----------|

### Backlog hygiene notes
- <e.g. 40% of bugs have no severity; 12 items have no epic>
```

## Quality checks
- Every item named has a Jira key and link; no item is invented or paraphrased beyond recognition.
- Every split slice is independently valuable and testable (no "backend part / frontend part" split unless justified).
- Every "not ready" item has a concrete question, not just "needs more detail".
- Close proposals state their signal (age, duplicate key, merged PR) and exclude S1/S2 bugs.
- Counts in the header match the tables.

## Guardrails
- Proposals only. Do not close, merge, re-rank, re-estimate or edit tickets until the user confirms, item by item or
  as an explicit batch.
- Do not estimate story points for the team; estimation belongs to the people doing the work. Suggest questions that
  make estimation possible.
- Do not judge individuals from ticket ownership or age (no "X's tickets are always vague").

## Reference — default Definition of Ready
Clear user and value ("so that"), testable acceptance criteria (Given/When/Then for behavior), dependencies identified
and owned, UX or API contract available if needed, small enough for one sprint, no open legal, privacy or security
question, and the team can estimate it.
