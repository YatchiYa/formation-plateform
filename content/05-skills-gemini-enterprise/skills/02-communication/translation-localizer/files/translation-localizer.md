---
name: translation-localizer
description: "Translates and localizes text between languages while keeping meaning, tone and format: keeps Company brand and product names as written, applies a team glossary found in Drive or Confluence, adapts units, dates, currencies and formality to the target country, and lists ambiguities and terms to validate. Use whenever the user needs a document, email, product text, training material, slide or message in another language, or asks to check a translation, even if they just paste text and say 'in English please'. Triggers - translate, translation, localize, in English please, check my translation, version in Spanish, adapt for the market, traduis, traduction, traduire en anglais, version allemande, adapter pour le pays, relire ma traduction, localiser ce texte."
---

# Translation localizer

Delivers a translation that reads as if written by a native speaker in the target country, with brand names and
technical terms consistent across teams, and with doubts made visible instead of guessed.

## When to use
- An email, announcement, procedure or training must go to teammates or partners in another country.
- Product or sport content (benefits, technical features, size guides) must exist in several languages.
- A slide deck or Google Doc must be delivered in two languages.
- The user wants an existing translation checked for errors, false friends or tone.
- Not for: rewriting in the same language (use `message-rewriter`), writing a product page from a data sheet (use
  `product-page-copy`), or reviewing a document's content and logic (use `document-reviewer`).

## Inputs
- Source text or file (required).
- Target language and country, e.g. es-ES vs es-MX, pt-PT vs pt-BR, fr-FR vs fr-BE vs fr-CA (required; if only the
  language is given, assume the main country and state it).
- Audience and register: teammates, customers, suppliers, legal (optional, default: same register as the source).
- Glossary or reference translations (optional, default: searched in Drive and Confluence).

## Sources
1. **Drive / Confluence**: glossaries, terminology lists, translation memories, previous translated versions of the
   same document, product data sheets in the target language. Search "glossary", « glossaire », the product name.
2. **Gmail / Chat / Slack**: earlier exchanges with the same recipients, to mirror their terminology and formality.
3. **Jira / GitHub**: UI string files or tickets, when the text is interface copy (respect placeholders and length).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Prepare the term base.** Extract from the source: brand and model names, sport technical terms, internal
   names, acronyms. Mark each as *do not translate* (brands like Quechua, Kipsta, Domyos, Kalenji, Kiprun, Forclaz,
   Rockrider, Van Rysel, Simond, and model names), *glossary* (found in a cited glossary), or *to validate*.
2. **Translate for meaning, not words.** Rewrite idioms and sport slang with the target-country equivalent;
   keep sentence length and paragraph breaks; keep headings, lists, tables, links and placeholders
   ({name}, %s, [date]) intact.
3. **Localize** (list every change):
   - Dates (DD/MM vs MM/DD), decimals (2,5 vs 2.5), thousands separators, currency symbol and position.
   - Units: keep metric for Europe; for US/UK audiences add imperial in brackets only for customer-facing content.
   - Sizes (EU/UK/US shoe and clothing sizes): never convert yourself; flag "check official size chart".
   - Formality: tu/vous, du/Sie, tú/usted according to audience and local practice; state the choice.
   - Legal or policy terms (warranty, returns, labor terms): flag for local validation, do not adapt the substance.
4. **Run the false-friend and risk check**, e.g. FR « actuellement » ≠ EN "actually", FR « éventuellement » ≠ EN
   "eventually", FR « formation » = EN "training", ES "constipado" ≠ EN "constipated", DE "Gift" ≠ EN "gift",
   IT "magazzino" = warehouse, not magazine. Also check numbers and negations line by line against the source.
5. **List ambiguities**: each source passage with two possible readings, with the reading chosen and why.
6. For a translation review: return a table of issues (accuracy, terminology, fluency, locale, style) with severity
   (critical = meaning or safety changed, major = misleading, minor = style) and a corrected text.

## Output format
```markdown
_<source lang> → <target lang-COUNTRY> · register: <…> · glossary: <link or "none found">_

### Translation
<full translated text, same structure as the source>

### Terms kept or validated
| Source term | Target term | Status |
|-------------|-------------|--------|
| <term> | <term> | do not translate / glossary ([link](…)) / to validate |

### Localization changes
- <what changed: date format, units, formality…>

### To check before use
- <ambiguity or legal/safety term> — chosen reading: <…>
```

## Quality checks
- Every number, date, quantity and negation in the source appears correctly in the translation.
- Brand and product model names are unchanged; glossary terms are applied consistently everywhere.
- The structure (headings, lists, tables, placeholders, links) matches the source one to one.
- Every term not found in a glossary and not obvious is listed as "to validate".
- Safety, warranty, legal and health statements are flagged for native or legal validation, never paraphrased freely.

## Guardrails
- Customer-facing, legal, safety and labeling texts need a validation by a native speaker or the local team before
  publication; say so explicitly.
- Never invent a glossary term as if it were official; an unsourced choice is a proposal.
- Do not send or publish the translation; the user decides where it goes.
- Translate personal data only as needed; do not paste confidential documents into external tools.

## Example
Input: « Traduis en anglais (UK) ce message pour les coéquipiers du magasin de Londres : le stage de formation vélo
aura lieu le 04/11, merci de vous inscrire avant vendredi. »
→ "The bike training session takes place on 4 November; please sign up by Friday." Localization: date written out to
avoid DD/MM confusion; « stage de formation » → "training session" (not "stage"); « coéquipiers » → "teammates".
