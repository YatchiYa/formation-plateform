---
name: store-incident-report
description: "Writes a factual, privacy-safe store incident report: what happened, a timestamped timeline, people affected described by role only, impact on customers, teammates, sales and operations, immediate actions taken, notifications made, evidence retained and follow-up actions with owners, for safety events, customer or teammate accidents, theft, aggression, equipment failure, IT or till outage. Use whenever something went wrong in a store and needs to be reported, escalated or documented, even if the user just describes it in a few messy lines. Triggers - incident report, accident in store, theft report, till outage, safety incident, near miss, rapport d'incident, déclaration d'incident, accident client, accident du travail, vol en magasin, panne caisse, panne informatique, presque accident, chute en magasin, agression magasin."
---

# Store incident report

Produces a clear, neutral record of a store incident that managers, safety, IT or insurance contacts can act on, without
exposing more personal data than needed.

## When to use
- A customer or teammate was injured or nearly injured (fall, product falling from height, cutter, ladder).
- Theft, fraud, aggression or a security event.
- An outage: tills, payment terminals, network, door counters, lighting, heating, fire alarm.
- A product safety concern found in store (a defect, a recalled item still on sale).
- Not for: a blameless technical postmortem of an IT system (use `incident-postmortem`), status updates during an
  ongoing IT incident (use `incident-status-update`), or a customer complaint escalation (use
  `complaint-escalation-brief`).

## Inputs
- What happened, where and when (required): the user's account, notes, or messages.
- Category (optional, default: inferred): safety/accident, near miss, theft/security, aggression, IT/equipment,
  product safety, other.
- Actions already taken and who was informed (optional, default: asked as open questions in the report).
- The store's incident form or procedure (optional, default: searched in Drive/Confluence; if found, follow its
  fields and order instead of the generic template).
- A one-line account (what + when) is enough: draft the full report at once with [to confirm] for store, exact date
  and times, and put every missing detail in "Open questions for the reporter". Never reply with questions only.

## Sources
1. **Drive and Confluence**: the store or company incident procedure, the report form, the escalation list. Use them
   and cite them; never invent a procedure, a deadline or a contact.
2. **Gmail, Google Chat, Slack**: messages about the incident (timeline, who was called, IT ticket numbers).
3. **Jira**: IT or maintenance tickets linked to the outage.
4. **Databricks via Polco / Tableau** (outages only): sales or tickets per hour on the day vs the same weekday, to
   estimate the impact. Discover tables first; never assume column names; show the query and label it *estimate*.
5. **Calendar**: who was on duty is NOT pulled automatically; use only what the user provides.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Separate facts from interpretations.** Facts: what was seen, heard, measured, with time. Interpretations and
   hypotheses go in a separate line marked as such. Never assign blame or guess intent.
2. **Build the timeline**: detection, first response, escalation, resolution, each with time and actor role
   (« 15:42 — teammate (rayon fitness) finds the customer on the floor near the weights bay »).
3. **Describe people by role only**: « customer (adult) », « teammate A (checkout) ». Names, contact details and
   health details are not in the report body; they go only into the official channel the procedure defines.
4. **Impact**: people (injury level as reported, first aid given or not, emergency services called or not), operations
   (zones closed, duration), sales (outage: lost tickets estimated as normal tickets per hour × hours, labeled
   *estimate*), stock or equipment damaged.
5. **Immediate actions**: securing the area, first aid, calls made, product withdrawn, manual payment fallback.
6. **Evidence retained**: list types only (photos of the area, incident register entry, IT ticket, CCTV retained per
   procedure). Do not describe CCTV content beyond what the report needs, and never describe a person's appearance
   except when the procedure for a theft or aggression report requires it, and then only factually.
7. **Root cause (provisional)** using 5 whys for safety and outage events; mark it "to confirm".
8. **Follow-up actions**: corrective (fix this case) and preventive (avoid recurrence), owner role, due date.
9. **Notifications checklist**: who must be informed according to the procedure found, with status; if no procedure
   was found, say so and ask the user to check with their manager or safety contact.

## Output format
```markdown
# Incident report — <category> — <store> — <date, time>
**Status:** <open / closed> · **Severity (as reported):** <low / medium / high> · **Reported by:** <role>

## Summary
<3 sentences: what, impact, current status>

## Timeline
| Time | Event (facts only) | Actor (role) |
|------|--------------------|--------------|

## People involved (roles only)
- <role> — <involvement> — <care given>

## Impact
- People: …
- Operations: …
- Sales: <value or "n/a"> _(estimate, method: …)_
- Equipment / stock: …

## Immediate actions taken
- …

## Evidence retained
- <type> — <where it is kept / reference>

## Provisional cause (to confirm)
- <5 whys chain> · Hypotheses (not facts): …

## Follow-up actions
| # | Action | Type (corrective / preventive) | Owner (role) | Due |
|---|--------|-------------------------------|--------------|-----|

## Notifications
| Who (per procedure) | Done? | When |
|---------------------|-------|------|

## Open questions for the reporter
- …

_Procedure used: <link or "no procedure found, generic structure used">_
```

## Quality checks
- No customer or teammate name, phone, address, health detail beyond the reported injury level, or physical
  description appears in the report body.
- Every timeline line has a time (or "time unknown") and a role.
- Facts and hypotheses are in separate places; no sentence assigns blame.
- Any sales impact is labeled *estimate* with its formula.
- Every follow-up action has an owner role and a date.
- The procedure is cited, or its absence is stated.

## Guardrails
- Medical or legal judgment is out of scope: report what was observed and the care given; never diagnose or state
  liability.
- Workplace accidents and serious events may have legal reporting deadlines: tell the user to check the official
  procedure and their manager now; do not state a deadline that was not found in a source.
- Theft and aggression: no accusation of an identified person; refer to « suspected » events and to the competent
  channel. Do not share CCTV stills or descriptions in chat or email.
- Draft only: the report is not sent or filed anywhere without the user's confirmation, and only to the people the
  procedure names.
