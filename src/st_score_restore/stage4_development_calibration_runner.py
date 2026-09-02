"""Fail-closed Stage 4 private-metric development calibration runner contract.

The runner validates private Beethoven + Barley observation metrics against the
production-effective execution authorization and accepted 42-record human
reference bundle. Raw metric rows stay outside ordinary Git. This module does
not select numerical thresholds, touch held-out data, authorize production
changes, train a model, publish private evidence, grant Stage 4 PASS, or open
Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping, Sequence

from .dataset_contract_common import canonical_sha256
from .stage4_calibration import CalibrationObservation
from .stage4_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    validate_stage4_execution_authorization,
)
from .stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256,
    validate_reference_label_completion,
)

RUNNER_CONTRACT_VERSION = "0.1.0"
PRIVATE_METRIC_SCHEMA_VERSION = "1.0.0"
EXPECTED_RECORD_COUNT = 42

METRIC_SPECS: dict[str, dict[str, str]] = {
    "skew": {"metricName": "absoluteAngleDegrees", "direction": "higher_is_worse"},
    "blur": {"metricName": "laplacianVariance", "direction": "lower_is_worse"},
    "glare": {"metricName": "score", "direction": "higher_is_worse"},
    "shadow": {"metricName": "strength", "direction": "higher_is_worse"},
    "uneven_lighting": {"metricName": "coefficientOfVariation", "direction": "higher_is_worse"},
    "noise": {"metricName": "residualP90", "direction": "higher_is_worse"},
    "compression": {"metricName": "score", "direction": "higher_is_worse"},
}
BOUNDED_UNIT_FINDINGS = frozenset({"glare", "shadow", "uneven_lighting", "noise", "compression"})


class Stage4DevelopmentCalibrationRunnerError(ValueError):
    """Private metric input is missing, unsafe, unbound, or out of scope."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Stage4DevelopmentCalibrationRunnerError(code, message)


def _finite_number(value: Any) -> float:
    _require(
        not isinstance(value, bool) and isinstance(value, (int, float)),
        "invalid_metric_value",
        "rawValue must be a finite number",
    )
    number = float(value)
    _require(math.isfinite(number), "invalid_metric_value", "rawValue must be finite")
    return number


def validate_private_metric_batch(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    purpose_raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a private 42-row development metric batch without publishing rows."""

    _require(isinstance(raw, Mapping), "invalid_private_metric_batch", "private metric batch must be an object")
    value = deepcopy(dict(raw))
    authorization = validate_stage4_execution_authorization(
        authorization_raw, purpose_raw, acceptance_raw, completion_raw
    )
    completion = validate_reference_label_completion(completion_raw)

    _require(
        set(value) == {
            "schemaVersion", "contractVersion", "batchId", "environment",
            "authorizationDigest", "referenceBundleDigest", "records"
        },
        "invalid_private_metric_batch",
        "private metric batch top-level fields drifted",
    )
    _require(value["schemaVersion"] == PRIVATE_METRIC_SCHEMA_VERSION, "invalid_private_metric_batch", "private metric schema drifted")
    _require(value["contractVersion"] == RUNNER_CONTRACT_VERSION, "invalid_private_metric_batch", "runner contract version drifted")
    _require(isinstance(value["batchId"], str) and value["batchId"].strip(), "invalid_private_metric_batch", "batchId is required")
    _require(value["environment"] == authorization["scope"]["environment"], "environment_mismatch", "private metric environment does not match authorization")
    _require(
        value["authorizationDigest"] == {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "authorization_mismatch",
        "private metric batch is not bound to the accepted execution authorization",
    )
    _require(
        value["referenceBundleDigest"] == {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "reference_bundle_mismatch",
        "private metric batch is not bound to the accepted reference bundle",
    )

    records = value["records"]
    _require(isinstance(records, Sequence) and not isinstance(records, (str, bytes)), "invalid_private_metric_batch", "records must be an array")
    _require(len(records) == EXPECTED_RECORD_COUNT, "record_count_mismatch", "private metric batch must contain exactly 42 records")

    reference_records = completion["bundle"]["records"]
    expected_by_observation = {record["observationId"]: record for record in reference_records}
    authorized_items = {
        item["datasetItemId"]: item
        for item in authorization["scope"]["datasetItems"]
    }
    seen: set[str] = set()

    required_fields = {
        "observationId", "datasetItemId", "artifactSha256", "sourceFamilyId",
        "findingType", "metricName", "direction", "rawValue", "split",
        "dataClass", "purpose", "provenanceReference"
    }
    forbidden_truth_fields = {"referenceLabel", "predictedLabel", "modelLabel", "reviewerReference"}

    for raw_record in records:
        _require(isinstance(raw_record, Mapping), "invalid_private_metric_record", "private metric record must be an object")
        record = dict(raw_record)
        _require(not (set(record) & forbidden_truth_fields), "reference_truth_in_private_metrics", "private metric rows must not carry reference/model labels")
        _require(set(record) == required_fields, "invalid_private_metric_record", "private metric record fields drifted")

        observation_id = record["observationId"]
        _require(isinstance(observation_id, str) and observation_id in expected_by_observation, "observation_identity_mismatch", "unknown private metric observationId")
        _require(observation_id not in seen, "duplicate_observation", "duplicate private metric observationId")
        seen.add(observation_id)

        expected = expected_by_observation[observation_id]
        item_id = record["datasetItemId"]
        _require(item_id == expected["datasetItemId"], "observation_identity_mismatch", "datasetItemId does not match accepted label")
        _require(item_id in authorized_items, "authorization_mismatch", "dataset item is outside authorized execution scope")
        authorized_item = authorized_items[item_id]
        _require(record["artifactSha256"] == authorized_item["artifactSha256"], "artifact_identity_mismatch", "artifact SHA does not match authorization")
        _require(record["sourceFamilyId"] == expected["sourceFamilyId"] == authorized_item["sourceFamilyId"], "source_family_mismatch", "source family does not match accepted evidence")
        _require(record["findingType"] == expected["findingType"], "finding_identity_mismatch", "finding type does not match accepted label")

        finding = record["findingType"]
        _require(finding in METRIC_SPECS, "unsupported_metric", "finding is not Stage 4 metric-calibratable")
        spec = METRIC_SPECS[finding]
        _require(record["metricName"] == spec["metricName"], "metric_name_mismatch", "metricName does not match the canonical finding metric")
        _require(record["direction"] == spec["direction"], "metric_direction_mismatch", "metric direction does not match the canonical finding metric")
        number = _finite_number(record["rawValue"])
        _require(number >= 0.0, "invalid_metric_value", "Stage 4 private calibration metrics must be non-negative")
        if finding in BOUNDED_UNIT_FINDINGS:
            _require(number <= 1.0, "invalid_metric_value", "normalized Stage 4 metric must be within [0,1]")

        _require(record["split"] == "development", "held_out_in_development_batch", "private development batch cannot contain held-out rows")
        _require(record["dataClass"] == "real", "invalid_private_metric_record", "private development metrics must be real-data class")
        _require(record["purpose"] == "safety_calibration", "purpose_mismatch", "private development metrics must use safety_calibration purpose")
        provenance = record["provenanceReference"]
        _require(isinstance(provenance, str) and provenance.startswith("custody:"), "private_provenance_missing", "private metric provenance must use an opaque custody: reference")

    _require(seen == set(expected_by_observation), "observation_set_mismatch", "private metric observation set does not exactly match the accepted 42-label bundle")
    return value


def materialize_development_observations(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    purpose_raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> tuple[CalibrationObservation, ...]:
    """Join private metrics to accepted human labels inside the private execution boundary."""

    batch = validate_private_metric_batch(raw, authorization_raw, purpose_raw, acceptance_raw, completion_raw)
    completion = validate_reference_label_completion(completion_raw)
    labels = {record["observationId"]: record for record in completion["bundle"]["records"]}
    result: list[CalibrationObservation] = []
    for record in sorted(batch["records"], key=lambda item: item["observationId"]):
        reference = labels[record["observationId"]]
        result.append(
            CalibrationObservation(
                observation_id=record["observationId"],
                dataset_item_id=record["datasetItemId"],
                source_family_id=record["sourceFamilyId"],
                finding_type=record["findingType"],
                metric_name=record["metricName"],
                raw_value=record["rawValue"],
                reference_label=reference["referenceLabel"],
                split="development",
                data_class="real",
                purpose="safety_calibration",
                purpose_permission_granted=True,
                provenance_reference=record["provenanceReference"],
            )
        )
    _require(len(result) == EXPECTED_RECORD_COUNT, "record_count_mismatch", "materialized observation count drifted")
    return tuple(result)


def build_public_preparation_receipt(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    purpose_raw: Mapping[str, Any],
    acceptance_raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Emit a public-safe digest/count receipt; never emits raw values or row identities."""

    batch = validate_private_metric_batch(raw, authorization_raw, purpose_raw, acceptance_raw, completion_raw)
    counts = {finding: 0 for finding in sorted(METRIC_SPECS)}
    for record in batch["records"]:
        counts[record["findingType"]] += 1
    return {
        "schemaVersion": PRIVATE_METRIC_SCHEMA_VERSION,
        "contractVersion": RUNNER_CONTRACT_VERSION,
        "status": "development_calibration_input_prepared",
        "privateMetricBatchDigest": {"algorithm": "sha256", "value": canonical_sha256(batch)},
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "referenceBundleDigest": {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "recordCount": EXPECTED_RECORD_COUNT,
        "findingCounts": counts,
        "assertions": {
            "privateMetricRowsPublic": False,
            "rawMetricValuesPublic": False,
            "datasetItemIdentityPublic": False,
            "sourceFamilyIdentityPublic": False,
            "artifactBytesPublic": False,
            "derivativeBytesPublic": False,
            "candidateDerivationInputReady": True,
            "realDataCalibrationExecuted": False,
            "thresholdsCalibrated": False,
            "resourceLimitsCalibrated": False,
            "heldOutIncluded": False,
            "heldOutThresholdTuningUsed": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
    }


__all__ = [
    "BOUNDED_UNIT_FINDINGS", "EXPECTED_RECORD_COUNT", "METRIC_SPECS",
    "PRIVATE_METRIC_SCHEMA_VERSION", "RUNNER_CONTRACT_VERSION",
    "Stage4DevelopmentCalibrationRunnerError", "build_public_preparation_receipt",
    "materialize_development_observations", "validate_private_metric_batch",
]
