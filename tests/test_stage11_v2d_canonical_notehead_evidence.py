from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from st_score_restore.stage11_v2c_semantic_preservation import Stage11V2cSemanticPreservationError
from st_score_restore.stage11_v2d_canonical_notehead_evidence import (
    RESULT_BYTE_SIZE,
    RESULT_DRIVE_FILE_ID,
    RESULT_SHA256,
    validate_notehead_binding,
)

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "evidence" / "stage11" / "v2d" / "v2d-canonical-notehead-result-binding.v1.json"
SELECTION = ROOT / "evidence" / "stage11" / "v2d" / "v2d-class-selection-decision.v1.json"
CLEF_AUDIT = ROOT / "evidence" / "stage11" / "v2d" / "v2d-clef-feasibility-audit.v1.json"
STRATEGY = ROOT / "evidence" / "stage11" / "v2d" / "v2d-next-semantic-class-strategy.v1.json"
CURRENT_TRUTH = ROOT / "docs" / "live" / "ST_SCORE_RESTORE_STAGE11_V2D_CURRENT_TRUTH.json"


class Stage11V2dCanonicalNoteheadEvidenceTests(unittest.TestCase):
    def _binding(self) -> dict:
        return json.loads(BINDING.read_text(encoding="utf-8"))

    def test_committed_binding_is_exact_and_class_scoped(self) -> None:
        binding = self._binding()
        result = validate_notehead_binding(binding)
        self.assertEqual("pass", result["status"])
        self.assertEqual(18, result["pageCount"])
        self.assertAlmostEqual(0.9361482829653194, result["meanSourceRecall"])
        self.assertFalse(result["overallStage11PassAuthorized"])
        self.assertEqual(RESULT_DRIVE_FILE_ID, binding["sourceResult"]["driveFileId"])
        self.assertEqual(RESULT_BYTE_SIZE, binding["sourceResult"]["byteSize"])
        self.assertEqual(RESULT_SHA256, binding["sourceResult"]["sha256"])

    def test_binding_fails_closed_on_metric_or_overall_claim_tampering(self) -> None:
        binding = self._binding()
        tampered = copy.deepcopy(binding)
        tampered["pages"][0]["metric"]["matchedCount"] -= 1
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_notehead_binding(tampered)

        tampered = copy.deepcopy(binding)
        tampered["claimBoundary"]["overallStage11PassAuthorized"] = True
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_notehead_binding(tampered)

        tampered = copy.deepcopy(binding)
        tampered["runtimeEvidence"]["detector"]["wholeSessionFallbackDisabled"] = False
        with self.assertRaises(Stage11V2cSemanticPreservationError):
            validate_notehead_binding(tampered)

    def test_binding_fails_closed_on_hash_page_count_or_class_tampering(self) -> None:
        for mutate in (
            lambda payload: payload["sourceResult"].update(sha256="0" * 64),
            lambda payload: payload["pages"].pop(),
            lambda payload: payload["pages"][0]["metric"].update(classId="clef"),
            lambda payload: payload["pages"][0].update(teacherState="absent"),
        ):
            tampered = copy.deepcopy(self._binding())
            mutate(tampered)
            with self.assertRaises(Stage11V2cSemanticPreservationError):
                validate_notehead_binding(tampered)

    def test_class_decision_and_current_truth_accept_only_notehead(self) -> None:
        selection = json.loads(SELECTION.read_text(encoding="utf-8"))
        notehead = next(item for item in selection["classResults"] if item["classId"] == "notehead")
        self.assertEqual("SELECT_CANONICAL_CPU_RERUN", notehead["decision"])
        self.assertEqual(17, notehead["pagesAtRecallGte0_80"])
        self.assertEqual("PASS_CANONICAL_CLASS_EVIDENCE", selection["canonicalOutcome"]["decision"])
        self.assertFalse(selection["claimBoundary"]["semanticPreservationEstablished"])
        self.assertFalse(selection["claimBoundary"]["overallStage11PassAuthorized"])

        truth = json.loads(CURRENT_TRUTH.read_text(encoding="utf-8"))
        self.assertEqual(["notehead"], truth["classMatrix"]["PASS"])
        self.assertEqual(["clef"], truth["classMatrix"]["REVIEW_ONLY"])
        for key in (
            "semanticPreservationEstablished",
            "overallStage11PassAuthorized",
            "productionReady",
            "productionPromotionAuthorized",
            "stage12EntryAuthorized",
        ):
            self.assertFalse(truth["safetyBoundaries"][key])
        self.assertTrue(truth["pullRequest"]["mustRemainDraft"])
        self.assertFalse(truth["pullRequest"]["mergeAuthorized"])

    def test_clef_audit_is_arithmetically_bound_and_does_not_request_colab(self) -> None:
        audit = json.loads(CLEF_AUDIT.read_text(encoding="utf-8"))
        evidence = audit["exploratoryClefEvidence"]
        pages = evidence["pages"]
        self.assertEqual(18, len(pages))
        self.assertEqual(12, sum(page["sourceRecall"] >= 0.80 for page in pages))
        self.assertEqual(586, sum(page["sourceCount"] for page in pages))
        self.assertEqual(450, sum(page["matchedCount"] for page in pages))
        self.assertEqual(557, sum(page["candidateCount"] for page in pages))
        self.assertEqual(107, sum(page["candidateOnlyCount"] for page in pages))
        self.assertAlmostEqual(450 / 586, evidence["pooledSourceRecall"])
        self.assertAlmostEqual(107 / 557, evidence["candidateOnlyShareOfRestoredCandidates"])
        self.assertEqual("REVIEW_ONLY_NO_CANONICAL_RERUN", audit["decision"]["disposition"])
        self.assertFalse(audit["decision"]["canonicalRerunPrepared"])
        self.assertFalse(audit["equivalenceAndCost"]["newColabRunRequiredNow"])

    def test_remaining_class_strategy_has_complete_fail_closed_matrix(self) -> None:
        strategy = json.loads(STRATEGY.read_text(encoding="utf-8"))
        matrix = strategy["currentClassMatrix"]
        all_classes = set().union(*map(set, matrix.values()))
        self.assertEqual(
            {
                "staff_line", "tab_line", "notehead", "stem", "beam_or_flag",
                "rest", "accidental", "clef", "barline", "tie_or_slur",
                "tab_digit", "tab_string",
            },
            all_classes,
        )
        self.assertEqual(10, len(strategy["classStrategies"]))
        self.assertFalse(strategy["principles"]["audiverisIncluded"])
        for value in strategy["claimBoundary"].values():
            self.assertFalse(value)


if __name__ == "__main__":
    unittest.main()
