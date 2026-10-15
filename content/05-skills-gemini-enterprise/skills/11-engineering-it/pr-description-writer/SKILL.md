---
name: pr-description-writer
description: "Writes a reviewer-friendly GitHub pull request description from the diff, commits and linked Jira issue: a Conventional Commits title, what changed and why, how it was tested, risks and rollback, deployment notes and a review guide that tells reviewers where to look first. Use whenever the user opens or updates a PR, pastes a diff or branch, or asks for a PR title, summary or commit message, even if they only say 'help me describe this change'. Triggers - write PR description, PR summary, pull request body, PR title, squash commit message, describe my changes, rédige la description de la PR, résumé de ma pull request, message de commit, titre de PR, décris mes changements."
---

# PR description writer

Turns a diff into a pull request description that lets a reviewer understand the change in two minutes and lets the
next engineer understand it in two years.

## When to use
- The user is about to open a PR, or the current description is empty or "fix stuff".
- A squash-merge needs a clean Conventional Commits message.
- A large PR needs a review guide (which files matter, in which order).
- Not for: reviewing the code quality (use `pr-review-assistant`), user-facing release notes (use
  `release-notes-writer`), or a design document before coding (use `tech-spec-writer`).

## Inputs
- PR link, branch name, or pasted diff (required).
- Jira issue key (optional, default: parsed from the branch name, commits or title).
- How the author tested it (optional, default: inferred from test files in the diff, and the gaps are marked as
  questions for the author).

## Sources
1. **GitHub**: the diff, commit messages, the repo's PR template (.github/pull_request_template.md), CI status on the
   PR, and recent merged PRs in the same repo to match title and scope conventions.
2. **Jira**: the linked issue: summary, acceptance criteria, epic, fix version.
3. **Confluence and Drive**: the tech spec or ADR if the ticket or commits link to one.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. If the repo has a PR template, fill **its** sections in its order and add missing ones from the template below only
   if they add value.
2. Build the **title** in Conventional Commits form: type(scope)!: imperative summary, ≤ 72 characters. Types: feat,
   fix, perf, refactor, test, docs, build, ci, chore, revert. Add ! and a BREAKING CHANGE note when an API contract,
   event schema, config key or database column changes incompatibly. Follow the repo's existing scope names.
3. Write **Why** from the ticket and commits: the problem or user need, in 1–3 sentences. If the reason is not in any
   source, ask the author instead of inventing one.
4. Write **What changed** as 3–7 bullets grouped by intent (not file by file). Call out behavior changes separately
   from refactors.
5. Write **How to test**: steps a reviewer can follow, plus the automated tests added or changed (file names from the
   diff). Never state that tests pass unless GitHub CI reports it.
6. Write **Risk and rollback**: blast radius (which users, stores, channels or services), feature flag, migrations
   (reversible or not), config or secret changes needed before deploy, and how to roll back (revert, flag off, down
   migration).
7. Add a **Review guide** for PRs over ~200 changed lines: the 2–4 files to read first and why; files that are
   generated or mechanical.
8. List open questions for the author where the diff alone cannot tell (for example "Was this tested against the
   store POS sandbox?").

## Output format
```markdown
**Title:** <type(scope)!: summary ≤ 72 chars>

## Why
<1–3 sentences> · Closes <JIRA-KEY>

## What changed
- <behavior change>
- <refactor / tooling>

## How to test
1. <step>
- Automated: <test files added/changed> · CI: <status from GitHub or "not run yet">

## Risk and rollback
- **Blast radius:** <…>
- **Migrations / config:** <none | details, reversible yes/no>
- **Feature flag:** <name or "none">
- **Rollback:** <revert | flag off | down migration>

## Review guide
1. <file> — <why start here>
_Mechanical changes: <generated files, renames>_

## Screenshots / API examples
<only if UI or API contract changed>

---
_Questions for the author before publishing: <list or "none">_
```

## Quality checks
- The title is ≤ 72 characters, uses a valid type, imperative mood, and has ! when there is a breaking change.
- Every bullet in "What changed" maps to something visible in the diff.
- "Why" comes from the ticket, commits or the user; otherwise it is a question, not a guess.
- Rollback is concrete; "revert the PR" is flagged as insufficient when the PR contains a non-reversible migration.
- No secret, token or customer personal data from the diff appears in the description.

## Guardrails
- Draft only. Do not edit the PR, push commits or link tickets until the user confirms.
- Do not overstate testing: "tested" means the author or CI did it, not the model.
- Keep internal ticket context out of PRs in public or partner-visible repositories; ask if the repo visibility is
  unclear.

## Example
Branch feat/STOCK-412-reserve-on-add-to-cart → Title: feat(cart)!: reserve stock when an item is added to the cart.
Risk: changes the stock reservation event schema (breaking for the store replenishment consumer), behind a flag,
rollback = flag off; the new column reserved_until is additive and safe to keep.
