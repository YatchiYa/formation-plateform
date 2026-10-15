---
name: social-media-post-pack
description: "Creates a ready-to-review social media post pack for one message across several networks (Instagram, Facebook, LinkedIn, TikTok, X, YouTube Shorts): hook-first copy variants per network, hashtags, call to action, visual or video brief, WCAG-compliant alt text and captions, and a posting plan. Use whenever someone needs social posts, captions, a launch announcement on social, a community post for a store or a sport event, even if they only ask for 'a quick post' or 'something for Insta'. Triggers - social post, Instagram caption, LinkedIn post, TikTok script, social media pack, hashtags, post réseaux sociaux, publication Instagram, post LinkedIn, légende Insta, script TikTok, pack réseaux sociaux."
---

# Social media post pack

Turns one message into native posts for each network, with copy variants to test, a visual brief the studio can
execute and accessibility built in. Native beats cross-posted: each network gets its own hook, length and format.

## When to use
- A product launch, a campaign, a store event or a sport moment (first snow, marathon weekend) needs social posts.
- A team or a store wants posts for its own page or for LinkedIn (employer brand, B2B).
- An existing post needs variants for testing.
- Not for: the overall campaign strategy (use `campaign-brief`), a newsletter (use `email-newsletter-writer`), an
  internal announcement (use `internal-announcement-writer`) or a reply to a customer comment (use
  `customer-reply-drafter`).

## Inputs
- The message, product or event, and the goal: reach, engagement, traffic, store visits or recruitment (required).
- Networks (optional, default: Instagram, Facebook and LinkedIn).
- Account: national brand, product brand (Quechua, Kipsta…), store or employer page (optional, default: ask if the
  tone guidelines differ).
- Assets available: photos, video, link, date and place (optional, default: visual brief only).

## Sources
1. **Drive and Confluence**: brand and social guidelines, hashtag lists, legal mentions, campaign brief, product data
   sheet, past high-performing posts.
2. **Tableau or Databricks**: past post performance by format if a social dashboard exists (reach, engagement rate,
   saves, clicks). Cite it; do not guess benchmarks.
3. **Slack and Chat**: community or social team channels for current priorities and sensitivities.
4. **Calendar and Airtable**: editorial calendar, event date and place.
If a source is not connected or returns nothing, say so in one line and continue with what you have. Never announce a search without giving its result in the same answer. If the essential data is still missing, ask for it in one grouped question, show the outline you will fill, and use placeholders such as [to confirm] instead of invented examples.

## Workflow
1. **One message, one CTA.** Write the core message in ≤ 15 words before any copy. If the user gives three messages,
   split them into separate posts.
2. **Hook first**: the first line (or first 2 seconds of video) decides the scroll. Write 3 hook types and keep the
   best 2 per network: *question* ("Wet rock on your trail?"), *bold fact* from a source, *scene* ("6:30, first chair
   lift, fresh snow"). Avoid clickbait the content does not deliver.
3. **Adapt per network**:
   - Instagram: hook ≤ 125 characters before "more", 3–8 relevant hashtags, carousel or Reel.
   - TikTok / Shorts: 15–30 s script with hook, proof, payoff; on-screen text; captions mandatory.
   - LinkedIn: professional angle (teammates, expertise, B2B), 3–5 short paragraphs, ≤ 3 hashtags.
   - Facebook: community and local angle, event details, link.
   - X: ≤ 280 characters, one link.
4. **Hashtags**: mix branded (from guidelines only), sport community (#trailrunning) and local (#Grenoble) tags.
   No trending tag unrelated to the post.
5. **Visual brief**: subject, setting, action, framing, text overlay, format ratio (4:5, 9:16, 1:1). Show real sport
   practice with diverse practitioners; no unsafe practice (no helmet on a bike, off-piste without gear).
6. **Accessibility (WCAG 2.2)**: alt text for every image (≤ 125 characters, describe what is seen and why it
   matters, no "image of", no hashtags), captions for every video, emojis at the end of a sentence and ≤ 3,
   CamelCase hashtags (#TrailRunning) for screen readers.
7. **Variants for testing**: two versions of the hook or CTA per network, one variable changed at a time.
8. **Plan**: suggested day and time slot from past performance if found, else marked *assumption*.

## Output format
```markdown
**Post pack — <topic> · goal: <goal> · accounts: <…>**
_Core message: <≤ 15 words> · CTA: <one action> · Assumptions: <one line>_

### Instagram (<format, ratio>)
**Variant A:** <copy>
**Variant B:** <copy, hook changed>
Hashtags: …
Alt text: …

### LinkedIn
…

### TikTok / Shorts script (<duration>)
| Time | Visual | On-screen text | Voice/caption |
|------|--------|----------------|---------------|

### Visual brief
- Subject / setting / action: …
- Framing and ratios: …
- Text overlay: …

### Posting plan
| Network | Date/slot | Variant | Link/UTM | Owner |
|---------|-----------|---------|----------|-------|

### To validate before posting
- <claims, rights, legal mentions>
```

## Quality checks
- Each network version has its own hook and respects its length limits.
- Every image has alt text and every video has captions or a caption note.
- Exactly one CTA per post, and every link has a UTM placeholder.
- No product fact, price or promo condition appears without a source.
- Hashtags: within the per-network count, CamelCase, none invented as "official".

## Guardrails
- No invented product claims, prices, promo mechanics or performance figures. Promotions must show the real
  conditions (dates, scope) from the source.
- Green claims ("eco", "sustainable", "planet-friendly") go to `green-claim-checker`.
- Influencer or partner content must carry a clear ad disclosure (for example #ad, #publicité / «collaboration
  commerciale»).
- People in visuals: only with image rights; no identifiable minors without documented consent.
- Never invent brand guidelines or official hashtags. Draft only: the user publishes.
