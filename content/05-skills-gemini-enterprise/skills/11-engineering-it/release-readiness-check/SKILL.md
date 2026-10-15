---
name: release-readiness-check
description: "Runs a go/no-go readiness check for a release from Jira and GitHub: scope done versus planned, open blockers and critical bugs, CI and test status as reported, database migrations and backward compatibility, feature flags, rollback plan, monitoring and on-call, change freeze and peak-period risk, and stakeholder communication, ending with a Go / Go with conditions / No-go recommendation and the exact conditions. Use whenever a team prepares a production release, a deployment to stores, a mobile app submission or a release review meeting, even if they only ask 'are we good to ship'. Triggers - release readiness, go no-go, ready to ship, release checklist, deployment checklist, can we release, mise en production, go no go, prêt pour la MEP, checklist de release, revue avant déploiement."
---

# Release readiness check

Gives the release owner an evidence-based go/no-go view in one screen, so the decision is made on facts and the
risks are accepted consciously, not discovered in production.

## When to use
- Before a release review or a go/no-go meeting.
- Before a deployment with higher risk: database migration, payment or checkout change, store POS rollout, mobile
  app store submission, peak period (sales, Black Friday, back to school).
- When the user asks whether a fix version or milestone is ready.
- Not for: reviewing the code of one PR (use `pr-review-assistant`), writing the release notes (use
  `release-notes-writer`), or reporting project status (use `project-status-report`).

## Inputs
- Release identifier: Jira fix version, GitHub milestone, release branch or tag (required).
- Planned date and time, and target environments (optional, default: from the Jira version or asked).
- The team's release checklist or Definition of Done (optional, default: from Confluence, else the checklist below).
- Known freeze periods (optional, default: searched in Confluence/Calendar; never assumed).

## Sources
1. **Jira**: issues in the fix version (status, type, priority, severity), open bugs linked to it, unresolved
   blockers, issues added after the scope freeze, release or change ticket if one exists.
2. **GitHub**: PRs in the milestone or between the last tag and the release branch, their merge and review status,
   CI check results on the release commit as reported by GitHub, migration files, config and infrastructure changes,
   feature flag changes.
3. **Confluence and Drive**: release checklist, change management process, freeze calendar, runbooks, SLO pages,
   previous release postmortems.
4. **Calendar**: the release slot, on-call coverage and team availability on release day and the day after.
5. **Slack and Google Chat**: release channel for known issues, QA sign-off, business sign-off.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Scope**: compare planned vs done. List items not Done, items added late, and PRs merged without a ticket.
2. **Quality gates**: open bugs by severity in the version or the touched components; CI status of the release
   commit (quote GitHub, never infer); QA or UAT sign-off evidence; known flaky or skipped tests if visible.
3. **Change risk**: migrations (reversible? expand/contract? lock risk on large tables?), API or event contract
   changes and their consumers, config and secret changes, new dependencies, infrastructure changes.
4. **Recoverability**: rollback method per change (redeploy previous version, flag off, down migration), and whether
   rollback was rehearsed; anything one-way is a condition.
5. **Operability**: dashboards and alerts for new paths, runbooks updated, on-call staffed for release day + 1,
   release time vs traffic peaks (avoid Friday evening and peak trading hours unless justified).
6. **Communication**: release notes, store or customer service briefing if behavior changes, stakeholders informed.
7. Rate each gate ✅ met / ⚠️ risk accepted with condition / ❌ not met, with evidence. Then the recommendation:
   **Go** (no ❌, ⚠️ only minor), **Go with conditions** (named, owned, checkable before the slot), **No-go** (any ❌
   on blockers, rollback or S1/S2 bugs). The decision belongs to the release owner.
8. Add DORA context if the team tracks it (change failure rate, deployment frequency, lead time, time to restore):
   small, frequent releases lower risk; a big-bang release with many changes is itself a risk to call out.

## Output format
```markdown
**Release <version> · planned <date time TZ> · <environments>**
**Recommendation: <Go | Go with conditions | No-go>** — <one-line reason> · _decision: release owner_

### Gates
| Gate | Status | Evidence |
|------|--------|----------|
| Scope complete | ✅/⚠️/❌ | <n/N done, links> |
| No open S1/S2 bugs | | |
| CI green on release commit | | <as reported by GitHub> |
| QA / business sign-off | | |
| Migrations safe and reversible | | |
| Contract changes coordinated | | |
| Rollback plan defined and tested | | |
| Monitoring, alerts, runbooks | | |
| On-call and timing | | |
| Communication ready | | |

### Conditions to meet before go
1. <condition> — owner: <…> — check by: <time>

### Top risks
- <risk> → mitigation: …

### Not in this release (moved out)
- <KEY — summary>
```

## Quality checks
- Every gate status cites evidence (link, ticket, PR, message); unknown evidence is ⚠️ "not found", never ✅.
- CI and test statuses are quoted from GitHub; the model claims no test execution.
- The recommendation follows the rule in step 7; conditions are specific, owned and checkable.
- Every migration and contract change is listed with its reversibility.
- Peak or freeze conflicts are flagged when found.

## Guardrails
- Recommend, do not decide: the release owner (or change advisory process) makes the call.
- Do not trigger deployments, merge PRs, move tickets or post in channels; draft messages only on request.
- Do not invent a freeze calendar, change process or on-call rota; cite or ask.
- No secrets or customer data in the report, even if found in config diffs.

## Example
Input: "Go/no-go for checkout 4.12 tomorrow 07:00?"
→ Recommendation: Go with conditions. ❌ none; ⚠️ the orders table migration adds a non-null column with a default
(lock risk on a large table, condition: confirm the migration approach with the DBA before 18:00); ⚠️ one S3 bug open
on promo display (risk accepted by the PO per the release thread); ✅ CI green on the release commit as reported by
GitHub; rollback = redeploy 4.11, the migration is additive and safe to keep.
