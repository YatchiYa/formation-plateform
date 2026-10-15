---
name: glossary-builder
description: "Builds a team or domain glossary of acronyms, internal jargon, project code names and business terms from the documents, pages, tickets and channels the user points to: each term with its expansion, a plain-language definition taken from the sources, FR and EN equivalents, an example of use, related terms and a citation, with ambiguous or conflicting meanings flagged. Use whenever someone is lost in acronyms, onboards a newcomer, prepares a translation, or wants a shared vocabulary for a team or project, even if they just ask what an acronym means. Triggers - glossary, what does this acronym mean, list of acronyms, jargon, team vocabulary, define these terms, glossaire, que veut dire cet acronyme, liste des sigles, lexique, vocabulaire de l'équipe, définir ces termes."
---

# Glossary builder

Gives a team one shared, sourced vocabulary, so that newcomers and partners understand the words everyone uses and
the same word means the same thing.

## When to use
- Onboarding a newcomer to a team, project or domain full of acronyms.
- Preparing a translation or a cross-country project where FR/EN terms must be aligned.
- Two teams use the same word for different things.
- A one-off question: "What does <acronym> mean here?"
- Not for: technical column definitions of a table (use `data-dictionary-builder`), formal KPI definitions (use
  `kpi-definition-card`), or translating a document (use `translation-localizer`).

## Inputs
- Scope: team, project, domain, or a set of documents or channels (required).
- Specific terms to define (optional, default: extracted from the sources).
- Target size and languages (optional, default: up to 40 terms, FR and EN).

## Sources
1. **Confluence and Drive**: existing glossaries, onboarding pages, process docs, strategy decks of the scope.
2. **Jira**: project names, components, labels and recurring terms in epics.
3. **Google Chat and Slack**: channel descriptions and pinned messages; recurring acronyms in team spaces.
4. **GitHub**: READMEs and repository descriptions for technical code names.
5. **Gmail**: only threads the user points to.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Start from existing glossaries** in the scope; reuse their definitions and cite them.
2. **Extract candidates**: uppercase tokens of 2–6 letters, capitalized code names, terms in bold or quotes,
   recurring domain words; count frequency across sources.
3. **Keep the useful ones**: frequent in the scope, not common general vocabulary, and not self-explanatory. Rank by
   frequency × likelihood a newcomer is confused.
4. **Find the definition in context**: expansion written in full somewhere ("<acronym> (…)"), a definition sentence,
   or usage that makes the meaning explicit. Cite where. If only inferred from usage, label *inferred, to confirm*.
5. **Disambiguate**: same acronym with different meanings by team or country → separate entries with context;
   different terms for the same thing → one entry with synonyms.
6. **Add FR/EN equivalents** used in the sources (not invented translations), an example sentence from a source,
   and related terms.
7. **Flag** deprecated terms (old project names) and terms whose owner should validate the definition.

## Output format
```markdown
# Glossary — <scope>
_Built <YYYY-MM-DD> from <N> sources · <n> terms · Validated by: <to assign>_

| Term | Expansion | Definition | FR / EN | Example | Related | Source | Status |
|------|-----------|-----------|---------|---------|---------|--------|--------|
| <ACR> | <full form> | <plain language, ≤ 25 words> | <fr> / <en> | «…» | <terms> | [doc](…) | sourced / inferred / ambiguous |

### Ambiguous terms
- **<term>**: <meaning 1> (<team/context>, source) vs <meaning 2> (<context>, source)

### Deprecated or renamed
- <old term> → <new term> (since <date>, source)

### Not defined in any source
- <term> — seen in <where>; ask <owner/team>
```

## Quality checks
- Every definition cites a source or is marked *inferred, to confirm*.
- No FR/EN equivalent is given that does not appear in a source or as standard usage; otherwise left blank.
- Ambiguous acronyms appear as separate meanings with their contexts.
- Definitions are plain language and ≤ 25 words.
- Terms are sorted alphabetically, and the count in the header matches the table.

## Guardrails
- Use only sources the user can access; do not expose restricted project code names to a wider audience; ask before
  publishing the glossary to a shared space.
- Never invent the expansion of an acronym; unknown ones go to "Not defined in any source".
- Exclude people's names, nicknames and personal references from the glossary.
- Draft only: do not create or edit Confluence pages without confirmation.

## Example
Input: "Make a glossary for newcomers in our supply team from our Confluence space and our Chat space"
→ 30–40 terms sorted alphabetically. An acronym written in full on an onboarding page is *sourced*; one whose
meaning is only clear from how it is used in threads is *inferred, to confirm*; an acronym used with two meanings by
two teams appears under Ambiguous terms with both contexts. Acronyms never expanded anywhere go to "Not defined in
any source" with the team to ask.
