"""Fail-closed Stage 4 expanded private-metric development calibration runner.

This runner prepares the authorized Beethoven + Barley + Wikimedia development
scope for private metric execution. Raw metric rows remain outside ordinary Git.
The exact reference truth is joined only after validation from the two immutable,
governance-accepted human reference bundles.

The contract does not itself execute calibration, choose thresholds, change
resource limits, touch held-out Chopin data, train or publish a model, grant
Stage 4 PASS, or open Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
import math
from typing import Any, Mapping, Sequence

from .dataset_contract_common import canonical_sha256
from .stage4_calibration import CalibrationObservation
from .stage4_development_calibration_runner import BOUNDED_UNIT_FINDINGS, METRIC_SPECS
from .stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256 as BEETHOVEN_BARLEY_BUNDLE_SHA256,
    validate_reference_label_completion,
)
from .stage4_wikimedia_expanded_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    EXPECTED_ITEMS,
    validate_wikimedia_expanded_execution_authorization,
)
from .stage4_wikimedia_reference_acceptance import (
    WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
    validate_wikimedia_human_label_completion,
)

RUNNER_CONTRACT_VERSION = "0.3.1"
PRIVATE_METRIC_SCHEMA_VERSION = "1.2.0"
EXPECTED_RECORD_COUNT = 49
EXPECTED_MEASURED_RECORD_COUNT = 30
EXPECTED_NOT_APPLICABLE_RECORD_COUNT = 19
EXPECTED_MEASURED_SOURCE_FAMILY_COUNT = 2

BEETHOVEN_ID = "dataset.item.imslp799143-beethoven-op48-no3.v1"
BARLEY_ID = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
WIKIMEDIA_ID = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"

MEASUREMENT_STATUSES = frozenset({"measured", "not_applicable"})
NOT_APPLICABLE_REASONS = frozenset(
    {
        "source_vector_only_preserved",
        "metric_not_applicable_to_png_derivative",
    }
)


class Stage4ExpandedDevelopmentCalibrationRunnerError(ValueError):
    """Expanded private metric input is malformed, unbound, or out of scope."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Stage4ExpandedDevelopmentCalibrationRunnerError(code, message)


def _finite_number(value: Any) -> float:
    _require(
        not isinstance(value, bool) and isinstance(value, (int, float)),
        "invalid_metric_value",
        "rawValue must be a finite number",
    )
    number = float(value)
    _require(math.isfinite(number), "invalid_metric_value", "rawValue must be finite")
    return number


def _expected_measurement(item_id: str, finding: str) -> tuple[str, str | None]:
    """Return analyzer-compatible applicability for the authorized development scope."""

    if item_id == BARLEY_ID:
        return "not_applicable", "source_vector_only_preserved"
    if item_id in {BEETHOVEN_ID, WIKIMEDIA_ID} and finding == "compression":
        # quality_analysis._compression_metrics is JPEG-only. Beethoven is measured
        # from PDF-derived PNG pages and Wikimedia is an admitted source PNG, so
        # neither PNG path may invent a numeric compression score.
        return "not_applicable", "metric_not_applicable_to_png_derivative"
    if item_id in {BEETHOVEN_ID, WIKIMEDIA_ID}:
        return "measured", None
    raise Stage4ExpandedDevelopmentCalibrationRunnerError(
        "authorization_mismatch",
        "dataset item is outside the exact expanded development applicability contract",
    )


def _validated_reference_records(
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    bb_completion = validate_reference_label_completion(beethoven_barley_completion_raw)
    wiki_completion, _ = validate_wikimedia_human_label_completion(
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )
    records = [
        *bb_completion["bundle"]["records"],
        *wiki_completion["bundle"]["records"],
    ]
    _require(
        len(records) == EXPECTED_RECORD_COUNT,
        "reference_record_count_mismatch",
        "expanded reference truth must contain exactly 49 records",
    )
    by_observation: dict[str, dict[str, Any]] = {}
    for record in records:
        observation_id = record.get("observationId")
        _require(
            isinstance(observation_id, str) and observation_id,
            "observation_identity_mismatch",
            "reference observationId is missing",
        )
        _require(
            observation_id not in by_observation,
            "duplicate_observation",
            "duplicate observationId across accepted reference bundles",
        )
        by_observation[observation_id] = record
    return by_observation


def validate_expanded_private_metric_batch(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    beethoven_barley_purpose_raw: Mapping[str, Any],
    beethoven_barley_acceptance_raw: Mapping[str, Any],
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_purpose_raw: Mapping[str, Any],
    wikimedia_acceptance_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one custody-only 49-row expanded development measurement batch."""

    _require(
        isinstance(raw, Mapping),
        "invalid_private_metric_batch",
        "private metric batch must be an object",
    )
    value = deepcopy(dict(raw))
    authorization = validate_wikimedia_expanded_execution_authorization(
        authorization_raw,
        beethoven_barley_purpose_raw,
        beethoven_barley_acceptance_raw,
        beethoven_barley_completion_raw,
        wikimedia_purpose_raw,
        wikimedia_acceptance_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )
    references = _validated_reference_records(
        beethoven_barley_completion_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )

    _require(
        set(value)
        == {
            "schemaVersion",
            "contractVersion",
            "batchId",
            "environment",
            "authorizationDigest",
            "referenceBundleDigests",
            "records",
        },
        "invalid_private_metric_batch",
        "expanded private metric batch top-level fields drifted",
    )
    _require(
        value["schemaVersion"] == PRIVATE_METRIC_SCHEMA_VERSION,
        "invalid_private_metric_batch",
        "private metric schema drifted",
    )
    _require(
        value["contractVersion"] == RUNNER_CONTRACT_VERSION,
        "invalid_private_metric_batch",
        "runner contract version drifted",
    )
    _require(
        isinstance(value["batchId"], str) and value["batchId"].strip(),
        "invalid_private_metric_batch",
        "batchId is required",
    )
    _require(
        value["environment"] == authorization["scope"]["environment"],
        "environment_mismatch",
        "private metric environment does not match expanded authorization",
    )
    _require(
        value["authorizationDigest"]
        == {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "authorization_mismatch",
        "private metric batch is not bound to the expanded execution authorization",
    )
    _require(
        value["referenceBundleDigests"]
        == {
            "beethovenBarley": {
                "algorithm": "sha256",
                "value": BEETHOVEN_BARLEY_BUNDLE_SHA256,
            },
            "wikimedia": {
                "algorithm": "sha256",
                "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
            },
        },
        "reference_bundle_mismatch",
        "private metric batch is not bound to both accepted reference bundles",
    )

    records = value["records"]
    _require(
        isinstance(records, Sequence) and not isinstance(records, (str, bytes)),
        "invalid_private_metric_batch",
        "records must be an array",
    )
    _require(
        len(records) == EXPECTED_RECORD_COUNT,
        "record_count_mismatch",
        "expanded private metric batch must contain exactly 49 records",
    )

    authorized_items = {
        item["datasetItemId"]: item for item in authorization["scope"]["datasetItems"]
    }
    _require(
        set(authorized_items) == set(EXPECTED_ITEMS),
        "authorization_mismatch",
        "expanded authorization exact item set drifted",
    )

    seen: set[str] = set()
    measured_count = 0
    not_applicable_count = 0
    measured_source_families: set[str] = set()
    required_fields = {
        "observationId",
        "datasetItemId",
        "artifactSha256",
        "sourceFamilyId",
        "findingType",
        "metricName",
        "direction",
        "measurementStatus",
        "rawValue",
        "notApplicableReason",
        "split",
        "dataClass",
        "purpose",
        "provenanceReference",
    }
    forbidden_truth_fields = {
        "referenceLabel",
        "predictedLabel",
        "modelLabel",
        "reviewerReference",
    }

    for raw_record in records:
        _require(
            isinstance(raw_record, Mapping),
            "invalid_private_metric_record",
            "private metric record must be an object",
        )
        record = dict(raw_record)
        _require(
            not (set(record) & forbidden_truth_fields),
            "reference_truth_in_private_metrics",
            "private metric rows must not carry reference/model labels",
        )
        _require(
            set(record) == required_fields,
            "invalid_private_metric_record",
            "private metric record fields drifted",
        )

        observation_id = record["observationId"]
        _require(
            isinstance(observation_id, str) and observation_id in references,
            "observation_identity_mismatch",
            "unknown private metric observationId",
        )
        _require(
            observation_id not in seen,
            "duplicate_observation",
            "duplicate private metric observationId",
        )
        seen.add(observation_id)

        expected = references[observation_id]
        item_id = record["datasetItemId"]
        _require(
            item_id == expected["datasetItemId"],
            "observation_identity_mismatch",
            "datasetItemId does not match accepted human reference",
        )
        _require(
            item_id in authorized_items,
            "authorization_mismatch",
            "dataset item is outside expanded authorized execution scope",
        )
        authorized_item = authorized_items[item_id]
        _require(
            record["artifactSha256"] == authorized_item["artifactSha256"],
            "artifact_identity_mismatch",
            "artifact SHA does not match expanded authorization",
        )
        _require(
            record["sourceFamilyId"]
            == expected["sourceFamilyId"]
            == authorized_item["sourceFamilyId"],
            "source_family_mismatch",
            "source family does not match accepted evidence",
        )
        _require(
            record["findingType"] == expected["findingType"],
            "finding_identity_mismatch",
            "finding type does not match accepted human reference",
        )

        finding = record["findingType"]
        _require(
            isinstance(finding, str) and finding in METRIC_SPECS,
            "unsupported_metric",
            "finding is not Stage 4 metric-calibratable",
        )
        spec = METRIC_SPECS[finding]
        _require(
            record["metricName"] == spec["metricName"],
            "metric_name_mismatch",
            "metricName does not match the canonical finding metric",
        )
        _require(
            record["direction"] == spec["direction"],
            "metric_direction_mismatch",
            "metric direction does not match the canonical finding metric",
        )

        status = record["measurementStatus"]
        _require(
            isinstance(status, str) and status in MEASUREMENT_STATUSES,
            "invalid_measurement_status",
            "measurementStatus is not recognized",
        )
        expected_status, expected_reason = _expected_measurement(item_id, finding)
        _require(
            status == expected_status,
            "measurement_applicability_mismatch",
            "measurementStatus contradicts the expanded applicability contract",
        )
        if status == "measured":
            _require(
                record["notApplicableReason"] is None,
                "invalid_measurement_status",
                "measured rows cannot carry a notApplicableReason",
            )
            number = _finite_number(record["rawValue"])
            _require(
                number >= 0.0,
                "invalid_metric_value",
                "Stage 4 private calibration metrics must be non-negative",
            )
            if finding in BOUNDED_UNIT_FINDINGS:
                _require(
                    number <= 1.0,
                    "invalid_metric_value",
                    "normalized Stage 4 metric must be within [0,1]",
                )
            measured_count += 1
            measured_source_families.add(record["sourceFamilyId"])
        else:
            _require(
                record["rawValue"] is None,
                "invented_not_applicable_value",
                "not_applicable rows must not carry a numeric rawValue",
            )
            reason = record["notApplicableReason"]
            _require(
                isinstance(reason, str) and reason in NOT_APPLICABLE_REASONS,
                "invalid_not_applicable_reason",
                "notApplicableReason is not recognized",
            )
            _require(
                reason == expected_reason,
                "measurement_applicability_mismatch",
                "notApplicableReason contradicts the expanded applicability contract",
            )
            not_applicable_count += 1

        _require(
            record["split"] == "development",
            "held_out_in_development_batch",
            "expanded private development batch cannot contain held-out rows",
        )
        _require(
            record["dataClass"] == "real",
            "invalid_private_metric_record",
            "private development metrics must be real-data class",
        )
        _require(
            record["purpose"] == "safety_calibration",
            "purpose_mismatch",
            "private development metrics must use safety_calibration purpose",
        )
        provenance = record["provenanceReference"]
        _require(
            isinstance(provenance, str) and provenance.startswith("custody:"),
            "private_provenance_missing",
            "private metric provenance must use an opaque custody: reference",
        )

    _require(
        seen == set(references),
        "observation_set_mismatch",
        "private metric observation set does not exactly match the accepted 49-record reference truth",
    )
    _require(
        measured_count == EXPECTED_MEASURED_RECORD_COUNT,
        "measurement_count_mismatch",
        "expanded private batch must contain exactly 30 measured rows",
    )
    _require(
        not_applicable_count == EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
        "measurement_count_mismatch",
        "expanded private batch must contain exactly 19 not-applicable rows",
    )
    _require(
        len(measured_source_families) == EXPECTED_MEASURED_SOURCE_FAMILY_COUNT,
        "measured_source_family_count_mismatch",
        "expanded private batch must provide measured support from exactly two source families",
    )
    return value


def materialize_expanded_development_observations(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    beethoven_barley_purpose_raw: Mapping[str, Any],
    beethoven_barley_acceptance_raw: Mapping[str, Any],
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_purpose_raw: Mapping[str, Any],
    wikimedia_acceptance_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
) -> tuple[CalibrationObservation, ...]:
    """Join measured custody metrics to accepted human truth inside the private boundary."""

    batch = validate_expanded_private_metric_batch(
        raw,
        authorization_raw,
        beethoven_barley_purpose_raw,
        beethoven_barley_acceptance_raw,
        beethoven_barley_completion_raw,
        wikimedia_purpose_raw,
        wikimedia_acceptance_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )
    references = _validated_reference_records(
        beethoven_barley_completion_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )
    result: list[CalibrationObservation] = []
    for record in sorted(batch["records"], key=lambda item: item["observationId"]):
        if record["measurementStatus"] != "measured":
            continue
        reference = references[record["observationId"]]
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
    _require(
        len(result) == EXPECTED_MEASURED_RECORD_COUNT,
        "measurement_count_mismatch",
        "materialized expanded measured observation count drifted",
    )
    return tuple(result)


def build_expanded_public_preparation_receipt(
    raw: Mapping[str, Any],
    authorization_raw: Mapping[str, Any],
    beethoven_barley_purpose_raw: Mapping[str, Any],
    beethoven_barley_acceptance_raw: Mapping[str, Any],
    beethoven_barley_completion_raw: Mapping[str, Any],
    wikimedia_purpose_raw: Mapping[str, Any],
    wikimedia_acceptance_raw: Mapping[str, Any],
    wikimedia_completion_raw: Mapping[str, Any],
    wikimedia_work_package_raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Emit aggregate-only preparation evidence; never emit private rows or raw values."""

    batch = validate_expanded_private_metric_batch(
        raw,
        authorization_raw,
        beethoven_barley_purpose_raw,
        beethoven_barley_acceptance_raw,
        beethoven_barley_completion_raw,
        wikimedia_purpose_raw,
        wikimedia_acceptance_raw,
        wikimedia_completion_raw,
        wikimedia_work_package_raw,
    )
    finding_counts: dict[str, dict[str, int]] = {
        finding: {"total": 0, "measured": 0, "notApplicable": 0}
        for finding in METRIC_SPECS
    }
    measured_families: set[str] = set()
    for record in batch["records"]:
        finding = record["findingType"]
        finding_counts[finding]["total"] += 1
        if record["measurementStatus"] == "measured":
            finding_counts[finding]["measured"] += 1
            measured_families.add(record["sourceFamilyId"])
        else:
            finding_counts[finding]["notApplicable"] += 1

    return {
        "schemaVersion": "1.0.0",
        "status": "expanded_development_calibration_input_prepared_with_abstentions",
        "runnerContractVersion": RUNNER_CONTRACT_VERSION,
        "privateBatchDigest": {
            "algorithm": "sha256",
            "value": canonical_sha256(batch),
        },
        "authorizationDigest": {
            "algorithm": "sha256",
            "value": AUTHORIZATION_CANONICAL_SHA256,
        },
        "referenceBundleDigests": {
            "beethovenBarley": {
                "algorithm": "sha256",
                "value": BEETHOVEN_BARLEY_BUNDLE_SHA256,
            },
            "wikimedia": {
                "algorithm": "sha256",
                "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
            },
        },
        "recordCount": EXPECTED_RECORD_COUNT,
        "measuredRecordCount": EXPECTED_MEASURED_RECORD_COUNT,
        "notApplicableRecordCount": EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
        "measuredSourceFamilyCount": len(measured_families),
        "findingCounts": finding_counts,
        "assertions": {
            "candidateDerivationInputReady": True,
            "notApplicableMeasurementsPresent": True,
            "fullMetricCoverage": False,
            "crossFamilyMeasuredSupportSatisfied": len(measured_families) >= 2,
            "privateMetricRowsPublic": False,
            "rawMetricValuesPublic": False,
            "artifactBytesPublic": False,
            "derivativeBytesPublic": False,
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
    "BARLEY_ID",
    "BEETHOVEN_ID",
    "EXPECTED_MEASURED_RECORD_COUNT",
    "EXPECTED_MEASURED_SOURCE_FAMILY_COUNT",
    "EXPECTED_NOT_APPLICABLE_RECORD_COUNT",
    "EXPECTED_RECORD_COUNT",
    "MEASUREMENT_STATUSES",
    "NOT_APPLICABLE_REASONS",
    "PRIVATE_METRIC_SCHEMA_VERSION",
    "RUNNER_CONTRACT_VERSION",
    "Stage4ExpandedDevelopmentCalibrationRunnerError",
    "WIKIMEDIA_ID",
    "build_expanded_public_preparation_receipt",
    "materialize_expanded_development_observations",
    "validate_expanded_private_metric_batch",
]
