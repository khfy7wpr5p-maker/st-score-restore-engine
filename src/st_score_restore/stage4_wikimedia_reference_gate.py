"""Fail-closed Stage 4 Wikimedia human-reference ingestion preparation.

This module prepares, but does not perform, the next external-evidence gate for the
Wikimedia Guitar Technical Exercise development source family. The committed work
package must remain pristine and awaiting human labels. Actual human labels arrive
as a separate runtime/input payload and are validated against the immutable seven
review slots.

A successful completion candidate is still *pending separate governance
acceptance*. This module never accepts a reference bundle, authorizes calibration
execution, changes production thresholds/resources, evaluates held-out data,
grants Stage 4 PASS, or opens Stage 5.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import re
from typing import Any, Mapping, Sequence

from .dataset_contract_common import canonical_sha256
from .stage4_reference_labels import (
    REFERENCE_LABELS,
    ReferenceLabelBundle,
    ReferenceLabelRecord,
    Stage4ReferenceLabelError,
)

WIKIMEDIA_PACKAGE_ID = "stage4.reference-label-review.wikimedia-guitar-technical-exercise.v1"
WIKIMEDIA_GRANT_DIGEST = "603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07"
WIKIMEDIA_ITEM_ID = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
WIKIMEDIA_SOURCE_FAMILY_ID = "source.family.wikimedia-guitar-technical-exercise-no1.v1"
WIKIMEDIA_ARTIFACT_SHA256 = "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb"
WIKIMEDIA_BUNDLE_ID = "stage4.reference-labels.wikimedia-guitar-technical-exercise.development.v1"
HELD_OUT_ITEM_ID = "dataset.item.imslp82860-chopin-op69.v2"

EXPECTED_FINDINGS = frozenset(
    {"skew", "blur", "glare", "shadow", "uneven_lighting", "noise", "compression"}
)
EXPECTED_REVIEW_COUNT = 7
OPAQUE_REVIEWER = re.compile(r"^reviewer:opq_[0-9a-f]{32}$")
OPAQUE_PROVENANCE = re.compile(r"^evidence:opq_[0-9a-f]{32}$")


class Stage4WikimediaReferenceGateError(ValueError):
    """Wikimedia human-reference input is incomplete, unsafe, or out of scope."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Stage4WikimediaReferenceGateError(code, message)


def _iso_date(value: Any) -> str:
    _require(isinstance(value, str) and bool(value.strip()), "invalid_review_date", "reviewedOn is required")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise Stage4WikimediaReferenceGateError(
            "invalid_review_date", "reviewedOn must use YYYY-MM-DD ISO format"
        ) from exc
    return value


def validate_wikimedia_review_work_package(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the committed pristine work package without populating human truth."""

    _require(isinstance(raw, Mapping), "invalid_work_package", "work package must be an object")
    value = deepcopy(dict(raw))
    _require(value.get("schemaVersion") == "1.0.0", "invalid_work_package", "schemaVersion drifted")
    _require(value.get("packageId") == WIKIMEDIA_PACKAGE_ID, "invalid_work_package", "packageId drifted")
    _require(value.get("state") == "awaiting_human_labels", "invalid_work_package", "work package must remain awaiting_human_labels")
    _require(value.get("contractVersion") == "0.1.0", "invalid_work_package", "contractVersion drifted")
    _require(value.get("purposeGrantDigest") == WIKIMEDIA_GRANT_DIGEST, "grant_mismatch", "purpose-grant binding drifted")

    scope = value.get("reviewScope")
    _require(isinstance(scope, Mapping), "invalid_work_package", "reviewScope must be an object")
    _require(scope.get("split") == "development", "scope_mismatch", "review must remain development-only")
    _require(scope.get("dataClass") == "real", "scope_mismatch", "review must remain real-data class")
    _require(scope.get("purpose") == "safety_calibration", "scope_mismatch", "review purpose drifted")
    _require(scope.get("reviewMethodRequired") == "human_expert_review", "scope_mismatch", "human expert review is required")
    _require(scope.get("acceptedRealReferenceBundle") is False, "premature_gate_open", "work package prematurely accepts a reference bundle")
    _require(scope.get("realDataCalibrationExecutionAuthorized") is False, "premature_gate_open", "work package prematurely authorizes calibration")
    _require(scope.get("modelPredictionsAllowedAsReference") is False, "unsafe_reference_source", "model predictions cannot be reference truth")

    _require(set(value.get("labelVocabulary", [])) == set(REFERENCE_LABELS), "label_vocabulary_mismatch", "reference-label vocabulary drifted")
    _require(set(value.get("findingTypes", [])) == set(EXPECTED_FINDINGS), "finding_taxonomy_mismatch", "finding taxonomy drifted")

    item = value.get("item")
    _require(isinstance(item, Mapping), "invalid_work_package", "item must be an object")
    _require(item.get("datasetItemId") == WIKIMEDIA_ITEM_ID, "item_identity_mismatch", "dataset item drifted")
    _require(item.get("sourceFamilyId") == WIKIMEDIA_SOURCE_FAMILY_ID, "item_identity_mismatch", "source family drifted")
    _require(item.get("artifactSha256") == WIKIMEDIA_ARTIFACT_SHA256, "item_identity_mismatch", "artifact SHA-256 drifted")
    _require(item.get("inputKind") == "png" and item.get("pageCount") == 1, "item_identity_mismatch", "Wikimedia item must remain one-page PNG")

    pages = item.get("pages")
    _require(isinstance(pages, list) and len(pages) == 1, "invalid_work_package", "work package must contain exactly one page")
    _require(pages[0].get("pageNumber") == 1, "invalid_work_package", "work package page number drifted")
    reviews = pages[0].get("reviews")
    _require(isinstance(reviews, list) and len(reviews) == EXPECTED_REVIEW_COUNT, "review_count_mismatch", "work package must contain exactly seven review slots")
    _require({row.get("findingType") for row in reviews} == set(EXPECTED_FINDINGS), "finding_taxonomy_mismatch", "review slots do not cover the exact seven findings")
    _require(len({row.get("labelId") for row in reviews}) == EXPECTED_REVIEW_COUNT, "review_identity_mismatch", "label IDs are not unique")
    _require(len({row.get("observationId") for row in reviews}) == EXPECTED_REVIEW_COUNT, "review_identity_mismatch", "observation IDs are not unique")
    for row in reviews:
        _require(isinstance(row, Mapping), "invalid_work_package", "review slot must be an object")
        _require(
            all(row.get(field) is None for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn")),
            "committed_human_truth_forbidden",
            "committed work package must not contain populated human-reference fields",
        )

    exclusions = value.get("heldOutExclusions")
    _require(isinstance(exclusions, list) and len(exclusions) == 1, "held_out_boundary_mismatch", "exact held-out exclusion is required")
    held = exclusions[0]
    _require(held.get("datasetItemId") == HELD_OUT_ITEM_ID, "held_out_boundary_mismatch", "held-out identity drifted")
    _require(held.get("includedInDevelopmentReview") is False, "held_out_boundary_mismatch", "held-out data entered development review")
    _require(held.get("candidateDerivationAuthorized") is False, "held_out_boundary_mismatch", "held-out candidate derivation was authorized")

    assertions = value.get("assertions")
    _require(isinstance(assertions, Mapping), "invalid_work_package", "assertions must be an object")
    for key in (
        "humanLabelsPresent",
        "referenceBundleAccepted",
        "labelsAutomaticallyGenerated",
        "modelPredictionsUsedAsReferenceLabels",
        "heldOutIncludedInDevelopmentReview",
        "expansionCalibrationExecutionAuthorized",
        "expansionCalibrationExecuted",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        _require(assertions.get(key) is False, "premature_gate_open", f"unsafe work-package assertion became true: {key}")
    return value


def build_wikimedia_reference_completion_candidate(
    work_package_raw: Mapping[str, Any],
    completed_reviews: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a pending-acceptance candidate from externally supplied human review.

    ``completed_reviews`` is never inferred from image metrics or model output. It
    must contain exactly the seven human-reviewed rows matching the committed work
    package identities.
    """

    package = validate_wikimedia_review_work_package(work_package_raw)
    _require(
        isinstance(completed_reviews, Sequence) and not isinstance(completed_reviews, (str, bytes)),
        "invalid_completed_reviews",
        "completed reviews must be an array",
    )
    _require(len(completed_reviews) == EXPECTED_REVIEW_COUNT, "human_labels_incomplete", "exactly seven completed human reviews are required")

    baseline_reviews = package["item"]["pages"][0]["reviews"]
    expected_by_observation = {row["observationId"]: row for row in baseline_reviews}
    required_fields = {
        "labelId", "observationId", "findingType", "referenceLabel",
        "reviewerReference", "provenanceReference", "reviewedOn"
    }
    seen: set[str] = set()
    records: list[ReferenceLabelRecord] = []

    for raw_row in completed_reviews:
        _require(isinstance(raw_row, Mapping), "invalid_completed_reviews", "completed review row must be an object")
        row = dict(raw_row)
        _require(set(row) == required_fields, "invalid_completed_reviews", "completed review fields drifted")
        observation_id = row["observationId"]
        _require(observation_id in expected_by_observation, "review_identity_mismatch", "unknown observationId")
        _require(observation_id not in seen, "review_identity_mismatch", "duplicate observationId")
        seen.add(observation_id)
        expected = expected_by_observation[observation_id]
        _require(row["labelId"] == expected["labelId"], "review_identity_mismatch", "labelId does not match work package")
        _require(row["findingType"] == expected["findingType"], "review_identity_mismatch", "findingType does not match work package")
        _require(row["referenceLabel"] in REFERENCE_LABELS, "invalid_reference_label", "referenceLabel is outside the allowed vocabulary")
        _require(
            isinstance(row["reviewerReference"], str) and bool(OPAQUE_REVIEWER.fullmatch(row["reviewerReference"])),
            "reviewer_reference_not_opaque",
            "reviewerReference must be an opaque reviewer:opq_<32hex> token",
        )
        _require(
            isinstance(row["provenanceReference"], str) and bool(OPAQUE_PROVENANCE.fullmatch(row["provenanceReference"])),
            "provenance_reference_not_opaque",
            "provenanceReference must be an opaque evidence:opq_<32hex> token",
        )
        reviewed_on = _iso_date(row["reviewedOn"])
        try:
            records.append(
                ReferenceLabelRecord(
                    label_id=row["labelId"],
                    observation_id=observation_id,
                    dataset_item_id=WIKIMEDIA_ITEM_ID,
                    source_family_id=WIKIMEDIA_SOURCE_FAMILY_ID,
                    finding_type=row["findingType"],
                    reference_label=row["referenceLabel"],
                    split="development",
                    data_class="real",
                    purpose="safety_calibration",
                    purpose_permission_granted=True,
                    provenance_reference=row["provenanceReference"],
                    reviewer_reference=row["reviewerReference"],
                    review_method="human_expert_review",
                    reviewed_on=reviewed_on,
                )
            )
        except Stage4ReferenceLabelError as exc:
            raise Stage4WikimediaReferenceGateError(exc.code, exc.message) from exc

    _require(seen == set(expected_by_observation), "human_labels_incomplete", "completed review identity set is incomplete")
    bundle = ReferenceLabelBundle(bundle_id=WIKIMEDIA_BUNDLE_ID, records=tuple(records))
    counts = {label: 0 for label in sorted(REFERENCE_LABELS)}
    for record in bundle.records:
        counts[record.reference_label] += 1

    return {
        "schemaVersion": "1.0.0",
        "state": "human_labels_complete_pending_separate_acceptance",
        "workPackageDigest": {"algorithm": "sha256", "value": canonical_sha256(package)},
        "purposeGrantDigest": {"algorithm": "sha256", "value": WIKIMEDIA_GRANT_DIGEST},
        "bundle": bundle.to_dict(),
        "bundleDigest": {"algorithm": "sha256", "value": bundle.digest()},
        "labelCounts": counts,
        "assertions": {
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
    }


__all__ = [
    "EXPECTED_FINDINGS",
    "EXPECTED_REVIEW_COUNT",
    "HELD_OUT_ITEM_ID",
    "Stage4WikimediaReferenceGateError",
    "WIKIMEDIA_ARTIFACT_SHA256",
    "WIKIMEDIA_BUNDLE_ID",
    "WIKIMEDIA_GRANT_DIGEST",
    "WIKIMEDIA_ITEM_ID",
    "WIKIMEDIA_PACKAGE_ID",
    "WIKIMEDIA_SOURCE_FAMILY_ID",
    "build_wikimedia_reference_completion_candidate",
    "validate_wikimedia_review_work_package",
]
