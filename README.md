# Pop-up Pick

**A planning tool for RGC's pop-ups that picks the event, the five client brands and the samples, and forecasts how many useful WatchHumans reviews each pop-up will earn.**

Built for EAT_HACK. The full build plan is in [eat_hack.md](eat_hack.md).

> Brands and products are **RGC's real clients** (`brands.csv`). All WatchHumans users, reviews, ratings and pop-up outcomes are **synthetic**: never present them as a client's real results. Borough figures are real Census 2021 data. `events.csv` is currently a **placeholder** of invented events at real London venues.

---

## Overview

RGC runs RGC-first pop-ups, usually two a month: a stall at an event with four or five client brands giving away free product. Each pop-up costs staff time, stall fees and client stock. It pays back in WatchHumans sign-ups and in honest reviews of the brands. Today, RGC chooses the event and the lineup by judgement.

Pop-up Pick turns that choice into a forecast that RGC can check afterwards. It works both ways:

- **Events → brands.** Pick an event and get the best 5-brand lineup, units to bring, the best time slot, and three reasons.
- **Brands → events.** Pick a client brand and get its event profile: where it wins, its best moment and audience, what to sample, where to avoid, and its top five upcoming events.

### The headline number: qualified reviews per pop-up (QRP)

QRP counts WatchHumans reviews written at a pop-up, or within 7 days of it, by people in the reviewed brand's target segment. A single figure covers what RGC gains (sign-ups and data) and what the client gains (feedback from the right people).

```
QRP(e, L) = Σ_{b ∈ L}  F_e × s(e, L) × r_{b,e} × q_{b,e}
```

| Term | Meaning |
|---|---|
| F | Footfall past the stall at event e |
| s | Share who stop and sign up; depends on the lineup L |
| r | Chance that a sign-up reviews brand b |
| q | Share of those reviewers inside b's target segments |

---

## Use case for RGC

| RGC asks | Screen | RGC gets |
|---|---|---|
| "Should we do this event, and with whom?" | Event planner | Ranked events with expected sign-ups, QRP and cost per qualified review; the best lineup with units, time slot and three reasons; the usual lineup's QRP for comparison |
| "Where does this client's product win?" | Brand profiles | Fit across the 7 event types, best moment, best audience, what to sample, where to avoid, top 5 upcoming events |
| "What should next month look like?" | Month plan and impact | The month's pop-ups (RGC's usual 2 a month) and their lineups; total QRP against the habit plan, with the uplift and its confidence interval |

Clients do not pay RGC for pop-up placement, and pop-ups are one RGC service among several. The month plan therefore doesn't guarantee every brand a slot: each pop-up gets its best lineup. Every brand still gets a profile, so RGC can bring it when the right event comes up.

---

## Impact

The tool is measured by its **uplift** over how RGC plans today. The "habit" plan brings RGC's five favourite brands to the biggest events.

```
Uplift = QRP_tool / QRP_habit − 1
```

Current results on synthetic data:

| Measure | Tool | Habit | |
|---|---|---|---|
| Qualified reviews per pop-up, on 12 held-out pop-ups | 186.4 | 136.1 | **+37.0%** (95% CI +28.1% to +44.8%) |
| Cost per qualified review, same 12 pop-ups | £2.22 | £3.04 | −27% |
| November month plan, 2 pop-ups | 396 QRP, £1.66 per review | 289 QRP, £5.04 per review | +37% |
| Sign-up forecast error on held-out pop-ups (Poisson deviance, lower is better) | 2.47 | 65.3 (footfall-only guess) | |

**These numbers show how much is at stake if the patterns hold. They are not a measured result.** The model learns only from the noisy CSVs. A hidden "truth" inside the generator judges the outcome, and the model never sees it.

**Measuring it for real:** give each pop-up a QR code in the WatchHumans sign-up flow, and tag reviews with the pop-up's code. Then alternate tool-picked and manually picked pop-ups for a season, and compare QRP and cost per qualified review.

| Metric | Who it serves | How RGC measures it for real |
|---|---|---|
| Sign-ups per pop-up | RGC: traction | A QR code per pop-up in the sign-up flow |
| QRP | RGC and clients | Reviews tagged with the pop-up code, joined to the reviewer's segment |
| Cost per qualified review | RGC: efficiency | Staff hours, stall fee, travel and units given, divided by QRP |

---

## Plan

The build runs in four hours, split across three roles: data lead, model lead, and app and demo lead. See [eat_hack.md](eat_hack.md) for the timeline, gates, cut order and demo script.

1. Synthetic WatchHumans tables, real London borough data, and an event list. ✅
2. The model: fit score, outcome forecasts, lineup optimiser, month plan, brand profiles, uplift test. ✅
3. The Streamlit app, with three screens reading `outputs/`. ⏳ (app lead)
4. Real upcoming events in place of the placeholder `events.csv`. ⏳
5. RGC's brand sheet (`brands.csv`, 49 real brands) mapped onto the model's need states and segments. ✅

---

## Data files and sources

| File | Rows | Source | Key fields |
|---|---|---|---|
| `brands.csv` | 71 products, 49 brands | **RGC's brand sheet** (real clients) | brand, product, category, sub-category, flavour, format, dietary flags, need states and target segments (inferred), label claims, label → target link |
| `brand_features.csv` | 49 | Built from `brands.csv` | 8 need states, 5 target segments, lineup role (drink, savoury, sweet, condiment, functional, other), vegan, gluten-free, adults-only, chilling, favourite five*, units per month* |
| `brand_products.csv` | 70 | Built from `brands.csv` | one row per product: need states, flavour, format, claims; used to pick what to sample |
| `data/mappings/*.csv` | 39 + 47 | Team assumptions, editable | each inferred need-state or segment phrase in the sheet → weights on the model's 8 needs and 5 segments |
| `popups.csv` | 60 past pop-ups, 2 a month, Apr 2024 to Sep 2026 | Synthetic | date, event type, borough, footfall, lineup, habit flag, stops, sign-ups, reviews, qualified reviews, costs, train/test split (48/12) |
| `popup_brands.csv` | 300 | Synthetic | pop-up × brand: units given, reviews, qualified reviews, average rating |
| `users.csv` | 5,000 | Synthetic WatchHumans | age band, borough, segment and segment scores, traits, category affinities, dietary needs, sign-up source (pop-up code or organic) |
| `reviews.csv` | 20,000 | Synthetic WatchHumans | user, brand, pop-up code or blank, rating 1–5, would buy, liked/disliked attribute, in target segment. Pop-up reviews reconcile exactly with `popup_brands.csv` |
| `boroughs.csv` | 33 | **Census 2021** (ONS TS007, via Nomis); WatchHumans users synthetic | population, share aged 18–34, inner/outer, WatchHumans users per 1,000 people |
| `data/raw/borough_census_2021.csv` | 33 | Census 2021 | the raw borough download |
| `event_types.csv` | 7 | The crowd table in eat_hack.md | need-state vector, assumed audience mix, peak slot, moment, typical dwell and staff |
| `events.csv` | 36, Oct to Dec 2026 | **Placeholder**: real venues, invented events | type, start/end, venue, borough, lat/lon, expected attendance, indoor, audience tags, stall cost, link |

\* Assumptions: the habit "favourite five" are the five brands with the most products on the shelf (Simply Roasted, The Protein Ball Co., Well & Truly, Gut Food / Ferment Fizz, Blanco Niño), and stock per month is synthetic.

**Event types (7):** community, concerts, conferences, expos, festivals, performing arts, sports.
**Need states (8):** hydrate, recover, energy, focus, discovery, sharing, treat, value.
**Segments (5):** students, young professionals, fitness, families, foodies.

**Sources**
- [WatchHumans](https://watchhumans.com/): free products, honest video reviews, community partners such as run clubs
- [ONS Census 2021, TS007 Age by single year, via Nomis](https://www.nomisweb.co.uk/)
- Real events to collect: [London hackathons aggregator](https://london-hackathons.vercel.app), [Let's Do This: London running events](https://www.letsdothis.com/gb/running-events/in-london), food markets, match screenings and campus fairs
- The evidence behind the crowd table is listed in [eat_hack.md](eat_hack.md#sources)

---

## Model structure

```
scripts/                       data generation (writes the CSVs)
  build_brand_features.py      brands.csv + data/mappings -> brand_features.csv, brand_products.csv
  generate_popups.py           past pop-ups, hidden truth (never read by the model)
  generate_watchhumans_data.py users, reviews, boroughs
  get_borough_census.py        Census 2021 download
  build_event_types.py         crowd table -> event_types.csv
  generate_events.py           placeholder events.csv
model/                         the model (reads only the CSVs)
  data.py                      load and validate inputs; event cost
  fit.py                       step 1: fit score and reasons
  outcomes.py                  step 2: Poisson sign-up and review models
  optimise.py                  steps 3 and 6: best lineup, units, time slot
  plan.py                      step 4: month plan
  profiles.py                  step 5: brand event profiles
  impact.py                    uplift test on the 12 held-out pop-ups
  run.py                       runs everything and writes outputs/
outputs/                       what the app reads (+ outputs/stubs/: 5-row versions)
```

1. **Fit score** for every brand at every event:
   `fit = cos(n_b, n_e) × a × c × (1 + h)`
   - n is the need-state vector of the brand and of the event type.
   - a is audience overlap: the crowd's segment mix, learned from who signed up at past pop-ups, against the brand's targets.
   - c is context: chilled or frozen products outdoors, hydrating products in summer.
   - h is the brand's learned rating lift at that event type, shrunk towards zero when it has few reviews.
2. **Expected outcomes** come from two Poisson regressions trained on the 48 training pop-ups.
   - Sign-ups: from footfall, dwell, event type and lineup appeal.
   - Reviews per sign-up: from fit, dwell and event type.
   - QRP = sign-ups × r × q.
3. **Lineup optimiser** shortlists each event's 20 best eligible brands and scores all 15,504 possible 5-brand lineups among them.
   - The score is QRP, with a bonus for covering drink, savoury, sweet and condiment.
   - Hard rules: at least 1 vegan and 1 gluten-free option, at most 2 chilled brands, frozen only indoors, units in stock, and no alcohol or CBD at community, expo or conference events.
   - For each brand it picks the product whose need states best match the event type.
4. **Month plan:** rank events by QRP per pound, with a bonus for boroughs where WatchHumans has few users. Fill RGC's capacity (2 pop-ups a month by default) with no same-day clashes.
5. **Brand profiles:** fit by event type, best moment and audience, what to sample, where to avoid, top 5 events, and a paragraph filled from the numbers by a template.
6. **Quantities and timing:** units = expected stops × 1.2, capped by stock. The slot is the event type's peak-need moment, kept within the event's hours.

The **uplift test** is the only code that touches the generator. The model chooses lineups for the 12 held-out pop-ups, and the generator's hidden world scores them.

---

## Inputs and outputs

**Inputs:** `brand_features.csv` and `brand_products.csv` (built from `brands.csv`), `popups.csv`, `popup_brands.csv`, `users.csv`, `reviews.csv`, `boroughs.csv`, `event_types.csv` and `events.csv`. To add or change brands, edit `brands.csv`, add any new phrases to `data/mappings/`, and rerun the data build.

**Outputs** (`outputs/`):

| File | Contents |
|---|---|
| `scores.csv` | event_id, brand_id, fit, exp_signups, exp_reviews, exp_qrp, in_best_lineup, reason_1–3 (36 × 49 rows) |
| `lineups.json` | event_id → name, date, event_type, brands[5], brand_names[5], products{brand: product}, units{brand: n}, slot, qrp, habit_qrp, cost, cost_per_qr, reasons[3] |
| `profiles.json` | brand_id → fit_by_type{7}, best_type, best_moment, best_audience, sample, avoid, top_events[5], text |
| `impact.json` | uplift, ci_low, ci_high, qrp_tool, qrp_habit, cost_per_qr_tool, cost_per_qr_habit, n_test, per_popup[12] |
| `month_plan.json` | month, capacity, popups[{event_id, date, brands, qrp, cost}], total_qrp, habit_total_qrp, brands_featured |

Example lineup (`E003`, a tech meetup at the Barbican, 15:00–16:30, 221 units each): INDI Brain Bar, mindfuel flow Mushroom Iced Latte, Little's Toffee Nut Instant Coffee, Mission Lemon & Ginseng Energy Drink and All That Matters Superfood Puffs. Expected 168 qualified reviews against 124 for the usual five (synthetic).

---

## Run it

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

To rebuild the data (only needed after changing a generator):

```bash
.venv/bin/python scripts/get_borough_census.py && .venv/bin/python scripts/build_brand_features.py && .venv/bin/python scripts/generate_popups.py . && .venv/bin/python scripts/generate_watchhumans_data.py . && .venv/bin/python scripts/build_event_types.py && .venv/bin/python scripts/generate_events.py
```

To run the model:

```bash
.venv/bin/python -m model.run --month 2026-11 --capacity 2
```
