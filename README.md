# Pop-up Pick

**A planning tool for RGC's pop-ups. For any event, it matches the WatchHumans archetypes expected in the crowd to RGC's client products, picks the best 2–5 products to bring, and forecasts how many useful reviews the pop-up will earn.**

Built for EAT_HACK. The full build plan, team split and demo script are in [eat_hack.md](eat_hack.md).

> Brands and products are **RGC's real clients** (`brands.csv`). All WatchHumans users, reviews, ratings and pop-up outcomes are **synthetic**: never present them as a client's real results. Borough figures are real Census 2021 data. `events.csv` is a **placeholder** of invented events at real London venues.

---

## Overview

RGC runs RGC-first pop-ups, usually **two a month**: a stall at an event where client brands give away free product. Each pop-up costs staff time, stall fees and client stock. It pays back in WatchHumans sign-ups and in honest reviews of the brands. Today, RGC chooses the event and the products by judgement.

**The idea: archetype matching.** WatchHumans profiles every user against 10 archetypes, built from their purchasing data in the app. Pop-up Pick puts events and products on the same 10 archetypes:

| Profile | Says | Built from |
|---|---|---|
| **Crowd** (per event) | Which archetypes to expect, and in what share | The crowd table's assumption for the event type, updated with the archetypes of people who signed up at past pop-ups of that type |
| **Product affinity** (per product) | How much each archetype likes the product | RGC's brand sheet (target-shopper phrases → archetypes), updated with WatchHumans ratings by reviewer archetype |
| **User** (per person) | Which archetype each user is | WatchHumans purchasing data (synthetic here) |

The match score is how much the expected crowd will like a product. The tool picks the combination of products that best covers the crowd: every archetype present should find something it likes.

The tool works both ways:

- **Events → products.** Pick an event and get the best lineup of 2 to 5 products (more for bigger events), the units to bring, the best time slot, and three reasons.
- **Brands → events.** Pick a client brand and get its archetype profile and event profile: where it wins, its best moment and archetype, what to sample, where to avoid, and its top five upcoming events.

### The headline number: qualified reviews per pop-up (QRP)

QRP counts WatchHumans reviews written at a pop-up, or within 7 days of it, by people in one of the reviewed brand's target archetypes (its top three). A single figure covers what RGC gains (sign-ups and data) and what the client gains (feedback from the right people).

```
QRP(e, L) = Σ_{b ∈ L}  F_e × s(e, L) × r_{b,e} × q_{b,e}
```

| Term | Meaning |
|---|---|
| F | Footfall past the stall at event e (expected attendance) |
| s | Share who stop and sign up; rises with the lineup's archetype match |
| r | Chance that a sign-up reviews brand b |
| q | Share of those reviewers inside b's target archetypes |

---

## Use case for RGC

| RGC asks | Screen | RGC gets |
|---|---|---|
| "Should we do this event, and with what?" | Event planner | Ranked events with expected sign-ups, QRP and cost per qualified review. For each event: the expected archetype mix; the best 2–5 products with units, time slot and three reasons; the usual lineup's match and QRP for comparison |
| "Where does this client's product win?" | Brand profiles | The brand's 10-archetype profile and target archetypes; fit across the 7 event types; best moment and archetype; what to sample; where to avoid; top 5 upcoming events |
| "What should next month look like?" | Month plan and impact | The month's pop-ups (2 by default) and their lineups; total QRP and cost per qualified review against the habit plan, with the uplift and its confidence interval |

**Examples**, from the placeholder events:
- **Weekend AI hackathon, Here East** (550 people, 5 products, 15:00–16:30): Sunfly Sunflower Seed Butter, Little's Toffee Nut Instant Coffee, The Protein Ball Co. Stuffed Matcha & Vanilla, ötzibrew Dandelion & Burdock Coffee Alternative, Mr Filbert's Teriyaki Mochi Rice Bites. Archetype match 0.62 against 0.51 for the usual five: Protein Ball Co. wins the trend enthusiasts, Little's the on-the-go shoppers, and Mr Filbert's the experience explorers.
- **Comedy night, Camden** (70 people, 3 products): Penrhos Handcrafted Dry Gin, JimJams Hazelnut Chocolate Spread, NOMO Caramel Choc Bar.

Clients do not pay RGC for pop-up placement, and pop-ups are one RGC service among several. So no brand is guaranteed a slot: each pop-up gets its best lineup. Every brand still gets a profile, so RGC can bring it when the right event comes up.

---

## Impact

The tool is measured by its **uplift** over how RGC plans today. The "habit" plan brings RGC's usual five brands (the first 2–5 of them, matching the lineup size) to the biggest events.

```
Uplift = QRP_tool / QRP_habit − 1
```

Current results on synthetic data:

| Measure | Tool | Habit | Difference |
|---|---|---|---|
| Archetype match per pop-up, 36 upcoming events (0–1) | 0.64 | 0.52 | +22% |
| Qualified reviews per pop-up, 12 held-out pop-ups | 62.8 | 57.1 | **+9.9%** (95% CI +4.8% to +17.3%) |
| Cost per qualified review, same 12 pop-ups | £6.60 | £7.25 | −9% |
| November month plan, 2 pop-ups | 141 QRP for £516 (£3.65 per review) | 140 QRP for £668 (£4.76 per review) | −23% cost per review |
| Sign-up forecast error, held-out pop-ups (Poisson deviance, lower is better) | 1.98 | 67.1 (footfall-only guess) | |
| Product archetype profile error vs. the hidden truth | 0.071 (sheet + reviews) | 0.087 (sheet only) | −18% |

**These numbers show how much is at stake if the patterns hold. They are not a measured result.** The model learns only from the noisy CSVs. A hidden "truth" inside the generator judges the outcome, and the model never sees it. In that world, people stop at the stall when it has something their archetype likes: the hypothesis a real pilot would test.

**Measuring it for real:** give each pop-up a QR code in the WatchHumans sign-up flow, and tag reviews with the pop-up's code. Then alternate tool-picked and manually picked pop-ups for a season, and compare QRP and cost per qualified review.

| Metric | Who it serves | How RGC measures it for real |
|---|---|---|
| Sign-ups per pop-up | RGC: traction | A QR code per pop-up in the sign-up flow |
| QRP | RGC and clients | Reviews tagged with the pop-up code, joined to the reviewer's archetype |
| Cost per qualified review | RGC: efficiency | Staff hours, stall fee, travel and units given, divided by QRP |
| Archetype match | RGC and clients | The match score against the actual archetypes of the people who signed up |

---

## Plan

The build runs in four hours, split across three roles: data lead, model lead, and app and demo lead. See [eat_hack.md](eat_hack.md) for the timeline, gates, cut order and demo script.

1. Synthetic WatchHumans tables, real London borough data, and an event list. ✅
2. RGC's brand sheet (`brands.csv`, 49 real brands, 70 products) mapped onto the 10 archetypes and 8 need states. ✅
3. Archetype matching: events, products and users on the same 10 archetypes. ✅
4. The model: match, outcome forecasts, lineup optimiser with attendance-scaled size, month plan, brand profiles, uplift test. ✅
5. The Streamlit app, with three screens reading `outputs/`. ⏳ (app lead)
6. Real upcoming events in place of the placeholder `events.csv`. ⏳
7. Real WatchHumans archetype definitions and user split, if RGC can share them, in place of the synthetic assumptions. ⏳

**Next, with real data:** a QR code per pop-up; a season of alternating tool-picked and manual pop-ups; and the run clubs and communities WatchHumans already partners with.

---

## Data files and sources

| File | Rows | Source | Key fields |
|---|---|---|---|
| `brands.csv` | 71 products, 49 brands | **RGC's brand sheet** (real clients) | brand, product, category, sub-category, flavour, format, dietary flags, need states and target segments (inferred), label claims, label → target link |
| `brand_products.csv` | 70 | Built from `brands.csv` | one row per product: 10 archetype affinities, 8 need states, flavour, format, claims |
| `brand_features.csv` | 49 | Built from `brands.csv` | 10 archetype affinities, 3 target archetypes, 8 need states, lineup role, vegan, gluten-free, adults-only, chilling, favourite five\*, units per month\* |
| `data/mappings/archetypes.csv` | 47 | Team assumption, editable | each target-shopper phrase in the sheet → weights on the 10 archetypes |
| `data/mappings/need_states.csv` | 39 | Team assumption, editable | each need-state phrase in the sheet → weights on the 8 need states |
| `event_types.csv` | 7 | The crowd table in eat_hack.md | assumed 10-archetype crowd mix, need-state vector, peak slot, moment, typical dwell and staff |
| `events.csv` | 36, Oct to Dec 2026 | **Placeholder**: real venues, invented events | type, start/end, venue, borough, lat/lon, expected attendance (70 to 5,000), indoor, audience tags, stall cost, link |
| `popups.csv` | 60 past pop-ups, 2 a month, Apr 2024 to Sep 2026 | Synthetic | date, event type, borough, footfall, lineup, habit flag, stops, sign-ups, reviews, qualified reviews, costs, train/test split (48/12) |
| `popup_brands.csv` | 300 | Synthetic | pop-up × brand: units given, reviews, qualified reviews, average rating |
| `users.csv` | 5,000 | Synthetic WatchHumans | primary and secondary archetype, score on all 10 archetypes, age band, borough, traits, food-category affinities, dietary needs, sign-up source (pop-up code or organic) |
| `reviews.csv` | 20,000 | Synthetic WatchHumans | user, brand, pop-up code or blank, rating 1–5, would buy, liked/disliked attribute, in target archetype. Pop-up reviews reconcile exactly with `popup_brands.csv` |
| `boroughs.csv` | 33 | **Census 2021** (ONS TS007, via Nomis); WatchHumans users synthetic | population, share aged 18–34, inner/outer, WatchHumans users per 1,000 people |
| `data/raw/borough_census_2021.csv` | 33 | Census 2021 | the raw borough download |

\* Assumptions: the habit "favourite five" are the five brands with the most products on the shelf (Simply Roasted, Well & Truly, The Protein Ball Co., Gut Food / Ferment Fizz, Blanco Niño). Stock per month is synthetic.

**Archetypes (10):** wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner, conscious consumer.
**Event types (7):** community, concerts, conferences, expos, festivals, performing arts, sports.
**Need states (8):** hydrate, recover, energy, focus, discovery, sharing, treat, value.

**Sources**
- [WatchHumans](https://watchhumans.com/): free products, honest video reviews, community partners such as run clubs
- RGC's brand sheet (`brands.csv` / `brands.csv.xlsx`), compiled by the team
- [ONS Census 2021, TS007 Age by single year, via Nomis](https://www.nomisweb.co.uk/)
- Real events to collect: [London hackathons aggregator](https://london-hackathons.vercel.app), [Let's Do This: London running events](https://www.letsdothis.com/gb/running-events/in-london), food markets, match screenings and campus fairs
- The evidence behind the crowd table's need states is listed in [eat_hack.md](eat_hack.md#sources)

---

## Model structure

```
scripts/                       data build (writes the CSVs)
  build_brand_features.py      brands.csv + data/mappings -> brand_features.csv, brand_products.csv
  build_event_types.py         crowd table -> event_types.csv
  generate_events.py           placeholder events.csv
  generate_popups.py           past pop-ups; the hidden truth (never read by the model)
  generate_watchhumans_data.py users, reviews, boroughs
  get_borough_census.py        Census 2021 download
model/                         the model (reads only the CSVs)
  data.py                      load and validate inputs; event cost
  fit.py                       step 1: archetype match, fit and reasons
  outcomes.py                  step 2: Poisson sign-up and review models
  optimise.py                  steps 3 and 6: lineup size, best lineup, units, time slot
  plan.py                      step 4: month plan
  profiles.py                  step 5: brand archetype and event profiles
  impact.py                    uplift test on the 12 held-out pop-ups
  run.py                       runs everything and writes outputs/
outputs/                       what the app reads (+ outputs/stubs/: 5-row versions)
```

1. **Archetype match.**
   - `match(p, e) = Σ_a crowd_e[a] × affinity_p[a]`, over the 10 archetypes.
   - The crowd mix blends the assumed mix for the type with the archetypes of past pop-up sign-ups (50 sign-ups' worth of weight on the assumption), nudged by the event's audience tags.
   - Product affinity blends the brand sheet with ratings by reviewer archetype. With 20 reviews from an archetype, the two count equally.
   - **Fit** for brand b = `max over its products of match × moment × c`. The moment is `0.5 + 0.5 × cos(needs_p, needs_e)` (e.g. thirst after a run), and c is practical context (chilled products outdoors, hydrating products in summer).
2. **Expected outcomes** come from two Poisson regressions trained on the 48 training pop-ups.
   - Sign-ups: from footfall, dwell, event type and the lineup's archetype match.
   - Reviews per sign-up: from fit, dwell and event type.
   - QRP = sign-ups × r × q.
3. **Lineup optimiser.**
   - **Size scales with expected attendance:** 2 products under 50 people, 3 under 150, 4 under 500, and 5 at 500 or more.
   - Shortlist the event's 20 best eligible brands, then score every combination of that size (up to 15,504).
   - The score is the lineup's archetype match, `Σ_a crowd_e[a] × (best product in the lineup for archetype a)`. Each expected archetype is credited with its favourite product, so products that win different parts of the crowd beat near-duplicates.
   - Hard rules: at least 1 vegan and 1 gluten-free option, at most 2 chilled brands, frozen only indoors, units in stock, and no alcohol or CBD at community, expo or conference events.
   - Each brand brings its best-matching product at that event.
4. **Month plan:** rank events by QRP per pound, with a bonus for boroughs where WatchHumans has few users. Fill RGC's capacity (2 pop-ups a month by default) with no same-day clashes. No brand is guaranteed a slot.
5. **Brand profiles:** the archetype profile, target archetypes, fit by event type, best moment and archetype, what to sample, where to avoid, top 5 events, and a paragraph filled from the numbers by a template.
6. **Quantities and timing:**
   - Units per product = expected stops × 1.2, where expected stops = attendance × the type's stop rate. Units are capped by stock.
   - The slot is the event type's peak-need moment, kept within the event's hours.

The **uplift test** is the only code that touches the generator. The model chooses lineups for the 12 held-out pop-ups, and the generator's hidden world scores them.

---

## Inputs and outputs

**Inputs:** `brand_features.csv` and `brand_products.csv` (built from `brands.csv`), `event_types.csv`, `events.csv`, `popups.csv`, `popup_brands.csv`, `users.csv`, `reviews.csv` and `boroughs.csv`.

- **To change brands:** edit `brands.csv`, add any new phrases to `data/mappings/`, and rerun the data build.
- **To use real events:** replace `events.csv`, keeping the same columns.

**Outputs** (`outputs/`):

| File | Contents |
|---|---|
| `scores.csv` | event_id, brand_id, product, match, fit, exp_signups, exp_reviews, exp_qrp, in_best_lineup, reason_1–3 (36 × 49 rows) |
| `lineups.json` | event_id → name, date, event_type, lineup_size, brands, brand_names, products{brand: product}, archetype_mix{10}, match, habit_match, units{brand: n}, slot, exp_signups, exp_reviews, qrp, habit_qrp, cost, cost_per_qr, reasons[3] |
| `profiles.json` | brand_id → archetype_affinity{10}, target_archetypes[3], fit_by_type{7}, best_type, best_moment, best_audience, sample, avoid, top_events[5], text |
| `impact.json` | uplift, ci_low, ci_high, qrp_tool, qrp_habit, cost_per_qr_tool, cost_per_qr_habit, n_test, per_popup[12] |
| `month_plan.json` | month, capacity, popups[{event_id, date, brands, qrp, cost}], total_qrp, habit_total_qrp, cost_per_qr, brands_featured |

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
