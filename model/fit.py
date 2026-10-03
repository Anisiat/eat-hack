"""Step 1: fit score for every brand at every event.

fit_{b,e} = cos(n_b, n_e) x a_{b,e} x c_{b,e} x (1 + h_{b,k})
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import NEEDS, SEGMENTS, brand_matrices, nice, pct

PRIOR_WEIGHT = 50       # sign-ups of evidence the assumed crowd mix is worth
SHRINK_K = 10           # reviews at which a learned lift is trusted halfway
TAG_BOOST = 1.3         # audience tags on an event nudge its segment mix
WINTER = {10, 11, 12, 1, 2, 3}
SUMMER = {6, 7, 8}


@dataclass
class FitModel:
    type_mix: pd.DataFrame      # event_type x SEGMENTS, rows sum to 1
    lift: pd.DataFrame          # brand_id x event_type, h (0 where no evidence)
    lift_n: pd.DataFrame        # brand_id x event_type, review counts behind h
    lift_stars: pd.DataFrame    # brand_id x event_type, rating gap in stars


def train(d):
    """Learn the audience mix per event type and the brand lift h from the training pop-ups only."""
    et, popups = d["event_types"], d["popups"]
    train_ids = set(popups.loc[popups["split"] == "train", "popup_id"])
    types = et.index.tolist()

    # audience mix: assumed crowd table, updated with who actually signed up at past pop-ups
    assumed = et[[f"mix_{s}" for s in SEGMENTS]].to_numpy(float)
    u = d["users"][d["users"]["signup_source"].isin(train_ids)]
    u = u.merge(popups[["popup_id", "event_type"]], left_on="signup_source", right_on="popup_id")
    counts = pd.crosstab(u["event_type"], u["segment"]).reindex(index=types, columns=SEGMENTS, fill_value=0)
    mix = (counts.to_numpy(float) + PRIOR_WEIGHT * assumed) / (counts.sum(1).to_numpy()[:, None] + PRIOR_WEIGHT)
    type_mix = pd.DataFrame(mix, index=types, columns=SEGMENTS)

    # lift: brand's pop-up rating at type k against its own pop-up average, shrunk towards zero
    r = d["reviews"][d["reviews"]["popup_id"].isin(train_ids)]
    r = r.merge(popups[["popup_id", "event_type"]], on="popup_id")
    brand_mean = r.groupby("brand_id")["rating"].mean()
    g = r.groupby(["brand_id", "event_type"])["rating"].agg(["mean", "size"])
    gap = (g["mean"] - g.index.get_level_values(0).map(brand_mean).to_numpy())
    n = g["size"]
    h = n / (n + SHRINK_K) * gap / 2.5
    bids = d["brands"].index
    lift = h.unstack().reindex(index=bids, columns=types).fillna(0.0)
    lift_n = n.unstack().reindex(index=bids, columns=types).fillna(0).astype(int)
    lift_stars = gap.unstack().reindex(index=bids, columns=types).fillna(0.0)
    return FitModel(type_mix, lift, lift_n, lift_stars)


def event_mix(fm, events):
    """Audience mix per event: the type mix, nudged by the event's audience tags."""
    mix = fm.type_mix.loc[events["event_type"]].to_numpy().copy()
    for i, tags in enumerate(events["audience_tags"].fillna("")):
        for t in filter(None, str(tags).split("|")):
            if t in SEGMENTS:
                mix[i, SEGMENTS.index(t)] *= TAG_BOOST
    return mix / mix.sum(1, keepdims=True)


def score(d, fm, events):
    """Fit and its parts for every event (rows) x brand (columns)."""
    brands, et = d["brands"], d["event_types"]
    n_b, target = brand_matrices(brands)
    n_e = et.loc[events["event_type"], [f"need_{n}" for n in NEEDS]].to_numpy(float)
    cos = (n_e @ n_b.T) / (np.linalg.norm(n_e, axis=1)[:, None] * np.linalg.norm(n_b, axis=1)[None, :])

    mix = event_mix(fm, events)
    q = mix @ target.T                                       # share of crowd in the brand's targets
    a = 0.4 + 0.6 * q

    outdoor = (events["indoor"].to_numpy() == 0)[:, None]
    month = events["month"].to_numpy()[:, None]
    chill = brands["needs_chilling"].to_numpy()[None, :] == 1
    frozen = brands["frozen"].to_numpy()[None, :] == 1
    hydrate = brands["need_hydrate"].to_numpy()[None, :] >= 0.5
    c = np.ones_like(cos)
    c = np.where(chill & outdoor, c * 0.85, c)
    c = np.where(frozen & outdoor & np.isin(month, list(WINTER)), c * 0.6, c)
    c = np.where(hydrate & outdoor & np.isin(month, list(SUMMER)), c * 1.1, c)

    h = fm.lift.loc[brands.index, :].T.reindex(events["event_type"]).to_numpy()
    fit = cos * a * c * (1 + h)
    contrib = n_e[:, None, :] * n_b[None, :, :]               # events x brands x needs
    return dict(fit=fit, cos=cos, a=a, q=q, c=c, h=h, mix=mix, top_need=contrib.argmax(2),
                outdoor=outdoor[:, 0], chill=chill[0], frozen=frozen[0])


def reasons(d, fm, events, parts, i, j):
    """Three plain-language reasons for brand j at event i, strongest first."""
    b = d["brands"].iloc[j]
    etype = events["event_type"].iloc[i]
    need = NEEDS[parts["top_need"][i, j]]
    targets = [s for s in SEGMENTS if b[f"target_{s}"] == 1]
    out = [f"{need.capitalize()} need matches the {nice(etype)} crowd "
           f"(brand {b[f'need_{need}']:.1f}, event {d['event_types'].at[etype, f'need_{need}']:.1f})",
           f"{pct(parts['q'][i, j])} of the crowd is in its target segments ({', '.join(nice(t) for t in targets)})"]
    n = fm.lift_n.at[b["brand_id"], etype]
    stars = fm.lift_stars.at[b["brand_id"], etype]
    if n >= 5:
        out.append(f"Rated {stars:+.1f} stars against its pop-up average at {nice(etype)} ({n} reviews)")
    elif parts["c"][i, j] < 1:
        out.append("Penalised: needs chilling or freezing at an outdoor event")
    elif parts["c"][i, j] > 1:
        out.append("Boosted: hydrating product at a summer outdoor event")
    else:
        out.append(f"No WatchHumans reviews at {nice(etype)} yet; fit comes from need states and audience")
    return out
