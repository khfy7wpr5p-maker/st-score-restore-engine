"""Fail-closed Stage 4 Wikimedia real reference-bundle acceptance contract.

This module records a separate governance acceptance for the already-completed
Wikimedia Guitar Technical Exercise development reference bundle. Acceptance makes
that exact development bundle eligible for candidate derivation. It does not
authorize or execute calibration, touch held-out data, change production
thresholds/resources, grant Stage 4 PASS, or open Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_reference_labels import (
    ReferenceLabelBundle,
    freeze_reference_label_bundle,
    require_candidate_derivation_eligible,
)
from .stage4_wikimedia_reference_gate import (
    HELD_OUT_ITEM_ID,
    WIKIMEDIA_BUNDLE_ID,
    WIKIMEDIA_GRANT_DIGEST,
    WIKIMEDIA_ITEM_ID,
    WIKIMEDIA_SOURCE_FAMILY_ID,
    validate_wikimedia_review_work_package,
)

ACCEPTANCE_SCHEMA_VERSION = "1.0.0"
ACCEPTANCE_ID = "stage4.reference-label-acceptance.wikimedia-guitar-technical-exercise.v1"
ACCEPTANCE_DECISION = "ACCEPT_REAL_REFERENCE_BUNDLE"
ACCEPTED_ON = "2026-09-03"
DECISION_AUTHORITY_REFERENCE = "authority:project-governance-owner-20260903-02"
ACCEPTANCE_SOURCE_CODE = "explicit_user_authorization"

WIKIMEDIA_WORK_PACKAGE_CANONICAL_SHA256 = "9ccec309f611f8057b8b4a20a1aba732544c1638f2b959656b9503718206337c"
WIKIMEDIA_COMPLETION_CANONICAL_SHA256 = "50b593bdf15812eec28a77e2897ba222686410a8f22827592392b64a03353094"
WIKIMEDIA_BUNDLE_CANONICAL_SHA256 = "37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4"
REFERENCE_RECEIPT_CANONICAL_SHA256 = "036bb31ca2672e443885ed06e213ef6913be7c66609ab5017b6f22ed3f33c801"
ACCEPTANCE_CANONICAL_SHA256 = "79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3"
EXPECTED_LABEL_COUNTS = {"clear": 7, "not_assessed": 0, "possible": 0, "probable": 0}


class Stage4WikimediaReferenceAcceptanceError(ValueError):
    """Wikimedia acceptance evidence is malformed, unbound, or over-authorizing."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4WikimediaReferenceAcceptanceError(message)


def validate_wikimedia_human_label_completion(
    completion_raw: Mapping[str, Any],
    work_package_raw: Mapping[str, Any],
) -> tuple[dict[str, Any], ReferenceLabelBundle]:
    """Validate the exact completed human evidence before governance acceptance."""

    _require(isinstance(completion_raw, Mapping), "completion evidence must be an object")
    package = validate_wikimedia_review_work_package(work_package_raw)
    _require(
        canonical_sha256(package) == WIKIMEDIA_WORK_PACKAGE_CANONICAL_SHA256,
        "Wikimedia work-package canonical digest drifted",
    )

    completion = deepcopy(dict(completion_raw))
    _require(
        set(completion) == {
            "schemaVersion",
            "state",
            "workPackageDigest",
            "purposeGrantDigest",
            "bundle",
            "bundleDigest",
            "labelCounts",
            "assertions",
        },
        "Wikimedia completion top-level fields drifted",
    )
    _require(completion["schemaVersion"] == "1.0.0", "Wikimedia completion schema drifted")
    _require(
        completion["state"] == "human_labels_complete_pending_separate_acceptance",
        "Wikimedia completion state drifted",
    )
    _require(
        completion["workPackageDigest"]
        == {"algorithm": "sha256", "value": WIKIMEDIA_WORK_PACKAGE_CANONICAL_SHA256},
        "Wikimedia completion work-package binding drifted",
    )
    _require(
        completion["purposeGrantDigest"]
        == {"algorithm": "sha256", "value": WIKIMEDIA_GRANT_DIGEST},
        "Wikimedia completion purpose-grant binding drifted",
    )
    _require(
        completion["bundleDigest"]
        == {"algorithm": "sha256", "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256},
        "Wikimedia completion bundle digest binding drifted",
    )
    _require(completion["labelCounts"] == EXPECTED_LABEL_COUNTS, "Wikimedia label counts drifted")
    _require(
        completion["assertions"]
        == {
            "humanLabelsPresent": True,
            "labelsAutomaticallyGenerated": False,
            "modelPredictionsUsedAsReferenceLabels": False,
            "referenceBundleAccepted": False,
            "candidateDerivationEligible": False,
            "expansionCalibrationExecutionAuthorized": False,
            "expansionCalibrationExecuted": False,
            "heldOutIncludedInDevelopmentReview": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "Wikimedia completion assertions drifted or opened a downstream gate",
    )

    bundle_raw = completion.get("bundle")
    _require(isinstance(bundle_raw, Mapping), "Wikimedia completion bundle is missing")
    records = bundle_raw.get("records")
    _require(isinstance(records, list) and len(records) == 7, "Wikimedia bundle must contain exactly seven labels")
    bundle = ReferenceLabelBundle.from_records(WIKIMEDIA_BUNDLE_ID, records)
    _require(bundle.to_dict() == bundle_raw, "Wikimedia bundle serialization drifted")
    _require(bundle.digest() == WIKIMEDIA_BUNDLE_CANONICAL_SHA256, "Wikimedia bundle canonical digest drifted")
    _require(
        all(record.dataset_item_id == WIKIMEDIA_ITEM_ID for record in bundle.records),
        "Wikimedia accepted bundle contains an unexpected dataset item",
    )
    _require(
        all(record.source_family_id == WIKIMEDIA_SOURCE_FAMILY_ID for record in bundle.records),
        "Wikimedia accepted bundle contains an unexpected source family",
    )
    _require(
        all(record.reference_label == "clear" for record in bundle.records),
        "Wikimedia accepted bundle label truth drifted",
    )
    _require(
        all(record.review_method == "human_expert_review" for record in bundle.records),
        "Wikimedia accepted bundle lost human expert provenance",
    )
    _require(
        canonical_sha256(completion) == WIKIMEDIA_COMPLETION_CANONICAL_SHA256,
        "Wikimedia completion canonical digest drifted",
    )
    return completion, bundle


def validate_wikimedia_reference_acceptance(
    raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
    work_package_raw: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the explicit governance acceptance without opening later gates."""

    _require(isinstance(raw, Mapping), "Wikimedia acceptance evidence must be an object")
    value = deepcopy(dict(raw))
    _, bundle = validate_wikimedia_human_label_completion(completion_raw, work_package_raw)

    _require(
        set(value) == {
            "schemaVersion",
            "acceptanceId",
            "decision",
            "acceptedOn",
            "decisionAuthorityReference",
            "acceptanceSourceCode",
            "completionDigest",
            "workPackageDigest",
            "purposeGrantDigest",
            "bundleDigest",
            "acceptedReferenceReceipt",
            "scope",
            "assertions",
        },
        "Wikimedia acceptance top-level fields drifted",
    )
    _require(value["schemaVersion"] == ACCEPTANCE_SCHEMA_VERSION, "Wikimedia acceptance schema drifted")
    _require(value["acceptanceId"] == ACCEPTANCE_ID, "Wikimedia acceptance id drifted")
    _require(value["decision"] == ACCEPTANCE_DECISION, "Wikimedia reference bundle is not explicitly accepted")
    _require(value["acceptedOn"] == ACCEPTED_ON, "Wikimedia acceptance date drifted")
    _require(
        value["decisionAuthorityReference"] == DECISION_AUTHORITY_REFERENCE,
        "Wikimedia decision authority binding drifted",
    )
    _require(value["acceptanceSourceCode"] == ACCEPTANCE_SOURCE_CODE, "Wikimedia acceptance source drifted")
    _require(
        value["completionDigest"]
        == {"algorithm": "sha256", "value": WIKIMEDIA_COMPLETION_CANONICAL_SHA256},
        "Wikimedia completion digest binding drifted",
    )
    _require(
        value["workPackageDigest"]
        == {"algorithm": "sha256", "value": WIKIMEDIA_WORK_PACKAGE_CANONICAL_SHA256},
        "Wikimedia work-package digest binding drifted",
    )
    _require(
        value["purposeGrantDigest"] == {"algorithm": "sha256", "value": WIKIMEDIA_GRANT_DIGEST},
        "Wikimedia purpose-grant digest binding drifted",
    )
    _require(
        value["bundleDigest"] == {"algorithm": "sha256", "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256},
        "Wikimedia bundle digest binding drifted",
    )

    receipt = freeze_reference_label_bundle(bundle, accepted_real_reference_bundle=True)
    _require(
        receipt.get("receiptDigest")
        == {"algorithm": "sha256", "value": REFERENCE_RECEIPT_CANONICAL_SHA256},
        "Wikimedia accepted reference receipt digest drifted",
    )
    _require(
        value["acceptedReferenceReceipt"] == receipt,
        "Wikimedia accepted reference receipt does not match the frozen bundle",
    )
    require_candidate_derivation_eligible(bundle, accepted_real_reference_bundle=True)

    _require(
        value["scope"]
        == {
            "split": "development",
            "dataClass": "real",
            "purpose": "safety_calibration",
            "recordCount": 7,
            "datasetItemCount": 1,
            "sourceFamilyCount": 1,
            "candidateDerivationEligible": True,
            "heldOutIncluded": False,
            "heldOutTuningAuthorized": False,
        },
        "Wikimedia acceptance scope drifted or became unsafe",
    )
    _require(
        value["assertions"]
        == {
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
        "Wikimedia acceptance assertions drifted or over-authorized downstream work",
    )
    _require(
        receipt.get("scope", {}).get("labelCounts") == EXPECTED_LABEL_COUNTS,
        "Wikimedia accepted receipt human-label counts drifted",
    )
    _require(
        receipt.get("assertions", {}).get("realReferenceBundleAccepted") is True,
        "Wikimedia accepted receipt did not mark the real reference bundle accepted",
    )
    _require(
        receipt.get("assertions", {}).get("realDataCalibrationAuthorized") is False,
        "Wikimedia reference acceptance improperly authorized calibration execution",
    )
    _require(
        HELD_OUT_ITEM_ID not in {record.dataset_item_id for record in bundle.records},
        "held-out Chopin entered the Wikimedia development acceptance",
    )
    _require(
        canonical_sha256(value) == ACCEPTANCE_CANONICAL_SHA256,
        "Wikimedia acceptance canonical digest drifted",
    )
    return value


def summarize_wikimedia_reference_acceptance(
    raw: Mapping[str, Any],
    completion_raw: Mapping[str, Any],
    work_package_raw: Mapping[str, Any],
) -> dict[str, Any]:
    value = validate_wikimedia_reference_acceptance(raw, completion_raw, work_package_raw)
    return {
        "schemaVersion": ACCEPTANCE_SCHEMA_VERSION,
        "decision": ACCEPTANCE_DECISION,
        "acceptanceDigest": {"algorithm": "sha256", "value": ACCEPTANCE_CANONICAL_SHA256},
        "bundleDigest": value["bundleDigest"],
        "recordCount": 7,
        "labelCounts": dict(EXPECTED_LABEL_COUNTS),
        "referenceBundleAccepted": True,
        "candidateDerivationEligible": True,
        "realDataCalibrationExecutionAuthorized": False,
        "heldOutIncluded": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


__all__ = [
    "ACCEPTANCE_CANONICAL_SHA256",
    "ACCEPTANCE_DECISION",
    "ACCEPTANCE_ID",
    "ACCEPTANCE_SCHEMA_VERSION",
    "ACCEPTANCE_SOURCE_CODE",
    "ACCEPTED_ON",
    "DECISION_AUTHORITY_REFERENCE",
    "EXPECTED_LABEL_COUNTS",
    "REFERENCE_RECEIPT_CANONICAL_SHA256",
    "Stage4WikimediaReferenceAcceptanceError",
    "WIKIMEDIA_BUNDLE_CANONICAL_SHA256",
    "WIKIMEDIA_COMPLETION_CANONICAL_SHA256",
    "WIKIMEDIA_WORK_PACKAGE_CANONICAL_SHA256",
    "summarize_wikimedia_reference_acceptance",
    "validate_wikimedia_human_label_completion",
    "validate_wikimedia_reference_acceptance",
]
