---
name: sop-writer
description: "Writes a standard operating procedure (SOP) that people can follow on the job: purpose, scope, roles (RACI), prerequisites, numbered steps written as one action per step with the expected result, control points and records, safety and quality warnings, exceptions and escalation, revision table, plus suggestions for visuals and a one-page job aid. Use whenever someone needs to document how a recurring task is done by people (for IT systems, alerts and outages use runbook-writer), standardize a practice across stores, warehouses or teams, or train new teammates, even if they only ask to 'write down how we do it'. Triggers - SOP, standard operating procedure, work instruction, procedure, how-to process, job aid, checklist, mode opératoire, procédure, standard de travail, instruction de travail, formaliser un process."
---

# SOP writer

Produces a procedure a new teammate can follow correctly the first time, and an auditor can check: clear steps,
explicit controls, named records, and an owner who keeps it up to date.

## When to use
- A recurring task is done differently by each person, store or shift and needs a standard.
- A process change, audit finding or incident requires a written procedure.
- Onboarding: a new teammate needs a step-by-step guide (e.g. receiving a delivery, opening the cash desk, handling
  a product recall on the shelf, closing the workshop).
- Not for: improving or redesigning the process first (use `process-improvement-kaizen`), an IT operations runbook
  (use `runbook-writer`), a customer-facing help article (use `kb-article-writer`), or checking a process against a
  policy (use `policy-compliance-check`).

## Inputs
- The task or process and who performs it (required).
- How it is done today: notes, transcript, video description, existing draft, or an interview with the expert
  (required; search Drive and Confluence for an existing version first).
- Applicable rules: internal policy, safety or quality standard, legal requirement (optional; searched, never
  invented).
- Format target: full SOP, one-page job aid, or both (optional, default: both).

## Sources
1. **Drive and Confluence**: existing procedures and templates (reuse the internal SOP template and numbering if one
   exists), policies, safety and quality standards, audit reports, training material.
2. **Meet transcripts in Drive and Chat / Slack**: expert explanations, frequent questions from teammates (good
   candidates for warnings and FAQs).
3. **Jira**: incidents or tickets caused by the task done wrong, to turn into control points.
4. **Gmail**: instructions sent by the process owner, recall or quality notices.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Frame the SOP: purpose (why, what risk it controls), scope (where it applies, where it does not), trigger (what
   starts it), output (what "done" looks like), frequency.
2. Define **roles** with a RACI: who performs, who is accountable, who is consulted, who is informed. Use roles
   (e.g. "reception teammate", "store manager"), not names.
   Every row has exactly one A: when the performer is also accountable write « R/A »; a row with only R, C and I
   is incomplete.
3. List **prerequisites**: training, access, tools, PPE (personal protective equipment), materials.
4. Write the **steps**: numbered, one action per step, starting with an imperative verb, ≤ 20 words, followed by
   the expected result when it is not obvious. Group into phases of 3–7 steps. Use decision points as "If … then go
   to step N". Fill the step numbers in decision points only after the final numbering, then check each target is
   the step that handles that case. Split any step over 20 words into two steps.
5. Insert **controls** where errors are costly: what is checked, by whom, against which criterion, and the record
   kept (form, system entry, photo, signature). Add **warnings** before the step they concern: ⚠️ Safety,
   ❗ Quality, 🔒 Data / privacy.
6. Write **exceptions and escalation**: the 3–5 most likely deviations and what to do, who to call.
7. Suggest **visuals**: where a photo, diagram or swimlane helps (e.g. correct pallet stacking, label position).
   Describe them; do not fabricate images.
8. Add the **document control** block: owner, version, effective date, review date (default 12 months, *proposal*),
   change history.
9. Produce the **one-page job aid**: the steps as a checklist, the warnings, the escalation contact role.
10. Run a "**newcomer test**": reread as someone on day 1 and list any undefined term or missing step as open
    questions to the expert.

## Output format
```markdown
# SOP — <Title> · <ID if any> · v<0.x draft>
| Owner | Effective date | Review date | Applies to |
|-------|----------------|-------------|-----------|

## 1. Purpose and scope
<why, risk controlled> · In scope: … · Out of scope: …
**Trigger:** … · **Output:** … · **Frequency:** …

## 2. Roles (RACI)
| Activity | <Role A> | <Role B> | <Role C> |
|----------|----------|----------|----------|

## 3. Prerequisites
- Training / access / tools / PPE: …

## 4. Procedure
### Phase A — <name>
1. <Verb + object>. → Expected: …
2. ⚠️ Safety: … then <verb + object>.
3. If <condition>, go to step 7.
**Control A:** <what> · by <role> · criterion <…> · record <…>

## 5. Exceptions and escalation
| Situation | What to do | Escalate to (role) |
|-----------|-----------|--------------------|

## 6. Records
| Record | Where kept | Retention |
|--------|-----------|-----------|

## 7. Suggested visuals
- Step <n>: <photo / diagram description>

## 8. Change history
| Version | Date | Change | Author |
|---------|------|--------|--------|

---
## Job aid (one page)
- [ ] <step> …
⚠️ … · Problem? → <role>

**Open questions for the process owner:** …
```

## Quality checks
- Every step starts with a verb, contains one action and is ≤ 20 words.
- Every decision point leads to an existing step number; no dead ends.
- Each control names what, who, criterion and record.
- Every rule or regulation cited has a source link; none is invented.
- Roles in the RACI have exactly one "A" per activity.
- The job aid matches the procedure step for step.

## Guardrails
- Never invent safety, legal or quality requirements (e.g. weight limits, temperatures, retention periods); cite the
  source or leave `[to confirm with <owner>]`.
- Safety-critical steps (machinery, ladders, electrical, chemicals, manual handling) must be validated by the
  competent person (health and safety); say so at the top of the draft.
- Records that contain personal data state a retention period from policy or `[to confirm with data protection]`.
- Draft only: do not publish to Confluence or Drive as the official version without explicit confirmation by the
  process owner.
