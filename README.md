# Pop-up Pick

**A planning tool for RGC's pop-ups. For any small event (under 200 people), it matches the WatchHumans archetypes expected in the crowd to RGC's client products, picks the best 2–5 products to bring, and forecasts what the pop-up is worth in pounds: review income (£599 per 15 reviews) minus what it costs, plus the sign-ups and video reach it brings for the pitch.**

Built for EAT_HACK. The full build plan, team split, UI spec and demo script are in [eat_hack.md](eat_hack.md).

> Brands and products are **RGC's real clients** (`brands.csv`). All WatchHumans users, reviews, ratings and pop-up outcomes are **synthetic**: never present them as a client's real results. Pound values come from **assumptions** in `data/value_assumptions.csv` for RGC to replace. Borough figures are real Census 2021 data. `events.csv` is a **placeholder** of invented events at real London venues.

---

## Overview

RGC runs RGC-first pop-ups, usually **two a month, at small events of under 200 people**: a stall where client brands give away free product. Each pop-up costs about £150 for a half day (pitch, insurance, consumables, transport, staff food) plus the product given away. It pays back in reviews RGC sells to clients (£599 for 15, about £40 each), plus WatchHumans sign-ups and publicity. Today, marketing chooses the event and the products by judgement, and some pop-ups don't pay back.

**The idea: archetype matching.** WatchHumans profiles every user against 10 archetypes, built from their purchasing data in the app. Pop-up Pick puts events and products on the same 10 archetypes:

| Profile | Says | Built from |
|---|---|---|
| **Crowd** (per event) | Which archetypes to expect, and in what share | The crowd table's assumption for the event type, updated with the archetypes of people who signed up at past pop-ups of that type |
| **Product affinity** (per product) | How much each archetype likes the product | RGC's brand sheet (target-shopper phrases → archetypes), updated with WatchHumans ratings by reviewer archetype |
| **User** (per person) | Which archetype each user is | WatchHumans purchasing data (synthetic here) |

The match score is how much the expected crowd will like a product. The tool picks the combination of products that best covers the crowd, so every archetype present finds something it likes. It then forecasts sign-ups, reviews and the pop-up's net value, and flags events likely to lose money.

The tool works both ways:

- **Events → products.** Pick an event and get the best 2–5 products (more for bigger crowds), units to bring, time slot, net value, chance of losing money, and three reasons.
- **Brands → events.** Pick a client brand and get its archetype profile and event profile: where it wins, its best moment and archetype, what to sample, where to avoid, and its top five upcoming events.

### The headline number: net value per pop-up (£)

Built only from things RGC can count with a QR code per pop-up. We don't try to judge whether a reviewer is the "right" person, because that can't be verified.

```
Net value = reviews × £39.93          (RGC's price: £599 for 15 reviews)
          + sign-ups × £0              (no paid acquisition today)
          + publicity × £0             (not monetised today; video views reported for the pitch)
          − event cost − units given × £0.50
```

| Part | How RGC measures it for real | Default assumption |
|---|---|---|
| Sign-ups | QR code per pop-up in the WatchHumans sign-up flow | £0 (RGC doesn't pay for acquisition today). Counted and reported for the pitch |
| Reviews | Reviews tagged with the pop-up's code | **£39.93 each**: RGC charges clients £599 for 15 reviews |
| Publicity | Views of review videos from the pop-up; social mentions and tags | £0 today. Estimated views (50% of reviews are videos × 150 views) are reported so they can go into the pitch |
| Event cost | Receipts | Pitch £30–150 + insurance £35 + consumables £30 + transport £20 inner / £35 outer + staff food £10 each ≈ £125–255 for the placeholder events (staff wages excluded by default) |
| Product given | Units brought | £0.50 per unit |

A pop-up is **wasted** when its net value is below zero. Each forecast includes the chance of that happening.

---

## Use case for RGC

| RGC asks | Screen | RGC gets |
|---|---|---|
| "Should we do this event, and with what?" | Event planner | Ranked events with expected sign-ups, reviews, net value and chance of losing money. For each event: the expected archetype mix; the best 2–5 products with units, time slot and three reasons; the usual lineup's net value for comparison |
| "Where does this client's product win?" | Brand profiles | The brand's 10-archetype profile and target archetypes; fit across the 7 event types; best moment and archetype; what to sample; where to avoid; top 5 upcoming events |
| "What should next month look like?" | Month plan and impact | The month's 2 pop-ups and their lineups, events skipped as likely losses, net value against the habit plan, marketing time saved, and the monthly impact in pounds |

**Examples**, from the placeholder events:
- **Weekend AI hackathon, Here East** (140 people → 4 products, 15:00–16:30). mindfuel flow Mushroom Iced Latte, Helen Browning's Organic Corned Beef, ape2o GO Steel Bottle and Mr Filbert's Teriyaki Mochi Rice Bites, 115 units each. Expected 45 sign-ups and 79 reviews.
  - Value: 79 reviews × £39.93 = £3,158, − £125 (event) − £230 (product) = **£2,803 net**, against £2,538 for the usual lineup.
  - For the pitch: 45 new WatchHumans sign-ups and about 5,900 video views.
  - Chance of losing money: about 0%.
- **Pottery workshop, Islington** (30 people → 2 products): about 2 reviews, expected **−£55**, 83% chance of a loss. The month plan skips it.

Clients do not pay RGC for pop-up placement, and pop-ups are one RGC service among several. So no brand is guaranteed a slot: each pop-up gets its best lineup. Every brand still gets a profile, so RGC can bring it when the right event comes up.

---

## Impact

The tool's impact is measured **in pounds a month**, against how RGC plans today. The "habit" plan brings RGC's usual brands (as many as the lineup size) to the biggest events.

```
Monthly impact = (net value per pop-up with the tool − with the habit) × pop-ups per month
               + (marketing hours by hand − with the tool) × pop-ups per month × hourly rate
```

Current results on synthetic data with the default assumptions:

| Measure | Tool | Habit | Difference |
|---|---|---|---|
| Net value per pop-up, 12 held-out pop-ups | £1,354 | £1,147 | **+£207** (95% CI £124 to £297) |
| Wasted pop-ups (net value below £0), same 12 | 8% | 8% | same |
| Reviews per pop-up, same 12 | 42.3 | 37.1 | +14.0% (95% CI +12.9% to +16.0%) |
| Archetype match, 36 upcoming events (0–1) | 0.63 | 0.51 | +24% |
| Marketing time per month (5 h → 1 h per pop-up, £30/h) | 2 h | 10 h | **8 h = £240 saved** |
| **Monthly impact** (2 pop-ups) | | | **£655 a month (£415 from better lineups + £240 of time), about £7,860 a year** |
| November plan, 2 pop-ups | £5,238 net (5 likely-loss events skipped) | £1,612 net at the biggest events | +£3,866 incl. time saved |

**Accuracy checks:**
- The sign-up forecast's error on held-out pop-ups is 2.53 (Poisson deviance), against 8.19 for a footfall-only guess.
- Learning from ratings cuts the error in products' archetype profiles by 18% against the brand sheet alone.

**Biggest levers:** at about £40 a review, a pop-up pays back once it brings in roughly 5–10 reviews, so 25 of the 36 upcoming events are worth doing. The value comes from **choosing the right events** (the November plan earns about three times the biggest-event habit plan) and **better-matched lineups** (+14% reviews). The smallest events, such as a 30-person workshop, still rarely pay back.

**These numbers show how much is at stake if the patterns hold. They are not a measured result.** Outcomes come from a hidden synthetic "truth" the model never sees, and pound values come from assumptions. The result rests on **each pop-up review being billable at £39.93**, i.e. clients have enough reviews contracted to absorb them. Most lineup brands get about 3 reviews per pop-up, and 7% get more than 15 (one £599 package). If extra reviews can't be billed, value falls. Change it in `data/value_assumptions.csv` and rerun.

**Measuring it for real:**
1. Put a QR code per pop-up in the sign-up flow and tag reviews with the pop-up code.
2. Count video views and social mentions.
3. Keep receipts for every pop-up.
4. Time the planning by hand for a month.
5. Alternate tool-picked and manually picked pop-ups for a season, and compare net value per pop-up and the share of wasted pop-ups.

---

## Plan

The build runs in four hours, split across three roles: data lead, model lead, and app and demo lead. See [eat_hack.md](eat_hack.md) for the timeline, gates, cut order, UI spec and demo script.

1. Synthetic WatchHumans tables, real London borough data, and an event list (small events under 200 people). ✅
2. RGC's brand sheet (`brands.csv`, 49 real brands, 70 products) mapped onto the 10 archetypes and 8 need states. ✅
3. Archetype matching: events, products and users on the same 10 archetypes. ✅
4. The model: match, forecasts, lineup sized to attendance, pound value and chance of waste, month plan, brand profiles, impact test. ✅
5. The Streamlit or web app reading `outputs/` (see the location finder UI spec in eat_hack.md). ⏳ (app lead)
6. Real upcoming events in place of the placeholder `events.csv`. ⏳
7. RGC's real figures in `data/value_assumptions.csv`, and real WatchHumans archetype data if RGC can share it. ⏳

**Next, with real data:** QR codes per pop-up, a season of alternating tool-picked and manual pop-ups, and the run clubs and communities WatchHumans already partners with.

---

## Data files and sources

| File | Rows | Source | Key fields |
|---|---|---|---|
| `brands.csv` | 71 products, 49 brands | **RGC's brand sheet** (real clients) | brand, product, category, sub-category, flavour, format, dietary flags, need states and target segments (inferred), label claims, label → target link |
| `brand_products.csv` | 70 | Built from `brands.csv` | one row per product: 10 archetype affinities, 8 need states, flavour, format, claims |
| `brand_features.csv` | 49 | Built from `brands.csv` | 10 archetype affinities, 3 target archetypes, 8 need states, lineup role, vegan, gluten-free, adults-only, chilling, favourite five\*, units per month\* |
| `data/mappings/archetypes.csv` | 47 | Team assumption, editable | each target-shopper phrase in the sheet → weights on the 10 archetypes |
| `data/mappings/need_states.csv` | 39 | Team assumption, editable | each need-state phrase in the sheet → weights on the 8 need states |
| `data/value_assumptions.csv` | 20 | **RGC's pricing and costs, plus assumptions** | £ per review (£599 / 15), sign-up and 1,000 views (£0 today); video share and views; unit cost; per-event costs (pitch, insurance, consumables, transport, staff food, optional wages); one-off kit; marketing hours and rate; pop-ups per month; attendance cap |
| `event_types.csv` | 7 | The crowd table in eat_hack.md | assumed 10-archetype crowd mix, need-state vector, peak slot, moment, typical dwell and staff |
| `events.csv` | 36, Oct to Dec 2026 | **Placeholder**: real venues, invented small events | type, start/end, venue, borough, lat/lon, expected attendance (20 to 190), indoor, audience tags, stall cost, link |
| `popups.csv` | 60 past pop-ups, 2 a month, Apr 2024 to Sep 2026 | Synthetic | date, event type, borough, footfall (under 200), lineup, habit flag, stops, sign-ups, reviews, costs, train/test split (48/12) |
| `popup_brands.csv` | 300 | Synthetic | pop-up × brand: units given, reviews, average rating |
| `users.csv` | 5,000 | Synthetic WatchHumans | primary and secondary archetype, score on all 10 archetypes, age band, borough, traits, food-category affinities, dietary needs, sign-up source (pop-up code or organic) |
| `reviews.csv` | 20,000 | Synthetic WatchHumans | user, brand, pop-up code or blank, rating 1–5, would buy, liked/disliked attribute. Pop-up reviews reconcile exactly with `popup_brands.csv` |
| `boroughs.csv` | 33 | **Census 2021** (ONS TS007, via Nomis); WatchHumans users synthetic | population, share aged 18–34, inner/outer, WatchHumans users per 1,000 people |
| `data/raw/borough_census_2021.csv` | 33 | Census 2021 | the raw borough download |

\* Assumptions: the habit "favourite five" are the five brands with the most products on the shelf (Simply Roasted, Well & Truly, The Protein Ball Co., Gut Food / Ferment Fizz, Blanco Niño). Stock per month is synthetic. The synthetic data still contains a legacy `qualified_reviews` column; the model doesn't use it.

**Archetypes (10):** wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner, conscious consumer.
**Event types (7):** community, concerts, conferences, expos, festivals, performing arts, sports.
**Need states (8):** hydrate, recover, energy, focus, discovery, sharing, treat, value.

**Sources**
- [WatchHumans](https://watchhumans.com/): free products, honest video reviews, community partners such as run clubs
- RGC's brand sheet (`brands.csv` / `brands.csv.xlsx`) and per-event cost figures, from the team
- [ONS Census 2021, TS007 Age by single year, via Nomis](https://www.nomisweb.co.uk/)
- Real events to collect: [London hackathons aggregator](https://london-hackathons.vercel.app), [Let's Do This: London running events](https://www.letsdothis.com/gb/running-events/in-london), food markets, match screenings and campus fairs
- The evidence behind the crowd table's need states is listed in [eat_hack.md](eat_hack.md#sources)

---

## Model structure

```
scripts/                       data build (writes the CSVs)
  build_brand_features.py      brands.csv + data/mappings -> brand_features.csv, brand_products.csv
  build_event_types.py         crowd table -> event_types.csv
  generate_events.py           placeholder events.csv (small events)
  generate_popups.py           past pop-ups; the hidden truth (never read by the model)
  generate_watchhumans_data.py users, reviews, boroughs
  get_borough_census.py        Census 2021 download
model/                         the model (reads only the CSVs)
  data.py                      load and validate inputs; attendance cap; per-event cost
  fit.py                       step 1: archetype match, fit and reasons
  outcomes.py                  step 2: Poisson sign-up and review models
  optimise.py                  steps 3 and 6: lineup size, best lineup, units, time slot
  value.py                     pound value, chance of waste, marketing time saved
  plan.py                      step 4: month plan (skips likely losses)
  profiles.py                  step 5: brand archetype and event profiles
  impact.py                    impact test on the 12 held-out pop-ups, in reviews and pounds
  run.py                       runs everything and writes outputs/
outputs/                       what the app reads (+ outputs/stubs/: 5-row versions)
```

1. **Archetype match.**
   - `match(p, e) = Σ_a crowd_e[a] × affinity_p[a]`, over the 10 archetypes.
   - The crowd mix blends the assumed mix for the type with the archetypes of past pop-up sign-ups, nudged by the event's audience tags.
   - Product affinity blends the brand sheet with ratings by reviewer archetype. With 20 reviews from an archetype, the two count equally.
   - **Fit** for brand b = `max over its products of match × moment × c`. The moment is `0.5 + 0.5 × cos(needs_p, needs_e)` (e.g. thirst after a run), and c is practical context (chilled products outdoors, hydrating products in summer).
2. **Forecasts** come from two Poisson regressions trained on the 48 training pop-ups.
   - Sign-ups: from footfall, dwell, event type and the lineup's archetype match.
   - Reviews per sign-up: from fit, dwell and event type.
3. **Lineup optimiser.**
   - Only events under 200 people are considered.
   - **Size scales with expected attendance:** 2 products under 50 people, 3 under 100, 4 under 150, and 5 from 150 to 199.
   - Shortlist the event's 20 best eligible brands, then score every combination of that size (up to 15,504) on archetype match: `Σ_a crowd_e[a] × (best product in the lineup for archetype a)`.
   - Hard rules: at least 1 vegan and 1 gluten-free option, at most 2 chilled brands, frozen only indoors, units in stock, and no alcohol or CBD at community, expo or conference events.
4. **Pound value** (`value.py`): net value from the forecasts and `data/value_assumptions.csv`. The chance of waste = P(net value < £0), with sign-ups treated as Poisson.
5. **Month plan:** skip events with a negative expected net value or a chance of waste above 50%. Rank the rest by net value, with a bonus for boroughs where WatchHumans has few users. Fill 2 pop-ups a month with no same-day clashes. No brand is guaranteed a slot.
6. **Brand profiles:** the archetype profile, target archetypes, fit by event type, best moment and archetype, what to sample, where to avoid, top 5 events, and a paragraph filled from the numbers by a template.
7. **Quantities and timing:**
   - Units per product = expected stops × 1.2, where expected stops = attendance × the type's stop rate. Units are capped by stock.
   - The slot is the event type's peak-need moment, kept within the event's hours.

The **impact test** is the only code that touches the generator. The model chooses lineups for the 12 held-out pop-ups, and the generator's hidden world plays both lineups out.

---

## Inputs and outputs

**Inputs:** `brand_features.csv` and `brand_products.csv` (built from `brands.csv`), `data/value_assumptions.csv`, `event_types.csv`, `events.csv`, `popups.csv`, `popup_brands.csv`, `users.csv`, `reviews.csv` and `boroughs.csv`.

- **To change brands:** edit `brands.csv`, add any new phrases to `data/mappings/`, and rerun the data build.
- **To use real events:** replace `events.csv`, keeping the same columns; events of 200 or more people are skipped.
- **To use real money figures:** edit `data/value_assumptions.csv` and rerun the model.

**Outputs** (`outputs/`):

| File | Contents |
|---|---|
| `scores.csv` | event_id, brand_id, product, match, fit, exp_signups, exp_reviews, in_best_lineup, reason_1–3 (36 × 49 rows) |
| `lineups.json` | event_id → name, date, event_type, expected_attendance, lineup_size, brands, brand_names, products, units, slot, archetype_mix{10}, match, exp_signups, exp_reviews, value{review_value, signup_value, publicity_value, est_video_views, event_cost, product_cost, net_value, p_waste}, habit_brands, habit_match, habit_exp_reviews, habit_value, reasons[3] |
| `profiles.json` | brand_id → archetype_affinity{10}, target_archetypes[3], fit_by_type{7}, best_type, best_moment, best_audience, sample, avoid, top_events[5], text |
| `impact.json` | net_value_tool, net_value_habit, net_gain_per_popup (+95% CI), waste_rate_tool, waste_rate_habit, review_uplift (+CI), monthly_time_saved_gbp, monthly_impact_gbp, yearly_impact_gbp, per_popup[12] |
| `month_plan.json` | month, capacity, popups[{event_id, date, brands, exp_reviews, net_value, p_waste}], net_value, habit_net_value, skipped_events, marketing_hours_saved, marketing_time_saved_gbp, month_gain_gbp, brands_featured |

---

## Run it

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

To rebuild the data (only needed after changing the brand sheet, mappings or a generator):

```bash
.venv/bin/python scripts/get_borough_census.py && .venv/bin/python scripts/build_brand_features.py && .venv/bin/python scripts/build_event_types.py && .venv/bin/python scripts/generate_events.py && .venv/bin/python scripts/generate_popups.py . && .venv/bin/python scripts/generate_watchhumans_data.py .
```

To run the model:

```bash
.venv/bin/python -m model.run --month 2026-11 --capacity 2
```
