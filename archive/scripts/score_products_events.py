"""
score_products_events.py - match every RGC product to every real event, both scored on the 10 WatchHumans
archetypes with the same keyword method (get_product_archetypes.py, get_event_archetypes.py).

  1. Rescale.  Each product's and each event's 10 scores are divided by their own top score, so the
               strongest archetype is 1 for both (product labels hold more text than event listings, so raw
               scores run higher for products).
  2. Match.    The event's rescaled scores become crowd shares (summing to 1), blended 70/30 with the
               WatchHumans population so no archetype is absent;
               match(p, e) = sum_a share_e[a] x product_p[a], from 0 to 1.
  3. Lineup.   Lineup size scales with attendance (2 under 50 people, 3 under 100, 4 under 150, else 5).
               The best-matching products are picked, one per brand, with a small penalty (0.05) for repeating
               a primary archetype already in the lineup. lineup_match = the lineup's average match.
               Adults-only products (alcohol, CBD) are left out of family events.

Reads:  data/processed/products_archetypes.csv, data/processed/events_archetypes.csv, brand_products.csv
Writes: data/processed/product_event_scores.csv  one row per event x product: match, rank
        data/processed/event_lineups.csv         one row per event: lineup, products, match, in_london

Run:  python scripts/score_products_events.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from scripts.generate_watchhumans_synthetic import ARCHETYPE_PREVALENCE
    from scripts.get_event_archetypes import ARCHETYPES
except ImportError:
    from generate_watchhumans_synthetic import ARCHETYPE_PREVALENCE
    from get_event_archetypes import ARCHETYPES

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = PROJECT_ROOT / "data" / "processed"
SCORE_COLUMNS = [f"{a}_score" for a in ARCHETYPES]
SIZE_TIERS = [(50, 2), (100, 3), (150, 4), (float("inf"), 5)]
LONDON = dict(lat=(51.28, 51.70), lon=(-0.51, 0.34))           # Greater London bounding box
POPULATION_WEIGHT = 0.3       # crowd = 70% the event's keyword profile + 30% the WatchHumans population
DIVERSITY_PENALTY = 0.05      # match points a product loses if its primary archetype is already in the lineup
FAMILY = re.compile(r"\b(family|families|kids?|children|pantomime|panto)\b", re.I)


def rescale(scores):
    """Divide each row by its top score, so the strongest archetype is 1."""
    top = scores.max(axis=1, keepdims=True)
    return np.divide(scores, top, out=np.zeros_like(scores), where=top > 0)


def lineup_size(attendance):
    att = 0 if pd.isna(attendance) else attendance
    return next(k for limit, k in SIZE_TIERS if att < limit)


def pick_lineup(match, primaries, brands, allowed, k):
    """Best-matching products, one per brand; a product whose primary archetype is already in the lineup
    pays a small penalty, so the lineup spreads across the crowd instead of repeating one profile."""
    chosen, used_brands, used_primaries = [], set(), set()
    for _ in range(k):
        score = match - DIVERSITY_PENALTY * np.array([p in used_primaries for p in primaries])
        score[~allowed] = -np.inf
        score[[i for i, b in enumerate(brands) if b in used_brands]] = -np.inf
        i = int(np.argmax(score))
        if not np.isfinite(score[i]):
            break
        chosen.append(i)
        used_brands.add(brands[i])
        used_primaries.add(primaries[i])
    return chosen, float(match[chosen].mean()) if chosen else 0.0


def main():
    products = pd.read_csv(PROCESSED / "products_archetypes.csv")
    events = pd.read_csv(PROCESSED / "events_archetypes.csv")
    flags = pd.read_csv(PROJECT_ROOT / "brand_products.csv")[["product_id", "adults_only"]]
    products = products.merge(flags, on="product_id", how="left").fillna({"adults_only": 0})

    prod = rescale(products[SCORE_COLUMNS].to_numpy(float))                  # P x A, top archetype = 1
    ev = rescale(events[SCORE_COLUMNS].to_numpy(float))                      # E x A
    shares = ev / np.where(ev.sum(1, keepdims=True) > 0, ev.sum(1, keepdims=True), 1)
    pop = np.array([ARCHETYPE_PREVALENCE[a] for a in ARCHETYPES], float)
    shares = (1 - POPULATION_WEIGHT) * shares + POPULATION_WEIGHT * pop / pop.sum()   # same rule as the model
    match = shares @ prod.T                                                  # E x P

    pairs, lineups = [], []
    brands = products["brand"].tolist()
    primaries = [ARCHETYPES[i] for i in prod.argmax(1)]
    for e, row in events.iterrows():
        text = f"{row['title']} {row.get('description', '')}"
        family = bool(FAMILY.search(text)) and "adult" not in str(row["title"]).lower()
        allowed = ~(family & (products["adults_only"].to_numpy() == 1))
        order = np.argsort(-match[e])
        rank = {p: r + 1 for r, p in enumerate(order)}
        for p in range(len(products)):
            pairs.append(dict(event_id=row["event_id"], title=row["title"], product_id=products.at[p, "product_id"],
                              brand=brands[p], product=products.at[p, "product"],
                              match=round(float(match[e, p]), 4), rank=rank[p], allowed=bool(allowed[p])))
        k = lineup_size(row["phq_attendance"])
        chosen, lineup_match = pick_lineup(match[e], primaries, brands, allowed, k)
        top = [ARCHETYPES[i] for i in np.argsort(-shares[e])[:3]]
        lineups.append(dict(
            event_id=row["event_id"], title=row["title"], category=row["category"], start_local=row["start_local"],
            attendance=row["phq_attendance"],
            in_london=bool(LONDON["lat"][0] <= row["latitude"] <= LONDON["lat"][1]
                           and LONDON["lon"][0] <= row["longitude"] <= LONDON["lon"][1]),
            family_event=family, top_archetypes="|".join(top), lineup_size=k,
            brands="|".join(brands[i] for i in chosen),
            products="|".join(products.at[i, "product"] for i in chosen),
            lineup_match=round(lineup_match, 3),
            best_single_product=products.at[int(order[0]), "product"],
            best_single_match=round(float(match[e, order[0]]), 3)))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(pairs).to_csv(PROCESSED / "product_event_scores.csv", index=False)
    out = pd.DataFrame(lineups)
    out.to_csv(PROCESSED / "event_lineups.csv", index=False)
    print(f"Scored {len(products)} products x {len(events)} events "
          f"({out['in_london'].sum()} in London). Saved to {PROCESSED}/")
    print(out[["title", "attendance", "lineup_size", "brands", "lineup_match"]].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
