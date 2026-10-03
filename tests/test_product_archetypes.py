import unittest

from scripts.get_product_archetypes import load_segment_map, product_profile


class ProductArchetypeTests(unittest.TestCase):
    def setUp(self):
        self.segments = load_segment_map()

    def test_label_claims_drive_scores(self):
        protein = product_profile({"Marketing claims / label keywords": "10G HIGH PROTEIN\nNO ADDED SUGAR",
                                   "Category": "Snacks"}, self.segments)[0]
        treat = product_profile({"Marketing claims / label keywords": "Indulgent fudge and brownie chocolate",
                                 "Category": "Confectionery"}, self.segments)[0]
        self.assertGreater(protein["wellness_seeker_score"], treat["wellness_seeker_score"])
        self.assertGreater(treat["impulse_buyer_score"], protein["impulse_buyer_score"])

    def test_target_segments_count_and_scores_stay_in_range(self):
        scores, evidence = product_profile({"Target segments (inferred)": "Eco-conscious shoppers",
                                            "Category": "Pantry"}, self.segments)
        self.assertGreater(scores["conscious_consumer_score"], 0)
        self.assertTrue(any(e["source"] == "target_segments" for e in evidence["conscious_consumer"]))
        self.assertTrue(all(0 <= v < 1 for v in scores.values()))


if __name__ == "__main__":
    unittest.main()
