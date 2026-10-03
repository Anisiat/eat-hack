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

The first pop-up costs more like £350–400 because of one-off kit (about £250), which isn't counted per event. Staff wages aren't counted by default; set `staff_hourly_cost_gbp` to include them. All values live in `data/value_assumptions.csv` for RGC to replace with real figures.

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

Three sources: synthetic WatchHumans tables, real upcoming London events, and public Census 2021 location data. The synthetic tables mirror what the app already collects: interests, hobbies and goals, likes and dislikes, and rated video reviews.

| File | Rows | Source | Key fields |
| --- | --- | --- | --- |
| `brands.csv` | 71 products from 49 real RGC client brands | RGC's brand sheet | brand, product, category, sub-category, flavour, format, dietary flags, need states and target segments (inferred), label claims, label → target link |
| `brand_features.csv`, `brand_products.csv` | 49 brands, 70 products | Built from `brands.csv` by `scripts/build_brand_features.py`, using the phrase mappings in `data/mappings/` (archetypes.csv, need_states.csv) | 10 archetype affinities, 3 target archetypes, 8 need states, lineup role, vegan, gluten-free, adults-only, chilling; favourite five and stock are assumptions |
| `users.csv` | 5,000 | Synthetic WatchHumans | age band, borough, primary and secondary archetype and a score on all 10 WatchHumans archetypes, traits, category affinities, dietary needs, sign-up source (pop-up code or organic) |
| `reviews.csv` | 20,000 | Synthetic WatchHumans | user, brand, pop-up code or none, rating 1 to 5, would buy, liked or disliked attribute, in target archetype; pop-up reviews reconcile with `popup_brands.csv` |
| `popups.csv` | 60 past pop-ups, 2 a month from Apr 2024 to Sep 2026 | Synthetic | date, event type (one of seven), borough, footfall, 5-brand lineup, sign-ups, reviews, cost |
| `popup_brands.csv` | 300 | Synthetic | pop-up, brand, units given, reviews, average rating |
| `data/value_assumptions.csv` | 20 | Assumptions for RGC to replace | value per sign-up, per review and per 1,000 views; video share; views per video; unit cost; per-event costs (pitch, insurance, consumables, transport, staff food, optional wages); one-off kit; marketing hours and rate; pop-ups per month; attendance cap (200) |
| `events.csv` | 30 to 40 upcoming | Real London listings, collected by hand | type, start and end, venue, latitude and longitude, expected attendance, indoor or outdoor, audience tags, stall cost, link |
| `boroughs.csv` | 33 | Census 2021 (ONS TS007, via Nomis); WatchHumans users synthetic | population, share aged 18 to 34, inner or outer, WatchHumans users per 1,000 people |

**brands.csv titles** Brand,	Product / variant,	Category,	Sub-category,	Flavour profile,	Format,	Dietary flags,	Need states served (inferred),	Target segments (inferred),	Marketing claims / label keywords,	Label → target link (inferred)


**Event types.** Seven categories, used in `popups.csv` and `events.csv`: community, concerts, conferences, expos, festivals, performing arts, sports. The gatherings in the crowd table map onto them: run clubs, food markets, family days and workshops are community; gigs and club nights are concerts; hackathons are conferences; campus fairs are expos; races and match screenings are sports.

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
   \text{match}_{p,e} = \sum_{a=1}^{10} \text{crowd}_e[a] \times \text{affinity}_p[a] \qquad \text{fit}_{b,e} = \max_{p \in b} \text{match}_{p,e} \times \text{moment}_{p,e} \times c_{b,e}
   ```

   **Archetype matching.** Events, products and users share the 10 WatchHumans archetypes (wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner, conscious consumer), which WatchHumans builds from each user's purchasing data. The event's crowd mix starts from the crowd table and is updated with who signed up at past pop-ups. Each product's archetype affinity starts from the brand sheet's target phrases and is updated with ratings by reviewer archetype. match = Σ_a crowd[a] × affinity[a]. Fit = the best product's match × moment (need-state cosine with the event type) × context (chilling outdoors, hydration in summer).
2. **Expected outcomes.** A Poisson regression trained on the 48 training pop-ups predicts sign-ups from footfall, event type, dwell time and the lineup's archetype match. A second gives reviews per sign-up from fit. Together with `data/value_assumptions.csv` they give each lineup's net value and its chance of losing money.
3. **Lineup optimiser.** For each event, shortlist the 20 eligible brands with the best fit, then score every combination of the shortlist at the event's lineup size, in under a second. Events are capped below 200 people. Lineup size scales with expected attendance: 2 products under 50 people, 3 under 100, 4 under 150, and 5 from 150 to 199 (up to 15,504 combinations). The score is the lineup's archetype match: each archetype expected at the event is credited with its favourite product in the lineup, weighted by its share of the crowd, so products that each win a different part of the crowd beat near-duplicates. Hard constraints: at least one vegan and one gluten-free option, chilled capacity, units in stock, and no alcohol or CBD at community, expo or conference events.
4. **Month plan.** Skip events whose forecast says they will probably lose money, rank the rest by expected net value, and fill RGC's capacity, usually 2 pop-ups a month, with no date clashes. No brand is guaranteed a slot: clients do not pay RGC for pop-up placement, and pop-ups are one RGC service among several. Boroughs where WatchHumans has few users get a bonus, because new sign-ups are worth more there.
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

**File contract.** All in `outputs/`, built by `python -m model.run [--month 2026-11 --capacity 2]` from the input CSVs plus `event_types.csv` (the crowd table) and `events.csv`. Agree these at T+0:00. Write stub files with five fake rows at T+0:15 so the app starts immediately.

```
scores.csv       event_id, brand_id, product, match, fit, exp_signups, exp_reviews, in_best_lineup, reason_1, reason_2, reason_3
lineups.json     event_id -> name, date, event_type, expected_attendance, lineup_size, brands, products, units{brand: n}, slot, match, exp_signups, exp_reviews, value{net_value, p_waste, ...}, habit_value, reasons[3]
profiles.json    brand_id -> fit_by_type{7}, best_type, best_moment, best_audience, sample, avoid, top_events[5], text
impact.json      review_uplift (+CI), net_value_tool, net_value_habit, net_gain_per_popup (+CI), waste_rate_tool, waste_rate_habit, monthly_impact_gbp, yearly_impact_gbp, per_popup[12]
month_plan.json  month, capacity, popups[{event_id, date, brands, exp_reviews, net_value, p_waste}], net_value, habit_net_value, skipped_events, marketing_time_saved_gbp, month_gain_gbp
```
## Location finder UI (replaces the "Location finder UI" section; paste after "Inputs and outputs", before "Team split")

The marketing team's job today: find events, work out who will be there, then guess which products to request from the warehouse. The location finder puts all three on one screen. **Find the best location for the audience, see which WatchHumans archetypes are attending, get the products and quantities to bring.** Everything on the screen is interactive: the map, the list, the filters, the timeline, the lineup, the plan and the impact view all respond to each other.

It is the front end to the same engine. It reads the output files and calculates nothing itself.

This replaces the Event planner and Brand profiles screens with one map-first screen. The Month plan and impact screen is folded in as the Timeline tab (month plan) and the Impact drawer, in the same look.

### Opening sequence: the PopUpPick bubble

The product is called **PopUpPick** (one word) in the UI. When the page opens, nobody sees the tool straight away. They see the name first, then the site appears.

1. **Dark screen.** The whole screen is the Really Good Culture dark background, the charcoal canvas `#1D1D1D` from `tokens.css`. Nothing else is visible.
2. **The bubble.** The name **PopUpPick** appears centred inside a soap-bubble: a translucent circle (about 60% of the screen width on mobile, up to about 420px on desktop) with a thin rim in the RGC gradient (`#C2FF00` to `#4DC9E2`), a soft highlight in the top left and a faint inner glow. The name is white, Helvetica weight 400, tight tracking (about -.045em), sized to sit inside the circle.
3. **It floats.** The bubble grows in with a slight overshoot (about 0.6s), then drifts and wobbles gently (about 1.4s). A small monospace hint, "Click to pop", fades in underneath.
4. **It pops.** After about 2 seconds, or the moment someone clicks, taps or presses Enter or Space, the bubble swells slightly and bursts: 10 to 14 small droplets in lime, cyan and white fly outward and fade in about 0.5s.
5. **The site is revealed.** As the bubble bursts, the dark overlay fades away and the real site is underneath, already loaded, on the Map tab. The top bar slides down with the PopUpPick wordmark, the map fades in, and the pins drop in one after another. From here the Timeline tab is one press away, and the Map tab brings the map back. The whole sequence takes about 3 seconds.

Rules for the sequence:

- The site loads underneath the bubble, so the map, tiles and data are ready when it pops. If the data has not loaded after 5 seconds, the bubble stays and shows a short message ("Still loading the events") rather than popping onto an empty map.
- Anyone can skip: a click, a key press, or a visible "Skip" button pops it immediately. Adding `?nosplash` to the address skips it for development.
- Clicking the PopUpPick wordmark in the top bar replays it, which is useful for the demo video.
- Pure CSS and a small amount of JavaScript, animating only transform and opacity. No animation library.
- With reduced motion switched on: no floating, no droplets; the name shows on the dark screen for about 0.8s, then cross-fades into the site.
- Accessibility: the overlay has the accessible name "PopUpPick", keyboard focus moves into the site once the overlay is gone, and the overlay is removed from the page afterwards.
- No sound.

This sequence is also the opening shot for the pitch video.

### Front end: one interactive web page

Build the front end as a single-page web app: **Leaflet** for the map (free and open source, no account or token), plain JavaScript or React for the panels, served by a small Python server (FastAPI or Flask) that reads the CSV and JSON files in `outputs/`. The model and the file contract do not change, apart from the additions listed under "How the UI connects to the engine".

Leaflet is chosen because it is reliable and well known, needs nothing to be set up, and has what the UI needs built in or as a standard plugin: custom pins, clustering, animated fly-to, drawn circles, GeoJSON shapes and keyboard support.

Streamlit with a map component is the fallback if the app lead prefers it, but it cannot do the opening sequence, hover cross-highlighting between map and list, or fully custom styling without a custom component. Decide at T+0:00.

### Every engine feature and where it shows in the UI

| Engine feature | Where it shows in the UI | Source |
| --- | --- | --- |
| Archetype match (step 1) | Fit score on every pin and list row; archetype chips naming who is attending; archetype bars in the panel | `scores.csv` fit; `event_audience.json` crowd |
| Expected outcomes (step 2) | Expected sign-ups, reviews and QRP on the panel; expected reviews on each product tile | `scores.csv` exp_signups, exp_reviews, exp_qrp |
| Lineup optimiser, 2 to 5 products by attendance (step 3) | Product tiles, with a line such as "4 products for about 300 people" | `lineups.json` lineup_size, brands |
| Each archetype credited with its favourite product | Winner badge on tiles; clicking an archetype bar highlights the product that wins it | `lineups.json` archetype_winner |
| Hard constraints: vegan, gluten-free, chilling, units in stock, no alcohol or CBD at community, expo and conference events | "Lineup checks" row of ticks under the tiles; a red flag if a check fails | `lineups.json` checks |
| Month plan: QRP per pound, capacity (usually 2 a month), no date clashes, borough bonus (step 4) | Timeline tab: month and capacity selectors, "Use recommended plan" button, clash warnings, a "New sign-ups borough" tag on bonus boroughs | `month_plan.json`; `boroughs.csv` |
| Brands featured; no guaranteed slots | Plan tray stat "Brands featured: N of 49", with a note that clients do not pay for placement | `month_plan.json` brands_featured |
| Brand event profiles (step 5) | Not shown on this screen. Product to events mode is removed | `profiles.json` |
| Quantities and timing (step 6) | Units on each tile, best time slot, units capped by stock | `lineups.json` units, slot |
| Stock | Stock check per product, and across the whole plan in the tray; stock is labelled an assumption | `brand_products.csv` |
| Habit plan against tool plan | "Versus the usual five" comparison on the panel and the tray | `lineups.json` habit_qrp |
| Uplift and its confidence interval | Impact drawer: uplift with its interval as a range bar, QRP tool against habit, 12 held-out pop-ups as paired bars | `impact.json` |
| Cost per qualified review | On the panel, in the tray and in the Impact drawer | `lineups.json` cost, cost_per_qr; `impact.json` |
| Synthetic data | A permanent "synthetic data, not a measured result" label by the uplift number | all |
| Real measurement: a QR code per pop-up | Every event in the plan gets a pop-up code shown in the tray and written to the request list, ready to put in the WatchHumans sign-up flow | UI (code from event id and date) |
| Event facts and type tagging | Type badge, venue, times, attendance and a link to the source listing on the panel | `events.csv` |

### Screen layout

This is the page the bubble opens onto.

| Area | What it shows |
| --- | --- |
| Top bar (charcoal) | RGC logo and the PopUpPick wordmark, Impact button, search, uplift strip |
| Filter row | Event type buttons first, then pills for audience tag, archetype, date range, indoor or outdoor, borough, stall cost |
| Tabs | Two tabs only: **Map** and **Timeline**. One is shown at a time. Map is the default |
| Left | Ranked event list, the same events as the map, sorted by expected QRP. Always visible on both tabs |
| Centre | The active tab. Map tab shows the interactive map. Timeline tab shows the timeline (month plan). Both read the same data |
| Right | Detail panel for the selected event |
| Bottom | Plan tray: events added, capacity, total QRP against habit, brands featured, pop-up codes, request list export |

### Tabs

- **Map tab:** press it and the centre shows the map, nothing else.
- **Timeline tab:** press it and the centre shows the timeline, nothing else.
- Filters, the ranked list, the selected event, the detail panel and the plan tray carry across both tabs. Switching tabs never resets them.
- There is no third tab and no mode toggle.

### Archetype labels on every event

Each event shows who is attending, using the 10 WatchHumans archetypes (wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner, conscious consumer). The mix is the engine's crowd estimate for the event (`event_audience.json`).

- **List row:** the top archetype as a chip with its share, for example "Wellness seeker 34%", plus a smaller chip for the second.
- **Pin tooltip:** the top three archetypes with their shares.
- **Pin label:** when zoomed in past a set level, a short label under the pin ("Wellness 34%").
- **Detail panel:** all 10 archetypes as bars, sorted by share, with the top one called out in one sentence ("Mostly wellness seekers and experience explorers").
- **Filter:** an Archetype filter ("show events where smart savers are the biggest group"). Filtering by archetype updates pins, list and timeline.
- Clicking an archetype bar highlights the product in the lineup that wins that archetype (from `archetype_winner`).
- Chips are neutral: white fill, 1px border, monospace 12px, with the top chip tinted indigo. Archetypes never get their own colours, so they do not compete with the fit or event type colours.
- The panel always says "estimated crowd mix, updated with who signed up at past pop-ups".

### Everything is interactive

**Map tab**

- Hover a pin: tooltip with name, date, score and top archetypes. The matching list row highlights.
- Click a pin: map flies to it, the pin grows with an indigo ring, the panel opens.
- Zoomed out, nearby pins cluster into a count; click a cluster to zoom in.
- Hover a list row: the matching pin pulses.
- Draw or drag a radius: the list and plan figures filter to events inside it.
- Click a borough (borough layer on): zoom to it and filter to it, with its stats.
- Drag to pan, scroll or pinch to zoom. Controls: zoom buttons, reset view, toggle the borough layer.

**Filters and list**

- Pills update pins, list and timeline instantly, with pins animating in and out and a live count.
- Sort by expected QRP, date, distance from centre or stall cost.
- Tick two events and open a side-by-side compare (archetypes, lineup, QRP, cost).

**Detail panel**

- Stall-size toggle (Small, Medium, Large) switches the units shown. The engine precomputes the three sets, so the UI never calculates quantities.
- Click a product tile for its reasons (`scores.csv` reason_1 to 3) and expected reviews.
- "Add to plan" animates the event into the tray. The stock check updates for the whole plan.

**Timeline tab (month plan)**

- Fills the centre when the Timeline tab is pressed. The map is hidden until the Map tab is pressed again.
- Events on a date axis, grouped by week, coloured by event type.
- Clicking an event opens the same detail panel.
- Month and capacity selectors; "Use recommended plan" loads `month_plan.json`. Manual picks and the recommended plan can be compared side by side.
- Drag across the timeline to brush a date range; the list filters to match, and so does the map when you go back to it.
- Clashing dates show a warning. The tray turns amber when over capacity.

**Plan tray**

- Reorder, remove or swap events. Total QRP, uplift against habit, brands featured and the summed request list update live. Export the request list as CSV, including each pop-up's code.

**Impact drawer**

- Opens from the top bar. Uplift with its confidence interval, QRP and cost per qualified review for tool against habit, and the 12 held-out pop-ups as paired bars. Clicking a bar selects that pop-up. The synthetic-data label is always visible.

**Keyboard and motion**

- Arrow keys move through the list, Enter opens the panel, Escape closes it. Visible keyboard focus on every control.
- Transitions follow the site's motion (small upward reveal, about .25 to .8s easing) and switch off under reduced motion.

### Map (Leaflet)

The map is in the UK. An interactive, realistic street map of London (or wherever in the UK the events are), with no account or key needed.

- **Library:** Leaflet, plus the Leaflet.markercluster plugin for clustering.
- **Tiles:** OpenStreetMap standard tiles (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`). The attribution "© OpenStreetMap contributors" must stay visible on the map. OpenStreetMap's tile servers have a usage policy that is fine for a demo but not for heavy production use, so check the policy before launch and swap in a tile provider then; only the tile URL changes.
- **Realistic and interactive:** drag to pan, scroll or pinch to zoom, double-click to zoom in, and zoom down to street level so the team can see the real venue. Initial view fits the bounding box of `events.csv`.
- **Looks like RGC, not a default map:** apply a CSS filter to the tile layer only (for example reduced saturation and a slight warm tint, tuned until the land reads close to `#F4F3EF`) so the pins are the loudest thing. The pins themselves stay crisp.
- **Pins:** custom Leaflet `divIcon` pins, built in HTML and CSS. Pin fill shows fit; pin size shows expected attendance; the fit score (0 to 100) sits inside the pin in monospace; the selected pin gets an indigo `#6A6AE2` ring.
- **Fit colours:** strong `#22A651`, medium `#EAC24A`, weak `#C9C7C0`.
- **Fly-to and clustering:** `flyTo` animates to a selected event; nearby pins cluster into a count that zooms in when clicked.
- **Radius search:** a draggable Leaflet circle that filters the list and plan figures.
- **Borough layer (optional):** a GeoJSON layer shaded by WatchHumans users per 1,000 people from `boroughs.csv` (pale means new sign-ups are worth the most, which is the month plan's borough bonus).
- **If the internet drops:** tiles are the only part that need the network. The app keeps working on a plain `#F4F3EF` background with all pins, lists and panels. Test on the venue's wifi before the demo, and record the video early.
- No heatmap. Events are separate points, and a heatmap would blur them into a density that does not exist.

### Filters

**Event type** is the main filter. It sits first in the filter row, as a row of buttons, one per event type.

| Button | Value in `event_type` |
| --- | --- |
| Community | `community` |
| Concerts | `concerts` |
| Conferences | `conferences` |
| Expos | `expos` |
| Festivals | `festivals` |
| Performing arts | `performing_arts` |
| Sports | `sports` |

- The seven values match the `event_type` column in `events.csv` exactly.
- Press a button to show only that type. Press more than one to combine them. Press again to switch it off.
- With nothing pressed, all seven types show.
- The map, the ranked list and the timeline all update together.
- Each button carries its event type colour (see "Event type colours").

The other filters:

- Audience tag: food, tech, fitness, students, families, from `audience_tags` in `events.csv`. "Food events" and "tech events" are tags, not types: a food market is community with a food tag, a hackathon is conferences with a tech tag.
- Archetype (the biggest group at the event), date range, indoor or outdoor, borough, maximum stall cost, and "clear all".

### Detail panel (same on map and timeline)

1. **Event:** name, type, date, start and end time, venue, borough, expected attendance, source link.
2. **Who is attending:** the 10 archetype bars and the one-sentence summary (see "Archetype labels"), plus the borough's share aged 18 to 34.
3. **Bring:** 2 to 5 product tiles (brand, product, units, expected reviews, winner badge), the best time slot, and the line explaining the lineup size.
4. **Lineup checks:** vegan option, gluten-free option, chilled capacity, stock, alcohol and CBD rule, each ticked or flagged.
5. **Why:** the engine's three reasons for the lineup, one plain sentence each.
6. **Compare:** tool lineup QRP against habit lineup QRP, expected sign-ups, cost and cost per qualified review.
7. **Add to plan.**

### Request list

Every event added to the plan contributes its units per product, already capped by stock. The tray sums them per product and exports one CSV for the warehouse: brand, product, units, event, date, pop-up code. Quantities follow the engine's rule: expected stops times one sample times a 1.2 buffer.

### Look and feel: Really Good Culture

The visual reference is the `rgc-brand-reference` folder: `index.html` (palette, type, components, artwork, product previews), `tokens.css` (extracted colours, font stacks, starter components), `assets/` (logos, illustrations, icons, product previews, with `asset-manifest.json`). Import `tokens.css` and use the files in `assets/` rather than recreating them. Where this section and `tokens.css` disagree, `tokens.css` wins.

**Overall treatment.** Restrained typography and dense detail next to playful, tactile 3D artwork. A charcoal brand frame (top bar and optional feature panels), a pale neutral workspace for long use, white rounded cards, and subtle purple selection states. The tool is used repeatedly, so the workspace is the light treatment from the product previews, not the dark marketing look.

**Colours** (from the active RGC site styles)

| Role | Value | Used for |
| --- | --- | --- |
| Charcoal canvas | `#1D1D1D` | Opening sequence background, top bar, brand frame |
| Dark text | `#141414` | Text on light surfaces |
| Workspace | `#F4F3EF` (warm) or pale grey | Page background |
| Cards | `#FFFFFF` | List, panels, plan tray |
| Dark detail panel | `#161618` | Detail panel, as in the explorer |
| CTA lime | `#B8F000` | Primary action only |
| CTA green | `#22A651` | Primary action gradient end, strong fit |
| Indigo | `#6A6AE2` | Selection, selected pin ring, focus states, top archetype chip |
| CTA gradient | `linear-gradient(90deg,#B8F000,#22A651)` | The one primary action per screen ("Add to plan") |
| Hero text gradient | `linear-gradient(120deg,#C2FF00,#4DC9E2)` | Bubble rim in the opening sequence, large headings, welcome state only |

**Fit colours** (map pins)

| Fit | Colour |
| --- | --- |
| Strong | `#22A651` |
| Medium | `#EAC24A` |
| Weak | `#C9C7C0` |

**Event type colours** (reuse RGC's category palette for the seven types, in the event type buttons, timeline bars, list dots and legend; the map pins stay coloured by fit so the two never compete)

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

**Typography:** Helvetica, Helvetica Neue, Arial for headings and body (headings weight 400, tight tracking about -.045em); Menlo, SF Mono, ui-monospace for labels, nav, buttons, pin scores and archetype chips (actions 14px uppercase, eyebrows 12px uppercase with wide tracking); Geist for a few supporting headings. Everyday text 14 to 16px, labels 12 to 13px.

**Shape and components**

- Controls (inputs, filter pills, selects): 12px radius, white fill, 1px charcoal border at 16%, green focus border with a faint halo. Primary action: 999px pill, 13px 26px padding, dark label on the lime to green gradient, lifts 1px on hover.
- Panels and cards: 22 to 24px radius, 16 to 24px inner padding, 12 to 16px gaps.
- Top bar: 72px high, charcoal, compact logo, ghost pill buttons, gradient CTA.
- Event cards in the list look like product cards: title, score in monospace, archetype chips, one line on why.
- The lineup is a row of white tiles with the unit count on each, like a shelf.
- Colour never carries meaning alone: the score number is on every pin and every status has a label.

**Artwork.** Use the 3D pieces sparingly, in welcome and empty states and panel headers, never behind tables or charts. Candidates from `assets/`: `rgc-logo.png` (top bar), `star-3d.webp` and `chain.webp` (empty states), `cereal-*.webp` (small ornaments), `bg-*.webp` (soft backgrounds behind the detail header only).

**Voice.** Warm and a little playful in empty and welcome states ("Hi Human, where are we popping up?"), plain and exact everywhere else (units, QRP, dates, shortfalls). Labels like "Not enough in the warehouse" beat generic "Error".

### How the UI connects to the engine

The UI reads files only. It never recomputes fit, QRP or quantities, and the language model never ranks.

| File | Made by | Used for |
| --- | --- | --- |
| `events.csv` | Data lead | Pins, filters, event details, source links |
| `boroughs.csv` and a London borough boundary file (GeoJSON) | Data lead | Borough layer, borough stats, borough bonus tag |
| `brands.csv`, `brand_products.csv` | Data lead | Brand and product names, stock for the stock check |
| `scores.csv` | Model lead | Pin colour, score, list order, expected outcomes, reasons |
| `lineups.json` | Model lead | Products, units, slot, QRP against habit, checks, archetype winners |
| `profiles.json` | Model lead | Brand event profiles. Not shown on this screen now that Product to events mode is removed |
| `impact.json` | Model lead | Impact drawer and uplift strip |
| `month_plan.json` | Model lead | Recommended plan, capacity, brands featured |
| `event_audience.json` (new) | Model lead | Archetype labels and the "Who is attending" panel |
| `requests.csv` (new, written by the UI) | App lead | Warehouse request list with pop-up codes |
| `rgc-brand-reference/` (tokens.css, assets/) | Brand scrape | Colours, type, artwork |

Additions to the file contract (the engine already computes all of these; the files just need to write them out):

```
event_audience.json  event_id -> crowd{10 archetypes, sums to 1}, top_archetypes[3], borough, borough_share_18_34, source_note
lineups.json         add: lineup_size, archetype_winner{archetype: product_id}, checks{vegan, gluten_free, chilled_ok, alcohol_ok, in_stock}, units_by_size{small, medium, large} per product
scores.csv           add: best_product_id
```

`units` stays the medium set; `units_by_size` is what the stall-size toggle switches between. If the engine does not produce it, drop the toggle rather than computing quantities in the UI.

### Build notes

- The map needs no account or key. Tiles need an internet connection (see "If the internet drops").
- Start from stub files (five fake rows each, T+0:15). The UI must run on stubs before the real files exist, including a stub `event_audience.json` with plausible archetype mixes.
- Build order: theme and the PopUpPick opening sequence; Map tab with pins; list, filters and detail panel with archetype labels and cross-highlighting; plan tray and request export; Impact drawer; Timeline tab with the recommended plan; borough layer; compare view.
- Cut order for the UI: compare view, borough layer, timeline brushing, then the stall-size toggle. Keep the opening sequence, the pins, the event type filter, archetype labels, the detail panel, the plan tray, the stock check and the Impact drawer.
- Honesty: the uplift strip and Impact drawer always say uplift on synthetic data is not a measured result.

## Team split

Build for 2.5 hours, then spend 1.5 hours on the demo, all inside your 4 hours. If you start at 13:30, T+4:00 is the 17:30 deadline.

&#91;embedded content: team timeline · 3 people, 2 gates, submit at T+3:45\]

Bars run in parallel; diamonds are gates and fixed times.

| Person | Builds | Hands over |
| --- | --- | --- |
| Data lead | Generator, `events.csv`, `boroughs.csv`, the crowd table as code, profile text | Synthetic tables by T+1:00, events by T+1:30 |
| Model lead | Fit score, Poisson model, lineup optimiser, month plan, uplift test | `scores.csv` by T+1:15; lineups, profiles and impact by T+2:30 |
| App and demo lead | Streamlit: event planner, brand profiles, month plan and impact; then the video | Working app by T+2:30, video by T+3:30 |

**Rules.**

- Stub files go in at T+0:15, so nobody waits on anybody.
- Gate at T+1:15: one event becomes a lineup end to end on synthetic data. If not, drop the month plan and keep the two-way screens.
- Feature freeze at T+2:30; after that, fixes only.
- Cut order if late: borough bonus, then the Poisson model (use fit times footfall instead), then the map, then the month plan. Never cut the two-way screens or the uplift number.

## Demo

The demo runs the three screens in order and lands on one number: the monthly impact in pounds against the habit plan. Replace bracketed values with real output before recording.

# PopUpPick — Before we pack the van
# PopUpPick — Two-minute demo script

## 0:00–0:20 · The pop-up problem

**Visual:** Cookies and mayo on a table at a hand-painting event. Hands reach for the cookies. The mayo stays.

**Voiceover:**  
“At a hand-painting event, the cookies went quickly. The mayo didn’t. Same table. Same crowd. Different results. The team had spent hours finding the event, organising products and setting up—but that effort didn’t give every brand the same chance to connect.”

**On-screen text:**  
**Cookies moved. Mayo stayed.**

## 0:20–0:32 · Why it matters

**Visual:** Quick cuts: event listings, spreadsheets, stock requests, packing boxes.

**Voiceover:**  
“A poor match means missed exposure for client brands, fewer opportunities for WatchHumans sign-ups and reviews, and time and budget that could have worked harder elsewhere.”

**On-screen text:**  
**The event matters. The audience matters. The lineup matters.**

## 0:32–0:53 · Introducing PopUpPick

**Visual:** Charcoal screen. The PopUpPick bubble appears, then pops to reveal the London map.

**Voiceover:**  
“Introducing PopUpPick.

“PopUpPick helps RGC find events where its clients’ products fit the audience—and recommends what to bring, how much, and when to sample.

“It adds a planning layer to RGC’s intelligence, helping the team put products in front of people more likely to try them.”

**On-screen text:**  
**Find suitable events. Bring products that fit.**

## 0:53–1:14 · Show the match

**Visual:** Filter upcoming London events. Select one. Open its estimated audience panel, then click an audience group to highlight a recommended product.

**Voiceover:**  
“Here’s how it works. Choose an upcoming event and see its estimated audience. PopUpPick recommends a product lineup and explains each match. Click an audience group to see which product serves it best—so every product has a reason to be on the table.”

**On-screen text:**  
**Who’s coming → What fits → Why**

## 1:14–1:36 · Turn it into action

**Visual:** Show quantities, sampling time and stock checks. Compare the recommendation with the usual lineup. Add the event to the plan and reveal the stock request.

**Voiceover:**  
“The team gets suggested quantities, a sampling time, and stock and dietary checks. Compare expected sign-ups, reviews and net value with the usual lineup. Then add suitable events to the monthly plan and export one clear stock request.”

**On-screen text:**  
**From event search to packing list.**

**Visible beside forecasts:**  
Synthetic data · Not measured results

## 1:36–2:00 · Make the value clear

**Visual:** Show the completed plan. Highlight client exposure, WatchHumans growth and planning time. Finish on the PopUpPick wordmark.

**Voiceover:**  
“For RGC, the value is clear: less time spent planning, fewer resources committed to poor matches, and better opportunities for client exposure, sign-ups and reviews.

“This demo uses synthetic data. Tracking real results helps improve the next plan.

“Before we pack the van, let’s make sure the products fit the crowd.”

**Final on-screen text:**  
**PopUpPick**  
**The right event. The right audience. A better opportunity.**

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
