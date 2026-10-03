import unittest

import numpy as np
import pandas as pd

from scripts.data_mapping.event_archetypes import (
    ARCHETYPES, BEHAVIOUR_COLUMNS, build_event_personas, build_event_behaviour_profile,
    build_archetype_profiles, score_event_against_archetypes, load_watch_humans,
)


class EventArchetypeTests(unittest.TestCase):
    def test_event_details_distinguish_same_category(self):
        yoga, _ = build_event_behaviour_profile({'title': 'Yoga and meditation', 'category': 'community'})
        sale, _ = build_event_behaviour_profile({'title': 'Discount bargain sale', 'category': 'community'})
        self.assertGreater(yoga['health_consciousness'], sale['health_consciousness'])
        self.assertGreater(sale['price_sensitivity'], yoga['price_sensitivity'])

    def test_no_substring_or_placeholder_evidence(self):
        values, evidence = build_event_behaviour_profile({'title': 'Freestyle wholesale talkative', 'description': 'Sourced from predicthq.com'})
        self.assertTrue(all(score == .5 for score in values.values()))
        self.assertTrue(all(not matches for matches in evidence.values()))

    def test_missing_and_invalid_labels(self):
        values, _ = build_event_behaviour_profile({'phq_label_weights': {'fitness': float('nan'), 'health': 'invalid'}})
        self.assertTrue(all(score == .5 for score in values.values()))
        values, _ = build_event_behaviour_profile({'phq_labels': ['fitness']})
        self.assertGreater(values['health_consciousness'], .5)

    def test_similarity_is_based_on_profile_distance(self):
        prototypes = pd.DataFrame(.5, index=ARCHETYPES, columns=BEHAVIOUR_COLUMNS)
        prototypes.loc['wellness_seeker'] = .9
        scores = score_event_against_archetypes(dict.fromkeys(BEHAVIOUR_COLUMNS, .9), prototypes)
        self.assertEqual(scores['wellness_seeker_score'], 1)
        self.assertAlmostEqual(scores['smart_saver_score'], .6)
        self.assertEqual(len(scores), 10)

    def test_evidence_and_entities(self):
        values, evidence = build_event_behaviour_profile({'entity_names': ['Artisan food market']})
        self.assertTrue(any(matches for matches in evidence.values()))
        self.assertTrue(all(0 <= score <= 1 for score in values.values()))

    def test_real_watch_humans_profiles_map_events(self):
        profiles = build_archetype_profiles(load_watch_humans())
        result = build_event_personas(pd.DataFrame([{'title': 'Yoga', 'event_id': 'E1'}]), profiles)
        scores = result[[f'{a}_score' for a in ARCHETYPES]]
        self.assertTrue(np.isfinite(scores).all().all())
        self.assertTrue(((scores >= 0) & (scores <= 1)).all().all())
        self.assertIn(result.iloc[0].primary_archetype, ARCHETYPES)
