"""Fail-closed Stage 4 completed human reference-label evidence contract.

This slice records human labels supplied through the review work package. It validates
identity, provenance tokens, purpose permission, counts, and bundle digest, while
explicitly keeping reference-bundle acceptance and real calibration execution false.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_purpose_grants import APPROVED_GRANT_CANONICAL_SHA256
from .stage4_reference_label_work_package import WORK_PACKAGE_CANONICAL_SHA256, DEVELOPMENT_ITEMS
from .stage4_reference_labels import (
    FINDING_TYPES,
    REFERENCE_LABELS,
    ReferenceLabelBundle,
    Stage4ReferenceLabelError,
    require_candidate_derivation_eligible,
)

COMPLETION_SCHEMA_VERSION = "1.0.0"
COMPLETION_ID = "stage4.reference-label-completion.beethoven-barley.v1"
COMPLETION_STATE = "human_labels_complete_pending_acceptance"
COMPLETION_CANONICAL_SHA256 = "3434e74e7d993db2384711f9c6c31f31d148c65bc5896bd120f82b5dcab2e1fd"
BUNDLE_ID = "stage4.reference-labels.beethoven-barley.development.v1"
BUNDLE_CANONICAL_SHA256 = "edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14"
REVIEWER_REFERENCE = "reviewer:opq_stage4_20260902_01"
PROVENANCE_REFERENCE = "evidence:stage4-human-review-session-20260902-01"
REVIEWED_ON = "2026-09-02"
EXPECTED_LABEL_COUNTS = {"clear": 36, "not_assessed": 0, "possible": 5, "probable": 1}


class Stage4ReferenceLabelCompletionError(ValueError):
    """Completed human-label evidence is unsafe, inconsistent, or prematurely accepted."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4ReferenceLabelCompletionError(message)


def _expected_observation_ids() -> set[str]:
    result: set[str] = set()
    for item in DEVELOPMENT_ITEMS.values():
        short = item["short"]
        for page_number in range(1, item["pageCount"] + 1):
            for finding in FINDING_TYPES:
                result.add(f"stage4.obs.{short}.p{page_number}.{finding}.v1")
    return result


def validate_reference_label_completion(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise Stage4ReferenceLabelCompletionError("completion evidence must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion", "completionId", "state", "workPackageDigest", "purposeGrantDigest",
            "reviewScope", "reviewSession", "bundle", "bundleDigest", "labelCounts", "assertions"
        },
        "completion top-level fields drifted",
    )
    _require(value["schemaVersion"] == COMPLETION_SCHEMA_VERSION, "completion schema drifted")
    _require(value["completionId"] == COMPLETION_ID, "completion id drifted")
    _require(value["state"] == COMPLETION_STATE, "completion state must remain pending acceptance")
    _require(value["workPackageDigest"] == WORK_PACKAGE_CANONICAL_SHA256, "work-package binding drifted")
    _require(value["purposeGrantDigest"] == APPROVED_GRANT_CANONICAL_SHA256, "purpose-grant binding drifted")
    _require(
        value["reviewScope"] == {
            "split": "development",
            "dataClass": "real",
            "purpose": "safety_calibration",
            "reviewMethod": "human_expert_review",
            "purposePermissionGranted": True,
            "acceptedRealReferenceBundle": False,
            "realDataCalibrationExecutionAuthorized": False,
            "modelPredictionsAllowedAsReference": False,
        },
        "review scope drifted or became permissive",
    )
    _require(
        value["reviewSession"] == {
            "reviewerReference": REVIEWER_REFERENCE,
            "provenanceReference": PROVENANCE_REFERENCE,
            "reviewedOn": REVIEWED_ON,
        },
        "review-session provenance drifted",
    )

    bundle_raw = value["bundle"]
    _require(isinstance(bundle_raw, Mapping), "bundle must be an object")
    _require(bundle_raw.get("bundleId") == BUNDLE_ID, "bundle id drifted")
    records = bundle_raw.get("records")
    _require(isinstance(records, list) and len(records) == 42, "completed bundle must contain exactly 42 records")
    bundle = ReferenceLabelBundle.from_records(BUNDLE_ID, records)
    _require(bundle.to_dict() == bundle_raw, "bundle serialization or scope drifted")
    _require(bundle.digest() == BUNDLE_CANONICAL_SHA256, "bundle canonical digest drifted")
    _require(
        value["bundleDigest"] == {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "bundle digest binding drifted",
    )

    expected_observation_ids = _expected_observation_ids()
    _require({record.observation_id for record in bundle.records} == expected_observation_ids, "observation identity set drifted")
    _require({record.reference_label for record in bundle.records}.issubset(REFERENCE_LABELS), "label vocabulary drifted")
    _require({record.finding_type for record in bundle.records} == set(FINDING_TYPES), "finding taxonomy coverage drifted")
    _require({record.dataset_item_id for record in bundle.records} == set(DEVELOPMENT_ITEMS), "development item scope drifted")
    for record in bundle.records:
        expected = DEVELOPMENT_ITEMS[record.dataset_item_id]
        _require(record.source_family_id == expected["sourceFamilyId"], "source-family identity drifted")
        _require(record.reviewer_reference == REVIEWER_REFERENCE, "reviewer reference drifted")
        _require(record.provenance_reference == PROVENANCE_REFERENCE, "provenance reference drifted")
        _require(record.reviewed_on == REVIEWED_ON, "review date drifted")
        _require(record.review_method == "human_expert_review", "review method drifted")
        _require(record.purpose_permission_granted is True, "purpose permission was not preserved")

    counts = {label: 0 for label in sorted(REFERENCE_LABELS)}
    for record in bundle.records:
        counts[record.reference_label] += 1
    _require(counts == EXPECTED_LABEL_COUNTS, "human label counts drifted")
    _require(value["labelCounts"] == EXPECTED_LABEL_COUNTS, "declared human label counts drifted")

    _require(
        value["assertions"] == {
            "humanLabelsPresent": True,
            "recordCount": 42,
            "referenceBundleAccepted": False,
            "labelsAutomaticallyGenerated": False,
            "modelPredictionsUsedAsReferenceLabels": False,
            "heldOutIncludedInDevelopmentReview": False,
            "realDataCalibrationExecuted": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "completion assertions drifted or became permissive",
    )

    try:
        require_candidate_derivation_eligible(bundle, accepted_real_reference_bundle=False)
    except Stage4ReferenceLabelError as exc:
        _require(exc.code == "real_reference_bundle_not_accepted", "unexpected candidate-derivation rejection")
    else:
        raise Stage4ReferenceLabelCompletionError("unaccepted real bundle unexpectedly became derivation-eligible")

    _require(canonical_sha256(value) == COMPLETION_CANONICAL_SHA256, "completion canonical digest drifted")
    return value


def summarize_reference_label_completion(raw: Mapping[str, Any]) -> dict[str, Any]:
    value = validate_reference_label_completion(raw)
    return {
        "schemaVersion": COMPLETION_SCHEMA_VERSION,
        "status": COMPLETION_STATE,
        "completionDigest": {"algorithm": "sha256", "value": COMPLETION_CANONICAL_SHA256},
        "bundleDigest": value["bundleDigest"],
        "recordCount": 42,
        "labelCounts": dict(EXPECTED_LABEL_COUNTS),
        "referenceBundleAccepted": False,
        "realDataCalibrationExecutionAuthorized": False,
        "heldOutIncluded": False,
    }


__all__ = [
    "BUNDLE_CANONICAL_SHA256", "BUNDLE_ID", "COMPLETION_CANONICAL_SHA256", "COMPLETION_ID",
    "COMPLETION_SCHEMA_VERSION", "COMPLETION_STATE", "EXPECTED_LABEL_COUNTS",
    "PROVENANCE_REFERENCE", "REVIEWED_ON", "REVIEWER_REFERENCE",
    "Stage4ReferenceLabelCompletionError", "summarize_reference_label_completion",
    "validate_reference_label_completion",
]
