---
name: policy-compliance-check
description: "Checks a document, process, project, campaign or practice against one or more internal policies found in Drive or Confluence: breaks each policy into testable requirements, maps the evidence, rates each requirement compliant, partial, gap or not assessable with exact citations on both sides, and proposes remediation actions with owners. Not legal advice. Use whenever someone asks whether something follows the rules, prepares an internal audit or control, or wants to be sure before launch, even if they say 'are we OK with the policy'. Triggers - policy compliance check, does this comply with, check against policy, internal audit prep, gap analysis, conformité à la politique, vérifier la conformité, est-ce conforme, analyse d'écarts, contrôle interne, respect de la procédure."
---

# Policy compliance check

Gives the owner of a document or process a clear, cited gap analysis against an internal policy: what is met, what
is missing, what to fix, so issues are solved before an audit or a launch rather than after.

## When to use
- Before launching a process, campaign, tool or partnership governed by an internal policy (purchasing, travel,
  data, security, brand, sustainability, ethics, health and safety).
- Preparing an internal audit or control, or answering an auditor's question.
- A teammate wonders if a practice in their team still follows an updated policy.
- Not for: GDPR screening of a processing (use `gdpr-processing-check`), AI Act classification (use
  `ai-use-case-risk-screen`), policy questions from customers (use `customer-policy-qa`) or teammates on HR rules
  (use `hr-policy-qa`), or sustainability claims in marketing (use `green-claim-checker`).

## Inputs
- The object to check: document, process description, project page, campaign, form (required).
- The policy or policies to check against (required: name or link; search Drive/Confluence if only the topic is
  given, and confirm the version with the user if several exist).
- Scope: country, entity, team (optional, default: the scope stated in the policy).

## Sources
1. **Drive and Confluence**: the policy (latest approved version, with owner and date), related standards,
   procedures and templates, previous audits or controls on the same topic.
2. **Jira**: tickets, approvals or workflow evidence that show how the process actually runs.
3. **Gmail / Chat / Slack**: approvals or exceptions granted, only if the user points to them.
4. **Airtable / Databricks**: registers or logs used as evidence (e.g. approvals register), queried for counts only.
5. **GitHub**: optional, configuration evidence for IT or security policies.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Pin the policy**: title, version, date, owner, scope. If the policy found is a draft, outdated or out of scope,
   say so before continuing.
2. **Extract requirements**: split the policy into atomic, testable statements. Keep "must/shall" (mandatory) apart
   from "should/recommended". Number them R1, R2… with the policy section.
3. **Map evidence** for each requirement: where the object meets it (quote + location), contradicts it, or is
   silent. Evidence must be in the object or in a cited source; the user's statement counts but is labeled
   "declared".
4. **Rate** each requirement: ✅ Compliant · 🟠 Partial · ❌ Gap · ❓ Not assessable (evidence missing).
   Recommended items can only be 🟠 at worst, never ❌.
5. **Assess severity** of each gap: High (mandatory, affects safety, legal, money or personal data, or is
   systematic) · Medium (mandatory, isolated, workaround exists) · Low (recommended or formal).
6. **Propose remediation**: one action per gap, owner role, and whether it blocks launch. Note if an exception
   process exists in the policy and who approves exceptions.
7. **Summarize** with a compliance score: compliant mandatory requirements / assessable mandatory requirements.

## Output format
```markdown
# Compliance check — <object> vs <policy title v.x (date)>
> Not legal advice. Internal gap analysis; the policy owner or Legal/Compliance confirms.
**Result:** <n>/<m> mandatory requirements met · <n> gaps (<n> high) · <n> not assessable · Launch-blocking: <yes/no>
_Policy owner: <role> · Scope: <…> · Object version: <link/date>_

### Gaps to fix
| Req. | Requirement (policy §) | Finding (evidence) | Severity | Action | Owner | Blocking |
|------|-----------------------|--------------------|----------|--------|-------|----------|

### Full assessment
| Req. | Type (must/should) | Requirement (§) | Rating | Evidence |
|------|-------------------|-----------------|--------|----------|

### Not assessable — evidence needed
- R<n>: <what proof is needed and from whom>

### Exceptions
<exception process and approver from the policy | none described>
```

## Quality checks
- Every requirement cites the policy section; every rating cites evidence or says "no evidence".
- Mandatory and recommended requirements are labeled and rated per step 4.
- The score counts only assessable mandatory requirements, and the numbers add up.
- Each gap has an action, an owner role and a blocking flag.
- The policy version and date are stated, and outdated or draft policies are flagged.

## Guardrails
- Not legal advice. The result is a self-assessment, not an audit opinion or certification.
- Never invent a policy requirement or extend a policy beyond its written scope; if no policy is found, stop and say so.
- Findings describe processes and documents, not individuals; do not name teammates as responsible for gaps.
- Read only: no ticket, email or document change without the user's confirmation.

## Example
Input: « Notre process de prise de photos clients en magasin pour les réseaux sociaux est-il conforme à la politique
image et données ? »
→ Policy pinned (title, version, owner). 9 requirements extracted (6 mandatory). Result: 4/5 assessable mandatory
requirements met, 1 gap (high): no written consent kept for minors' photos (§ x.y) → action: consent form and storage
rule, owner: store manager role, blocking: yes. 1 not assessable: retention of photos, evidence needed from the
social media team. Suggest also running `gdpr-processing-check`.
