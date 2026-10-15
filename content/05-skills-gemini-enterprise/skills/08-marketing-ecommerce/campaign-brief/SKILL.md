---
name: campaign-brief
description: "Writes a one-page creative and media campaign brief: business and communication objective, audience with a job-to-be-done, one consumer insight, a single-minded proposition with reasons to believe, mandatory elements, channel role per funnel stage, KPIs with baselines, budget split and retro-planning. Use whenever someone launches or relaunches a campaign, briefs an agency or the in-house studio, prepares a seasonal push (ski season, back to school, running season) or a product launch, even if they only ask for 'a quick brief' or 'some campaign ideas'. Triggers - campaign brief, creative brief, media brief, brief the agency, launch campaign, brief de campagne, brief créatif, brief agence, lancer une campagne, plan de campagne, brief média."
---

# Campaign brief

Turns a business need into a single-minded brief that an agency, the studio and the media team can execute without a
second meeting. A good brief is narrow: one audience, one insight, one proposition, one primary KPI.

## When to use
- A campaign, a product launch or a seasonal push (ski season, back to school, spring running) needs a brief.
- An agency or the in-house studio is waiting for a brief, or a brief came back with off-target work.
- Several stakeholders disagree on the objective or the message and need one page to align on.
- Not for: the promotional sequencing across the season (use `promo-calendar-planner`), building the personas
  themselves (use `customer-persona-builder`), the post-campaign results (use `marketing-performance-report`) or
  the social posts (use `social-media-post-pack`).

## Inputs
- Product, range or sport concerned, and the business problem (required).
- Objective: awareness, consideration, conversion, retention or store traffic (required, ask if unclear).
- Target audience (optional, default: derived from personas or research found in Drive).
- Budget, dates, markets and channels already decided (optional, default: left as placeholders, never invented).
- Brand guidelines and past briefs (optional, default: searched in Drive and Confluence).

## Sources
1. **Drive and Confluence**: previous briefs and post-campaign reports for the same sport or season, brand
   guidelines, personas, product briefs and range plans, market studies.
2. **Databricks (SQL or Polco)**: baselines for the KPIs (sales of the range N-1 over the same weeks, share of new
   customers, store vs online split). Show the query or the Polco question used.
3. **Tableau**: existing campaign or category dashboards, to reuse the official KPI definitions.
4. **Gmail, Chat and Slack**: the requester's brief, stakeholder constraints, agency exchanges.
5. **Jira and Airtable**: the marketing request ticket or campaign tracker with dates and owners.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Business problem first.** Write it as a number to move ("grow trail running shoe sales among road runners
   +X % vs N-1 on weeks 10–16"). If no figure is available, mark the target *to be set* and keep the KPI.
2. **One objective, one funnel stage.** Map to See / Think / Do / Care. Refuse a brief that asks one asset to do
   awareness and conversion at the same time; propose two phases instead.
3. **Audience with a job-to-be-done**: "When I <situation>, I want to <motivation>, so I can <outcome>". Example:
   "When I move from road to trail, I want shoes that grip on wet rock, so I can run my first 20 km race without
   fear". Describe behavior and context, not demographics alone.
4. **Insight**: one human truth with tension, built as *observation + because + but*. Cite where it comes from
   (study, reviews, survey). A product feature is not an insight.
5. **Proposition**: one sentence, single-minded. Add 2–3 **reasons to believe**, each traced to a data sheet, a test
   or a review source. No claim without proof; any environmental claim goes to `green-claim-checker`.
6. **Channel role**: for each channel, its job in the funnel (paid social = reach and stop the scroll, search =
   capture intent, CRM = activate members, store = trial and advice). Note the attribution limits up front.
7. **KPIs**: one primary KPI tied to the objective, 2–3 secondary, 1–2 guardrails (margin, return rate,
   unsubscribe). Give the baseline and source for each, or mark *baseline missing*.
8. **Mandatories and retro-planning**: logos, legal mentions, formats, languages; backward plan from the live date
   (brief → concept → validation → production → trafficking).
9. Run the quality checks and list the open questions for the requester.

## Output format
```markdown
# Campaign brief — <Campaign name> (<market>, <dates>)
_Owner: <name> · Status: draft · Sources: <links>_
_Assumptions: <one line>_

## 1. Business problem
<1–2 sentences, with the number to move and its baseline>

## 2. Objective
**Funnel stage:** <See/Think/Do/Care> · **Primary KPI:** <KPI, target, baseline, source>

## 3. Audience
- **Who:** <behavioral description>
- **Job-to-be-done:** When I …, I want to …, so I can …
- **What they think/do today:** …

## 4. Insight
<observation> because <reason>, but <tension>. _(source: …)_

## 5. Proposition
**<one sentence>**
- Reason to believe 1 — <fact> _(source: …)_
- Reason to believe 2 — …

## 6. Tone and mandatories
- Tone: <from brand guidelines link, or "guidelines not found">
- Must include: … · Must avoid: …

## 7. Channels
| Channel | Role in the funnel | Format | Budget share | KPI |
|---------|--------------------|--------|--------------|-----|

## 8. KPIs
| Type | KPI | Baseline (source) | Target |
|------|-----|-------------------|--------|
| Primary | | | |
| Guardrail | | | |

## 9. Budget and timeline
| Milestone | Date | Owner |
|-----------|------|-------|

## Open questions
- …
```

## Quality checks
- The proposition is one sentence and can be repeated by someone who read the brief once.
- The insight contains a tension and a source; it is not a product feature.
- Every reason to believe and every baseline cites a source or is marked *assumption*.
- Exactly one primary KPI, matching the funnel stage of the objective.
- Budget, dates and prices come from the user or a source; otherwise they are placeholders.

## Guardrails
- Never invent product specs, prices, test results or performance claims ("the lightest", "100 % waterproof").
  Superlatives and comparisons need proof that the brief cites (EU Unfair Commercial Practices rules).
- Environmental or durability claims are routed to `green-claim-checker` before they enter the brief.
- Do not invent brand guidelines or tone rules. Use the document found in Drive or Confluence, or say none was found.
- Audience descriptions use behavior and sport practice, not stereotypes about gender, age or origin.
- Draft only: do not send the brief to an agency or create tickets until the user confirms.
