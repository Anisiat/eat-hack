# Pop-up Pick for RGC: Build Plan

Oct 3, 2026 · @Maks

## The tool

Pop-up Pick is a new planning module for RGC's RGC-first pop-ups. It tells RGC which events to pop up at, which client products to bring (2 to 5, scaled by the event's expected attendance), and what to sample, and it gives every client brand an event profile showing where its products win.

**Why RGC needs it.** Every pop-up costs staff time and free product from clients, and pays back in [WatchHumans](https://watchhumans.com/) sign-ups, reviews and publicity. WatchHumans already partners with run clubs and other communities to put products in front of people in person. Today the choice of event and lineup is judgement; this tool makes it a forecast RGC can check afterwards.

**It works both ways.**

- **Events to brands:** pick an event, get the best lineup, the products and quantities to bring, the best time slot, and the reasons.
- **Brands to events:** pick a client brand, get its event profile (event types, moments and audiences where it wins, and where it doesn't) and its best upcoming events.

**The headline number** is net value per pop-up in pounds: review income (RGC charges £599 for 15 reviews) minus what the pop-up costs. Sign-ups and video views are reported alongside for the pitch. RGC pops up only at small events, with expected attendance under 200.

**Built today** on synthetic WatchHumans data, real upcoming London events and public location data. RGC's real data replaces the synthetic tables without changing the model.

## Impact metric

We can't verify whether a reviewer is in a brand's "target" audience, and reviews aren't the only payback: pop-ups also bring publicity. So the headline is **net value per pop-up, in pounds**, built only from things RGC can count with a QR code per pop-up:

```latex
\text{Net value}(e, L) = S \cdot v_S + R \cdot (v_R + v_P) - \text{event cost} - \text{units} \cdot c_U
```

S is expected sign-ups and R is expected reviews (both depend on the event and the lineup L). v_R is the value of a review: **£39.93**, RGC's price of £599 for 15 reviews. v_S, the value of a sign-up, is **£0** today because RGC doesn't pay for acquisition. v_P, publicity, is **£0** today but reported as estimated video views so it can be built into the pitch. c_U is the cost of one sample unit (£0.50).

**Event cost**, once RGC owns the basic kit, is about £150 for a half day (typically £95–290):

| Per-event cost | Typical | Model default |
| --- | --- | --- |
| Pitch fee | £30–150 | the event's listed stall cost, kept within £30–150 |
| Insurance (single-event public liability) | £20–50 | £35 |
| Consumables (bags, flyers, stickers, tape, pens) | £20–40 | £30 |
| Transport and parking | £15–40 | £20 inner London, £35 outer |
| Food and drink for whoever's staffing | £10 | £10 per staff member |

The first pop-up costs more like £350–400 because of one-off kit (about £250), which isn't counted per event. Staff wages aren't counted by default; set `staff_hourly_cost_gbp` to include them. All values live in `data/assumptions/value_assumptions.csv` for RGC to replace with real figures.

A pop-up is **wasted** when its net value is below zero. The forecast gives each event a chance of waste, so the month plan skips events that are more likely than not to lose money.

| Metric | Who it serves | How RGC measures it for real |
| --- | --- | --- |
| Sign-ups per pop-up | RGC: traction | A QR code per pop-up in the WatchHumans sign-up flow |
| Reviews per pop-up | RGC and clients | Reviews tagged with the pop-up's code |
| Publicity | RGC and clients | Views of review videos from the pop-up; social mentions and tags |
| Net value per pop-up | RGC | The four above in pounds, minus stall, staff, travel and product given |
| Wasted pop-ups | RGC | Share of pop-ups with net value below zero |
| Marketing time | RGC | Hours spent choosing events and lineups, by hand against with the tool |

**The tool's impact** is measured in pounds a month:

```latex
\text{Impact} = (\overline{\text{net}}_{\text{tool}} - \overline{\text{net}}_{\text{habit}}) \times \text{pop-ups per month} + (h_{\text{manual}} - h_{\text{tool}}) \times \text{pop-ups per month} \times \text{hourly rate}
```

The habit plan is the baseline: RGC's usual lineup at the biggest events. Today it is measured on 12 held-out synthetic pop-ups with bootstrap confidence intervals. With real data, alternate tool-picked and manually picked pop-ups for a season, time the planning both ways, and compare net value per pop-up.

On synthetic data, the numbers show how much is at stake if the patterns hold; they are not a measured result. Say so on the slide.

## Data

Three sources: synthetic WatchHumans tables and pop-up history, RGC's real brand sheet, and real upcoming UK events from PredictHQ. The synthetic tables mirror what the app already collects: interests, hobbies and goals, likes and dislikes, and rated video reviews.

| File | Rows | Source | Key fields |
| --- | --- | --- | --- |
| `brands.csv` | 71 products from 49 real RGC client brands | RGC's brand sheet | brand, product, category, sub-category, flavour, format, dietary flags, need states and target segments (inferred), label claims, label → target link |
| `brand_features.csv`, `brand_products.csv` | 49 brands, 70 products | Built from `data/raw/brands.csv` by `scripts/build_brand_features.py`, from the keyword archetype scores in `data/archetypes/products_archetypes.csv` (`get_product_archetypes.py`), rescaled so each product's top archetype is 1 | 10 archetype scores, 3 target archetypes, a match score per event type, 8 need states, lineup role, vegan, gluten-free, adults-only, chilling; favourite five and stock are assumptions |
| `users.csv` | 5,000 | Synthetic WatchHumans | age band, borough, primary and secondary archetype and a score on all 10 WatchHumans archetypes, traits, category affinities, dietary needs, sign-up source (pop-up code or organic) |
| `reviews.csv` | 20,000 | Synthetic WatchHumans | user, brand, pop-up code or none, rating 1 to 5, would buy, liked or disliked attribute, in target archetype; pop-up reviews reconcile with `popup_brands.csv` |
| `popups.csv` | 60 past pop-ups, 2 a month from Apr 2024 to Sep 2026 | Synthetic | date, event type (one of seven), borough, footfall, 5-brand lineup, sign-ups, reviews, cost |
| `popup_brands.csv` | 300 | Synthetic | pop-up, brand, units given, reviews, average rating |
| `data/assumptions/value_assumptions.csv` | 20 | Assumptions for RGC to replace | value per sign-up, per review and per 1,000 views; video share; views per video; unit cost; per-event costs (pitch, insurance, consumables, transport, staff food, optional wages); one-off kit; marketing hours and rate; pop-ups per month; attendance cap (200) |
| `data/archetypes/events_archetypes.csv` | 22 upcoming | Real UK events from PredictHQ (`get_raw_event_data.py`), scored by `get_event_archetypes.py` | title, description, category, start and end, latitude and longitude, attendance, 10 archetype scores with evidence |
| `data/archetypes/products_archetypes.csv` | 70 | `get_product_archetypes.py`, the same keyword method applied to `data/raw/brands.csv` | 10 archetype scores with evidence |

**brands.csv titles** Brand,	Product / variant,	Category,	Sub-category,	Flavour profile,	Format,	Dietary flags,	Need states served (inferred),	Target segments (inferred),	Marketing claims / label keywords,	Label → target link (inferred)


**Event types.** Seven categories (the PredictHQ categories), used in `popups.csv` and the real events: community, concerts, conferences, expos, festivals, performing arts, sports. The gatherings in the crowd table map onto them: run clubs, food markets, family days and workshops are community; gigs and club nights are concerts; hackathons are conferences; campus fairs are expos; races and match screenings are sports.

**How the generator works.**

- A hidden "truth" sets each rating and sign-up rate from need-state fit, audience match and brand quality, plus noise. The model never sees these parameters; it learns only from the noisy tables.
- Past lineups follow habit: RGC's five favourite brands appear in 70% of past pop-ups. That gives the tool something real to beat.
- Train on the first 48 past pop-ups and test on the last 12, split by date.
- Brands are RGC's real clients, but every rating, review and pop-up outcome is synthetic. Label it as synthetic in any public video, and never present a synthetic rating as a client's real result.

**Where the events come from.** The London hackathon aggregator, Let's Do This for runs and races, food markets, match screenings and campus fairs. Record facts and links only.

## What each crowd wants

Each event type has a moment and a set of need states. This table seeds the synthetic data and the fit score; real WatchHumans ratings refine it over time. These are starting assumptions; the evidence behind three rows is below the table.

## What each niche gathering might want

Small gatherings offer specific moments to explore: a coffee after a social run, an ingredient to take home after a cooking class, or a snack during a pottery break.

These are **starting hypotheses for synthetic data and the fit score**. WatchHumans feedback can help refine them; actual purchase behaviour is needed to validate demand. A good fit depends on timing, price, what the organiser already provides, and whether outside food is welcome.

| Gathering | The moment | Possible needs or motivations | Food and drink to test | Condiments or take-home products | Potentially weaker fit |
| --- | --- | --- | --- | --- | --- |
| **Weekend social run club** | Finished running; staying to chat | Refreshment, hunger, a social ritual | Water, iced coffee, pastries, small savoury snacks | Nut butter sample packs, breakfast granola | Large meals when people are leaving quickly |
| **Evening distance-running group** | Training ends close to dinner | Thirst, substantial food, convenience | Drinks, wraps, sandwiches, filling snack bars | Easy meal sauces for dinner at home | Tiny tasting portions when people want a meal |
| **Small overnight hackathon** | Coding through dinner or taking a late break | Convenience, hunger, minimal interruption | Wraps, onigiri, resealable snacks, coffee and caffeine-free drinks | Sauce sachets with meals | Food requiring assembly or leaving greasy hands |
| **Beginner cooking class** | Participants taste the dish they have just made | Recreate it at home, build confidence, discover ingredients | Samples of ingredients used in the lesson; a recipe-linked ingredient kit | The exact spice blend, chilli oil, paste or dressing used | Unrelated products with no connection to the recipe |
| **Pasta-making workshop** | Sitting down to eat the finished pasta | Complete the meal, share, recreate the experience | Focaccia, paired drinks, a take-home pasta kit | Pesto, tomato sauce, finishing olive oil | Snacks that compete with an included meal |
| **Dessert or baking class** | Decorating, tasting and packing creations | Customisation, gifting, trying techniques at home | Tea, coffee, small contrasting flavour samples | Fruit curds, compotes, chocolate sauces, decorating kits | More full-size desserts when participants already have plenty |
| **Wine-tasting evening** | Comparing wines between guided pours | Explore pairings, share small bites, remember favourites | Cheese, crackers, olives, bread, water | Chutneys, tapenade, products used in the tasting | Strong flavours that interfere with the planned tasting |
| **Morning yoga class** | Class ends; some participants linger before work | Refreshment, a light breakfast, convenience | Tea, coffee, fruit pots, small breakfast pots | Granola or fruit compote to take home | Full meals when the venue has no seating or time to linger |
| **Yoga festival or day retreat** | Break between sessions or a scheduled lunch | Eat comfortably, refresh, accommodate varied dietary preferences | Clearly labelled bowls, wraps, fruit, hot and cold drinks | Dressings or snack packs tied to food served that day | Large portions immediately before an active session |
| **Evening painting or drawing class** | Social break or end-of-class conversation | A small treat, refreshment, sharing | Drinks with lids, bite-size savouries, individually portioned treats | Packaged local preserves or giftable treats, if relevant to the event | Open dips and messy food beside artwork |
| **Weekend pottery workshop** | Hands washed; a scheduled break | Warm drink, small reward, conversation | Tea, coffee, biscuits, small cakes | Take-home tea, coffee or biscuit gift packs | Food served while participants are handling clay |
| **Fermentation or pickling workshop** | Tasting results and discussing home experiments | Learn, compare flavours, try making something | Guided samples, bread or crackers for tasting | Starter kits, pickling spice blends, jars of the products demonstrated | Generic snacks with no link to the workshop |
| **Match screening** | Two hours of shared viewing | Sharing, savoury, celebration | Crisps, popcorn, sharing snacks, soft drinks, low and no alcohol beer | Dips, hot sauce | Single-serve health products |
| **Gig, club night** | Late, dancing, hot room | Hydrate, energy, late savoury | Electrolytes, water, energy drinks | None | Breakfast items |
| **All-day outdoor festival** | Heat, walking, queues | Hydrate, cool down, portable | Cold drinks, ice lollies, portable snacks | Hot sauce near food stalls | Chilled items with no power |
| **Campus fair, freshers** | Students browsing stalls | Value, novelty, energy | Energy drinks, snacks, quick meals | Condiments for student cooking | Premium-priced items |

### How this informs the fit score

Score the **specific product in the specific moment**, using:

- **Occasion fit:** Is there an observed reason to eat, drink or take something home?
- **Practical fit:** Can people comfortably consume or carry it?
- **Offer fit:** Is the price, portion and format suitable?
- **Unmet need:** Is the organiser already providing an equivalent?
- **Evidence:** Is the match based on an assumption, participant feedback or actual purchases?

A cooking-class participant asking to buy the sauce they just used is stronger evidence than assuming every yoga attendee wants a particular snack.

**Evidence behind three rows.**

- **Runs:** sports-medicine guidance says the goal after exercise is to replace any fluid and electrolyte deficit; sweat rates run roughly 0.5 to 2.0 litres an hour.
- **Hackathons:** dehydration measurably dulls attention, and sugary carbohydrates are linked to more fatigue within an hour, which is why sugar-led products sit in the weak-fit column.
- **Match screenings:** on Euro 2024 England match days, beer purchases rose 13% and crisps and snacks 5%.

Sources are listed at the end of the doc.

## How it works

Six steps run in order: score every brand at every event, predict outcomes, pick the best lineup, choose the month's events, then write the profiles, quantities and timing. Every number traces back to its inputs.

1. **Archetype match for every product at every event.**

   ```latex
   \text{match}_{p,e} = \sum_{a=1}^{10} \text{crowd}_e[a] \times \text{affinity}_p[a] \qquad \text{fit}_{b,e} = \max_{p \in b} \text{match}_{p,e} \times c_{b,e}
   ```

   **Archetype matching.** Events, products and users share the 10 WatchHumans archetypes (wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner, conscious consumer), which WatchHumans builds from each user's purchasing data. Events and products are scored with **one keyword method** (`get_event_archetypes.py` for events, `get_product_archetypes.py` for products): keywords in each text field add weight, plus category and label/segment tables, and score = 1 − e^(−total). Both are rescaled so their top archetype is 1. An event's crowd = its rescaled scores as shares, blended 70/30 with the WatchHumans population. Each product's profile is updated with ratings by reviewer archetype. match = Σ_a crowd[a] × affinity[a]; fit = the best product's match × context (chilling outdoors). There is no need-state moment factor.
2. **Expected outcomes.** A Poisson regression trained on the 48 training pop-ups predicts sign-ups from footfall, event type, dwell time and the lineup's archetype match. A second gives reviews per sign-up from fit. Together with `data/assumptions/value_assumptions.csv` they give each lineup's net value and its chance of losing money.
3. **Lineup optimiser.** For each event, shortlist the 20 eligible brands with the best fit, then score every combination of the shortlist at the event's lineup size, in under a second. Events are capped below 200 people. Lineup size scales with expected attendance: 2 products under 50 people, 3 under 100, 4 under 150, and 5 from 150 to 199 (up to 15,504 combinations). The score is the lineup's archetype match: each archetype expected at the event is credited with its favourite product in the lineup, weighted by its share of the crowd, so products that each win a different part of the crowd beat near-duplicates. Hard constraints: at least one vegan and one gluten-free option, chilled capacity, units in stock, and no alcohol or CBD at community, expo or conference events.
4. **Month plan.** Skip events whose forecast says they will probably lose money, rank the rest by expected net value, and fill RGC's capacity, usually 2 pop-ups a month, with no date clashes. No brand is guaranteed a slot: clients do not pay RGC for pop-up placement, and pop-ups are one RGC service among several. Events run UK-wide; transport is £20 + £0.40 per km from London, so distant events must earn more to be picked.
5. **Brand event profiles.** For each brand: fit across the seven event types, its best moment and audience, what to sample, where to avoid, and its top five upcoming events with expected reviews. A language model writes the profile paragraph from these numbers; it never sets them.
6. **Quantities and timing.** Units to bring per product equal expected stops (attendance × the type's stop rate) times one sample times a 1.2 buffer, capped by stock. The time slot is the event's peak-need moment from the crowd table.

**Stack.** Python, pandas, scikit-learn (PoissonRegressor) and Streamlit. A language model also tags each event description into one of the seven event types.

## Inputs and outputs

The app has three screens, one per question RGC asks. Each reads the same scored files, so the three of you can build in parallel from the first 15 minutes.

| Screen | RGC enters | RGC gets |
| --- | --- | --- |
| Event planner (events to brands) | An event, or a date range; units available; stall size | Ranked events with expected sign-ups, reviews, net value and chance of waste; best lineup with products, units, time slot and three reasons; the habit lineup's net value for comparison |
| Brand profiles (brands to events) | A client brand | Its event profile: fit across the seven event types, best moment, best audience, what to sample, where to avoid; its top five upcoming events with expected reviews |
| Month plan and impact | Month, pop-up capacity | A calendar of pop-ups and lineups; net value against the habit plan, events skipped as likely losses, marketing time saved, and the monthly impact in pounds |

**File contract.** All in `outputs/`, built by `python -m model.run [--month 2026-12 --capacity 2]` from the input CSVs plus `data/processed/event_types.csv` and the real events in `data/archetypes/events_archetypes.csv`. Agree these at T+0:00.

```
scores.csv       event_id, brand_id, product, match, fit, exp_signups, exp_reviews, in_best_lineup, reason_1, reason_2, reason_3
lineups.json     event_id -> name, date, event_type, expected_attendance, lineup_size, brands, products, units{brand: n}, slot, match, exp_signups, exp_reviews, value{net_value, p_waste, ...}, habit_value, reasons[3]
impact.json      review_uplift (+CI), net_value_tool, net_value_habit, net_gain_per_popup (+CI), waste_rate_tool, waste_rate_habit, monthly_impact_gbp, yearly_impact_gbp, per_popup[12]
month_plan.json  month, capacity, popups[{event_id, date, brands, exp_reviews, net_value, p_waste}], net_value, habit_net_value, skipped_events, marketing_time_saved_gbp, month_gain_gbp
```
## Location finder UI (paste after "Inputs and outputs", before "Team split")

The marketing team's job today: find events, work out who will be there, then guess which products to request from the warehouse. The location finder puts all three on one screen. **Find the best location for the audience, see who is there, get the products and quantities to bring.** Everything on the screen is interactive: the map, the list, the filters, the timeline, the lineup and the plan all respond to each other.

It is the front end to the same engine. It reads the scored files and calculates nothing itself.

This replaces the Event planner and Brand profiles screens with one map-first screen. The Month plan and impact screen stays, and takes the same look.

> **Built:** `python app.py` runs the workflow and serves this UI at http://localhost:8000 (code in `app/`). Differences from the spec below: net value (£) and expected reviews replace QRP; no borough layer, borough filter or audience tags (retired / not in PredictHQ data); the stall-cost filter is an event-cost filter; the side-by-side compare view and timeline brushing are not built (first two in the cut order); stub files are not used. Brand profiles (`profiles.json`) are no longer produced, since nothing shows them.
>
> **Update:** QRP has been replaced by net value per pop-up (£) and expected reviews (see Impact metric), events are capped below 200 people, and events now come from `data/archetypes/events_archetypes.csv` (real UK events, no `events.csv`, no audience tags), the crowd is the 10 WatchHumans archetypes rather than 5 segments, `boroughs.csv` and the Census data are retired (no borough layer), and there are no stub files (use the real `outputs/`). Read "QRP" in this section as net value.

### Front end: one interactive web page

Because everything must be interactive and branded, build the front end as a single-page web app: **Mapbox GL JS** for the map, plain JavaScript or React for the panels, served by a small Python server (FastAPI or Flask) that reads the same CSV and JSON files. The model and the file contract do not change.

Streamlit with pydeck is the fallback if the app lead prefers it, but be aware of what it cannot do well: hover cross-highlighting between map and list, fly-to animation, timeline brushing and fully custom styling all need a custom component. Decide at T+0:00.

### Screen layout

| Area | What it shows |
| --- | --- |
| Top bar (charcoal) | RGC logo, mode toggle (Event to products, Product to events), filter pills, search, impact strip |
| Left | Ranked event list, the same events as the map, sorted by expected QRP |
| Centre | Mapbox map, with Map and Timeline tabs over the same data |
| Right | Detail panel for the selected event |
| Bottom | Plan tray: events added to the plan, capacity, total QRP, request list export |

### Everything is interactive

**Map**
- Hover a pin: tooltip with event name, date, score and top audience segment. The matching row in the list highlights.
- Click a pin: map flies to it, the pin grows with an indigo ring, the detail panel opens.
- Zoomed out, nearby pins cluster into a count; click a cluster to zoom in.
- Hover a row in the list: the matching pin pulses.
- Draw or drag a radius ("search this area"): the list and plan figures filter to events inside it.
- Click a borough (when the borough layer is on): the map zooms to it and the filter sets to that borough, with its stats shown.
- Basemap controls: zoom, reset view, toggle the borough layer.

**Filters and list**
- Filter pills update the pins, list and timeline instantly, with pins animating in and out.
- The list sorts by expected QRP, date, distance from the centre, or stall cost, and shows a live count ("14 events").
- Select two events with the compare tick and open a side-by-side compare (audience, lineup, QRP, cost).

**Detail panel**
- Click a segment bar in "who is there" to highlight which brands target that segment.
- Click a brand tile to open its reasons and its profile, and "Show where this brand wins" to jump to Product to events mode with that brand selected.
- Stall-size toggle (Small, Medium, Large) switches the units shown. The engine precomputes all three, so the UI never calculates quantities.
- "Add to plan" animates the event into the plan tray. The stock check updates with the whole plan, not just this event.

**Timeline tab**
- Drag across the timeline to brush a date range; the map and list filter to match.
- Click a bar to select the event everywhere. Clashing dates show a warning, and the plan tray turns amber when over capacity.

**Plan tray**
- Reorder, remove or swap events. Total QRP, uplift against habit and the summed request list update live. Export the request list as CSV.

**Keyboard and motion**
- Arrow keys move through the list, Enter opens the panel, Escape closes it. Visible keyboard focus on every control.
- Transitions follow the site's motion (small upward reveal, about .25 to .8s easing) and switch off under reduced motion.

### Map (Mapbox)

- Mapbox GL basemap centred on the bounding box of `events.csv` (London for now, wherever the events are later). Token in an environment variable, never in the repo.
- Style: Mapbox Light, desaturated and recoloured to `#F4F3EF` land, with labels and roads turned down so the pins are the loudest thing.
- Pin fill shows fit; pin size shows expected attendance; the fit score (0 to 100) sits inside the pin in monospace. Selected pin gets an indigo `#6A6AE2` ring.
- Fit colours: strong `#22A651`, medium `#EAC24A`, weak `#C9C7C0`. In Product to events mode the fill shows the selected brand's fit instead of the best lineup's.
- Optional borough layer: shading by WatchHumans users per 1,000 people from `boroughs.csv` (pale means new sign-ups are worth the most).
- No heatmap. Events are separate points, and a heatmap would blur them into a density that does not exist.

### Filters

- Event type: the seven types (community, concerts, conferences, expos, festivals, performing arts, sports).
- Audience tag: food, tech, fitness, students, families, from `audience_tags` in `events.csv`. "Food events" and "tech events" are tags, not types: a food market is community with a food tag, a hackathon is conferences with a tech tag.
- Date range, indoor or outdoor, borough, maximum stall cost, and a "clear all".

### Detail panel (same on map and timeline)

1. **Event:** name, date, start and end time, venue, borough, expected attendance, link.
2. **Who is there:** audience segment mix (students, young professionals, fitness, families, foodies) as bars, age mix, and the borough's share aged 18 to 34. Labelled "estimated from event tags and Census 2021".
3. **Bring:** the 5 brands as product tiles with units and the best time slot.
4. **Why:** three reasons per brand, from `scores.csv`, one plain sentence each.
5. **Compare:** tool lineup QRP against habit lineup QRP, and cost per qualified review.
6. **Stock check:** units needed against units available per brand, with a clear flag on any shortfall.
7. **Add to plan.**

### Product to events mode

Pick a client brand. The map recolours by that brand's fit, the list re-sorts by its expected reviews, and the panel shows its profile from `profiles.json`: best moment, best audience, what to sample, where to avoid, and its top five upcoming events.

### Request list

Every event added to the plan contributes its units. The plan tray sums them per brand and exports one CSV for the warehouse: brand, product, units, event, date. Quantities follow the engine's rule: expected stops times one sample times a 1.2 buffer.

### Look and feel: Really Good Culture

The visual reference is the `rgc-brand-reference` folder: `index.html` (palette, type, components, artwork, product previews), `tokens.css` (extracted colours, font stacks, starter components), `assets/` (logos, illustrations, icons, product previews, with `asset-manifest.json`). Import `tokens.css` and use the files in `assets/` rather than recreating them. Where this section and `tokens.css` disagree, `tokens.css` wins.

**Overall treatment.** Restrained typography and dense detail next to playful, tactile 3D artwork. A charcoal brand frame (top bar and optional feature panels), a pale neutral workspace for long use, white rounded cards, and subtle purple selection states. The tool is used repeatedly, so the workspace is the light treatment from the product previews, not the dark marketing look.

**Colours** (from the active RGC site styles)

| Role | Value | Used for |
| --- | --- | --- |
| Charcoal canvas | `#1D1D1D` | Top bar, brand frame |
| Dark text | `#141414` | Text on light surfaces |
| Workspace | `#F4F3EF` (warm) or pale grey | Page background |
| Cards | `#FFFFFF` | List, panels, plan tray |
| Dark detail panel | `#161618` | Optional dark detail panel, as in the explorer |
| CTA lime | `#B8F000` | Primary action only |
| CTA green | `#22A651` | Primary action gradient end, strong fit |
| Indigo | `#6A6AE2` | Selection, selected pin ring, focus states |
| CTA gradient | `linear-gradient(90deg,#B8F000,#22A651)` | The one primary action per screen ("Add to plan") |
| Hero text gradient | `linear-gradient(120deg,#C2FF00,#4DC9E2)` | Large headings, welcome state only |

**Event type colours** (reuse RGC's category palette for the seven types, in the timeline bars, list dots and legend; the map pins stay coloured by fit so the two never compete)

| Event type | Colour |
| --- | --- |
| Community | `#40C0C0` |
| Concerts | `#C060B0` |
| Conferences | `#4B4BF0` |
| Expos | `#8FD3EC` |
| Festivals | `#F06040` |
| Performing arts | `#FFB088` |
| Sports | `#4FA8CF` |

When an event is selected, the detail panel's soft radial glow takes that event's type colour, as the explorer does when a category is selected.

**Typography**

| Use | Style |
| --- | --- |
| Headings and body | Helvetica, Helvetica Neue, Arial, sans-serif; headings weight 400 with tight tracking (about -.045em) |
| Labels, nav, buttons, pin scores, metadata | Menlo, SF Mono, ui-monospace, monospace; actions 14px uppercase, eyebrows 12px uppercase with wide tracking |
| Accent | Geist, for a few supporting headings |
| Sizes | 14 to 16px everyday text, 12 to 13px labels; keep tiny marketing tags out of dense flows |

**Shape, spacing and components**
- Controls (inputs, filter pills, selects): 12px radius, white fill, 1px charcoal border at 16%, green focus border with a faint halo. Primary action: 999px pill, 13px 26px padding, dark label on the lime to green gradient, lifts 1px on hover.
- Panels and cards: 22 to 24px radius, 16 to 24px inner padding, 12 to 16px gaps, subtle separators.
- Top bar: 72px high, charcoal, compact logo, ghost pill filters, gradient CTA.
- Event cards in the list look like product cards: title, score in monospace, audience chips, one line on why.
- The five-brand lineup is a row of white tiles with the unit count on each, like a shelf.
- Colour never carries meaning alone: the score number is on every pin and every status has a label.

**Artwork.** Use the 3D pieces sparingly, in welcome and empty states and panel headers, never behind tables or charts. Candidates from `assets/`: `rgc-logo.png` (top bar), `star-3d.webp` and `chain.webp` (empty states), `cereal-*.webp` (small ornaments on audience chips), `bg-*.webp` (soft panel backgrounds behind the detail header only).

**Voice.** Warm and a little playful in empty and welcome states ("Hi Human, where are we popping up?"), plain and exact everywhere else (units, QRP, dates, shortfalls). Labels like "Not enough in the warehouse" beat generic "Error".

### How the UI connects to the engine

The UI reads files only. It never recomputes fit, QRP or quantities, and the language model never ranks.

| File | Made by | Used for |
| --- | --- | --- |
| `events.csv` | Data lead | Pins, filters, event details |
| `boroughs.csv` and a London borough boundary file (GeoJSON) | Data lead | Borough layer, borough stats |
| `brands.csv` | Data lead | Brand names, products, units available for the stock check |
| `scores.csv` | Model lead | Pin colour, score, list order, reasons |
| `lineups.json` | Model lead | Products, units per stall size, time slot, QRP against habit |
| `profiles.json` | Model lead | Product to events mode |
| `impact.json` | Model lead | Impact strip |
| `event_audience.json` (new) | Model lead | "Who is there" panel |
| `requests.csv` (new, written by the UI) | App lead | Warehouse request list |
| `rgc-brand-reference/` (tokens.css, assets/) | Brand scrape | Colours, type, artwork |

Two changes to the file contract:

```
event_audience.json  event_id -> borough, segment_mix{5 segments, sums to 1}, age_mix{18-24, 25-34, 35-44, 45+}, top_segment, borough_share_18_34, source_note
lineups.json         event_id -> brands[5], units{brand: {small, medium, large}}, slot, qrp, habit_qrp, cost
```

The segment mix comes from the event's audience tags and the borough's age profile, using the same audience-overlap term `a` as the fit score. It is an estimate, and the panel says so. The stall-size toggle only switches between the three precomputed unit sets.

### Build notes

- Start from stub files (five fake rows each, T+0:15). The UI must run on stubs before the real files exist.
- Build order: theme and map with pins; list, filters and detail panel with cross-highlighting; plan tray and request export; Product to events mode; timeline with brushing; borough layer; compare view.
- Cut order for the UI: compare view, borough layer, timeline brushing, then Product to events mode. Keep the pins, the detail panel, the plan tray and the stock check.
- Honesty: the impact strip says uplift on synthetic data is not a measured result.

## Team split

Build for 2.5 hours, then spend 1.5 hours on the demo, all inside your 4 hours. If you start at 13:30, T+4:00 is the 17:30 deadline.

&#91;embedded content: team timeline · 3 people, 2 gates, submit at T+3:45\]

Bars run in parallel; diamonds are gates and fixed times.

| Person | Builds | Hands over |
| --- | --- | --- |
| Data lead | Generator, real events (PredictHQ + archetype scores), product archetype scores, profile text | Synthetic tables by T+1:00, events by T+1:30 |
| Model lead | Fit score, Poisson model, lineup optimiser, month plan, uplift test | `scores.csv` by T+1:15; lineups, profiles and impact by T+2:30 |
| App and demo lead | Streamlit: event planner, brand profiles, month plan and impact; then the video | Working app by T+2:30, video by T+3:30 |

**Rules.**

- Stub files go in at T+0:15, so nobody waits on anybody.
- Gate at T+1:15: one event becomes a lineup end to end on synthetic data. If not, drop the month plan and keep the two-way screens.
- Feature freeze at T+2:30; after that, fixes only.
- Cut order if late: the Poisson model (use fit times footfall instead), then the map, then the month plan. Never cut the two-way screens or the uplift number.

## Demo

The demo runs the three screens in order and lands on one number: the monthly impact in pounds against the habit plan. Replace bracketed values with real output before recording.

**2-minute video**

| Time | Screen | Line |
| --- | --- | --- |
| 0:00 | Title over a photo of The Shelf | "RGC runs RGC-first pop-ups: four or five client brands, free product, and every pop-up should grow WatchHumans. Today the event and the lineup are judgement calls." |
| 0:15 | Brand profiles: a client brand, e.g. Dr. Will's | "This client wins at community events and food markets, with foodies. It loses at sports events." (Synthetic ratings: say so on screen.) |
| 0:35 | Event planner: a real upcoming London hackathon | "Pick a real event. The planner brings \[five brands\], \[N\] units each, timed for the mid-afternoon slump. Here are the three reasons." |
| 1:00 | Same event: habit lineup against tool lineup | "RGC's usual lineup would earn \[X\] reviews here and lose money. The planner's earns \[Y\] and \[£Z\] net." |
| 1:15 | Month plan and impact | "It skips \[N\] events that would lose money, and with marketing time saved that's \[£M\] a month, tested on 12 held-out pop-ups." |
| 1:35 | How it works | "Synthetic WatchHumans data, real London events. Plug in real data and a QR code per pop-up measures the result." |
| 1:50 | Close | "Every pop-up becomes an experiment that makes the next one better." |

**5-minute live final**

1. *0:00 Hook.* "This room is a pop-up audience, and The Shelf is today's lineup." Run the planner live on EAT\_HACK itself as a hackathon event.
2. *0:45 Live demo.* Brand profile, then event planner, then month plan.
3. *2:30 How it works.* The six steps on one slide. "The language model writes and tags; it never ranks."
4. *3:30 Impact and honesty.* Uplift with its confidence interval, and why synthetic data still proves the pipeline.
5. *4:15 Next.* Real WatchHumans data, a QR code per pop-up, a season of alternating tool-picked and manual pop-ups, and the run clubs and communities WatchHumans already partners with.

**Judge questions**

| Question | Answer |
| --- | --- |
| It's synthetic data, so what does it prove? | The pipeline and the metric are real. The generator hides its truth from the model, and real data swaps in without code changes. |
| Why not just pick the biggest events? | Footfall isn't fit, and staff time costs the same either way. The habit plan against the tool plan shows the gap in net value and wasted pop-ups. |
| What about brands that don't get picked? | Clients don't pay for pop-up placement, and pop-ups are one RGC service among several. Every brand still gets its event profile, showing where it wins, so RGC can bring it when the right event comes up. |

## Sources

- [WatchHumans](https://watchhumans.com/): free products, honest video reviews, rewards, community partners such as run clubs
- [London hackathons aggregator](https://london-hackathons.vercel.app): upcoming London hackathons from Luma, Meetup, Devpost, MLH and Eventbrite
- [Let's Do This, London running events](https://www.letsdothis.com/gb/running-events/in-london): races and 50+ London parkrun locations
- [ACSM position stand, Exercise and Fluid Replacement (2007)](https://pubmed.ncbi.nlm.nih.gov/17277604/): replace fluid and electrolyte deficits after exercise
- [Baker, sweat testing (GSSI)](https://gssiweb.org/docs/default-source/sse-docs/baker_sse_161.pdf?sfvrsn=2): sweat rates of roughly 0.5 to 2.0 litres an hour
- [Wittbrodt and Millard-Stafford, 2018](https://library.fabresearch.org/viewItem.php?id=11865): dehydration impairs attention and executive function
- [Mantantzis et al., 2019](https://pubmed.ncbi.nlm.nih.gov/30951762/): sugary carbohydrates linked to more fatigue within an hour
- [Kantar, July 2024](https://www.kantar.com/uki/Inspiration/FMCG/2024-wp-falling-inflation-football-and-fake-tan): England match days lifted beer 13% and snacks 5%
