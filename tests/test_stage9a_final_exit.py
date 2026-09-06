from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage9a_final_exit import (
    Stage9AFinalExitError,
    validate_stage9a_final_exit,
)
from st_score_restore.stage9a_final_exit_current_truth import (
    Stage9AFinalTruthError,
    validate_stage9a_final_exit_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage9AFinalExitTests(unittest.TestCase):
    def setUp(self):
        self.acceptance = load("evidence/stage9a/final-exit/stage9a-final-exit-acceptance.v1.json")
        self.truth = load("docs/live/ST_SCORE_RESTORE_STAGE9A_FINAL_EXIT_CURRENT_TRUTH.json")

    def test_final_exit_passes(self):
        result = validate_stage9a_final_exit(self.acceptance)
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["stage10EntryEligible"])
        self.assertFalse(result["stage10EntryAuthorized"])

    def test_failed_ci_cannot_be_accepted(self):
        mutated = copy.deepcopy(self.acceptance)
        mutated["capabilityCheckpoint"]["postmergeCi"]["stage9aGovernance"]["result"] = "FAILURE"
        with self.assertRaises(Stage9AFinalExitError):
            validate_stage9a_final_exit(mutated)

    def test_training_cannot_be_recast_as_complete(self):
        mutated = copy.deepcopy(self.acceptance)
        mutated["acceptedCapabilities"]["trainedMspmModelComplete"] = True
        with self.assertRaises(Stage9AFinalExitError):
            validate_stage9a_final_exit(mutated)

    def test_stage10_cannot_be_silently_authorized(self):
        mutated = copy.deepcopy(self.acceptance)
        mutated["stage10"]["entryAuthorized"] = True
        with self.assertRaises(Stage9AFinalExitError):
            validate_stage9a_final_exit(mutated)

    def test_current_truth_passes(self):
        result = validate_stage9a_final_exit_current_truth(self.truth, self.acceptance)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["firstIncompleteBoundary"], "separate_stage10_entry_authorization")
        self.assertFalse(result["trainedMspmModelEstablished"])

    def test_truth_cannot_start_stage10(self):
        mutated = copy.deepcopy(self.truth)
        mutated["stage10"]["started"] = True
        with self.assertRaises(Stage9AFinalTruthError):
            validate_stage9a_final_exit_current_truth(mutated, self.acceptance)

    def test_truth_cannot_claim_trained_model(self):
        mutated = copy.deepcopy(self.truth)
        mutated["assertions"]["trained_mspm_model_established"] = True
        with self.assertRaises(Stage9AFinalTruthError):
            validate_stage9a_final_exit_current_truth(mutated, self.acceptance)

    def test_truth_checkpoint_is_bound(self):
        mutated = copy.deepcopy(self.truth)
        mutated["production_checkpoint"]["main_sha"] = "deadbeef"
        with self.assertRaises(Stage9AFinalTruthError):
            validate_stage9a_final_exit_current_truth(mutated, self.acceptance)


if __name__ == "__main__":
    unittest.main()
