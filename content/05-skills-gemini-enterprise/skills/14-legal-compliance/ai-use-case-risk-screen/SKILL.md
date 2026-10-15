---
name: ai-use-case-risk-screen
description: "Screens an AI use case, tool or agent against the EU AI Act (Regulation (EU) 2024/1689): checks Art. 5 prohibited practices, Annex III high-risk areas and the Art. 6(3) exception, Art. 50 transparency duties, general-purpose AI context, Company's role as provider or deployer, data and GDPR links, human oversight, and lists the required steps and owners, with a dated applicability note. Not legal advice. Use whenever someone plans, buys, builds or extends an AI system, chatbot, agent, scoring or recommendation model, especially in HR, customer service, stores or marketing, even if they do not mention the AI Act (to find where AI could help a team, use ai-use-case-finder). Triggers - AI Act check, AI risk screening, is this AI high-risk, AI use case compliance, can we use AI for, AI Act conformité, ce cas d'usage IA est-il à haut risque, analyse de risque IA, règlement IA, classification AI Act, usage IA autorisé."
---

# AI use case risk screen

Gives a project owner a first EU AI Act classification of their AI use case, the obligations that follow and who
must be involved, before money or data is committed. Legal, the DPO and the AI governance owners confirm.

## When to use
- A team wants to buy, build or configure an AI system, agent or model (including on Gemini Enterprise).
- An existing AI tool gets a new purpose, new users or new data (e.g. extended from marketing to HR).
- Procurement or a steering committee asks "what does the AI Act say about this?".
- Not for: the GDPR assessment of the same use case (use `gdpr-processing-check`, run both), finding AI use cases
  (use `ai-use-case-finder`), or checking a marketing claim (use `green-claim-checker`).

## Inputs
- Description: what the system does, its output (content, recommendation, decision, score), who uses it, who is
  affected (customers, teammates, candidates, public) (required).
- Origin: built in-house, bought, configured from a general-purpose model, and under whose name it is offered
  (required, determines provider vs deployer).
- Data used for input and training (optional, default: ask if personal or biometric data might be involved).
- Countries of use (optional, default: EU). Internal AI policy or governance process (optional; search Drive/
  Confluence).

## Sources
1. **Drive and Confluence**: internal AI policy, AI governance or review process, AI inventory, previous screenings,
   vendor documentation and instructions for use.
2. **Jira / Confluence**: project specs, epics or requests describing the use case.
3. **Gmail**: vendor answers on model, data and conformity documentation.
4. **GitHub**: optional, system prompts or model configuration if built in-house.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Is it an AI system?** Machine-based, some autonomy, infers from input how to generate outputs (predictions,
   content, recommendations, decisions) — Art. 3(1). Pure rule-based automation may fall outside; note uncertainty.
2. **Role**: *provider* (develops or has it developed and places it on the market or puts it into service under its
   own name) or *deployer* (uses it under its authority). A deployer becomes a provider of a high-risk system if it
   puts its name or trademark on it, substantially modifies it, or changes its intended purpose so it becomes
   high-risk (Art. 25).
3. **Prohibited practices (Art. 5)** — any match = stop and go to Legal: harmful manipulative or deceptive
   techniques; exploiting vulnerabilities due to age, disability or social or economic situation; social scoring
   leading to unjustified detrimental treatment; predicting criminal offences based solely on profiling or
   personality traits; untargeted scraping of facial images to build facial recognition databases; emotion
   recognition in the workplace or in education (except medical or safety reasons); biometric categorisation to
   infer race, political opinions, trade union membership, religious or philosophical beliefs, sex life or sexual
   orientation; real-time remote biometric identification in public spaces for law enforcement (narrow exceptions).
4. **High-risk**: (a) Annex III areas: 1 biometrics; 2 critical infrastructure; 3 education and vocational training;
   4 employment, workers management and access to self-employment (recruitment and selection, decisions on terms,
   promotion, termination, task allocation based on behaviour or traits, monitoring and evaluation); 5 access to
   essential private and public services (incl. public benefits, creditworthiness, life and health insurance
   pricing, emergency call triage); 6 law enforcement; 7 migration, asylum, border control; 8 justice and
   democratic processes. (b) Art. 6(1): safety component of a product covered by Annex I legislation needing
   third-party conformity assessment. **Art. 6(3) exception**: an Annex III system is not high-risk if it does not
   pose a significant risk, e.g. only a narrow procedural task, improving a completed human activity, detecting
   patterns without replacing human assessment, or a preparatory task — but never when it profiles natural persons.
   The provider must document that assessment (Art. 6(4)).
5. **Transparency (Art. 50)**: people must be told they interact with an AI system unless obvious; providers of
   generative systems mark synthetic content in a machine-readable way; deployers disclose deep fakes and AI-
   generated text published to inform the public on matters of public interest (unless human-reviewed under
   editorial responsibility); deployers inform people exposed to emotion recognition or biometric categorisation.
6. **General-purpose AI**: if a GPAI model is used through a vendor, GPAI obligations (Chapter V) sit with the model
   provider; Company's obligations come from its own use case. Ask the vendor for documentation.
7. **Obligations by tier**, see Reference. Always add: AI literacy for staff using the system (Art. 4), GDPR check,
   internal AI governance step, and worker information/consultation duties for workplace use.
8. **Human oversight design**: who reviews outputs, when they can override, what the system must never do alone.
9. **Applicability date** and remaining questions for Legal.

## Output format
```markdown
# AI Act screening — <use case> · <date>
> Not legal advice. First classification under Regulation (EU) 2024/1689; Legal confirms.
**Tier: <Prohibited | High-risk (Annex III point x / Art. 6(1)) | Transparency (Art. 50) | Minimal>** — <one-line reason>
**Company's role:** <provider | deployer | to clarify> · **Confidence:** <high | medium | low>

### Screening
| Test | Result | Why (article) |
|------|--------|---------------|
| AI system (Art. 3(1)) | | |
| Prohibited practice (Art. 5) | | |
| Annex III area / Art. 6(1) | | |
| Art. 6(3) exception | | |
| Transparency (Art. 50) | | |

### Required steps
| Step | Owner | Before go-live? |
|------|-------|-----------------|

### Human oversight
- <who, when, override, never-alone rules>

### Data and GDPR
- <personal data? special categories? → run gdpr-processing-check>

### Applicable from
<date(s) per the timeline in Reference, with the caveat line>

### Questions for Legal / vendor
1. <…>
```

## Quality checks
- Each of the five screening tests has a result and an article reference.
- A high-risk claim names the Annex III point or Art. 6(1); an Art. 6(3) exception is never applied to profiling.
- The role (provider/deployer) is justified with the Art. 25 test when the system is bought and customised.
- Every required step has an owner role.
- The timeline section includes the caveat on possible amendments.

## Guardrails
- Not legal advice; validate with Legal and the DPO before any decision. When uncertain between two tiers, report
  the stricter one and the open question.
- HR uses (recruitment, evaluation, promotion, termination, task allocation, monitoring) are presumed high-risk
  pending Legal review; the AI never takes these decisions alone.
- Do not state fines as likely outcomes. Penalty ceilings (Art. 99) may be quoted only as context.
- Do not invent vendor certifications or conformity status; ask the vendor and cite their answer.

## Reference
Deployer duties for high-risk systems (Art. 26): use per instructions; competent human oversight; relevant input
data; monitor and report serious incidents; keep logs at least six months; inform workers' representatives and
affected workers before workplace use; inform people subject to decisions. Fundamental rights impact assessment
(Art. 27) for public bodies, private entities providing public services, and Annex III point 5(b)/(c) uses.
Providers of high-risk systems: risk management, data governance, technical documentation, logging, transparency,
human oversight, accuracy and robustness, quality management, conformity assessment, registration (Art. 8–17, 43, 49).
Timeline (Art. 113 as amended by the Digital Omnibus on AI, Regulation (EU) 2026/1744, in force 27 Jul 2026):
in force 1 Aug 2024; prohibitions and AI literacy from 2 Feb 2025; GPAI and penalties from 2 Aug 2025; Art. 50
transparency from 2 Aug 2026 (grace period to 2 Dec 2026 for Art. 50(2) marking of systems already on the market);
Annex III high-risk from **2 Dec 2027**; Annex I (Art. 6(1)) high-risk from **2 Aug 2028**. The Omnibus also adds
a prohibition on systems producing non-consensual intimate imagery or CSAM. Dates checked October 2026, so confirm
with Legal that they have not changed again.
