from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from st_score_restore.stage10_final_exit_current_truth import (
    Stage10CurrentTruthError,
    validate_stage10_final_exit_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage10FinalCurrentTruthTests(unittest.TestCase):
    def args(self):
        return (
            load("docs/live/ST_SCORE_RESTORE_STAGE10_FINAL_EXIT_CURRENT_TRUTH.json"),
            load("evidence/stage10/final-exit/stage10-final-exit-acceptance.v1.json"),
            load("evidence/stage10/stage10-entry-authorization.v1.json"),
            load("docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json"),
            load("api/stage10-selector-contract.v1.json"),
        )

    def test_committed_current_truth_passes(self):
        result = validate_stage10_final_exit_current_truth(*self.args())
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["stage10State"], "COMPLETE_PASS_PROVIDER_NEUTRAL_ST_RESTORE_SELECTOR_FOUNDATION")
        self.assertFalse(result["stage11Started"])

    def mutate_and_require_failure(self, mutation):
        args = list(self.args())
        args[0] = deepcopy(args[0])
        mutation(args[0])
        with self.assertRaises(Stage10CurrentTruthError):
            validate_stage10_final_exit_current_truth(*args)

    def test_stage11_authorization_mutation_fails(self):
        self.mutate_and_require_failure(lambda truth: truth["stage11"].__setitem__("entry_authorized", True))

    def test_production_mutation_fails(self):
        self.mutate_and_require_failure(lambda truth: truth["deployment"].__setitem__("production_deployment_authorized", True))

    def test_live_selector_mutation_fails(self):
        self.mutate_and_require_failure(lambda truth: truth["stage10"].__setitem__("live_selector_activation_authorized", True))

    def test_checkpoint_mutation_fails(self):
        self.mutate_and_require_failure(lambda truth: truth["production_checkpoint"].__setitem__("main_sha", "tampered"))

    def test_omr_truth_mutation_fails(self):
        self.mutate_and_require_failure(lambda truth: truth["assertions"].__setitem__("omr_correctness_established", True))


if __name__ == "__main__":
    unittest.main()
