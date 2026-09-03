"""Validate public-safe Stage 4 expanded real development execution evidence.

The underlying 49-row private metric batch and raw metric values remain in
custody only. This module validates aggregate/digest execution evidence after
Beethoven + Barley + Wikimedia development execution. It does not accept that
evidence, authorize production threshold/resource changes, use held-out data,
grant Stage 4 PASS, or open Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_candidate_derivation import DERIVATION_METHODOLOGY_ID
from .stage4_expanded_development_calibration_runner import (
    EXPECTED_MEASURED_RECORD_COUNT,
    EXPECTED_MEASURED_SOURCE_FAMILY_COUNT,
    EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
    EXPECTED_RECORD_COUNT,
    RUNNER_CONTRACT_VERSION,
)
from .stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256 as BEETHOVEN_BARLEY_BUNDLE_SHA256,
)
from .stage4_wikimedia_expanded_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
)
from .stage4_wikimedia_reference_acceptance import (
    WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
)

EVIDENCE_SCHEMA_VERSION = "1.0.0"
EVIDENCE_ID = "stage4.expanded-real-development-calibration-execution.v1"
PRIVATE_METRIC_BATCH_SHA256 = "010789271c9046188964c23ee497651eb1adbf2ff5b952b2cda5b78ddc155b52"
QUALITY_CONFIGURATION_SHA256 = "1464fd126f663c55927edf3d8123b1528662d6740623027ae8d4d13b96866ee0"
EVIDENCE_CANONICAL_SHA256 = "552a85a68dd789bd00dc4cb7ce6db38078a77c45297a7e5f716d008eae908b0c"

_EXPECTED_RUNTIME = {
    "pythonVersion": "3.12.14",
    "numpyVersion": "2.3.5",
    "opencvPythonHeadlessVersion": "4.13.0.92",
    "pypdfium2Version": "5.13.0",
    "qualityAnalyzerVersion": "0.1.1",
    "pdfRenderDpi": 200,
}

_EXPECTED_OUTCOMES: dict[str, dict[str, Any]] = {
    "blur": {
        "metricName": "laplacianVariance",
        "status": "abstained",
        "measuredObservationCount": 5,
        "referenceClassCounts": {"clear": 4, "possible": 1, "probable": 0, "not_assessed": 0},
        "reasonCodes": ["insufficient_reference_class_support"],
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": "83c51d86e4ba0a040db58f3f8e9b2b5d55eec07f84c65af7345adbc87b3cd705"},
    },
    "compression": {
        "metricName": "score",
        "status": "not_applicable",
        "measuredObservationCount": 0,
        "referenceClassCounts": {"clear": 0, "possible": 0, "probable": 0, "not_assessed": 0},
        "reasonCodes": ["no_measured_development_observations"],
        "privateDerivationReportDigest": None,
    },
    "glare": {
        "metricName": "score",
        "status": "abstained",
        "measuredObservationCount": 5,
        "referenceClassCounts": {"clear": 5, "possible": 0, "probable": 0, "not_assessed": 0},
        "reasonCodes": ["insufficient_reference_class_support"],
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": "298e87a66e1a4353d72574f5b29dae5b18092a52b0b71d38040d0e5d9253af31"},
    },
    "noise": {
        "metricName": "residualP90",
        "status": "abstained",
        "measuredObservationCount": 5,
        "referenceClassCounts": {"clear": 1, "possible": 3, "probable": 1, "not_assessed": 0},
        "reasonCodes": ["clear_possible_metric_overlap", "possible_probable_metric_overlap"],
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": "ac26a585a99503f093e1b1711020dd3131ca1c8badc482131e403e4f239743be"},
    },
    "shadow": {
        "metricName": "strength",
        "status": "abstained",
        "measuredObservationCount": 5,
        "referenceClassCounts": {"clear": 5, "possible": 0, "probable": 0, "not_assessed": 0},
        "reasonCodes": ["insufficient_reference_class_support"],
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": "bdb8b3cb90f168d6d18f7e856f67467ab45ddaae5132bc721d41184031a94e53"},
    },
    "skew": {
        "metricName": "absoluteAngleDegrees",
        "status": "abstained",
        "measuredObservationCount": 5,
        "referenceClassCounts": {"clear": 5, "possible": 0, "probable": 0, "not_assessed": 0},
        "reasonCodes": ["insufficient_reference_class_support"],
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": "94db50a338ff316848e9592768622474b05de6fa5f1739a9bf2f8a46984f3305"},
    },
    "uneven_lighting": {
        "metricName": "coefficientOfVariation",
        "status": "abstained",
        "measuredObservationCount": 5,
        "referenceClassCounts": {"clear": 5, "possible": 0, "probable": 0, "not_assessed": 0},
        "reasonCodes": ["insufficient_reference_class_support"],
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": "fb0270362b4cc75501dcd4198b786a667dfdaa77fe9a04a8d8932cd43d85afd7"},
    },
}


class Stage4ExpandedRealDevelopmentExecutionEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4ExpandedRealDevelopmentExecutionEvidenceError(message)


def validate_expanded_real_development_execution_evidence(raw: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(raw, Mapping), "expanded execution evidence must be an object")
    value = deepcopy(dict(raw))
    digest_obj = value.pop("evidenceDigest", None)
    _require(
        digest_obj == {"algorithm": "sha256", "value": EVIDENCE_CANONICAL_SHA256},
        "expanded evidence digest field drifted",
    )
    _require(canonical_sha256(value) == EVIDENCE_CANONICAL_SHA256, "expanded evidence canonical digest mismatch")
    _require(value.get("schemaVersion") == EVIDENCE_SCHEMA_VERSION, "schema version drifted")
    _require(value.get("evidenceId") == EVIDENCE_ID, "evidence id drifted")
    _require(value.get("state") == "executed_abstained", "execution state drifted")
    _require(value.get("executedOn") == "2026-09-03", "execution date drifted")

    scope = value.get("scope") or {}
    _require(scope.get("purpose") == "safety_calibration", "purpose drifted")
    _require(scope.get("split") == "development" and scope.get("dataClass") == "real", "development-only scope drifted")
    _require(scope.get("environment") == "stage1_offline", "execution environment drifted")
    _require(scope.get("authorizedDatasetItemCount") == 3, "authorized item count drifted")
    _require(scope.get("referenceRecordCount") == EXPECTED_RECORD_COUNT == 49, "reference record count drifted")
    _require(scope.get("privateMetricRecordCount") == EXPECTED_RECORD_COUNT == 49, "private metric record count drifted")
    _require(scope.get("measuredRecordCount") == EXPECTED_MEASURED_RECORD_COUNT == 30, "measured record count drifted")
    _require(scope.get("notApplicableRecordCount") == EXPECTED_NOT_APPLICABLE_RECORD_COUNT == 19, "not-applicable record count drifted")
    _require(scope.get("measuredSourceFamilyCount") == EXPECTED_MEASURED_SOURCE_FAMILY_COUNT == 2, "measured source-family count drifted")

    bindings = value.get("bindings") or {}
    _require(bindings.get("authorizationDigest") == {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256}, "authorization digest drifted")
    _require(
        bindings.get("referenceBundleDigests") == {
            "beethovenBarley": {"algorithm": "sha256", "value": BEETHOVEN_BARLEY_BUNDLE_SHA256},
            "wikimedia": {"algorithm": "sha256", "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256},
        },
        "reference bundle digests drifted",
    )
    _require(bindings.get("privateMetricBatchDigest") == {"algorithm": "sha256", "value": PRIVATE_METRIC_BATCH_SHA256}, "private metric batch digest drifted")
    _require(bindings.get("runnerContractVersion") == RUNNER_CONTRACT_VERSION == "0.3.1", "runner contract drifted")
    _require(bindings.get("candidateDerivationMethodologyId") == DERIVATION_METHODOLOGY_ID, "candidate methodology drifted")
    _require(bindings.get("qualityConfigurationDigest") == {"algorithm": "sha256", "value": QUALITY_CONFIGURATION_SHA256}, "quality configuration digest drifted")

    _require(value.get("executionRuntime") == _EXPECTED_RUNTIME, "execution runtime drifted")

    outcomes = value.get("findingOutcomes")
    _require(isinstance(outcomes, list) and len(outcomes) == 7, "finding outcomes must contain seven findings")
    by_type = {item.get("findingType"): item for item in outcomes if isinstance(item, Mapping)}
    _require(set(by_type) == set(_EXPECTED_OUTCOMES), "finding set drifted")
    for finding, expected in _EXPECTED_OUTCOMES.items():
        item = by_type[finding]
        for key, expected_value in expected.items():
            _require(item.get(key) == expected_value, f"{finding} {key} drifted")

    summary = value.get("summary") or {}
    _require(
        summary == {
            "candidateDerivedCount": 0,
            "abstainedFindingCount": 6,
            "notApplicableFindingCount": 1,
            "thresholdsCalibrated": False,
            "crossFamilyMeasuredSupportSatisfied": True,
        },
        "expanded execution summary drifted",
    )

    assertions = value.get("assertions") or {}
    _require(assertions.get("realDataCalibrationExecuted") is True, "real execution claim missing")
    _require(assertions.get("developmentEvidenceOnly") is True, "development-only assertion drifted")
    for key in (
        "privateMetricRowsPublic",
        "rawMetricValuesPublic",
        "artifactBytesPublic",
        "derivativeBytesPublic",
        "candidateThresholdValuesPublic",
        "heldOutThresholdTuningUsed",
        "heldOutEvaluationUsed",
        "thresholdsCalibrated",
        "resourceLimitsCalibrated",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "metricAcceptanceTargetPolicyApplied",
        "modelTrainingAuthorized",
        "publicationAuthorized",
        "executionEvidenceAccepted",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        _require(assertions.get(key) is False, f"unsafe assertion became true: {key}")

    rendered = str(value)
    for forbidden in (
        "rawValue",
        "observationId",
        "datasetItemId",
        "sourceFamilyId",
        "provenanceReference",
        "possibleThreshold",
        "probableThreshold",
        "candidateManifest",
    ):
        _require(forbidden not in rendered, f"public expanded execution evidence leaked private field: {forbidden}")

    value["evidenceDigest"] = digest_obj
    return value


__all__ = [
    "EVIDENCE_CANONICAL_SHA256",
    "EVIDENCE_ID",
    "PRIVATE_METRIC_BATCH_SHA256",
    "QUALITY_CONFIGURATION_SHA256",
    "Stage4ExpandedRealDevelopmentExecutionEvidenceError",
    "validate_expanded_real_development_execution_evidence",
]
