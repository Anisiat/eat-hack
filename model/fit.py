"""Step 1: archetype match between each event's expected crowd and each brand's products.

Three archetype profiles meet here (10 WatchHumans archetypes each):
  crowd_e      expected archetype mix at event e. For real events: the event's own archetype scores from
               events_archetypes.csv, rescaled so the top archetype is 1 and made into shares. For past pop-ups:
               the crowd table's assumption for the type, updated with who signed up at past pop-ups
  aff_p        how much each archetype likes product p: the brand sheet's phrases (data/mappings), updated
               with WatchHumans ratings by reviewer archetype (shrunk towards the sheet when reviews are few)
  match_{p,e}  = sum_a crowd_e[a] x aff_p[a]: how much the average person at e will like p

fit_{b,e} = max over b's products of  match_{p,e}  x  c_{b,e}      (c is practical context: chilling outdoors)
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import ARCHETYPES, nice, pct

PRIOR_WEIGHT = 50       # sign-ups of evidence the assumed crowd mix is worth
SHRINK_K = 20           # reviews from one archetype at which ratings and the sheet count equally
RATING_PER_AFFINITY = 2.2   # stars between an archetype that loves a product and one that doesn't
TAG_BOOST = 1.3
WINTER = {10, 11, 12, 1, 2, 3}
SUMMER = {6, 7, 8}


@dataclass
class FitModel:
    type_mix: pd.DataFrame      # event_type x ARCHETYPES, rows sum to 1
    aff: pd.DataFrame           # brand_id x ARCHETYPES, learned affinity
    aff_prior: pd.DataFrame     # brand_id x ARCHETYPES, from the brand sheet
    aff_n: pd.DataFrame         # brand_id x ARCHETYPES, reviews behind the learned part


def train(d):
    """Learn crowd mixes and archetype affinities from data before the held-out pop-ups only."""
    et, popups = d["event_types"], d["popups"]
    train_ids = set(popups.loc[popups["split"] == "train", "popup_id"])
    test_start = popups.loc[popups["split"] == "test", "date"].min()
    types = et.index.tolist()

    assumed = et[[f"mix_{a}" for a in ARCHETYPES]].to_numpy(float)
    u = d["users"][d["users"]["signup_source"].isin(train_ids)]
    u = u.merge(popups[["popup_id", "event_type"]], left_on="signup_source", right_on="popup_id")
    counts = pd.crosstab(u["event_type"], u["primary_archetype"]).reindex(index=types, columns=ARCHETYPES,
                                                                          fill_value=0)
    mix = (counts.to_numpy(float) + PRIOR_WEIGHT * assumed) / (counts.sum(1).to_numpy()[:, None] + PRIOR_WEIGHT)
    type_mix = pd.DataFrame(mix, index=types, columns=ARCHETYPES)

    # archetype affinity: rating gap by reviewer archetype, converted to affinity units and shrunk to the sheet
    r = d["reviews"]
    # organic reviews only: pop-up ratings in this data are per stall, not per archetype
    r = r[(r["popup_id"] == "") & (r["review_date"] < test_start)]
    r = r.merge(d["users"][["user_id", "primary_archetype"]], on="user_id")
    bids = d["brands"].index
    prior = d["brands"][[f"arch_{a}" for a in ARCHETYPES]].set_axis(ARCHETYPES, axis=1)
    g = r.groupby(["brand_id", "primary_archetype"])["rating"].agg(["mean", "size"])
    mean_r = g["mean"].unstack().reindex(index=bids, columns=ARCHETYPES)
    n = g["size"].unstack().reindex(index=bids, columns=ARCHETYPES).fillna(0)
    brand_mean = r.groupby("brand_id")["rating"].mean().reindex(bids)
    learned = prior.mean(1).to_numpy()[:, None] + (mean_r.sub(brand_mean, axis=0)) / RATING_PER_AFFINITY
    w = n / (n + SHRINK_K)
    aff = (w * learned.fillna(prior) + (1 - w) * prior).clip(0, 1)
    return FitModel(type_mix, aff, prior, n.astype(int))


def event_mix(fm, events):
    crowd = [f"crowd_{a}" for a in ARCHETYPES]
    if set(crowd) <= set(events.columns):                    # real events carry their own archetype mix
        return events[crowd].to_numpy(float)
    mix = fm.type_mix.loc[events["event_type"]].to_numpy().copy()
    for i, tags in enumerate(events["audience_tags"].fillna("")):
        for t in filter(None, str(tags).split("|")):
            if t in ARCHETYPES:
                mix[i, ARCHETYPES.index(t)] *= TAG_BOOST
    return mix / mix.sum(1, keepdims=True)


def score(d, fm, events):
    """Fit and its parts for every event (rows) x brand (columns), via each brand's best product."""
    brands, et, pr = d["brands"], d["event_types"], d["products"]
    bids = list(brands.index)
    mix = event_mix(fm, events)                                              # E x A

    # product affinities: the sheet's product profile, shifted by what reviews taught us about its brand
    shift = (fm.aff - fm.aff_prior).loc[pr["brand_id"]].to_numpy()
    aff_p = np.clip(pr[[f"arch_{a}" for a in ARCHETYPES]].to_numpy(float) + shift, 0, 1)   # P x A
    match_p = mix @ aff_p.T                                                  # E x P

    outdoor = (events["indoor"].to_numpy() == 0)[:, None]
    month = events["month"].to_numpy()[:, None]
    chill = brands["needs_chilling"].to_numpy()[None, :] == 1
    frozen = brands["frozen"].to_numpy()[None, :] == 1
    hydrate = brands["need_hydrate"].to_numpy()[None, :] >= 0.5
    c = np.ones((len(events), len(bids)))
    c = np.where(chill & outdoor, c * 0.85, c)
    c = np.where(frozen & outdoor & np.isin(month, list(WINTER)), c * 0.6, c)
    c = np.where(hydrate & outdoor & np.isin(month, list(SUMMER)), c * 1.1, c)

    E, B, A = len(events), len(bids), len(ARCHETYPES)
    p_brand = pr["brand_id"].map({b: j for j, b in enumerate(bids)}).to_numpy()
    fit = np.zeros((E, B))
    best = np.zeros((E, B), int)
    match = np.zeros((E, B))
    per_arch = np.zeros((E, B, A))       # each archetype's liking of the brand's chosen product, in context
    for j in range(B):
        idx = np.flatnonzero(p_brand == j)
        sc = match_p[:, idx]
        k = sc.argmax(1)
        best[:, j] = idx[k]
        rows = np.arange(E)
        match[:, j] = match_p[rows, idx[k]]
        fit[:, j] = sc[rows, k] * c[:, j]
        per_arch[:, j, :] = aff_p[idx[k]] * c[:, j][:, None]

    target = brands[[f"target_{a}" for a in ARCHETYPES]].to_numpy(float)
    q = mix @ target.T                                                       # crowd share in target archetypes
    return dict(fit=fit, match=match, c=c, q=q, mix=mix, per_arch=per_arch, best_product=best)


def coverage(parts, i, lineup):
    """Lineup match at event i: every expected archetype is credited with its favourite product in the lineup."""
    return float(parts["per_arch"][i, list(lineup)].max(0) @ parts["mix"][i])


def reasons(d, fm, events, parts, i, j):
    """Three plain-language reasons for brand j at event i, strongest first."""
    b = d["brands"].iloc[j]
    bid = b["brand_id"]
    etype = events["event_type"].iloc[i]
    prod = d["products"].iloc[parts["best_product"][i, j]]
    mix = parts["mix"][i]
    contrib = mix * fm.aff.loc[bid].to_numpy()
    top = [ARCHETYPES[k] for k in np.argsort(-contrib)[:2]]
    share = sum(mix[ARCHETYPES.index(a)] for a in top)
    best_arch = fm.aff.loc[bid].idxmax()
    out = [f"{prod['product']} suits the expected crowd: {pct(share)} are {nice(top[0])}s or {nice(top[1])}s, "
           f"who like it (affinity {fm.aff.at[bid, top[0]]:.2f}, {fm.aff.at[bid, top[1]]:.2f})",
           f"Archetype match {parts['match'][i, j]:.2f} at this {nice(etype)} event; the brand's strongest "
           f"archetype is {nice(best_arch)} ({fm.aff.at[bid, best_arch]:.2f})"]
    n = int(fm.aff_n.loc[bid, top[0]])
    gap = fm.aff.at[bid, top[0]] - fm.aff_prior.at[bid, top[0]]
    if n >= 10:
        out.append(f"{n} WatchHumans reviews from {nice(top[0])}s moved its affinity {gap:+.2f} from the brand sheet")
    elif parts["c"][i, j] < 1:
        out.append("Penalised: needs chilling at an outdoor event")
    else:
        out.append(f"Few reviews from {nice(top[0])}s yet; affinity comes from the brand sheet")
    return out
