import unittest

import pandas as pd

from scripts.get_event_archetypes import (
    ARCHETYPES, build_event_personas, calculate_event_archetype_scores, event_profile,
)


class EventArchetypeTests(unittest.TestCase):
    def test_event_details_distinguish_same_category(self):
        yoga = calculate_event_archetype_scores({'title': 'Yoga and meditation', 'category': 'community'})
        sale = calculate_event_archetype_scores({'title': 'Discount bargain sale', 'category': 'community'})
        self.assertGreater(yoga['wellness_seeker_score'], sale['wellness_seeker_score'])
        self.assertGreater(sale['smart_saver_score'], yoga['smart_saver_score'])
        self.assertEqual(len(yoga), len(ARCHETYPES))
        self.assertTrue(all(0 <= score <= 1 for score in yoga.values()))

    def test_no_substring_or_placeholder_evidence(self):
        scores = calculate_event_archetype_scores({'title': 'Freestyle wholesale talkative', 'description': 'Sourced from predicthq.com'})
        self.assertTrue(all(score == 0 for score in scores.values()))

    def test_missing_and_invalid_labels(self):
        scores = calculate_event_archetype_scores({'phq_label_weights': {'fitness': float('nan'), 'health': 'invalid'}})
        self.assertTrue(all(score == 0 for score in scores.values()))
        scores = calculate_event_archetype_scores({'phq_labels': ['fitness']})
        self.assertGreater(scores['wellness_seeker_score'], 0)

    def test_category_does_not_force_perfect_score(self):
        scores = calculate_event_archetype_scores({'category': 'sports'})
        self.assertLess(max(scores.values()), 0.2)

    def test_evidence_and_entities(self):
        scores, evidence = event_profile({'entity_names': ['Artisan food market'], 'type': 'Yoga workshop'})
        self.assertGreater(scores['quality_seeker_score'], 0)
        self.assertGreater(scores['wellness_seeker_score'], 0)
        self.assertEqual(evidence['quality_seeker'][0]['source'], 'entity_names')

    def test_empty_or_unknown_events_have_no_invented_winner(self):
        empty = build_event_personas(pd.DataFrame())
        self.assertTrue(empty.empty)
        profile = build_event_personas(pd.DataFrame([{'title': 'Unknown event'}]))
        self.assertIsNone(profile.iloc[0]['primary_archetype'])
        self.assertIsNone(profile.iloc[0]['secondary_archetype'])


if __name__ == '__main__':
    unittest.main()
