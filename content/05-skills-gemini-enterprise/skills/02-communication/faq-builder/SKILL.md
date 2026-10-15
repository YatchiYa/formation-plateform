---
name: faq-builder
description: "Builds a sourced FAQ from documents, email and chat threads, Jira or support tickets and meeting notes: finds the questions people really ask, groups them by theme, answers each one in plain language with a citation, and lists the questions with no official answer yet and who should answer them. Use whenever a project, a new tool, a policy, an event or a change keeps generating the same questions, or someone needs a Q&A for an intranet page, an onboarding or a launch, even if they ask for 'a Q&A' or 'the common questions'. Triggers - FAQ, Q&A, frequently asked questions, common questions, build a FAQ, questions people ask, foire aux questions, FAQ pour l'équipe, questions fréquentes, créer une FAQ, questions-réponses, les questions qu'on nous pose."
---

# FAQ builder

Produces an FAQ where every answer is traceable to a source, so teammates can self-serve and the project team
stops answering the same question ten times.

## When to use
- A launch, a new tool, a new process or a reorganization generates repeated questions in Chat, Slack or email.
- An intranet or Confluence page needs a Q&A section.
- An onboarding kit, training or event needs "practical questions" covered.
- Support or ticket data shows recurring "how do I" questions.
- Not for: answering one HR policy question (use `hr-policy-qa`), answering customer policy questions (use
  `customer-policy-qa`), writing a help-center article for one problem (use `kb-article-writer`), or the
  announcement itself (use `internal-announcement-writer`).

## Inputs
- Topic and audience (required).
- Source scope: docs, channels, ticket project, date range (optional, default: Drive and Confluence for the topic,
  plus Chat/Slack/Gmail over the last 60 days).
- Target size (optional, default: 10–20 questions).
- Publication place: intranet, Confluence, email, printed in store (optional; adapts length).

## Sources
1. **Drive / Confluence**: the reference documents for the answers (policy, project page, guide, decision record).
   These are the only sources for official answers.
2. **Google Chat / Slack**: questions asked in channels and their answers; messages ending with "?" on the topic.
3. **Gmail**: questions received by the user or a shared mailbox on the topic.
4. **Jira (or Jira Service Management)**: tickets on the topic: summaries, recurring categories, resolutions.
5. **Drive (Meet transcripts)**: Q&A parts of town halls, trainings or kickoff sessions.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Harvest questions.** Collect every real question from sources 2–5 with its frequency and source link. Rewrite
   each in the asker's words, first person ("Can I…?", « Est-ce que je dois… ? »).
2. **Cluster and deduplicate.** Merge questions with the same answer; keep the most common phrasing. Count
   occurrences: this ranks them.
3. **Add the obvious unasked ones**: for any change, cover What is it? Why? When? Who is concerned? What do I
   have to do? What if I can't / don't? Who do I ask? Where is the doc?
4. **Group into 3–6 themes** in the reader's logic (Basics, Access & tools, Schedule, Practical cases, Support),
   most frequent theme first.
5. **Answer from reference sources only.** Answer in ≤ 60 words, first sentence = the direct answer (yes / no /
   the number / the step), then the condition or exception, then the link. Cite the source for each answer.
   If no reference doc was actually read, write no answers: keep the questions, mark each ❓ with
   `[answer from <doc> — to fill]`, and never create document names, section numbers, URLs, dates or prices.
6. **Classify confidence**: ✅ official (from a reference doc), 💬 informal (from a chat answer by the project team,
   to confirm), ❓ no answer found. Never fill ❓ with a plausible guess.
7. **List the open questions** with a suggested owner (author of the reference doc, project lead) and a draft
   message asking them.
8. Recommend a review date and owner for the FAQ, since answers age.

## Output format
```markdown
# FAQ — <topic>
_For: <audience> · Last updated: <date> · Owner: <to assign> · Sources: <N docs, N threads, N tickets>_

## <Theme 1>
**<Question?>**
<Direct answer.> <Condition/exception.> ✅ ([source](…))

**<Question?>**
… 💬 to confirm ([thread](…))

## <Theme 2>
…

## Open questions (no official answer yet)
| Question | Asked (times) | Suggested owner |
|----------|---------------|-----------------|

_Draft message to owners: <short text>_
```

## Quality checks
- Every answer has a source link and a confidence mark; no ❓ question has an invented answer; every cited doc,
  section and link was actually opened in this session.
- Each answer's first sentence answers the question directly.
- No two questions share the same answer (duplicates merged).
- Questions are phrased as the reader would ask them, not as headings.
- Answers ≤ 60 words; longer content is linked, not pasted.

## Guardrails
- Official answers come only from reference documents; chat answers are marked "to confirm".
- Do not quote who asked a question; questions are anonymized.
- HR, legal, safety or pay questions without a reference document go to "Open questions", never answered by inference.
- Draft only: publishing on the intranet or Confluence, or posting to channels, requires the user's confirmation.

## Example
Input: « Fais une FAQ pour le déploiement du nouvel outil de planning en magasin, à partir du canal Chat du projet. »
→ Output in French, themes *L'essentiel*, *Accès et connexion*, *Mon planning au quotidien*, *Aide*. « Est-ce que je
peux encore échanger un créneau avec un coéquipier ? » answered ✅ from the user guide in Drive; « Que se passe-t-il
pour les heures déjà posées ? » found 6 times in Chat but with no reference answer → *Open questions*, owner = project
lead, with a draft message.
