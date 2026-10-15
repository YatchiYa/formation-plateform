---
name: regulatory-watch-digest
description: "Produces a dated regulatory watch digest on a topic (for example consumer law, product safety, data protection, AI, sustainability reporting, packaging, labour) from the sources the user provides or that are found in Drive, Gmail newsletters, Confluence and Slack: what changed, legal status and stage, key dates, who is affected inside Company, impact rating, actions and owners, each item linked to its source. Not legal advice. Use whenever someone asks what is new in a regulation, needs a monthly legal or compliance watch, or must brief a team on an upcoming rule, even if they just forward a newsletter. Triggers - regulatory watch, legal watch, what's new in regulation, regulatory update, compliance digest, veille réglementaire, veille juridique, nouveautés réglementaires, actualité réglementaire, synthèse réglementaire, nouvelle loi impact."
---

# Regulatory watch digest

Turns regulatory news and newsletters into a short, dated digest that tells each team what changes for them, when,
and what to do next. It reports what sources say; Legal confirms interpretation.

## When to use
- Monthly or quarterly watch on a topic for a team (legal, compliance, product, e-commerce, HR, sustainability).
- A newsletter, alert or article arrives and the user wants to know if it matters.
- Before a planning cycle, to list upcoming obligations and their dates.
- Not for: competitor moves (use `competitor-watch`), checking a project against an internal policy (use
  `policy-compliance-check`), or a deep analysis of one long legal text (use `long-document-digest`).

## Inputs
- Topic(s) and jurisdictions (required, e.g. "EU + France, product safety").
- Period (optional, default: since the last digest found, else last 30 days).
- Source material: links, PDFs, newsletters, or permission to search connected sources (required: at least one).
- Audience and teams to map impact to (optional, default: inferred from the topic).

## Sources
1. **Gmail**: legal newsletters and alerts in the period (law firms, trade associations, authorities), filtered by
   topic keywords.
2. **Drive and Confluence**: previous digests (to avoid repeats and track follow-ups), internal legal notes,
   the list of teams and owners per topic if it exists.
3. **Slack / Google Chat**: legal, compliance or public-affairs channels sharing updates.
4. **Jira**: open compliance actions linked to earlier items.
5. Links and files the user provides. Only official texts (e.g. Official Journal, authority websites) can confirm
   a legal status; secondary sources are labeled as such.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Collect** items in the period on the topic. For each, keep: title, source, publication date, link.
2. **Deduplicate** items about the same text; keep the most authoritative source and list the others.
3. **Classify the stage**: Proposal · In negotiation · Adopted / published · In force · Applicable from <date> ·
   Guidance or enforcement action · Court decision. Never upgrade a stage beyond what a source states.
4. **Extract key facts**: instrument and number (regulation, directive, national law, decree, guidance), scope,
   main obligations, dates (publication, entry into force, application, transition periods), sanctions only if stated.
   A directive needs national transposition: give the transposition deadline if stated, not national details unless
   sourced.
5. **Map impact** to Company activities and teams: product design and sourcing, stores, e-commerce, marketing,
   customer service, HR, data and IT, logistics, finance. Rate impact: High (new obligation affecting core
   activity or with near deadline) · Medium · Low · Watch (proposal stage).
6. **Propose actions**: who should analyse, decide or prepare, by when; link existing Jira actions if found.
7. **Track the past**: list items from the previous digest whose status changed.

## Output format
```markdown
# Regulatory watch — <topic> · <jurisdictions> · <period> (as of <date>)
> Not legal advice. Summary of sources; Legal confirms interpretation and impact.
**Top 3 this period:** 1. <…> 2. <…> 3. <…>

### Items
| Impact | Item (instrument) | Stage | Key dates | What changes | Teams | Source |
|--------|-------------------|-------|-----------|--------------|-------|--------|

### Details (High and Medium only)
**<Item>** — <stage>, <dates>
- What it requires: <…>
- Who is affected: <…>
- Action: <…> · Owner: <role> · By: <date>
- Source: [<official text / secondary>](link)

### Upcoming deadlines (next 12 months)
| Date | Obligation | Item |
|------|-----------|------|

### Status changes since last digest
- <item>: <old stage> → <new stage>

_Sources scanned: <list with status> · Items found: <n> · Not covered: <topics/jurisdictions without source>_
```

## Quality checks
- Every item has a link and a publication date; items without a source are excluded.
- Stage and dates match the source exactly; secondary sources are labeled.
- Each High or Medium item has an action, an owner role and a date.
- The digest states its "as of" date and the period covered.
- No impact claim relies on an internal Company fact that is not sourced.

## Guardrails
- Not legal advice; interpretations are framed as "the source says" or "to confirm with Legal".
- Do not guess transposition, entry-into-force or application dates; missing → "date not stated in sources".
- Do not present a proposal as adopted law.
- Draft only: sharing the digest or creating Jira actions happens after the user confirms.

## Example
Input: "Veille du mois sur la sécurité des produits et la loi conso, UE + France" with three newsletters in Gmail.
→ Digest dated, period stated. Items deduplicated (two newsletters on the same guidance → one item, official source
preferred). Each item tagged with its stage exactly as sourced; one proposal labeled "Watch". Deadlines table only
lists dates written in the sources. Footer lists topics with no source found this month.
