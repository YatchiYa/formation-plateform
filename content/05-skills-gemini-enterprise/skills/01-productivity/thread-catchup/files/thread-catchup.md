---
name: thread-catchup
description: "Summarizes a long Gmail, Google Chat or Slack thread into what a late joiner needs: the current state in two lines, decisions taken, open questions, who owes what by when, where people disagree, and a suggested reply. Use whenever the user is added to a long conversation, cannot face reading 40 messages, asks what was decided or what they need to do in a thread, even if they only paste a link. Triggers - catch me up on this thread, summarize this thread, tl;dr, what was decided, what do I need to do here, long email chain, résume ce fil, résumé de la discussion, de quoi ça parle, qu'est-ce qui a été décidé, je n'ai pas suivi, fais-moi un point sur ce thread."
---

# Thread catch-up

Reads a long conversation so the user does not have to, and tells them where it stands, what was decided and what
is expected from them.

## When to use
- The user is CC'd or tagged into a long email chain, Chat space or Slack thread.
- Before replying to a thread with many participants or several sub-topics.
- To forward context to someone joining the topic.
- Not for: a topic spread across many threads and tools over weeks (use `topic-digest`), a meeting transcript
  (use `meeting-notes-to-actions`), or writing the full reply (use `email-reply-drafter`).

## Inputs
- The thread (required): Gmail link or subject, Chat space or Slack channel plus thread link, or pasted text.
- The user's role in it (optional, default: inferred from mentions and To/CC).
- "Since when" (optional, default: since the user's last message in the thread, or the whole thread if none).

## Sources
1. **Gmail, Google Chat or Slack**: every message in the thread, with author, timestamp and reactions; edited or
   deleted markers when visible.
2. **Drive and Confluence**: docs linked in the thread, to check which version people refer to.
3. **Jira**: tickets mentioned by key, to report their real current status.
4. **Calendar**: meetings referenced in the thread ("let's discuss Thursday") to see if they happened.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Order messages by time. Split the thread into sub-topics if it drifted (one line each).
2. Tag every message with one function: *proposal*, *question*, *answer*, *decision*, *commitment*, *objection*,
   *info*. Ignore pure acknowledgements ("+1", "merci") except as agreement signals.
3. **Decisions.** Count something as decided only if a person with the authority or the group explicitly agreed
   ("ok go", "validé", "on part là-dessus", "approved") and nobody objected afterwards. Otherwise it is a
   *proposal*. Record who decided and the message link.
4. **Commitments.** Extract "I'll…", "je m'en occupe", "je te reviens", "we will send by…" as actions: owner,
   deliverable, due date (convert "Friday" into an absolute date from the message date). No owner → "unassigned".
5. **Open questions.** Questions with no answer, or answered then contested. Mark the ones addressed to the user.
6. **Positions.** If people disagree, state each position neutrally in one line with its main argument. No
   judgment of tone or people.
7. **Delta.** If "since when" applies, list what changed since the user's last message.
8. **Status line.** Two sentences: where the topic stands, and what is blocking it.
9. Suggest a reply only for the asks addressed to the user, in the thread's language and register (draft).

## Output format
```markdown
**<Thread subject> · <N> messages · <N> people · <first date> → <last date>**
**Where it stands:** <2 sentences>

### Decisions
- <decision> — by <name>, <date> ([msg](…))

### Who owes what
| Owner | Action | Due | Status |
|-------|--------|-----|--------|
| <name / unassigned> | <verb + deliverable> | <date> | open / done / overdue |

### Open questions
- <question> — asked by <name> · **for you** if addressed to the user

### Differing views (if any)
- <name>: <position + main argument>
- <name>: <position + main argument>

### Since your last message (if applicable)
- <change>

### Suggested reply (draft)
> <short reply answering the asks addressed to the user>
```

## Quality checks
- Every decision and action links to the message it comes from.
- Nothing is listed as a decision without an explicit agreement and no later objection.
- Relative dates are converted to absolute dates using the message's date.
- The summary is at most a third of the length of the original thread, and the status line is two sentences.
- Linked Jira tickets show their current status from Jira, not from the thread.

## Guardrails
- Report what was said, not what people meant. No inference about motives, mood or performance of participants.
- Do not post the summary or reply into the thread; the user decides.
- If the thread contains sensitive personal data (health, HR case, salary), summarize it as "sensitive personal
  topic discussed" and do not reproduce details.
- If parts of the thread are inaccessible (private channel, missing messages), say so instead of filling gaps.
