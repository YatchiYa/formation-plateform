---
name: cross-source-search
description: "Searches across Drive, Confluence, Jira, Slack, Google Chat, Gmail and GitHub with a deliberate strategy (query reformulation, French and English synonyms and acronyms, recency filters, source authority ranking), then returns one consolidated answer where every claim is cited, conflicting sources are shown side by side, and a confidence level is given. Use whenever someone asks where something is, what the current rule or status is, whether a decision was made, or any question whose answer lives somewhere in internal tools, even if they only say 'do we have a doc on…' or 'I remember someone said…'. Triggers - find, where is, search for, do we have a doc on, what was decided about, look up, trouve-moi, où est, chercher, est-ce qu'on a un doc sur, qu'est-ce qui a été décidé sur, retrouver l'info."
---

# Cross-source search

Finds the answer a teammate needs across all connected tools and tells them where it comes from and how sure it is,
instead of a list of links to open.

## When to use
- "Where is the latest version of…", "do we have a doc on…", "what's the process for…".
- A fact or decision is scattered across emails, tickets, chats and pages.
- Before writing something new, to check whether it already exists.
- Not for: who to ask (use `expert-finder`), a timeline of a topic over a period (use `topic-digest`), summarizing
  one long thread (use `thread-catchup`), official HR or customer policy answers (use `hr-policy-qa` or
  `customer-policy-qa`), or comparing two documents (use `document-comparison`).

## Inputs
- The question (required).
- Scope hints (optional, default: all connected sources, last 24 months, recency-weighted): project, team,
  country, period, document type.
- Desired output (optional, default: answer + sources; "just the link" if the user asks for a document).

## Sources
1. **Confluence**: official pages, process docs, decision records (space, page owner, last updated).
2. **Drive**: Docs, Sheets, Slides, PDFs, Meet transcripts and notes (owner, modified date, shared drive name).
3. **Jira**: issues, epics and comments for decisions, status and owners.
4. **GitHub**: READMEs, ADRs, code comments, PR discussions for technical questions.
5. **Gmail, Google Chat and Slack**: threads for recent decisions and informal context.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Decompose the question** into the facts needed (what, which version, who decided, when).
2. **Build the query set** (3–6 queries, not one):
   - key terms + synonyms in **French and English** (e.g. retour / return / reprise; magasin / store; fournisseur /
     supplier), internal acronyms and their expansion, project code names found in first results;
   - exact phrases in quotes for names and titles; person or team names when relevant;
   - date filters: start recent (last 6–12 months), widen only if nothing relevant.
3. **Search each source**, keep for each hit: title, link, owner/author, date, source type, the exact passage.
   Search only through real connected tools; never print a tool call as text or report a hit you did not receive.
   If no source is connected, the whole answer is: « No source connected — nothing found », the Searched line with
   every source ✗, the queries you would run, and a request to paste the relevant docs or threads.
4. **Rank by authority**, then recency:
   official/approved page or policy (Confluence space of the owning team, shared drive "official") >
   decision record, signed or approved doc > Jira issue status/resolution > meeting notes and transcripts >
   email > chat message > personal draft. Newer beats older at the same level; a newer chat does not override an
   official page, but is shown as a possible change.
5. **Extract the answer**: one claim per sentence, each with its citation. Quote short exact passages for rules,
   numbers and dates.
6. **Handle conflicts**: when sources disagree, show both with dates and authority, say which one prevails and why,
   and suggest who can settle it (doc owner).
7. **Confidence**: High = authoritative and recent source, no conflict; Medium = indirect or older source, or minor
   conflict; Low = only informal sources, old, or contradictory.
8. **Gaps**: say what was not found and the queries tried, so the user can refine.

## Output format
```markdown
**<Direct answer in 1–3 sentences>** [1][2]
**Confidence:** High | Medium | Low — <why>

### Details
- <claim> [n]
- <claim> [n]

### Conflicting information
| Says | Source | Date | Authority | Prevails? |
|------|--------|------|-----------|-----------|

### Sources
1. [<title>](link) — <source type>, <owner>, <date>
2. …

_Searched: Confluence ✓ · Drive ✓ · Jira ✓ · GitHub ✗ (not connected) · Gmail ✓ · Chat ✓ · Slack ✓ — queries: «…», «…»_
_Not found: <what is missing>_
```

## Quality checks
- Every sentence in the answer that states a fact carries at least one citation number.
- Each cited source has a date and its type; the newest relevant source date is visible.
- Conflicts are shown, not silently resolved; the section is omitted only when there are none.
- At least one French and one English query were run when the topic is not language-specific.
- The "Searched" line lists every source and its real status.

## Guardrails
- Only surface content the user can already access through their own permissions; never paraphrase a document from
  a restricted space they cannot open.
- Do not reproduce personal or sensitive content from emails or chats (HR, health, salary, disciplinary); point to
  the thread with a neutral description instead.
- No fabrication: if nothing answers the question, say so; never fill gaps with general knowledge presented as an
  internal rule.
- Quote briefly; link rather than copy whole documents.

## Example
Input: « Quelle est la règle actuelle pour les notes de frais en déplacement à l'étranger ? »
→ Queries in FR and EN (notes de frais, frais de déplacement, expense report, travel policy). Answer from the
official policy page with its date [1]; a recent Chat message announcing a change is shown under Conflicting
information as *not yet reflected in the official page* [3], with the page owner as the person to confirm.
Confidence: Medium.
