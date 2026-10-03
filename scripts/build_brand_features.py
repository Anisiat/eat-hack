"""
build_brand_features.py - turn RGC's brand sheet (brands.csv, one row per product) into model-ready tables.

Archetype scores use the keyword method shared with events (get_event_archetypes.py):
  1. get_product_archetypes.py scores every product on the 10 WatchHumans archetypes from its label claims,
     name, sub-category, need states, dietary flags, flavour, sheet category and target-segment phrases.
  2. Here each product's scores are rescaled so its strongest archetype is 1 (arch_*), the same rescaling
     applied to events. A brand's profile is the mean of its products; its top 3 archetypes are its targets.
  3. For each event type in event_types.csv (crowd shares from the same keyword method), how well the product
     suits a typical crowd: event_k = sum_a crowd_k[a] x arch[a].

Reads:
  data/raw/brands.csv                      RGC's real client products (Brand, Product / variant, Category, ...)
  data/archetypes/products_archetypes.csv  keyword archetype scores per product (get_product_archetypes.py)
  data/mappings/need_states.csv            need-state phrase -> 8 need states (practical rules: chilling, hydration)
  data/processed/event_types.csv           crowd archetype shares per event type (optional: step 3)
Writes:
  data/processed/brand_products.csv   one row per product: arch_* (10), event_* (7), need_* (8), role, dietary and practical flags
  data/processed/brand_features.csv   one row per brand: arch_*, target_* (top 3 archetypes), event_* (its best product per type),
                       best_event_type, role, flags, favourite_five (assumed habit lineup), units_available_per_month

Run:  python scripts/get_product_archetypes.py && python scripts/build_brand_features.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
from generate_watchhumans_synthetic import ARCHETYPES, CATEGORY_PROFILES  # noqa: E402

NEEDS = ["hydrate", "recover", "energy", "focus", "discovery", "sharing", "treat", "value"]
SEED = 44
N_TARGETS = 3               # a brand's target archetypes: its three highest scores
CONDIMENT_TERMS = ("cooking", "meal", "add heat", "spread", "topping")
# product role -> WatchHumans category profile; used by the user generator for category affinities
ROLE_TO_PROFILE = {"drink": "functional_drinks", "savoury": "healthy_snacks", "sweet": "grab_and_go",
                   "condiment": "premium_food", "functional": "healthy_snacks", "other": "sustainable_products"}
assert set(ROLE_TO_PROFILE.values()) <= set(CATEGORY_PROFILES)
SCORE_COLUMNS = [f"{a}_score" for a in ARCHETYPES]


def split_terms(cell):
    return [t.strip() for t in str(cell).replace(";", "\n").split("\n") if t.strip()]


def core_category(row, terms):
    """Map the sheet's category to the model's lineup roles: drink, savoury, sweet, condiment, functional, other."""
    cat, low = row["category"], [t.lower() for t in terms]
    if cat in ("Drinks", "Alcoholic drinks"):
        return "drink"
    if cat == "Confectionery":
        return "sweet"
    if cat == "Wellness" or any("protein" in t for t in low):
        return "functional"
    if cat == "Snacks":
        return "sweet" if any("sweet" in t for t in low) else "savoury"
    if cat == "Pantry":
        return "condiment" if any(k in t for t in low for k in CONDIMENT_TERMS) else "drink"
    return "other"


def rescale(scores):
    """Divide by the top score so the strongest archetype is 1 (the same rescaling used for events)."""
    top = scores.max()
    return scores / top if top > 0 else scores


def main():
    sheet = pd.read_csv(paths.BRANDS, encoding="utf-8-sig")
    sheet.columns = [c.strip() for c in sheet.columns]
    sheet = sheet.rename(columns={
        "Brand": "brand", "Product / variant": "product", "Category": "category", "Sub-category": "sub_category",
        "Flavour profile": "flavour", "Format": "format", "Dietary flags": "dietary_flags",
        "Need states served (inferred)": "need_terms", "Target segments (inferred)": "segment_terms",
        "Marketing claims / label keywords": "claims", "Label → target link (inferred)": "label_link"})
    sheet = sheet.drop_duplicates(["brand", "product"]).reset_index(drop=True)
    for c in ["flavour", "claims", "label_link", "dietary_flags"]:
        sheet[c] = sheet[c].fillna("").astype(str).str.replace("\n", "; ").str.strip()

    keyword = pd.read_csv(paths.PRODUCTS_ARCHETYPES).set_index(["brand", "product"])
    need_map = pd.read_csv(paths.NEED_STATES).set_index("term")[NEEDS]
    et_path = paths.EVENT_TYPES
    event_types = pd.read_csv(et_path).set_index("event_type") if et_path.exists() else None
    missing = sorted(set(map(tuple, sheet[["brand", "product"]].to_numpy())) - set(keyword.index))
    assert not missing, f"products missing from products_archetypes.csv (rerun get_product_archetypes.py): {missing}"

    brand_ids = {b: f"B{i + 1:02d}" for i, b in enumerate(dict.fromkeys(sheet["brand"]))}
    prows = []
    for i, r in sheet.iterrows():
        nterms, sterms = split_terms(r["need_terms"]), split_terms(r["segment_terms"])
        needs = need_map.reindex([t for t in nterms if t in need_map.index]).sum().clip(0, 1).reindex(NEEDS).fillna(0)
        arch = rescale(keyword.loc[(r["brand"], r["product"]), SCORE_COLUMNS].to_numpy(float))
        flags = (r["dietary_flags"] + " " + r["claims"]).lower()
        adults = r["category"] == "Alcoholic drinks" or "cbd" in (r["product"] + r["sub_category"]).lower() \
            or any(t.lower().startswith("adult") for t in sterms)
        row = dict(product_id=f"S{i + 1:03d}", brand_id=brand_ids[r["brand"]], brand_name=r["brand"],
                   product=r["product"], category=r["category"], sub_category=r["sub_category"],
                   core_category=core_category(r, nterms), flavour=r["flavour"], format=r["format"],
                   dietary_flags=r["dietary_flags"], claims=r["claims"], label_link=r["label_link"],
                   vegan=int("vegan" in flags or "plant-based" in flags or "plant based" in flags),
                   gluten_free=int("gluten-free" in flags or "gluten free" in flags),
                   adults_only=int(adults),
                   needs_chilling=int(r["category"] in ("Drinks", "Alcoholic drinks")
                                      and any(k in r["format"].lower() for k in ("can", "bottle"))))
        row.update({f"need_{n}": round(float(needs[n]), 3) for n in NEEDS})
        row.update({f"arch_{a}": round(float(v), 3) for a, v in zip(ARCHETYPES, arch)})
        if event_types is not None:
            for t, e in event_types.iterrows():
                row[f"event_{t}"] = round(float(e[[f"mix_{a}" for a in ARCHETYPES]].to_numpy(float) @ arch), 3)
        prows.append(row)
    products = pd.DataFrame(prows)
    event_cols = [c for c in products.columns if c.startswith("event_")]

    # brand level: mean archetype scores, top 3 archetypes, best product per event type, most common role
    rng = np.random.default_rng(SEED)
    counts = products["brand_id"].value_counts()
    # RGC's assumed habit lineup: the five brands with the most products on the shelf (ties alphabetical)
    favourites = (products.groupby(["brand_id", "brand_name"]).size().reset_index(name="n")
                  .sort_values(["n", "brand_name"], ascending=[False, True])["brand_id"].head(5).tolist())
    brows = []
    for bid, g in products.groupby("brand_id", sort=True):
        needs = g[[f"need_{n}" for n in NEEDS]].mean()
        arch = g[[f"arch_{a}" for a in ARCHETYPES]].mean().to_numpy()
        top = set(np.argsort(-arch, kind="stable")[:N_TARGETS])
        row = dict(brand_id=bid, brand_name=g["brand_name"].iloc[0],
                   category=g["core_category"].mode().iloc[0], sheet_category=g["category"].iloc[0],
                   sub_category=g["sub_category"].iloc[0], description=g["product"].iloc[0],
                   n_products=int(counts[bid]), products="|".join(g["product"]))
        row.update({f"need_{n}": round(float(needs[f"need_{n}"]), 3) for n in NEEDS})
        row.update({f"arch_{a}": round(float(v), 3) for a, v in zip(ARCHETYPES, arch)})
        row.update({f"target_{a}": int(k in top) for k, a in enumerate(ARCHETYPES)})
        row.update({c: round(float(g[c].max()), 3) for c in event_cols})          # its best product there
        if event_cols:
            row["best_event_type"] = max(event_cols, key=lambda c: row[c])[len("event_"):]
        row.update(needs_chilling=int(g["needs_chilling"].max()), frozen=0, vegan=int(g["vegan"].max()),
                   gluten_free=int(g["gluten_free"].max()), adults_only=int(g["adults_only"].min()),
                   favourite_five=int(bid in favourites),
                   units_available_per_month=int(rng.integers(6, 21) * 100))   # synthetic stock
        brows.append(row)
    brands = pd.DataFrame(brows)

    products.to_csv(paths.BRAND_PRODUCTS, index=False)
    brands.to_csv(paths.BRAND_FEATURES, index=False)
    if event_types is None:
        print("event_types.csv not found: run build_event_types.py first for event_* scores")
    print(f"Wrote {len(products)} products and {len(brands)} brands "
          f"(favourites: {', '.join(brands.loc[brands['favourite_five'] == 1, 'brand_name'])})")


if __name__ == "__main__":
    main()
