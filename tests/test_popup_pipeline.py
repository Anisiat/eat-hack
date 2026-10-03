import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import numpy as np
import pandas as pd

from tests.run_popup_pipeline import (
    ROOT, ARCHETYPES, NEED_TRAITS, api_params, discover, fetch_events, filter_events,
    rank_products, read_config, select,
)


def config():
    c = read_config(ROOT / 'config/popup_events.json')
    for field in ('latitude', 'longitude', 'radius_km'):
        c.pop(field)
    return c


def event(id='E1', attendance='100', **fields):
    return {'id': id, 'title': 'Yoga and wellness workshop', 'description': 'Yoga, healthy food and meditation.',
            'country': 'GB', 'brand_safe': True, 'category': 'community',
            'start': '2026-11-10T10:00:00Z', 'end': '2026-11-10T12:00:00Z',
            'phq_attendance': attendance, **fields}


class PipelineTests(unittest.TestCase):
    def test_filter_boundaries_and_placeholder(self):
        data = [event('good', '199.5'), event('edge', 200), event('bad', 'unknown'),
                event('missing', None), event('negative', -1), event('infinite', 'inf'),
                event('placeholder', description=' Sourced FROM\npredicthq.com '),
                event('old', start='2026-01-01'), event('wrong', country='US'),
                event('unsafe', brand_safe=False), event('cancelled', state='deleted')]
        result = filter_events(data, config())
        self.assertEqual(result.event_id.tolist(), ['good'])
        self.assertTrue(pd.api.types.is_float_dtype(result.phq_attendance))

    def test_radius(self):
        c = read_config(ROOT / 'config/popup_events.json')
        good = event('london', geo={'geometry': {'coordinates': [-0.12, 51.5]}})
        far = event('far', geo={'geometry': {'coordinates': [-3, 55]}})
        self.assertEqual(filter_events([good, far], c).event_id.tolist(), ['london'])

    def test_pagination_and_safe_endpoint(self):
        first = Mock(status_code=200)
        first.json.return_value = {'results': [event()], 'next': 'https://untrusted.invalid/page', 'overflow': False}
        second = Mock(status_code=200)
        second.json.return_value = {'results': [event(), event('E2')], 'next': None}
        get = Mock(side_effect=[first, second])
        result = fetch_events(config(), 'dummy', get)
        self.assertEqual(len(result), 2)
        self.assertEqual(get.call_args_list[1].kwargs['params']['offset'], 1)
        self.assertEqual(get.call_args_list[1].args[0], 'https://api.predicthq.com/v1/events/')
        self.assertEqual(api_params(config())['phq_attendance.lt'], 200)
        self.assertEqual(api_params(config())['start.lt'], '2027-01-01')

    def test_errors_and_truncation(self):
        for response in [Mock(status_code=401), Mock(status_code=429)]:
            with self.assertRaises(ValueError):
                fetch_events(config(), 'dummy', Mock(return_value=response))
        response = Mock(status_code=200)
        response.json.return_value = {'results': [], 'overflow': True}
        with self.assertRaisesRegex(ValueError, 'truncated'):
            fetch_events(config(), 'dummy', Mock(return_value=response))
        c = config(); c['max_pages'] = 1
        response.json.return_value = {'results': [event()], 'next': 'page2'}
        with self.assertRaisesRegex(ValueError, 'max_pages'):
            fetch_events(c, 'dummy', Mock(return_value=response))

    def test_ranking_changes_with_archetype_and_exact_count(self):
        products = []
        for i, a in enumerate(ARCHETYPES[:3]):
            row = {'product_id': str(i), 'brand_id': str(i), 'adults_only': 0, 'vegan': 1, 'needs_chilling': 0}
            row.update({f'arch_{x}': float(x == a) for x in ARCHETYPES})
            row.update({f'need_{n}': 0.5 for n in NEED_TRAITS})
            products.append(row)
        products = pd.DataFrame(products)
        e = {'event_id': 'E1', **{f'event_{t}': .5 for t in NEED_TRAITS.values()}}
        for i, a in enumerate(ARCHETYPES[:3]):
            e.update({f'{x}_score': float(x == a) for x in ARCHETYPES})
            chosen, ranked = rank_products(e, products, 2)
            self.assertEqual(len(chosen), 2)
            self.assertEqual(chosen.iloc[0].product_id, str(i))
            self.assertTrue(ranked.fit_score.between(0, 1).all())
        with self.assertRaises(ValueError):
            rank_products(e, products, 4)
        products['adults_only'] = 1
        with self.assertRaises(ValueError):
            rank_products(e, products, 1)

    def test_end_to_end_offline_real_profiles_and_products(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            fixture = folder / 'api.json'
            fixture.write_text(json.dumps([event(), event('over', 200)]))
            result = discover(config(), folder / 'out', ROOT / 'data/processed/watch_humans_synthetic.csv', fixture)
            self.assertEqual(len(result), 1)
            self.assertTrue(np.isfinite(result[[f'{a}_score' for a in ARCHETYPES]]).all().all())
            selected = select(folder / 'out', 'E1', 3, one_per_brand=True)
            self.assertEqual(selected.brand_id.nunique(), 3)
            self.assertEqual(len(pd.read_csv(folder / 'out/selected_products.csv')), 3)
            with self.assertRaises(ValueError):
                select(folder / 'out', 'does-not-exist', 3)

    def test_bad_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            for update in [{'max_attendance': '200'}, {'max_attendance': -1}, {'start_date': '2027-01-01'}, {'max_pages': 0}]:
                path.write_text(json.dumps({**config(), **update}))
                with self.assertRaises(ValueError):
                    read_config(path)
