"""Load and check every input table. The model reads only these CSVs, never the generators."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

NEEDS = ["hydrate", "recover", "energy", "focus", "discovery", "sharing", "treat", "value"]
# Same list as scripts/generate_watchhumans_synthetic.py; load() checks it against brand_features.csv.
ARCHETYPES = ["wellness_seeker", "trend_enthusiast", "thoughtful_buyer", "smart_saver", "quality_seeker",
              "on_the_go_shopper", "impulse_buyer", "experience_explorer", "everyday_planner", "conscious_consumer"]
CORE_CATEGORIES = {"drink", "savoury", "sweet", "condiment"}

REQUIRED = {
    "brand_features": ["brand_id", "brand_name", "category", "sub_category", "description", "needs_chilling",
                       "frozen", "vegan", "gluten_free", "adults_only", "favourite_five", "units_available_per_month"]
              + [f"need_{n}" for n in NEEDS] + [f"arch_{a}" for a in ARCHETYPES] + [f"target_{a}" for a in ARCHETYPES],
    "brand_products": ["product_id", "brand_id", "product", "flavour", "format", "claims", "label_link"]
                      + [f"need_{n}" for n in NEEDS] + [f"arch_{a}" for a in ARCHETYPES],
    "popups": ["popup_id", "date", "event_type", "indoor", "dwell_hours", "footfall", "lineup", "staff",
               "stops", "signups", "reviews", "stall_fee_gbp", "travel_gbp", "split"],
    "popup_brands": ["popup_id", "brand_id", "reviews"],
    "users": ["user_id", "primary_archetype", "signup_source"],
    "reviews": ["user_id", "brand_id", "popup_id", "review_date", "rating", "liked_attribute", "disliked_attribute"],
    "event_types": ["event_type", "peak_slot", "moment", "dwell_hours", "staff", "indoor_share"]
                   + [f"need_{n}" for n in NEEDS] + [f"mix_{a}" for a in ARCHETYPES],
}
DATA = ROOT / "data"
EVENTS_PATH = DATA / "archetypes" / "events_archetypes.csv"        # real UK events (PredictHQ), keyword-scored
ASSUMPTIONS_PATH = DATA / "assumptions" / "value_assumptions.csv"
# where each input table lives (the model reads CSVs only; scripts/paths.py lists the same locations)
TABLE_PATHS = {
    "brand_features": DATA / "processed" / "brand_features.csv",
    "brand_products": DATA / "processed" / "brand_products.csv",
    "event_types": DATA / "processed" / "event_types.csv",
    "popups": DATA / "synthetic" / "popups.csv",
    "popup_brands": DATA / "synthetic" / "popup_brands.csv",
    "users": DATA / "synthetic" / "users.csv",
    "reviews": DATA / "synthetic" / "reviews.csv",
}
EVENT_COLUMNS = ["event_id", "title", "category", "start_local", "end_local", "latitude", "longitude",
                 "phq_attendance"] + [f"{a}_score" for a in ARCHETYPES]
CATEGORY_TO_TYPE = {"performing-arts": "performing_arts"}                    # PredictHQ category -> event type
LONDON_CENTRE = (51.5074, -0.1278)
POPULATION_WEIGHT = 0.3     # crowd = 70% the event's keyword profile + 30% the WatchHumans population
FAMILY = re.compile(r"\b(family|families|kids?|children|pantomime|panto)\b", re.I)


def load():
    d = {name: pd.read_csv(TABLE_PATHS[name]) for name in REQUIRED}
    d["events"] = pd.read_csv(EVENTS_PATH)
    missing = set(EVENT_COLUMNS) - set(d["events"].columns)
    assert not missing, f"events_archetypes.csv is missing columns: {sorted(missing)}"
    d["events"]["event_type"] = d["events"]["category"].replace(CATEGORY_TO_TYPE)
    for name, cols in REQUIRED.items():
        missing = set(cols) - set(d[name].columns)
        assert not missing, f"{name}.csv is missing columns: {sorted(missing)}"
    d["reviews"]["popup_id"] = d["reviews"]["popup_id"].fillna("")
    found = [c[len("arch_"):] for c in d["brand_features"].columns if c.startswith("arch_")]
    assert found == ARCHETYPES, f"archetypes in brand_features.csv {found} differ from the model's {ARCHETYPES}"
    d["brands"] = d.pop("brand_features").set_index("brand_id", drop=False)
    d["products"] = d.pop("brand_products").fillna("")
    d["event_types"] = d["event_types"].set_index("event_type", drop=False)
    unknown = set(d["events"]["event_type"]) - set(d["event_types"].index)
    assert not unknown, f"events_archetypes.csv has categories with no event type: {unknown}"
    return d


def load_assumptions():
    a = pd.read_csv(ASSUMPTIONS_PATH)
    return dict(zip(a["key"], a["value"].astype(float)))


def event_cost(stall, staff, dwell, transport, A):
    """Per-event cost once RGC owns the basic kit: pitch fee + insurance + consumables + transport and parking
    + food for the staff (+ staff wages if staff_hourly_cost_gbp > 0). Typically £95-290 for a half day."""
    pitch = min(max(stall, A["pitch_fee_min_gbp"]), A["pitch_fee_max_gbp"])
    wages = staff * (dwell + 2) * A["staff_hourly_cost_gbp"]          # dwell plus 2 hours set-up
    return pitch + A["insurance_gbp"] + A["consumables_gbp"] + transport + staff * A["staff_food_gbp"] + wages


def km_from_london(lat, lon):
    """Great-circle distance from central London, in km."""
    la1, lo1, la2, lo2 = map(np.radians, (LONDON_CENTRE[0], LONDON_CENTRE[1], lat, lon))
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(h))


def upcoming_events(d):
    """Real UK events (events_archetypes.csv) as model-ready rows: crowd archetype shares, footfall, dwell,
    staff, month, cost."""
    et = d["event_types"]
    A = load_assumptions()
    ev = d["events"].copy()
    ev = ev[ev["phq_attendance"] < A["max_attendance"]].copy()      # RGC pops up only at small events
    ev["name"] = ev["title"]
    ev["start"] = pd.to_datetime(ev["start_local"])
    ev["end"] = pd.to_datetime(ev["end_local"])
    ev["date"] = ev["start"].dt.date.astype(str)
    ev["month"] = ev["start"].dt.month
    ev["footfall"] = ev["phq_attendance"].astype(float)
    hours = (ev["end"] - ev["start"]).dt.total_seconds() / 3600
    typical = ev["event_type"].map(et["dwell_hours"])
    ev["dwell_hours"] = hours.where(hours > 0, typical)               # listings without a duration
    ev["end"] = ev["start"] + pd.to_timedelta(ev["dwell_hours"], unit="h")
    ev["staff"] = ev["event_type"].map(et["staff"])
    ev["indoor"] = (ev["event_type"].map(et["indoor_share"]) >= 0.5).astype(int)
    ev["audience_tags"] = ""
    ev["family_event"] = [bool(FAMILY.search(str(t))) and "adult" not in str(t).lower() for t in ev["title"]]
    ev["km_from_london"] = km_from_london(ev["latitude"].to_numpy(float), ev["longitude"].to_numpy(float)).round(1)
    # crowd: the event's keyword archetype scores, rescaled (top archetype = 1), made into shares, then blended
    # 70/30 with the WatchHumans population (organic sign-ups), the same rule used for event types
    sc = ev[[f"{a}_score" for a in ARCHETYPES]].to_numpy(float)
    sc = sc / np.where(sc.max(1, keepdims=True) > 0, sc.max(1, keepdims=True), 1)
    shares = sc / np.where(sc.sum(1, keepdims=True) > 0, sc.sum(1, keepdims=True), 1)
    organic = d["users"].loc[d["users"]["signup_source"] == "organic", "primary_archetype"]
    population = organic.value_counts(normalize=True).reindex(ARCHETYPES, fill_value=0).to_numpy()
    shares = (1 - POPULATION_WEIGHT) * shares + POPULATION_WEIGHT * population
    for k, a in enumerate(ARCHETYPES):
        ev[f"crowd_{a}"] = shares[:, k]
    transport = A["transport_base_gbp"] + A["transport_per_km_gbp"] * ev["km_from_london"]
    ev["cost"] = [event_cost(A["pitch_fee_default_gbp"], r.staff, r.dwell_hours, t, A)
                  for r, t in zip(ev.itertuples(), transport)]
    return ev.set_index("event_id", drop=False)


def past_events(d):
    """popups.csv in the same shape as upcoming_events, for training and the uplift test."""
    p = d["popups"].copy()
    p["event_id"] = p["popup_id"]
    p["month"] = pd.to_datetime(p["date"]).dt.month
    p["audience_tags"] = ""
    A = load_assumptions()
    p["cost"] = [event_cost(r.stall_fee_gbp, r.staff, r.dwell_hours, r.travel_gbp, A) for r in p.itertuples()]
    p["family_event"] = False
    p["name"] = p.get("event_name", p["popup_id"])
    return p.set_index("event_id", drop=False)


def pct(x):
    return f"{100 * x:.0f}%"


def nice(s):
    return str(s).replace("_", " ")


def as_int(x):
    return int(np.round(x))
