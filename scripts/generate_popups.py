"""
generate_popups.py - synthetic RGC-first pop-up history for Pop-up Pick (EAT_HACK).

Reads brand_features.csv (RGC's real client brands, from build_brand_features.py).
Writes two files to an output folder (default: ./out):
  popups.csv        60 past pop-ups (2 a month), one row each, Apr 2024 to Sep 2026
  popup_brands.csv  one row per pop-up and brand: units, reviews, qualified reviews, rating

Brand names are RGC's real clients, but every outcome here is synthetic; event names are generic.
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
# WatchHumans archetypes, built from each user's purchasing data in the app (shared definition)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
from generate_watchhumans_synthetic import ARCHETYPE_PREVALENCE, ARCHETYPES  # noqa: E402
from get_event_archetypes import calculate_event_archetype_scores  # noqa: E402  (keyword method)
EVENT_TYPES = ["community", "concerts", "conferences", "expos", "festivals", "performing_arts", "sports"]
CORE_CATEGORIES = {"drink", "savoury", "sweet", "condiment"}

# ---------------------------------------------------------------- brands (RGC's real clients)
# Read from brand_features.csv, built from RGC's brand sheet by build_brand_features.py.
_bf = pd.read_csv(paths.BRAND_FEATURES)
BRAND = {}
for r in _bf.itertuples():
    targets = [a for a in ARCHETYPES if getattr(r, f"target_{a}") == 1]
    BRAND[r.brand_id] = dict(brand_id=r.brand_id, brand_name=r.brand_name, category=r.category,
                             sub_category=r.sub_category, description=r.description,
                             needs=np.array([getattr(r, f"need_{n}") for n in NEEDS], float),
                             target=np.array([1.0 if a in targets else 0.0 for a in ARCHETYPES]),
                             aff=np.array([getattr(r, f"arch_{a}") for a in ARCHETYPES], float),
                             targets=targets, needs_chilling=r.needs_chilling, frozen=r.frozen, vegan=r.vegan,
                             gluten_free=r.gluten_free, adults_only=r.adults_only,
                             hot_drink=int(r.category == "drink" and r.sheet_category == "Pantry"))
FAVOURITE_FIVE = _bf.loc[_bf["favourite_five"] == 1, "brand_id"].tolist()   # RGC's habit lineup

# ---------------------------------------------------------------- event types
# Seven event categories (PredictHQ-style). Each blends the sub-types listed in its names.
# RGC pops up only at small events: expected attendance under 200.
# needs: same order as NEEDS. The crowd mix by ARCHETYPES is not hand-set: keyword_crowd() scores each type with
# the same keyword method as real events (get_event_archetypes.py), on its PredictHQ category.
EVENT = {
    "sports": dict(needs=[1., .9, .5, .1, .2, .5, .2, .3],
                   footfall=(40, 199), dwell=2, stop=.35, signup=.28, stall=(0, 40), staff=2, indoor=0.3,
                   start=["09:00", "17:00", "19:45"], days=[1, 2, 5, 6],
                   names=["Community 5K finish", "10K race finish", "Half marathon finish",
                          "Football screening", "Rugby screening"],
                   boroughs=["Richmond upon Thames", "Wandsworth", "Greenwich", "Hackney", "Tower Hamlets",
                             "Southwark", "Lambeth", "Hammersmith and Fulham", "Brent", "Kingston upon Thames",
                             "Barnet", "Waltham Forest"]),
    "community": dict(needs=[.3, .2, .2, .1, .9, .7, .7, .5],
                      footfall=(20, 199), dwell=3, stop=.35, signup=.25, stall=(0, 60), staff=1, indoor=0.3,
                      start=["09:00", "11:00"], days=[5, 6],
                      names=["Weekend food market", "Farmers' market", "Run club social", "Family fun day",
                             "Community street party"],
                      boroughs=["Southwark", "Hackney", "Lewisham", "Greenwich", "Camden", "Islington", "Lambeth",
                                "Waltham Forest", "Haringey", "Croydon", "Ealing", "Merton", "Newham",
                                "Richmond upon Thames"]),
    "concerts": dict(needs=[.9, .2, .8, 0., .3, .4, .3, .3],
                     footfall=(60, 199), dwell=4, stop=.20, signup=.15, stall=(40, 120), staff=2, indoor=1.0,
                     start=["19:30"], days=[3, 4, 5],
                     names=["Live gig", "Club night", "DJ night", "Arena concert"],
                     boroughs=["Hackney", "Camden", "Lambeth", "Islington", "Southwark", "Tower Hamlets", "Brent",
                               "Greenwich", "Hammersmith and Fulham"]),
    "conferences": dict(needs=[.4, .1, .9, 1., .4, .3, .4, .6],
                        footfall=(30, 199), dwell=7, stop=.55, signup=.40, stall=(0, 50), staff=1, indoor=1.0,
                        start=["09:30", "10:00"], days=[1, 2, 3, 5, 6],
                        names=["Weekend AI hackathon", "Student hackathon", "Fintech hack day", "Tech conference",
                               "Startup summit"],
                        boroughs=["Islington", "Hackney", "Camden", "Tower Hamlets", "City of London",
                                  "Westminster", "Southwark", "Newham"]),
    "expos": dict(needs=[.2, 0., .6, .4, .8, .3, .5, .9],
                  footfall=(60, 199), dwell=4, stop=.30, signup=.40, stall=(30, 100), staff=2, indoor=0.9,
                  start=["10:00", "11:00"], days=[0, 1, 2, 3, 5],
                  names=["Freshers' fair", "Societies fair", "Food and drink expo", "Lifestyle show"],
                  boroughs=["Camden", "Westminster", "Tower Hamlets", "Kensington and Chelsea", "Southwark",
                            "Islington", "Newham", "Hammersmith and Fulham", "Hillingdon"]),
    "festivals": dict(needs=[1., .3, .6, 0., .7, .6, .7, .3],
                      footfall=(100, 199), dwell=7, stop=.20, signup=.20, stall=(80, 200), staff=2, indoor=0.0,
                      start=["12:00"], days=[5, 6],
                      names=["Summer music festival", "Food and music festival", "Street food festival",
                             "Street festival"],
                      boroughs=["Newham", "Lambeth", "Hackney", "Greenwich", "Haringey", "Tower Hamlets",
                                "Waltham Forest", "Brent", "Barking and Dagenham", "Croydon"]),
    "performing_arts": dict(needs=[.3, 0., .2, .1, .4, .8, .9, .3],
                            footfall=(30, 199), dwell=2.5, stop=.25, signup=.20, stall=(20, 80), staff=1,
                            indoor=0.85, start=["18:30", "19:00"], days=[3, 4, 5],
                            names=["Theatre interval", "Comedy night", "Dance show", "Open-air theatre"],
                            boroughs=["Westminster", "Camden", "Southwark", "Lambeth", "Islington", "Hackney",
                                      "Richmond upon Thames", "Kensington and Chelsea"]),
}
PHQ_CATEGORY = {"performing_arts": "performing-arts"}       # event type -> PredictHQ category
POPULATION_WEIGHT = 0.3     # crowds are 70% the event's keyword profile, 30% the WatchHumans population


def crowd_shares(scores):
    """Keyword archetype scores -> crowd shares: rescale so the top archetype is 1, normalise to sum to 1,
    then blend with the WatchHumans population so no archetype is ever absent."""
    s = np.array([scores[f"{a}_score"] for a in ARCHETYPES], float)
    s = s / s.max() if s.max() > 0 else np.ones(len(ARCHETYPES))
    pop = np.array([ARCHETYPE_PREVALENCE[a] for a in ARCHETYPES], float)
    return (1 - POPULATION_WEIGHT) * s / s.sum() + POPULATION_WEIGHT * pop / pop.sum()


def keyword_crowd(event_type):
    """A typical event of this type, scored on its PredictHQ category alone (the keyword method's category table)."""
    return crowd_shares(calculate_event_archetype_scores({"category": PHQ_CATEGORY.get(event_type, event_type)}))


for t, p in EVENT.items():
    p["needs"] = np.array(p["needs"], float)
    p["mix"] = keyword_crowd(t)

OUTER_BOROUGHS = {"Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Croydon", "Ealing", "Enfield",
                  "Greenwich", "Harrow", "Havering", "Hillingdon", "Hounslow", "Kingston upon Thames", "Merton",
                  "Redbridge", "Richmond upon Thames", "Sutton", "Waltham Forest"}   # ONS Outer London
MONTHLY_HIGH_C = {1: 8, 2: 9, 3: 12, 4: 15, 5: 18, 6: 21, 7: 23, 8: 23, 9: 20, 10: 16, 11: 11, 12: 8}

# RGC's habit: big, busy events, whatever the brand fit
HABIT_EVENT_WEIGHTS = {"community": .25, "festivals": .18, "expos": .15, "sports": .14,
                       "concerts": .10, "performing_arts": .10, "conferences": .08}
FESTIVAL_MONTHS = {5, 6, 7, 8, 9}

# ---------------------------------------------------------------- hidden truth (never written to CSV)
QUALITY = dict(zip(sorted(BRAND), np.random.default_rng(SEED + 1).normal(0, 0.25, len(BRAND))))
# true archetype affinities: the brand sheet's reading plus what only real reviews would reveal
_rng_aff = np.random.default_rng(SEED + 3)
TRUE_AFF = {b: np.clip(BRAND[b]["aff"] + _rng_aff.normal(0, 0.12, len(ARCHETYPES)), 0.05, 1)
            for b in sorted(BRAND)}


def target_share(bid, event_type):
    """Share of the event's crowd inside the brand's target archetypes."""
    return float(EVENT[event_type]["mix"] @ BRAND[bid]["target"])


def _moment_context(bid, event):
    """Hidden moment fit (need states) times practical context, for brand bid at event."""
    b, p = BRAND[bid], EVENT[event["event_type"]]
    cos = float(b["needs"] @ p["needs"] / (np.linalg.norm(b["needs"]) * np.linalg.norm(p["needs"]) + 1e-9))
    f = 0.5 + 0.5 * cos
    outdoor = not event["indoor"]
    if b["needs_chilling"] and outdoor and event["event_type"] in ("sports", "festivals", "community"):
        f *= 0.85
    if outdoor and event["temp_c"] >= 20 and b["needs"][0] >= 0.5:
        f *= 1.15
    if b["frozen"] and event["temp_c"] <= 12:
        f *= 0.6
    if b["adults_only"] and event["event_type"] in ("community", "expos", "conferences"):
        f *= 0.3        # alcohol or CBD at family, student and work events lands badly
    return f


def true_fit(bid, event):
    """Hidden fit between a brand and an event, 0 to 1: how much the expected crowd likes it, in the moment."""
    match = float(EVENT[event["event_type"]]["mix"] @ TRUE_AFF[bid])
    return float(np.clip(_moment_context(bid, event) * (0.2 + 1.2 * match), 0, 1))


def lineup_appeal(lineup, event):
    """People stop when the stall has something their archetype likes: each archetype in the crowd is drawn
    by its favourite product in the lineup."""
    mix = EVENT[event["event_type"]]["mix"]
    per_arch = np.array([_moment_context(b, event) * (0.2 + 1.2 * TRUE_AFF[b]) for b in lineup])
    return float(np.clip(mix @ per_arch.max(0), 0, 1))


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
        q = target_share(bid, event["event_type"])
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
def make_history(n_months=30, per_month=2, first_month=(2024, 4)):   # RGC runs 2 pop-ups a month
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
            # per-event cost once the kit is owned: pitch, insurance £35, consumables £30, staff food £10 each
            stall = min(max(stall, 30), 150)
            staff_cost = p["staff"] * 10
            travel = 35 if borough in OUTER_BOROUGHS else 20
            total = stall + 35 + 30 + staff_cost + travel
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


if __name__ == "__main__":
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else paths.SYNTHETIC
    out_dir.mkdir(parents=True, exist_ok=True)
    popups, popup_brands = make_history()
    popups.to_csv(out_dir / "popups.csv", index=False)
    popup_brands.to_csv(out_dir / "popup_brands.csv", index=False)
    print(f"Wrote {len(popups)} pop-ups, {len(popup_brands)} pop-up brand rows, {len(BRAND)} brands to {out_dir}/")
