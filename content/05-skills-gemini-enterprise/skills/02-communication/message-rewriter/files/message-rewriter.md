---
name: message-rewriter
description: "Rewrites a message, email or post for a target audience and goal: clearer, shorter, firmer, warmer or more diplomatic, adapted to a manager, an executive, a store team, a supplier, a customer or a partner, and returns two variants with a short list of what changed and why. Use whenever the user pastes a draft and asks to improve it, fix the tone, make it more professional, shorten it, or make it less aggressive, even if they only say 'can you rework this'. Triggers - rewrite this, rephrase, improve my email, make it shorter, more polite, more assertive, fix the tone, polish this message, reformule, réécris ce message, améliore mon mail, rends-le plus court, plus diplomate, plus ferme, change le ton, corrige ce texte."
---

# Message rewriter

Takes the user's draft and makes it do its job with its reader: understood at first read, right tone, clear ask,
nothing lost.

## When to use
- A draft feels too long, too blunt, too vague, too emotional or too formal.
- The same content must go to a different audience (from a team chat to a director, from French HQ jargon to a
  supplier abroad).
- A delicate message: saying no, escalating, reminding someone for the third time, admitting a mistake.
- Not for: replying to a thread from scratch (use `email-reply-drafter`), translating (use `translation-localizer`),
  reviewing a full document (use `document-reviewer`), or preparing a difficult face-to-face talk (use
  `difficult-conversation-prep`).

## Inputs
- The draft text (required).
- Audience: manager, executive, peer, store team, supplier, customer, external partner (optional, default: inferred
  from the draft; stated in one line).
- Goal: inform, get a decision, get an action, say no, apologize, escalate, thank (optional, default: inferred).
- Constraint: channel (email, Chat, Slack, SMS), max length, formality (tu/vous) (optional).

## Sources
1. **Gmail / Chat / Slack**: if the draft replies to a thread, the thread itself, to keep facts and commitments
   consistent and to mirror the formality the other person uses.
2. **Drive / Confluence**: writing or brand-tone guidelines, if the user mentions them.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Diagnose before rewriting.** Score the draft 1–3 on five axes and name the main problem:
   - Purpose: is the ask or point findable in the first 2 lines?
   - Structure: one idea per paragraph, logical order?
   - Length: words that the reader does not need?
   - Tone: fits the relationship and the goal (no passive aggression, no over-apology, no jargon)?
   - Action: who does what by when, explicit?
2. **Apply the audience profile**:
   - Executive: BLUF, ≤ 120 words, numbers and decision, no back-story.
   - Manager: context in 1 line, the ask, the options you see.
   - Store or floor team: short sentences, concrete actions, when and where, read on a phone.
   - Supplier / partner: formal, factual, reference numbers (order, PO, ticket), deadline, no internal jargon.
   - Customer: empathy first, then solution, no blame, no internal process detail.
3. **Apply the goal pattern**:
   - Say no: thank → clear no → reason in one line → alternative.
   - Escalate: fact → impact → what was tried → precise ask → deadline.
   - Reminder: neutral reference to the first request → new deadline → make it easy (link, 1-click answer).
   - Apology: own it → impact acknowledged → fix → prevention. One apology, not three.
4. **Rewrite**, keeping every fact, figure, date, commitment and name of the original. Use active voice, cut hedges
   ("just", "I think maybe", « je me permets de »), replace vague words with specifics already in the draft.
5. **Produce two variants**: A = the recommended version, B = a contrasting option (shorter, or warmer, or firmer).
6. **List the changes** (≤ 5 bullets) so the user learns the pattern, and flag anything you could not keep or that
   reads as a commitment the user may not want to make.

## Output format
```markdown
_Read as: <audience> · goal: <goal> · main issue: <one phrase>_

### Version A — recommended
<rewritten message, subject line first if email>

### Version B — <shorter | warmer | firmer>
<variant>

### What changed
- <change> — <why it helps the reader>
- …
_Check: <any fact or commitment to confirm, or "all facts kept">_
```

## Quality checks
- Every fact, number, date and name in the original appears unchanged in both versions.
- The ask (or main point) is in the first two lines of Version A.
- Version A is shorter than the original unless the user asked for more detail.
- Formality (tu/vous, first names) matches the audience and the existing thread.
- No new commitment, promise or deadline was added that the user did not write.

## Guardrails
- Do not change the meaning to make it sound nicer: if the original refuses, the rewrite still refuses.
- Remove insults, sarcasm and personal remarks about colleagues; if the draft accuses a named person, suggest a
  factual version and recommend a conversation rather than a written message.
- Remove sensitive personal data (health, salary, disciplinary details) that the recipient does not need.
- Draft only: never send or post. The user copies or confirms the final text.

## Example
Input (to a supplier): « Bonjour, ça fait 3 fois qu'on vous relance, la livraison des tentes n'est toujours pas
arrivée, c'est inadmissible. »
→ Version A (firm, formal): « Bonjour, la livraison de la commande <n° PO> (tentes) prévue le <date> n'est pas
arrivée malgré nos relances du <dates>. Pouvez-vous nous confirmer d'ici jeudi 12 h une date de livraison ferme ?
Sans retour, nous devrons revoir l'implantation du rayon camping. » Changes: reference number moved first, emotion
replaced by impact and deadline; PO number and dates left as placeholders to fill.
