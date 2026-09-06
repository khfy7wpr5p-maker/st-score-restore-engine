from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage8_final_exit_current_truth import (
    EXPECTED_CURRENT_TRUTH_SHA256,
    Stage8FinalExitCurrentTruthError,
    validate_stage8_final_exit_current_truth,
)

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Stage8FinalExitCurrentTruthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = load("evidence/stage8/stage8-entry-authorization.v1.json")
        self.stage7_truth = load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json")
        self.contract = load("api/stage8-docres-candidate-contract.v1.json")
        self.acceptance = load("evidence/stage8/final-exit/stage8-final-exit-acceptance.v1.json")
        self.current_truth = load("docs/live/ST_SCORE_RESTORE_STAGE8_FINAL_EXIT_CURRENT_TRUTH.json")

    def validate(self, current_truth: dict | None = None):
        return validate_stage8_final_exit_current_truth(
            self.authorization,
            self.stage7_truth,
            self.contract,
            self.acceptance,
            current_truth or self.current_truth,
        )

    def test_final_current_truth_is_valid_and_bounded(self):
        result = self.validate()
        self.assertEqual("COMPLETE_PASS_DOCRES_OPTIONAL_CANDIDATE_CONTRACT", result["stage8State"])
        self.assertTrue(result["stage8ExitPass"])
        self.assertTrue(result["stage9EntryEligible"])
        self.assertFalse(result["stage9EntryAuthorized"])
        self.assertFalse(result["docresRuntimeDependencyApproved"])
        self.assertFalse(result["liveDocresRuntimeActivationAuthorized"])
        self.assertFalse(result["stage9ComparatorSelectionAuthorized"])
        self.assertEqual(EXPECTED_CURRENT_TRUTH_SHA256, result["currentTruthDigest"])

    def test_stage9_cannot_be_silently_started_or_authorized(self):
        for field in ("entry_authorized", "started"):
            with self.subTest(field=field):
                changed = deepcopy(self.current_truth)
                changed["stage9"][field] = True
                with self.assertRaises(Stage8FinalExitCurrentTruthError):
                    self.validate(changed)

    def test_docres_runtime_and_model_cannot_be_silently_approved(self):
        changed = deepcopy(self.current_truth)
        changed["stage8"]["dependency_status"] = "APPROVED"
        with self.assertRaises(Stage8FinalExitCurrentTruthError):
            self.validate(changed)

        changed = deepcopy(self.current_truth)
        changed["stage8"]["model_artifact_status"] = "APPROVED"
        with self.assertRaises(Stage8FinalExitCurrentTruthError):
            self.validate(changed)

        for field in (
            "docres_runtime_dependency_approved",
            "model_artifact_download_authorized",
            "model_weights_use_authorized",
            "network_fetch_authorized",
            "live_docres_runtime_activation_authorized",
            "real_user_docres_cohort_authorized",
        ):
            with self.subTest(field=field):
                changed = deepcopy(self.current_truth)
                changed["assertions"][field] = True
                with self.assertRaises(Stage8FinalExitCurrentTruthError):
                    self.validate(changed)

    def test_comparator_and_final_selection_remain_separately_gated(self):
        for field in ("stage9_comparator_selection_authorized", "automatic_final_selection_authorized"):
            changed = deepcopy(self.current_truth)
            changed["assertions"][field] = True
            with self.assertRaises(Stage8FinalExitCurrentTruthError):
                self.validate(changed)

    def test_source_and_historical_invariants_cannot_be_weakened(self):
        for field in ("historical_evidence_immutable", "source_artifact_immutable", "derived_artifacts_provenance_bound"):
            changed = deepcopy(self.current_truth)
            changed["assertions"][field] = False
            with self.assertRaises(Stage8FinalExitCurrentTruthError):
                self.validate(changed)

    def test_unsupported_quality_claims_remain_false(self):
        for field in (
            "omr_correctness_established",
            "musical_truth_established",
            "restoration_effectiveness_established",
            "production_availability_or_scalability_established",
            "color_fidelity_certified",
        ):
            changed = deepcopy(self.current_truth)
            changed["assertions"][field] = True
            with self.assertRaises(Stage8FinalExitCurrentTruthError):
                self.validate(changed)

    def test_ci_checkpoint_and_continuation_boundary_are_exact(self):
        changed = deepcopy(self.current_truth)
        changed["production_checkpoint"]["postmerge_ci"]["stage8_governance"]["result"] = "FAILURE"
        with self.assertRaises(Stage8FinalExitCurrentTruthError):
            self.validate(changed)

        changed = deepcopy(self.current_truth)
        changed["continuation_state"]["stage9_started"] = True
        with self.assertRaises(Stage8FinalExitCurrentTruthError):
            self.validate(changed)


if __name__ == "__main__":
    unittest.main()
