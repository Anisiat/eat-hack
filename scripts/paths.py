"""Where every data file lives. Scripts import from here so a move only needs one edit.

data/raw/          inputs exactly as received (brand sheet, PredictHQ pull)
data/mappings/     team assumptions that translate text into archetypes and need states
data/assumptions/  RGC pricing and cost assumptions
data/archetypes/   events and products scored on the 10 WatchHumans archetypes (keyword method)
data/processed/    model-ready tables built from the above
data/synthetic/    synthetic WatchHumans users and reviews, and the synthetic pop-up history
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
MAPPINGS = DATA / "mappings"
ASSUMPTIONS = DATA / "assumptions"
ARCHETYPES_DIR = DATA / "archetypes"
PROCESSED = DATA / "processed"
SYNTHETIC = DATA / "synthetic"

# raw
BRANDS = RAW / "brands.csv"
EVENTS_RAW = RAW / "events_raw.pkl"
# mappings and assumptions
SEGMENT_ARCHETYPES = MAPPINGS / "segment_archetypes.csv"
NEED_STATES = MAPPINGS / "need_states.csv"
VALUE_ASSUMPTIONS = ASSUMPTIONS / "value_assumptions.csv"
# archetype scores
EVENTS_ARCHETYPES = ARCHETYPES_DIR / "events_archetypes.csv"
PRODUCTS_ARCHETYPES = ARCHETYPES_DIR / "products_archetypes.csv"
# processed
BRAND_FEATURES = PROCESSED / "brand_features.csv"
BRAND_PRODUCTS = PROCESSED / "brand_products.csv"
EVENT_TYPES = PROCESSED / "event_types.csv"
# synthetic
POPUPS = SYNTHETIC / "popups.csv"
POPUP_BRANDS = SYNTHETIC / "popup_brands.csv"
USERS = SYNTHETIC / "users.csv"
REVIEWS = SYNTHETIC / "reviews.csv"
