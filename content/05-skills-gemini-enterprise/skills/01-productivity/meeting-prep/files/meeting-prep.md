---
name: meeting-prep
description: "Prepares the user for one upcoming meeting: who will be there and their recent context, the history of the topic across emails, docs, Jira and past meeting notes, the probable goal, the user's position, the questions to ask and the outcome to aim for, on one page. Use whenever the user has a specific meeting coming up, asks what a meeting is about, who someone is, or what to say in a meeting, even if they only give the meeting title. Triggers - prepare my meeting, meeting prep, brief me for, what is this meeting about, who is attending, before my call with, préparer ma réunion, prépa réunion, briefe-moi pour, c'est quoi cette réunion, qui sera là, avant mon rendez-vous avec."
---

# Meeting prep

Gives the user, in five minutes of reading, what they need to walk into one specific meeting knowing why it exists,
who is in the room, what happened before and what they want to leave with.

## When to use
- A meeting is coming up and the user has not followed the topic closely.
- The user was invited without context, or the invite has no agenda.
- A meeting with senior people, another team or an external partner where preparation matters.
- Not for: all of today's meetings at once (use `daily-briefing`), a 1:1 with a direct report (use
  `one-on-one-prep`), a sales discovery call (use `discovery-call-prep`), or building the agenda as organizer (use
  `meeting-agenda-builder`).

## Inputs
- The meeting (required): title, time or Calendar link. Default: the user's next meeting with other attendees.
- What the user wants from it (optional, default: inferred and stated as an assumption).

## Sources
1. **Google Calendar**: title, description, organizer, attendees and their responses, attached docs, previous
   occurrences of the same recurring event.
2. **Drive**: attached and linked docs; notes or Meet transcripts of previous occurrences; docs recently edited by
   attendees on the same topic.
3. **Gmail, Chat and Slack**: last 30 days of threads between the user and the attendees on the topic, especially
   open questions and promises.
4. **Jira and Confluence**: tickets and pages named in the invite or the threads, with their current status.
5. **GitHub** (tech meetings): PRs or issues linked in the invite.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Read the invite. Extract the stated purpose and any agenda. If none, infer the **meeting type** from the title,
   attendees and threads: *decide*, *align/inform*, *solve a problem*, *brainstorm*, *review/status*, or
   *relationship*. State the inference and its evidence.
2. **Attendees.** For each person (max 8; group the rest by team): role or team as found in email signatures,
   Calendar or Drive; their last interaction with the user; what they asked or promised; their likely stake. Use only
   work information found in sources.
3. **History.** Build a short timeline of the topic: key emails, decisions, doc versions, ticket status changes,
   last meeting's actions and whether they were done (check Jira or the threads).
4. **Open items.** List unresolved questions, pending decisions and overdue actions, especially those owned by the
   user (they will be asked).
5. **The user's position.** From the user's own emails and docs, summarize what they have said so far. Flag
   contradictions with newer facts.
6. **Aim.** Write the outcome to target ("leave with a go/no-go on the Forclaz backpack sample budget") and the
   fallback ("agree on who decides and when").
7. **Questions to ask.** 3–5 questions that move toward the aim, each tied to an open item. Add 1–2 questions the
   user is likely to be asked, with a suggested answer from sources.
8. **Read first.** At most 3 documents, with the section to read and the estimated reading time.

## Output format
```markdown
**<Meeting title> · <day HH:MM–HH:MM> · organizer <name> · type: <decide / align / …>**
**Your aim:** <target outcome> · **Fallback:** <minimum acceptable outcome>

### Why this meeting
<2–3 lines; mark inferred purpose as *inferred*>

### Who's there
| Name | Role / team | Last interaction with you | Their likely stake |
|------|-------------|---------------------------|--------------------|

### What happened so far
- <date> — <event> ([link](…))

### Open items
- <item> — owner <name> · **yours** if the user owns it

### Questions to ask
1. <question> — moves toward: <aim>
### You may be asked
- <question> → suggested answer: <from source> ([link](…))

### Read first (≈ <min> min)
- <doc> — <section> ([link](…))
```

## Quality checks
- The meeting type and purpose are either quoted from the invite or labeled *inferred* with the evidence.
- Every history line and suggested answer has a source link.
- Actions from the last occurrence are listed with their real status.
- Questions to ask are specific to this meeting; none could be pasted into any other meeting unchanged.
- The whole prep reads in about 5 minutes (≤ 40 lines outside tables).

## Guardrails
- Attendee context is limited to professional information found in sources. No personal life, health, opinions or
  speculation about personality.
- Do not reply to the invite, propose new times or message attendees unless the user asks and confirms a draft.
- Do not include content from confidential documents or threads the attendees should not see if the user plans to
  share the prep; warn when a source is restricted.
