from pathlib import Path

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Change this if your events_raw.pkl lives somewhere else
EVENTS_PATH = PROJECT_ROOT / "data" / 'raw' /"events_raw.pkl"


# ============================================================
# MANUAL EVENT
# ============================================================

EAT_HACK_EVENT = {
    "event_id": "manual_eat_hack_2026",

    "title": "EAT Hack",

    "description": (
        "EAT Hack is a one-day London hackathon focused on retail, "
        "consumer behaviour, food and AI. Participants include developers, "
        "founders, challenger brands and retail innovators building products "
        "around behavioural insight, retail decision-making and future "
        "consumer experiences."
    ),

    # Closest useful high-level category for this type of event
    "category": "conferences",

    "start_local": "2026-10-03 09:00:00",
    "end_local": "2026-10-03 20:00:00",

    "duration_seconds": 11 * 60 * 60,

    # London-level coordinates for now.
    # Replace these with the actual venue coordinates if you have them.
    "longitude": -0.1278,
    "latitude": 51.5074,

    # PredictHQ-derived quantities are unknown for this manually added event
    "rank": pd.NA,
    "local_rank": pd.NA,
    "phq_attendance": pd.NA,

    # These are useful for your downstream archetype mapping
    "phq_labels": [
        "technology",
        "business",
        "food",
        "community",
    ],

    "phq_label_weights": [
        1.0,
        0.8,
        0.8,
        0.7,
    ],

    "entity_names": [
        "EAT Hack",
        "Really Good Culture",
    ],

    "entity_types": [
        "event",
        "organization",
    ],

    "predicted_event_spend": pd.NA,
    "predicted_event_spend_industries": pd.NA,
    "impact_patterns": pd.NA,

    "brand_safe": True,

    "duration_hours": 11.0,
}


# ============================================================
# ADD EVENT
# ============================================================

def main():

    events = pd.read_pickle(EVENTS_PATH)

    print(f"Loaded {len(events)} events")
    print(f"Columns: {events.columns.tolist()}")

    # --------------------------------------------------------
    # Check schema
    # --------------------------------------------------------

    missing_from_manual = [
        col
        for col in events.columns
        if col not in EAT_HACK_EVENT
    ]

    if missing_from_manual:
        raise ValueError(
            "Manual EAT Hack row is missing columns:\n"
            + "\n".join(missing_from_manual)
        )

    # Only keep columns that exist in the real dataframe,
    # and preserve exactly the same order
    new_event = pd.DataFrame(
        [EAT_HACK_EVENT]
    )[events.columns]

    # --------------------------------------------------------
    # Avoid duplicates
    # --------------------------------------------------------

    already_exists = (
        events["event_id"]
        .astype(str)
        .eq(EAT_HACK_EVENT["event_id"])
        .any()
    )

    if already_exists:
        print("EAT Hack already exists — no row added.")
        return

    # --------------------------------------------------------
    # Append
    # --------------------------------------------------------

    events = pd.concat(
        [events, new_event],
        ignore_index=True,
    )

    events.to_pickle(EVENTS_PATH)

    print(
        f"Added EAT Hack successfully.\n"
        f"Events now: {len(events)}"
    )

    print(
        events.loc[
            events["event_id"]
            == "manual_eat_hack_2026"
        ].T
    )


if __name__ == "__main__":
    main()