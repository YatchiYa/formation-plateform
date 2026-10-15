---
name: talking-points-writer
description: "Writes talking points or a short speech meant to be spoken: town hall, store opening, team kickoff, season launch, award or farewell, partner or club event. Delivers a hook, three key messages with a story or proof each, a call to action and a closing line, timed to the minute, in spoken style, with a one-card cheat sheet and answers to likely tough questions. Use whenever someone must speak in front of a team, customers or partners, even for two minutes, or asks 'what should I say', even if they don't say 'speech'. Triggers - talking points, speech, short speech, what should I say, kickoff speech, town hall remarks, toast, opening remarks, éléments de langage, discours, prise de parole, mot d'accueil, discours d'inauguration, quoi dire en réunion, speech pour l'équipe."
---

# Talking points writer

Prepares the user to speak with confidence: a short, memorable, spoken message, timed for the slot, true to the
facts and to their own voice.

## When to use
- Town hall, all-hands, team kickoff, season launch, store opening or anniversary.
- Recognition moment: award, promotion, farewell, thanks to a team after a peak period.
- Speaking at a partner, club, school or local authority event.
- A manager needs consistent "éléments de langage" on a topic before talking to their team.
- Not for: slide decks (use `presentation-storyline`), written announcements (use `internal-announcement-writer`),
  a full change program (use `change-communication-plan`), or a one-to-one hard conversation (use
  `difficult-conversation-prep`).

## Inputs
- Occasion, audience and size (required).
- Duration (required; ask with the occasion if missing; default for a toast or welcome: 2 minutes).
- The key message or what the audience should feel or do (optional, default: inferred and stated).
- Facts available: results, names to thank, anecdotes (optional, default: searched in sources).
- Speaker's style: formal, warm, energetic, humorous (optional, default: warm and direct).

## Sources
1. **Drive / Confluence**: event brief, project or store results, previous speeches by the same speaker (to match
   their voice), official key messages if the topic has them.
2. **Gmail / Chat / Slack**: kudos and thank-you messages, customer feedback, team highlights to quote as stories.
3. **Databricks / Tableau**: the 1–2 figures worth saying out loud, if the user wants numbers.
4. **Calendar**: event details (time, place, duration of the slot).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Set the budget**: spoken pace ≈ 130 words per minute; 2 min ≈ 260 words. Keep 10% slack for pauses.
2. **Define the one thing**: the sentence the audience should repeat afterwards (≤ 12 words).
3. **Build the structure** (hook → 3 messages → call to action → close):
   - Hook (≤ 15% of time): a concrete moment, a customer or teammate story, a striking fact, a question. Never
     "I'm happy to be here".
   - 3 messages max, each = claim + proof (figure, example or story) + "so what for you".
   - Call to action: one specific thing the audience does next.
   - Close: callback to the hook or the one thing; end on energy, not on "thank you, any questions".
4. **Write for the ear**: sentences ≤ 15 words, active verbs, "we" and "you", one number per message at most,
   rounded and compared ("one in three customers"), rule of three, repetition of the key line. Mark pauses with
   « / » and emphasis in bold.
5. **Recognition moments**: name the person or team, the specific action, its effect on customers or colleagues.
   Specific beats superlative.
6. **Fit the occasion**: for a store opening or sport event, connect to the local sport community and to the purpose
   of making sport accessible; for a tough period, acknowledge the effort and the difficulty before the next step.
7. **Prepare Q&A**: 3–5 likely or tough questions with short, honest answers; "I don't know yet, I'll come back
   to you by <date>" is a valid answer.
8. Produce a **cue card**: the hook, 3 keywords, the call to action, the closing line.

## Output format
```markdown
**Occasion:** <…> · **Audience:** <…> · **Duration:** <N> min ≈ <N> words
**The one thing:** <sentence>

### Full text (spoken)
<Hook>
<Message 1 + proof>
<Message 2 + proof>
<Message 3 + proof>
<Call to action>
<Close>

### Cue card
- Hook: …
- 1 · … / 2 · … / 3 · …
- Ask: …
- Close: …

### Likely questions
| Question | Short answer |
|----------|--------------|

_Facts used: <figure → source> · To confirm: <names, pronunciation, figures>_
```

## Quality checks
- The word count fits the duration at ≈ 130 words per minute (± 10%).
- There are at most 3 key messages, each with a proof from a source or the user.
- Every figure, name and anecdote is sourced or provided by the user; nothing invented.
- No sentence over 20 words in the spoken text.
- The text ends with a call to action and a closing line, not with a generic thank-you.

## Guardrails
- Never invent anecdotes, customer stories, quotes or results; if none is available, propose a placeholder the user
  fills with a real one.
- Recognition: check names and how the person wants to be mentioned; avoid personal or health details.
- Do not make commitments on behalf of the company (jobs, budgets, dates) that the sources do not support.
- For external audiences, keep internal figures and confidential projects out unless the user confirms they are public.

## Example
Input: « 3 minutes pour l'inauguration du magasin, devant les équipes, le maire et des clubs locaux. »
→ ≈ 390 words in French. Hook: a real teammate story the user provides (placeholder if none). Messages: a place to
try and practice sport · a team of passionate sport teammates · partnerships with local clubs (only those named by
the user). Call to action: « Venez tester, venez pratiquer. » Cue card + likely questions such as parking, opening
hours and local jobs, answered only from the user's facts.
