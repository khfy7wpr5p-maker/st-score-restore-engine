import unittest

from st_score_restore.stage11_v2a_preservation import (
    V2A_LOSS_WEIGHTS,
    V2A_MAX_EPOCHS,
    V2A_LEARNING_RATE,
    v2a_candidate_gate,
    v2a_candidate_rank,
)


class Stage11V2APreservationTests(unittest.TestCase):
    def test_v2a_weights_are_valid_and_more_preservation_weighted_than_v2(self):
        weights = V2A_LOSS_WEIGHTS.as_dict()
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertGreater(weights["symbol_region_l1"] + weights["ink_recall_penalty"], 0.40)
        self.assertLess(V2A_LEARNING_RATE, 2e-4)
        self.assertEqual(V2A_MAX_EPOCHS, 8)

    def test_v2a_gate_requires_preservation_and_cleanup_floor(self):
        good = v2a_candidate_gate({
            "inkRecallDelta": -0.04,
            "pixelL1ImprovementPercent": 50.0,
            "edgeL1ImprovementPercent": 8.0,
        })
        weak_cleanup = v2a_candidate_gate({
            "inkRecallDelta": -0.01,
            "pixelL1ImprovementPercent": 40.0,
            "edgeL1ImprovementPercent": 8.0,
        })
        weak_preservation = v2a_candidate_gate({
            "inkRecallDelta": -0.06,
            "pixelL1ImprovementPercent": 60.0,
            "edgeL1ImprovementPercent": 12.0,
        })
        self.assertTrue(good["developmentGatePassed"])
        self.assertFalse(weak_cleanup["developmentGatePassed"])
        self.assertFalse(weak_preservation["developmentGatePassed"])

    def test_rank_prefers_passing_candidate(self):
        passing = {"inkRecallDelta": -0.049, "pixelL1ImprovementPercent": 48.0, "edgeL1ImprovementPercent": 6.0}
        failing = {"inkRecallDelta": -0.051, "pixelL1ImprovementPercent": 60.0, "edgeL1ImprovementPercent": 15.0}
        self.assertGreater(v2a_candidate_rank(passing), v2a_candidate_rank(failing))


if __name__ == "__main__":
    unittest.main()
