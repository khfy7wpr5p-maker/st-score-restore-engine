"""Fail-closed Stage 4 human reference-label work-package contract.

This module validates an *empty* human-review worksheet. It deliberately cannot
turn the worksheet into accepted reference evidence, cannot invent labels, and
cannot authorize calibration execution. Real labels must be supplied by a human
expert and accepted through a later, separate evidence decision.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .dataset_contract_common import canonical_sha256
from .stage4_reference_labels import FINDING_TYPES, REFERENCE_LABELS, REFERENCE_LABEL_CONTRACT_VERSION
from .stage4_purpose_grants import APPROVED_GRANT_CANONICAL_SHA256

WORK_PACKAGE_SCHEMA_VERSION = "1.0.0"
WORK_PACKAGE_ID = "stage4.reference-label-review.beethoven-barley.v1"
WORK_PACKAGE_CANONICAL_SHA256 = "93e1a61bbdd698dbabf1ba88164453056acf3f2ea37fa159305a0f244b2253ba"
WORK_PACKAGE_STATE = "awaiting_human_labels"

DEVELOPMENT_ITEMS = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": {
        "short": "beethoven",
        "sourceFamilyId": "source.family.imslp799143-beethoven-op48-no3.v1",
        "artifactSha256": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
        "pageCount": 4,
    },
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": {
        "short": "barley",
        "sourceFamilyId": "source.family.barley-mnoah-your-face-your-tongue-your-wit.v1",
        "artifactSha256": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
        "pageCount": 2,
    },
}
HELD_OUT_ITEM = {
    "datasetItemId": "dataset.item.imslp82860-chopin-op69.v2",
    "artifactSha256": "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3",
    "split": "held_out",
    "purpose": "held_out_evaluation",
    "includedInDevelopmentReview": False,
    "candidateDerivationAuthorized": False,
}


class Stage4ReferenceLabelWorkPackageError(ValueError):
    """The human-review work package is unsafe, non-empty, or out of scope."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage4ReferenceLabelWorkPackageError(message)


def validate_reference_label_work_package(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise Stage4ReferenceLabelWorkPackageError("work package must be an object")
    value = deepcopy(dict(raw))
    _require(
        set(value) == {
            "schemaVersion", "packageId", "state", "contractVersion", "purposeGrantDigest",
            "reviewScope", "labelVocabulary", "findingTypes", "items", "heldOutExclusions", "assertions"
        },
        "work-package top-level fields drifted",
    )
    _require(value["schemaVersion"] == WORK_PACKAGE_SCHEMA_VERSION, "work-package schema drifted")
    _require(value["packageId"] == WORK_PACKAGE_ID, "work-package id drifted")
    _require(value["state"] == WORK_PACKAGE_STATE, "work package must remain awaiting_human_labels")
    _require(value["contractVersion"] == REFERENCE_LABEL_CONTRACT_VERSION, "reference-label contract version drifted")
    _require(value["purposeGrantDigest"] == APPROVED_GRANT_CANONICAL_SHA256, "purpose-grant binding drifted")
    _require(value["labelVocabulary"] == sorted(REFERENCE_LABELS), "label vocabulary drifted")
    _require(value["findingTypes"] == sorted(FINDING_TYPES), "finding taxonomy drifted")

    _require(
        value["reviewScope"] == {
            "split": "development",
            "dataClass": "real",
            "purpose": "safety_calibration",
            "reviewMethodRequired": "human_expert_review",
            "acceptedRealReferenceBundle": False,
            "realDataCalibrationExecutionAuthorized": False,
            "modelPredictionsAllowedAsReference": False,
        },
        "review scope drifted or became permissive",
    )

    items = value["items"]
    _require(isinstance(items, list) and len(items) == 2, "work package must contain exactly two development items")
    seen_items: set[str] = set()
    slot_count = 0
    label_ids: set[str] = set()
    observation_ids: set[str] = set()
    for item in items:
        _require(isinstance(item, dict), "work-package item must be an object")
        _require(set(item) == {"datasetItemId", "sourceFamilyId", "artifactSha256", "pageCount", "pages"}, "work-package item fields drifted")
        item_id = item["datasetItemId"]
        _require(item_id in DEVELOPMENT_ITEMS and item_id not in seen_items, f"unexpected or duplicate development item: {item_id}")
        seen_items.add(item_id)
        expected = DEVELOPMENT_ITEMS[item_id]
        _require(item["sourceFamilyId"] == expected["sourceFamilyId"], f"source-family identity drifted: {item_id}")
        _require(item["artifactSha256"] == expected["artifactSha256"], f"artifact identity drifted: {item_id}")
        _require(item["pageCount"] == expected["pageCount"], f"page count drifted: {item_id}")
        pages = item["pages"]
        _require(isinstance(pages, list) and len(pages) == expected["pageCount"], f"page review count drifted: {item_id}")
        _require([page.get("pageNumber") for page in pages] == list(range(1, expected["pageCount"] + 1)), f"page order drifted: {item_id}")
        for page in pages:
            _require(set(page) == {"pageNumber", "reviews"}, "page review fields drifted")
            page_number = page["pageNumber"]
            reviews = page["reviews"]
            _require(isinstance(reviews, list) and len(reviews) == len(FINDING_TYPES), "each page must expose exactly one slot per finding")
            _require([r.get("findingType") for r in reviews] == sorted(FINDING_TYPES), "finding order/scope drifted")
            for review in reviews:
                _require(
                    set(review) == {
                        "labelId", "observationId", "findingType", "referenceLabel",
                        "reviewerReference", "provenanceReference", "reviewedOn"
                    },
                    "review slot fields drifted",
                )
                finding = review["findingType"]
                short = expected["short"]
                _require(review["labelId"] == f"stage4.label.{short}.p{page_number}.{finding}.v1", "label id drifted")
                _require(review["observationId"] == f"stage4.obs.{short}.p{page_number}.{finding}.v1", "observation id drifted")
                _require(review["labelId"] not in label_ids, "duplicate label id")
                _require(review["observationId"] not in observation_ids, "duplicate observation id")
                label_ids.add(review["labelId"])
                observation_ids.add(review["observationId"])
                for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn"):
                    _require(review[field] is None, f"work package unexpectedly contains human evidence in {field}")
                slot_count += 1

    _require(seen_items == set(DEVELOPMENT_ITEMS), "development item set drifted")
    _require(slot_count == 42, "human-review slot count must be exactly 42")
    _require(value["heldOutExclusions"] == [HELD_OUT_ITEM], "held-out exclusion drifted")
    _require(
        value["assertions"] == {
            "humanLabelsPresent": False,
            "referenceBundleAccepted": False,
            "labelsAutomaticallyGenerated": False,
            "modelPredictionsUsedAsReferenceLabels": False,
            "heldOutIncludedInDevelopmentReview": False,
            "realDataCalibrationExecuted": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
        "work-package assertions drifted",
    )
    _require(canonical_sha256(value) == WORK_PACKAGE_CANONICAL_SHA256, "work-package canonical digest drifted")
    return value


def summarize_reference_label_work_package(raw: Mapping[str, Any]) -> dict[str, Any]:
    value = validate_reference_label_work_package(raw)
    return {
        "schemaVersion": WORK_PACKAGE_SCHEMA_VERSION,
        "status": WORK_PACKAGE_STATE,
        "packageDigest": {"algorithm": "sha256", "value": WORK_PACKAGE_CANONICAL_SHA256},
        "developmentItemCount": len(value["items"]),
        "pageCount": sum(item["pageCount"] for item in value["items"]),
        "reviewSlotCount": sum(len(page["reviews"]) for item in value["items"] for page in item["pages"]),
        "humanLabelsPresent": False,
        "referenceBundleAccepted": False,
        "realDataCalibrationExecutionAuthorized": False,
        "heldOutIncluded": False,
    }


__all__ = [
    "DEVELOPMENT_ITEMS", "HELD_OUT_ITEM", "Stage4ReferenceLabelWorkPackageError",
    "WORK_PACKAGE_CANONICAL_SHA256", "WORK_PACKAGE_ID", "WORK_PACKAGE_SCHEMA_VERSION",
    "summarize_reference_label_work_package", "validate_reference_label_work_package",
]
