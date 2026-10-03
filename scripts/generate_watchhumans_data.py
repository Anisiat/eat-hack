"""
generate_watchhumans_data.py - synthetic WatchHumans users and reviews for Pop-up Pick (EAT_HACK).

Reads (from the output folder): popups.csv, popup_brands.csv
Reads: data/raw/borough_census_2021.csv  (run get_borough_census.py first)
Writes three files to the output folder (default: repo root):
  users.csv     5,000 WatchHumans users: borough, segment, traits, category affinities, diet, sign-up source
  reviews.csv   about 20,000 reviews; pop-up reviews reconcile exactly with popup_brands.csv
  boroughs.csv  33 London boroughs: real Census 2021 population and 18-34 share, plus WatchHumans users

Segments match the brand targets in brand_features.csv. A review is qualified when the reviewer's primary
segment is one of the brand's target segments. Hidden truth (brand quality) comes from
generate_popups.py and is never written out.

Run:  python scripts/generate_watchhumans_data.py [output_folder]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_popups import BRAND, EVENT, QUALITY, SEGMENTS  # noqa: E402

SEED = 42
N_USERS = 5000
N_REVIEWS = 20000
ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "data" / "raw" / "borough_census_2021.csv"
PERIOD = (pd.Timestamp("2024-04-01"), pd.Timestamp("2026-09-30"))
CATEGORIES = ["drink", "savoury", "sweet", "condiment", "functional", "other"]
DIETS = ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_allergy"]

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- segment profiles
# age: (mean, sd, low, high); traits and category affinities: expected values 0 to 1
SEGMENT_PROFILE = {
    "students": dict(
        age=(21, 2.5, 18, 26),
        traits=dict(health_consciousness=.45, novelty_seeking=.75, social_influence=.80, price_sensitivity=.90,
                    convenience_orientation=.70, sustainability_orientation=.55),
        affinity=dict(drink=.70, savoury=.75, sweet=.75, condiment=.45, functional=.55, other=.40),
        diet_mult=1.2),
    "young_professionals": dict(
        age=(29, 4, 22, 40),
        traits=dict(health_consciousness=.60, novelty_seeking=.70, social_influence=.65, price_sensitivity=.45,
                    convenience_orientation=.85, sustainability_orientation=.60),
        affinity=dict(drink=.75, savoury=.65, sweet=.55, condiment=.60, functional=.65, other=.40),
        diet_mult=1.2),
    "fitness": dict(
        age=(31, 6, 19, 50),
        traits=dict(health_consciousness=.90, novelty_seeking=.50, social_influence=.55, price_sensitivity=.50,
                    convenience_orientation=.65, sustainability_orientation=.60),
        affinity=dict(drink=.70, savoury=.40, sweet=.30, condiment=.35, functional=.90, other=.40),
        diet_mult=1.6),
    "families": dict(
        age=(38, 5, 27, 55),
        traits=dict(health_consciousness=.65, novelty_seeking=.35, social_influence=.40, price_sensitivity=.70,
                    convenience_orientation=.75, sustainability_orientation=.55),
        affinity=dict(drink=.50, savoury=.60, sweet=.75, condiment=.50, functional=.35, other=.40),
        diet_mult=0.9),
    "foodies": dict(
        age=(33, 7, 21, 55),
        traits=dict(health_consciousness=.60, novelty_seeking=.90, social_influence=.60, price_sensitivity=.30,
                    convenience_orientation=.35, sustainability_orientation=.75),
        affinity=dict(drink=.65, savoury=.70, sweet=.60, condiment=.95, functional=.40, other=.40),
        diet_mult=1.5),
}
TRAITS = list(SEGMENT_PROFILE["students"]["traits"])
DIET_BASE = dict(vegetarian=.08, vegan=.04, gluten_free=.05, dairy_free=.06, nut_allergy=.02)

# what reviewers like or dislike, by brand category
ATTRIBUTES = {
    "drink": ["taste", "fizz", "sweetness", "refreshing", "aftertaste", "price", "packaging"],
    "savoury": ["crunch", "seasoning", "saltiness", "portion size", "price", "packaging"],
    "sweet": ["taste", "sweetness", "texture", "ingredients", "price", "packaging"],
    "condiment": ["heat", "flavour depth", "versatility", "texture", "price", "jar size"],
    "functional": ["taste", "texture", "ingredients", "energy boost", "price", "portability"],
    "other": ["design", "build quality", "size", "usefulness", "price"],
    "hot_drink": ["taste", "aroma", "strength", "ingredients", "price", "packaging"],
}


def clip01(x):
    return np.clip(x, 0, 1)


def age_band(age):
    return "18-24" if age < 25 else "25-34" if age < 35 else "35-44" if age < 45 else "45+"


# ---------------------------------------------------------------- users
def make_person(segment, borough, source, signup_date):
    prof = SEGMENT_PROFILE[segment]
    m, sd, lo, hi = prof["age"]
    age = int(np.clip(round(rng.normal(m, sd)), lo, hi))
    scores = {s: float(clip01(rng.normal(.30, .15))) for s in SEGMENTS}
    scores[segment] = float(clip01(rng.normal(.85, .08)))
    others = sorted((s for s in SEGMENTS if s != segment), key=scores.get, reverse=True)
    if scores[others[0]] >= scores[segment]:          # primary always has the top score
        scores[others[0]] = scores[segment] - .05
    diet = [d for d in DIETS if rng.random() < DIET_BASE[d] * prof["diet_mult"]]
    if "vegan" in diet and "vegetarian" in diet:
        diet.remove("vegetarian")
    row = dict(age=age, age_band=age_band(age), borough=borough, segment=segment, secondary_segment=others[0])
    row.update({f"{s}_score": round(scores[s], 3) for s in SEGMENTS})
    row.update({t: round(float(clip01(rng.normal(v, .10))), 3) for t, v in prof["traits"].items()})
    row.update({f"{c}_affinity": round(float(clip01(rng.normal(v, .12))), 3) for c, v in prof["affinity"].items()})
    row.update(dietary_needs="|".join(diet) if diet else "none", signup_source=source,
               signup_date=signup_date)
    return row


def popup_segments(n, mix, needs):
    """Segments for one pop-up's n sign-ups, drawn from the event mix, repaired until every brand's
    review and qualified-review counts are feasible.  needs: list of (target_set, reviews, qualified)."""
    def violation(seg):
        v = 0
        for tgt, r, q in needs:
            inside = sum(s in tgt for s in seg)
            v += max(0, q - inside) + max(0, (r - q) - (n - inside))
        return v

    seg = list(rng.choice(SEGMENTS, n, p=mix))
    for _ in range(200):
        if violation(seg) == 0:
            return seg
        seg = list(rng.choice(SEGMENTS, n, p=mix))
    # local repair: flip single users while it lowers the violation
    best = violation(seg)
    while best:
        i, s = int(rng.integers(n)), SEGMENTS[rng.integers(len(SEGMENTS))]
        old, seg[i] = seg[i], s
        v = violation(seg)
        if v <= best:
            best = v
        else:
            seg[i] = old
    return seg


def make_users(popups, popup_brands, census):
    boroughs = census["borough"].tolist()
    w_any = census["pop_18_34"].to_numpy(float)
    w_any /= w_any.sum()
    w_org = census["pop_18_34"].to_numpy(float) * np.where(census["inner_outer"] == "inner", 1.5, 1.0)
    w_org /= w_org.sum()

    users, popup_members = [], {}
    for p in popups.itertuples():
        n = int(p.signups)
        rows = popup_brands[popup_brands["popup_id"] == p.popup_id]
        needs = [(set(BRAND[r.brand_id]["targets"]), int(r.reviews), int(r.qualified_reviews))
                 for r in rows.itertuples()]
        segs = popup_segments(n, EVENT[p.event_type]["mix"], needs)
        members = []
        for s in segs:
            b = p.borough if rng.random() < .5 else boroughs[rng.choice(len(boroughs), p=w_any)]
            members.append(len(users))
            users.append(make_person(s, b, p.popup_id, p.date))
        popup_members[p.popup_id] = members

    n_organic = N_USERS - len(users)
    assert n_organic > 0, "more pop-up sign-ups than users"
    org_mix = np.array([.20, .35, .15, .12, .18])
    days = (PERIOD[1] - PERIOD[0]).days
    for _ in range(n_organic):
        s = SEGMENTS[rng.choice(len(SEGMENTS), p=org_mix)]
        b = boroughs[rng.choice(len(boroughs), p=w_org)]
        d = (PERIOD[0] + pd.Timedelta(days=int(rng.integers(days + 1)))).date().isoformat()
        users.append(make_person(s, b, "organic", d))

    df = pd.DataFrame(users)
    # ids in sign-up order
    order = df.sort_values(["signup_date", "signup_source"], kind="stable").index
    new_id = {old: f"H{i + 1:05d}" for i, old in enumerate(order)}
    df.insert(0, "user_id", df.index.map(new_id))
    df = df.loc[order].reset_index(drop=True)
    popup_members = {k: [new_id[i] for i in v] for k, v in popup_members.items()}
    return df, popup_members


# ---------------------------------------------------------------- reviews
def attributes(category, rating):
    opts = ATTRIBUTES[category]
    liked = disliked = ""
    if rating >= 4:
        liked = rng.choice(opts)
        if rng.random() < .2:
            disliked = rng.choice([o for o in opts if o != liked])
    elif rating <= 2:
        disliked = rng.choice(opts)
        if rng.random() < .2:
            liked = rng.choice([o for o in opts if o != disliked])
    else:
        if rng.random() < .5:
            liked = rng.choice(opts)
        else:
            disliked = rng.choice(opts)
    return liked, disliked


def would_buy(rating, price_sensitivity):
    z = 1.6 * (rating - 3.3) - 1.2 * (price_sensitivity - .5)
    return int(rng.random() < 1 / (1 + np.exp(-z)))


def ratings_with_mean(n, mean):
    """n integer ratings 1-5 whose sum is round(mean * n)."""
    r = np.clip(np.round(rng.normal(mean, .8, n)), 1, 5).astype(int)
    target = int(np.clip(round(mean * n), n, 5 * n))
    while r.sum() != target:
        if r.sum() < target:
            idx = np.flatnonzero(r < 5)
            r[rng.choice(idx)] += 1
        else:
            idx = np.flatnonzero(r > 1)
            r[rng.choice(idx)] -= 1
    return r


def make_reviews(users, popups, popup_brands, popup_members):
    u = users.set_index("user_id")
    pdate = popups.set_index("popup_id")["date"]
    rows = []
    for r in popup_brands.itertuples():
        n_rev, n_q = int(r.reviews), int(r.qualified_reviews)
        if n_rev == 0:
            continue
        b = BRAND[r.brand_id]
        members = popup_members[r.popup_id]
        inside = [m for m in members if u.at[m, "segment"] in b["targets"]]
        outside = [m for m in members if u.at[m, "segment"] not in b["targets"]]
        chosen = (list(rng.choice(inside, n_q, replace=False)) +
                  list(rng.choice(outside, n_rev - n_q, replace=False)))
        for uid, rating in zip(chosen, ratings_with_mean(n_rev, r.avg_rating)):
            d = pd.Timestamp(pdate[r.popup_id]) + pd.Timedelta(days=int(rng.integers(0, 8)))
            rows.append(review_row(uid, r.brand_id, r.popup_id, d, int(rating), u.at[uid, "price_sensitivity"]))

    # organic reviews: anyone, any brand, after sign-up
    seen = {(x["user_id"], x["brand_id"]) for x in rows}
    bids = sorted(BRAND)
    target = np.array([BRAND[b]["target"] for b in bids])                     # brands x segments
    cat_idx = [CATEGORIES.index(BRAND[b]["category"]) for b in bids]
    seg_scores = users[[f"{s}_score" for s in SEGMENTS]].to_numpy()
    affinity = users[[f"{c}_affinity" for c in CATEGORIES]].to_numpy()
    activity = .5 + users["social_influence"].to_numpy() + users["novelty_seeking"].to_numpy()
    activity *= (PERIOD[1] - pd.to_datetime(users["signup_date"])).dt.days.to_numpy() + 14
    activity /= activity.sum()
    seg_of = users["segment"].to_numpy()
    sec_of = users["secondary_segment"].to_numpy()
    uids = users["user_id"].to_numpy()
    signup = pd.to_datetime(users["signup_date"]).to_numpy()

    while len(rows) < N_REVIEWS:
        i = rng.choice(len(users), p=activity)
        pref = np.exp(2.0 * (seg_scores[i] @ target.T) / np.maximum(target.sum(1), 1) + 1.5 * affinity[i][cat_idx])
        j = rng.choice(len(bids), p=pref / pref.sum())
        bid = bids[j]
        if (uids[i], bid) in seen:
            continue
        seen.add((uids[i], bid))
        tg = BRAND[bid]["targets"]
        seg_fit = 1.0 if seg_of[i] in tg else .5 if sec_of[i] in tg else 0.0
        mean = 2.8 + 1.4 * seg_fit + .8 * (affinity[i][cat_idx[j]] - .5) + QUALITY[bid]
        rating = int(np.clip(round(rng.normal(mean, .8)), 1, 5))
        start = pd.Timestamp(signup[i])
        d = start + pd.Timedelta(days=int(rng.integers(0, (PERIOD[1] - start).days + 1)))
        rows.append(review_row(uids[i], bid, "", d, rating, users.at[i, "price_sensitivity"]))

    df = pd.DataFrame(rows).sort_values(["review_date", "user_id"], kind="stable").reset_index(drop=True)
    df.insert(0, "review_id", [f"R{i + 1:05d}" for i in range(len(df))])
    seg = users.set_index("user_id")["segment"]
    df["in_target_segment"] = [int(seg[x] in BRAND[b]["targets"]) for x, b in zip(df["user_id"], df["brand_id"])]
    return df


def review_row(uid, bid, popup_id, date, rating, price_sensitivity):
    b = BRAND[bid]
    liked, disliked = attributes("hot_drink" if b["hot_drink"] else b["category"], rating)
    return dict(user_id=uid, brand_id=bid, popup_id=popup_id, review_date=date.date().isoformat(),
                rating=rating, would_buy=would_buy(rating, price_sensitivity),
                liked_attribute=liked, disliked_attribute=disliked)


# ---------------------------------------------------------------- boroughs
def make_boroughs(census, users):
    counts = users["borough"].value_counts()
    df = census.copy()
    df["watchhumans_users"] = df["borough"].map(counts).fillna(0).astype(int)
    df["watchhumans_users_per_1000"] = (1000 * df["watchhumans_users"] / df["population_2021"]).round(3)
    df["source"] = "census_2021; watchhumans_users synthetic"
    return df


# ---------------------------------------------------------------- checks
def check(users, reviews, boroughs, popups, popup_brands):
    assert len(users) == N_USERS and users["user_id"].is_unique
    assert len(boroughs) == 33 and set(users["borough"]) <= set(boroughs["borough"])
    assert boroughs["watchhumans_users"].sum() == N_USERS
    per_popup = users[users["signup_source"] != "organic"]["signup_source"].value_counts()
    assert (per_popup.reindex(popups["popup_id"]).fillna(0).astype(int).values == popups["signups"].values).all()
    pr = reviews[reviews["popup_id"] != ""].groupby(["popup_id", "brand_id"]).agg(
        reviews=("rating", "size"), qualified_reviews=("in_target_segment", "sum"), mean=("rating", "mean"))
    pb = popup_brands[popup_brands["reviews"] > 0].set_index(["popup_id", "brand_id"])
    pr = pr.reindex(pb.index)
    assert (pr["reviews"] == pb["reviews"]).all() and (pr["qualified_reviews"] == pb["qualified_reviews"]).all()
    assert ((pr["mean"] - pb["avg_rating"]).abs() <= np.maximum(.05, .5 / pb["reviews"]) + 1e-9).all()
    assert not reviews.duplicated(["user_id", "brand_id"]).any()
    signup = users.set_index("user_id")["signup_date"]
    assert (reviews["review_date"].values >= signup[reviews["user_id"]].values).all()


if __name__ == "__main__":
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT)
    popups = pd.read_csv(out_dir / "popups.csv")
    popup_brands = pd.read_csv(out_dir / "popup_brands.csv")
    census = pd.read_csv(CENSUS)

    users, members = make_users(popups, popup_brands, census)
    reviews = make_reviews(users, popups, popup_brands, members)
    boroughs = make_boroughs(census, users)
    check(users, reviews, boroughs, popups, popup_brands)

    users.to_csv(out_dir / "users.csv", index=False)
    reviews.to_csv(out_dir / "reviews.csv", index=False)
    boroughs.to_csv(out_dir / "boroughs.csv", index=False)
    print(f"Wrote {len(users)} users ({(users['signup_source'] != 'organic').sum()} from pop-ups), "
          f"{len(reviews)} reviews ({(reviews['popup_id'] != '').sum()} at pop-ups), "
          f"{len(boroughs)} boroughs to {out_dir}/")
