from pathlib import Path

import json
import math
import re
import pandas as pd


# -----------------------------------
# Paths
# -----------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_EVENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "events_raw.pkl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "events_archetypes.csv"
)


# -----------------------------------
# Watch Humans archetypes
# -----------------------------------

ARCHETYPES = [
    "wellness_seeker",
    "trend_enthusiast",
    "thoughtful_buyer",
    "smart_saver",
    "quality_seeker",
    "on_the_go_shopper",
    "impulse_buyer",
    "experience_explorer",
    "everyday_planner",
    "conscious_consumer",
]


# -----------------------------------
# PredictHQ label -> archetype mapping
#
# These are OUR modelling assumptions.
# Values represent strength of association.
#
# 0   = no meaningful association
# 1.0 = very strong association
# -----------------------------------

PHQ_LABEL_TO_ARCHETYPE = {

    # ---------------------------
    # Wellness / health
    # ---------------------------

    "wellness": {
        "wellness_seeker": 1.0,
        "conscious_consumer": 0.5,
        "quality_seeker": 0.3,
    },

    "health": {
        "wellness_seeker": 0.9,
        "thoughtful_buyer": 0.4,
        "conscious_consumer": 0.4,
    },

    "fitness": {
        "wellness_seeker": 1.0,
        "on_the_go_shopper": 0.3,
        "experience_explorer": 0.3,
    },

    "running": {
        "wellness_seeker": 1.0,
        "on_the_go_shopper": 0.4,
        "experience_explorer": 0.4,
    },

    # ---------------------------
    # Fashion / beauty
    # ---------------------------

    "beauty-and-fashion": {
        "trend_enthusiast": 0.9,
        "quality_seeker": 0.7,
        "impulse_buyer": 0.5,
        "experience_explorer": 0.4,
    },

    "fashion": {
        "trend_enthusiast": 1.0,
        "quality_seeker": 0.7,
        "impulse_buyer": 0.5,
        "experience_explorer": 0.4,
    },

    # ---------------------------
    # Music / nightlife
    # ---------------------------

    "music": {
        "trend_enthusiast": 0.7,
        "experience_explorer": 0.8,
        "impulse_buyer": 0.4,
    },

    "electronic": {
        "trend_enthusiast": 0.9,
        "experience_explorer": 0.9,
        "impulse_buyer": 0.6,
    },

    "nightlife": {
        "trend_enthusiast": 0.9,
        "experience_explorer": 0.9,
        "impulse_buyer": 0.7,
        "on_the_go_shopper": 0.3,
    },

    "pop": {
        "trend_enthusiast": 0.8,
        "experience_explorer": 0.6,
        "impulse_buyer": 0.4,
    },

    "hip-hop-and-rnb-and-soul": {
        "trend_enthusiast": 0.8,
        "experience_explorer": 0.7,
        "impulse_buyer": 0.5,
    },

    # ---------------------------
    # Food / drink
    # ---------------------------

    "food": {
        "quality_seeker": 0.6,
        "experience_explorer": 0.6,
        "wellness_seeker": 0.3,
        "on_the_go_shopper": 0.3,
    },

    "food-and-beverage": {
        "quality_seeker": 0.6,
        "experience_explorer": 0.6,
        "wellness_seeker": 0.4,
        "on_the_go_shopper": 0.4,
    },

    "alcohol": {
        "trend_enthusiast": 0.5,
        "experience_explorer": 0.7,
        "impulse_buyer": 0.6,
        "nightlife": 0.0,
    },

    # ---------------------------
    # Markets / shopping
    # ---------------------------

    "market": {
        "experience_explorer": 0.8,
        "impulse_buyer": 0.6,
        "trend_enthusiast": 0.5,
        "quality_seeker": 0.4,
        "smart_saver": 0.3,
    },

    "consumer-goods": {
        "thoughtful_buyer": 0.5,
        "impulse_buyer": 0.5,
        "quality_seeker": 0.4,
        "smart_saver": 0.4,
    },

    # ---------------------------
    # Culture / immersive
    # ---------------------------

    "visual-art": {
        "experience_explorer": 0.9,
        "quality_seeker": 0.5,
        "trend_enthusiast": 0.4,
    },

    "arts-and-entertainment": {
        "experience_explorer": 0.9,
        "trend_enthusiast": 0.5,
        "quality_seeker": 0.4,
    },

    "performing-arts": {
        "experience_explorer": 0.9,
        "quality_seeker": 0.5,
    },

    # ---------------------------
    # Sustainability / outdoors
    # ---------------------------

    "nature-and-outdoor-activities": {
        "wellness_seeker": 0.7,
        "conscious_consumer": 0.8,
        "experience_explorer": 0.5,
    },

    "environment": {
        "conscious_consumer": 1.0,
        "thoughtful_buyer": 0.4,
    },

    # ---------------------------
    # Family / practical
    # ---------------------------

    "family": {
        "everyday_planner": 1.0,
        "thoughtful_buyer": 0.4,
        "smart_saver": 0.4,
    },

    # ---------------------------
    # Tech
    # ---------------------------

    "science-and-technology": {
        "trend_enthusiast": 0.6,
        "experience_explorer": 0.7,
        "thoughtful_buyer": 0.5,
        "quality_seeker": 0.4,
    },
}


# -----------------------------------
# PredictHQ category -> archetype mapping
# -----------------------------------

CATEGORY_TO_ARCHETYPE = {

    "concerts": {
        "trend_enthusiast": 0.8,
        "experience_explorer": 0.9,
        "impulse_buyer": 0.5,
    },

    "festivals": {
        "trend_enthusiast": 0.8,
        "experience_explorer": 1.0,
        "impulse_buyer": 0.6,
        "on_the_go_shopper": 0.3,
    },

    "sports": {
        "wellness_seeker": 0.6,
        "experience_explorer": 0.6,
        "on_the_go_shopper": 0.4,
    },

    "expos": {
        "thoughtful_buyer": 0.6,
        "trend_enthusiast": 0.5,
        "experience_explorer": 0.5,
        "quality_seeker": 0.4,
    },

    "conferences": {
        "thoughtful_buyer": 0.8,
        "quality_seeker": 0.5,
        "everyday_planner": 0.4,
    },

    "community": {
        "experience_explorer": 0.5,
        "conscious_consumer": 0.5,
        "everyday_planner": 0.4,
    },

    "performing-arts": {
        "experience_explorer": 0.9,
        "quality_seeker": 0.5,
    },
}


# -----------------------------------
# Title / description keywords
#
# These are only supporting evidence.
# -----------------------------------

TEXT_KEYWORDS = {

    "wellness_seeker": [
        "wellness",
        "health",
        "healthy",
        "fitness",
        "pilates",
        "yoga",
        "running",
        "run club",
        "mindfulness",
        "meditation",
        "functional",
    ],

    "trend_enthusiast": [
        "viral",
        "trending",
        "trend",
        "launch",
        "launching",
        "limited edition",
        "limited drop",
        "drop",
        "exclusive",
        "fashion",
        "streetwear",
        "social media",
        "influencer",
    ],

    "thoughtful_buyer": [
        "expert",
        "educational",
        "workshop",
        "demonstration",
        "talk",
        "conference",
        "seminar",
        "masterclass",
    ],

    "smart_saver": [
        "discount",
        "deal",
        "sale",
        "free",
        "affordable",
        "value",
        "bargain",
    ],

    "quality_seeker": [
        "premium",
        "luxury",
        "high-end",
        "artisan",
        "artisanal",
        "designer",
        "exclusive",
        "fine dining",
    ],

    "on_the_go_shopper": [
        "grab-and-go",
        "grab and go",
        "convenient",
        "convenience",
        "quick",
        "commuter",
        "street food",
    ],

    "impulse_buyer": [
        "limited",
        "exclusive",
        "flash",
        "sale",
        "deal",
        "drop",
        "giveaway",
    ],

    "experience_explorer": [
        "immersive",
        "interactive",
        "experience",
        "experiential",
        "installation",
        "pop-up",
        "popup",
        "workshop",
        "festival",
    ],

    "everyday_planner": [
        "family",
        "household",
        "practical",
        "community",
        "children",
        "parents",
    ],

    "conscious_consumer": [
        "sustainable",
        "sustainability",
        "ethical",
        "eco-friendly",
        "eco friendly",
        "recycled",
        "zero waste",
        "plant-based",
        "plant based",
    ],
}


# Scores are heuristic affinities, not probabilities or measured audience shares.
# Specific text outweighs broad categories; independent scores need not sum to 1.
FIELD_WEIGHTS = {
    "title": 0.65,
    "description": 0.40,
    "entity_names": 0.25,
    "entity_types": 0.15,
    "type": 0.30,
}

# Extend vocabulary to cover event types present in the source dataset.
TEXT_KEYWORDS["experience_explorer"] += [
    "concert", "comedy", "theatre", "theater", "salsa", "live music", "tasting",
]
TEXT_KEYWORDS["trend_enthusiast"] += ["nightlife", "electronic", "dj"]
TEXT_KEYWORDS["conscious_consumer"] += ["vegan", "organic", "repair", "reuse"]
TEXT_KEYWORDS["smart_saver"].remove("free")
TEXT_KEYWORDS["smart_saver"] += ["free entry", "free admission", "free event"]


def normalise_text(value):
    if isinstance(value, (list, tuple)):
        value = " ".join(item for item in value if isinstance(item, str))
    if not isinstance(value, str):
        return ""
    return " ".join(re.sub(r"[^\w]+", " ", value.casefold()).split())


def matched_keywords(value, keywords):
    text = normalise_text(value)
    if text == "sourced from predicthq com":
        return []
    # Longest phrases first: don't count 'limited' again inside 'limited edition'.
    matches = []
    for keyword in sorted(set(map(normalise_text, keywords)), key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
        if keyword and re.search(pattern, text):
            matches.append(keyword)
            text = re.sub(pattern, " ", text)
    return matches


def event_profile(row):
    evidence = {archetype: [] for archetype in ARCHETYPES}
    strengths = {archetype: 0.0 for archetype in ARCHETYPES}

    def add(archetype, strength, source, matches):
        if strength > 0:
            strengths[archetype] += strength
            evidence[archetype].append({"source": source, "matches": matches})

    for field, weight in FIELD_WEIGHTS.items():
        for archetype, keywords in TEXT_KEYWORDS.items():
            matches = matched_keywords(row.get(field), keywords)
            # Cap evidence from verbose descriptions or keyword-heavy titles.
            add(archetype, weight * min(len(matches), 3), field, matches)

    category = normalise_text(row.get("category")).replace(" ", "-")
    for archetype, affinity in CATEGORY_TO_ARCHETYPE.get(category, {}).items():
        add(archetype, 0.20 * affinity, "category", [category])

    label_weights = row.get("phq_label_weights")
    if not isinstance(label_weights, dict):
        labels = row.get("phq_labels", [])
        label_weights = {label: 1.0 for label in labels if isinstance(label, str)} if isinstance(labels, (list, tuple)) else {}

    label_strengths = {archetype: 0.0 for archetype in ARCHETYPES}
    label_matches = {archetype: [] for archetype in ARCHETYPES}
    for label, raw_weight in label_weights.items():
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(weight) or weight <= 0:
            continue
        weight = min(weight, 1.0)
        label = normalise_text(label).replace(" ", "-")
        mappings = PHQ_LABEL_TO_ARCHETYPE.get(label, {})
        for archetype in ARCHETYPES:
            affinity = mappings.get(archetype, 0.0)
            if not affinity and matched_keywords(label, TEXT_KEYWORDS[archetype]):
                affinity = 0.6
            if affinity:
                label_strengths[archetype] += weight * affinity
                label_matches[archetype].append(label)

    for archetype in ARCHETYPES:
        add(archetype, 0.45 * min(label_strengths[archetype], 1.0),
            "phq_labels", label_matches[archetype])

    # Saturation keeps scores comparable across events without forcing a winner to 1.
    scores = {
        f"{archetype}_score": round(1 - math.exp(-strengths[archetype]), 3)
        for archetype in ARCHETYPES
    }
    return scores, evidence


def calculate_event_archetype_scores(row):
    return event_profile(row)[0]


SCORE_COLUMNS = [f"{archetype}_score" for archetype in ARCHETYPES]
EVENT_COLUMNS = [
    "event_id", "title", "description", "category", "start_local", "end_local",
    "longitude", "latitude", "rank", "local_rank", "phq_attendance",
    "predicted_event_spend",
]


def get_top_archetypes(row):
    supported = sorted(
        (archetype for archetype in ARCHETYPES if row[f"{archetype}_score"] > 0),
        key=lambda archetype: row[f"{archetype}_score"], reverse=True,
    )
    return {
        "primary_archetype": supported[0] if supported else None,
        "secondary_archetype": supported[1] if len(supported) > 1 else None,
    }


def build_event_personas(events):
    records = []
    for _, row in events.iterrows():
        scores, evidence = event_profile(row)
        records.append({
            **scores, **get_top_archetypes(scores),
            "archetype_evidence": json.dumps(evidence, ensure_ascii=False),
        })
    profiles = pd.DataFrame(records, columns=[
        *SCORE_COLUMNS, "primary_archetype", "secondary_archetype", "archetype_evidence",
    ])
    return pd.concat([
        events.reindex(columns=EVENT_COLUMNS).reset_index(drop=True), profiles,
    ], axis=1)


def main():
    events = pd.read_pickle(RAW_EVENTS_PATH)
    personas = build_event_personas(events)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    personas.to_csv(OUTPUT_PATH, index=False)
    print(f"Processed {len(personas)} events. Saved to {OUTPUT_PATH}")
    print(personas[["title", *SCORE_COLUMNS]].head().to_string(index=False))


if __name__ == "__main__":
    main()
