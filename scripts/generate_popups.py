"""
generate_popups.py - synthetic RGC-first pop-up history for Pop-up Pick (EAT_HACK).

Writes three files to an output folder (default: ./out):
  brands.csv        20 fictional client brands: what RGC knows about each brand
  popups.csv        60 past pop-ups, one row each, Oct 2025 to Sep 2026
  popup_brands.csv  one row per pop-up and brand: units, reviews, qualified reviews, rating

Everything is synthetic. Brand names are invented; event names are generic.
The hidden truth (brand quality and the outcome formulas) lives only in this file and
never appears in the CSVs. The model must learn from the CSVs alone; only the uplift
test may call simulate().

Run:  python scripts/generate_popups.py [output_folder]   (use . to write to the repo root)
"""
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

# ---------------------------------------------------------------- shared taxonomy
NEEDS = ["hydrate", "recover", "energy", "focus", "discovery", "sharing", "treat", "value"]
SEGMENTS = ["students", "young_professionals", "fitness", "families", "foodies"]
EVENT_TYPES = ["community", "concerts", "conferences", "expos", "festivals", "performing_arts", "sports"]
CORE_CATEGORIES = {"drink", "savoury", "sweet", "condiment"}

# ---------------------------------------------------------------- brands (fictional)
# id, name, category, sub_category, description,
# needs (hydrate, recover, energy, focus, discovery, sharing, treat, value), target segments,
# needs_chilling, frozen, vegan, gluten_free
BRANDS = [
    ("B01", "Sparkfold Soda", "drink", "prebiotic soda", "Lightly sparkling prebiotic soda",
     [.6, .1, .2, .2, .6, .4, .6, .3], ["students", "young_professionals", "foodies"], 1, 0, 1, 1),
    ("B02", "Tidewell Hydrate", "drink", "electrolyte drink", "Low-sugar electrolyte drink for after exercise",
     [1., .9, .4, .2, .2, 0., 0., .3], ["fitness", "young_professionals"], 0, 0, 1, 1),
    ("B03", "Northbrew", "drink", "cold brew coffee", "Canned cold brew coffee",
     [.1, 0., 1., .9, .3, .1, .3, .3], ["young_professionals", "students"], 1, 0, 1, 1),
    ("B04", "Kombuchee", "drink", "kombucha", "Small-batch kombucha in seasonal flavours",
     [.5, .2, .2, .1, .8, .3, .4, .2], ["foodies", "young_professionals"], 1, 0, 1, 1),
    ("B05", "Lentil Lark", "savoury", "lentil crisps", "Baked lentil crisps in sharing bags",
     [0., .1, .3, .2, .3, .9, .6, .5], ["students", "young_professionals", "families"], 0, 0, 1, 1),
    ("B06", "Popwright", "savoury", "popcorn", "Sweet and salty popcorn",
     [0., 0., .2, .2, .3, 1., .7, .6], ["students", "young_professionals", "families"], 0, 0, 1, 1),
    ("B07", "Seedwork", "savoury", "seed crackers", "Seeded crackers for grazing boards",
     [0., .2, .3, .3, .5, .6, .3, .3], ["foodies", "young_professionals"], 0, 0, 1, 1),
    ("B08", "Umami Drift", "savoury", "seaweed snacks", "Crispy seaweed puffs",
     [0., 0., .2, .2, .8, .5, .5, .4], ["foodies", "students"], 0, 0, 1, 1),
    ("B09", "Cacao Field", "sweet", "dark chocolate", "Single-origin dark chocolate bars",
     [0., .1, .5, .5, .5, .4, .9, .2], ["young_professionals", "foodies"], 0, 0, 1, 1),
    ("B10", "Lolly Loft", "sweet", "ice lollies", "Real-fruit ice lollies",
     [.6, .1, .1, 0., .3, .3, 1., .4], ["families", "students"], 1, 1, 1, 1),
    ("B11", "Crumbhouse", "sweet", "cookies", "Gooey bakery-style cookies",
     [0., 0., .4, .1, .2, .6, 1., .5], ["students", "families"], 0, 0, 0, 0),
    ("B12", "Fruitling", "sweet", "fruit snacks", "Fruit and veg snacks for children",
     [.1, 0., .3, 0., .2, .3, .8, .6], ["families"], 0, 0, 1, 1),
    ("B13", "Ember & Ash", "condiment", "hot sauce", "Small-batch hot sauces",
     [0., 0., .1, 0., 1., .7, .5, .2], ["foodies", "young_professionals"], 0, 0, 1, 1),
    ("B14", "Redline", "condiment", "chilli oil", "Crunchy chilli oil",
     [0., 0., .1, 0., .9, .5, .5, .2], ["foodies"], 0, 0, 1, 1),
    ("B15", "Tangle", "condiment", "chutney", "Fruit chutneys and relishes",
     [0., 0., .1, 0., .7, .6, .5, .3], ["foodies", "families"], 0, 0, 1, 1),
    ("B16", "Dip Shift", "condiment", "dip pots", "Single-serve hummus and dip pots",
     [0., .1, .3, .3, .4, .9, .4, .5], ["young_professionals", "students"], 1, 0, 1, 1),
    ("B17", "Protein Rebel", "functional", "protein bar", "High-protein snack bars",
     [0., .9, .7, .4, .2, .1, .3, .5], ["fitness", "young_professionals", "students"], 0, 0, 0, 1),
    ("B18", "Fuel Bites", "functional", "energy balls", "Oat and date energy balls",
     [0., .6, .9, .5, .2, .2, .4, .5], ["fitness", "students"], 0, 0, 1, 0),
    ("B19", "Rootshot", "functional", "ginger shots", "Cold-pressed ginger shots",
     [.2, .5, .7, .4, .5, 0., .1, .2], ["young_professionals", "fitness"], 1, 0, 1, 1),
    ("B20", "Mellow Gut", "functional", "fibre gummies", "Prebiotic fibre gummies",
     [0., .2, .1, .3, .4, .1, .4, .4], ["young_professionals", "families"], 0, 0, 0, 1),
]
FAVOURITE_FIVE = ["B01", "B05", "B11", "B13", "B17"]   # RGC's habit lineup

BRAND = {}
for bid, name, cat, sub, desc, needs, targets, chill, frozen, vegan, gf in BRANDS:
    BRAND[bid] = dict(brand_id=bid, brand_name=name, category=cat, sub_category=sub, description=desc,
                      needs=np.array(needs, float),
                      target=np.array([1.0 if s in targets else 0.0 for s in SEGMENTS]),
                      targets=targets, needs_chilling=chill, frozen=frozen, vegan=vegan, gluten_free=gf)

# ---------------------------------------------------------------- event types
# Seven event categories (PredictHQ-style). Each blends the sub-types listed in its names.
# needs: same order as NEEDS; mix: audience share by SEGMENTS (sums to 1)
EVENT = {
    "sports": dict(needs=[1., .9, .5, .1, .2, .5, .2, .3], mix=[.10, .35, .40, .10, .05],
                   footfall=(300, 1500), dwell=2, stop=.22, signup=.28, stall=(0, 120), staff=2, indoor=0.3,
                   start=["09:00", "17:00", "19:45"], days=[1, 2, 5, 6],
                   names=["Community 5K finish", "10K race finish", "Half marathon finish",
                          "Football screening", "Rugby screening"],
                   boroughs=["Richmond upon Thames", "Wandsworth", "Greenwich", "Hackney", "Tower Hamlets",
                             "Southwark", "Lambeth", "Hammersmith and Fulham", "Brent", "Kingston upon Thames",
                             "Barnet", "Waltham Forest"]),
    "community": dict(needs=[.3, .2, .2, .1, .9, .7, .7, .5], mix=[.10, .25, .15, .25, .25],
                      footfall=(200, 2000), dwell=3, stop=.18, signup=.25, stall=(0, 200), staff=2, indoor=0.3,
                      start=["09:00", "11:00"], days=[5, 6],
                      names=["Weekend food market", "Farmers' market", "Run club social", "Family fun day",
                             "Community street party"],
                      boroughs=["Southwark", "Hackney", "Lewisham", "Greenwich", "Camden", "Islington", "Lambeth",
                                "Waltham Forest", "Haringey", "Croydon", "Ealing", "Merton", "Newham",
                                "Richmond upon Thames"]),
    "concerts": dict(needs=[.9, .2, .8, 0., .3, .4, .3, .3], mix=[.35, .45, .05, .00, .15],
                     footfall=(300, 2000), dwell=4, stop=.10, signup=.15, stall=(150, 400), staff=3, indoor=1.0,
                     start=["19:30"], days=[3, 4, 5],
                     names=["Live gig", "Club night", "DJ night", "Arena concert"],
                     boroughs=["Hackney", "Camden", "Lambeth", "Islington", "Southwark", "Tower Hamlets", "Brent",
                               "Greenwich", "Hammersmith and Fulham"]),
    "conferences": dict(needs=[.4, .1, .9, 1., .4, .3, .4, .6], mix=[.35, .55, .04, .02, .04],
                        footfall=(100, 800), dwell=7, stop=.45, signup=.40, stall=(0, 150), staff=2, indoor=1.0,
                        start=["09:30", "10:00"], days=[1, 2, 3, 5, 6],
                        names=["Weekend AI hackathon", "Student hackathon", "Fintech hack day", "Tech conference",
                               "Startup summit"],
                        boroughs=["Islington", "Hackney", "Camden", "Tower Hamlets", "City of London",
                                  "Westminster", "Southwark", "Newham"]),
    "expos": dict(needs=[.2, 0., .6, .4, .8, .3, .5, .9], mix=[.55, .20, .05, .05, .15],
                  footfall=(500, 3000), dwell=4, stop=.18, signup=.40, stall=(50, 250), staff=3, indoor=0.9,
                  start=["10:00", "11:00"], days=[0, 1, 2, 3, 5],
                  names=["Freshers' fair", "Societies fair", "Food and drink expo", "Lifestyle show"],
                  boroughs=["Camden", "Westminster", "Tower Hamlets", "Kensington and Chelsea", "Southwark",
                            "Islington", "Newham", "Hammersmith and Fulham", "Hillingdon"]),
    "festivals": dict(needs=[1., .3, .6, 0., .7, .6, .7, .3], mix=[.25, .40, .10, .10, .15],
                      footfall=(1500, 5000), dwell=7, stop=.08, signup=.20, stall=(300, 800), staff=4, indoor=0.0,
                      start=["12:00"], days=[5, 6],
                      names=["Summer music festival", "Food and music festival", "Street food festival",
                             "Street festival"],
                      boroughs=["Newham", "Lambeth", "Hackney", "Greenwich", "Haringey", "Tower Hamlets",
                                "Waltham Forest", "Brent", "Barking and Dagenham", "Croydon"]),
    "performing_arts": dict(needs=[.3, 0., .2, .1, .4, .8, .9, .3], mix=[.10, .45, .05, .10, .30],
                            footfall=(200, 1200), dwell=2.5, stop=.12, signup=.20, stall=(50, 200), staff=2,
                            indoor=0.85, start=["18:30", "19:00"], days=[3, 4, 5],
                            names=["Theatre interval", "Comedy night", "Dance show", "Open-air theatre"],
                            boroughs=["Westminster", "Camden", "Southwark", "Lambeth", "Islington", "Hackney",
                                      "Richmond upon Thames", "Kensington and Chelsea"]),
}
for p in EVENT.values():
    p["needs"] = np.array(p["needs"], float)
    p["mix"] = np.array(p["mix"], float)

OUTER_BOROUGHS = {"Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Croydon", "Ealing", "Enfield",
                  "Greenwich", "Harrow", "Havering", "Hillingdon", "Hounslow", "Kingston upon Thames", "Merton",
                  "Redbridge", "Richmond upon Thames", "Sutton", "Waltham Forest"}   # ONS Outer London
STAFF_RATE_GBP = 16.0                       # assumed loaded hourly cost per staff member
MONTHLY_HIGH_C = {1: 8, 2: 9, 3: 12, 4: 15, 5: 18, 6: 21, 7: 23, 8: 23, 9: 20, 10: 16, 11: 11, 12: 8}

# RGC's habit: big, busy events, whatever the brand fit
HABIT_EVENT_WEIGHTS = {"community": .25, "festivals": .18, "expos": .15, "sports": .14,
                       "concerts": .10, "performing_arts": .10, "conferences": .08}
FESTIVAL_MONTHS = {5, 6, 7, 8, 9}

# ---------------------------------------------------------------- hidden truth (never written to CSV)
QUALITY = dict(zip(sorted(BRAND), np.random.default_rng(SEED + 1).normal(0, 0.25, len(BRAND))))


def segment_match(bid, event_type):
    """Share of the event's crowd inside the brand's target segments."""
    return float(EVENT[event_type]["mix"] @ BRAND[bid]["target"])


def true_fit(bid, event):
    """Hidden fit between a brand and an event, 0 to 1."""
    b, p = BRAND[bid], EVENT[event["event_type"]]
    cos = float(b["needs"] @ p["needs"] / (np.linalg.norm(b["needs"]) * np.linalg.norm(p["needs"])))
    f = cos * (0.4 + 0.6 * segment_match(bid, event["event_type"]))
    outdoor = not event["indoor"]
    if b["needs_chilling"] and outdoor and event["event_type"] in ("sports", "festivals", "community"):
        f *= 0.85
    if outdoor and event["temp_c"] >= 20 and b["needs"][0] >= 0.5:
        f *= 1.15
    if b["frozen"] and event["temp_c"] <= 12:
        f *= 0.6
    return float(np.clip(f, 0, 1))


def lineup_appeal(lineup, event):
    fits = [true_fit(b, event) for b in lineup]
    cover = len({BRAND[b]["category"] for b in lineup} & CORE_CATEGORIES) / 4
    same_sub = sum(BRAND[a]["sub_category"] == BRAND[c]["sub_category"] for a, c in combinations(lineup, 2))
    return float(np.clip(np.mean(fits) * (0.85 + 0.15 * cover) - 0.05 * same_sub, 0, 1))


def simulate(event, lineup, seed=None):
    """Outcomes of one pop-up. seed=None returns expected values; an int returns one random draw.

    event: dict with event_type, footfall, indoor (0/1), temp_c
    lineup: list of 5 brand ids
    """
    p = EVENT[event["event_type"]]
    appeal = lineup_appeal(lineup, event)
    stop_rate = p["stop"] * (0.75 + 0.5 * appeal)
    dwell_factor = min(1.0, 0.5 + p["dwell"] / 8)
    rng = None if seed is None else np.random.default_rng(seed)

    stops = event["footfall"] * stop_rate if rng is None else rng.binomial(event["footfall"], stop_rate)
    signups = stops * p["signup"] if rng is None else rng.binomial(stops, p["signup"])
    per_brand = []
    for bid in lineup:
        fit = true_fit(bid, event)
        r = (0.25 + 0.3 * fit) * dwell_factor
        q = segment_match(bid, event["event_type"])
        mean_rating = float(np.clip(3.0 + 1.8 * fit + QUALITY[bid], 1, 5))
        if rng is None:
            reviews, qualified, rating = signups * r, signups * r * q, mean_rating
            units = stops * 0.65
        else:
            reviews = rng.binomial(signups, r)
            qualified = rng.binomial(reviews, q)
            rating = (float(np.clip(rng.normal(mean_rating, 0.6 / np.sqrt(reviews) + 0.05), 1, 5))
                      if reviews else np.nan)
            units = int(round(stops * rng.uniform(0.5, 0.8)))
        per_brand.append(dict(brand_id=bid, units_given=units, reviews=reviews,
                              qualified_reviews=qualified, avg_rating=rating))
    return dict(appeal=appeal, stops=stops, signups=signups, per_brand=per_brand,
                reviews=sum(x["reviews"] for x in per_brand),
                qualified_reviews=sum(x["qualified_reviews"] for x in per_brand))


# ---------------------------------------------------------------- history generator
def make_history(n_months=12, per_month=5, first_month=(2025, 10)):
    rng = np.random.default_rng(SEED)
    rows, brand_rows, used_dates = [], [], set()
    year, month = first_month
    pid = 0
    for _ in range(n_months):
        weights = {k: v for k, v in HABIT_EVENT_WEIGHTS.items()
                   if not (k == "festivals" and month not in FESTIVAL_MONTHS)}
        types = list(weights)
        probs = np.array([weights[t] for t in types]) / sum(weights.values())
        days_in_month = pd.Period(f"{year}-{month:02d}").days_in_month
        for _ in range(per_month):
            etype = types[rng.choice(len(types), p=probs)]
            p = EVENT[etype]
            # a date in this month on a suitable weekday, not already used
            for _ in range(200):
                d = pd.Timestamp(year=year, month=month, day=int(rng.integers(1, days_in_month + 1)))
                if d.weekday() in p["days"] and d not in used_dates:
                    break
            used_dates.add(d)
            borough = p["boroughs"][rng.integers(len(p["boroughs"]))]
            indoor = int(rng.random() < p["indoor"])
            temp = round(MONTHLY_HIGH_C[month] + rng.normal(0, 2.5), 1)
            footfall = int(rng.integers(p["footfall"][0], p["footfall"][1] + 1))
            habit = rng.random() < 0.70
            if habit:
                lineup = list(FAVOURITE_FIVE)
            else:   # occasional variety: five random brands, at least one drink
                while True:
                    lineup = sorted(rng.choice(sorted(BRAND), 5, replace=False).tolist())
                    if any(BRAND[b]["category"] == "drink" for b in lineup):
                        break
            event = dict(event_type=etype, footfall=footfall, indoor=indoor, temp_c=temp)
            pid += 1
            out = simulate(event, lineup, seed=SEED * 1000 + pid)

            stall = 0 if p["stall"][1] == 0 else int(round(rng.integers(p["stall"][0], p["stall"][1] + 1), -1))
            staff_cost = p["staff"] * (p["dwell"] + 2) * STAFF_RATE_GBP
            travel = 40 + (20 if borough in OUTER_BOROUGHS else 0)
            total = stall + staff_cost + travel
            ratings = [x["avg_rating"] for x in out["per_brand"] if x["reviews"]]
            weights_r = [x["reviews"] for x in out["per_brand"] if x["reviews"]]

            rows.append(dict(
                popup_id=f"P{pid:03d}", date=d.date().isoformat(), weekday=d.day_name(),
                start_time=p["start"][rng.integers(len(p["start"]))], event_type=etype,
                event_name=f"{p['names'][rng.integers(len(p['names']))]}, {borough}", borough=borough,
                indoor=indoor, dwell_hours=p["dwell"], temp_c=temp, footfall=footfall,
                lineup="|".join(lineup), habit_lineup=int(habit), staff=p["staff"],
                stops=int(out["stops"]), units_given=int(sum(x["units_given"] for x in out["per_brand"])),
                signups=int(out["signups"]), reviews=int(out["reviews"]),
                qualified_reviews=int(out["qualified_reviews"]),
                avg_rating=round(float(np.average(ratings, weights=weights_r)), 2) if ratings else np.nan,
                stall_fee_gbp=stall, staff_cost_gbp=round(staff_cost, 2), travel_gbp=travel,
                total_cost_gbp=round(total, 2),
                cost_per_signup_gbp=round(total / max(out["signups"], 1), 2),
                cost_per_qualified_review_gbp=round(total / max(out["qualified_reviews"], 1), 2)))
            for x in out["per_brand"]:
                brand_rows.append(dict(popup_id=f"P{pid:03d}", brand_id=x["brand_id"],
                                       brand_name=BRAND[x["brand_id"]]["brand_name"],
                                       units_given=int(x["units_given"]), reviews=int(x["reviews"]),
                                       qualified_reviews=int(x["qualified_reviews"]),
                                       avg_rating=None if np.isnan(x["avg_rating"]) else round(x["avg_rating"], 2)))
        month += 1
        if month == 13:
            year, month = year + 1, 1

    popups = pd.DataFrame(rows).sort_values("date", kind="stable").reset_index(drop=True)
    new_id = {old: f"P{i + 1:03d}" for i, old in enumerate(popups["popup_id"])}   # P001 = earliest
    popups["popup_id"] = popups["popup_id"].map(new_id)
    popups["split"] = ["train"] * (len(popups) - 12) + ["test"] * 12
    popup_brands = pd.DataFrame(brand_rows)
    popup_brands["popup_id"] = popup_brands["popup_id"].map(new_id)
    popup_brands = popup_brands.sort_values("popup_id", kind="stable")
    return popups, popup_brands.reset_index(drop=True)


def brands_table():
    rng = np.random.default_rng(SEED + 2)
    rows = []
    for bid in sorted(BRAND):
        b = BRAND[bid]
        row = dict(brand_id=bid, brand_name=b["brand_name"], category=b["category"],
                   sub_category=b["sub_category"], description=b["description"])
        row.update({f"need_{n}": v for n, v in zip(NEEDS, b["needs"])})
        row.update({f"target_{s}": int(v) for s, v in zip(SEGMENTS, b["target"])})
        row.update(needs_chilling=b["needs_chilling"], frozen=b["frozen"], vegan=b["vegan"],
                   gluten_free=b["gluten_free"], favourite_five=int(bid in FAVOURITE_FIVE),
                   units_available_per_month=int(rng.integers(6, 21) * 100))
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    out_dir.mkdir(parents=True, exist_ok=True)
    popups, popup_brands = make_history()
    brands_table().to_csv(out_dir / "brands.csv", index=False)
    popups.to_csv(out_dir / "popups.csv", index=False)
    popup_brands.to_csv(out_dir / "popup_brands.csv", index=False)
    print(f"Wrote {len(popups)} pop-ups, {len(popup_brands)} pop-up brand rows, {len(BRAND)} brands to {out_dir}/")
