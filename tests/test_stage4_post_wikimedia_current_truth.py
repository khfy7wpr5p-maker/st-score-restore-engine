from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools import validate_stage4_post_wikimedia_current_truth as validator

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"


class Stage4PostWikimediaCurrentTruthTests(unittest.TestCase):
    def test_repository_current_truth_validator_passes(self) -> None:
        self.assertEqual(validator.main(), 0)

    def test_live_handoff_separates_historical_execution_expansion_and_human_truth(self) -> None:
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        self.assertEqual(handoff["repository_main_sha"], "76f5643dde72c8cc4b02b517133331e9dea00146")
        self.assertEqual(
            handoff["repository_current_truth"]["main_sha"],
            validator.EXPANSION_BASELINE_MAIN,
        )
        self.assertEqual(
            handoff["human_reference_current_truth"]["main_sha"],
            validator.COMPLETION_MAIN,
        )
        self.assertTrue(handoff["current_execution_truth"]["real_data_calibration_executed"])
        self.assertFalse(handoff["stage4"]["real_data_calibration_executed"])
        self.assertTrue(handoff["stage4"]["current_execution_truth"]["real_data_calibration_executed"])

    def test_wikimedia_work_package_human_fields_remain_unpopulated(self) -> None:
        package = json.loads(WORK_PACKAGE.read_text(encoding="utf-8"))
        reviews = package["item"]["pages"][0]["reviews"]
        self.assertEqual(len(reviews), 7)
        self.assertEqual({row["findingType"] for row in reviews}, validator.FINDINGS)
        for row in reviews:
            self.assertIsNone(row["referenceLabel"])
            self.assertIsNone(row["reviewerReference"])
            self.assertIsNone(row["provenanceReference"])
            self.assertIsNone(row["reviewedOn"])

    def test_separate_wikimedia_completion_contains_exact_user_supplied_all_clear_labels(self) -> None:
        completion = json.loads(COMPLETION.read_text(encoding="utf-8"))
        records = completion["bundle"]["records"]
        self.assertEqual(len(records), 7)
        self.assertEqual({row["findingType"] for row in records}, validator.FINDINGS)
        self.assertEqual({row["referenceLabel"] for row in records}, {"clear"})
        self.assertEqual(
            completion["labelCounts"],
            {"clear": 7, "not_assessed": 0, "possible": 0, "probable": 0},
        )

    def test_wikimedia_human_completion_does_not_open_downstream_gates(self) -> None:
        handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
        wiki = handoff["stage4"]["wikimedia_expansion"]
        self.assertTrue(wiki["human_labels_present"])
        self.assertEqual(
            wiki["human_label_completion_state"],
            "human_labels_complete_pending_separate_acceptance",
        )
        self.assertEqual(
            wiki["human_label_counts"],
            {"clear": 7, "possible": 0, "probable": 0, "not_assessed": 0},
        )
        self.assertTrue(wiki["work_package_remains_pristine"])
        self.assertFalse(wiki["reference_bundle_accepted"])
        self.assertFalse(wiki["candidate_derivation_eligible"])
        self.assertFalse(wiki["calibration_execution_authorized"])
        self.assertFalse(wiki["calibration_executed"])
        self.assertFalse(wiki["held_out_included"])
        self.assertFalse(wiki["stage4_exit_pass"])
        self.assertFalse(wiki["stage5_entry_authorized"])


if __name__ == "__main__":
    unittest.main()
