from pathlib import Path
import subprocess
import sys

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

SCRIPTS_MAPPING_DIR = SCRIPTS_DIR / "data_mapping"
EVENT_MAPPING_SCRIPT = SCRIPTS_MAPPING_DIR / "event_archetypes.py"
PRODUCT_MAPPING_SCRIPT = SCRIPTS_DIR / "build_brand_features.py"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"



# ------------------------------------------------------------
# EVENT TO TEST
# ------------------------------------------------------------

# Change this to whatever ID you use for the manually
# added EAT Hack event.
TARGET_EVENT_ID = "manual_eat_hack_2026"

# Fallback if you prefer finding it by title.
TARGET_EVENT_TITLE = "EAT Hack"


# ------------------------------------------------------------
# INPUT / OUTPUT FILES
# ------------------------------------------------------------

EVENT_ARCHETYPES_PATH = (
    PROCESSED_DIR
    / "events_archetypes.csv"
)

PRODUCT_ARCHETYPES_PATH = (
    PROJECT_ROOT
    / "brand_products.csv"
)

RECOMMENDATIONS_PATH = (
    OUTPUTS_DIR
    / "eat_hack_product_recommendations.csv"
)


# ============================================================
# ARCHETYPE FEATURE SPACE
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

SCORE_COLUMNS = [
    f"{archetype}_score"
    for archetype in ARCHETYPES
]


# ============================================================
# RUN AN EXISTING SCRIPT
# ============================================================

def run_script(script_path):
    script_path = Path(script_path)
    if not script_path.is_absolute():
        script_path = SCRIPTS_DIR / script_path

    if not script_path.exists():
        raise FileNotFoundError(
            f"Could not find script: {script_path}"
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Running {script_path.relative_to(PROJECT_ROOT)}"
    )

    print(
        "=" * 70
    )

    subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


# ============================================================
# VALIDATE ARCHETYPE DATA
# ============================================================

def validate_archetype_columns(
    df,
    dataset_name,
):

    missing = [
        column
        for column in SCORE_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{dataset_name} is missing archetype columns:\n"
            + "\n".join(missing)
        )


# ============================================================
# FIND TARGET EVENT
# ============================================================

def get_target_event(events_df):

    # First try event ID
    if "event_id" in events_df.columns:

        matches = events_df[
            events_df["event_id"]
            == TARGET_EVENT_ID
        ]

        if len(matches) > 0:
            return matches.iloc[0]

    # Fall back to title
    if "title" in events_df.columns:

        matches = events_df[
            events_df["title"]
            .fillna("")
            .str.casefold()
            == TARGET_EVENT_TITLE.casefold()
        ]

        if len(matches) > 0:
            return matches.iloc[0]

    raise ValueError(
        f"Could not find target event "
        f"'{TARGET_EVENT_TITLE}' "
        f"or ID '{TARGET_EVENT_ID}'."
    )


# ============================================================
# WORK OUT PRODUCT COLUMN NAMES
# ============================================================

def get_product_name_column(products_df):

    candidates = [
        "product_name",
        "product",
        "brand_name",
        "name",
    ]

    for column in candidates:

        if column in products_df.columns:
            return column

    raise ValueError(
        "Could not find a product name column. "
        "Expected one of: "
        + ", ".join(candidates)
    )


def get_product_id_column(products_df):

    candidates = [
        "product_id",
        "brand_id",
        "id",
    ]

    for column in candidates:

        if column in products_df.columns:
            return column

    return None


# ============================================================
# MATCH EVENT TO PRODUCTS
# ============================================================

def match_event_to_products(
    event,
    products_df,
):

    validate_archetype_columns(
        products_df,
        "Products dataset",
    )

    product_name_col = (
        get_product_name_column(
            products_df
        )
    )

    product_id_col = (
        get_product_id_column(
            products_df
        )
    )

    # --------------------------------------------------------
    # Event vector
    # --------------------------------------------------------

    event_vector = (
        event[SCORE_COLUMNS]
        .astype(float)
        .fillna(0)
        .to_numpy()
        .reshape(1, -1)
    )

    # --------------------------------------------------------
    # Product vectors
    # --------------------------------------------------------

    product_vectors = (
        products_df[SCORE_COLUMNS]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .fillna(0)
        .to_numpy()
    )

    # --------------------------------------------------------
    # Cosine similarity
    # --------------------------------------------------------

    similarities = cosine_similarity(
        event_vector,
        product_vectors,
    )[0]

    recommendations = (
        products_df.copy()
    )

    recommendations[
        "persona_fit"
    ] = similarities

    recommendations[
        "persona_fit_pct"
    ] = (
        recommendations[
            "persona_fit"
        ]
        * 100
    ).round(1)

    # Add event context
    recommendations[
        "event_id"
    ] = event.get("event_id")

    recommendations[
        "event_title"
    ] = event.get("title")

    # Clean output names
    recommendations[
        "recommended_product"
    ] = recommendations[
        product_name_col
    ]

    if product_id_col:

        recommendations[
            "recommended_product_id"
        ] = recommendations[
            product_id_col
        ]

    # Highest fit first
    recommendations = (
        recommendations
        .sort_values(
            "persona_fit",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    recommendations[
        "rank"
    ] = (
        recommendations.index
        + 1
    )

    return recommendations


# ============================================================
# OPTIONAL: BUILD A DIVERSE POP-UP ASSORTMENT
# ============================================================

def select_diverse_assortment(
    recommendations,
    max_products=5,
):

    # If teammates provide category information,
    # avoid selecting 5 nearly identical products.

    if "category" not in recommendations.columns:

        return (
            recommendations
            .head(max_products)
            .copy()
        )

    selected_rows = []
    used_categories = set()

    for _, row in recommendations.iterrows():

        category = row.get(
            "category"
        )

        # Take the best product from each category first
        if pd.notna(category):

            if category in used_categories:
                continue

            used_categories.add(
                category
            )

        selected_rows.append(
            row
        )

        if len(selected_rows) == max_products:
            break

    # If there aren't enough categories,
    # fill remaining slots with highest-ranked products.
    if len(selected_rows) < max_products:

        selected_names = {
            row["recommended_product"]
            for row in selected_rows
        }

        for _, row in recommendations.iterrows():

            if (
                row["recommended_product"]
                in selected_names
            ):
                continue

            selected_rows.append(
                row
            )

            if len(selected_rows) == max_products:
                break

    return pd.DataFrame(
        selected_rows
    ).reset_index(drop=True)


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print(
        "\nRGC POP-UP RECOMMENDATION PIPELINE"
    )

    # --------------------------------------------------------
    # STEP 1:
    # Run event -> archetype scoring
    #
    # This script:
    # - loads events_raw.pkl
    # - loads Watch Humans
    # - derives Watch Humans archetype prototypes
    # - scores every event
    # --------------------------------------------------------

    run_script(EVENT_MAPPING_SCRIPT)

    # --------------------------------------------------------
    # STEP 2:
    # Optionally rebuild brand/product features
    # --------------------------------------------------------

    run_script(PRODUCT_MAPPING_SCRIPT)

    # --------------------------------------------------------
    # STEP 3:
    # Load event archetypes
    # --------------------------------------------------------

    if not EVENT_ARCHETYPES_PATH.exists():

        raise FileNotFoundError(
            f"Missing event archetypes file:\n"
            f"{EVENT_ARCHETYPES_PATH}"
        )

    events_df = pd.read_csv(
        EVENT_ARCHETYPES_PATH
    )

    validate_archetype_columns(
        events_df,
        "Events dataset",
    )

    # --------------------------------------------------------
    # STEP 4:
    # Find EAT Hack
    # --------------------------------------------------------

    event = get_target_event(
        events_df
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "TARGET EVENT"
    )

    print(
        "=" * 70
    )

    print(
        event["title"]
    )

    print(
        "\nEvent archetype profile:"
    )

    event_scores = (
        event[SCORE_COLUMNS]
        .astype(float)
        .sort_values(
            ascending=False
        )
    )

    for column, score in event_scores.items():

        archetype_name = (
            column
            .replace(
                "_score",
                "",
            )
            .replace(
                "_",
                " ",
            )
            .title()
        )

        print(
            f"{archetype_name:25s} "
            f"{score:.3f}"
        )

    # --------------------------------------------------------
    # STEP 5:
    # Load product / brand archetypes
    # --------------------------------------------------------

    if not PRODUCT_ARCHETYPES_PATH.exists():

        raise FileNotFoundError(
            "\nProduct archetype file not found:\n"
            f"{PRODUCT_ARCHETYPES_PATH}\n\n"
            "Run scripts/build_brand_features.py to generate the product table."
        )

    products_df = pd.read_csv(
        PRODUCT_ARCHETYPES_PATH
    ).rename(columns={
        f"arch_{archetype}": f"{archetype}_score"
        for archetype in ARCHETYPES
    })

    # --------------------------------------------------------
    # STEP 6:
    # Match event -> products
    # --------------------------------------------------------

    recommendations = (
        match_event_to_products(
            event,
            products_df,
        )
    )

    # --------------------------------------------------------
    # STEP 7:
    # Select final diverse assortment
    # --------------------------------------------------------

    final_assortment = (
        select_diverse_assortment(
            recommendations,
            max_products=5,
        )
    )

    # --------------------------------------------------------
    # STEP 8:
    # Save full ranking
    # --------------------------------------------------------

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    recommendations.to_csv(
        RECOMMENDATIONS_PATH,
        index=False,
    )

    # --------------------------------------------------------
    # STEP 9:
    # Print recommendation
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"RECOMMENDED PRODUCTS FOR "
        f"{event['title']}"
    )

    print(
        "=" * 70
    )

    display_columns = [
        "recommended_product",
        "persona_fit_pct",
    ]

    if "category" in final_assortment.columns:

        display_columns.insert(
            1,
            "category",
        )

    print(
        final_assortment[
            display_columns
        ]
        .to_string(
            index=False
        )
    )

    print(
        f"\nFull ranking saved to:\n"
        f"{RECOMMENDATIONS_PATH}"
    )


if __name__ == "__main__":
    main()