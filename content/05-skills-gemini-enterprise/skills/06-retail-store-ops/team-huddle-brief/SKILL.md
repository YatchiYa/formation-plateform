---
name: team-huddle-brief
description: "Writes a ready-to-say 5-minute floor team huddle: yesterday's numbers in plain words, today's focus and target, one safety point, one customer story, one piece of recognition and the day's practical info, with a short version for the team chat. Use whenever a store manager, department manager or duty manager prepares the morning or shift briefing for teammates, even if they only ask 'what do I tell the team today'. Triggers - team huddle, morning huddle, shift briefing, pre-opening talk, what to tell the team, brief équipe, brief du matin, point d'équipe, réunion d'ouverture, quart d'heure sécurité, message à l'équipe, top départ, brief avant ouverture."
---

# Team huddle brief

Turns the day's numbers and context into a short, energizing talk that a manager can say in five minutes standing on
the shop floor, and that teammates remember.

## When to use
- Every morning before opening, or at a shift change (afternoon or evening team).
- Before a peak day: first Saturday of the ski season, a back-to-school Wednesday, a sales period opening.
- After a tough day, to reset focus without blame.
- Not for: the manager's own detailed numbers (use `store-daily-brief`), individual feedback to one teammate (use
  `feedback-sbi-writer`), a store-wide written announcement (use `internal-announcement-writer`), or a speech for an
  opening or award (use `talking-points-writer`).

## Inputs
- Store (required) and team or shift (optional, default: whole store, morning).
- Yesterday's key numbers (optional, default: pulled from sources; if unavailable, the huddle skips numbers).
- Today's focus chosen by the manager (optional, default: proposed from data and agenda).
- A customer story or recognition item (optional, default: proposed from messages or reviews; the manager confirms).
- Language and tone (optional, default: the user's language, warm and direct).

## Sources
1. **Databricks via Polco or Tableau**: yesterday's revenue, visitors, conversion, average basket vs N-1 and target,
   and the best performing sport universe. Discover the right table or view first; never assume column names.
2. **Google Calendar**: today's events, visits, deliveries, trainings, workshop bookings.
3. **Gmail, Google Chat, Slack**: HQ or regional instructions, price or promo changes, product recalls, safety notes,
   thank-you messages from customers, colleagues' shout-outs.
4. **Drive and Confluence**: the safety topics calendar or rules the store already uses, and any huddle template.
5. **Customer reviews or feedback exports**: a positive or instructive comment about the store (no customer name).
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **Numbers in plain words** (≤ 30 seconds): one result and one driver, rounded, positive framing, no wall of
   figures. « Hier 12 400 €, +5 % vs l'an dernier, grâce au panier moyen : bravo pour les ventes complémentaires. »
   If the day was bad, name one controllable cause, never a person.
2. **Today's focus** (1 minute): one behaviour, not three, linked to a number. Examples: greet every customer within
   the first metres in the ski boot zone; propose the workshop check with every bike sold; refill the running sock
   wall before 11:00. Add today's target if one exists.
3. **Safety point** (30 seconds): one concrete point from the store's rules or the day's risks: ladder and high-shelf
   handling, cutters, pallet truck in the aisles during opening, a wet entrance on a rainy day, fire exits kept clear
   during a delivery. Use the store's own rule wording if found in Drive; otherwise keep it general and practical.
4. **Customer story** (1 minute): a real, anonymized moment from feedback or the manager: what the customer needed,
   what the teammate did, what it changed. Ties to the purpose « Move people through the wonders of sport ».
5. **Recognition** (30 seconds): specific behaviour and its effect, only with the manager's consent and only if the
   person is comfortable with public praise; otherwise praise a team.
6. **Practical info** (30 seconds): deliveries, visits, events, breaks, who is on checkout and workshop.
7. **Close with a question** to the team (« Qu'est-ce qui pourrait nous bloquer aujourd'hui ? ») to get one idea.
8. Write the short chat version (≤ 6 lines) for teammates who were not present.

## Output format
```markdown
# Huddle — <store> — <weekday DD Month> — <shift>
_~5 min · say it, don't read it_

**1. Yesterday (30 s)**
<two sentences>

**2. Today's focus (1 min)**
<one behaviour + why + target if any>

**3. Safety (30 s)**
<one concrete point>

**4. Customer story (1 min)**
<anonymized story, 3–4 sentences>

**5. Recognition (30 s)**
<specific behaviour → effect> _(manager to confirm)_

**6. Practical (30 s)**
- <delivery / visit / event / roles>

**7. Question to the team**
<one open question>

---
**Chat version**
<≤ 6 lines with one emoji max>
```

## Quality checks
- Spoken length is about 5 minutes: roughly 600–700 words maximum in the main part.
- One focus only, phrased as an observable behaviour.
- At most three numbers in the whole huddle, each traceable to a query, dashboard view or the manager's notes.
- The customer story contains no customer name, photo, or detail that could identify them.
- The safety point is concrete and doable today.

## Guardrails
- Never single out a teammate for poor performance in a group huddle; that belongs in a private conversation.
- No invented numbers, customer stories or safety rules: if nothing real is available, leave the slot as a prompt for
  the manager.
- Recognition is drafted for the manager to validate; do not post anything to team channels without confirmation.
- Keep personal data out: no health, absence reasons or HR matters in the huddle.
