"""Discover matching events, map Watch Humans profiles, then select X products."""
import argparse
from datetime import date, timedelta
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.build_brand_features import build_tables
from scripts.data_mapping.event_archetypes import (
    ARCHETYPES, ARCHETYPE_SCORE_COLUMNS, BEHAVIOUR_COLUMNS,
    build_archetype_profiles, build_event_personas, load_watch_humans,
)

# The data-pulling directory is not a Python package name.
_spec = importlib.util.spec_from_file_location('raw_events', ROOT / 'scripts/data-pulling/raw_event_data.py')
_raw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_raw)
API_URL = 'https://api.predicthq.com/v1/events/'


def read_config(path):
    config = json.loads(Path(path).read_text())
    allowed = {'country', 'start_date', 'end_date', 'categories', 'query', 'min_attendance',
               'max_attendance', 'latitude', 'longitude', 'radius_km', 'brand_safe_only', 'max_pages'}
    unknown = set(config) - allowed
    if unknown:
        raise ValueError(f'Unknown event parameters: {sorted(unknown)}')
    config = {'country': 'GB', 'min_attendance': 1, 'max_attendance': 200,
              'brand_safe_only': True, 'max_pages': 100, **config}
    start, end = date.fromisoformat(config['start_date']), date.fromisoformat(config['end_date'])
    if start > end:
        raise ValueError('start_date must be on or before end_date')
    for name in ('min_attendance', 'max_attendance'):
        value = config[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'{name} must be a finite number')
    if not 0 <= config['min_attendance'] < config['max_attendance']:
        raise ValueError('Attendance limits must satisfy 0 <= min < max (max is exclusive)')
    if type(config['max_pages']) is not int or config['max_pages'] < 1:
        raise ValueError('max_pages must be a positive integer')
    if type(config['brand_safe_only']) is not bool:
        raise ValueError('brand_safe_only must be true or false')
    if not isinstance(config['country'], str) or len(config['country']) != 2:
        raise ValueError('country must be a two-letter country code')
    config['country'] = config['country'].upper()
    if 'query' in config and not isinstance(config['query'], str):
        raise ValueError('query must be a string')
    if 'categories' in config and (not isinstance(config['categories'], list) or
                                   any(not isinstance(x, str) for x in config['categories'])):
        raise ValueError('categories must be a list of strings')
    geo = [key in config for key in ('latitude', 'longitude', 'radius_km')]
    if any(geo):
        if not all(geo):
            raise ValueError('Provide latitude, longitude and radius_km together')
        lat, lon, radius = [config[k] for k in ('latitude', 'longitude', 'radius_km')]
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (lat, lon, radius)):
            raise ValueError('Location parameters must be finite numbers')
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and radius > 0):
            raise ValueError('Invalid latitude, longitude or radius')
    return config


def api_params(config):
    params = {
        'country': config['country'], 'start.gte': config['start_date'],
        'start.lt': (date.fromisoformat(config['end_date']) + timedelta(days=1)).isoformat(),
        'phq_attendance.gte': config['min_attendance'],
        'phq_attendance.lt': config['max_attendance'],
        'brand_unsafe.exclude': str(config['brand_safe_only']).lower(),
        'state': 'active', 'sort': 'start,id', 'limit': 100,
    }
    if config.get('categories'):
        params['category'] = ','.join(config['categories'])
    if config.get('query'):
        params['q'] = config['query']
    if 'radius_km' in config:
        params['within'] = f"{config['radius_km']}km@{config['latitude']},{config['longitude']}"
    return params


def fetch_events(config, token, get=requests.get):
    if not token:
        raise ValueError('Set PREDICTHQ_TOKEN in your environment or project .env')
    events, seen = [], set()
    offset = 0
    for _ in range(config['max_pages']):
        try:
            response = get(API_URL, headers={'Authorization': f'Bearer {token}', 'Accept': 'application/json'},
                           params={**api_params(config), 'offset': offset}, timeout=30)
        except requests.RequestException:
            raise ValueError('PredictHQ connection failed; retry discovery later') from None
        if response.status_code != 200:
            raise ValueError(f'PredictHQ returned HTTP {response.status_code}; check token, permissions or quota')
        try:
            payload = response.json()
        except ValueError:
            raise ValueError('PredictHQ returned invalid JSON') from None
        if not isinstance(payload, dict) or not isinstance(payload.get('results'), list):
            raise ValueError('PredictHQ response is missing a results list')
        if payload.get('overflow'):
            raise ValueError('PredictHQ subscription truncated results; narrow the event parameters')
        batch = payload['results']
        before = len(events)
        for event in batch:
            if not isinstance(event, dict) or not event.get('id'):
                raise ValueError('PredictHQ returned an event without an ID')
            if event['id'] not in seen:
                seen.add(event['id'])
                events.append(event)
        if not payload.get('next'):
            return events
        if len(events) == before:
            raise ValueError('PredictHQ pagination made no progress')
        offset += len(batch)
    raise ValueError('max_pages reached; narrow filters or increase max_pages (no partial results saved)')


def filter_events(events, config):
    """Apply numeric attendance, description, date and geographic checks locally too."""
    rows = []
    for event in events:
        row = _raw.parse_event(event) if 'id' in event else dict(event)
        if 'id' in event:
            row['start_local'] = event.get('start_local') or event.get('start')
            row['end_local'] = event.get('end_local') or event.get('end')
        description = row.get('description')
        if not isinstance(description, str) or not description.strip():
            continue
        if ' '.join(description.split()).casefold() == 'sourced from predicthq.com':
            continue
        try:
            attendance = float(row.get('phq_attendance'))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(attendance) or not config['min_attendance'] <= attendance < config['max_attendance']:
            continue
        start = pd.to_datetime(event.get('start') or row.get('start_local'), errors='coerce', utc=True)
        if pd.isna(start) or not config['start_date'] <= start.date().isoformat() <= config['end_date']:
            continue
        if config.get('categories') and row.get('category') not in config['categories']:
            continue
        if event.get('country') and event['country'] != config['country']:
            continue
        if config['brand_safe_only'] and event.get('brand_safe') is False:
            continue
        if event.get('state', 'active') != 'active':
            continue
        if 'radius_km' in config:
            try:
                lat, lon = float(row['latitude']), float(row['longitude'])
            except (KeyError, TypeError, ValueError):
                continue
            if not math.isfinite(lat + lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            lat1, lat2 = math.radians(config['latitude']), math.radians(lat)
            a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(math.radians(lon-config['longitude'])/2)**2
            distance = 6371 * 2 * math.asin(math.sqrt(min(1, max(0, a))))
            if distance > config['radius_km']:
                continue
        row['phq_attendance'] = attendance
        row.pop('brand_safe', None)
        row.pop('duration_seconds', None)
        if not row.get('event_id'):
            raise ValueError('An event is missing its event_id')
        rows.append(row)
    if not rows:
        raise ValueError('No events match the filters with useful descriptions')
    return pd.DataFrame(rows).drop_duplicates('event_id').reset_index(drop=True)


def write_csv(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=path.parent, delete=False) as f:
            tmp = Path(f.name)
            df.to_csv(f, index=False)
        os.replace(tmp, path)
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)


def discover(config, out, humans_path, events_file=None):
    if events_file:
        # JSON is portable and contains original API records, including country/safety.
        raw = json.loads(Path(events_file).read_text())
        raw = raw.get('results') if isinstance(raw, dict) else raw
        if not isinstance(raw, list):
            raise ValueError('events-file must contain a JSON event list or results object')
        if config.get('query'):
            raise ValueError('Offline discovery cannot reproduce API full-text query semantics; omit query')
    else:
        load_dotenv(ROOT / '.env')
        raw = fetch_events(config, os.getenv('PREDICTHQ_TOKEN', '').strip())
    events = filter_events(raw, config)
    humans = load_watch_humans(humans_path)
    required = ARCHETYPE_SCORE_COLUMNS + BEHAVIOUR_COLUMNS
    values = humans[required].to_numpy(dtype=float)
    if not len(humans) or not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError('Watch Humans scores and traits must be finite numbers in [0, 1]')
    if (humans[ARCHETYPE_SCORE_COLUMNS].sum() <= 0).any():
        raise ValueError('Each archetype needs positive Watch Humans weights')
    profiles = build_archetype_profiles(humans)
    mapped = build_event_personas(events, profiles)
    out = Path(out)
    write_csv(profiles.reset_index(), out / 'watch_humans_profiles.csv')
    write_csv(mapped, out / 'events.csv')
    (out / 'discovery.json').write_text(json.dumps({'filters': config, 'source': 'offline' if events_file else 'PredictHQ',
        'fetched': len(raw), 'retained': len(mapped), 'watch_humans_file': str(humans_path)}, indent=2))
    # A previous selection belongs to the old event snapshot.
    for name in ('selected_products.csv', 'product_scores.csv', 'selection.json'):
        (out / name).unlink(missing_ok=True)
    return mapped


# Event behavioural signals translated to the existing product need-state space.
NEED_TRAITS = {
    'hydrate': 'health_consciousness', 'recover': 'health_consciousness',
    'energy': 'convenience_orientation', 'focus': 'planning_orientation',
    'discovery': 'novelty_seeking', 'sharing': 'social_influence',
    'treat': 'experience_seeking', 'value': 'price_sensitivity',
}


def rank_products(event, products, count, one_per_brand=False, vegan=False, no_chilling=False, allow_adults=False):
    if type(count) is not int or count < 1:
        raise ValueError('Product count must be a positive integer')
    if products['product_id'].duplicated().any():
        raise ValueError('Product IDs must be unique')
    products = products.copy()
    if not allow_adults:
        products = products.loc[pd.to_numeric(products['adults_only'], errors='coerce').eq(0)]
    if vegan:
        products = products.loc[pd.to_numeric(products['vegan'], errors='coerce').eq(1)]
    if no_chilling:
        products = products.loc[pd.to_numeric(products['needs_chilling'], errors='coerce').eq(0)]
    arch = np.array([float(event[f'{a}_score']) for a in ARCHETYPES])
    if not np.isfinite(arch).all() or (arch < 0).any() or (arch > 1).any() or arch.sum() == 0:
        raise ValueError('Selected event has no valid archetype scores')
    mix = arch / arch.sum()
    product_arch = products[[f'arch_{a}' for a in ARCHETYPES]].apply(pd.to_numeric, errors='coerce').to_numpy()
    needs = np.array([float(event[f'event_{trait}']) for trait in NEED_TRAITS.values()])
    product_needs = products[[f'need_{n}' for n in NEED_TRAITS]].apply(pd.to_numeric, errors='coerce').to_numpy()
    for values in (product_arch, product_needs, needs):
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError('Event traits and product affinities must be finite values in [0, 1]')
    products['archetype_fit'] = product_arch @ mix
    products['event_context_fit'] = product_needs @ needs / needs.sum() if needs.sum() else 0.0
    products['fit_score'] = 0.75 * products['archetype_fit'] + 0.25 * products['event_context_fit']
    products['match_reasons'] = [
        '; '.join(f'{ARCHETYPES[i]}: event {arch[i]:.3f}, product {row[i]:.3f}'
                  for i in np.argsort(-(row * mix), kind='stable')[:3])
        for row in product_arch
    ]
    products = products.sort_values(['fit_score', 'product_id'], ascending=[False, True]).reset_index(drop=True)
    candidates = products.drop_duplicates('brand_id') if one_per_brand else products
    if len(candidates) < count:
        raise ValueError(f'Requested {count} products, but only {len(candidates)} satisfy the constraints')
    chosen = candidates.head(count).copy()
    chosen.insert(0, 'selection_rank', range(1, count+1))
    chosen.insert(0, 'event_id', event['event_id'])
    return chosen, products


def select(out, event_id, count, **constraints):
    out = Path(out)
    events = pd.read_csv(out / 'events.csv', dtype={'event_id': str})
    event = events.loc[events['event_id'] == event_id]
    if len(event) != 1:
        raise ValueError(f'Event ID {event_id!r} is not uniquely present in {out / "events.csv"}')
    products, _ = build_tables(ROOT)
    chosen, ranked = rank_products(event.iloc[0], products, count, **constraints)
    write_csv(ranked, out / 'product_scores.csv')
    write_csv(chosen, out / 'selected_products.csv')
    (out / 'selection.json').write_text(json.dumps({
        'event_id': event_id, 'title': event.iloc[0]['title'], 'count': count,
        'product_ids': chosen['product_id'].tolist(), 'constraints': constraints,
        'scoring': '0.75 * archetype affinity + 0.25 * event need-state fit',
        'limitations': 'Heuristic fit using synthetic Watch Humans profiles and inferred product mappings; not predicted sales. Stock, budget and venue permission are not evaluated.',
    }, indent=2))
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    discovery = commands.add_parser('discover', help='Fetch/filter events and map Watch Humans profiles')
    discovery.add_argument('--config', type=Path, default=ROOT / 'config/popup_events.json')
    discovery.add_argument('--watch-humans', type=Path, default=ROOT / 'data/processed/watch_humans_synthetic.csv')
    discovery.add_argument('--events-file', type=Path, help='Offline JSON API response; no network request')
    discovery.add_argument('--output-dir', type=Path, default=ROOT / 'outputs/popup_pipeline')
    selection = commands.add_parser('select', help='Choose X products for a discovered event ID')
    selection.add_argument('--event-id', required=True)
    selection.add_argument('--products', type=int, required=True)
    selection.add_argument('--output-dir', type=Path, default=ROOT / 'outputs/popup_pipeline')
    selection.add_argument('--one-per-brand', action='store_true')
    selection.add_argument('--vegan', action='store_true')
    selection.add_argument('--no-chilling', action='store_true')
    selection.add_argument('--allow-adults', action='store_true', help='Include alcohol/CBD/adults-only products')
    args = parser.parse_args()
    try:
        if args.command == 'discover':
            result = discover(read_config(args.config), args.output_dir, args.watch_humans, args.events_file)
            print(result[['event_id', 'title', 'phq_attendance', 'primary_archetype']].to_string(index=False))
            print(f'Choose an event_id above and run select --event-id ID --products X. Saved to {args.output_dir}')
        else:
            result = select(args.output_dir, args.event_id, args.products, one_per_brand=args.one_per_brand,
                            vegan=args.vegan, no_chilling=args.no_chilling, allow_adults=args.allow_adults)
            print(result[['selection_rank', 'brand_name', 'product', 'fit_score', 'match_reasons']].to_string(index=False))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Pipeline error: {error}\n')


if __name__ == '__main__':
    main()
