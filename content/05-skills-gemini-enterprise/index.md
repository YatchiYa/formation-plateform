---
type: "category"
title: "Skills Gemini Enterprise"
icon: "🧰"
description: "160 skills prêts à importer dans Gemini Enterprise, classés en 17 métiers. Lisez-les, téléchargez-les, adaptez-les."
---
# Company skill library for Gemini Enterprise

160 ready-to-upload **skills** (Agent Skills `SKILL.md` standard) for Company teammates in Gemini Enterprise.
They cover 17 domains, from personal productivity to HR, B2B sales, store operations, data and engineering.
The skills are written for the connectors already set up in the tenant: **Google Workspace** (Gmail, Calendar, Drive,
Chat, Meet), **Jira and Confluence**, **Slack**, **GitHub**, **Airtable**, **Tableau** and **Databricks** (SQL MCP and Polco).

→ The full list is in [CATALOG.md](00-catalogue.md), with one line per skill.

## Layout

```
skills-agents-gemini-entreprise/
├── README.md                ← this file
├── CATALOG.md               ← generated list of the 160 skills
├── docs/SKILL-STANDARD.md   ← authoring rules every skill follows
├── skills/
│   ├── 01-productivity/          (13)  daily-briefing, inbox-triage, meeting-prep, meeting-notes-to-actions…
│   ├── 02-communication/         (10)  executive-summary-writer, translation-localizer, presentation-storyline…
│   ├── 03-management-leadership/ (10)  one-on-one-prep, feedback-sbi-writer, okr-builder, decision-memo…
│   ├── 04-hr-people/             (15)  job-description-writer, interview-kit-builder, onboarding-plan-builder…
│   ├── 05-sales-b2b/             (12)  account-research, b2b-proposal-builder, tender-response-builder…
│   ├── 06-retail-store-ops/      (12)  store-daily-brief, store-performance-analysis, sport-universe-review…
│   ├── 07-customer-service/      (8)   customer-reply-drafter, ticket-triage, product-review-insights…
│   ├── 08-marketing-ecommerce/   (11)  campaign-brief, product-page-copy, seo-content-brief, ab-test-readout…
│   ├── 09-product-design/        (11)  product-brief, field-test-protocol, eco-design-review, user-story-writer…
│   ├── 10-data-analytics/        (10)  databricks-sql-builder, data-question-answerer, metric-anomaly-investigator…
│   ├── 11-engineering-it/        (12)  pr-review-assistant, incident-postmortem, tech-spec-writer, runbook-writer…
│   ├── 12-project-management/    (9)   project-charter, project-status-report, raid-log-builder…
│   ├── 13-finance-procurement/   (7)   budget-variance-analysis, business-case-builder, supplier-evaluation…
│   ├── 14-legal-compliance/      (6)   contract-summary, gdpr-processing-check, ai-use-case-risk-screen…
│   ├── 15-sustainability/        (3)   green-claim-checker, csr-data-request, circular-offer-ideas
│   ├── 16-knowledge-search/      (7)   cross-source-search, expert-finder, topic-digest, glossary-builder…
│   └── 17-ai-adoption/           (4)   skills-navigator, skill-builder, prompt-improver, ai-use-case-finder
│       └── <skill-name>/SKILL.md      one file per skill (name + description frontmatter, instructions)
├── dist/                    ← generated, ready to upload
│   ├── md/<domain>/<skill>.md     upload as Markdown
│   ├── zip/<domain>/<skill>.zip   upload as ZIP (SKILL.md at the zip root)
│   └── all-skills-md.zip          everything, to hand to an admin
├── evals/
│   ├── prompts.json         320 realistic user prompts (FR + EN), 2 per skill
│   └── results/             Gemini routing and execution results
└── scripts/
    ├── build.py             validate → dist/ + CATALOG.md + skills-navigator
    └── eval_gemini.py       routing and execution evals on Vertex AI
```

## Every skill is built the same way

The rules are in [docs/SKILL-STANDARD.md](00-standard-skill.md) and checked by `scripts/build.py`.

- **Frontmatter:** only `name` and `description`. The description says what the skill does and when to use it, with
  trigger phrases in **English and French**, so that Gemini's automatic selection works whichever language users write in.
- **Body sections, in order:** When to use (with a "Not for:" line that sends the user to sibling skills) → Inputs
  → Sources (which connector to query for what) → Workflow (the real method: frameworks, formulas, checklists) →
  Output format (an exact template) → Quality checks → Guardrails.
- **Rules for the whole library:**
  - No invented facts: every number, policy and name is cited or labeled as an assumption.
  - **Draft first, act after confirmation:** nothing is sent, posted or created in Jira without it.
  - Answers come in the user's language, and personal data is kept to what the task needs (GDPR).
  - People skills support human decisions and never rank or reject anyone, because the EU AI Act classes AI used
    in employment as high-risk.
- **One file per skill:** Gemini Enterprise says skills "work best with Canvas when a skill has only one SKILL.md file".

## Install in Gemini Enterprise

Prerequisites (admin):
1. Skills are on by default. If the **Skills** tab is missing, an admin turns it back on in *Manage team → General
   → Skills → Enable skills*.
2. To publish skills to teams, turn on *General settings → Sharing → Enable skill sharing*. You can make shared skills
   need admin review first.
3. Editions: Standard, Plus and Pay-as-you-go users can upload. **Frontline** users can install and use shared skills,
   but cannot upload their own.

Upload one skill:
1. Gemini Enterprise → **Skills** → **+ Add** → **Upload skill**.
2. Choose `dist/zip/<domain>/<skill>.zip` (recommended, the documented format) or `dist/md/<domain>/<skill>.md`.
3. Click **Import**. The name and description are read from the file, and the skill is on by default.

Roll out to teammates: upload once from a skill-owner account, then use **⋮ → Share** with the persona's group
addresses (comma-separated). Teammates find the skills under *Skills → + Add → Browse skills → Shared with me*
and click **Install**.

Use: type `/` in the chat box to pick a skill, or write `@skill-name …`, or simply ask. Gemini picks a skill
automatically from its description. Note that one prompt cannot use a skill **and** an agent at the same time.

> There is no public API to import skills in bulk (checked October 2026), so uploads are done in the UI.
> Start with `skills-navigator` and the persona pack below.

### Persona packs (recommended rollout)

Installing all 160 skills for everyone is possible, but people adopt them faster with a focused pack per persona. Everyone
gets the **Core pack**, plus the pack for their persona.

| Pack | Skills |
|------|--------|
| **Core (everyone)** | skills-navigator, daily-briefing, weekly-review, inbox-triage, email-reply-drafter, thread-catchup, meeting-prep, meeting-notes-to-actions, follow-up-tracker, message-rewriter, translation-localizer, cross-source-search, prompt-improver |
| **Store manager** | store-daily-brief, store-performance-analysis, sport-universe-review, team-huddle-brief, staff-planning-assistant, stock-availability-analysis, seasonal-operation-planner, local-sport-event-planner, workshop-service-review, store-action-plan, store-incident-report, one-on-one-prep, feedback-sbi-writer |
| **Area / regional manager** | store-visit-report, store-performance-analysis, store-action-plan, okr-progress-review, decision-memo, steering-committee-pack, team-health-check |
| **HR / people partner** | all of `04-hr-people`, difficult-conversation-prep, change-communication-plan, gdpr-processing-check |
| **People manager** | one-on-one-prep, feedback-sbi-writer, difficult-conversation-prep, performance-review-writer, career-development-plan, team-retrospective, okr-builder, new-manager-90-day-plan |
| **B2B sales (Company Pro)** | all of `05-sales-b2b`, sales-call-recap, objection-handler, contract-summary |
| **Customer service** | all of `07-customer-service`, message-rewriter |
| **Marketing & e-commerce** | all of `08-marketing-ecommerce`, green-claim-checker, presentation-storyline |
| **Product & design** | all of `09-product-design`, research-synthesis, eco-design-review, circular-offer-ideas |
| **Data & analytics** | all of `10-data-analytics`, insight-storyteller, presentation-storyline |
| **Engineering & IT** | all of `11-engineering-it`, architecture-decision-record, knowledge-capture-page |
| **PMO / transformation** | all of `12-project-management`, change-communication-plan, workshop-designer |
| **Finance & procurement** | all of `13-finance-procurement`, contract-summary, nda-triage |
| **Legal, DPO, CSR** | all of `14-legal-compliance` and `15-sustainability` |

## Customize for Company

The skills never invent internal facts. They look for them in Drive and Confluence, or ask the user. To make them
sharper, a skill owner can add the internal links in the **Sources** section of a skill: the competency framework,
KPI definitions, brand book, return policy, Tableau view names or Databricks catalogs. Then run `python3 scripts/build.py`
and upload the new version.

To create a new skill: use the `skill-builder` skill in Gemini, or copy any folder, edit it and run the build.

## Verify and build

```bash
pip install pyyaml
python3 scripts/build.py --check   # validate only
python3 scripts/build.py           # validate + regenerate dist/, CATALOG.md and skills-navigator
PROJECT=<gcp-project> python3 scripts/eval_gemini.py routing     # does Gemini pick the right skill?
PROJECT=<gcp-project> python3 scripts/eval_gemini.py execution   # does it follow the skill well?
```

VERIFICATION_PLACEHOLDER

## Sources and credits

- Format: the [Agent Skills specification](https://agentskills.io/specification), and the Gemini Enterprise docs
  [Create and manage skills](https://docs.cloud.google.com/gemini/enterprise/docs/skills) and the
  [user help page](https://support.google.com/g/answer/18067667).
- Inspiration (structure and coverage, no content copied): [anthropics/skills](https://github.com/anthropics/skills) and
  [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0).
- The regulatory points used in the skills (GDPR, the EU AI Act as amended by Regulation (EU) 2026/1744, Directive (EU)
  2024/825, Omnibus price rule, CSRD) were checked as of **October 2026**. They are not legal advice, and Legal should confirm them.
