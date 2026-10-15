---
name: code-explainer
description: "Explains a code file, function, pull request or area of a GitHub repository for a newcomer, a non-developer or a reviewer: what it does in plain words, where it sits in the system, the main flow step by step with file and line references, key concepts and jargon, data in and out, side effects and dependencies, gotchas, and where to start reading or changing it. Adapts depth to the audience. Use whenever someone asks what a piece of code does, how a service works, where something is implemented, or needs to onboard on a codebase, even if they just paste a link and ask 'what is this'. Triggers - explain this code, what does this do, how does this service work, walk me through the repo, where is X implemented, explique ce code, que fait cette fonction, comment marche ce service, présente-moi le repo, où est codé."
---

# Code explainer

Helps a reader understand unfamiliar code fast and correctly: what it does, how data flows through it, and what to
be careful about, at the level the reader needs.

## When to use
- A new teammate onboards on a repository or service.
- A product owner, analyst or support engineer needs to know how a behavior is implemented (for example how the
  delivery promise date is computed).
- A reviewer needs context on a module before reviewing a change to it.
- Not for: judging code quality or finding bugs in a PR (use `pr-review-assistant`), writing a design for new work
  (use `tech-spec-writer`), or a full onboarding plan for a person (use `onboarding-plan-builder`).

## Inputs
- What to explain: repo, folder, file, function, PR link, or a question like "where is the stock check done?" (required).
- Audience (optional, default: developer new to this codebase). Options: non-developer, developer, reviewer.
- Depth (optional, default: overview + main flow; deep dive on request).

## Sources
1. **GitHub**: the target files; README, docs folder, architecture notes and ADRs; entry points (main, routes,
   controllers, handlers, consumers), API definitions (OpenAPI, proto, GraphQL schema), config, tests (they show
   intended behavior), and recent PRs touching the area (why it changed).
2. **Confluence and Drive**: design docs, architecture overviews and glossaries for the domain.
3. **Jira**: tickets linked from commits or PRs, to explain business intent.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. Locate: for a question ("where is X"), search the repo for domain terms, routes, function names and test names;
   list candidate locations and pick the one confirmed by code, not by file name alone.
2. Give the **one-paragraph purpose**: what this code is for, in business terms first (who uses it, which customer
   or store action triggers it), then technical terms.
3. Place it in the **system**: who calls it, what it calls (databases, queues, external APIs, other services), and
   what triggers it (HTTP request, event, schedule, user action).
4. Walk the **main flow** in 5–10 numbered steps, each with file:line references. Explain the "why" when comments,
   commits or tickets give it; otherwise describe "what" only.
5. Explain **data in and out**: inputs, outputs, main data structures, persisted state, events emitted.
6. Flag **gotchas**: implicit assumptions, surprising side effects, global state, retries, caching, time zones,
   currency handling, feature flags that change behavior, dead code, and areas with no tests.
7. Add a **glossary** of domain and technical terms used (for example SKU, click-and-collect, idempotency key).
8. For non-developers, replace code detail with an analogy and a simple flow; keep file links for whoever follows up.
9. End with **where to start**: files to read first, tests to read, and the safest place to make a typical change.

## Output format
```markdown
**<Repo / path>** — <one-line purpose> · _audience: <…>_

### What it does
<plain-language paragraph>

### Where it fits
<caller> → **<this component>** → <dependencies> (triggered by <…>)

### Main flow
1. <step> — [file:line](link)

### Data in / out
- In: … · Out: … · Stored: … · Events: …

### Watch out for
- …

### Glossary
| Term | Meaning here |
|------|--------------|

### Where to start
- Read first: …
- Tests that show the behavior: …
- Open questions (not answerable from the code): …
```

## Quality checks
- Every claim about behavior points to a file and line that the model actually read.
- Business intent is stated only when a doc, ticket, commit or comment supports it; otherwise it is marked as an
  inference.
- The explanation matches the audience (no unexplained jargon for non-developers).
- The model never claims it ran, executed or debugged the code; runtime behavior is described as "according to the
  code".
- Gotchas include untested areas when tests are missing.

## Guardrails
- Do not reproduce secrets, keys, credentials or customer data found in code, config or fixtures; mention their
  presence as a risk instead and recommend rotation.
- Respect repository access: explain only repos the user can read through the connector.
- Do not judge the authors; explain code neutrally (route quality concerns to a review).
- If the code and the docs disagree, say so and trust the code for current behavior.

## Example
Input: "Where is the click-and-collect availability computed? I'm a product owner."
→ Purpose in business terms first ("decides whether the 'collect in store in 2 h' badge shows for a product"), the
flow from the product page request to the store stock lookup and the safety-stock rule, each step with a file link,
a gotcha such as "the store stock cache refreshes every few minutes according to the config, so the badge can lag
behind a sale", and an open question for the team when the rule's business origin is not documented.
