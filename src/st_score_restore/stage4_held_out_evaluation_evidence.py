"""Fail-closed Stage 4 held-out evaluation evidence bridge.

The Stage 4 zero-candidate policy does not require a second execution of the
Chopin artifact. This module binds the accepted zero-candidate development
state to the immutable real Stage 3 held-out execution receipt. It cannot tune
thresholds, feed evaluation results back into candidate derivation, accept the
held-out evidence, grant Stage 4 PASS, or open Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256

SCHEMA_VERSION = "1.0.0"
HELD_OUT_DATASET_ITEM_ID = "dataset.item.imslp82860-chopin-op69.v2"
HELD_OUT_SOURCE_FAMILY_ID = "source.family.imslp82860-chopin-op69.v1"
HELD_OUT_ARTIFACT_SHA256 = "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3"
HELD_OUT_BYTE_SIZE = 1114479
HELD_OUT_PAGE_COUNT = 8

AUTHORIZATION_ID = "stage4.held-out-evaluation-evidence-review-authorization.chopin-op69.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_STAGE4_HELD_OUT_EVALUATION_EVIDENCE_REVIEW"
AUTHORIZATION_CANONICAL_SHA256 = "934bb1cac10a6c421923aeb72741cc63097983b7c50d4326d1b9f12dc5d7eb38"
AUTHORIZATION_AUTHORITY = "authority:project-governance-owner-20260903-06"

EVIDENCE_ID = "stage4.held-out-evaluation-evidence.chopin-op69.zero-candidate.v1"
EVIDENCE_STATE = "ready_pending_separate_acceptance"
EVIDENCE_CANONICAL_SHA256 = "45dc380effe34d7f35ec9af2f05f802eaca9194fa8a889d1aaefae87c5221219"

STAGE3_EXECUTION_EVIDENCE_DIGEST = "a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6"
STAGE3_HELD_OUT_RECEIPT_DIGEST = "6c61bfcc1197779aa6fc7de68d536a39b2fba62c230cafdee50d5616005e1ce9"
STAGE3_EXIT_ACCEPTANCE_DIGEST = "e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90"
DEVELOPMENT_EXECUTION_ACCEPTANCE_DIGEST = "4b891f3263c542c59d5632732c8010ef1bc6aeba17dfd71ffbde9ee6ed7be396"
METRIC_POLICY_ACCEPTANCE_DIGEST = "bf62d308f70ca44db617cf2968485e422627abfce70643c78b4da20d58d04801"


class Stage4HeldOutEvaluationEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4HeldOutEvaluationEvidenceError(message)


def validate_held_out_evaluation_review_authorization(raw: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "held-out review authorization must be an object")
    value = deepcopy(dict(raw))
    _require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "held-out review authorization digest drifted")
    _require(value.get("schemaVersion") == SCHEMA_VERSION, "held-out review authorization schema drifted")
    _require(value.get("authorizationId") == AUTHORIZATION_ID, "held-out review authorization id drifted")
    _require(value.get("decision") == AUTHORIZATION_DECISION, "held-out evidence review is not authorized")
    _require(value.get("authorizedOn") == "2026-09-03", "held-out review authorization date drifted")
    _require(value.get("decisionAuthorityReference") == AUTHORIZATION_AUTHORITY, "held-out review authority drifted")
    _require(value.get("authorizationSourceCode") == "explicit_user_authorization", "held-out review authorization source drifted")

    _require(
        value.get("scope") == {
            "stage": 4,
            "datasetItemId": HELD_OUT_DATASET_ITEM_ID,
            "sourceFamilyId": HELD_OUT_SOURCE_FAMILY_ID,
            "artifactSha256": HELD_OUT_ARTIFACT_SHA256,
            "split": "held_out",
            "purpose": "held_out_evaluation",
            "reuseExistingRealExecutionEvidence": True,
            "newArtifactExecutionRequired": False,
            "candidateDerivationAuthorized": False,
            "thresholdTuningAuthorized": False,
            "evaluationFeedbackIntoCandidateAuthorized": False,
        },
        "held-out review authorization scope drifted or became permissive",
    )
    _require(
        value.get("bindings") == {
            "stage3RealCorpusExecutionEvidenceDigest": STAGE3_EXECUTION_EVIDENCE_DIGEST,
            "stage3ExitAcceptanceDigest": STAGE3_EXIT_ACCEPTANCE_DIGEST,
            "stage4ExpandedDevelopmentExecutionAcceptanceDigest": DEVELOPMENT_EXECUTION_ACCEPTANCE_DIGEST,
            "stage4MetricPolicyAcceptanceDigest": METRIC_POLICY_ACCEPTANCE_DIGEST,
        },
        "held-out review authorization bindings drifted",
    )
    assertions = value.get("assertions", {})
    _require(assertions.get("historicalHeldOutPurposeAuthorizationPreserved") is True, "historical held-out purpose authorization was not preserved")
    _require(assertions.get("historicalRealHeldOutExecutionPresent") is True, "historical real held-out execution missing")
    _require(assertions.get("stage4HeldOutEvidenceReviewAuthorized") is True, "Stage 4 held-out evidence review authorization missing")
    for key in (
        "stage4HeldOutEvidenceAccepted",
        "heldOutThresholdTuningAuthorized",
        "heldOutThresholdTuningUsed",
        "evaluationFedBackIntoCandidate",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        _require(assertions.get(key) is False, f"unsafe held-out authorization flag became true: {key}")
    return value


def validate_held_out_evaluation_evidence_candidate(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    stage3_execution_raw: Mapping[str, Any],
    stage3_exit_acceptance_raw: Mapping[str, Any],
    development_acceptance_raw: Mapping[str, Any],
    metric_policy_acceptance_raw: Mapping[str, Any],
) -> dict[str, Any]:
    validate_held_out_evaluation_review_authorization(authorization_raw)
    _require(isinstance(raw, Mapping), "held-out evaluation evidence candidate must be an object")
    value = deepcopy(dict(raw))
    _require(canonical_sha256(value) == EVIDENCE_CANONICAL_SHA256, "held-out evaluation evidence digest drifted")
    _require(value.get("schemaVersion") == SCHEMA_VERSION, "held-out evidence schema drifted")
    _require(value.get("evidenceId") == EVIDENCE_ID, "held-out evidence id drifted")
    _require(value.get("state") == EVIDENCE_STATE, "held-out evidence must remain pending separate acceptance")
    _require(value.get("mode") == "zero_candidate_safe_abstention", "held-out evidence mode drifted")

    _require(
        value.get("scope") == {
            "stage": 4,
            "datasetItemId": HELD_OUT_DATASET_ITEM_ID,
            "sourceFamilyId": HELD_OUT_SOURCE_FAMILY_ID,
            "artifactSha256": HELD_OUT_ARTIFACT_SHA256,
            "split": "held_out",
            "purpose": "held_out_evaluation",
        },
        "held-out evidence scope drifted",
    )
    _require(
        value.get("bindings") == {
            "reviewAuthorizationDigest": AUTHORIZATION_CANONICAL_SHA256,
            "stage3RealCorpusExecutionEvidenceDigest": STAGE3_EXECUTION_EVIDENCE_DIGEST,
            "stage3HeldOutReceiptDigest": STAGE3_HELD_OUT_RECEIPT_DIGEST,
            "stage3ExitAcceptanceDigest": STAGE3_EXIT_ACCEPTANCE_DIGEST,
            "stage4ExpandedDevelopmentExecutionAcceptanceDigest": DEVELOPMENT_EXECUTION_ACCEPTANCE_DIGEST,
            "stage4MetricPolicyAcceptanceDigest": METRIC_POLICY_ACCEPTANCE_DIGEST,
        },
        "held-out evidence bindings drifted",
    )

    _require(stage3_execution_raw.get("evidenceDigest") == {"algorithm": "sha256", "value": STAGE3_EXECUTION_EVIDENCE_DIGEST}, "Stage 3 execution evidence binding drifted")
    receipts = [item for item in stage3_execution_raw.get("receipts", []) if item.get("datasetItemId") == HELD_OUT_DATASET_ITEM_ID]
    _require(len(receipts) == 1, "exactly one Chopin held-out Stage 3 receipt is required")
    receipt = receipts[0]
    _require(receipt.get("receiptDigest") == {"algorithm": "sha256", "value": STAGE3_HELD_OUT_RECEIPT_DIGEST}, "Stage 3 held-out receipt digest drifted")
    _require(receipt.get("sourceDigest") == {"algorithm": "sha256", "value": HELD_OUT_ARTIFACT_SHA256}, "held-out source digest drifted")
    _require(receipt.get("byteSize") == HELD_OUT_BYTE_SIZE, "held-out byte size drifted")
    _require(receipt.get("split") == "held_out" and receipt.get("purpose") == "held_out_evaluation", "held-out purpose/split drifted")
    _require(receipt.get("status") == "completed", "historical real held-out execution is not completed")
    _require(receipt.get("pageSummary", {}).get("pageCount") == HELD_OUT_PAGE_COUNT, "held-out page count drifted")
    _require(receipt.get("pageSummary", {}).get("renderedPageCount") == HELD_OUT_PAGE_COUNT, "held-out rendered page count drifted")
    _require(receipt.get("pageSummary", {}).get("pageOrderPreserved") is True, "held-out page order was not preserved")
    _require(receipt.get("assertions", {}).get("exactDigestMatched") is True, "held-out exact digest was not matched")
    _require(receipt.get("assertions", {}).get("exactByteSizeMatched") is True, "held-out exact byte size was not matched")
    _require(receipt.get("assertions", {}).get("heldOutThresholdTuningUsed") is False, "historical held-out tuning was used")

    _require(canonical_sha256(stage3_exit_acceptance_raw) == STAGE3_EXIT_ACCEPTANCE_DIGEST, "Stage 3 exit acceptance digest drifted")
    _require(stage3_exit_acceptance_raw.get("decision") == "PASS", "Stage 3 exit was not accepted")
    _require(stage3_exit_acceptance_raw.get("gates", {}).get("heldOutNonTuning") == "pass", "Stage 3 held-out non-tuning gate is not pass")

    _require(canonical_sha256(development_acceptance_raw) == DEVELOPMENT_EXECUTION_ACCEPTANCE_DIGEST, "accepted development execution digest drifted")
    _require(development_acceptance_raw.get("decision") == "ACCEPT_EXPANDED_REAL_DEVELOPMENT_EXECUTION_EVIDENCE", "development execution evidence is not accepted")
    _require(development_acceptance_raw.get("scope", {}).get("candidateDerivedCount") == 0, "held-out zero-candidate bridge requires candidateDerivedCount=0")
    _require(development_acceptance_raw.get("scope", {}).get("heldOutIncluded") is False, "held-out data leaked into development evidence")

    _require(canonical_sha256(metric_policy_acceptance_raw) == METRIC_POLICY_ACCEPTANCE_DIGEST, "metric-policy acceptance digest drifted")
    _require(metric_policy_acceptance_raw.get("decision") == "ACCEPT_STAGE4_METRIC_ACCEPTANCE_TARGET_POLICY", "metric target policy is not accepted")
    _require(metric_policy_acceptance_raw.get("scope", {}).get("currentMode") == "zero_candidate_safe_abstention", "accepted metric policy mode drifted")
    targets = metric_policy_acceptance_raw.get("acceptedTargets", {})
    _require(targets.get("sourceFamilyLeakageCount") == 0, "accepted leakage target drifted")
    _require(targets.get("heldOutThresholdTuningUsed") is False, "accepted non-tuning target drifted")
    _require(targets.get("evaluationFedBackIntoCandidate") is False, "accepted no-feedback target drifted")
    _require(targets.get("zeroCandidateCoverageMayBeZero") is True, "zero-candidate coverage rule drifted")
    _require(targets.get("rateMetricsNotApplicableWhenAssessedCountZero") is True, "zero-assessed rate rule drifted")

    expected_receipt = {
        "status": "completed",
        "purpose": "held_out_evaluation",
        "split": "held_out",
        "environment": "stage1_offline",
        "storageClass": "managed_standard",
        "sourceSha256": HELD_OUT_ARTIFACT_SHA256,
        "byteSize": HELD_OUT_BYTE_SIZE,
        "pageCount": HELD_OUT_PAGE_COUNT,
        "renderedPageCount": HELD_OUT_PAGE_COUNT,
        "pageOrderPreserved": True,
        "exactDigestMatched": True,
        "exactByteSizeMatched": True,
    }
    _require(value.get("realExecutionReceipt") == expected_receipt, "Stage 4 public held-out receipt summary drifted")

    summary = value.get("evaluationSummary", {})
    _require(summary.get("candidateDerivedCount") == 0, "held-out candidate count must be zero")
    _require(summary.get("candidateAppliedCount") == 0 and summary.get("assessedCandidateCount") == 0, "zero-candidate held-out review cannot assess/apply candidates")
    _require(summary.get("coverageRate") == 0.0, "zero-candidate coverage must be 0.0")
    for key in ("notAssessedRate", "exactMatchRate", "falseNegativeRate", "falsePositiveRate"):
        _require(summary.get(key) == "not_applicable", f"{key} must be not_applicable in zero-assessed mode")
    _require(summary.get("sourceFamilyLeakageCount") == 0, "source-family leakage detected")
    _require(summary.get("heldOutThresholdTuningUsed") is False, "held-out threshold tuning was used")
    _require(summary.get("evaluationFedBackIntoCandidate") is False, "held-out evaluation fed back into candidate derivation")
    _require(summary.get("productionThresholdChangeAuthorized") is False, "held-out evidence authorized production threshold changes")
    _require(summary.get("productionResourceLimitChangeAuthorized") is False, "held-out evidence authorized resource-limit changes")
    _require(summary.get("decision") == "ELIGIBLE_FOR_SEPARATE_HELD_OUT_EVIDENCE_ACCEPTANCE_REVIEW", "held-out evidence must stop at separate acceptance review")

    assertions = value.get("assertions", {})
    _require(assertions.get("realHeldOutArtifactPreviouslyExecuted") is True, "real held-out execution provenance missing")
    _require(assertions.get("stage4HeldOutEvidenceBridgePerformed") is True, "Stage 4 evidence bridge not performed")
    _require(assertions.get("newHeldOutArtifactExecutionPerformed") is False, "bridge must not claim a new held-out artifact execution")
    for key in (
        "heldOutEvaluationEvidenceAccepted",
        "heldOutThresholdTuningUsed",
        "evaluationFedBackIntoCandidate",
        "candidateThresholdsAccepted",
        "thresholdsCalibrated",
        "resourceLimitsCalibrated",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        _require(assertions.get(key) is False, f"unsafe held-out evidence flag became true: {key}")
    return value


def summarize_held_out_evaluation_evidence_candidate(raw: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "held-out evaluation evidence candidate must be an object")
    _require(canonical_sha256(raw) == EVIDENCE_CANONICAL_SHA256, "held-out evaluation evidence digest drifted")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "state": EVIDENCE_STATE,
        "evidenceDigest": {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256},
        "heldOutDatasetItemId": HELD_OUT_DATASET_ITEM_ID,
        "mode": "zero_candidate_safe_abstention",
        "candidateDerivedCount": 0,
        "heldOutEvaluationEvidenceAccepted": False,
        "remainingReadinessBlockers": ["no_real_held_out_evaluation_evidence_is_accepted"],
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "AUTHORIZATION_CANONICAL_SHA256",
    "EVIDENCE_CANONICAL_SHA256",
    "EVIDENCE_ID",
    "EVIDENCE_STATE",
    "HELD_OUT_DATASET_ITEM_ID",
    "Stage4HeldOutEvaluationEvidenceError",
    "summarize_held_out_evaluation_evidence_candidate",
    "validate_held_out_evaluation_evidence_candidate",
    "validate_held_out_evaluation_review_authorization",
]
