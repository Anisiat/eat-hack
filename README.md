# PopUpPick

**PopUpPick tells Really Good Culture (RGC) which client products to bring to a pop-up, and whether the pop-up is worth doing.** For each event it estimates who will be in the crowd, matches that crowd to RGC's products on the 10 WatchHumans shopper archetypes, picks the best 2–5 products, and forecasts what the pop-up is worth in pounds.

Built at EAT_HACK, 3 October 2026. The original build plan, UI spec and demo script are in [eat_hack.md](eat_hack.md).

> **What's real and what isn't.** Brands and products are RGC's real clients (`data/raw/brands.csv`). Events are real UK listings from PredictHQ, plus EAT Hack itself. WatchHumans users, reviews and the pop-up history are **synthetic**, so every result below shows what's at stake, not a measured result. Never present a synthetic rating as a client's real result.

---

## The problem

RGC runs RGC-first pop-ups, usually **two a month at small events of under 200 people**: a stall where a handful of client brands give away free product.

- **Each pop-up costs money:** about £150 for a half day (pitch, insurance, consumables, transport, staff food), plus the product given away.
- **It pays back in reviews:** RGC sells honest WatchHumans reviews to clients at **£599 for 15**, about £40 each. Pop-ups also bring new WatchHumans sign-ups and publicity.
- **Today it's a judgement call.** Marketing spends hours finding an event and guessing which products to request from the warehouse. The usual habit is the same few brands at the biggest events, whoever turns up. Some pop-ups don't pay back, and nobody can say in advance which.

## The solution

PopUpPick turns that judgement into a forecast RGC can check afterwards.

**The core idea is one shared language.** WatchHumans already profiles every user against 10 archetypes: wellness seeker, trend enthusiast, thoughtful buyer, smart saver, quality seeker, on-the-go shopper, impulse buyer, experience explorer, everyday planner and conscious consumer. PopUpPick scores **events** and **products** on the same 10 archetypes with **one keyword method**, so it can measure how well a product suits the people expected at an event.

For any event, PopUpPick gives:
- **Who will be there:** the expected share of each archetype in the crowd.
- **What to bring:** 2–5 products (more for bigger crowds), each the favourite of a different part of the crowd, with units per product, the best time slot and three reasons.
- **What it's worth:** expected sign-ups and reviews, net value in £, and the chance the pop-up loses money, all compared with RGC's usual lineup.
- **What to do this month:** the best 2 pop-ups, skipping events likely to lose money.

---

## Quick start

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

```bash
.venv/bin/python app.py
```

`app.py` is the single entry point. It runs the whole workflow in about 6 seconds, then opens the **PopUpPick** website at http://localhost:8000.

| Option | What it does |
|---|---|
| `--no-rebuild` | Serve the current `outputs/` without rerunning the workflow |
| `--fetch-events` | Pull fresh events from PredictHQ first (needs `PREDICTHQ_TOKEN` in `.env`) |
| `--export site` | Write a static copy of the website to `site/` for Vercel or any static host |
| `--port 8001` | Serve on another port |
| `?nosplash` in the address | Skip the opening animation (clicking the PopUpPick wordmark replays it) |

---

## How it works

```
data/raw/brands.csv ─────► get_product_archetypes ─► products' archetype scores ─┐
data/raw/events_raw.pkl ─┐                                                      ├─► model ─► outputs/ ─► website
data/raw/manual_events ──┴► get_event_archetypes ──► events' archetype scores ──┤
synthetic pop-up history, users, reviews ───────────────────────────────────────┤
data/assumptions/value_assumptions.csv (£599 / 15 reviews, costs) ──────────────┘
```

### 1. Score events and products on the archetypes (one keyword method)
`scripts/get_event_archetypes.py` scores each event from its title, description, PredictHQ category and labels. `scripts/get_product_archetypes.py` applies the same method to each product, using its label claims, name, sub-category, need states, dietary flags, flavour, sheet category and target-segment phrases.
- Each matching keyword adds the weight of the field it's in (title or label claims 0.65, description or product name 0.40, down to flavour 0.15), with at most 3 matches per field.
- The category adds 0.20 × a category table, and labels or target segments add 0.45 × a phrase table (`data/mappings/segment_archetypes.csv`).
- Score per archetype = 1 − e^(−total). Every score keeps its evidence: which words fired.

### 2. Build the model's view of each event and product
- **Rescale.** Each event's and product's scores are divided by their own top score, so the strongest archetype is 1 for both.
- **Crowd.** An event's rescaled scores become shares that sum to 1, blended 70/30 with the WatchHumans population, so no archetype is ever absent.
- **Learn from reviews.** Each product's profile is nudged by how each reviewer archetype rated it. With 20 reviews from an archetype, ratings and keywords count equally. This cuts profile error by 21% against keywords alone.

### 3. Match and pick the lineup
- **Match** for product p at event e = Σ over the 10 archetypes of crowd share × product score: how much the average attendee will like it. Each brand brings its best-matching product.
- **Lineup size** comes from attendance: 2 products under 50 people, 3 under 100, 4 under 150, and 5 from 150 to 199.
- **Lineup score** = Σ crowd share × the best score any product in the lineup has for that archetype. Every group in the crowd is credited with its favourite product, so the best lineup covers the whole crowd rather than repeating one profile. All combinations from the event's 20 best-matching brands are scored.
- **Hard rules:** at least one vegan and one gluten-free option, at most 2 chilled products, stock available, and no alcohol or CBD at community, expo, conference or family events.

### 4. Forecast and value
- **Forecasts.** Two Poisson models trained on 48 past pop-ups predict sign-ups (rising with the lineup's match, footfall and dwell time) and reviews per sign-up. The 12 most recent pop-ups are held back for testing.
- **Net value** = reviews × £39.93 − event cost − product given (£0.50 a unit). Sign-ups and publicity are £0 today but reported, so they can go in the pitch.
- **Event cost** = pitch (£30–150, £90 when unknown) + insurance £35 + consumables £30 + staff food £10 each + transport (£20 + £0.40/km from London).
- **Chance of a loss** = the probability net value comes out below £0.
- **Units** = expected stops × 1.2, capped by stock, with small, medium and large stall sizes.

### 5. Plan the month and measure impact
- **Month plan.** Skip events with negative expected value or a chance of loss over 50%, rank the rest by net value, and take 2 with no same-day clash. Clients don't pay for placement, so no brand is guaranteed a slot.
- **Impact test.** At the 12 held-out pop-ups, PopUpPick's lineup and RGC's usual lineup are played out in the hidden synthetic world (`scripts/generate_popups.py`). The model never sees that world; it's only used to judge.

---

## Worked example: EAT Hack

EAT Hack, 3 October 2026, central London, about 100 people, so **4 products**.

| Crowd group | Share | Its favourite in the lineup |
|---|---|---|
| Quality seekers | 21% | Simply Roasted Sea Salt Potato Crisps (score 0.96) |
| Everyday planners | 18% | Dr. Will's Avocado Oil Mayo (1.00) |
| Experience explorers | 16% | Pentire Adrift, non-alcoholic (1.00) |
| The other 7 groups | 45% | spread across the four, including Helen Browning's Organic Corned Beef |

| | PopUpPick | Usual lineup |
|---|---|---|
| Archetype match | **0.85** | 0.60 |
| Expected reviews | **48** | 35 |
| Net value | **£1,584** (48 × £39.93 − £185 event − £160 product) | £1,071 |

80 units of each product, best served 15:00–16:30, with 28 expected WatchHumans sign-ups.

---

## Impact

Synthetic results with the default assumptions:

| Measure | PopUpPick | Usual lineup | Difference |
|---|---|---|---|
| Reviews per pop-up, 12 held-out pop-ups | 40.8 | 34.4 | **+18.6%** (95% CI +13.8% to +22.2%) |
| Net value per pop-up, same 12 | £1,298 | £1,043 | **+£255** (95% CI £121 to £419) |
| Archetype match, 23 upcoming events | 0.89 | 0.59 | +51% |
| Marketing time (5 h → 1 h per pop-up at £30/h) | 2 h a month | 10 h a month | £240 a month |
| **Total** | | | **£751 a month, about £9,010 a year** |
| December plan, 2 pop-ups | £850 (5 likely losses skipped) | £325 at the biggest events | |

The sign-up forecast's error on held-out pop-ups is 2.82 (Poisson deviance), against 7.18 for a footfall-only guess.

**Limitations**
- **The history is synthetic.** The numbers show what's at stake if the patterns hold.
- **Champion products repeat.** The strongest product for a common archetype wins at many events (e.g. Saucerer's pasta sauce). A rotation rule or monthly stock limits would spread brands more evenly.
- **No "moment" factor, by design.** Matching is archetype-only, so a product can be picked for an event even if the setting is unusual for it.
- **Distance.** Events far from London (Scotland, Northern Ireland) usually lose money on transport.

**Measuring it for real:**
1. Put a QR code on each pop-up in the WatchHumans sign-up flow, and tag reviews with the pop-up code (each pop-up gets one in the app).
2. Keep receipts for every pop-up.
3. Time the planning both ways for a month.
4. Alternate tool-picked and manually picked pop-ups for a season, and compare net value per pop-up.

Real results then replace the synthetic history with no code changes.

---

## The PopUpPick website

`app.py` serves a single-page app in `app/` (plain HTML, CSS and JavaScript, Leaflet map, RGC look). It reads `outputs/` and calculates nothing itself.

- **Opening:** the PopUpPick bubble on charcoal pops into the site.
- **Map tab:** real UK events as pins. Colour shows archetype match, size shows attendance, and nearby events cluster.
- **List and filters:** a ranked event list with filters for event type, biggest archetype, dates, indoor or outdoor, cost, radius and search.
- **Detail panel:**
  - who is attending (10 archetype bars; click one to see which product wins that group);
  - the products to bring, with units per stall size;
  - lineup checks, reasons, and the comparison with the usual lineup.
- **Timeline tab:** the month plan, with the recommended plan and clash or over-capacity warnings.
- **Plan tray:** pop-up codes, a stock check, and a request-list export for the warehouse (CSV, also saved to `outputs/requests.csv`).
- **Impact drawer:** the uplift with confidence intervals and the 12 held-out pop-ups.

---

## Repository structure

```
app.py                 single entry point: runs the workflow, then serves the website
app/                   the website: index.html, styles.css, app.js
model/                 the recommender (reads only CSVs)
  data.py              load inputs; real events -> crowd shares, attendance, UK cost
  fit.py               archetype match, learning from reviews, reasons
  outcomes.py          Poisson sign-up and review forecasts
  optimise.py          lineup size, best lineup, units, time slot
  value.py             net value in £, chance of a loss, marketing time
  plan.py              month plan
  impact.py            impact test on the 12 held-out pop-ups
  run.py               runs the model and writes outputs/
scripts/               the data pipeline (paths.py says where every file lives)
  get_raw_event_data.py             PredictHQ pull (only with --fetch-events)
  get_event_archetypes.py           keyword method for events
  get_product_archetypes.py         keyword method for products
  build_event_types.py              crowd and settings per event type
  build_brand_features.py           rescaled product and brand tables
  generate_popups.py                synthetic pop-up history and the hidden "truth"
  generate_watchhumans_data.py      synthetic users and reviews
  generate_watchhumans_synthetic.py WatchHumans definitions: archetypes, prevalence, traits
data/
  raw/           brands.csv, events_raw.pkl, manual_events.csv (EAT Hack)
  mappings/      segment_archetypes.csv, need_states.csv (team assumptions, editable)
  assumptions/   value_assumptions.csv (RGC pricing and costs)
  archetypes/    events_archetypes.csv, products_archetypes.csv
  processed/     brand_products.csv, brand_features.csv, event_types.csv
  synthetic/     popups.csv, popup_brands.csv, users.csv, reviews.csv
outputs/               what the website reads
design/rgc-brand-reference/   RGC colour tokens and the 4 images the website uses
tests/                 unit tests for event scoring, product scoring and the user generator
eat_hack.md            original build plan, UI spec and demo script
vercel.json            static deployment settings
```

## Data files and sources

| File | Rows | Source | What it holds |
|---|---|---|---|
| `data/raw/brands.csv` | 71 rows: 70 products, 49 brands | **RGC's brand sheet** (real clients) | brand, product, category, flavour, format, dietary flags, need states and target segments (inferred), label claims |
| `data/raw/events_raw.pkl` | 22 | **PredictHQ** (real UK events under 200 people) | title, description, category, labels, dates, location, attendance |
| `data/raw/manual_events.csv` | 1 | Hand-entered, same definition as Anisia's `add_eat_hack_event.py` | EAT Hack |
| `data/mappings/segment_archetypes.csv` | 47 | Team assumption | each target-segment phrase in the brand sheet → archetype weights |
| `data/mappings/need_states.csv` | 39 | Team assumption | each need-state phrase → 8 need states (used for practical rules) |
| `data/assumptions/value_assumptions.csv` | 21 | RGC pricing and team assumptions | £ per review, unit cost, per-event costs, transport, marketing time, pop-ups per month, attendance cap |
| `data/archetypes/events_archetypes.csv` | 23 | keyword method | 10 archetype scores per event, with evidence |
| `data/archetypes/products_archetypes.csv` | 70 | keyword method | 10 archetype scores per product, with evidence |
| `data/processed/brand_products.csv`, `brand_features.csv` | 70, 49 | built from the above | rescaled scores, best event type, dietary and practical flags, assumed stock and usual lineup |
| `data/processed/event_types.csv` | 7 | keyword method on the category | typical crowd, duration, staff and peak time per event type (for past pop-ups) |
| `data/synthetic/popups.csv`, `popup_brands.csv` | 60, 300 | **Synthetic** | past pop-ups (2 a month, Apr 2024 – Sep 2026), 48 for training, 12 held out |
| `data/synthetic/users.csv`, `reviews.csv` | 5,000, 20,000 | **Synthetic WatchHumans** | users with archetype scores and traits; ratings by user and brand |

**Sources:** [WatchHumans](https://watchhumans.com/), [PredictHQ](https://www.predicthq.com/), RGC's brand sheet and cost figures from the team, and [Really Good Culture](https://reallygoodculture.com/) for the visual identity.

## Outputs

| File | Contents |
|---|---|
| `outputs/lineups.json` | per event: title, date and times, location, attendance, lineup size, products and units (per stall size), time slot, crowd mix, match, expected sign-ups and reviews, £ value and chance of loss, checks, the archetype each product wins, the usual lineup's figures, three reasons |
| `outputs/event_audience.json` | per event: crowd share of each archetype and the top three |
| `outputs/scores.csv` | per event and brand: best product, match, expected reviews, three reasons |
| `outputs/month_plan.json` | the recommended pop-ups for the month, against the habit plan, with time saved |
| `outputs/impact.json` | uplift with confidence intervals, net value and waste rates, monthly and yearly impact, the 12 held-out pop-ups |
| `outputs/requests.csv` | written by the website: warehouse request list with pop-up codes (not committed) |

---

## Change inputs

- **New events:** set `PREDICTHQ_TOKEN` in `.env` and run `python app.py --fetch-events`, or add a row to `data/raw/manual_events.csv`.
- **New or changed brands:** edit `data/raw/brands.csv`, and add any new target-segment phrases to `data/mappings/segment_archetypes.csv`.
- **Real money figures:** edit `data/assumptions/value_assumptions.csv`; each row says how to replace it.
- **Real WatchHumans data:** replace the files in `data/synthetic/` with the same columns.

## Deploy publicly (Vercel)

The website is static, so it runs on any static host. Deployed, "Export request list" still downloads the CSV; only the save into `outputs/requests.csv` needs the local server.

- **From GitHub:** import the repo in Vercel. `vercel.json` sets the build command (`python3 app.py --export site --no-rebuild`) and the output folder.
- **From this machine** (needs Node.js and a Vercel login):

```bash
.venv/bin/python app.py --export site --no-rebuild
```

```bash
npx vercel deploy site --prod
```

The public site shows real client names next to synthetic forecasts, with a "synthetic data, not a measured result" label on every screen. Keep those labels.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

## Team

Built at EAT_HACK by Maks Mroczkowski, Anisia Talianu, Jayla Kwok and Sophia Mok.
