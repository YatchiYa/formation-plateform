---
name: team-newsletter
description: "Compiles a periodic team newsletter from what actually happened: wins and results, what shipped or went live, upcoming dates and events, decisions taken, recognition of teammates, and one useful tip, pulled from Drive, Jira, GitHub, Calendar, Chat and Slack, each item with its source, in an email-ready and a Chat-ready version. Use whenever someone prepares a weekly or monthly team update, a digest for stakeholders, a store or department newsletter, or asks 'what did the team do this month', even if they don't say newsletter. Triggers - team newsletter, weekly digest, monthly update, team update email, what did we ship, news of the team, newsletter d'équipe, lettre d'info, actu de l'équipe, point mensuel, récap du mois, digest hebdo, nouvelles de l'équipe."
---

# Team newsletter

Gives a team and its stakeholders a short, lively and sourced digest of the period: what we achieved, what is
coming, and who to thank.

## When to use
- Weekly or monthly team or department update, sent by email or posted in a space.
- A store, warehouse or HQ team wants to share its news with the wider organization.
- A manager wants to keep stakeholders informed without a meeting.
- Not for: a project RAG status (use `project-status-report`), a single announcement (use
  `internal-announcement-writer`), the user's own weekly review (use `weekly-review`), or a topic history over time
  (use `topic-digest`).

## Inputs
- Team or scope, and the period (required; default period: last 7 days if weekly, last calendar month if monthly).
- Audience: the team itself, stakeholders, leadership (optional, default: the team).
- Fixed sections or a previous edition to mirror (optional, default: searched in Drive or Gmail).
- Items the user wants to include (optional).

## Sources
1. **Jira**: issues and epics moved to Done in the period, releases, new epics started; group by epic.
2. **GitHub**: merged PRs and releases in the team's repositories (summarize by feature, not by PR).
3. **Drive / Confluence**: documents and pages published or significantly updated, decision records, previous
   newsletter editions (for format and continuity).
4. **Google Chat / Slack**: team space highlights: thanks, kudos, celebrations, customer feedback shared.
5. **Calendar**: upcoming events in the next period (go-lives, trainings, workshops, sport events, holidays).
6. **Databricks / Tableau**: the 1–3 KPIs the team follows, if the user names them or a previous edition shows them.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Collect** items from each source for the period, with link, owner and date.
2. **Filter by reader value**: keep what changes something for the reader (a new capability, a result, a decision,
   a date to remember). Drop routine tasks, sub-tasks and internal refactors unless they enable something.
3. **Sort into sections**: Headline (the one thing to remember) · Wins & results · Shipped / done · Decisions ·
   Coming up · Shout-outs · Tip or "did you know" · Numbers (optional).
4. **Write each item as impact, not activity**: "Store teams can now book repair slots online (link)", not
   "Closed JIRA-1234". ≤ 2 lines each, one link.
5. **Shout-outs**: name only people credited in a source (kudos message, PR, doc), say what they did and its effect.
   Spread recognition; avoid always naming the same people. Prefer team credit when the source is a team effort.
6. **Upcoming**: dates from Calendar or Jira only, with what readers should do (register, prepare, expect).
7. **Produce two versions**: email (≤ 400 words, skimmable) and Chat/Slack post (≤ 120 words with link to the email
   or doc). Suggest a subject line with the headline.

## Output format
```markdown
**Subject:** <Team> news — <period> · <headline in ≤ 8 words>

### 🏁 Headline
<2 lines>

### 🏆 Wins & results
- <impact> ([source](…))

### 🚀 Shipped
- <feature/change and who benefits> ([link](…))

### 🧭 Decisions
- <decision> — <so what> ([source](…))

### 📅 Coming up
| Date | What | What to do |
|------|------|------------|

### 🙌 Shout-outs
- <Name or team> — <what they did → effect> ([source](…))

### 💡 Tip of the <week/month>
<one practical tip>

---
**Chat / Slack version**
<≤ 120 words>
_Sources checked: Jira ✓ · GitHub ✓ · Drive ✓ · Chat ✓ · Slack ✗ · Calendar ✓_
```

## Quality checks
- Every item has a source link and falls inside the period.
- Items describe an impact for the reader, not a ticket number or a task name.
- The email version is ≤ 400 words and the chat version ≤ 120 words.
- Every person named in shout-outs is credited in a source; no one is singled out negatively.
- Upcoming dates come from Calendar or Jira, not guessed.

## Guardrails
- No individual performance comparisons, rankings or criticism; the newsletter celebrates, it does not evaluate.
- No personal life events (birth, illness, wedding) unless the user confirms the person agreed.
- Leave out confidential items (unreleased products, non-public figures, HR matters) when the audience is wider than
  the team; flag them instead.
- Draft only: sending or posting requires the user's confirmation.

## Example
Input: « Newsletter mensuelle de l'équipe data pour nos parties prenantes, octobre. »
→ Subject « Data team — octobre · le tableau de bord stock est en ligne ». Shipped items grouped by Jira epic and
described by user benefit; decisions from the Confluence decision log; « À venir » from Calendar (training session,
freeze before peak season); shout-outs only for teammates thanked in the Slack channel, with links.
