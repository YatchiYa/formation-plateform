---
name: release-notes-writer
description: "Writes release notes from Jira fix versions and GitHub releases, merged pull requests or tags, in two versions: user-facing notes in plain benefit language (app store text, website or in-app what's new, store teammate tool update) and internal notes for support, stores and engineering (changes, known issues, rollout, how to report problems). Filters out invisible changes, groups by user impact and flags anything not ready to announce. Use whenever a team ships a version or sprint and has to tell users or colleagues what changed, even if they only say 'what's new in this release'. Triggers - release notes, what's new, changelog, app store update text, version notes, notes de version, nouveautés de la version, journal des modifications, texte mise à jour app, communiquer une mise en production, quoi de neuf dans l'appli."
---

# Release notes writer

Turns tickets and pull requests into notes people actually read: users learn what is better for them, support and
store teams learn what changed and what to watch, and nothing unfinished or confidential slips out.

## When to use
- A version of an app, website or internal tool is about to be released or just went live.
- An app store "What's new" text is needed, with its length limits.
- Support or store teams need a briefing on a release before customers ask.
- Not for: a go/no-go readiness check (use `release-readiness-check`), a PR description (use
  `pr-description-writer`), an incident communication (use `incident-status-update`) or a roadmap update (use
  `roadmap-update`).

## Inputs
- Release identifier: Jira fix version, GitHub release or tag range, or a date range (required).
- Product and audiences (optional, default: end users + internal support).
- Channels and limits (optional, default: in-app or web notes; app stores have a character limit, check the
  current limit for each store before final copy).
- Tone and language(s) (optional, default: the product's existing notes; user's language).

## Sources
1. **Jira**: issues in the fix version (type, summary, description, labels, components, customer-facing flag,
   linked bugs), known open bugs on the version.
2. **GitHub**: release notes draft, merged PRs between tags, PR titles and labels; feature-flag changes.
3. **Confluence and Drive**: previous release notes (to match format and tone), PRD for headline features,
   rollout plan (percentage, countries, stores).
4. **Slack and Chat**: release channel announcements, last-minute scope changes, known issues.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Collect changes**: one line per issue or PR with ID, type (feature, improvement, fix, technical), component and link.
2. **Filter**: drop invisible changes (refactoring, dependencies, CI) from the user version, but keep security fixes
   as a generic line ("Security improvements") and keep technical items relevant to internal teams.
3. **Check release status**: exclude items behind a disabled feature flag, partial rollouts not yet visible to all,
   or tagged confidential; list them in "Not announced" for the user to confirm.
4. **Group by user impact**: New, Improved, Fixed. Merge related tickets into one benefit line.
5. **Write user notes**: benefit first, in the user's words, one sentence each, no ticket jargon or internal names.
   Example: "Find your size faster: the size guide now opens directly from the product photo." Fixes say what now
   works ("Your favourites now sync between app and website").
6. **Write internal notes**: per change, what changed, who is affected, rollout scope and date, known issues and
   workarounds, how to report a problem, and links.
7. **Fit channel limits**: app store version within the store's current limit, in-app version within 5 bullets.
8. **Hand over drafts**; publishing is done by the user or the release owner after confirmation.

## Output format
```markdown
# Release <version> — <product> (<date>)
_Sources: <fix version link> · <GitHub release / tag range> · Rollout: <scope>_

## User-facing notes
**New**
- <benefit sentence>
**Improved**
- …
**Fixed**
- …

## App store text (<n>/<limit> chars)
<text>

## Internal notes (support, stores, engineering)
| Change | Who is affected | Rollout | Known issues / workaround | Links |
|--------|-----------------|---------|---------------------------|-------|

**How to report a problem:** <channel from sources or *to confirm*>

## Not announced (please confirm)
- <item> — reason: <flag off / partial rollout / confidential>
```

## Quality checks
- Every user-facing line traces to at least one ticket or PR in the release.
- No user-facing line contains ticket IDs, internal tool names, code words or blame ("bug caused by…").
- Items behind a disabled flag or a partial rollout appear only in "Not announced" or with their scope stated.
- The app store text is within the limit and the count is shown.
- Known open bugs from Jira appear in the internal notes.

## Guardrails
- Never announce features that are not live for that audience, and never promise future features or dates.
- Security fixes are described generically; no vulnerability details in public notes.
- No personal data (customer names, emails, order numbers) from tickets in any version.
- Do not publish, post or update Jira/GitHub; give drafts and act only after the user confirms.
