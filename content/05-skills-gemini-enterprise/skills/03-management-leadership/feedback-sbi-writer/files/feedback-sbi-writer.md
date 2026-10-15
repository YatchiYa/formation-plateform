---
name: feedback-sbi-writer
description: "Turns raw observations into clear, fair feedback using Situation-Behavior-Impact (plus Intent when constructive): one recognition or improvement message, written and spoken versions, a question to open dialogue, an agreed next step and delivery tips (timing, channel, tone). Use whenever someone wants to give feedback to a teammate, peer, manager or supplier, thank someone meaningfully, or point out a problem without hurting the relationship, even if they just paste angry notes. Triggers - give feedback, write feedback, how do I tell him, recognition message, constructive feedback, SBI, donner du feedback, faire un retour à, féliciter un coéquipier, recadrer quelqu'un, comment lui dire, feedback constructif."
---

# Feedback SBI writer

Converts what a person saw into feedback that is specific, behavior-based and actionable, so it lands as help or
recognition rather than as judgment.

## When to use
- A manager or peer wants to recognize a concrete contribution (not just "great job").
- Something went wrong and the user wants to raise it constructively and quickly.
- The user has notes or an emotional first draft and wants it reframed.
- Upward feedback to a manager, or feedback to a partner or supplier contact.
- Not for: a full conversation plan on a serious or repeated issue (use `difficult-conversation-prep`),
  formal annual review text (use `performance-review-writer`), or rewriting any other message (use
  `message-rewriter`).

## Inputs
- What happened: the observation, ideally with date and context (required).
- Positive (recognition) or constructive (required; infer from the notes if clear).
- Relationship: report, peer, manager, external (optional, default: direct report).
- Channel: in person, video, written (optional, default: in person for constructive, written + public option for
  recognition).

## Sources
1. **Gmail, Chat and Slack**: the thread or message the user points to, to anchor the situation in facts (date,
   what was written).
2. **Jira, GitHub and Drive**: the ticket, PR or doc concerned, for factual impact (delay, rework, customer
   effect, result).
3. **Confluence and Drive**: the team's values, behaviors or competency framework, to use its wording when the
   behavior relates to one — only if found, never invented.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Separate facts from interpretations.** Rewrite each statement of the user's notes into one of: observable
   behavior (what was said or done), impact (consequence on people, customers, results), or interpretation/judgment
   ("lazy", "doesn't care", "always"). Interpretations are removed or turned into a question.
2. **Situation**: when and where, specific and recent ("at Tuesday's 9:00 huddle in the running aisle").
3. **Behavior**: what a camera would have recorded. Ban adjectives about personality and words like "always",
   "never", "attitude".
4. **Impact**: the real consequence, ideally on a third party (customer, team, project). For recognition, name
   the impact on the customer or team — this is what makes praise credible and repeatable. Use only an impact the
   user stated or a source shows; otherwise write `Impact: [what effect did it have on <team/customers>? — to fill]`
   in both versions and ask it in one line.
5. For constructive feedback add **Intent**: assume a positive intent and ask about it ("I imagine you wanted to
   go fast — what was your thinking?"). Then the **request**: one specific future behavior, plus an offer of help.
6. Calibrate **dose**: one topic per conversation. If the notes contain several issues, choose the one with the
   highest impact and list the others as "keep for later".
7. Write the **delivery tips**: within 48 hours, private for constructive, public allowed for recognition if the
   person likes it; open with the question, listen more than talk; end with an agreed next step and a follow-up date.
8. Run the fairness check: would this feedback be written the same way for any teammate who did the same thing?

## Output format
```markdown
**Feedback for <Name> · <recognition | constructive> · <channel>**

### Facts kept vs removed
| From your notes | Type | Used as |
|-----------------|------|---------|
| "<quote>" | behavior / impact / judgment | kept / reframed as question / removed |

### What to say (spoken, ~60 seconds)
- **Situation:** …
- **Behavior:** …
- **Impact:** …
- **(Intent question):** …
- **Request / next step:** …

### Written version (<email | Chat | Slack>, ≤ 80 words)
<text>

### Delivery tips
- When: … · Where: … · Open with: … · If they react with <likely reaction>: …

### Kept for later
- <other topics, if any>
```

## Quality checks
- The behavior line contains no adjective about the person and no "always/never".
- The impact names a concrete consequence (who or what was affected), not "it wasn't good", and comes from the
  user or a source; otherwise it is a [to fill] placeholder.
- Constructive feedback has exactly one topic and one specific request.
- The written version is ≤ 80 words and does not contain anything the spoken version does not.
- Every fact taken from a source has its link or date.

## Guardrails
- Never include health, family, origin, age, gender or other protected characteristics, even if the user's notes
  mention them; flag the removal.
- If the notes describe harassment, discrimination, violence, safety or legal issues, stop the SBI flow: say it
  must go to HR or the appropriate channel and do not draft a "feedback" that minimizes it.
- Do not send or post. Public recognition is posted only after the user confirms and the person is comfortable
  with it.
- Do not invent the impact; if unknown, write a question ("what effect did it have on…?") for the user to fill.
