from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

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


def test_review_authorization_is_exact_and_does_not_accept_evidence() -> None:
    value = validate_held_out_evaluation_review_authorization(load(AUTH))
    assert value["decision"] == "AUTHORIZE_STAGE4_HELD_OUT_EVALUATION_EVIDENCE_REVIEW"
    assert value["scope"]["reuseExistingRealExecutionEvidence"] is True
    assert value["scope"]["newArtifactExecutionRequired"] is False
    assert value["assertions"]["stage4HeldOutEvidenceAccepted"] is False
    assert len(AUTHORIZATION_CANONICAL_SHA256) == 64


def test_candidate_reuses_real_stage3_chopin_execution_and_stops_at_acceptance_review() -> None:
    candidate, auth, stage3, stage3_acceptance, development_acceptance, metric_policy_acceptance = inputs()
    value = validate_held_out_evaluation_evidence_candidate(
        candidate,
        auth,
        stage3,
        stage3_acceptance,
        development_acceptance,
        metric_policy_acceptance,
    )
    assert value["state"] == "ready_pending_separate_acceptance"
    assert value["realExecutionReceipt"]["pageCount"] == 8
    assert value["realExecutionReceipt"]["renderedPageCount"] == 8
    assert value["evaluationSummary"]["candidateDerivedCount"] == 0
    assert value["evaluationSummary"]["coverageRate"] == 0.0
    assert value["evaluationSummary"]["exactMatchRate"] == "not_applicable"
    assert value["evaluationSummary"]["sourceFamilyLeakageCount"] == 0
    assert value["evaluationSummary"]["heldOutThresholdTuningUsed"] is False
    assert value["evaluationSummary"]["evaluationFedBackIntoCandidate"] is False
    assert value["assertions"]["heldOutEvaluationEvidenceAccepted"] is False
    assert len(EVIDENCE_CANONICAL_SHA256) == 64


def test_summary_keeps_only_held_out_evidence_acceptance_blocker() -> None:
    summary = summarize_held_out_evaluation_evidence_candidate(load(CANDIDATE))
    assert summary["heldOutEvaluationEvidenceAccepted"] is False
    assert summary["remainingReadinessBlockers"] == ["no_real_held_out_evaluation_evidence_is_accepted"]
    assert summary["stage4ExitPass"] is False
    assert summary["stage5EntryAuthorized"] is False


def test_candidate_rejects_fake_assessed_metrics_in_zero_candidate_mode() -> None:
    candidate, auth, stage3, stage3_acceptance, development_acceptance, metric_policy_acceptance = inputs()
    tampered = deepcopy(candidate)
    tampered["evaluationSummary"]["exactMatchRate"] = 1.0
    with pytest.raises(Stage4HeldOutEvaluationEvidenceError):
        validate_held_out_evaluation_evidence_candidate(
            tampered,
            auth,
            stage3,
            stage3_acceptance,
            development_acceptance,
            metric_policy_acceptance,
        )


def test_candidate_rejects_held_out_tuning() -> None:
    candidate, auth, stage3, stage3_acceptance, development_acceptance, metric_policy_acceptance = inputs()
    tampered = deepcopy(candidate)
    tampered["evaluationSummary"]["heldOutThresholdTuningUsed"] = True
    with pytest.raises(Stage4HeldOutEvaluationEvidenceError):
        validate_held_out_evaluation_evidence_candidate(
            tampered,
            auth,
            stage3,
            stage3_acceptance,
            development_acceptance,
            metric_policy_acceptance,
        )
