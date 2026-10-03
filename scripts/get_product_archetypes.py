"""
get_product_archetypes.py - score every product in RGC's brand sheet (brands.csv) on the 10 WatchHumans
archetypes, using the same method get_event_archetypes.py uses for events, so products and events sit on
one comparable scale.

The method (mirrors event_profile in get_event_archetypes.py):
  1. Text keywords. Each text field is scanned for archetype keywords (the events' TEXT_KEYWORDS plus
     food-and-label words below). Every match adds the field's weight, at most 3 matches per field.
  2. Sheet category. The product's category (Snacks, Drinks, Pantry, ...) adds 0.20 x its archetype affinity.
  3. Target segments. The sheet's "Target segments (inferred)" phrases play the role of PredictHQ labels:
     each maps to archetypes (data/mappings/segment_archetypes.csv) and adds 0.45 x affinity, capped at 1.
  4. Saturation. score = 1 - exp(-strength): comparable across products without forcing a winner to 1.
Every score keeps its evidence (which words or phrases fired), and each product gets a primary and
secondary archetype.

Reads:  data/raw/brands.csv, data/mappings/segment_archetypes.csv
Writes: data/archetypes/products_archetypes.csv (one row per product)

Run:  python scripts/get_product_archetypes.py
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:   # works when imported as scripts.* (tests) or run as a script
    from scripts import paths
except ImportError:
    import paths
try:   # shared vocabulary and matching; works when imported as scripts.* or run as a script
    from scripts.get_event_archetypes import ARCHETYPES, TEXT_KEYWORDS, get_top_archetypes, matched_keywords
except ImportError:
    from get_event_archetypes import ARCHETYPES, TEXT_KEYWORDS, get_top_archetypes, matched_keywords

BRANDS_PATH = paths.BRANDS
SEGMENT_MAP_PATH = paths.SEGMENT_ARCHETYPES
OUTPUT_PATH = paths.PRODUCTS_ARCHETYPES

# brands.csv column -> weight. Label claims are the product's "title": short, specific, written to attract
# a shopper. Longer explanatory text counts less, like an event's description.
FIELD_WEIGHTS = {
    "Marketing claims / label keywords": 0.65,
    "Product / variant": 0.40,
    "Label → target link (inferred)": 0.40,
    "Need states served (inferred)": 0.30,
    "Sub-category": 0.30,
    "Dietary flags": 0.25,
    "Flavour profile": 0.15,
}
CATEGORY_WEIGHT = 0.20
SEGMENT_WEIGHT = 0.45
MAX_MATCHES_PER_FIELD = 3

# Sheet category -> archetype affinity (our assumptions, like CATEGORY_TO_ARCHETYPE for events)
CATEGORY_TO_ARCHETYPE = {
    "Snacks": {"impulse_buyer": 0.5, "on_the_go_shopper": 0.5, "wellness_seeker": 0.3},
    "Drinks": {"on_the_go_shopper": 0.4, "trend_enthusiast": 0.4, "wellness_seeker": 0.3},
    "Alcoholic drinks": {"experience_explorer": 0.7, "impulse_buyer": 0.5, "trend_enthusiast": 0.5},
    "Pantry": {"everyday_planner": 0.7, "thoughtful_buyer": 0.5, "quality_seeker": 0.4},
    "Confectionery": {"impulse_buyer": 0.8, "experience_explorer": 0.3},
    "Wellness": {"wellness_seeker": 1.0, "conscious_consumer": 0.4},
    "Accessories": {"conscious_consumer": 0.6, "on_the_go_shopper": 0.5},
}

# Food and label words, added to the events' vocabulary (a copy: the event keywords are not changed)
PRODUCT_KEYWORDS = {
    "wellness_seeker": ["protein", "high protein", "no added sugar", "low sugar", "sugar free", "less fat",
                        "low calorie", "kcal", "kcals", "fibre", "gut", "prebiotic", "probiotic", "vitamin",
                        "electrolyte", "adaptogen", "lion s mane", "caffeine free", "superfood", "ginseng",
                        "hydration", "sleep", "calm", "balance", "nutrition"],
    "trend_enthusiast": ["matcha", "cbd", "mushroom", "new", "innovative", "bold", "iced latte"],
    "thoughtful_buyer": ["no artificial", "non gmo", "free from", "no added junk", "allergens", "real fruit",
                         "natural", "naturally", "ingredients", "no sulphites"],
    "smart_saver": ["multipack", "sharing bag", "family size", "great value"],
    "quality_seeker": ["small batch", "handcrafted", "craft", "award", "award winning", "great taste",
                       "single origin", "truffle", "triple cooked", "artisan", "english sparkling", "dark chocolate"],
    "on_the_go_shopper": ["on the go", "snack bag", "portable", "resealable", "instant", "ready to drink",
                          "steel bottle", "snack pouch"],
    "impulse_buyer": ["sweet", "sour", "treat", "indulgent", "chocolate", "marshmallow", "marshmallows",
                      "gummies", "fudge", "brownie", "caramel", "crunch"],
    "experience_explorer": ["spicy", "chilli", "jalapeño", "jalapeno", "heat", "miso", "teriyaki", "cocktail",
                            "mixer", "botanical", "spritz", "aperitif", "toasting", "peri peri", "exotic"],
    "everyday_planner": ["cooking", "recipe", "meal", "pantry", "breakfast", "spread", "everyday", "pasta sauce",
                         "mayo", "tea"],
    "conscious_consumer": ["organic", "vegan", "plant based", "eco", "recyclable", "compostable", "b corp",
                           "give back", "gives back", "ethical", "palm oil free", "reusable", "plastic free"],
}
KEYWORDS = {a: list(dict.fromkeys(TEXT_KEYWORDS.get(a, []) + PRODUCT_KEYWORDS.get(a, []))) for a in ARCHETYPES}
SCORE_COLUMNS = [f"{a}_score" for a in ARCHETYPES]


def split_phrases(cell):
    return [t.strip() for t in str(cell).replace(";", "\n").split("\n") if t.strip() and str(cell) != "nan"]


def load_segment_map(path=SEGMENT_MAP_PATH):
    m = pd.read_csv(path).set_index("term")
    return {term: {a: float(v) for a, v in row.items() if a in ARCHETYPES and v > 0} for term, row in m.iterrows()}


def product_profile(row, segment_map):
    """Archetype scores and evidence for one product row of brands.csv."""
    strengths = {a: 0.0 for a in ARCHETYPES}
    evidence = {a: [] for a in ARCHETYPES}

    def add(archetype, strength, source, matches):
        if strength > 0:
            strengths[archetype] += strength
            evidence[archetype].append({"source": source, "matches": matches})

    for field, weight in FIELD_WEIGHTS.items():
        text = " ".join(split_phrases(row.get(field, "")))
        for archetype in ARCHETYPES:
            matches = matched_keywords(text, KEYWORDS[archetype])
            add(archetype, weight * min(len(matches), MAX_MATCHES_PER_FIELD), field, matches)

    category = str(row.get("Category", "")).strip()
    for archetype, affinity in CATEGORY_TO_ARCHETYPE.get(category, {}).items():
        add(archetype, CATEGORY_WEIGHT * affinity, "category", [category])

    seg_strength = {a: 0.0 for a in ARCHETYPES}
    seg_matches = {a: [] for a in ARCHETYPES}
    for phrase in split_phrases(row.get("Target segments (inferred)", "")):
        for archetype, affinity in segment_map.get(phrase, {}).items():
            seg_strength[archetype] += affinity
            seg_matches[archetype].append(phrase)
    for archetype in ARCHETYPES:
        add(archetype, SEGMENT_WEIGHT * min(seg_strength[archetype], 1.0), "target_segments", seg_matches[archetype])

    scores = {f"{a}_score": round(1 - math.exp(-strengths[a]), 3) for a in ARCHETYPES}
    return scores, evidence


def build_product_personas(sheet, segment_map):
    sheet = sheet.drop_duplicates(["Brand", "Product / variant"]).reset_index(drop=True)
    unmapped = sorted({p for cell in sheet["Target segments (inferred)"] for p in split_phrases(cell)
                       if p not in segment_map})
    records = []
    for i, row in sheet.iterrows():
        scores, evidence = product_profile(row, segment_map)
        records.append({"product_id": f"S{i + 1:03d}", "brand": row["Brand"], "product": row["Product / variant"],
                        "category": row["Category"], "sub_category": row["Sub-category"],
                        **scores, **get_top_archetypes(scores),
                        "archetype_evidence": json.dumps(evidence, ensure_ascii=False)})
    return pd.DataFrame(records), unmapped


def main():
    sheet = pd.read_csv(BRANDS_PATH, encoding="utf-8-sig")
    sheet.columns = [c.strip() for c in sheet.columns]
    personas, unmapped = build_product_personas(sheet, load_segment_map())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    personas.to_csv(OUTPUT_PATH, index=False)
    if unmapped:
        print("Target-segment phrases with no archetype mapping (add to segment_archetypes.csv):", unmapped)
    print(f"Scored {len(personas)} products. Saved to {OUTPUT_PATH}")
    print(personas[["brand", "product", "primary_archetype", "secondary_archetype"]].head().to_string(index=False))


if __name__ == "__main__":
    main()
