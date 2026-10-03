# Pop-up Pick

**A planning tool for RGC's pop-ups. For real UK events (under 200 people), it scores the expected crowd and every client product on the same 10 WatchHumans archetypes, picks the best 2–5 products to bring, and forecasts what the pop-up is worth in pounds: review income minus what it costs.**

Built for EAT_HACK. The full build plan, team split, UI spec and demo script are in [eat_hack.md](eat_hack.md).

> Brands and products are **RGC's real clients** (`data/raw/brands.csv`). Events are **real UK listings from PredictHQ** (`data/archetypes/events_archetypes.csv`). All WatchHumans users, reviews, ratings and pop-up outcomes are **synthetic**: never present them as a client's real results. Pound values come from RGC's pricing plus **assumptions** in `data/assumptions/value_assumptions.csv`.

## Quick start: the PopUpPick app

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

```bash
.venv/bin/python app.py
```

`app.py` is the single entry point. It runs the whole workflow in about 6 seconds:
1. scores events and products on the archetypes;
2. builds the processed tables and the synthetic history;
3. runs the model.

It then opens the **PopUpPick** website at http://localhost:8000:
- **Opening:** the bubble opening sequence.
- **Map tab:** real UK events as pins (colour = archetype match, size = attendance), with clustering and fly-to.
- **List and filters:** a ranked list and filters (event type, biggest archetype, dates, indoor/outdoor, cost, radius).
- **Detail panel:** who is attending (10 archetype bars), the 2–5 products to bring with units per stall size, winner badges, lineup checks, reasons, and the comparison with the usual lineup.
- **Timeline tab:** the month plan, with the recommended plan and clash or over-capacity warnings.
- **Plan tray:** pop-up codes and a stock check, plus a request-list export (CSV, also saved to `outputs/requests.csv`).
- **Impact drawer:** the uplift with confidence intervals and the 12 held-out pop-ups.

Options:
- `--no-rebuild`: serve the current `outputs/` only.
- `--fetch-events`: pull fresh PredictHQ events first (needs `PREDICTHQ_TOKEN` in `.env`).
- `--port 8001`: use another port.
- `?nosplash` in the address skips the opening sequence. Clicking the wordmark replays it.

The site reads `outputs/` and calculates nothing itself. Map tiles come from OpenStreetMap, so they need an internet connection; everything else works offline. The server only listens on this machine and only serves `app/`, `outputs/`, `data/processed/` and `design/`.

### Deploy the website publicly (Vercel)

The website is static, so `python app.py --export site` writes everything it needs (0.9 MB) to `site/`. Deployed, the request-list export still downloads a CSV; only the save to `outputs/requests.csv` needs the local server.

- **From GitHub:** import the repo in Vercel. `vercel.json` already sets the build command (`python3 app.py --export site --no-rebuild`) and the output folder (`site`).
- **From this machine:** export, then deploy the folder with the Vercel CLI (needs Node.js and a Vercel login):

```bash
.venv/bin/python app.py --export site --no-rebuild
```

```bash
npx vercel deploy site --prod
```

The public site shows real RGC client names next to synthetic forecasts. The "synthetic data, not a measured result" labels stay visible on every screen; keep them.

---

## Overview

RGC runs RGC-first pop-ups, usually **two a month, at small events of under 200 people**: a stall where client brands give away free product. Each pop-up costs about £150 for a half day (pitch, insurance, consumables, transport, staff food) plus the product given away, and more for events far from London. It pays back in reviews RGC sells to clients (£599 for 15, about £40 each), plus WatchHumans sign-ups and publicity. Today, marketing chooses the event and the products by judgement, and some pop-ups don't pay back.

**The idea: one archetype language for events, products and people.** WatchHumans profiles every user against 10 archetypes. Pop-up Pick scores events and products on the same 10, with **one keyword method** (Anisia's `get_event_archetypes.py`):

| What | Scored from | Script |
|---|---|---|
| **Real events** | Title, description, PredictHQ category and labels | `scripts/get_event_archetypes.py` |
| **Event types** (for past pop-ups) | The PredictHQ category | same method, in `scripts/generate_popups.py` → `data/processed/event_types.csv` |
| **Products** | Label claims, product name, label → target link, need states, sub-category, dietary flags, flavour, sheet category, target-segment phrases | `scripts/get_product_archetypes.py` |
| **Users** | Archetype scores from purchasing data (synthetic here, from the shared definitions) | `scripts/generate_watchhumans_synthetic.py` |

The tool then works both ways:

- **Events → products.** Pick an event and get the best 2–5 products (more for bigger crowds), units to bring, time slot, net value, chance of losing money, and three reasons.
- **Brands → events.** Pick a client brand and get its archetype profile, where it wins, what to sample, where to avoid, and its top upcoming events.

### How the archetype scores become a lineup

1. **Keyword scores.** Every event and product gets a score per archetype. Each matching keyword adds the weight of the field it appears in (title or label claims 0.65, description or product name 0.40, …), at most 3 matches per field. The category adds 0.20 × a category table, and labels or target segments add 0.45 × a phrase table. Score = 1 − e^(−total), and the evidence (which words fired) is kept.
2. **Rescale.** Each event's and product's scores are divided by their own top score, so the strongest archetype is 1 for both. Product labels hold more text than event listings, so raw scores aren't comparable until this step.
3. **Crowd.** The event's rescaled scores are turned into shares that sum to 1, then blended 70/30 with the WatchHumans population mix, so no archetype is ever absent from a crowd.
4. **Learn from reviews.** Each product's archetype profile is nudged by WatchHumans ratings from each reviewer archetype (see [How each step uses the data](#how-each-step-uses-the-data)). With 20 reviews from an archetype, the reviews and the keyword score count equally.
5. **Match.** For product p at event e, `match = Σ_a crowd_e[a] × product_p[a]`, from 0 to 1: how much the average attendee will like it. A brand brings its best-matching product. Practical context adjusts it, e.g. ×0.85 for chilled products outdoors.
6. **Lineup.**
   - **Size:** set by attendance: 2 products under 50 people, 3 under 100, 4 under 150, 5 from 150 to 199.
   - **Search:** every combination of that size from the event's 20 best-matching eligible brands is scored (up to 15,504).
   - **Score:** `Σ_a crowd_e[a] × (the best product in the lineup for archetype a)`. Every archetype in the crowd is credited with its favourite product, so a lineup that has something for each part of the crowd beats near-duplicates.
   - **Hard rules:** at least 1 vegan and 1 gluten-free option, at most 2 chilled products, stock available, and no alcohol or CBD at community, expo, conference or family events.
7. **Forecast and £.** Two Poisson models trained on past pop-ups forecast sign-ups (rising with the lineup's match) and reviews. Net value = reviews × £39.93 − event cost − product cost, plus the chance the pop-up loses money.
8. **Month plan.** Skip events likely to lose money, rank the rest by net value, and fill 2 pop-ups a month with no same-day clashes.

---

## Use case for RGC

| RGC asks | Screen | RGC gets |
|---|---|---|
| "Should we do this event, and with what?" | Event planner | Ranked UK events with expected sign-ups, reviews, net value and chance of losing money. For each event: its archetype mix; the best 2–5 products with units, time slot and three reasons; the usual lineup's match and net value for comparison |
| "Where does this client's product win?" | Brand profiles | The brand's 10-archetype profile and target archetypes; fit across event types; best archetype; what to sample; where to avoid; top upcoming events |
| "What should next month look like?" | Month plan and impact | The month's 2 pop-ups and lineups, events skipped as likely losses, net value against the habit plan, marketing time saved, monthly impact in pounds |

**Example: Aladdin Pantomime at the Grand Leicester** (143 people → 4 products, 143 km from London, a family event, so no alcohol or CBD).
- **Crowd:** 39% everyday planners, 28% experience explorers, 12% quality seekers.
- **Lineup:** Saucerer Wild Mushroom & Truffle Pasta Sauce, JimJams Hazelnut Chocolate Spread, Pentire Adrift and Blanco Niño Creamy Jalapeño Tortilla Chips, 49 units each, in the interval (13:35–14:00).
- **Match:** 0.88 against 0.47 for the usual lineup.
- **Value:** 16.5 reviews × £39.93 = £660, − £242 event − £98 product = **£320 net**, against £24 for the usual lineup. Chance of a loss: 6%.

Clients do not pay RGC for pop-up placement, and pop-ups are one RGC service among several. So no brand is guaranteed a slot. Every brand still gets a profile.

---

## Impact

Measured **in pounds a month** against how RGC plans today. The "habit" plan brings RGC's usual brands (as many as the lineup size) to the biggest events.

```
Monthly impact = (net value per pop-up with the tool − with the habit) × pop-ups per month
               + (marketing hours by hand − with the tool) × pop-ups per month × hourly rate
```

Current results on synthetic outcomes with the default assumptions:

| Measure | Tool | Habit | Difference |
|---|---|---|---|
| Archetype match, 22 real events (0–1) | 0.89 | 0.59 | +51% |
| Reviews per pop-up, 12 held-out pop-ups | 40.8 | 34.4 | **+18.6%** (95% CI +13.8% to +22.2%) |
| Net value per pop-up, same 12 | £1,298 | £1,043 | **+£255** (95% CI £121 to £419) |
| Wasted pop-ups (net value below £0), same 12 | 8% | 8% | same |
| Marketing time (5 h → 1 h per pop-up, £30/h) | 2 h | 10 h | **8 h = £240 saved a month** |
| **Monthly impact** (2 pop-ups) | | | **£751 a month (£511 better lineups + £240 time), about £9,010 a year** |
| December plan, 2 pop-ups | £850 net (5 likely-loss events skipped) | £325 net at the biggest events | +£765 incl. time saved |

**Accuracy checks:**
- The sign-up forecast's error on held-out pop-ups is 2.82 (Poisson deviance), against 7.18 for a footfall-only guess.
- Learning from ratings cuts the error in products' archetype profiles by 21% against keywords alone (0.078 → 0.062).

**What drives it:** at about £40 a review, a pop-up pays back after roughly 5–10 reviews, so 17 of the 22 real events are worth doing. The value comes from **better-matched lineups** (+19% reviews) and **choosing the right events**. Events in Scotland and Northern Ireland lose money because of transport (£400+).

**Known limitations:**
- **The same "champion" products repeat.** The archetype with the strongest product tends to win at many events: Saucerer's pasta sauce (in 14 of 22 lineups), The Original Chicken Crackling's Chicken Salt (11) and The Protein Ball Co. (10) appear most. A rotation rule or monthly stock limits would spread brands more evenly.
- **No "moment" factor, by design.** The match is archetype-only, so a pasta sauce can be picked for a pantomime interval if its archetypes fit the crowd.
- **The keyword method only sees what's written.** A product with little label text gets a thin profile until reviews fill it in.

**These numbers show how much is at stake if the patterns hold. They are not a measured result.** Outcomes come from a hidden synthetic "truth" the model never sees. In that world, people stop at the stall when it has something their archetype likes: the hypothesis a real pilot would test.

**Measuring it for real:**
1. Put a QR code per pop-up in the sign-up flow and tag reviews with the pop-up code.
2. Count video views.
3. Keep receipts for every pop-up.
4. Time the planning by hand for a month.
5. Alternate tool-picked and manually picked pop-ups for a season, and compare net value per pop-up and the share of wasted pop-ups.

---

## Plan

The build runs in four hours, split across three roles: data lead, model lead, and app and demo lead. See [eat_hack.md](eat_hack.md).

1. Synthetic WatchHumans tables and past pop-ups (small events under 200 people). ✅
2. RGC's brand sheet (`brands.csv`, 49 real brands, 70 products). ✅
3. Real UK events from PredictHQ, scored on archetypes (Anisia). ✅
4. One keyword method for events, event types and products, and one set of WatchHumans definitions. ✅
5. The model: match, forecasts, lineup sized to attendance, pound value and chance of waste, month plan, brand profiles, impact test. ✅
6. The web app reading `outputs/` (see the location finder UI spec in eat_hack.md). ⏳ (app lead)
7. RGC's real figures in `data/assumptions/value_assumptions.csv`, and real WatchHumans archetype data if RGC can share it. ⏳

---

## Repository layout

```
data/
  raw/           inputs exactly as received
                   brands.csv (+ brands.xlsx)   RGC's brand sheet: 71 products, 49 real brands (xlsx = original)
                   events_raw.pkl               PredictHQ pull: 22 real UK events
                   manual_events.csv            hand-entered events (EAT_HACK, 3 Oct 2026), scored like PredictHQ ones
  mappings/      team assumptions that translate text, editable
                   segment_archetypes.csv       target-segment phrase -> archetype weights (products' "labels")
                   need_states.csv              need-state phrase -> 8 need states (practical rules only)
  assumptions/   value_assumptions.csv          RGC pricing (£599 / 15 reviews) and cost assumptions
  archetypes/    everything scored on the 10 WatchHumans archetypes (keyword method)
                   events_archetypes.csv        22 real events: scores, primary/secondary archetype, evidence
                   products_archetypes.csv      70 products: scores, primary/secondary archetype, evidence
  processed/     model-ready tables
                   brand_products.csv           rescaled product scores, event-type matches, flags
                   brand_features.csv           brand profiles, target archetypes, favourite five*, stock*
                   event_types.csv              keyword crowd mix per event type, dwell, staff, peak slot
  synthetic/     synthetic WatchHumans and pop-up history (stand-ins for RGC's real data)
                   popups.csv, popup_brands.csv 60 past pop-ups (2 a month, Apr 2024 - Sep 2026), 300 brand rows
                   users.csv, reviews.csv       5,000 users with archetypes; 20,000 reviews
                   watch_humans_synthetic.csv   standalone user base (generate_watchhumans_synthetic.py)
app.py           single entry point: runs the workflow, then serves the PopUpPick website
app/             the website: index.html, styles.css, app.js (Leaflet map, RGC look)
scripts/         the data pipeline, in run order below; paths.py says where every file lives
model/           the recommender (reads only CSVs)
outputs/         what the app reads
tests/           unit tests
design/          rgc-brand-reference: RGC look and feel for the app
archive/         retired files kept for reference (placeholder events, borough and Census data, earlier
                 mappings, the standalone matcher, output stubs); see archive/README.md
```

\* Assumptions: the habit "favourite five" are the five brands with the most products on the shelf (Simply Roasted, Well & Truly, The Protein Ball Co., Gut Food / Ferment Fizz, Blanco Niño). Stock per month is synthetic.

**Archetypes (10)**, defined once in `scripts/generate_watchhumans_synthetic.py`: wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner, conscious consumer.

**Sources:** [WatchHumans](https://watchhumans.com/); [PredictHQ](https://www.predicthq.com/) for real UK events; RGC's brand sheet and per-event cost figures from the team.

---

## Pipeline: which script makes which file

| Stage | Script | Reads | Writes |
|---|---|---|---|
| 1. Raw data | `get_raw_event_data.py` (needs a PredictHQ token) | PredictHQ API | `data/raw/events_raw.pkl` |
| 2. Map to archetypes | `get_event_archetypes.py` | `raw/events_raw.pkl` | `archetypes/events_archetypes.csv` |
| | `get_product_archetypes.py` | `raw/brands.csv`, `mappings/segment_archetypes.csv` | `archetypes/products_archetypes.csv` |
| 3. Process | `build_event_types.py` | event-type settings in `generate_popups.py` (keyword crowd per category) | `processed/event_types.csv` |
| | `build_brand_features.py` | `raw/brands.csv`, `archetypes/products_archetypes.csv`, `mappings/need_states.csv`, `processed/event_types.csv` | `processed/brand_products.csv`, `processed/brand_features.csv` |
| 4. Synthetic history | `generate_popups.py` | `processed/brand_features.csv` | `synthetic/popups.csv`, `synthetic/popup_brands.csv` |
| | `generate_watchhumans_data.py` | `synthetic/popups.csv`, `synthetic/popup_brands.csv` | `synthetic/users.csv`, `synthetic/reviews.csv` |
| 5. Model | `python -m model.run` | see below | `outputs/*` |

All paths are under `data/`.

## How each step uses the data

| Model step | What it does | Data files |
|---|---|---|
| **1. Crowd per event** | Rescale the event's archetype scores, turn them into shares, blend 70/30 with the WatchHumans population | `archetypes/events_archetypes.csv`; population from `synthetic/users.csv` (organic sign-ups) |
| **2. Product profiles** | Rescaled keyword scores per product and brand | `processed/brand_products.csv`, `processed/brand_features.csv` |
| **3. Learn from reviews** | Shift each brand's archetype profile by how each reviewer archetype rated it | `synthetic/reviews.csv` (who rated which brand, how, when), `synthetic/users.csv` (each reviewer's primary archetype), `processed/brand_features.csv` (the keyword profile it shifts), `synthetic/popups.csv` (split date: only reviews before the held-out period) |
| **4. Match** | `match = Σ_a crowd[a] × product[a]` per product and event; the brand brings its best product | outputs of steps 1–3; flags from `processed/brand_products.csv` |
| **5. Forecast** | Poisson models: sign-ups from footfall, dwell, type and lineup match; reviews per sign-up from match; stop rate per type | trained on `synthetic/popups.csv`, `synthetic/popup_brands.csv`; past crowds from `processed/event_types.csv` and `synthetic/users.csv` |
| **6. Lineup** | Size by attendance; best combination by archetype coverage; dietary, chilling, stock and adults-only rules | `archetypes/events_archetypes.csv` (attendance, title for family events), `processed/brand_features.csv` (vegan, gluten-free, chilling, adults-only, stock) |
| **7. £ value** | Reviews × £39.93 − event cost − product cost; chance of loss | `assumptions/value_assumptions.csv`; distance from `archetypes/events_archetypes.csv` (lat/lon) |
| **8. Month plan** | Skip likely losses, pick the best 2 | outputs of steps 6–7 |
| **9. Impact test** | Tool vs usual lineup at the 12 held-out pop-ups, scored by the hidden synthetic world | `synthetic/popups.csv` (test rows), `scripts/generate_popups.py` (the hidden world, only here) |

---

## Outputs

| File | Contents |
|---|---|
| `outputs/scores.csv` | event_id, brand_id, best_product_id, product, match, fit, exp_signups, exp_reviews, in_best_lineup, reason_1–3 (22 × 49 rows) |
| `outputs/lineups.json` | event_id → name, title, date, start/end, category, lat/lon, km_from_london, family_event, expected_attendance, lineup_size, size_line, brands, products, product_ids, units, units_by_size{small, medium, large}, product_reviews, archetype_winner, checks{vegan, gluten_free, chilled_ok, alcohol_ok, in_stock}, slot, archetype_mix{10}, match, exp_signups, exp_reviews, value{review_value, est_video_views, event_cost, product_cost, net_value, p_waste}, habit lineup and value, reasons[3] |
| `outputs/profiles.json` | brand_id → archetype_affinity{10}, target_archetypes[3], fit_by_type, best_type, best_audience, sample, avoid, top_events[5], text |
| `outputs/impact.json` | net_value_tool, net_value_habit, net_gain_per_popup (+95% CI), waste rates, review_uplift (+CI), monthly_impact_gbp, yearly_impact_gbp, per_popup[12] |
| `outputs/event_audience.json` | event_id → crowd{10 archetypes}, top_archetypes[3], source_note (for the "Who is attending" panel) |
| `outputs/requests.csv` | written by the app: the warehouse request list (brand, product, units, event, date, pop-up code) |
| `outputs/month_plan.json` | month, capacity, popups[{event_id, date, km_from_london, brands, exp_reviews, net_value, p_waste}], net_value, habit_net_value, skipped_events, marketing time saved, month_gain_gbp |

---

## Run it

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

To rebuild the data (only after changing brands, mappings, events or a generator):

```bash
.venv/bin/python scripts/get_event_archetypes.py && .venv/bin/python scripts/get_product_archetypes.py && .venv/bin/python scripts/build_event_types.py && .venv/bin/python scripts/build_brand_features.py && .venv/bin/python scripts/generate_popups.py && .venv/bin/python scripts/generate_watchhumans_data.py
```

To run the model and the tests:

```bash
.venv/bin/python -m model.run --month 2026-12 --capacity 2
```

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```
