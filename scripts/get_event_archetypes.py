from pathlib import Path

import json
import math
import re

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_EVENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "events_raw.pkl"
)

WATCH_HUMANS_PATH = (
    PROJECT_ROOT
    / "data" /'processed'
    / "watch_humans_synthetic.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "event_archetypes.csv"
)

ARCHETYPE_PROFILE_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "watch_humans_archetype_profiles.csv"
)


# ============================================================
# WATCH HUMANS ARCHETYPES
# ============================================================

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


ARCHETYPE_SCORE_COLUMNS = [
    f"{archetype}_score"
    for archetype in ARCHETYPES
]


# ============================================================
# SHARED BEHAVIOURAL FEATURE SPACE
#
# These columns already exist in the Watch Humans dataset.
# We infer these SAME features for each event.
# ============================================================

BEHAVIOUR_COLUMNS = [
    "health_consciousness",
    "novelty_seeking",
    "social_influence",
    "price_sensitivity",
    "quality_orientation",
    "convenience_orientation",
    "impulsivity",
    "experience_seeking",
    "planning_orientation",
    "sustainability_orientation",
]


# ============================================================
# PRODUCT AFFINITY COLUMNS
#
# These are not needed to score events yet.
# We save archetype-level averages because they will be useful
# later when matching archetypes -> brands/products.
# ============================================================

PRODUCT_AFFINITY_COLUMNS = [
    "functional_drinks_affinity",
    "healthy_snacks_affinity",
    "streetwear_affinity",
    "skincare_affinity",
    "premium_food_affinity",
    "sustainable_products_affinity",
    "viral_products_affinity",
    "grab_and_go_affinity",
    "premium_beauty_affinity",
    "discount_products_affinity",
]


# ============================================================
# PREDICTHQ LABEL -> BEHAVIOURAL FEATURE MAPPING
#
# IMPORTANT:
# We are NOT mapping labels directly to archetypes anymore.
#
# Instead:
# PredictHQ -> behaviour
# Watch Humans -> archetype definitions
#
# Values indicate how strongly a label suggests a behaviour.
# ============================================================

PHQ_LABEL_TO_BEHAVIOUR = {

    # -------------------------
    # Health / wellness
    # -------------------------

    "wellness": {
        "health_consciousness": 1.0,
        "sustainability_orientation": 0.4,
        "quality_orientation": 0.3,
    },

    "health": {
        "health_consciousness": 1.0,
        "planning_orientation": 0.3,
        "quality_orientation": 0.3,
    },

    "fitness": {
        "health_consciousness": 0.9,
        "experience_seeking": 0.4,
        "convenience_orientation": 0.2,
    },

    "running": {
        "health_consciousness": 0.9,
        "experience_seeking": 0.5,
        "social_influence": 0.3,
    },

    "nature-and-outdoor-activities": {
        "health_consciousness": 0.6,
        "experience_seeking": 0.6,
        "sustainability_orientation": 0.7,
    },

    # -------------------------
    # Fashion / beauty
    # -------------------------

    "beauty-and-fashion": {
        "novelty_seeking": 0.8,
        "social_influence": 0.8,
        "quality_orientation": 0.7,
        "impulsivity": 0.5,
        "experience_seeking": 0.5,
    },

    "fashion": {
        "novelty_seeking": 0.8,
        "social_influence": 0.8,
        "quality_orientation": 0.7,
        "impulsivity": 0.5,
    },

    # -------------------------
    # Music / nightlife
    # -------------------------

    "music": {
        "novelty_seeking": 0.5,
        "social_influence": 0.6,
        "experience_seeking": 0.8,
        "impulsivity": 0.3,
    },

    "electronic": {
        "novelty_seeking": 0.8,
        "social_influence": 0.7,
        "experience_seeking": 0.9,
        "impulsivity": 0.5,
    },

    "nightlife": {
        "novelty_seeking": 0.8,
        "social_influence": 0.8,
        "experience_seeking": 0.9,
        "impulsivity": 0.7,
        "planning_orientation": -0.2,
    },

    "pop": {
        "novelty_seeking": 0.6,
        "social_influence": 0.8,
        "experience_seeking": 0.6,
    },

    "hip-hop-and-rnb-and-soul": {
        "novelty_seeking": 0.6,
        "social_influence": 0.7,
        "experience_seeking": 0.7,
    },

    # -------------------------
    # Food and drink
    # -------------------------

    "food": {
        "quality_orientation": 0.5,
        "experience_seeking": 0.6,
        "convenience_orientation": 0.3,
    },

    "food-and-beverage": {
        "quality_orientation": 0.5,
        "experience_seeking": 0.6,
        "convenience_orientation": 0.4,
    },

    "alcohol": {
        "experience_seeking": 0.6,
        "social_influence": 0.5,
        "impulsivity": 0.5,
        "health_consciousness": -0.2,
    },

    # -------------------------
    # Shopping / markets
    # -------------------------

    "market": {
        "experience_seeking": 0.7,
        "novelty_seeking": 0.5,
        "impulsivity": 0.4,
        "social_influence": 0.3,
    },

    "consumer-goods": {
        "quality_orientation": 0.4,
        "planning_orientation": 0.4,
        "impulsivity": 0.3,
    },

    # -------------------------
    # Arts / culture
    # -------------------------

    "visual-art": {
        "experience_seeking": 0.9,
        "novelty_seeking": 0.6,
        "quality_orientation": 0.4,
    },

    "arts-and-entertainment": {
        "experience_seeking": 0.9,
        "novelty_seeking": 0.5,
        "social_influence": 0.4,
    },

    "performing-arts": {
        "experience_seeking": 0.8,
        "quality_orientation": 0.5,
    },

    # -------------------------
    # Environment
    # -------------------------

    "environment": {
        "sustainability_orientation": 1.0,
        "planning_orientation": 0.3,
        "health_consciousness": 0.3,
    },

    # -------------------------
    # Family
    # -------------------------

    "family": {
        "planning_orientation": 0.9,
        "price_sensitivity": 0.4,
        "convenience_orientation": 0.5,
        "impulsivity": -0.3,
    },

    # -------------------------
    # Technology
    # -------------------------

    "science-and-technology": {
        "novelty_seeking": 0.7,
        "experience_seeking": 0.6,
        "quality_orientation": 0.4,
    },
}


# ============================================================
# PREDICTHQ CATEGORY -> BEHAVIOURAL FEATURES
#
# Broader than PHQ labels, so category evidence gets less weight.
# ============================================================

CATEGORY_TO_BEHAVIOUR = {

    "concerts": {
        "experience_seeking": 0.8,
        "social_influence": 0.6,
        "novelty_seeking": 0.5,
    },

    "festivals": {
        "experience_seeking": 0.9,
        "social_influence": 0.7,
        "novelty_seeking": 0.6,
        "impulsivity": 0.4,
    },

    "sports": {
        "health_consciousness": 0.5,
        "experience_seeking": 0.5,
        "social_influence": 0.3,
    },

    "expos": {
        "novelty_seeking": 0.5,
        "planning_orientation": 0.4,
        "quality_orientation": 0.4,
        "experience_seeking": 0.4,
    },

    "conferences": {
        "planning_orientation": 0.7,
        "quality_orientation": 0.5,
        "impulsivity": -0.3,
    },

    "community": {
        "social_influence": 0.4,
        "planning_orientation": 0.4,
        "sustainability_orientation": 0.3,
    },

    "performing-arts": {
        "experience_seeking": 0.8,
        "quality_orientation": 0.5,
    },
}


# ============================================================
# TEXT -> BEHAVIOURAL FEATURES
#
# Title and description provide additional semantic evidence.
# ============================================================

TEXT_KEYWORDS = {

    "health_consciousness": [
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
        "nutrition",
    ],

    "novelty_seeking": [
        "new",
        "launch",
        "launching",
        "limited edition",
        "limited drop",
        "debut",
        "exclusive",
        "immersive",
        "interactive",
        "innovation",
        "experimental",
    ],

    "social_influence": [
        "viral",
        "trending",
        "trend",
        "social media",
        "influencer",
        "dj",
        "festival",
        "nightlife",
        "party",
        "community",
    ],

    "price_sensitivity": [
        "discount",
        "deal",
        "sale",
        "affordable",
        "value",
        "bargain",
        "free entry",
        "free admission",
    ],

    "quality_orientation": [
        "premium",
        "luxury",
        "high-end",
        "artisan",
        "artisanal",
        "designer",
        "exclusive",
        "fine dining",
        "curated",
    ],

    "convenience_orientation": [
        "grab-and-go",
        "grab and go",
        "convenient",
        "convenience",
        "quick",
        "commuter",
        "street food",
    ],

    "impulsivity": [
        "limited",
        "exclusive",
        "flash sale",
        "deal",
        "drop",
        "giveaway",
        "one night only",
    ],

    "experience_seeking": [
        "immersive",
        "interactive",
        "experience",
        "experiential",
        "installation",
        "pop-up",
        "popup",
        "festival",
        "concert",
        "live music",
        "tasting",
        "workshop",
        "exhibition",
    ],

    "planning_orientation": [
        "family",
        "conference",
        "seminar",
        "scheduled",
        "educational",
        "masterclass",
        "community",
    ],

    "sustainability_orientation": [
        "sustainable",
        "sustainability",
        "ethical",
        "eco-friendly",
        "eco friendly",
        "recycled",
        "zero waste",
        "plant-based",
        "plant based",
        "vegan",
        "organic",
        "repair",
        "reuse",
    ],
}


# ============================================================
# TEXT HELPERS
# ============================================================

def normalise_text(value):

    if isinstance(value, (list, tuple)):
        value = " ".join(
            item
            for item in value
            if isinstance(item, str)
        )

    if not isinstance(value, str):
        return ""

    return " ".join(
        re.sub(
            r"[^\w]+",
            " ",
            value.casefold()
        ).split()
    )


def matched_keywords(value, keywords):

    text = normalise_text(value)

    if text == "sourced from predicthq com":
        return []

    matches = []

    # Match longer phrases first
    for keyword in sorted(
        set(map(normalise_text, keywords)),
        key=len,
        reverse=True,
    ):

        if not keyword:
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(keyword)
            + r"(?!\w)"
        )

        if re.search(pattern, text):

            matches.append(keyword)

            # Prevent double-counting overlapping terms
            text = re.sub(
                pattern,
                " ",
                text,
            )

    return matches


# ============================================================
# LOAD AND VALIDATE WATCH HUMANS DATA
# ============================================================

def load_watch_humans():

    df = pd.read_csv(
        WATCH_HUMANS_PATH
    )

    required_columns = (
        ARCHETYPE_SCORE_COLUMNS
        + BEHAVIOUR_COLUMNS
    )

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Watch Humans dataset is missing required columns: "
            + ", ".join(missing)
        )

    numeric_columns = (
        ARCHETYPE_SCORE_COLUMNS
        + BEHAVIOUR_COLUMNS
        + PRODUCT_AFFINITY_COLUMNS
    )

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    return df


# ============================================================
# BUILD ARCHETYPE PROTOTYPES FROM WATCH HUMANS
#
# IMPORTANT:
#
# We use each person's continuous archetype score as the weight.
#
# Therefore someone with:
#
# trend_enthusiast_score = 0.9
#
# contributes much more to the Trend Enthusiast prototype than
# someone with trend_enthusiast_score = 0.2.
#
# We do NOT rely only on primary_archetype.
# ============================================================

def build_archetype_profiles(watch_humans_df):

    profile_columns = (
        BEHAVIOUR_COLUMNS
        + [
            column
            for column in PRODUCT_AFFINITY_COLUMNS
            if column in watch_humans_df.columns
        ]
    )

    profiles = []

    for archetype in ARCHETYPES:

        score_column = (
            f"{archetype}_score"
        )

        weights = (
            watch_humans_df[score_column]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        profile = {
            "archetype": archetype
        }

        if weights.sum() == 0:

            for column in profile_columns:
                profile[column] = np.nan

        else:

            for column in profile_columns:

                values = (
                    watch_humans_df[column]
                    .to_numpy(dtype=float)
                )

                valid = np.isfinite(values)

                if not valid.any():
                    profile[column] = np.nan
                    continue

                profile[column] = np.average(
                    values[valid],
                    weights=weights[valid],
                )

        profiles.append(profile)

    return (
        pd.DataFrame(profiles)
        .set_index("archetype")
    )


# ============================================================
# EVENT -> BEHAVIOURAL PROFILE
#
# This is the ONLY translation layer.
#
# PredictHQ fields are converted into the SAME behavioural
# dimensions contained in Watch Humans.
#
# Archetypes themselves are NOT assigned here.
# ============================================================

def build_event_behaviour_profile(row):

    # Start at a neutral midpoint.
    #
    # Absence of evidence for a trait does NOT mean the audience
    # has zero of that trait.
    values = {
        feature: 0.5
        for feature in BEHAVIOUR_COLUMNS
    }

    evidence = {
        feature: []
        for feature in BEHAVIOUR_COLUMNS
    }

    adjustments = {
        feature: 0.0
        for feature in BEHAVIOUR_COLUMNS
    }

    def add(feature, amount, source, match):

        if feature not in adjustments:
            return

        adjustments[feature] += amount

        evidence[feature].append(
            {
                "source": source,
                "match": match,
                "amount": round(amount, 3),
            }
        )

    # --------------------------------------------------------
    # 1. PredictHQ PHQ labels
    # --------------------------------------------------------

    label_weights = row.get(
        "phq_label_weights"
    )

    if not isinstance(label_weights, dict):

        labels = row.get(
            "phq_labels",
            []
        )

        if isinstance(
            labels,
            (list, tuple),
        ):

            label_weights = {
                label: 1.0
                for label in labels
                if isinstance(label, str)
            }

        else:
            label_weights = {}

    for label, raw_weight in label_weights.items():

        try:
            phq_weight = float(
                raw_weight
            )

        except (TypeError, ValueError):
            continue

        if (
            not math.isfinite(phq_weight)
            or phq_weight <= 0
        ):
            continue

        phq_weight = min(
            phq_weight,
            1.0,
        )

        normalised_label = (
            normalise_text(label)
            .replace(" ", "-")
        )

        mappings = (
            PHQ_LABEL_TO_BEHAVIOUR.get(
                normalised_label,
                {}
            )
        )

        for feature, association in mappings.items():

            add(
                feature=feature,
                amount=(
                    0.55
                    * phq_weight
                    * association
                ),
                source="phq_label",
                match=normalised_label,
            )

    # --------------------------------------------------------
    # 2. PredictHQ category
    # --------------------------------------------------------

    category = (
        normalise_text(
            row.get("category")
        )
        .replace(" ", "-")
    )

    category_mappings = (
        CATEGORY_TO_BEHAVIOUR.get(
            category,
            {}
        )
    )

    for feature, association in category_mappings.items():

        add(
            feature=feature,
            amount=(
                0.20
                * association
            ),
            source="category",
            match=category,
        )

    # --------------------------------------------------------
    # 3. Title
    # --------------------------------------------------------

    title = row.get(
        "title",
        ""
    )

    for feature, keywords in TEXT_KEYWORDS.items():

        matches = matched_keywords(
            title,
            keywords,
        )

        # Cap number of title contributions
        for match in matches[:3]:

            add(
                feature=feature,
                amount=0.16,
                source="title",
                match=match,
            )

    # --------------------------------------------------------
    # 4. Description
    # --------------------------------------------------------

    description = row.get(
        "description",
        ""
    )

    for feature, keywords in TEXT_KEYWORDS.items():

        matches = matched_keywords(
            description,
            keywords,
        )

        # Description is weaker evidence
        for match in matches[:3]:

            add(
                feature=feature,
                amount=0.08,
                source="description",
                match=match,
            )

    # --------------------------------------------------------
    # 5. Entity names
    # --------------------------------------------------------

    entity_names = row.get(
        "entity_names",
        []
    )

    for feature, keywords in TEXT_KEYWORDS.items():

        matches = matched_keywords(
            entity_names,
            keywords,
        )

        for match in matches[:2]:

            add(
                feature=feature,
                amount=0.06,
                source="entity_names",
                match=match,
            )

    # --------------------------------------------------------
    # Convert adjustments into final 0-1 features
    #
    # Positive evidence raises from 0.5.
    # Negative evidence lowers from 0.5.
    # --------------------------------------------------------

    for feature in BEHAVIOUR_COLUMNS:

        adjustment = adjustments[
            feature
        ]

        if adjustment >= 0:

            values[feature] = (
                0.5
                + 0.5
                * (
                    1
                    - math.exp(
                        -adjustment
                    )
                )
            )

        else:

            values[feature] = (
                0.5
                - 0.5
                * (
                    1
                    - math.exp(
                        adjustment
                    )
                )
            )

        values[feature] = float(
            np.clip(
                values[feature],
                0,
                1,
            )
        )

    return values, evidence


# ============================================================
# EVENT BEHAVIOUR -> ARCHETYPE SIMILARITY
#
# Compare each event with the Watch Humans-derived archetype
# prototypes.
#
# Similarity:
#
#     1 - RMSE
#
# Both vectors are on 0-1, so resulting similarity is also
# approximately 0-1.
#
# Higher = event audience looks more like that archetype.
# ============================================================

def score_event_against_archetypes(
    event_behaviour,
    archetype_profiles,
):

    event_vector = np.array(
        [
            event_behaviour[column]
            for column in BEHAVIOUR_COLUMNS
        ],
        dtype=float,
    )

    scores = {}

    for archetype in ARCHETYPES:

        prototype = (
            archetype_profiles
            .loc[
                archetype,
                BEHAVIOUR_COLUMNS
            ]
            .to_numpy(
                dtype=float
            )
        )

        valid = (
            np.isfinite(event_vector)
            & np.isfinite(prototype)
        )

        if not valid.any():

            scores[
                f"{archetype}_score"
            ] = np.nan

            continue

        rmse = np.sqrt(
            np.mean(
                (
                    event_vector[valid]
                    - prototype[valid]
                )
                ** 2
            )
        )

        similarity = 1 - rmse

        scores[
            f"{archetype}_score"
        ] = round(
            float(
                np.clip(
                    similarity,
                    0,
                    1,
                )
            ),
            3,
        )

    return scores


# ============================================================
# PRIMARY / SECONDARY ARCHETYPE
# ============================================================

def get_top_archetypes(scores):

    valid_scores = {
        archetype: scores.get(
            f"{archetype}_score"
        )
        for archetype in ARCHETYPES
    }

    valid_scores = {
        archetype: score
        for archetype, score
        in valid_scores.items()
        if pd.notna(score)
    }

    ranked = sorted(
        valid_scores,
        key=valid_scores.get,
        reverse=True,
    )

    return {
        "primary_archetype":
            ranked[0]
            if ranked
            else None,

        "secondary_archetype":
            ranked[1]
            if len(ranked) > 1
            else None,
    }


# ============================================================
# BUILD EVENT PERSONA DATASET
# ============================================================

def build_event_personas(
    events_df,
    archetype_profiles,
):

    records = []

    for _, row in events_df.iterrows():

        (
            behaviour_profile,
            evidence,
        ) = build_event_behaviour_profile(
            row
        )

        archetype_scores = (
            score_event_against_archetypes(
                behaviour_profile,
                archetype_profiles,
            )
        )

        top_archetypes = (
            get_top_archetypes(
                archetype_scores
            )
        )

        record = {

            # Event identity
            "event_id":
                row.get("event_id"),

            "title":
                row.get("title"),

            "description":
                row.get("description"),

            "category":
                row.get("category"),

            "start_local":
                row.get("start_local"),

            "end_local":
                row.get("end_local"),

            # Location
            "longitude":
                row.get("longitude"),

            "latitude":
                row.get("latitude"),

            # Opportunity variables
            "rank":
                row.get("rank"),

            "local_rank":
                row.get("local_rank"),

            "phq_attendance":
                row.get("phq_attendance"),

            "predicted_event_spend":
                row.get(
                    "predicted_event_spend"
                ),

            # Keep original PHQ semantic data
            "phq_labels":
                row.get("phq_labels"),

            # Derived behavioural profile
            **{
                f"event_{feature}":
                    round(value, 3)
                for feature, value
                in behaviour_profile.items()
            },

            # Watch Humans-derived archetype scores
            **archetype_scores,

            **top_archetypes,

            # Explainability / debugging
            "behaviour_evidence":
                json.dumps(
                    evidence,
                    ensure_ascii=False,
                ),
        }

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load Watch Humans
    # --------------------------------------------------------

    print(
        "\nLoading Watch Humans dataset..."
    )

    watch_humans_df = (
        load_watch_humans()
    )

    print(
        f"Loaded "
        f"{len(watch_humans_df)} "
        f"Watch Humans consumers."
    )

    # --------------------------------------------------------
    # Learn archetype profiles
    # --------------------------------------------------------

    archetype_profiles = (
        build_archetype_profiles(
            watch_humans_df
        )
    )

    ARCHETYPE_PROFILE_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    archetype_profiles.to_csv(
        ARCHETYPE_PROFILE_OUTPUT_PATH
    )

    print(
        "\nWatch Humans-derived "
        "archetype profiles:"
    )

    print(
        archetype_profiles[
            BEHAVIOUR_COLUMNS
        ]
        .round(3)
        .to_string()
    )

    # --------------------------------------------------------
    # Load raw PredictHQ events
    # --------------------------------------------------------

    print(
        "\nLoading raw PredictHQ events..."
    )

    events_df = pd.read_pickle(
        RAW_EVENTS_PATH
    )

    print(
        f"Loaded {len(events_df)} events."
    )

    # --------------------------------------------------------
    # Score events
    # --------------------------------------------------------

    event_personas_df = (
        build_event_personas(
            events_df,
            archetype_profiles,
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    event_personas_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        f"\nProcessed "
        f"{len(event_personas_df)} events."
    )

    print(
        f"Saved event archetypes to:\n"
        f"{OUTPUT_PATH}"
    )

    # --------------------------------------------------------
    # Inspect results
    # --------------------------------------------------------

    print(
        "\nPrimary archetype distribution:"
    )

    print(
        event_personas_df[
            "primary_archetype"
        ]
        .value_counts(
            dropna=False
        )
    )

    print(
        "\nExample event profiles:"
    )

    display_columns = [
        "title",
        "category",
        "primary_archetype",
        "secondary_archetype",
        *ARCHETYPE_SCORE_COLUMNS,
    ]

    print(
        event_personas_df[
            display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()