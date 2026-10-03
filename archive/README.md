# Archive

Files that are **no longer part of the PopUpPick pipeline**, kept for reference. Nothing here is read by `app.py`, the scripts or the model. The scripts in here are kept as they were and may not run as-is: paths and inputs have since moved.

| File | What it was | Why it was retired |
|---|---|---|
| `data/placeholder/events.csv` | 36 invented events at real London venues, made by `scripts/generate_events.py` | Replaced by real UK events from PredictHQ (`data/archetypes/events_archetypes.csv`) |
| `scripts/generate_events.py` | Generator for the placeholder events above | As above |
| `data/synthetic/boroughs.csv` | 33 London boroughs: Census 2021 population and 18–34 share, plus synthetic WatchHumans users per borough | Its main use was the London "low-coverage borough" bonus, dropped when events went UK-wide. Users no longer have a home borough |
| `data/raw/borough_census_2021.csv` | ONS Census 2021 age profile for the 33 London boroughs (via Nomis) | Only fed `boroughs.csv` and the users' borough |
| `scripts/get_borough_census.py` | Downloads the Census data above | As above |
| `scripts/score_products_events.py` | Standalone product × event matcher (rescaled keyword scores, simple greedy lineup). Archived version predates `scripts/paths.py` | Superseded by the model's recommendations in `outputs/lineups.json` (review learning, full lineup search, forecasts, £) |
| `data/processed/product_event_scores.csv` | Output of the script above: every product's match at every real event, with rank | As above |
| `data/processed/event_lineups.csv` | Output of the script above: one simple lineup per real event | As above |
| `data/mappings/traits.csv` | Target-segment phrase → levels on the 10 WatchHumans behavioural traits (the trait-based product scoring) | Products now use the same keyword method as events (`scripts/get_product_archetypes.py`) |
| `data/mappings/segments.csv` | Target-segment phrase → the 5 old segments (students, young professionals, fitness, families, foodies) | Replaced by the 10 WatchHumans archetypes |
| `outputs/stubs/*` | 5-row versions of the model outputs, so the app could be built before the model was ready | The real outputs exist now; these are from an earlier model version |
