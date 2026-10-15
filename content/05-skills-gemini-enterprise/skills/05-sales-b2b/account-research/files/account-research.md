---
name: account-research
description: "Builds a one-page research brief on a B2B prospect or customer organisation (sports club, school, company, municipality, association): profile, sport and equipment needs, buying calendar, decision makers by role, relationship history found in Gmail, Drive and Airtable, trigger events and the best entry point, with every fact sourced. Use whenever a seller is about to contact, call, visit or quote an organisation, or asks who an account is and what we already know about it, even if they only paste a name or a website. Triggers - research this account, account profile, who is this prospect, what do we know about, background on the club, fiche compte, recherche prospect, que sait-on de, profil client B2B, préparer la prospection, qui contacter chez."
---

# Account research

Gives a Company Pro seller a sourced, one-page picture of an organisation before the first touch, so the first
message or call is relevant instead of generic.

## When to use
- Before prospecting a new organisation (a football club, a school, a company launching a wellbeing programme, a town hall).
- Before a meeting with an existing customer whose history the user does not know (account handover, new seller).
- When an inbound request arrives and the seller wants to qualify it quickly.
- Not for: the call agenda and questions (use `discovery-call-prep`), a multi-year strategy for a key account
  (use `account-plan`), or writing the outreach messages (use `prospect-outreach-sequence`).

## Inputs
- Organisation name, plus city or website (required).
- Segment (optional, default: inferred): sports club, school or university, company, local authority, association, other.
- What the user wants to sell or explore (optional, default: open discovery).
- Depth (optional, default: one page; "deep" adds the full contact history).

## Sources
1. **Airtable** (CRM or tracker base): the account record, contacts, past opportunities, stage, amounts, last activity,
   notes. Read the base schema first and use its real field names.
2. **Gmail**: threads with the organisation's domain or contact names: past quotes, complaints, open questions,
   tone of the relationship, last exchange date.
3. **Drive**: past proposals, quotes, order forms, tender files and meeting notes mentioning the organisation.
4. **Calendar**: past and upcoming meetings with its people.
5. **Databricks (SQL or Polco)**: if a B2B sales table exists, order history for the account (dates, categories, amounts).
   State the table and filter used.
6. **Slack, Chat, Confluence**: internal mentions (store teams that know the club, segment playbooks for this type of customer).
7. **Public information the user provides or pastes** (website, annual report, league page, public tender notices).
   Do not browse or scrape personal profiles.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Identify the entity** precisely: legal name, city, segment, size signal (number of licensed members and teams for a
   club, pupils for a school, employees and sites for a company, inhabitants and sports facilities for a town). If two
   organisations match, ask which one.
2. **Pull internal history** first (Airtable, Gmail, Drive, Databricks). Build a dated timeline: first contact, quotes,
   orders, issues, last touch. Flag anything unresolved (late delivery, complaint, unanswered quote): it must be
   handled before any new pitch.
3. **Map the needs by segment** with this lens, and keep only what evidence supports:
   - Club: kits per team and age category, training gear, balls and field equipment, season start (often summer),
     sponsor logos, volunteer-run purchasing, budget from membership fees and local subsidies.
   - School: PE and sports association equipment, durability and safety, budget year, purchasing rules (public schools
     may be subject to public procurement).
   - Company: wellbeing or CSR programme, sport challenges, on-site fitness room, branded gear for events, HR or CSR
     budget owner.
   - Local authority: equipment for municipal facilities, summer camps, sport events; buys through public procurement,
     so watch for tender notices rather than pitching informally.
4. **Find trigger events** that create a reason to talk now: promotion to a higher league, new sports facility, new
   school year, company relocation or new wellbeing policy, published tender or budget vote, sponsor change. Each one
   needs a source and a date.
5. **Map the buying roles** (role first, name only if found in a source): user (coach, PE teacher), influencer
   (technical director, CSR lead), economic buyer (club president or treasurer, school head or bursar, HR director,
   elected official and purchasing department), gatekeeper. Mark unknown roles as gaps to fill.
6. **Pick the entry point**: the role with the most pain and least friction, plus the angle (the trigger event) and one
   relevant proof the user can cite (only real references found in Drive or Airtable).
7. Score **fit** High / Medium / Low with a one-line reason (segment match, volume potential, timing, relationship).

## Output format
```markdown
# <Organisation> — account brief
_<Segment> · <City, country> · Fit: <High/Medium/Low> — <reason> · Sources: <links>_

**In one line:** <who they are and why they matter now>

### Profile
| Item | Value | Source |
|------|-------|--------|
| Size | <members / pupils / employees / inhabitants> | <link or "user"> |
| Sports & teams | … | … |
| Buying calendar | <season start, budget year, tender window> | … |

### Our history
- <date> — <event: quote, order, issue, meeting> ([link](…))
- ⚠️ Open issue: <unresolved item, if any>

### Likely needs (evidence-based)
1. <need> — evidence: <source>
2. …

### Trigger events
- <event> — <date> ([link](…))

### Buying roles
| Role | Person (if sourced) | What they care about | Status |
|------|---------------------|----------------------|--------|
| Economic buyer | … | … | Known / Gap |

### Entry point
- **Who:** <role> · **Angle:** <trigger + value> · **Proof to cite:** <real reference or "none found">

### Gaps to fill on the first call
- …

_Sources checked: Airtable ✓ · Gmail ✓ · Drive ✓ · Databricks ✗ (no B2B table found) · …_
```

## Quality checks
- Every fact in Profile, History and Trigger events has a source or is labeled *assumption*.
- Any open issue in the history is surfaced at the top of History with ⚠️.
- Buying roles name people only when a source names them; otherwise the role is marked Gap.
- Needs follow the segment lens and none is generic ("they need sport equipment" fails).
- The brief fits on one page (max ~40 lines of content).

## Guardrails
- GDPR: collect only professional data needed for the sale (name, role, professional contact). No personal social
  media, family, health or political details, even about elected officials beyond their public role.
- Do not scrape or summarise personal LinkedIn profiles; use what the user pastes, and only the professional part.
- Never invent order history, prices, references or volumes. If Databricks has no data, say so.
- For public bodies with an open tender, remind the user that contact must go through the official channel
  (see `tender-response-builder`).
- Read only: do not create or edit Airtable records unless the user confirms a drafted update.
