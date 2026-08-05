"""Stage 1A dataset governance metadata validation (standard library only)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

CATALOG_SCHEMA_VERSION = "1.0.0"
SNAPSHOT_SCHEMA_VERSION = "1.0.0"

ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
LOCATOR = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")

PURPOSES = (
    "fixture_validation",
    "quality_evaluation",
    "quality_calibration",
    "pdf_pipeline_evaluation",
    "safety_calibration",
    "held_out_evaluation",
    "model_training",
    "publication",
    "demonstration",
)
PERMISSION_STATES = {
    "not_requested",
    "pending",
    "granted",
    "denied",
    "expired",
    "withdrawn",
    "not_applicable",
}
SPLITS = {"unassigned", "development", "calibration", "held_out", "training_reserved"}
SOURCE_KINDS = {"project_authored", "public_domain", "licensed", "user_provided", "synthetic"}
INPUT_MEDIA = {
    "digital_pdf": "application/pdf",
    "scanned_pdf": "application/pdf",
    "hybrid_pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "phone_photo": "image/jpeg",
}
NOTATION_KINDS = {"staff", "guitar_tab", "combined_staff_tab"}
DEGRADATIONS = {
    "none",
    "skew",
    "perspective",
    "page_curl",
    "shadow",
    "glare",
    "uneven_lighting",
    "blur",
    "noise",
    "compression",
    "low_resolution",
}


class DatasetManifestError(ValueError):
    """Dataset metadata violates the approved Stage 1A contract."""


def _obj(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DatasetManifestError(f"{where} must be an object")
    return value


def _arr(value: Any, where: str, *, empty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (not empty and not value):
        qualifier = "an" if empty else "a non-empty"
        raise DatasetManifestError(f"{where} must be {qualifier} array")
    return value


def _fields(value: dict[str, Any], names: set[str], where: str) -> None:
    missing, unknown = names - value.keys(), value.keys() - names
    if missing or unknown:
        raise DatasetManifestError(
            f"{where} field mismatch; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )


def _text(value: Any, where: str, *, null: bool = False) -> str | None:
    if value is None and null:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DatasetManifestError(f"{where} must be a non-empty string")
    return value


def _match(
    value: Any,
    pattern: re.Pattern[str],
    where: str,
    *,
    null: bool = False,
) -> str | None:
    text = _text(value, where, null=null)
    if text is not None and not pattern.fullmatch(text):
        raise DatasetManifestError(f"{where} has invalid format")
    return text


def _enum(value: Any, choices: set[str], where: str) -> str:
    text = _text(value, where)
    assert text is not None
    if text not in choices:
        raise DatasetManifestError(f"{where} has unsupported value: {text}")
    return text


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise DatasetManifestError(f"{where} must be a boolean")
    return value


def _int(value: Any, where: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise DatasetManifestError(f"{where} must be an integer >= {minimum}")
    return value


def canonical_sha256(value: Any) -> str:
    """Return a deterministic digest for JSON-compatible metadata."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _permission(raw: Any, where: str) -> str:
    value = _obj(raw, where)
    names = {
        "status",
        "authorizationReference",
        "authorizedBy",
        "authorizedOn",
        "expiresOn",
        "restrictions",
        "revokedOn",
        "revocationReference",
    }
    _fields(value, names, where)
    status = _enum(value["status"], PERMISSION_STATES, f"{where}.status")
    auth = (
        _text(
            value["authorizationReference"],
            f"{where}.authorizationReference",
            null=True,
        ),
        _text(value["authorizedBy"], f"{where}.authorizedBy", null=True),
        _match(value["authorizedOn"], DATE, f"{where}.authorizedOn", null=True),
    )
    expires = _match(value["expiresOn"], DATE, f"{where}.expiresOn", null=True)
    revoked = _match(value["revokedOn"], DATE, f"{where}.revokedOn", null=True)
    rev_ref = _text(
        value["revocationReference"],
        f"{where}.revocationReference",
        null=True,
    )
    restrictions = _arr(
        value["restrictions"],
        f"{where}.restrictions",
        empty=True,
    )
    for index, restriction in enumerate(restrictions):
        _text(restriction, f"{where}.restrictions[{index}]")
    if status == "granted":
        if None in auth or revoked is not None or rev_ref is not None:
            raise DatasetManifestError(
                f"{where} granted permission requires authorization evidence only"
            )
    elif status == "expired":
        if None in auth or expires is None or revoked is not None or rev_ref is not None:
            raise DatasetManifestError(
                f"{where} expired permission requires authorization and expiry"
            )
    elif status == "withdrawn":
        if None in auth or revoked is None or rev_ref is None:
            raise DatasetManifestError(
                f"{where} withdrawn permission requires authorization and "
                "revocation evidence"
            )
    elif any(item is not None for item in (*auth, expires, revoked, rev_ref)):
        raise DatasetManifestError(
            f"{where} {status} permission cannot claim authorization evidence"
        )
    return status


def _item(raw: Any, index: int) -> dict[str, Any]:
    where = f"items[{index}]"
    value = _obj(raw, where)
    names = {
        "datasetItemId",
        "sourceFamilyId",
        "parentItemId",
        "artifact",
        "provenance",
        "privacy",
        "input",
        "permissions",
        "split",
        "retention",
        "syntheticGeneration",
        "review",
        "assertions",
    }
    _fields(value, names, where)
    item_id = _match(value["datasetItemId"], ID, f"{where}.datasetItemId")
    family_id = _match(value["sourceFamilyId"], ID, f"{where}.sourceFamilyId")
    parent_id = _match(
        value["parentItemId"],
        ID,
        f"{where}.parentItemId",
        null=True,
    )
    assert item_id and family_id
    if parent_id == item_id:
        raise DatasetManifestError(f"{where}.parentItemId cannot reference itself")

    artifact = _obj(value["artifact"], f"{where}.artifact")
    _fields(
        artifact,
        {"state", "sha256", "byteSize", "storageLocator"},
        f"{where}.artifact",
    )
    artifact_state = _enum(
        artifact["state"],
        {"metadata_only", "external_available", "revoked"},
        f"{where}.artifact.state",
    )
    digest = _match(
        artifact["sha256"],
        SHA,
        f"{where}.artifact.sha256",
        null=True,
    )
    size = artifact["byteSize"]
    if size is not None:
        _int(size, f"{where}.artifact.byteSize", 1)
    locator = _match(
        artifact["storageLocator"],
        LOCATOR,
        f"{where}.artifact.storageLocator",
        null=True,
    )
    if artifact_state == "metadata_only" and any(
        item is not None for item in (digest, size, locator)
    ):
        raise DatasetManifestError(
            f"{where}.artifact metadata_only cannot reference bytes"
        )
    if artifact_state == "external_available" and any(
        item is None for item in (digest, size, locator)
    ):
        raise DatasetManifestError(
            f"{where}.artifact external_available requires digest, size, and locator"
        )
    if artifact_state == "revoked" and (
        digest is None or size is None or locator is not None
    ):
        raise DatasetManifestError(
            f"{where}.artifact revoked keeps digest/size but no locator"
        )

    provenance = _obj(value["provenance"], f"{where}.provenance")
    _fields(
        provenance,
        {"sourceKind", "sourceReference", "rightsHolder", "licenseId", "usageBasis"},
        f"{where}.provenance",
    )
    source_kind = _enum(
        provenance["sourceKind"],
        SOURCE_KINDS,
        f"{where}.provenance.sourceKind",
    )
    for name in ("sourceReference", "rightsHolder", "licenseId", "usageBasis"):
        _text(provenance[name], f"{where}.provenance.{name}")

    privacy = _obj(value["privacy"], f"{where}.privacy")
    _fields(
        privacy,
        {
            "classification",
            "reviewStatus",
            "deidentificationMethod",
            "deidentifiedArtifactSha256",
        },
        f"{where}.privacy",
    )
    privacy_class = _enum(
        privacy["classification"],
        {"none", "deidentified", "personal", "student"},
        f"{where}.privacy.classification",
    )
    privacy_review = _enum(
        privacy["reviewStatus"],
        {"not_required", "pending", "approved", "rejected"},
        f"{where}.privacy.reviewStatus",
    )
    deid_method = _text(
        privacy["deidentificationMethod"],
        f"{where}.privacy.deidentificationMethod",
        null=True,
    )
    deid_sha = _match(
        privacy["deidentifiedArtifactSha256"],
        SHA,
        f"{where}.privacy.deidentifiedArtifactSha256",
        null=True,
    )
    if privacy_class == "none" and (
        privacy_review not in {"not_required", "approved"}
        or deid_method
        or deid_sha
    ):
        raise DatasetManifestError(
            f"{where}.privacy none classification is inconsistent"
        )
    if privacy_class == "deidentified" and (
        privacy_review != "approved"
        or deid_method is None
        or deid_sha is None
    ):
        raise DatasetManifestError(
            f"{where}.privacy deidentified data requires approved method and digest"
        )
    if privacy_class in {"personal", "student"} and (
        privacy_review == "not_required"
        or deid_method is not None
        or deid_sha is not None
    ):
        raise DatasetManifestError(
            f"{where}.privacy identifiable data requires review and cannot "
            "claim de-identification"
        )

    input_data = _obj(value["input"], f"{where}.input")
    _fields(
        input_data,
        {"kind", "mediaType", "notationKinds", "pageCount", "degradations"},
        f"{where}.input",
    )
    kind = _enum(input_data["kind"], set(INPUT_MEDIA), f"{where}.input.kind")
    if input_data["mediaType"] != INPUT_MEDIA[kind]:
        raise DatasetManifestError(f"{where}.input.mediaType does not match kind")
    for field, choices in (
        ("notationKinds", NOTATION_KINDS),
        ("degradations", DEGRADATIONS),
    ):
        raw_values = _arr(input_data[field], f"{where}.input.{field}")
        values = {
            _enum(item, choices, f"{where}.input.{field}[]")
            for item in raw_values
        }
        if len(values) != len(raw_values):
            raise DatasetManifestError(f"{where}.input.{field} must be unique")
        if field == "degradations" and "none" in values and len(values) > 1:
            raise DatasetManifestError(
                f"{where}.input.degradations cannot mix none and damage"
            )
    _int(input_data["pageCount"], f"{where}.input.pageCount", 1)

    permissions = _obj(value["permissions"], f"{where}.permissions")
    _fields(permissions, set(PURPOSES), f"{where}.permissions")
    states = {
        purpose: _permission(
            permissions[purpose],
            f"{where}.permissions.{purpose}",
        )
        for purpose in PURPOSES
    }
    granted = {
        purpose for purpose, state in states.items() if state == "granted"
    }
    split = _enum(value["split"], SPLITS, f"{where}.split")
    if split == "unassigned" and granted:
        raise DatasetManifestError(
            f"{where} unassigned item cannot activate purpose permissions"
        )
    if split == "held_out" and granted != {"held_out_evaluation"}:
        raise DatasetManifestError(
            f"{where} held_out item may grant only held_out_evaluation"
        )
    if split in {"development", "calibration"} and granted & {
        "held_out_evaluation",
        "model_training",
    }:
        raise DatasetManifestError(
            f"{where} {split} item cannot be held-out or training data"
        )
    if split == "training_reserved" and granted != {"model_training"}:
        raise DatasetManifestError(
            f"{where} training_reserved item may grant only model_training"
        )
    if granted and (
        artifact_state != "external_available"
        or privacy_review in {"pending", "rejected"}
    ):
        raise DatasetManifestError(
            f"{where} active permission requires approved external artifact"
        )
    if privacy_class in {"personal", "student"} and granted & {
        "model_training",
        "publication",
        "demonstration",
    }:
        raise DatasetManifestError(
            f"{where} identifiable personal/student data cannot be trained or published"
        )
    if (
        source_kind == "user_provided"
        and "model_training" in granted
        and privacy_class != "deidentified"
    ):
        raise DatasetManifestError(
            f"{where} user-provided training requires deidentified data"
        )

    retention = _obj(value["retention"], f"{where}.retention")
    _fields(
        retention,
        {"policy", "expiresOn", "storageClass", "deletionRequired"},
        f"{where}.retention",
    )
    policy = _enum(
        retention["policy"],
        {
            "metadata_only",
            "external_until_date",
            "delete_after_validation",
            "prohibited",
        },
        f"{where}.retention.policy",
    )
    expires = _match(
        retention["expiresOn"],
        DATE,
        f"{where}.retention.expiresOn",
        null=True,
    )
    storage = _enum(
        retention["storageClass"],
        {"not_assigned", "custody_external"},
        f"{where}.retention.storageClass",
    )
    deletion = _bool(
        retention["deletionRequired"],
        f"{where}.retention.deletionRequired",
    )
    if (policy == "external_until_date") != (expires is not None):
        raise DatasetManifestError(
            f"{where}.retention expiry does not match policy"
        )
    if artifact_state == "metadata_only" and (
        policy not in {"metadata_only", "prohibited"}
        or storage != "not_assigned"
    ):
        raise DatasetManifestError(
            f"{where}.retention does not match metadata-only artifact"
        )
    if artifact_state == "external_available" and (
        policy in {"metadata_only", "prohibited"}
        or storage != "custody_external"
    ):
        raise DatasetManifestError(
            f"{where}.retention external artifact requires external "
            "custody/deletion policy"
        )
    if artifact_state == "revoked" and not deletion:
        raise DatasetManifestError(
            f"{where}.retention revoked item must require deletion"
        )

    synthetic = value["syntheticGeneration"]
    if source_kind == "synthetic":
        synthetic = _obj(synthetic, f"{where}.syntheticGeneration")
        _fields(
            synthetic,
            {
                "generator",
                "generatorVersion",
                "generatorCommit",
                "seed",
                "parameters",
                "cleanSourceApproved",
            },
            f"{where}.syntheticGeneration",
        )
        _text(synthetic["generator"], f"{where}.syntheticGeneration.generator")
        _text(
            synthetic["generatorVersion"],
            f"{where}.syntheticGeneration.generatorVersion",
        )
        _match(
            synthetic["generatorCommit"],
            SHA,
            f"{where}.syntheticGeneration.generatorCommit",
        )
        _int(synthetic["seed"], f"{where}.syntheticGeneration.seed")
        _obj(synthetic["parameters"], f"{where}.syntheticGeneration.parameters")
        if synthetic["cleanSourceApproved"] is not True or parent_id is None:
            raise DatasetManifestError(
                f"{where} synthetic item requires approved non-synthetic parent"
            )
    elif synthetic is not None or parent_id is not None:
        raise DatasetManifestError(
            f"{where} parent/generation metadata is only for synthetic sources"
        )

    review = _obj(value["review"], f"{where}.review")
    _fields(
        review,
        {"status", "reviewedBy", "reviewedOn", "notes"},
        f"{where}.review",
    )
    review_state = _enum(
        review["status"],
        {"planned", "pending", "approved", "rejected", "revoked"},
        f"{where}.review.status",
    )
    reviewer = _text(
        review["reviewedBy"],
        f"{where}.review.reviewedBy",
        null=True,
    )
    reviewed_on = _match(
        review["reviewedOn"],
        DATE,
        f"{where}.review.reviewedOn",
        null=True,
    )
    if not isinstance(review["notes"], str):
        raise DatasetManifestError(f"{where}.review.notes must be a string")
    completed = review_state in {"approved", "rejected", "revoked"}
    if completed != (reviewer is not None and reviewed_on is not None):
        raise DatasetManifestError(
            f"{where}.review reviewer/date do not match status"
        )
    if granted and review_state != "approved":
        raise DatasetManifestError(
            f"{where} active permission requires approved review"
        )
    if artifact_state == "external_available" and review_state != "approved":
        raise DatasetManifestError(
            f"{where} external artifact requires approved review"
        )
    if artifact_state == "revoked" and review_state != "revoked":
        raise DatasetManifestError(
            f"{where} revoked artifact requires revoked review"
        )

    assertions = _obj(value["assertions"], f"{where}.assertions")
    assertion_names = {
        "teacherApprovalImpliedDatasetPermission",
        "teacherApprovalImpliedTrainingPermission",
        "originalBytesInGit",
    }
    _fields(assertions, assertion_names, f"{where}.assertions")
    if any(assertions[name] is not False for name in assertion_names):
        raise DatasetManifestError(f"{where}.assertions must remain false")

    return {
        "raw": value,
        "id": item_id,
        "family": family_id,
        "parent": parent_id,
        "source": source_kind,
        "artifact": artifact_state,
        "digest": digest,
        "split": split,
        "review": review_state,
    }


def validate_dataset_catalog(data: Any) -> dict[str, Any]:
    """Validate a complete Stage 1A dataset catalog."""
    catalog = _obj(data, "catalog")
    _fields(
        catalog,
        {"schemaVersion", "catalogId", "description", "items"},
        "catalog",
    )
    if catalog["schemaVersion"] != CATALOG_SCHEMA_VERSION:
        raise DatasetManifestError(
            f"catalog.schemaVersion must be {CATALOG_SCHEMA_VERSION}"
        )
    _match(catalog["catalogId"], ID, "catalog.catalogId")
    _text(catalog["description"], "catalog.description")
    items = [
        _item(raw, index)
        for index, raw in enumerate(_arr(catalog["items"], "catalog.items"))
    ]

    by_id: dict[str, dict[str, Any]] = {}
    digest_family: dict[str, str] = {}
    family_splits: dict[str, set[str]] = {}
    for item in items:
        if item["id"] in by_id:
            raise DatasetManifestError(
                f"duplicate datasetItemId: {item['id']}"
            )
        by_id[item["id"]] = item
        if item["digest"]:
            prior = digest_family.setdefault(item["digest"], item["family"])
            if prior != item["family"]:
                raise DatasetManifestError(
                    "identical artifact digest crosses source families"
                )
        if item["split"] != "unassigned":
            family_splits.setdefault(item["family"], set()).add(item["split"])
    for item in items:
        if item["parent"] is None:
            continue
        parent = by_id.get(item["parent"])
        if parent is None:
            raise DatasetManifestError(
                f"{item['id']} references unknown parentItemId"
            )
        if parent["source"] == "synthetic":
            raise DatasetManifestError(
                f"{item['id']} cannot derive from synthetic parent"
            )
        if parent["family"] != item["family"]:
            raise DatasetManifestError(
                f"{item['id']} must share sourceFamilyId with parent"
            )
    if any(len(splits) > 1 for splits in family_splits.values()):
        raise DatasetManifestError("source-family split leakage detected")
    return catalog


def validate_dataset_snapshot(
    data: Any,
    *,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Validate a frozen dataset snapshot against its catalog."""
    catalog = validate_dataset_catalog(catalog)
    snapshot = _obj(data, "snapshot")
    names = {
        "schemaVersion",
        "snapshotId",
        "datasetId",
        "version",
        "createdAt",
        "catalogSha256",
        "assignments",
        "heldOutFrozen",
        "trainingUseActivated",
        "revokedItemIds",
        "coverage",
        "review",
    }
    _fields(snapshot, names, "snapshot")
    if snapshot["schemaVersion"] != SNAPSHOT_SCHEMA_VERSION:
        raise DatasetManifestError(
            f"snapshot.schemaVersion must be {SNAPSHOT_SCHEMA_VERSION}"
        )
    _match(snapshot["snapshotId"], ID, "snapshot.snapshotId")
    if snapshot["datasetId"] != catalog["catalogId"]:
        raise DatasetManifestError(
            "snapshot.datasetId must match catalog.catalogId"
        )
    _match(snapshot["version"], SEMVER, "snapshot.version")
    _match(snapshot["createdAt"], UTC, "snapshot.createdAt")
    if _match(
        snapshot["catalogSha256"],
        SHA,
        "snapshot.catalogSha256",
    ) != canonical_sha256(catalog):
        raise DatasetManifestError(
            "snapshot.catalogSha256 does not match catalog"
        )

    item_index = {
        item["datasetItemId"]: item for item in catalog["items"]
    }
    seen: set[str] = set()
    families: dict[str, set[str]] = {}
    ordered_ids: list[str] = []
    real_count = 0
    synthetic_count = 0
    held_out_present = False
    assignments = _arr(snapshot["assignments"], "snapshot.assignments")
    for index, raw in enumerate(assignments):
        where = f"snapshot.assignments[{index}]"
        assignment = _obj(raw, where)
        _fields(
            assignment,
            {"datasetItemId", "sourceFamilyId", "split", "itemSha256"},
            where,
        )
        item_id = _match(
            assignment["datasetItemId"],
            ID,
            f"{where}.datasetItemId",
        )
        family = _match(
            assignment["sourceFamilyId"],
            ID,
            f"{where}.sourceFamilyId",
        )
        split = _enum(
            assignment["split"],
            SPLITS - {"unassigned"},
            f"{where}.split",
        )
        item = item_index.get(item_id or "")
        if item is None or item_id in seen:
            raise DatasetManifestError(
                f"{where} references unknown or duplicate item"
            )
        seen.add(item_id)
        ordered_ids.append(item_id)
        if family != item["sourceFamilyId"] or split != item["split"]:
            raise DatasetManifestError(f"{where} family/split mismatch")
        if _match(
            assignment["itemSha256"],
            SHA,
            f"{where}.itemSha256",
        ) != canonical_sha256(item):
            raise DatasetManifestError(f"{where}.itemSha256 mismatch")
        if (
            item["artifact"]["state"] != "external_available"
            or item["review"]["status"] != "approved"
        ):
            raise DatasetManifestError(
                f"{where} snapshot requires approved external artifact"
            )
        families.setdefault(family, set()).add(split)
        held_out_present = held_out_present or split == "held_out"
        if item["provenance"]["sourceKind"] == "synthetic":
            synthetic_count += 1
        else:
            real_count += 1
    if ordered_ids != sorted(ordered_ids):
        raise DatasetManifestError(
            "snapshot.assignments must be sorted by datasetItemId"
        )
    if any(len(splits) > 1 for splits in families.values()):
        raise DatasetManifestError(
            "snapshot contains source-family split leakage"
        )
    if _bool(
        snapshot["heldOutFrozen"],
        "snapshot.heldOutFrozen",
    ) != held_out_present:
        raise DatasetManifestError(
            "snapshot.heldOutFrozen does not match assignments"
        )
    if _bool(
        snapshot["trainingUseActivated"],
        "snapshot.trainingUseActivated",
    ):
        raise DatasetManifestError(
            "Stage 1A snapshot cannot activate model training"
        )

    revoked_ids = [
        _match(item, ID, "snapshot.revokedItemIds[]")
        for item in _arr(
            snapshot["revokedItemIds"],
            "snapshot.revokedItemIds",
            empty=True,
        )
    ]
    if len(set(revoked_ids)) != len(revoked_ids):
        raise DatasetManifestError(
            "snapshot.revokedItemIds must be unique"
        )
    expected_revoked = sorted(
        item_id
        for item_id, item in item_index.items()
        if item["artifact"]["state"] == "revoked"
        or item["review"]["status"] == "revoked"
    )
    if sorted(revoked_ids) != expected_revoked or seen & set(revoked_ids):
        raise DatasetManifestError(
            "snapshot revocation set is inconsistent"
        )

    coverage = _obj(snapshot["coverage"], "snapshot.coverage")
    _fields(
        coverage,
        {"realItemCount", "syntheticItemCount", "gapNotes"},
        "snapshot.coverage",
    )
    if _int(
        coverage["realItemCount"],
        "snapshot.coverage.realItemCount",
    ) != real_count:
        raise DatasetManifestError(
            "snapshot.coverage.realItemCount mismatch"
        )
    if _int(
        coverage["syntheticItemCount"],
        "snapshot.coverage.syntheticItemCount",
    ) != synthetic_count:
        raise DatasetManifestError(
            "snapshot.coverage.syntheticItemCount mismatch"
        )
    gap_notes = _arr(
        coverage["gapNotes"],
        "snapshot.coverage.gapNotes",
        empty=True,
    )
    for index, note in enumerate(gap_notes):
        _text(note, f"snapshot.coverage.gapNotes[{index}]")

    review = _obj(snapshot["review"], "snapshot.review")
    _fields(
        review,
        {"status", "reviewedBy", "reviewedOn", "notes"},
        "snapshot.review",
    )
    if review["status"] != "approved":
        raise DatasetManifestError(
            "snapshot.review.status must be approved"
        )
    _text(review["reviewedBy"], "snapshot.review.reviewedBy")
    _match(review["reviewedOn"], DATE, "snapshot.review.reviewedOn")
    if not isinstance(review["notes"], str):
        raise DatasetManifestError(
            "snapshot.review.notes must be a string"
        )
    return snapshot


def load_dataset_catalog(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return validate_dataset_catalog(json.load(handle))


def load_dataset_snapshot(
    path: str | Path,
    *,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return validate_dataset_snapshot(json.load(handle), catalog=catalog)
