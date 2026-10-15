---
name: customer-persona-builder
description: "Builds evidence-based customer personas from research, reviews, survey answers, customer service themes and aggregated purchase data, framed around jobs-to-be-done and sport practice rather than stereotypes: context and triggers, functional, emotional and social jobs, barriers, decision criteria, channels, with each trait linked to evidence and a confidence level. Use whenever someone needs personas, target profiles, customer segments for a brief, or wants to understand who buys a range, even if they ask for 'a typical customer'. Triggers - personas, customer persona, target audience, jobs to be done, customer segments, who is our customer, persona client, cible marketing, profil client, segments clients, qui sont nos clients, client type."
---

# Customer persona builder

Creates personas that a product, marketing or store team can act on, because every trait comes from evidence and
describes what people try to get done in their sport, not who they are on paper.

## When to use
- Before a campaign brief, a product brief or a range plan, to agree on who we serve.
- When existing personas are old, untraceable or rely on clichés.
- After a research study, a survey or a review analysis, to turn findings into usable profiles.
- Not for: planning new research (use `user-research-plan`), synthesizing raw interviews (use
  `research-synthesis`), mining reviews alone (use `product-review-insights`) or writing the campaign itself (use
  `campaign-brief`).

## Inputs
- Scope: sport, category, range or service, and market (required).
- Evidence: research reports, interview notes, surveys, reviews, customer service themes, aggregated data (required;
  search Drive and Confluence first).
- Number of personas (optional, default: 3–4, enough to cover the main jobs, no more).
- Use of the personas: campaign, product, store, service (optional).

## Sources
1. **Drive and Confluence**: user research reports, interview syntheses, surveys, existing personas and segmentation
   studies, product briefs.
2. **Databricks (SQL or Polco)**: aggregated behavior only (purchase frequency, category mix, channel split, basket,
   seasonality) for segments of ≥ 100 customers. Show the queries used.
3. **Tableau**: customer or loyalty dashboards with segment definitions.
4. **Slack, Chat and Gmail**: customer service or store feedback threads summarizing recurring needs.
5. **Airtable or Jira**: research repositories or insight logs.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Inventory the evidence**: list each source with type (qualitative / quantitative), sample size, date and
   market. Flag evidence older than 3 years or from another market.
   Never simulate a source. If no study or review was actually retrieved, write « Evidence: 0 sources », give at
   most proto-personas labeled *hypotheses to validate* (all traits *weak*, Quote line « [no verbatim available] »),
   and ask for the documents.
2. **Extract jobs-to-be-done** as statements: "When <situation>, I want to <motivation>, so I can <outcome>". Separate
   functional (stay dry on a 3-day trek), emotional (feel safe on my first ski touring outing) and social (keep up
   with my running club) jobs.
3. **Cluster by job and context**, not by demographics. Typical axes in sport: practice level and frequency,
   motivation (performance, health, pleasure, social, nature), context (alone, family, club), and moment (starting,
   progressing, returning after a break).
4. **Build each persona**: name the persona by its job ("The trail convert", "The weekend family camper"), not with a
   fake first name and photo. Add triggers, barriers (price, fear of wrong size, lack of knowledge), decision criteria,
   information channels, what "success" looks like.
5. **Link evidence** to every trait with a source and a confidence: *strong* (several sources agree, quant + qual),
   *medium* (one solid source), *weak* (anecdote) — weak traits are labeled hypotheses.
6. **Size** each persona only if data allows; otherwise write "size unknown".
7. **Make it usable**: for each persona, 2–3 implications for messaging, product, store advice or service, and the
   open questions to research next.

## Output format
```markdown
# Personas — <scope> (<market>)
_Evidence: <N> sources (<list with dates>) · Gaps: <one line>_

## Overview
| Persona | Core job | Moment | Size (source) | Confidence |
|---------|----------|--------|---------------|------------|

## <Persona name — named by its job>
- **Job statement:** When …, I want to …, so I can …
- **Context:** <practice, frequency, setting>
- **Triggers:** …
- **Barriers:** …
- **Decision criteria:** 1. … 2. … 3. …
- **Channels:** …
- **Quote:** «…» _(source, anonymized)_
- **Implications:** messaging … · product … · store/service …
| Trait | Evidence | Confidence |
|-------|----------|------------|

## Open questions for research
- …
```

## Quality checks
- Every trait in every persona has a source and a confidence level.
- Personas differ by job or context; none is defined only by age, gender or income.
- Weak-evidence traits are labeled hypotheses.
- No numbers (sizes, shares) without a cited query or study.
- Every quote and every « Evidence » cell names a document actually retrieved in this session.
- Each persona has at least two concrete implications.

## Guardrails
- No stereotypes: do not assign sports, levels or budgets by gender, age, origin or disability. Use demographics only
  when the evidence shows them and they matter for the job.
- Privacy: work on aggregated or anonymized data; quotes are anonymized; no individual customer profiles and no
  segments smaller than 100 people from transactional data.
- Do not create sensitive-data segments (health conditions, religion, ethnicity) even if a proxy exists.
- Never invent research findings, survey figures or quotes. Missing evidence becomes an open question.
