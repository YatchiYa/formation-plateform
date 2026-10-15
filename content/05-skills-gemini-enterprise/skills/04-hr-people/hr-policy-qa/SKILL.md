---
name: hr-policy-qa
description: "Answers questions about HR policies and rules (leave, working time, remote work, expenses, training, mobility, parental leave, benefits, code of conduct) strictly from official policy documents found in Drive and Confluence, with a citation for every statement, the scope (country, entity, population) and the document date, and escalates to HR when the policy is missing, unclear or the case is personal. Use whenever a teammate or manager asks what the rule is, whether they are entitled to something, or how an HR process works, even if the question sounds simple. Triggers - HR policy, am I entitled, how many days, leave policy, remote work rule, expense rule, politique RH, règlement RH, ai-je droit, congés, télétravail, accord d'entreprise, combien de jours, note de frais."
---

# HR policy Q&A

Gives teammates and managers a fast, cited answer from the official policy, and a clear "ask HR" when the documents
do not settle the question. It never fills a gap with general knowledge.

## When to use
- "How many days of … can I take?", "Can I work remotely from …?", "Who approves …?"
- A manager needs to know the rule before answering a teammate.
- Someone wants the official source to share with their team.
- Not for: customer return or warranty rules (use `customer-policy-qa`), checking a document against a policy
  (use `policy-compliance-check`), or preparing a hard conversation with a teammate (use
  `difficult-conversation-prep`).

## Inputs
- The question (required).
- Country, entity and population: store, warehouse, HQ, manager or not, contract type (required when policies
  differ by scope; ask once if unknown and not inferable from the user's profile or question).
- Date of the situation (optional, default: today; policies change).

## Sources
1. **Confluence**: HR spaces, policy pages, FAQ pages. Prefer pages with an owner and a recent update date.
2. **Drive**: signed policies, collective or company agreements, handbooks, HR notes (PDF, Docs). Prefer the
   version marked final/signed and the latest date for the scope.
3. **Gmail and Chat**: only official HR announcements of a policy change (sender from HR), as a pointer to the
   document, never as the source of the rule itself.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Scope the question**: topic, country, entity, population, date. Rewrite it in one line.
2. **Search** in both languages and with synonyms: « congés payés / paid leave / vacation », « télétravail /
   remote work / hybrid », « frais / expenses ». Keep up to 5 candidate documents.
3. **Rank by authority**: signed agreement or official policy > HR Confluence page > FAQ > presentation >
   email. Discard drafts, documents for another country/entity, and versions superseded by a newer one.
4. **Answer only from the retained text**:
   - Quote or closely paraphrase the clause, with the document title, section and date.
   - State the scope exactly as written ("applies to employees of <entity> in <country>").
   - If two sources conflict, show both, say which one is more authoritative or more recent, and escalate.
5. **Confidence label**:
   - *Answered*: explicit clause covering the scope.
   - *Partially answered*: clause found but scope, date or a condition is unclear → list what to confirm.
   - *Not found*: no official source → say so, do not answer from general knowledge or labor law, give the
     escalation path (HR contact or HR portal, if found in Confluence).
6. **Personal cases** (health, disability, pregnancy, conflict, disciplinary, harassment, pay of a named person):
   give only the general rule and route to HR or the appropriate confidential channel. Do not analyze the
   personal situation.
7. Offer a short, shareable version of the answer for a manager to forward.

## Output format
```markdown
**Answer:** <1–3 sentences, direct> · **Confidence:** Answered / Partially answered / Not found
_Scope: <country · entity · population · date>_

**What the policy says**
> "<quote or close paraphrase>" — <Document title>, §<section>, <date> ([link](…))

**Conditions & process**
- <who approves, deadlines, forms — each with a source>

**To confirm with HR** (if any)
- …

**Shareable version** (≤ 60 words)
…

_Sources searched: Confluence ✓ · Drive ✓ · Gmail (HR announcements) ✓_
```

## Quality checks
- Every sentence in the answer maps to a cited document section; nothing comes from general knowledge.
- The cited document matches the user's country, entity and population, and is the latest found version.
- Conflicts between sources are shown, not silently resolved.
- "Not found" answers contain no guessed rule and do contain an escalation path or the advice to ask HR.
- Personal-case questions get the general rule only, plus routing.

## Guardrails
- Never invent or extrapolate a policy, entitlement, number of days, amount or deadline. Legal minimums from
  labor law are out of scope unless an official internal document states them.
- Not legal advice. For disputes, dismissals, discrimination, harassment or health matters, route to HR or the
  dedicated confidential channel without analyzing the case.
- Do not reveal other people's personal data found while searching (pay, absences, cases).
- Do not answer from a policy of another country or entity "by analogy".
