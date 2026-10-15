---
name: user-story-writer
description: "Turns a PRD, an epic, a workshop output or a rough idea into Jira-ready user stories: vertical slices with a clear persona and value, INVEST check per story, Gherkin acceptance criteria (Given, When, Then) including edge and error cases, definition-of-ready gaps, dependencies and a suggested order. Drafts only, never creates issues without confirmation. Use whenever someone needs to write, split, rewrite or check user stories or acceptance criteria, even if they only paste a feature title and say 'make tickets out of this'. Triggers - user stories, acceptance criteria, split this epic, Gherkin, write Jira tickets, story slicing, rédiger des user stories, critères d'acceptation, découper une epic, écrire les tickets Jira, story mapping, scénarios Gherkin."
---

# User story writer

Writes stories a team can estimate and build in one sprint, with acceptance criteria precise enough to test. Stories
are drafted in chat; they reach Jira only after the user approves them.

## When to use
- A PRD or an epic must become sprint-sized stories.
- Existing stories are too big, vague or technical and need splitting or rewriting.
- Acceptance criteria are missing before refinement or sprint planning.
- Not for: writing the PRD itself (use `prd-writer`), a bug report (use `bug-report-writer`), grooming a whole
  backlog for duplicates and stale items (use `backlog-grooming`) or planning the sprint (use
  `sprint-planning-assistant`).

## Inputs
- The source: PRD, epic key, notes or idea (required).
- Users or personas concerned (optional, default: taken from the PRD or epic).
- Jira project key, issue type and fields convention (optional, default: read from existing issues in the epic).
- Team's definition of ready and definition of done (optional, default: search Confluence).

## Sources
1. **Jira**: the epic and its existing child issues (avoid duplicates), recent stories of the team to mirror their
   format, labels, components and story-point scale.
2. **Confluence and Drive**: the PRD, designs, definition of ready / done, glossary of business terms.
3. **GitHub**: if relevant, existing endpoints or components the stories depend on.
4. **Slack and Chat**: refinement decisions and clarifications on the feature.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Map the flow** first (story mapping): list the user's steps left to right (backbone), then the stories under
   each step. Mark the thinnest end-to-end slice as release 1 (walking skeleton).
2. **Slice vertically**: each story delivers user-visible value through all layers. Use these splitting patterns
   when a story is too big: workflow steps, business rule variations, happy path first then errors, data types or
   sports, platforms (app / web), simple then complex UI, CRUD operations, spike for an unknown. Never split by
   layer (front / back / database) unless the team's convention says so.
3. **Write each story**: *As a <specific user>, I want <capability>, so that <value>.* The user is a real role (a
   trail runner using the app, a store teammate at the repair desk), not "the user" or "the system".
4. **Write acceptance criteria in Gherkin**, 3–6 per story:
   `Given <context> When <action> Then <observable outcome>`. Cover the happy path, at least one error or edge case
   (no network, empty list, invalid input, out-of-stock size), and accessibility or localization when it is UI.
   Criteria describe behaviour, not implementation.
5. **Run INVEST** on each story and note fails: Independent (can be built in any order or dependency stated),
   Negotiable (no frozen design inside), Valuable (value visible to a user or the business), Estimable (no
   unknown blocking an estimate, else add a spike), Small (fits in a sprint, rule of thumb ≤ half the sprint for
   one dev pair), Testable (criteria are pass/fail).
6. **Check readiness** against the team's definition of ready: designs linked, dependencies known, data and
   analytics needs stated, open questions resolved.
7. **Order** the stories: walking skeleton first, then risk-reducing stories, then value increments.
8. **Offer creation**: show the final list and ask whether to create the issues in Jira (project, epic link,
   labels). Create nothing before an explicit yes.

## Output format
````markdown
# Stories — <epic / feature> (<n> stories, release 1 = <ids>)
_Source: <PRD / epic link> · Jira project: <key> · Assumptions: <one line>_

## Story map
| Step 1: <…> | Step 2: <…> | Step 3: <…> |
|-------------|-------------|-------------|
| S1 (R1) | S3 (R1) | S5 (R1) |
| S2 | S4 | |

## S1 — <short title>
**As a** <user>, **I want** <capability>, **so that** <value>.
**Acceptance criteria**
```gherkin
Scenario: <happy path>
  Given …
  When …
  Then …
Scenario: <error / edge case>
  Given …
  When …
  Then …
```
**INVEST:** I ✓ N ✓ V ✓ E ✓ S ✓ T ✓ · **Ready gaps:** <none / list> · **Depends on:** <none / S#> · **Notes:** …

## Open questions
- <question> — <owner>

## Next step
Create these <n> issues in Jira <project> under <epic>? (yes / edit first)
````

## Quality checks
- Every story names a specific user and a value; none starts "As a user" or "As the system".
- Every story has at least one non-happy-path scenario.
- Every Then is observable (on screen, in a notification, in data) and contains no implementation detail.
- No story is a horizontal layer slice unless the team's convention requires it.
- INVEST fails are shown, with a fix proposal, not hidden.
- Nothing has been created in Jira; the last section asks for confirmation.

## Guardrails
- Draft, don't act: create or update Jira issues only after the user confirms the final list and target project.
- Do not invent business rules, prices, stock rules or legal texts; put them in open questions.
- Keep personal data out of examples (use fictitious, clearly fake values such as *runner@example.com*).
- Do not assign story points; estimation belongs to the team.

## Example
Input: « Epic : réservation d'une réparation vélo en ligne »
→ Backbone: choisir le service → choisir magasin et créneau → confirmer → suivre la réparation. Release 1: S1
« En tant que cycliste, je veux voir les créneaux disponibles de l'atelier de mon magasin… ». Edge case: « Étant donné
qu'aucun créneau n'est libre sur 14 jours, quand je choisis ce magasin, alors je vois les magasins proches avec des
créneaux ». Spike: règles de capacité atelier inconnues → question ouverte.
