import argparse
import os
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------

RANDOM_SEED = 42
N_CONSUMERS = 5000

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "watch_humans_synthetic.csv"

AREAS = [
    "Hackney",
    "Shoreditch",
    "Dalston",
    "Hackney Wick",
    "Brixton",
    "Clapham",
    "Camden",
    "Soho",
    "Peckham",
    "Islington",
    "Notting Hill",
    "Bermondsey"
]

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
    "conscious_consumer"
]

# Population prevalence.
# These are synthetic assumptions, not real Watch Humans proportions.
ARCHETYPE_PREVALENCE = {
    "wellness_seeker": 0.12,
    "trend_enthusiast": 0.13,
    "thoughtful_buyer": 0.11,
    "smart_saver": 0.09,
    "quality_seeker": 0.10,
    "on_the_go_shopper": 0.10,
    "impulse_buyer": 0.08,
    "experience_explorer": 0.11,
    "everyday_planner": 0.08,
    "conscious_consumer": 0.08
}

# -----------------------------
# ARCHETYPE PROFILES
# -----------------------------

# Each archetype has an expected mean for broader behavioural dimensions.
# Values are on a 0-1 scale.

ARCHETYPE_TRAITS = {
    "wellness_seeker": {
        "health_consciousness": 0.90,
        "novelty_seeking": 0.60,
        "social_influence": 0.55,
        "price_sensitivity": 0.45,
        "quality_orientation": 0.70,
        "convenience_orientation": 0.55,
        "impulsivity": 0.35,
        "experience_seeking": 0.55,
        "planning_orientation": 0.65,
        "sustainability_orientation": 0.75
    },

    "trend_enthusiast": {
        "health_consciousness": 0.50,
        "novelty_seeking": 0.95,
        "social_influence": 0.95,
        "price_sensitivity": 0.35,
        "quality_orientation": 0.60,
        "convenience_orientation": 0.55,
        "impulsivity": 0.70,
        "experience_seeking": 0.85,
        "planning_orientation": 0.30,
        "sustainability_orientation": 0.55
    },

    "thoughtful_buyer": {
        "health_consciousness": 0.65,
        "novelty_seeking": 0.40,
        "social_influence": 0.35,
        "price_sensitivity": 0.55,
        "quality_orientation": 0.80,
        "convenience_orientation": 0.35,
        "impulsivity": 0.15,
        "experience_seeking": 0.40,
        "planning_orientation": 0.90,
        "sustainability_orientation": 0.70
    },

    "smart_saver": {
        "health_consciousness": 0.45,
        "novelty_seeking": 0.35,
        "social_influence": 0.35,
        "price_sensitivity": 0.95,
        "quality_orientation": 0.45,
        "convenience_orientation": 0.60,
        "impulsivity": 0.35,
        "experience_seeking": 0.30,
        "planning_orientation": 0.75,
        "sustainability_orientation": 0.45
    },

    "quality_seeker": {
        "health_consciousness": 0.65,
        "novelty_seeking": 0.55,
        "social_influence": 0.45,
        "price_sensitivity": 0.15,
        "quality_orientation": 0.95,
        "convenience_orientation": 0.35,
        "impulsivity": 0.30,
        "experience_seeking": 0.60,
        "planning_orientation": 0.60,
        "sustainability_orientation": 0.65
    },

    "on_the_go_shopper": {
        "health_consciousness": 0.50,
        "novelty_seeking": 0.45,
        "social_influence": 0.45,
        "price_sensitivity": 0.50,
        "quality_orientation": 0.45,
        "convenience_orientation": 0.95,
        "impulsivity": 0.60,
        "experience_seeking": 0.35,
        "planning_orientation": 0.45,
        "sustainability_orientation": 0.40
    },

    "impulse_buyer": {
        "health_consciousness": 0.40,
        "novelty_seeking": 0.75,
        "social_influence": 0.75,
        "price_sensitivity": 0.55,
        "quality_orientation": 0.45,
        "convenience_orientation": 0.70,
        "impulsivity": 0.95,
        "experience_seeking": 0.70,
        "planning_orientation": 0.15,
        "sustainability_orientation": 0.35
    },

    "experience_explorer": {
        "health_consciousness": 0.55,
        "novelty_seeking": 0.90,
        "social_influence": 0.65,
        "price_sensitivity": 0.35,
        "quality_orientation": 0.65,
        "convenience_orientation": 0.35,
        "impulsivity": 0.55,
        "experience_seeking": 0.95,
        "planning_orientation": 0.35,
        "sustainability_orientation": 0.60
    },

    "everyday_planner": {
        "health_consciousness": 0.55,
        "novelty_seeking": 0.20,
        "social_influence": 0.25,
        "price_sensitivity": 0.65,
        "quality_orientation": 0.55,
        "convenience_orientation": 0.70,
        "impulsivity": 0.20,
        "experience_seeking": 0.20,
        "planning_orientation": 0.95,
        "sustainability_orientation": 0.50
    },

    "conscious_consumer": {
        "health_consciousness": 0.75,
        "novelty_seeking": 0.55,
        "social_influence": 0.40,
        "price_sensitivity": 0.35,
        "quality_orientation": 0.70,
        "convenience_orientation": 0.35,
        "impulsivity": 0.25,
        "experience_seeking": 0.55,
        "planning_orientation": 0.65,
        "sustainability_orientation": 0.95
    }
}

# -----------------------------
# PRODUCT CATEGORY AFFINITIES - what user archetypes would be looking for
# -----------------------------

CATEGORY_PROFILES = {
    "functional_drinks": {
        "wellness_seeker": 0.95,
        "trend_enthusiast": 0.75,
        "quality_seeker": 0.65,
        "on_the_go_shopper": 0.75,
        "conscious_consumer": 0.70
    },

    "healthy_snacks": {
        "wellness_seeker": 0.95,
        "quality_seeker": 0.65,
        "on_the_go_shopper": 0.75,
        "conscious_consumer": 0.70
    },

    "streetwear": {
        "trend_enthusiast": 0.95,
        "quality_seeker": 0.65,
        "impulse_buyer": 0.65,
        "experience_explorer": 0.80
    },

    "skincare": {
        "wellness_seeker": 0.70,
        "trend_enthusiast": 0.80,
        "thoughtful_buyer": 0.80,
        "quality_seeker": 0.80,
        "conscious_consumer": 0.75
    },

    "premium_food": {
        "thoughtful_buyer": 0.70,
        "quality_seeker": 0.95,
        "experience_explorer": 0.75,
        "conscious_consumer": 0.65
    },

    "sustainable_products": {
        "thoughtful_buyer": 0.70,
        "quality_seeker": 0.60,
        "experience_explorer": 0.55,
        "conscious_consumer": 0.95
    },

    "viral_products": {
        "trend_enthusiast": 0.95,
        "impulse_buyer": 0.85,
        "experience_explorer": 0.80
    },

    "grab_and_go": {
        "smart_saver": 0.55,
        "on_the_go_shopper": 0.95,
        "impulse_buyer": 0.70,
        "everyday_planner": 0.65
    },

    "premium_beauty": {
        "trend_enthusiast": 0.70,
        "thoughtful_buyer": 0.75,
        "quality_seeker": 0.95,
        "experience_explorer": 0.65
    },

    "discount_products": {
        "smart_saver": 0.95,
        "on_the_go_shopper": 0.55,
        "impulse_buyer": 0.70,
        "everyday_planner": 0.70
    }
}


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def clip01(x):
    """Clip values to the 0-1 range."""
    return np.clip(x, 0, 1)


def noisy_score(mean, rng, sd=0.12):
    """
    Generate a noisy score centred around a mean.
    """
    return float(clip01(rng.normal(mean, sd)))


def weighted_choice_from_dict(weight_dict, rng):
    """
    Select one key according to dictionary probabilities.
    """
    labels = list(weight_dict.keys())
    probs = np.array(list(weight_dict.values()), dtype=float)
    probs = probs / probs.sum()

    return rng.choice(labels, p=probs)


def generate_archetype_scores(primary_archetype, rng):
    """
    Generate scores for all 10 archetypes.

    Primary archetype receives the strongest mean score.
    Similar scores are still possible, allowing each person
    to have a realistic secondary archetype.
    """

    scores = {}

    for archetype in ARCHETYPES:

        if archetype == primary_archetype:
            mean = 0.82

        else:
            mean = 0.35

        scores[archetype] = noisy_score(mean, rng, sd=0.14)

    return scores


def generate_trait_scores(archetype_scores, rng):
    """
    Behavioural traits are generated as a weighted combination
    of all archetypes.

    Therefore consumers are not defined purely by one archetype.
    """

    traits = {}

    trait_names = list(
        next(iter(ARCHETYPE_TRAITS.values())).keys()
    )

    weights = np.array([
        archetype_scores[a]
        for a in ARCHETYPES
    ])

    for trait in trait_names:

        means = np.array([
            ARCHETYPE_TRAITS[a][trait]
            for a in ARCHETYPES
        ])

        weighted_mean = np.average(
            means,
            weights=weights
        )

        traits[trait] = noisy_score(
            weighted_mean,
            rng,
            sd=0.08
        )

    return traits


def generate_category_affinities(archetype_scores, rng):
    """
    Generate product-category affinity from archetype scores.
    """

    affinities = {}

    for category, archetype_profile in CATEGORY_PROFILES.items():

        weighted_values = []
        weights = []

        for archetype, expected_affinity in archetype_profile.items():

            weighted_values.append(expected_affinity)
            weights.append(archetype_scores[archetype])

        mean_affinity = np.average(
            weighted_values,
            weights=weights
        )

        affinities[category] = noisy_score(
            mean_affinity,
            rng,
            sd=0.10
        )

    return affinities


# -----------------------------
# SYNTHETIC DATA GENERATOR
# -----------------------------

def generate_watch_humans_dataset(n=N_CONSUMERS, seed=RANDOM_SEED):
    """Return synthetic demo consumers without reading files or writing output."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(n):

        primary = weighted_choice_from_dict(
            ARCHETYPE_PREVALENCE, rng
        )

        archetype_scores = generate_archetype_scores(
            primary, rng
        )

        # Derive actual primary + secondary from generated scores
        sorted_archetypes = sorted(
            archetype_scores,
            key=archetype_scores.get,
            reverse=True
        )

        primary = sorted_archetypes[0]
        secondary = sorted_archetypes[1]

        traits = generate_trait_scores(
            archetype_scores, rng
        )

        category_affinities = generate_category_affinities(
            archetype_scores, rng
        )

        age = int(
            np.clip(
                rng.normal(29, 7),
                18,
                55
            )
        )

        row = {
            "human_id": f"H{i+1:05d}",
            "age": age,
            "area": rng.choice(AREAS),

            "primary_archetype": primary,
            "secondary_archetype": secondary,
        }

        # archetype scores
        for archetype, score in archetype_scores.items():
            row[f"{archetype}_score"] = round(
                score,
                3
            )

        # behavioural traits
        for trait, score in traits.items():
            row[trait] = round(
                score,
                3
            )

        # category affinities
        for category, score in category_affinities.items():
            row[f"{category}_affinity"] = round(
                score,
                3
            )

        rows.append(row)

    return pd.DataFrame(rows)


def save_watch_humans_dataset(df, output_path=OUTPUT_CSV):
    """Atomically save a portable CSV; preserve existing output if writing fails."""
    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", suffix=".tmp",
            dir=output_path.parent, delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            df.to_csv(handle, index=False, lineterminator="\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Watch Humans demo data (no API or secrets required).")
    parser.add_argument("--rows", type=int, default=N_CONSUMERS)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--output", type=Path, default=OUTPUT_CSV)
    args = parser.parse_args()
    if args.rows < 1 or args.seed < 0:
        parser.error("--rows must be positive and --seed must be non-negative")
    watch_humans_df = generate_watch_humans_dataset(args.rows, args.seed)
    output_path = save_watch_humans_dataset(watch_humans_df, args.output)
    print(f"Saved {len(watch_humans_df)} synthetic consumers ({len(watch_humans_df.columns)} columns) to {output_path}")


if __name__ == "__main__":
    main()
