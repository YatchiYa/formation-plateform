---
name: gdpr-processing-check
description: "Screens a new or changed process, tool, project, data flow or vendor for GDPR before launch: personal data and special categories (Art. 9), purposes, candidate legal basis (Art. 6), the Art. 5 principles, retention, recipients and processors (Art. 28), transfers outside the EEA, data subject information, DPIA triggers (Art. 35 and EDPB criteria) and a draft record of processing entry (Art. 30), then routes open points to the DPO. Not legal advice. Use whenever someone plans to collect, reuse, share, combine or analyse personal data of customers, teammates or partners, or onboards a SaaS or AI tool, even if they never mention GDPR. Triggers - GDPR check, privacy check, do I need a DPIA, personal data, data protection review, vérification RGPD, check RGPD, faut-il une AIPD, données personnelles, registre des traitements, analyse d'impact, conformité RGPD."
---

# GDPR processing check

Gives a project owner a first, structured GDPR screening of their processing, so they arrive at the DPO with the
right facts, a draft record entry and a clear list of open questions. The DPO and Legal make the final assessment.

## When to use
- A new tool, app feature, campaign, survey, loyalty mechanic, store device or data pipeline uses personal data.
- Existing data will be reused for a new purpose, combined with other data, or shared with a vendor or partner.
- A vendor (SaaS, agency, AI tool) will access customer or teammate data.
- Not for: AI-specific risk tiering under the EU AI Act (use `ai-use-case-risk-screen`, and run both for AI tools),
  checking against an internal policy document (use `policy-compliance-check`), or answering a customer's data
  request (route to the privacy process).

## Inputs
- Description of the processing: what, why, who, which systems, which vendor (required).
- Data subjects: customers, prospects, teammates, candidates, children, partners (required).
- Data fields or categories (required; a schema, form or screenshot is ideal).
- Countries involved and where data is hosted or accessed from (optional, default: ask if any vendor is involved).
- Internal privacy templates: record of processing, DPIA template, retention schedule (optional; search Drive/
  Confluence).

## Sources
1. **Drive and Confluence**: internal privacy policy, retention schedule, record-of-processing template, DPIA
   template, DPO contact and procedure, approved vendor list.
2. **Jira / Confluence**: the project's specs or epics describing data flows.
3. **Databricks (SQL)**: optional, table schemas to list the actual fields (column names only, never row data).
4. **GitHub**: optional, data models or tracking plans in the repository.
5. **Gmail**: vendor documentation, data processing agreement drafts.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Map the data**: list data subjects, data categories and fields, sources, systems, recipients, processors,
   hosting and access locations. Flag **special categories (Art. 9)**: racial or ethnic origin, political opinions,
   religious or philosophical beliefs, trade union membership, genetic data, biometric data for unique
   identification, health, sex life or sexual orientation; and **criminal data (Art. 10)**. Sport data can reveal
   health (injuries, heart rate, medical certificates): treat it as potentially Art. 9.
2. **Purposes**: one line per purpose, specific and explicit. Different purposes may need different bases.
3. **Candidate legal basis per purpose (Art. 6(1))**: (a) consent, (b) contract, (c) legal obligation, (d) vital
   interests, (e) public task, (f) legitimate interests. For (f), outline the three-part test (interest, necessity,
   balancing) for the DPO. For employees, consent is rarely appropriate because of the imbalance of power. For Art. 9
   data, an Art. 9(2) condition is also needed. Present these as hypotheses for the DPO, never as conclusions.
4. **Principles check (Art. 5)**: lawfulness, fairness and transparency; purpose limitation; data minimisation
   (fields not needed → propose removal); accuracy; storage limitation (retention per category, from the internal
   schedule or "to define"); integrity and confidentiality; accountability.
5. **Processors and transfers**: each vendor needs Art. 28 processor terms; any access or hosting outside the EEA
   needs a Chapter V tool (adequacy decision under Art. 45, or appropriate safeguards such as standard contractual
   clauses under Art. 46) and a transfer assessment. Mark each as "in place / to check".
6. **Rights and information**: how people are informed (Art. 13/14), how they exercise access, erasure, objection
   (Art. 21, absolute for direct marketing), and whether solely automated decisions with legal or similarly
   significant effects occur (Art. 22).
7. **DPIA screening (Art. 35)**: mandatory cases in Art. 35(3) — systematic and extensive evaluation incl. profiling
   with legal or similar effects; large-scale special-category or criminal data; large-scale systematic monitoring
   of publicly accessible areas. Then the EDPB criteria (see Reference): two or more met → a DPIA is likely
   required. Also check the national supervisory authority's list if found in Drive/Confluence.
8. **Draft the Art. 30 record entry** and the list of questions for the DPO.

## Output format
```markdown
# GDPR screening — <processing name> · <date>
> Not legal advice. First screening to prepare the DPO review.
**Result:** DPIA <likely required | not indicated | to decide with DPO> · Open points: <n> · Blocking: <n>

### Data map
| Data subjects | Data categories / fields | Art. 9/10? | Source | Systems | Recipients / processors | Location |
|---------------|--------------------------|-----------|--------|---------|-------------------------|----------|

### Purposes and candidate legal basis
| Purpose | Candidate basis (Art. 6) | Art. 9(2) condition if needed | Reasoning / to confirm |
|---------|--------------------------|-------------------------------|------------------------|

### Principles (Art. 5)
| Principle | Status ✅/⚠️/❌ | Finding | Action |
|-----------|----------------|---------|--------|

### Processors and transfers
| Vendor | Role | Art. 28 terms | Outside EEA? | Transfer tool | Status |
|--------|------|--------------|--------------|---------------|--------|

### DPIA screening
- Art. 35(3) case: <none | which>
- EDPB criteria met: <list> → <count>/9

### Draft record of processing (Art. 30)
Controller · Purposes · Categories of data subjects · Categories of data · Recipients · Transfers · Retention ·
Security measures: <one line each>

### Questions for the DPO
1. <…>
```

## Quality checks
- Every field in the data map is classified, and every Art. 9 candidate is flagged.
- Each purpose has exactly one candidate basis and a "to confirm" note.
- Retention is a period from the internal schedule (with link) or "to define", never invented.
- The DPIA result follows the rule: any Art. 35(3) case or ≥ 2 EDPB criteria → "likely required".
- Every article cited matches the topic (5, 6, 9, 10, 13/14, 21, 22, 28, 30, 35, Chapter V).

## Guardrails
- Not legal advice. Never conclude that a processing "is compliant"; the DPO decides.
- Work on descriptions and schemas, not on real personal data. Do not query or display actual records.
- Do not recommend launching before blocking points (no legal basis, missing processor terms, unassessed
  transfers, DPIA likely but not done) are cleared by the DPO.
- Draft only: the record entry and DPO request are sent after the user confirms.

## Reference
EDPB DPIA criteria (Guidelines WP248 rev.01): evaluation or scoring; automated decision-making with legal or similar
effect; systematic monitoring; sensitive or highly personal data; large scale; matching or combining datasets;
vulnerable data subjects (including employees and children); innovative use or new technology; processing that
prevents people from exercising a right or using a service or contract.
