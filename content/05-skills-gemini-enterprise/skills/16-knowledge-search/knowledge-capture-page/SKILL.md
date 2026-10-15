---
name: knowledge-capture-page
description: "Turns scattered knowledge (Chat or Slack threads, email chains, meeting notes, Meet transcripts, Jira comments) into a clean, reusable Confluence or Google Docs page: a decision record (context, options, decision, rationale, consequences) or a how-to (prerequisites, numbered steps, troubleshooting), with owner, review date, sources and open points, after checking that no page already exists. Use whenever an answer or decision is buried in a thread and should be written down, someone says 'we should document this', or the same question keeps coming back, even if they just paste a thread. Triggers - document this, write a Confluence page, capture this decision, turn this thread into a page, how-to page, documente ça, rédige une page Confluence, formaliser la décision, transformer ce fil en page, page de procédure, capitaliser."
---

# Knowledge capture page

Turns knowledge buried in conversations into a page the next teammate will find and trust, with its sources and an
owner who keeps it alive.

## When to use
- A decision was made in a thread or meeting and must be recorded.
- A question keeps coming back in a channel and the answer should become a how-to.
- Tribal knowledge must be written down before someone leaves or changes role.
- Not for: meeting actions and recap email (use `meeting-notes-to-actions`), formal architecture decisions (use
  `architecture-decision-record`), controlled procedures with roles and controls (use `sop-writer`), customer-facing
  help articles (use `kb-article-writer`), or a long-form decision memo for approval (use `decision-memo`).

## Inputs
- The material: thread links, notes, transcript, tickets (required).
- Page type (optional, default: inferred; decision record if a choice was made, how-to if steps are described).
- Destination: Confluence space and parent page, or Drive folder (optional, default: ask once at the end).
- Owner of the page (optional, default: "to assign").

## Sources
1. **Google Chat, Slack and Gmail**: the threads provided, and replies after them that may change the outcome.
2. **Drive**: meeting notes, Meet transcripts, related docs.
3. **Confluence**: existing pages on the topic (to update instead of duplicating), space templates and conventions.
4. **Jira and GitHub**: tickets and PRs that implement or reference the decision or procedure.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Check for an existing page** in Confluence and Drive (FR and EN titles, synonyms). If one exists, propose an
   update with the changes instead of a new page.
2. **Extract** from the material: the question or problem, options discussed, the final outcome, who decided or
   validated, steps and their order, gotchas, links. Later messages override earlier ones; note reversals.
3. **Separate settled from open**: anything without clear agreement goes to "Open points", with who can close it.
4. **Write for a stranger**: title as the question or task people will search ("How to request access to…",
   "Decision: …"); first paragraph answers it; define acronyms; no "as discussed above".
5. **Structure by type**:
   - Decision record: status, date, deciders, context, options considered with pros/cons, decision, rationale,
     consequences, review trigger.
   - How-to: purpose, prerequisites and access, numbered steps (one action each, expected result), troubleshooting
     table, related links.
6. **Make it findable**: labels, FR and EN keywords, parent page, links from related pages.
7. **Governance**: owner, last verified date, review date (default: 6 months), sources section.
8. **Show the draft** and ask the user to confirm before publishing anywhere.

## Output format
```markdown
# <Searchable title>
| Status | Owner | Last verified | Next review | Labels |
|--------|-------|---------------|-------------|--------|
| <Draft / Decided / Superseded> | <name or to assign> | <YYYY-MM-DD> | <YYYY-MM-DD> | <fr/en keywords> |

**In short:** <2–3 sentences that answer the title>

## Context
## Options considered            <!-- decision record -->
| Option | Pros | Cons |
## Decision and rationale        <!-- decision record -->
## Consequences
## Prerequisites                 <!-- how-to -->
## Steps                         <!-- how-to -->
1. <action> → <expected result>
## Troubleshooting               <!-- how-to -->
| Symptom | Cause | Fix |
## Open points
- <point> — <who can close it>
## Sources
- [<thread / notes / ticket>](…) — <date>
```

## Quality checks
- The "In short" paragraph answers the title without reading further.
- Every decision or step is traceable to a listed source; nothing is added from general knowledge without a label.
- Unsettled items are in Open points, not presented as decisions.
- The page has an owner (or "to assign"), a last-verified date and a review date.
- An existing page search was done and its result stated.

## Guardrails
- Draft only: never publish, edit an existing page or post a link without the user's explicit confirmation.
- Strip personal remarks, blame, health or HR details from threads; keep only work content needed by future readers.
- Respect confidentiality: do not move content from a private channel or restricted doc to a wider space; ask the
  user to confirm the target audience first.
- Attribute decisions to roles or named deciders only when the source shows it.

## Example
Input: a 60-message Chat thread where a team settled how to name shared drives
→ Search finds no existing page, so a new decision record: « Décision : convention de nommage des drives partagés »,
status Decided, deciders as they appear in the thread, the 3 options discussed with pros/cons, the decision, and
one open point (archiving old drives) assigned to the person who raised it. Draft shown; publish only after
confirmation.
