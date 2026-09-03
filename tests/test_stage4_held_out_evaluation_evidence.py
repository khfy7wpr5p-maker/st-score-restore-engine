from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_held_out_evaluation_evidence import (
    AUTHORIZATION_CANONICAL_SHA256,
    EVIDENCE_CANONICAL_SHA256,
    Stage4HeldOutEvaluationEvidenceError,
    summarize_held_out_evaluation_evidence_candidate,
    validate_held_out_evaluation_evidence_candidate,
    validate_held_out_evaluation_review_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage4/governance/held-out-evaluation-evidence-review-authorization.v1.json"
CANDIDATE = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-candidate.v1.json"
STAGE3_EXECUTION = ROOT / "evidence/stage3/corpus/execution-evidence.v1.json"
STAGE3_ACCEPTANCE = ROOT / "evidence/stage3/corpus/stage3-exit-acceptance.v1.json"
DEVELOPMENT_ACCEPTANCE = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
METRIC_POLICY_ACCEPTANCE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def inputs() -> tuple[dict, dict, dict, dict, dict, dict]:
    return (
        load(CANDIDATE),
        load(AUTH),
        load(STAGE3_EXECUTION),
        load(STAGE3_ACCEPTANCE),
        load(DEVELOPMENT_ACCEPTANCE),
        load(METRIC_POLICY_ACCEPTANCE),
    )


class Stage4HeldOutEvaluationEvidenceTests(unittest.TestCase):
    def test_review_authorization_is_exact_and_does_not_accept_evidence(self) -> None:
        value = validate_held_out_evaluation_review_authorization(load(AUTH))
        self.assertEqual(value["decision"], "AUTHORIZE_STAGE4_HELD_OUT_EVALUATION_EVIDENCE_REVIEW")
        self.assertIs(value["scope"]["reuseExistingRealExecutionEvidence"], True)
        self.assertIs(value["scope"]["newArtifactExecutionRequired"], False)
        self.assertIs(value["assertions"]["stage4HeldOutEvidenceAccepted"], False)
        self.assertEqual(len(AUTHORIZATION_CANONICAL_SHA256), 64)

    def test_candidate_reuses_real_stage3_chopin_execution_and_stops_at_acceptance_review(self) -> None:
        candidate, auth, stage3, stage3_acceptance, development_acceptance, metric_policy_acceptance = inputs()
        value = validate_held_out_evaluation_evidence_candidate(
            candidate,
            auth,
            stage3,
            stage3_acceptance,
            development_acceptance,
            metric_policy_acceptance,
        )
        self.assertEqual(value["state"], "ready_pending_separate_acceptance")
        self.assertEqual(value["realExecutionReceipt"]["pageCount"], 8)
        self.assertEqual(value["realExecutionReceipt"]["renderedPageCount"], 8)
        self.assertEqual(value["evaluationSummary"]["candidateDerivedCount"], 0)
        self.assertEqual(value["evaluationSummary"]["coverageRate"], 0.0)
        self.assertEqual(value["evaluationSummary"]["exactMatchRate"], "not_applicable")
        self.assertEqual(value["evaluationSummary"]["sourceFamilyLeakageCount"], 0)
        self.assertIs(value["evaluationSummary"]["heldOutThresholdTuningUsed"], False)
        self.assertIs(value["evaluationSummary"]["evaluationFedBackIntoCandidate"], False)
        self.assertIs(value["assertions"]["heldOutEvaluationEvidenceAccepted"], False)
        self.assertEqual(len(EVIDENCE_CANONICAL_SHA256), 64)

    def test_summary_keeps_only_held_out_evidence_acceptance_blocker(self) -> None:
        summary = summarize_held_out_evaluation_evidence_candidate(load(CANDIDATE))
        self.assertIs(summary["heldOutEvaluationEvidenceAccepted"], False)
        self.assertEqual(summary["remainingReadinessBlockers"], ["no_real_held_out_evaluation_evidence_is_accepted"])
        self.assertIs(summary["stage4ExitPass"], False)
        self.assertIs(summary["stage5EntryAuthorized"], False)

    def test_candidate_rejects_fake_assessed_metrics_in_zero_candidate_mode(self) -> None:
        candidate, auth, stage3, stage3_acceptance, development_acceptance, metric_policy_acceptance = inputs()
        tampered = deepcopy(candidate)
        tampered["evaluationSummary"]["exactMatchRate"] = 1.0
        with self.assertRaises(Stage4HeldOutEvaluationEvidenceError):
            validate_held_out_evaluation_evidence_candidate(
                tampered,
                auth,
                stage3,
                stage3_acceptance,
                development_acceptance,
                metric_policy_acceptance,
            )

    def test_candidate_rejects_held_out_tuning(self) -> None:
        candidate, auth, stage3, stage3_acceptance, development_acceptance, metric_policy_acceptance = inputs()
        tampered = deepcopy(candidate)
        tampered["evaluationSummary"]["heldOutThresholdTuningUsed"] = True
        with self.assertRaises(Stage4HeldOutEvaluationEvidenceError):
            validate_held_out_evaluation_evidence_candidate(
                tampered,
                auth,
                stage3,
                stage3_acceptance,
                development_acceptance,
                metric_policy_acceptance,
            )


if __name__ == "__main__":
    unittest.main()
