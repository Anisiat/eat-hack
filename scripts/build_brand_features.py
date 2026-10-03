"""
build_brand_features.py - turn RGC's brand sheet (brands.csv, one row per product) into model-ready tables.

Reads:
  brands.csv                     RGC's real client products (Brand, Product / variant, Category, ...)
  data/mappings/need_states.csv  inferred need-state phrase -> weights on the 8 model need states
  data/mappings/segments.csv     inferred target-segment phrase -> weights on the 5 WatchHumans segments
Writes:
  brand_products.csv   one row per product: brand_id, product, flavour, format, claims, need_* (8), core category
  brand_features.csv   one row per brand: need_* (8), target_* (5), category, dietary and practical flags,
                       favourite_five (RGC's assumed habit lineup), units_available_per_month (synthetic)

Edit the mapping CSVs to change how phrases are read; unmapped phrases are listed when the script runs.

Run:  python scripts/build_brand_features.py [repo_folder]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

NEEDS = ["hydrate", "recover", "energy", "focus", "discovery", "sharing", "treat", "value"]
SEGMENTS = ["students", "young_professionals", "fitness", "families", "foodies"]
SEED = 44
TARGET_SHARE = 0.6          # a segment is a target when its weight is >= 60% of the brand's strongest segment
CONDIMENT_TERMS = ("cooking", "meal", "add heat", "spread", "topping")


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


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    sheet = pd.read_csv(root / "brands.csv", encoding="utf-8-sig")
    sheet.columns = [c.strip() for c in sheet.columns]
    sheet = sheet.rename(columns={
        "Brand": "brand", "Product / variant": "product", "Category": "category", "Sub-category": "sub_category",
        "Flavour profile": "flavour", "Format": "format", "Dietary flags": "dietary_flags",
        "Need states served (inferred)": "need_terms", "Target segments (inferred)": "segment_terms",
        "Marketing claims / label keywords": "claims", "Label → target link (inferred)": "label_link"})
    sheet = sheet.drop_duplicates(["brand", "product"]).reset_index(drop=True)
    for c in ["flavour", "claims", "label_link", "dietary_flags"]:
        sheet[c] = sheet[c].fillna("").astype(str).str.replace("\n", "; ").str.strip()

    need_map = pd.read_csv(root / "data" / "mappings" / "need_states.csv").set_index("term")[NEEDS]
    seg_map = pd.read_csv(root / "data" / "mappings" / "segments.csv").set_index("term")[SEGMENTS]
    missing_n, missing_s = set(), set()

    brand_ids = {b: f"B{i + 1:02d}" for i, b in enumerate(dict.fromkeys(sheet["brand"]))}
    prows = []
    for i, r in sheet.iterrows():
        nterms, sterms = split_terms(r["need_terms"]), split_terms(r["segment_terms"])
        missing_n |= {t for t in nterms if t not in need_map.index}
        missing_s |= {t for t in sterms if t not in seg_map.index}
        needs = need_map.reindex([t for t in nterms if t in need_map.index]).sum().clip(0, 1)
        segs = seg_map.reindex([t for t in sterms if t in seg_map.index]).max()
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
        row.update({f"need_{n}": round(float(needs.get(n, 0)), 3) for n in NEEDS})
        row.update({f"seg_{s}": float(segs.get(s, 0)) if len(segs) else 0.0 for s in SEGMENTS})
        prows.append(row)
    products = pd.DataFrame(prows)

    # brand level: average need states, strongest segments, most common role, any-product dietary flags
    rng = np.random.default_rng(SEED)
    counts = products["brand_id"].value_counts()
    # RGC's assumed habit lineup: the five brands with the most products on the shelf (ties alphabetical)
    favourites = (products.groupby(["brand_id", "brand_name"]).size().reset_index(name="n")
                  .sort_values(["n", "brand_name"], ascending=[False, True])["brand_id"].head(5).tolist())
    brows = []
    for bid, g in products.groupby("brand_id", sort=True):
        needs = g[[f"need_{n}" for n in NEEDS]].mean()
        seg = g[[f"seg_{s}" for s in SEGMENTS]].max().to_numpy()
        if seg.max() == 0:
            seg = np.ones(len(SEGMENTS))
        target = (seg >= TARGET_SHARE * seg.max()).astype(int)
        row = dict(brand_id=bid, brand_name=g["brand_name"].iloc[0],
                   category=g["core_category"].mode().iloc[0], sheet_category=g["category"].iloc[0],
                   sub_category=g["sub_category"].iloc[0], description=g["product"].iloc[0],
                   n_products=int(counts[bid]), products="|".join(g["product"]))
        row.update({f"need_{n}": round(float(needs[f"need_{n}"]), 3) for n in NEEDS})
        row.update({f"target_{s}": int(t) for s, t in zip(SEGMENTS, target)})
        row.update(needs_chilling=int(g["needs_chilling"].max()), frozen=0, vegan=int(g["vegan"].max()),
                   gluten_free=int(g["gluten_free"].max()), adults_only=int(g["adults_only"].min()),
                   favourite_five=int(bid in favourites),
                   units_available_per_month=int(rng.integers(6, 21) * 100))   # synthetic stock
        brows.append(row)
    brands = pd.DataFrame(brows)

    products.drop(columns=[f"seg_{s}" for s in SEGMENTS]).to_csv(root / "brand_products.csv", index=False)
    brands.to_csv(root / "brand_features.csv", index=False)
    if missing_n or missing_s:
        print("Unmapped phrases (add them to data/mappings/):", sorted(missing_n | missing_s))
    print(f"Wrote {len(products)} products and {len(brands)} brands "
          f"(favourites: {', '.join(brands.loc[brands['favourite_five'] == 1, 'brand_name'])})")


if __name__ == "__main__":
    main()
