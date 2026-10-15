---
name: insight-storyteller
description: "Turns analysis results (query outputs, dashboard figures, spreadsheets, notebook findings) into a decision-oriented data story: one headline that states the so-what, three supporting insights each with its number and source, the recommended decision, chart suggestions with the right chart type and title, caveats and confidence, in formats for a slide, an email or a Chat or Slack message. Use whenever someone has numbers and needs to present them, convince leadership, write the commentary of a report or turn a dashboard into a message, even if they only say 'help me present these figures'. Triggers - tell the story of this data, data storytelling, so what, present these results, insights for management, raconter les chiffres, mettre en forme les résultats, message clé, synthèse des résultats, commentaire des chiffres, présenter l'analyse."
---

# Insight storyteller

Turns numbers a teammate already has into a short story that leads to a decision, with every claim tied to its
figure and source.

## When to use
- After an analysis, before a steering committee, business review or management email.
- When a dashboard needs a weekly written commentary.
- When results are correct but nobody knows what to do with them.
- Not for: producing the numbers (use `data-question-answerer` or `metric-anomaly-investigator`), building a full
  slide deck outline (use `presentation-storyline`), a general document summary (use `executive-summary-writer`), or
  the monthly finance commentary (use `monthly-finance-commentary`).

## Inputs
- The analysis results: tables, figures, query outputs or a dashboard link (required).
- Audience and the decision they own (required; default if unstated: management of the user's perimeter).
- Format (optional, default: email/Chat message + one-slide version).
- Desired action, if the user has one (optional).

## Sources
1. **The user's material**: pasted tables, attached Sheets or Docs in **Drive**, notebook outputs.
2. **Tableau**: the views the figures come from, for links and to verify values.
3. **Databricks SQL MCP or Polco**: only to verify a figure or add a missing comparison base (read-only).
4. **Confluence and Drive**: KPI definitions, targets and previous commentaries, to keep consistency.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Find the so-what**: for each finding ask "so what for <audience>?" until it reaches a decision, risk or
   opportunity. Keep the 3 findings with the biggest impact on that decision.
2. **Headline** (≤ 20 words, a full sentence with a verb and a number): e.g. "Running drove 60 % of the growth;
   extending its stock cover is the main lever for Q4." Not a topic label.
3. **Pyramid**: headline → 3 supporting insights → evidence. Each insight = claim + number with comparison base
   + source. Use absolute and relative values; percentage points for rates.
4. **Check the logic**: comparisons like-for-like and aligned N-1; mix effects called out (total growth driven by
   mix, not performance); correlation not presented as cause; small bases flagged.
5. **Recommendation**: one decision or action, owner role, timing, and what would change the recommendation.
6. **Charts**: one chart per insight. Trend → line; ranking → sorted horizontal bar; contribution to change →
   waterfall; part-to-whole ≤ 5 parts → stacked bar. Title = the insight (action title), axis from zero for bars,
   highlight one series, annotate the key point. No pies with many slices, no dual axes, no 3D.
7. **Adapt the format**: email (BLUF first line), Chat/Slack (≤ 6 lines), slide (action title + chart + 3 bullets).

## Output format
```markdown
**<Headline: one sentence, verb + number + so-what>**

**Recommendation:** <action> — owner: <role> — by: <date/period>

**Why**
1. <Insight 1: claim + number vs base> (source: <view/query/doc>)
2. <Insight 2 …>
3. <Insight 3 …>

**Caveats:** <data freshness, definition, small base, mix effect> · **Confidence:** <H/M/L>

---
### Chart suggestions
| Insight | Chart type | Action title | Data needed |
|---------|-----------|--------------|-------------|

### Slide version
Title: <action title>
- <bullet 1> · <bullet 2> · <bullet 3>
Speaker note: <2 sentences>

### Chat / Slack version
<≤ 6 lines>
```

## Quality checks
- The headline is a sentence with a number and an implication, not a topic.
- Every number in the story appears in the user's material or a cited source, with its comparison base.
- Exactly one recommendation, with an owner role and a timing.
- Each chart suggestion has an action title and a chart type matching the rule above.
- Caveats include data freshness and any mix or small-base effect found.

## Guardrails
- Never add numbers that are not in the material or a cited source; if a comparison base is missing, say so.
- Do not overstate: no "caused", "proves" or "because" without a test supporting it; use "is associated with".
- Keep confidential figures (unpublished group results, margins) inside the intended audience; remind the user when
  the format is a broad Chat or Slack channel.
- No teammate-level rankings or names in performance stories unless the user's role requires it.

## Example
Input: a table of sales growth by sport for the quarter, audience = regional director
→ Headline: "<Sport A> delivered <x> % of the region's growth; securing its stock for <season> is the main lever."
Insight 2 notes that the total average basket rose partly through mix (more <Sport A> sales, which carry a higher
basket), not only through like-for-like gains. Chart suggestion: waterfall of contribution to growth by sport.
