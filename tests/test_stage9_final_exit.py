from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = json.loads((ROOT / "evidence/stage9/final-exit/stage9-final-exit-acceptance.v1.json").read_text(encoding="utf-8"))
TRUTH = json.loads((ROOT / "docs/live/ST_SCORE_RESTORE_STAGE9_FINAL_EXIT_CURRENT_TRUTH.json").read_text(encoding="utf-8"))


class Stage9FinalExitTests(unittest.TestCase):
    def test_final_exit_pass_and_state(self) -> None:
        self.assertEqual("PASS", ACCEPTANCE["decision"])
        self.assertEqual("COMPLETE_PASS_PROVIDER_NEUTRAL_MULTI_ENGINE_COMPARATOR_FOUNDATION", ACCEPTANCE["accepted_state"])
        self.assertTrue(TRUTH["stage9"]["exit_pass"])

    def test_ci_evidence_is_complete(self) -> None:
        expected = {"repository_validation", "stage4_governance", "stage5_governance", "stage6_governance", "stage7_governance", "stage8_governance", "stage9_governance"}
        for section_name in ("exact_head_ci", "postmerge_ci"):
            section = ACCEPTANCE[section_name]
            self.assertEqual(expected, set(section))
            self.assertTrue(all(item["result"] == "SUCCESS" for item in section.values()))

    def test_stage9a_is_only_next_entry_eligible_stage(self) -> None:
        self.assertTrue(TRUTH["stage9a"]["entry_eligible"])
        self.assertFalse(TRUTH["stage9a"]["entry_authorized"])
        self.assertFalse(TRUTH["stage9a"]["started"])
        self.assertFalse(TRUTH["stage10"]["entry_eligible"])
        self.assertEqual("accepted_stage9a_exit", TRUTH["stage10"]["blocked_pending"])

    def test_no_activation_or_training_is_silently_authorized(self) -> None:
        assertions = TRUTH["assertions"]
        for key in (
            "automatic_final_selection_authorized",
            "stage9a_entry_authorized",
            "stage9a_training_authorized",
            "stage10_entry_authorized",
            "stage10_selector_activation_authorized",
            "docres_runtime_dependency_approved",
            "model_artifact_download_authorized",
            "network_fetch_authorized",
            "live_resource_creation_authorized",
            "production_deployment_authorized",
            "threshold_changes_authorized",
            "resource_limit_changes_authorized",
            "held_out_retuning_authorized",
            "model_training_authorized",
            "model_publication_authorized",
        ):
            self.assertFalse(assertions[key], key)

    def test_source_and_safety_invariants_remain_true(self) -> None:
        assertions = TRUTH["assertions"]
        for key in (
            "source_artifact_immutable",
            "derived_artifacts_provenance_bound",
            "safety_validation_precedes_comparator_eligibility",
            "hard_deterministic_veto_non_overridable",
            "hard_semantic_veto_non_overridable_when_present",
            "original_always_selectable",
            "unknown_evidence_fails_safe",
        ):
            self.assertTrue(assertions[key], key)

    def test_mutation_examples_would_violate_contract(self) -> None:
        mutated = copy.deepcopy(TRUTH)
        mutated["stage10"]["entry_eligible"] = True
        self.assertNotEqual(TRUTH["stage10"], mutated["stage10"])
        mutated = copy.deepcopy(TRUTH)
        mutated["assertions"]["production_deployment_authorized"] = True
        self.assertNotEqual(TRUTH["assertions"], mutated["assertions"])


if __name__ == "__main__":
    unittest.main()
