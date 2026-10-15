---
name: expert-finder
description: "Finds the teammates most likely to know about a topic from work signals the user can see (authors and editors of Drive and Confluence pages, Jira assignees and commenters, GitHub committers and reviewers, active participants in Chat and Slack channels, meeting organizers), explains the evidence behind each suggestion, and drafts a short, respectful contact message. Use whenever someone asks who knows about something, who to ask, who owns a topic, process, tool or code area, or needs a contact in another team, even if they only say 'who can help me with…'. Triggers - who knows about, who should I ask, find an expert, who owns, point of contact, who worked on, qui connaît, à qui demander, trouver un expert, qui s'occupe de, interlocuteur pour, qui a travaillé sur."
---

# Expert finder

Points a teammate to the right people to ask, based on visible evidence of their work on the topic, and helps them
reach out without wasting anyone's time.

## When to use
- The user needs help on a topic, tool, process or code area outside their team.
- The user needs the owner of a document, dataset, dashboard or decision.
- A newcomer wants to know who to talk to about a subject.
- Not for: answering the question itself (use `cross-source-search`), mapping stakeholders of a project (use
  `stakeholder-map`), or preparing a meeting with the person once found (use `meeting-prep`).

## Inputs
- The topic, with any known keywords, systems or project names (required).
- What the user needs from the expert (optional, default: a 15-minute exchange or a pointer to the right doc).
- Constraints (optional): country, team, language.

## Sources
1. **Confluence and Drive**: page owners, authors and recent editors of documents on the topic.
2. **Jira**: assignees, reporters and frequent commenters on issues and epics about the topic; component leads.
3. **GitHub**: CODEOWNERS files, top committers and reviewers on the relevant repositories or paths (last 12 months).
4. **Google Chat and Slack**: people who answer questions on the topic in shared spaces and channels.
5. **Calendar and Gmail**: organizers of recurring meetings or senders of reference emails on the topic, only from the
   user's own mailbox and calendar.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Expand the topic** into search terms: FR/EN synonyms, acronyms, system and project names, repository names.
2. **Collect signals** per person, with links: authored/owns doc (strong), CODEOWNERS or component lead (strong),
   assignee of resolved issues (strong), reviewer or commenter (medium), answered questions in channels (medium),
   attendee or mention only (weak).
   If no source is connected, never name anyone: return « No source connected — no expert identified », the
   Signals searched line with every source ✗ and the expanded terms, where to look (owning team's space or
   channel, Confluence page owners) and the message draft addressed to that space, all in the same answer.
3. **Score** = sum of signals weighted strong 3 / medium 2 / weak 1, with recency: signals older than 18 months
   count half. Keep the top 3–5 people; prefer those with recent strong signals.
4. **Check role fit**: an official owner (page "owner" field, CODEOWNERS, component lead) comes first for decisions;
   active practitioners come first for how-to questions. Say which is which.
5. **Flag staleness**: last activity date per person; if a person seems to have changed role or left (no activity,
   documents reassigned), say "may no longer be on this topic" rather than guessing.
6. **Draft the contact message**: who the user is, the specific question, what they already checked (links), a small
   ask (15 min or a pointer), and an easy out. Suggest the channel (team space before DM when one exists).

## Output format
```markdown
**Best first contact: <Name> (<team/role if shown in sources>)** — <one-line reason>

| Person | Why (evidence) | Last activity | Best for |
|--------|----------------|---------------|----------|
| <Name> | owns [page](…); 12 resolved issues in [epic](…) | <date> | decision / how-to |

**Also try:** <team space or channel where the topic is discussed> ([link](…))

### Message draft (<channel>)
> Hi <first name>, I'm <user> from <team>. I'm working on <context> and I'm stuck on <specific question>.
> I've already read <links>. Could you point me to the right doc or spare 15 minutes this week?
> If someone else is better placed, a name would already help a lot. Thanks!

_Signals searched: Confluence ✓ · Drive ✓ · Jira ✓ · GitHub ✓ · Chat ✓ · Slack ✗ — terms: «…», «…»_
```

## Quality checks
- Every suggested person has at least one linked piece of evidence and a last-activity date.
- At most 5 people are listed; the first contact is justified.
- No information about the person beyond work activity on the topic appears.
- The message draft contains a specific question and the links already checked.

## Guardrails
- Use only work signals visible to the user; never infer seniority, performance, availability or personal traits.
- This is not a performance or skills assessment of people; do not rank colleagues for HR purposes.
- Do not send messages; the draft is sent by the user after they confirm.
- Do not suggest bypassing a team's official intake (support channel, Jira service desk) when one exists; show it
  first.

## Example
Input: « Qui connaît le process de transfert de stock entre magasins ? »
→ Output in French. Terms searched: transfert inter-magasins, stock transfer, mutation de stock, plus the Jira
project key found in the first results. Best first contact: the owner of the Confluence process page (last updated
3 months ago), then the assignee who resolved most transfer-related issues this year, then the team space where
these questions are answered. Draft message in French for that space, quoting the page already read.
