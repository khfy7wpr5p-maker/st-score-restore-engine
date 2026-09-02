"""Fail-closed Stage 4 real reference-label bundle acceptance contract.

This slice accepts one already-completed, human-reviewed development bundle for
future safety-calibration candidate derivation. It does not authorize execution,
held-out tuning, production threshold/resource changes, training, publication,
Stage 4 exit, or Stage 5 entry.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_purpose_grants import APPROVED_GRANT_CANONICAL_SHA256
from .stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256,
    BUNDLE_ID,
    COMPLETION_CANONICAL_SHA256,
    EXPECTED_LABEL_COUNTS,
    validate_reference_label_completion,
)
from .stage4_reference_label_work_package import WORK_PACKAGE_CANONICAL_SHA256
from .stage4_reference_labels import (
    ReferenceLabelBundle,
    freeze_reference_label_bundle,
    require_candidate_derivation_eligible,
)

ACCEPTANCE_SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage4.reference-label-acceptance.beethoven-barley.v1"
ACCEPTANCE_DECISION = "ACCEPT_REAL_REFERENCE_BUNDLE"
ACCEPTED_ON = "2026-09-02"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260902-01"
REFERENCE_RECEIPT_CANONICAL_SHA256 = "f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33"
ACCEPTANCE_CANONICAL_SHA256 = "88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c"


class Stage4ReferenceLabelAcceptanceError(ValueError):
    """Accepted reference-label evidence is malformed, unbound, or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4ReferenceLabelAcceptanceError(message)


def validate_reference_label_acceptance(
    raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise Stage4ReferenceLabelAcceptanceError("acceptance evidence must be an object")
    value = deepcopy(dict(raw))
    completion = validate_reference_label_completion(completion_raw)
    _require(canonical_sha256(completion) == COMPLETION_CANONICAL_SHA256, "completion canonical digest drifted")

    _require(
        set(value) == {
            "schemaVersion", "acceptanceId", "decision", "acceptedOn", "decisionAuthorityReference",
            "completionDigest", "workPackageDigest", "purposeGrantDigest", "bundleDigest",
            "acceptedReferenceReceipt", "scope", "assertions"
        },
        "reference-bundle acceptance top-level fields drifted",
    )
    _require(value["schemaVersion"] == ACCEPTANCE_SCHEMA_VERSION, "acceptance schema drifted")
    _require(value["acceptanceId"] == ACCEPTANCE_ID, "acceptance id drifted")
    _require(value["decision"] == ACCEPTANCE_DECISION, "reference bundle is not explicitly accepted")
    _require(value["acceptedOn"] == ACCEPTED_ON, "acceptance date drifted")
    _require(value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE, "decision authority binding drifted")
    _require(
        value["completionDigest"] == {"algorithm": "sha256", "value": COMPLETION_CANONICAL_SHA256},
        "completion digest binding drifted",
    )
    _require(
        value["workPackageDigest"] == {"algorithm": "sha256", "value": WORK_PACKAGE_CANONICAL_SHA256},
        "work-package digest binding drifted",
    )
    _require(
        value["purposeGrantDigest"] == {"algorithm": "sha256", "value": APPROVED_GRANT_CANONICAL_SHA256},
        "purpose-grant digest binding drifted",
    )
    _require(
        value["bundleDigest"] == {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "bundle digest binding drifted",
    )

    bundle_raw = completion.get("bundle")
    _require(isinstance(bundle_raw, Mapping), "accepted completion bundle is missing")
    records = bundle_raw.get("records")
    _require(isinstance(records, list) and len(records) == 42, "accepted bundle record count drifted")
    bundle = ReferenceLabelBundle.from_records(BUNDLE_ID, records)
    _require(bundle.to_dict() == bundle_raw, "accepted bundle serialization drifted")
    _require(bundle.digest() == BUNDLE_CANONICAL_SHA256, "accepted bundle canonical digest drifted")

    receipt = freeze_reference_label_bundle(bundle, accepted_real_reference_bundle=True)
    _require(
        receipt.get("receiptDigest") == {"algorithm": "sha256", "value": REFERENCE_RECEIPT_CANONICAL_SHA256},
        "accepted reference receipt digest drifted",
    )
    _require(value["acceptedReferenceReceipt"] == receipt, "accepted reference receipt does not match the frozen bundle")

    # Acceptance makes the development reference evidence derivation-eligible,
    # but does not itself authorize or execute calibration.
    require_candidate_derivation_eligible(bundle, accepted_real_reference_bundle=True)

    _require(
        value["scope"] == {
            "split": "development",
            "dataClass": "real",
            "purpose": "safety_calibration",
            "recordCount": 42,
            "datasetItemCount": 2,
            "sourceFamilyCount": 2,
            "candidateDerivationEligible": True,
            "heldOutIncluded": False,
            "heldOutTuningAuthorized": False,
        },
        "acceptance scope drifted or became unsafe",
    )
    _require(
        value["assertions"] == {
            "referenceBundleAccepted": True,
            "humanLabelsPresent": True,
            "labelsAutomaticallyGenerated": False,
            "modelPredictionsUsedAsReferenceLabels": False,
            "realDataCalibrationExecutionAuthorized": False,
            "realDataCalibrationExecuted": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "acceptance assertions drifted or over-authorized downstream work",
    )
    _require(
        receipt.get("scope", {}).get("labelCounts") == EXPECTED_LABEL_COUNTS,
        "accepted receipt human-label counts drifted",
    )
    _require(
        receipt.get("assertions", {}).get("realReferenceBundleAccepted") is True,
        "accepted receipt did not mark the real reference bundle accepted",
    )
    _require(
        receipt.get("assertions", {}).get("realDataCalibrationAuthorized") is False,
        "reference acceptance improperly authorized calibration execution",
    )
    _require(canonical_sha256(value) == ACCEPTANCE_CANONICAL_SHA256, "acceptance canonical digest drifted")
    return value


def summarize_reference_label_acceptance(
    raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
) -> dict[str, Any]:
    value = validate_reference_label_acceptance(raw, completion_raw)
    return {
        "schemaVersion": ACCEPTANCE_SCHEMA_VERSION,
        "decision": ACCEPTANCE_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "bundleDigest": value["bundleDigest"],
        "recordCount": 42,
        "labelCounts": dict(EXPECTED_LABEL_COUNTS),
        "referenceBundleAccepted": True,
        "candidateDerivationEligible": True,
        "realDataCalibrationExecutionAuthorized": False,
        "heldOutIncluded": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256", "ACCEPTANCE_DECISION", "ACCEPTANCE_ID",
    "ACCEPTANCE_SCHEMA_VERSION", "ACCEPTED_ON", "DECISION_AUTHORITY_REFERENCE",
    "REFERENCE_RECEIPT_CANONICAL_SHA256", "Stage4ReferenceLabelAcceptanceError",
    "summarize_reference_label_acceptance", "validate_reference_label_acceptance",
]
