"""Load and check every input table. The model reads only these CSVs, never the generators."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

NEEDS = ["hydrate", "recover", "energy", "focus", "discovery", "sharing", "treat", "value"]
SEGMENTS = ["students", "young_professionals", "fitness", "families", "foodies"]
CORE_CATEGORIES = {"drink", "savoury", "sweet", "condiment"}
STAFF_RATE_GBP = 16.0       # same loaded hourly rate as the pop-up cost columns

REQUIRED = {
    "brand_features": ["brand_id", "brand_name", "category", "sub_category", "description", "needs_chilling",
                       "frozen", "vegan", "gluten_free", "adults_only", "favourite_five", "units_available_per_month"]
              + [f"need_{n}" for n in NEEDS] + [f"target_{s}" for s in SEGMENTS],
    "brand_products": ["product_id", "brand_id", "product", "flavour", "format", "claims", "label_link"]
                      + [f"need_{n}" for n in NEEDS],
    "popups": ["popup_id", "date", "event_type", "borough", "indoor", "dwell_hours", "footfall", "lineup", "staff",
               "stops", "signups", "reviews", "qualified_reviews", "stall_fee_gbp", "total_cost_gbp", "split"],
    "popup_brands": ["popup_id", "brand_id", "reviews", "qualified_reviews"],
    "users": ["user_id", "segment", "borough", "signup_source"],
    "reviews": ["user_id", "brand_id", "popup_id", "rating", "liked_attribute", "disliked_attribute"],
    "boroughs": ["borough", "inner_outer", "watchhumans_users_per_1000"],
    "event_types": ["event_type", "peak_slot", "moment", "dwell_hours", "staff", "indoor_share"]
                   + [f"need_{n}" for n in NEEDS] + [f"mix_{s}" for s in SEGMENTS],
    "events": ["event_id", "name", "event_type", "start", "end", "venue", "borough", "expected_attendance",
               "indoor", "audience_tags", "stall_cost_gbp"],
}


def load(root=ROOT):
    d = {name: pd.read_csv(root / f"{name}.csv") for name in REQUIRED}
    for name, cols in REQUIRED.items():
        missing = set(cols) - set(d[name].columns)
        assert not missing, f"{name}.csv is missing columns: {sorted(missing)}"
    d["reviews"]["popup_id"] = d["reviews"]["popup_id"].fillna("")
    d["brands"] = d.pop("brand_features").set_index("brand_id", drop=False)
    d["products"] = d.pop("brand_products").fillna("")
    d["event_types"] = d["event_types"].set_index("event_type", drop=False)
    unknown = set(d["events"]["event_type"]) - set(d["event_types"].index)
    assert not unknown, f"events.csv has unknown event types: {unknown}"
    return d


def best_products(d, event_types):
    """For each event type, each brand's product whose need states best match the type: {type: {brand_id: row}}."""
    pr = d["products"]
    pn = pr[[f"need_{n}" for n in NEEDS]].to_numpy(float)
    out = {}
    for t in event_types:
        ne = d["event_types"].loc[t, [f"need_{n}" for n in NEEDS]].to_numpy(float)
        cos = pn @ ne / (np.linalg.norm(pn, axis=1) * np.linalg.norm(ne) + 1e-9)
        best = pr.assign(_cos=cos).sort_values("_cos", ascending=False).drop_duplicates("brand_id")
        out[t] = {r["brand_id"]: r for _, r in best.iterrows()}
    return out


def event_cost(stall, staff, dwell, borough, outer):
    """Stall fee + staff time (dwell plus 2 hours set-up) + travel; matches popups.csv cost columns."""
    return stall + staff * (dwell + 2) * STAFF_RATE_GBP + 40 + (20 if borough in outer else 0)


def upcoming_events(d):
    """events.csv as model-ready rows: footfall, dwell, staff, month, cost."""
    et = d["event_types"]
    outer = set(d["boroughs"].query("inner_outer == 'outer'")["borough"])
    ev = d["events"].copy()
    ev["start"] = pd.to_datetime(ev["start"])
    ev["end"] = pd.to_datetime(ev["end"])
    ev["date"] = ev["start"].dt.date.astype(str)
    ev["month"] = ev["start"].dt.month
    ev["footfall"] = ev["expected_attendance"].astype(float)
    ev["dwell_hours"] = ((ev["end"] - ev["start"]).dt.total_seconds() / 3600).fillna(
        ev["event_type"].map(et["dwell_hours"]))
    ev["staff"] = ev["event_type"].map(et["staff"])
    ev["audience_tags"] = ev["audience_tags"].fillna("")
    ev["cost"] = [event_cost(r.stall_cost_gbp, r.staff, r.dwell_hours, r.borough, outer) for r in ev.itertuples()]
    return ev.set_index("event_id", drop=False)


def past_events(d):
    """popups.csv in the same shape as upcoming_events, for training and the uplift test."""
    p = d["popups"].copy()
    p["event_id"] = p["popup_id"]
    p["month"] = pd.to_datetime(p["date"]).dt.month
    p["audience_tags"] = ""
    p["cost"] = p["total_cost_gbp"]
    p["name"] = p.get("event_name", p["popup_id"])
    return p.set_index("event_id", drop=False)


def brand_matrices(brands):
    needs = brands[[f"need_{n}" for n in NEEDS]].to_numpy(float)
    target = brands[[f"target_{s}" for s in SEGMENTS]].to_numpy(float)
    return needs, target


def pct(x):
    return f"{100 * x:.0f}%"


def nice(s):
    return str(s).replace("_", " ")


def as_int(x):
    return int(np.round(x))
