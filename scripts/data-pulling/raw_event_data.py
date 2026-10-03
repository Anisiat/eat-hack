import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


# -----------------------------------
# Paths / environment
# -----------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"




# -----------------------------------
# Parse one PredictHQ event
# -----------------------------------

def parse_event(event):

    # ---------------------------
    # Coordinates
    # ---------------------------

    geo = event.get("geo", {}) or {}
    geometry = geo.get("geometry", {}) or {}
    coordinates = geometry.get("coordinates", [None, None])

    if not isinstance(coordinates, list) or len(coordinates) < 2:
        coordinates = [None, None]

    longitude = coordinates[0]
    latitude = coordinates[1]

    # ---------------------------
    # Entities
    # ---------------------------

    entities = event.get("entities", []) or []

    entity_names = [
        entity.get("name")
        for entity in entities
        if entity.get("name")
    ]

    entity_types = [
        entity.get("type")
        for entity in entities
        if entity.get("type")
    ]

    # ---------------------------
    # PredictHQ labels
    # ---------------------------

    phq_labels = event.get("phq_labels", []) or []

    label_names = [
        label.get("label")
        for label in phq_labels
        if label.get("label")
    ]

    label_weights = {
        label.get("label"): label.get("weight")
        for label in phq_labels
        if label.get("label")
    }

    # ---------------------------
    # Return one clean event row
    # ---------------------------

    return {

        # Identity
        "event_id": event.get("id"),
        "title": event.get("title"),
        "description": event.get("description"),
        "category": event.get("category"),

        # Time
        "start_local": event.get("start_local"),
        "end_local": event.get("end_local"),
        "duration_seconds": event.get("duration"),

        # Location
        "longitude": longitude,
        "latitude": latitude,

        # Event importance / scale
        "rank": event.get("rank"),
        "local_rank": event.get("local_rank"),
        "phq_attendance": event.get("phq_attendance"),

        # Semantic information
        "phq_labels": label_names,
        "phq_label_weights": label_weights,
        "entity_names": entity_names,
        "entity_types": entity_types,

        # Commercial information
        "predicted_event_spend":
            event.get("predicted_event_spend"),

        "predicted_event_spend_industries":
            event.get("predicted_event_spend_industries"),

        "impact_patterns":
            event.get("impact_patterns"),

        # Safety
        "brand_safe":
            event.get("brand_safe"),
    }


# -----------------------------------
# Get API token
# -----------------------------------

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    load_dotenv(PROJECT_ROOT / ".env")
    token = os.getenv("PREDICTHQ_TOKEN", "").strip()

    if not token:
        raise SystemExit(
            "Set PREDICTHQ_TOKEN in the project .env file "
            "or your environment."
        )


    HEADERS = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


    # -----------------------------------
    # Request GB events
    # -----------------------------------

    EVENT_PARAMS = {
        "country": "GB",
        "phq_attendance.lt": 200,

        "start.gte": "2026-10-01",
        "start.lte": "2026-12-31",

        "limit": 200,

        "brand_unsafe.exclude": "true",
    }


    try:
        response = requests.get(
            "https://api.predicthq.com/v1/events/",
            headers=HEADERS,
            params=EVENT_PARAMS,
            timeout=30,
        )

    except requests.Timeout:
        raise SystemExit(
            "PredictHQ Events API timed out. Try again later."
        ) from None
    except requests.RequestException as error:
        raise SystemExit(
            f"Could not reach PredictHQ Events API: {error}"
        ) from None


    # -----------------------------------
    # Events API error handling
    # -----------------------------------

    if response.status_code == 401:
        raise SystemExit(
            "PredictHQ rejected PREDICTHQ_TOKEN (401). "
            "Check your API token."
        )

    if response.status_code == 403:
        raise SystemExit(
            "PredictHQ denied access to the Events API (403). "
            "Check your token permissions."
        )

    if not response.ok:
        raise SystemExit(
            f"PredictHQ Events request failed "
            f"(HTTP {response.status_code})."
        )


    try:
        data = response.json()

    except ValueError:
        raise SystemExit(
            "PredictHQ returned invalid JSON from the Events API."
        ) from None


    # -----------------------------------
    # Extract events
    # -----------------------------------

    results = (
        data.get("results")
        if isinstance(data, dict)
        else None
    )

    if not isinstance(results, list):
        raise SystemExit(
            "PredictHQ returned an unexpected response: "
            "missing results list."
        )

    if not results:
        raise SystemExit(
            "No GB events matched your query."
        )

    # Exclude placeholder-only descriptions on every run before building/saving rows.
    # Keep descriptions that include this attribution alongside actual event details.
    def has_placeholder_description(event):
        description = event.get("description") or ""
        return " ".join(description.split()).casefold() == "sourced from predicthq.com"


    fetched_count = len(results)
    results = [
        event
        for event in results
        if not has_placeholder_description(event)
    ]
    print(f"Excluded {fetched_count - len(results)} placeholder-only event descriptions.")

    if not results:
        raise SystemExit(
            "No events remain after excluding PredictHQ placeholder descriptions."
        )


    # -----------------------------------
    # Convert events -> dataframe
    # -----------------------------------

    events_raw_df = pd.DataFrame(
        [
            parse_event(event)
            for event in results
        ]
    )


    # -----------------------------------
    # Clean data types
    # -----------------------------------

    events_raw_df["start_local"] = pd.to_datetime(
        events_raw_df["start_local"],
        errors="coerce",
    )

    events_raw_df["end_local"] = pd.to_datetime(
        events_raw_df["end_local"],
        errors="coerce",
    )


    events_raw_df["duration_hours"] = (
        pd.to_numeric(
            events_raw_df["duration_seconds"],
            errors="coerce",
        )
        / 3600
    )


    numeric_columns = [
        "longitude",
        "latitude",
        "rank",
        "local_rank",
        "phq_attendance",
        "predicted_event_spend",
    ]

    for column in numeric_columns:
        events_raw_df[column] = pd.to_numeric(
            events_raw_df[column],
            errors="coerce",
        )


    # -----------------------------------
    # Enforce attendance limit on numeric values before saving.
    # Missing, invalid, negative, and infinite attendance values are excluded.
    # -----------------------------------

    events_raw_df["phq_attendance"] = events_raw_df["phq_attendance"].astype(float)
    events_raw_df = events_raw_df.loc[
        events_raw_df["phq_attendance"].ge(0)
        & events_raw_df["phq_attendance"].lt(200)
    ].reset_index(drop=True)


    # -----------------------------------
    # Save raw event dataset
    # -----------------------------------

    output_path = DATA_DIR / "events_raw.pkl"

    events_raw_df.to_pickle(output_path)


    # -----------------------------------
    # Summary
    # -----------------------------------

    print(
        f"\nLoaded {len(events_raw_df)} GB events."
    )

    print(
        f"Saved raw events to:\n{output_path}"
    )

    print("\nColumns:")

    print(
        events_raw_df.columns.tolist()
    )

    print("\nFirst five events:")

    print(
        events_raw_df[
            [
                "title",
                "category",
                "start_local",
                "phq_attendance",
                "rank",
                "local_rank",
            ]
        ].head()
    )
    print("\nExample event description:")
    descriptions = events_raw_df["description"].dropna()
    print(descriptions.iloc[0] if not descriptions.empty else "No event descriptions available.")


if __name__ == "__main__":
    main()
