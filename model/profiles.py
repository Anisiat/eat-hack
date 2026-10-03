"""Step 5: brand event profiles: where each client brand wins, what to sample, where to avoid.

The paragraph is filled from the numbers by a template; it never sets them. Products, flavours and
label claims come from RGC's brand sheet (brand_products.csv).
"""
import numpy as np
import pandas as pd

from . import fit as fitmod
from .data import ARCHETYPES, nice

MIN_ARCHETYPE_REVIEWS = 20
TYPE_LABEL = {"community": "community events", "concerts": "concerts and club nights",
              "conferences": "conferences and hackathons", "expos": "expos and fairs", "festivals": "festivals",
              "performing_arts": "performing-arts nights", "sports": "sports events"}


def type_events(d):
    """One neutral event per type: typical indoor or outdoor, no season, no audience tags."""
    et = d["event_types"]
    return pd.DataFrame(dict(event_type=et.index, indoor=(et["indoor_share"] >= 0.5).astype(int).to_numpy(),
                             month=0, audience_tags="")).set_index("event_type", drop=False)


def build(d, fm, scores, events):
    brands, reviews, users = d["brands"], d["reviews"], d["users"]
    te = type_events(d)
    parts = fitmod.score(d, fm, te)
    rv = reviews.merge(users[["user_id", "primary_archetype"]], on="user_id")
    profiles = {}
    for j, bid in enumerate(brands.index):
        b = brands.loc[bid]
        fbt = {t: round(float(parts["fit"][k, j]), 3) for k, t in enumerate(te.index)}
        best_t = max(fbt, key=fbt.get)
        worst_t = min(fbt, key=fbt.get)
        et = d["event_types"].loc[best_t]

        r = rv[rv["brand_id"] == bid]
        seg = r.groupby("primary_archetype")["rating"].agg(["mean", "size"])
        seg = seg[seg["size"] >= MIN_ARCHETYPE_REVIEWS]
        affinity = fm.aff.loc[bid].sort_values(ascending=False)       # learned archetype affinity
        best_seg = affinity.index[0]
        arch_profile = {a: round(float(v), 3) for a, v in fm.aff.loc[bid].items()}
        liked = r.loc[r["rating"] >= 4, "liked_attribute"].dropna().mode()
        disliked = r.loc[r["rating"] <= 3, "disliked_attribute"].dropna().mode()
        liked = liked.iloc[0] if len(liked) else None
        disliked = disliked.iloc[0] if len(disliked) else None

        prod = d["products"].iloc[parts["best_product"][list(te.index).index(best_t), j]]   # best product there
        product, flavour = prod["product"], prod["flavour"]
        claims = prod["claims"].replace("; ", ", ") if prod["claims"] else None
        label_link = prod["label_link"].rstrip(". ") or None

        sample = product + (f" ({flavour})" if flavour else "") + (f"; lead with its {liked}" if liked else "")
        avoid = f"{nice(worst_t)} (fit {fbt[worst_t]:.2f})" + (f"; reviewers mark down its {disliked}"
                                                                  if disliked else "")
        # events where the tool would bring this brand come first, then the events it fits best
        top = scores[scores["brand_id"] == bid].sort_values(["in_best_lineup", "fit"], ascending=False).head(5)
        top_events = [dict(event_id=row.event_id, name=events.at[row.event_id, "name"],
                           date=events.at[row.event_id, "date"], event_type=events.at[row.event_id, "event_type"],
                           exp_reviews=round(row.exp_reviews, 1))
                      for row in top.itertuples()]
        seg_txt = (f"{nice(best_seg)}s like it most (affinity {affinity.iloc[0]:.2f}, then {nice(affinity.index[1])}s "
                   f"at {affinity.iloc[1]:.2f}"
                   + (f"; {seg.at[best_seg, 'mean']:.1f} stars from {int(seg.at[best_seg, 'size'])} of their reviews)"
                      if best_seg in seg.index else ")"))
        when = {"finish": "at the finish", "interval": "in the interval"}.get(et["peak_slot"], et["peak_slot"])
        text = (f"{b['brand_name']} wins at {TYPE_LABEL[best_t]}. Best moment: "
                f"{et['moment'][0].lower() + et['moment'][1:]}, {when}. {seg_txt[0].upper() + seg_txt[1:]}. "
                f"Sample {sample}."
                + (f" Its label claims ({claims}) speak to this crowd" + (f": {label_link}." if label_link else ".")
                   if claims else "")
                + f" It is weakest at {TYPE_LABEL[worst_t]}, so bring other brands there. "
                + (f"Best upcoming: {top_events[0]['name']} on {top_events[0]['date']}, "
                   f"about {top_events[0]['exp_reviews']:.0f} reviews from it." if top_events else ""))
        profiles[bid] = dict(brand_name=b["brand_name"], fit_by_type=fbt, best_type=best_t,
                             best_moment=f"{et['moment']} ({et['peak_slot']})", best_audience=nice(best_seg),
                             archetype_affinity=arch_profile, target_archetypes=[a for a in ARCHETYPES
                                                                                 if b[f"target_{a}"] == 1],
                             sample=sample, avoid=avoid, top_events=top_events, text=text)
    return profiles
