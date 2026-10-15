---
name: local-sport-event-planner
description: "Plans a local sport event or community activity run by a store: concept tied to a sport universe and the local community, partners such as clubs, schools and associations, run sheet, logistics and equipment, safety and risk assessment, registration and consent, communication plan, budget lines from user data, KPIs and a debrief template. Use whenever a store team wants to organize a group run, bike ride, try-out day, kids' sport initiation, club day, repair workshop open day or any community activity, even if they only have a rough idea. Triggers - store event, local event, community event, group run, try-out day, club partnership, événement magasin, animation magasin, sortie running, journée découverte, initiation sport, partenariat club, journée portes ouvertes atelier, organiser un événement sportif."
---

# Local sport event planner

Turns an idea for a local sport moment into a safe, well-run event that brings people to the sport and the store
together with the local community.

## When to use
- A store team wants to run a group activity: Sunday morning run, gravel bike ride, kids' initiation, hiking outing,
  try-out of paddle boards, yoga session, ski waxing workshop.
- A partnership with a local club, school or association needs a concrete plan.
- An event is coming and the team needs a run sheet, safety checks and comms.
- Not for: a store-wide seasonal operation (use `seasonal-operation-planner`), an internal team offsite or meeting
  workshop (use `workshop-designer`), or social media post writing in depth (use `social-media-post-pack`).

## Inputs
- Store, idea and date window (required).
- Target audience and expected participants (optional, default: proposed from the concept, to confirm).
- Partners already contacted (optional).
- Budget and resources available (optional, default: no budget assumed; the plan lists the costs to fill in).
- Location: in store, car park, public space or partner venue (optional, default: to confirm; drives permits and safety).

## Sources
1. **Drive and Confluence**: internal event guidelines, safety or insurance rules for events, past event debriefs,
   partner agreements templates. Cite them; never invent a rule.
2. **Gmail, Chat, Slack**: exchanges with partners, local authorities or HQ about the event.
3. **Airtable**: partner lists, registrations or past event trackers if the store uses them.
4. **Databricks via Polco / Tableau**: sales of the sport universe and traffic on past event days vs comparable days,
   to set realistic KPIs. Discover tables first; never assume columns; label results as observations, not proof of causality.
5. **Calendar**: conflicts with other store events, deliveries and peak days.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Concept in one line**: who, what sport, what experience, why now (season, local race, school holidays). Check it
   serves the purpose « Move people through the wonders of sport »: participation and discovery first, not a sales
   pitch.
2. **Audience and format**: level (beginners, families, club members), group size, duration, inclusivity (levels,
   ages, accessibility), equipment provided or brought.
3. **Partners**: role of each partner (coach, venue, safety, communication), what the store provides, what the partner
   provides, the agreement to put in writing.
4. **Run sheet**: setup, welcome and registration, safety briefing, activity blocks, break, closing, teardown, with times
   and owner roles.
5. **Safety and risk assessment**: route or area check, weather plan B and cancellation criteria, qualified supervision
   for the activity, first aid kit and trained person, emergency contacts and access for emergency services, minors
   with parental consent and adult supervision, equipment checked (helmets, sizes, lights). Mark which points need
   validation by the store manager or the safety contact, and whether a permit or authorization from the local authority
   may be needed for public spaces (to check, never assumed).
6. **Registration and data**: collect only what is needed (name, contact, emergency contact, level), state the purpose,
   retention and consent for photos; marketing opt-in separate and optional.
7. **Communication**: in store, partner channels, store social accounts if they exist; message, dates, visuals brief.
8. **Budget**: list cost lines (equipment, refreshments, signage, partner fees) with amounts only from the user.
9. **KPIs and debrief**: participants vs target, satisfaction (a 2-question survey), new partner contacts, follow-up
   activities planned; sales observations are secondary and not claimed as caused by the event.

## Output format
```markdown
# <Event name> — <store> — <date>
**Concept:** <one line> · **Audience:** <who, how many> · **Owner:** <role>

## Format
- Sport and level: … · Duration: … · Location: … · Equipment: …

## Partners
| Partner | Role | Store provides | Partner provides | Agreement status |
|---------|------|----------------|------------------|------------------|

## Run sheet
| Time | Step | Owner (role) | Material |
|------|------|--------------|----------|

## Safety and risks
| Risk | Prevention | Plan B / response | Validated by |
|------|-----------|-------------------|--------------|
- Cancellation criteria: …
- Permits / authorizations to check: …

## Registration and consent
- Data collected: … · Purpose: … · Retention: … · Photo consent: … · Minors: …

## Communication plan
| When | Channel | Message | Owner |
|------|---------|---------|-------|

## Budget (user figures only)
| Line | Amount | Source |
|------|--------|--------|

## KPIs and debrief
- Participants target: … · Satisfaction question: … · Follow-up: …

## Retro-planning
| Date | Task | Owner |
|------|------|-------|
```

## Quality checks
- The safety section covers supervision, first aid, weather plan B, emergency access and minors (if any).
- Every run-sheet step has a time and an owner role.
- Registration collects only data the event needs, and photo and marketing consent are separate.
- Budget amounts all come from the user or a cited document; empty lines stay empty.
- KPIs focus on participation and satisfaction; no sales impact claimed as caused by the event.

## Guardrails
- Physical activity carries real risk: the store manager or safety contact validates the safety plan; this skill does
  not certify compliance, insurance or permits.
- Never invent partner commitments, prices or authorizations; mark them « to confirm with partner ».
- Minors: require parental consent and adult supervision in the plan; no photos of minors without explicit consent.
- Draft only: no invitations, partner emails or posts are sent without the user's confirmation.
