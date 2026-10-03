"""
generate_watchhumans_data.py - synthetic WatchHumans users and reviews for Pop-up Pick (EAT_HACK).

Reads (from the output folder): popups.csv, popup_brands.csv
Writes two files to the output folder (default: repo root):
  users.csv     5,000 WatchHumans users: archetype scores, 10 traits, 10 category affinities, diet,
                sign-up source (archetype definitions shared with generate_watchhumans_synthetic.py)
  reviews.csv   about 20,000 reviews; pop-up reviews reconcile exactly with popup_brands.csv

Each user has a primary archetype (one of the 10 WatchHumans archetypes) and a score on all 10. Pop-up
reviews match popup_brands.csv on count and average rating; in_target_archetype is informational only. Hidden truth (brand
quality, true archetype affinities) comes from generate_popups.py and is never written out.

Run:  python scripts/generate_watchhumans_data.py [output_folder]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
from generate_popups import BRAND, EVENT, QUALITY, TRUE_AFF  # noqa: E402
from build_brand_features import ROLE_TO_PROFILE  # noqa: E402  (brand role -> WatchHumans category)
from generate_watchhumans_synthetic import (  # noqa: E402
    ARCHETYPE_PREVALENCE, ARCHETYPE_TRAITS, ARCHETYPES,
    generate_archetype_scores, generate_category_affinities, generate_trait_scores)

SEGMENTS = ARCHETYPES      # users' primary archetype plays the role a segment used to

SEED = 42
N_USERS = 5000
N_REVIEWS = 20000
PERIOD = (pd.Timestamp("2024-04-01"), pd.Timestamp("2026-09-30"))
CATEGORIES = ["drink", "savoury", "sweet", "condiment", "functional", "other"]   # brand lineup roles
DIETS = ["vegetarian", "vegan", "gluten_free", "dairy_free", "nut_allergy"]

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- shared WatchHumans definitions
# Archetypes, prevalence, the 10 behavioural traits and the category profiles all come from
# generate_watchhumans_synthetic.py: the single source of truth for what a WatchHumans user is.
TRAITS = list(next(iter(ARCHETYPE_TRAITS.values())))
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


def age_band(age):
    return "18-24" if age < 25 else "25-34" if age < 35 else "35-44" if age < 45 else "45+"


# ---------------------------------------------------------------- users
def make_person(primary, source, signup_date):
    """One WatchHumans user, built exactly as generate_watchhumans_synthetic.py builds them, except that the
    primary archetype is fixed (pop-up sign-ups are drawn from the event's crowd)."""
    scores = generate_archetype_scores(primary, rng)
    top = max(scores, key=scores.get)
    if top != primary:                                   # keep the drawn primary on top
        scores[primary], scores[top] = scores[top], scores[primary]
    secondary = max((a for a in ARCHETYPES if a != primary), key=scores.get)
    traits = generate_trait_scores(scores, rng)
    affinities = generate_category_affinities(scores, rng)
    age = int(np.clip(rng.normal(29, 7), 18, 55))
    # dietary needs rise with health and sustainability orientation (pipeline addition)
    mult = 0.4 + traits["health_consciousness"] + 0.6 * traits["sustainability_orientation"]
    diet = [d for d in DIETS if rng.random() < DIET_BASE[d] * mult]
    if "vegan" in diet and "vegetarian" in diet:
        diet.remove("vegetarian")
    row = dict(age=age, age_band=age_band(age), primary_archetype=primary,
               secondary_archetype=secondary)
    row.update({f"{a}_score": round(scores[a], 3) for a in ARCHETYPES})
    row.update({t: round(v, 3) for t, v in traits.items()})
    row.update({f"{c}_affinity": round(v, 3) for c, v in affinities.items()})
    row.update(dietary_needs="|".join(diet) if diet else "none", signup_source=source,
               signup_date=signup_date)
    return row


def popup_segments(n, mix):
    """Primary archetypes for one pop-up's n sign-ups, drawn from the event's expected crowd."""
    return list(rng.choice(SEGMENTS, n, p=mix))


def make_users(popups, popup_brands):
    users, popup_members = [], {}
    for p in popups.itertuples():
        n = int(p.signups)
        segs = popup_segments(n, EVENT[p.event_type]["mix"])
        members = []
        for s in segs:
            members.append(len(users))
            users.append(make_person(s, p.popup_id, p.date))
        popup_members[p.popup_id] = members

    n_organic = N_USERS - len(users)
    assert n_organic > 0, "more pop-up sign-ups than users"
    org_mix = np.array([ARCHETYPE_PREVALENCE[a] for a in ARCHETYPES])
    days = (PERIOD[1] - PERIOD[0]).days
    for _ in range(n_organic):
        s = SEGMENTS[rng.choice(len(SEGMENTS), p=org_mix)]
        d = (PERIOD[0] + pd.Timedelta(days=int(rng.integers(days + 1)))).date().isoformat()
        users.append(make_person(s, "organic", d))

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
        n_rev = int(r.reviews)
        if n_rev == 0:
            continue
        members = popup_members[r.popup_id]
        chosen = list(rng.choice(members, n_rev, replace=False))     # any of the pop-up's sign-ups
        for uid, rating in zip(chosen, ratings_with_mean(n_rev, r.avg_rating)):
            d = pd.Timestamp(pdate[r.popup_id]) + pd.Timedelta(days=int(rng.integers(0, 8)))
            rows.append(review_row(uid, r.brand_id, r.popup_id, d, int(rating), u.at[uid, "price_sensitivity"]))

    # organic reviews: anyone, any brand, after sign-up
    seen = {(x["user_id"], x["brand_id"]) for x in rows}
    bids = sorted(BRAND)
    true_aff = np.array([TRUE_AFF[b] for b in bids])                          # brands x archetypes (hidden)
    cat_idx = [CATEGORIES.index(BRAND[b]["category"]) for b in bids]
    seg_scores = users[[f"{s}_score" for s in SEGMENTS]].to_numpy()
    affinity = users[[f"{ROLE_TO_PROFILE[c]}_affinity" for c in CATEGORIES]].to_numpy()   # per brand role
    activity = .5 + users["social_influence"].to_numpy() + users["novelty_seeking"].to_numpy()
    activity *= (PERIOD[1] - pd.to_datetime(users["signup_date"])).dt.days.to_numpy() + 14
    activity /= activity.sum()
    prim = users["primary_archetype"].map(ARCHETYPES.index).to_numpy()
    uids = users["user_id"].to_numpy()
    signup = pd.to_datetime(users["signup_date"]).to_numpy()

    while len(rows) < N_REVIEWS:
        i = rng.choice(len(users), p=activity)
        w = seg_scores[i] / seg_scores[i].sum()
        pref = np.exp(3.0 * (true_aff @ w) + 1.5 * affinity[i][cat_idx])
        j = rng.choice(len(bids), p=pref / pref.sum())
        bid = bids[j]
        if (uids[i], bid) in seen:
            continue
        seen.add((uids[i], bid))
        # rating driven by how much the reviewer's archetype truly likes the brand
        mean = 2.4 + 2.2 * true_aff[j, prim[i]] + .6 * (affinity[i][cat_idx[j]] - .5) + QUALITY[bid]
        rating = int(np.clip(round(rng.normal(mean, .8)), 1, 5))
        start = pd.Timestamp(signup[i])
        d = start + pd.Timedelta(days=int(rng.integers(0, (PERIOD[1] - start).days + 1)))
        rows.append(review_row(uids[i], bid, "", d, rating, users.at[i, "price_sensitivity"]))

    df = pd.DataFrame(rows).sort_values(["review_date", "user_id"], kind="stable").reset_index(drop=True)
    df.insert(0, "review_id", [f"R{i + 1:05d}" for i in range(len(df))])
    arch = users.set_index("user_id")["primary_archetype"]
    df["in_target_archetype"] = [int(arch[x] in BRAND[b]["targets"]) for x, b in zip(df["user_id"], df["brand_id"])]
    return df


def review_row(uid, bid, popup_id, date, rating, price_sensitivity):
    b = BRAND[bid]
    liked, disliked = attributes("hot_drink" if b["hot_drink"] else b["category"], rating)
    return dict(user_id=uid, brand_id=bid, popup_id=popup_id, review_date=date.date().isoformat(),
                rating=rating, would_buy=would_buy(rating, price_sensitivity),
                liked_attribute=liked, disliked_attribute=disliked)


# ---------------------------------------------------------------- checks
def check(users, reviews, popups, popup_brands):
    assert len(users) == N_USERS and users["user_id"].is_unique
    per_popup = users[users["signup_source"] != "organic"]["signup_source"].value_counts()
    assert (per_popup.reindex(popups["popup_id"]).fillna(0).astype(int).values == popups["signups"].values).all()
    pr = reviews[reviews["popup_id"] != ""].groupby(["popup_id", "brand_id"]).agg(
        reviews=("rating", "size"), mean=("rating", "mean"))
    pb = popup_brands[popup_brands["reviews"] > 0].set_index(["popup_id", "brand_id"])
    pr = pr.reindex(pb.index)
    assert (pr["reviews"] == pb["reviews"]).all()
    assert ((pr["mean"] - pb["avg_rating"]).abs() <= np.maximum(.05, .5 / pb["reviews"]) + 1e-9).all()
    assert not reviews.duplicated(["user_id", "brand_id"]).any()
    signup = users.set_index("user_id")["signup_date"]
    assert (reviews["review_date"].values >= signup[reviews["user_id"]].values).all()


if __name__ == "__main__":
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else paths.SYNTHETIC
    popups = pd.read_csv(out_dir / "popups.csv")
    popup_brands = pd.read_csv(out_dir / "popup_brands.csv")

    users, members = make_users(popups, popup_brands)
    reviews = make_reviews(users, popups, popup_brands, members)
    check(users, reviews, popups, popup_brands)

    users.to_csv(out_dir / "users.csv", index=False)
    reviews.to_csv(out_dir / "reviews.csv", index=False)
    print(f"Wrote {len(users)} users ({(users['signup_source'] != 'organic').sum()} from pop-ups), "
          f"{len(reviews)} reviews ({(reviews['popup_id'] != '').sum()} at pop-ups), "
          f"to {out_dir}/")
