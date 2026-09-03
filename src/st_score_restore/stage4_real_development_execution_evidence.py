"""Validate the public-safe Stage 4 real development execution receipt."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_development_calibration_runner import RUNNER_CONTRACT_VERSION
from .stage4_candidate_derivation import DERIVATION_METHODOLOGY_ID
from .stage4_execution_authorization import AUTHORIZATION_CANONICAL_SHA256
from .stage4_reference_label_completion import BUNDLE_CANONICAL_SHA256

EVIDENCE_SCHEMA_VERSION = "1.0.0"
EVIDENCE_ID = "stage4.real-development-calibration-execution.v1"
PRIVATE_METRIC_BATCH_SHA256 = "5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079"
EVIDENCE_CANONICAL_SHA256 = "0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a"


class Stage4RealDevelopmentExecutionEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4RealDevelopmentExecutionEvidenceError(message)


def validate_real_development_execution_evidence(raw: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "evidence must be an object")
    value = deepcopy(dict(raw))
    digest_obj = value.pop("evidenceDigest", None)
    _require(digest_obj == {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256}, "evidence digest field drifted")
    _require(canonical_sha256(value) == EVIDENCE_CANONICAL_SHA256, "evidence canonical digest mismatch")
    _require(value.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "schema version drifted")
    _require(value.get("evidenceId") == EVIDENCE_ID, "evidence id drifted")
    _require(value.get("state") == "executed_abstained", "execution state drifted")
    _require(value.get("executedOn") == "2026-09-03", "execution date drifted")

    scope = value.get("scope") or {}
    _require(scope.get("purpose") == "safety_calibration", "purpose drifted")
    _require(scope.get("split") == "development" and scope.get("dataClass") == "real", "development-only scope drifted")
    _require(scope.get("privateMetricRecordCount") == 42, "private metric record count drifted")
    _require(scope.get("measuredRecordCount") == 24, "measured record count drifted")
    _require(scope.get("notApplicableRecordCount") == 18, "not-applicable record count drifted")
    _require(scope.get("measuredSourceFamilyCount") == 1, "measured source-family count drifted")

    bindings = value.get("bindings") or {}
    _require(bindings.get("authorizationDigest") == {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256}, "authorization digest drifted")
    _require(bindings.get("referenceBundleDigest") == {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256}, "reference bundle digest drifted")
    _require(bindings.get("privateMetricBatchDigest") == {"algorithm": "sha256", "value": PRIVATE_METRIC_BATCH_SHA256}, "private metric batch digest drifted")
    _require(bindings.get("runnerContractVersion") == RUNNER_CONTRACT_VERSION == "0.2.0", "runner contract drifted")
    _require(bindings.get("candidateDerivationMethodologyId") == DERIVATION_METHODOLOGY_ID, "candidate methodology drifted")

    outcomes = value.get("findingOutcomes")
    _require(isinstance(outcomes, list) and len(outcomes) == 7, "finding outcomes must contain seven findings")
    by_type = {item.get("findingType"): item for item in outcomes if isinstance(item, Mapping)}
    _require(set(by_type) == {"skew", "blur", "glare", "shadow", "uneven_lighting", "noise", "compression"}, "finding set drifted")
    _require(by_type["compression"].get("status") == "not_applicable" and by_type["compression"].get("measuredObservationCount") == 0, "compression applicability drifted")
    for finding in {"skew", "blur", "glare", "shadow", "uneven_lighting", "noise"}:
        item = by_type[finding]
        _require(item.get("status") == "abstained", f"{finding} must remain abstained")
        _require(item.get("measuredObservationCount") == 4, f"{finding} measured count drifted")
        reasons = set(item.get("reasonCodes") or [])
        _require("insufficient_source_family_support" in reasons, f"{finding} lost cross-family abstention")
        _require("insufficient_reference_class_support" in reasons, f"{finding} lost class-support abstention")

    summary = value.get("summary") or {}
    _require(summary == {"candidateDerivedCount": 0, "abstainedFindingCount": 6, "notApplicableFindingCount": 1, "thresholdsCalibrated": False}, "execution summary drifted")
    assertions = value.get("assertions") or {}
    _require(assertions.get("realDataCalibrationExecuted") is True, "real execution non-claim drifted")
    for key in (
        "privateMetricRowsPublic", "rawMetricValuesPublic", "artifactBytesPublic", "derivativeBytesPublic",
        "heldOutThresholdTuningUsed", "heldOutEvaluationUsed", "thresholdsCalibrated", "resourceLimitsCalibrated",
        "productionThresholdChangeAuthorized", "productionResourceLimitChangeAuthorized", "metricAcceptanceTargetPolicyApplied",
        "modelTrainingAuthorized", "publicationAuthorized", "executionEvidenceAccepted", "stage4ExitPass", "stage5EntryAuthorized",
    ):
        _require(assertions.get(key) is False, f"unsafe assertion became true: {key}")

    rendered = str(value)
    for forbidden in ("rawValue", "observationId", "datasetItemId", "sourceFamilyId", "provenanceReference"):
        _require(forbidden not in rendered, f"public execution evidence leaked private field: {forbidden}")
    value["evidenceDigest"] = digest_obj
    return value


__all__ = [
    "EVIDENCE_CANONICAL_SHA256",
    "PRIVATE_METRIC_BATCH_SHA256",
    "Stage4RealDevelopmentExecutionEvidenceError",
    "validate_real_development_execution_evidence",
]
