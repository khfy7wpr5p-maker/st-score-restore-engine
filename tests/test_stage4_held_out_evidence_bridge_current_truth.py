from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_HELD_OUT_EVIDENCE_BRIDGE_CURRENT_TRUTH.json"


class Stage4HeldOutEvidenceBridgeCurrentTruthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.value = json.loads(OVERLAY.read_text(encoding="utf-8"))

    def test_production_checkpoint_is_pr144(self) -> None:
        checkpoint = self.value["production_checkpoint"]
        self.assertEqual(checkpoint["main_sha"], "e9cd13095e1c7ab1f2b88bd363071a10accc6332")
        self.assertEqual(checkpoint["merge_pr"], 144)
        self.assertEqual(checkpoint["exact_head_run"]["run_number"], 382)
        self.assertEqual(checkpoint["postmerge_run"]["run_number"], 383)
        self.assertEqual(checkpoint["exact_head_run"]["python_311"], "success")
        self.assertEqual(checkpoint["exact_head_run"]["python_312"], "success")
        self.assertEqual(checkpoint["postmerge_run"]["python_311"], "success")
        self.assertEqual(checkpoint["postmerge_run"]["python_312"], "success")

    def test_corrected_chopin_truth_is_explicit(self) -> None:
        truth = self.value["corrected_repository_truth"]
        self.assertIs(truth["prior_statement_that_chopin_held_out_was_not_authorized_or_executed_was_incorrect"], True)
        self.assertIs(truth["historical_held_out_evaluation_permission_granted"], True)
        self.assertIs(truth["historical_real_held_out_execution_completed"], True)
        self.assertIs(truth["historical_stage3_exit_accepted"], True)
        self.assertIs(truth["second_held_out_artifact_execution_required"], False)

    def test_exact_held_out_identity_and_non_tuning_are_preserved(self) -> None:
        scope = self.value["held_out_scope"]
        self.assertEqual(scope["dataset_item_id"], "dataset.item.imslp82860-chopin-op69.v2")
        self.assertEqual(scope["artifact_sha256"], "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3")
        self.assertEqual(scope["byte_size"], 1114479)
        self.assertEqual(scope["page_count"], 8)
        self.assertEqual(scope["rendered_page_count"], 8)
        self.assertIs(scope["held_out_threshold_tuning_used"], False)

    def test_zero_candidate_policy_does_not_invent_rates(self) -> None:
        evidence = self.value["stage4_held_out_evidence"]
        self.assertEqual(evidence["candidate_derived_count"], 0)
        self.assertEqual(evidence["coverage_rate"], 0.0)
        self.assertEqual(evidence["exact_match_rate"], "not_applicable")
        self.assertEqual(evidence["false_negative_rate"], "not_applicable")
        self.assertEqual(evidence["false_positive_rate"], "not_applicable")
        self.assertEqual(evidence["source_family_leakage_count"], 0)
        self.assertIs(evidence["evaluation_fed_back_into_candidate"], False)
        self.assertIs(evidence["evidence_bridge_ready"], True)
        self.assertIs(evidence["evidence_accepted"], False)

    def test_only_held_out_evidence_acceptance_blocker_remains(self) -> None:
        readiness = self.value["stage4_readiness"]
        self.assertEqual(readiness["state"], "ACTIVE_NOT_READY")
        self.assertEqual(readiness["blocker_count"], 1)
        self.assertEqual(readiness["blocker_codes"], ["no_real_held_out_evaluation_evidence_is_accepted"])
        assertions = self.value["assertions"]
        self.assertIs(assertions["held_out_evaluation_evidence_accepted"], False)
        self.assertIs(assertions["stage4_exit_pass"], False)
        self.assertIs(assertions["stage5_entry_authorized"], False)


if __name__ == "__main__":
    unittest.main()
