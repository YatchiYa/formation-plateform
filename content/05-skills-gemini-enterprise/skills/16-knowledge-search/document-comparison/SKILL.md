---
name: document-comparison
description: "Compares two documents or two versions of the same document (Google Docs, PDFs, Confluence pages, contracts, policies, specs, price lists) and reports what changed section by section: additions, deletions, modified wording with before and after quotes, changed numbers and dates, contradictions between the documents, and the practical impact of each change, ranked by importance. Use whenever someone asks what changed between two versions, whether two documents say the same thing, or needs to review a new version against the old one, even if they just share two links. Triggers - compare these documents, what changed, diff between versions, differences between, redline, compare v1 and v2, comparer ces documents, qu'est-ce qui a changé, différences entre, comparer deux versions, écarts entre les deux docs, nouvelle version."
---

# Document comparison

Shows a teammate exactly what differs between two documents and why it matters, so they review the changes instead
of re-reading everything.

## When to use
- A new version of a policy, process, contract, specification or price list arrives.
- Two teams have documents on the same subject that may contradict each other.
- A supplier or partner sends back an edited document.
- Not for: summarizing a single long document (use `long-document-digest`), legal analysis of a contract (use
  `contract-summary`), editorial critique of a draft (use `document-reviewer`), or checking a document against a
  policy (use `policy-compliance-check`).

## Inputs
- Document A and document B: links, attachments or version names (required). If "the previous version" of a
  Google Doc or Confluence page is meant, use the version history the user can access.
- Focus (optional, default: all substantive changes; formatting ignored): e.g. numbers, obligations, deadlines.
- Which document is the reference (optional, default: the older one, or the one the user calls "official").

## Sources
1. **Drive**: the two Docs, Sheets or PDFs, and Google Docs version history and comments.
2. **Confluence**: page versions and their change comments.
3. **Gmail and Chat or Slack**: the thread where the new version was sent, for the stated intent of the changes.
4. **Jira**: the ticket requesting the change, if referenced.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify** both documents: title, version or date, author, link. Confirm which is the reference.
2. **Align structure**: map sections of A to sections of B by heading and content (sections may be moved or
   renamed). Note added, removed, moved sections.
3. **Compare within aligned sections**, ignoring formatting and pure rewording that keeps the meaning. Classify each
   difference: Added · Removed · Modified (meaning) · Number/date changed · Moved.
4. **Quote** before and after for every Modified and Number/date change (short exact excerpts).
5. **Contradictions**: for two different documents (not versions), list statements that cannot both be true, with
   both quotes.
6. **Rate impact**: High (obligations, money, deadlines, scope, rights, safety), Medium (process or roles),
   Low (clarification). Explain the practical consequence in one line.
7. **Check stated intent**: if the sender described the changes, flag any change not mentioned in their description.

## Output format
```markdown
**<N> substantive changes (<h> high impact). Biggest: <one line>.**
_A: [<title, version/date>](…) · B: [<title, version/date>](…) · Reference: <A/B> · Formatting ignored_

### High-impact changes
| # | Section | Type | Before (A) | After (B) | Impact |
|---|---------|------|-----------|-----------|--------|

### Other changes
| # | Section | Type | Summary | Impact |
|---|---------|------|---------|--------|

### Structure changes
- Added: … · Removed: … · Moved/renamed: …

### Contradictions
- <statement A> vs <statement B> — <why both cannot hold>

### Not mentioned in the sender's description
- <change #>

### Questions to raise
- <question> — to <author/owner>
```

## Quality checks
- Every Modified or Number/date row has short exact quotes from both documents.
- Changes are ranked; all High-impact changes appear in the first table.
- Pure formatting changes are excluded and the header says so.
- Section references let the user find each change (heading or page number).
- If a document could not be fully read (scan, access), the answer says which part was not compared.

## Guardrails
- Compare only documents the user can access; do not fetch other versions from restricted locations.
- For contracts and legal texts, describe changes neutrally and recommend legal review for High-impact items;
  this is not legal advice.
- Never infer a change that is not in the text; if alignment is uncertain, say so.
- Do not edit, accept or reject suggestions in the documents unless the user confirms.

## Example
Input: « Compare la v3 et la v4 de la procédure de retour fournisseur »
→ Output in French. « 7 changements substantiels (2 à fort impact). Le plus important : le délai de déclaration
passe de <x> à <y> jours (§ 4.2). » Each high-impact row quotes the exact sentence from v3 and v4, the impact line
says who must change what, and the change not mentioned in the sender's email is flagged.
