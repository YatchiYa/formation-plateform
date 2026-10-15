---
name: internal-announcement-writer
description: "Writes an internal announcement in three ready-to-post versions (email, short Google Chat or Slack post, intranet or Confluence article) plus an anticipated FAQ and a pre-send checklist: what changes, why, who is affected, what to do and by when, who to ask. Use whenever a teammate must announce something to a team, a store, a region or the whole company, such as a new tool, an organization change, an arrival or departure, a process change, an event or a result, even if they only ask for 'a quick message to the team'. Triggers - announcement, announce to the team, all-hands email, internal comms, intranet post, Slack announcement, annonce interne, annoncer à l'équipe, mail à tous, message à toute l'équipe, communiquer une nouvelle, post sur l'intranet, note d'information."
---

# Internal announcement writer

Produces one consistent message in the formats each audience actually reads, so that every teammate learns the same
thing, knows what to do, and knows where to ask.

## When to use
- A new tool, process, rule or schedule starts, and teammates must act on it.
- An organization change: arrival, departure, new role, new team, store opening or move.
- A result, milestone or event must be shared (season results, award, store anniversary, sport event).
- The same news must go out by email, on Chat or Slack, and on the intranet without contradictions.
- Not for: planning a full change program over weeks (use `change-communication-plan`), a periodic team digest
  (use `team-newsletter`), a spoken speech (use `talking-points-writer`), or rewriting an existing message (use
  `message-rewriter`).

## Inputs
- The news itself and the facts: what, when, who (required).
- Audience: team, store, region, country, HQ function, all teammates (required).
- What the reader must do, and the deadline (optional, default: "no action required" stated explicitly).
- Sender and signature (optional, default: the user).
- Confidentiality or embargo date (optional). Ask if the news concerns a person or an organization change.

## Sources
1. **Drive / Confluence**: the decision doc, project page, previous announcements on the same topic (to keep
   continuity and reuse the internal names), and any comms guideline or template.
2. **Gmail / Chat / Slack**: the thread where the decision was taken, and earlier messages to the same audience.
3. **Calendar**: dates of the related events (training sessions, go-live, kick-off) to quote them correctly.
4. **Jira**: go-live date and scope, if the news is a release or a project milestone.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Fill the core message card** before writing; every version derives from it:
   - Headline (≤ 12 words, the news itself, not "Important information").
   - What changes · Why (one reason the reader cares about) · Who is affected · What to do + deadline ·
     Where to ask (person or channel) · Where to find more (link).
   Missing card items become placeholders like [date to confirm]; never invent them.
2. **Choose the structure by type**:
   - Change or new tool: what / why / what you need to do / support.
   - People news: who / role and scope / start date / short personal note only if the person agreed / welcome line.
   - Result or success: result / thanks to whom / what it means next.
   - Sensitive news (reorganization, closure): facts first, impact on people, next steps, support available; no
     humor, no spin, sent before rumors.
3. **Write the email**: subject = headline (+ [Action required] if there is an action), first two lines carry the
   whole message, then short sections, one call to action, sender signature.
4. **Write the Chat / Slack post**: ≤ 80 words, headline in bold, the action, a link to the email or intranet page,
   at most one emoji, @-mentions only for those who must act.
5. **Write the intranet / Confluence article**: title, standfirst (2 lines), body with sub-headings, a quote from the
   sponsor only if provided, FAQ, contacts.
6. **Draft the FAQ**: the 5–8 questions readers will really ask (Does it change my schedule? What if I can't attend?
   Who replaces X? Is it mandatory? Where is the training?). Answer only from the facts; otherwise "Answer pending —
   owner: <name>".
7. **Run the pre-send checklist**: right audience list, embargo respected, managers briefed before their teams
   for people or org news, dates and links checked, accessible (no info only in an image).

## Output format
```markdown
## Core message
| Headline | What changes | Why | Who | Action + deadline | Ask | More info |
|----------|--------------|-----|-----|-------------------|-----|-----------|

## 1. Email
**Subject:** <headline> [Action required — <date>]
<body ≤ 200 words>

## 2. Chat / Slack post
<≤ 80 words>

## 3. Intranet article
### <Title>
_<standfirst>_
<body with sub-headings>

## FAQ
**Q:** … **A:** … (source / "Answer pending — owner: …")

## Before you send
- [ ] Audience list: <…>   - [ ] Managers briefed first (if people/org news)
- [ ] Dates and links checked   - [ ] Embargo: <date or none>
_Placeholders to fill: <list>_
```

## Quality checks
- The headline, date and action are identical in all three versions.
- The email's first two lines alone tell the reader what happens and what to do.
- The Chat/Slack post is ≤ 80 words and links to the long version.
- Every fact (date, name, scope, figure) comes from the user or a cited source; gaps are visible placeholders.
- The FAQ answers only from facts and marks unknown answers as pending with an owner.
- Plain language: sentences ≤ 20 words on average, no unexplained internal acronym.

## Guardrails
- People news: share only what the person agreed to (no reason for a departure, no health or family details).
  For reorganizations or job impacts, advise checking with HR and local employee-representation rules before sending.
- Do not invent quotes from leaders; use a quote only if the user gives it.
- Draft only: never send the email or post the message; the user publishes after confirming the text and audience.
- Keep embargoed or confidential news out of channels wider than the stated audience.
