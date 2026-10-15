---
name: job-description-writer
description: "Writes an inclusive, skimmable job description and job ad for a store, warehouse, HQ, tech or sourcing role: mission, outcomes for the first year, responsibilities, a short must-have list kept apart from nice-to-haves, gender-neutral wording, a bias-word scan and channel-ready versions. Use whenever someone needs to open a position, rewrite an old job ad, post an offer on a careers site or LinkedIn, or wonders why an ad gets few or one-sided applicants, even if they only paste a list of tasks. Triggers - job description, job ad, job posting, write a JD, rewrite this ad, inclusive job ad, fiche de poste, offre d'emploi, annonce de recrutement, rédiger une offre, description de poste, ouvrir un poste."
---

# Job description writer

Turns a role need into an accurate, inclusive job description and a short ad that attracts the right teammates and
does not filter out good candidates with inflated or biased requirements.

## When to use
- A manager opens a position (new or replacement) and has only a task list or an old ad.
- An ad gets few applicants, or applicants from a narrow profile, and needs a rewrite.
- The same role must be posted on several channels (careers site, LinkedIn, school job board, store window).
- Not for: interview questions and scorecards (use `interview-kit-builder`), messages to candidates (use
  `candidate-communication-writer`), or the offer letter (use `offer-letter-drafter`).

## Inputs
- Role title, level and context: store, logistics/warehouse, office/HQ, tech/digital, production/sourcing (required).
- Main tasks or the old JD, and the reason for the opening (required). Search Drive and Confluence before asking.
- Country, city, contract type, working time, schedule pattern (weekends, shifts) (required for the ad; use
  placeholders if unknown).
- Salary range or band (optional, default: `[SALARY RANGE — to be provided by HR]`; never estimate it).
- Internal job family or competency framework, brand template for ads (optional, searched in Drive/Confluence).

## Sources
1. **Drive and Confluence**: the existing JD for the same job family, the career or competency framework, the
   employer-brand or ad template, and any inclusive-writing guide. Reuse internal wording and cite it.
2. **Gmail and Chat**: the hiring manager's brief or the opening request, if the user points to it.
3. **Jira** (tech roles only): the team's board, to describe the real stack and type of work, not a wish list.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Frame the role in one sentence**: who it serves and the outcome it owns. Store example: « Faire vivre le
   rayon randonnée pour que chaque client reparte équipé pour sa sortie ». Tech example: "Own the reliability of
   the checkout payment flow".
2. **Write 3–5 first-year outcomes** (what success looks like after 12 months), each measurable or observable.
   Outcomes attract better candidates than task lists and give the interview kit its competencies later.
3. **Responsibilities**: 5–8 bullets, verb first, grouped by outcome. Delete anything that is true of every job
   ("be dynamic", "other tasks").
4. **Requirements, split hard**:
   - **Must-have** (max 5): only what is needed on day 1 and can be checked in an interview. Test each one: "Would
     we really reject a candidate who lacks this?" If not, move it.
   - **Nice-to-have** (max 4), labelled as such. Long must-have lists discourage qualified applicants (an effect often reported
     as stronger for women), so they shrink and skew the pool.
   - Prefer skills over diplomas and years. Replace "5 years of experience" with the capability it stands for,
     unless the law or a certification requires it (e.g. forklift licence for a warehouse role, if the local rule
     applies; mark it *to confirm with HR*).
   - Sport practice: may be presented as a plus for sport-advisor roles, never as a must-have tied to a level of
     physical performance, and never with age or physique cues.
5. **Bias and clarity scan** (fix, then list what you changed):
   - Gendered or coded words: "rockstar", "ninja", "aggressive", "dominant", "young and dynamic team",
     « jeune », « digital native ». Replace with neutral behavior words.
   - French: use the gender-inclusive form the source template uses (e.g. « vendeur·se » or « vendeur / vendeuse »
     or a neutral title such as « Conseiller sportif (H/F) »). Do not mix styles in one ad.
   - Physical requirements: state only real job demands with the task ("lift boxes up to X kg, if confirmed")
     and add the accommodation sentence.
   - Jargon and internal acronyms: explain or delete.
   - Readability: sentences ≤ 20 words, the ad readable in under 2 minutes.
6. **Build the versions**: full JD (internal reference), ad (≤ 350 words), and short channel versions as asked.
7. Fill the **checklist** of open facts that HR or the manager must confirm before posting.

## Output format
```markdown
# <Role title> — <Context>, <City/Country>
_Sources: <old JD / framework / template links, or "none found">. Assumptions: <one line>_

## Job description (internal reference)
**Mission:** <one sentence>
**First-year outcomes**
1. …
**Responsibilities**
- <Verb> …
**Must-have** (max 5)
- …
**Nice-to-have**
- …
**Working conditions:** <contract, hours, schedule pattern, location, physical demands — or placeholders>
**Pay:** <range from HR or [SALARY RANGE — to be provided by HR]>

## Job ad (≤ 350 words, ready to post after checks)
<hook about the sport/team purpose> · <what you will do> · <what you bring> · <what we offer — only confirmed
items> · <how to apply + accommodation sentence>

## Short versions
- LinkedIn / social (≤ 600 characters): …
- Store window or school board (≤ 60 words): …

## Inclusion scan
| Original wording | Issue | Replaced by |
|------------------|-------|-------------|

## To confirm before posting
- [ ] Pay range · [ ] contract and hours · [ ] benefits list · [ ] legal mentions for <country> · [ ] approver
```

## Quality checks
- Must-have list has ≤ 5 items, each checkable in an interview; nothing in it is a proxy for age or gender.
- Every benefit, pay figure and policy line comes from a cited source or is a visible placeholder.
- The inclusion scan table is present, even if it says "no issue found".
- The ad states one accommodation sentence and how to apply.
- The ad is ≤ 350 words and has no internal acronym left unexplained.

## Guardrails
- Never mention or hint at age, gender, origin, nationality (only the legal right to work), family status, health,
  religion or appearance. No photo request, no "young team", no birth date in the application form.
- Never invent salary, benefits, perks, bonuses or policies. Use placeholders and the confirmation checklist.
- Legal mentions differ by country (e.g. pay transparency rules under the EU Pay Transparency Directive as transposed
  locally). Flag them for HR; do not assert what the local law requires unless a cited source says so.
- Draft only: do not publish or send the ad. A human approves the final version.
