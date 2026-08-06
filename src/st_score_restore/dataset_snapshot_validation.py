"""Authorized Stage 1A dataset snapshot validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from .dataset_catalog_validation import validate_dataset_catalog
from .dataset_contract_common import (
    _arr,
    _bool,
    _code_array,
    _date,
    _enum,
    _fields,
    _int,
    _match,
    _obj,
    _permission,
    _permission_valid_on,
    _restriction_by_type,
    _utc_datetime,
    canonical_sha256,
)
from .dataset_contract_constants import (
    ASSIGNED_SPLITS,
    DATASET_ACTOR_ID,
    DatasetManifestError,
    ENTRY_DECISION_ID,
    EVIDENCE_ID,
    ID,
    SHA,
    SEMVER,
    SNAPSHOT_FIELDS,
    SNAPSHOT_SCHEMA_VERSION,
    SPLIT_PURPOSES,
    STAGE1_ENVIRONMENT,
)


def _validate_dataset_snapshot_integrity(
    data: Any,
    *,
    catalog: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], datetime]:
    """Validate digest, assignment, review, and revocation integrity."""
    catalog = validate_dataset_catalog(catalog)
    snapshot = _obj(data, "snapshot")
    _fields(snapshot, SNAPSHOT_FIELDS, "snapshot")
    if snapshot["schemaVersion"] != SNAPSHOT_SCHEMA_VERSION:
        raise DatasetManifestError(
            f"snapshot.schemaVersion must be {SNAPSHOT_SCHEMA_VERSION}"
        )
    if snapshot["entryDecisionId"] != ENTRY_DECISION_ID:
        raise DatasetManifestError(
            f"snapshot.entryDecisionId must be {ENTRY_DECISION_ID}"
        )
    _match(snapshot["snapshotId"], ID, "snapshot.snapshotId")
    if snapshot["datasetId"] != catalog["catalogId"]:
        raise DatasetManifestError("snapshot.datasetId must match catalog.catalogId")
    _match(snapshot["version"], SEMVER, "snapshot.version")
    created_at = _utc_datetime(snapshot["createdAt"], "snapshot.createdAt")
    if snapshot["environment"] != STAGE1_ENVIRONMENT:
        raise DatasetManifestError(
            f"snapshot.environment must be {STAGE1_ENVIRONMENT}"
        )
    if (
        _match(snapshot["catalogSha256"], SHA, "snapshot.catalogSha256")
        != canonical_sha256(catalog)
    ):
        raise DatasetManifestError("snapshot.catalogSha256 does not match catalog")

    item_index = {item["datasetItemId"]: item for item in catalog["items"]}
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
        item_id = _match(assignment["datasetItemId"], ID, f"{where}.datasetItemId")
        family = _match(assignment["sourceFamilyId"], ID, f"{where}.sourceFamilyId")
        split = _enum(assignment["split"], ASSIGNED_SPLITS, f"{where}.split")
        item = item_index.get(item_id or "")
        if item is None or item_id in seen:
            raise DatasetManifestError(f"{where} references unknown or duplicate item")
        seen.add(item_id)
        ordered_ids.append(item_id)
        if family != item["sourceFamilyId"] or split != item["split"]:
            raise DatasetManifestError(f"{where} family/split mismatch")
        if (
            _match(assignment["itemSha256"], SHA, f"{where}.itemSha256")
            != canonical_sha256(item)
        ):
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
        raise DatasetManifestError("snapshot contains source-family split leakage")
    if _bool(snapshot["heldOutFrozen"], "snapshot.heldOutFrozen") != held_out_present:
        raise DatasetManifestError(
            "snapshot.heldOutFrozen does not match assignments"
        )
    if _bool(snapshot["trainingUseActivated"], "snapshot.trainingUseActivated"):
        raise DatasetManifestError("Stage 1A snapshot cannot activate model training")

    revoked_ids = [
        _match(item, ID, "snapshot.revokedItemIds[]")
        for item in _arr(
            snapshot["revokedItemIds"],
            "snapshot.revokedItemIds",
            empty=True,
        )
    ]
    if len(set(revoked_ids)) != len(revoked_ids):
        raise DatasetManifestError("snapshot.revokedItemIds must be unique")
    expected_revoked = sorted(
        item_id
        for item_id, item in item_index.items()
        if item["artifact"]["state"] == "revoked"
        or item["review"]["status"] == "revoked"
    )
    if sorted(revoked_ids) != expected_revoked or seen & set(revoked_ids):
        raise DatasetManifestError("snapshot revocation set is inconsistent")

    coverage = _obj(snapshot["coverage"], "snapshot.coverage")
    _fields(
        coverage,
        {"realItemCount", "syntheticItemCount", "gapCodes"},
        "snapshot.coverage",
    )
    if (
        _int(coverage["realItemCount"], "snapshot.coverage.realItemCount")
        != real_count
    ):
        raise DatasetManifestError("snapshot.coverage.realItemCount mismatch")
    if (
        _int(
            coverage["syntheticItemCount"],
            "snapshot.coverage.syntheticItemCount",
        )
        != synthetic_count
    ):
        raise DatasetManifestError("snapshot.coverage.syntheticItemCount mismatch")
    _code_array(coverage["gapCodes"], "snapshot.coverage.gapCodes")

    review = _obj(snapshot["review"], "snapshot.review")
    _fields(
        review,
        {"status", "reviewedBy", "reviewedOn", "evidenceReference", "noteCodes"},
        "snapshot.review",
    )
    if review["status"] != "approved":
        raise DatasetManifestError("snapshot.review.status must be approved")
    _match(review["reviewedBy"], DATASET_ACTOR_ID, "snapshot.review.reviewedBy")
    reviewed_on = _date(review["reviewedOn"], "snapshot.review.reviewedOn")
    _match(
        review["evidenceReference"],
        EVIDENCE_ID,
        "snapshot.review.evidenceReference",
    )
    _code_array(review["noteCodes"], "snapshot.review.noteCodes")
    if reviewed_on is not None and reviewed_on > created_at.date():
        raise DatasetManifestError(
            "snapshot.review.reviewedOn cannot be after snapshot.createdAt"
        )
    return snapshot, item_index, created_at


def _validate_item_at_snapshot_time(
    item: dict[str, Any],
    *,
    snapshot_date: date,
    index: int,
) -> None:
    """Reject data that was expired, revoking, or approved only after the snapshot."""
    where = f"snapshot.assignments[{index}]"
    if item["revocation"]["status"] != "not_revoked":
        raise DatasetManifestError(
            f"{where} item is revoked or pending deletion at snapshot time"
        )

    retention_expiry = item["retention"]["expiresOn"]
    if retention_expiry is not None and snapshot_date >= date.fromisoformat(
        retention_expiry
    ):
        raise DatasetManifestError(
            f"{where} item retention expired at or before snapshot time"
        )

    review_dates = (
        (
            "rights review",
            item["provenance"]["rightsReview"]["verifiedOn"],
        ),
        ("privacy review", item["privacy"]["reviewedOn"]),
        ("dataset review", item["review"]["reviewedOn"]),
    )
    for label, raw_date in review_dates:
        if raw_date is not None and date.fromisoformat(raw_date) > snapshot_date:
            raise DatasetManifestError(
                f"{where} {label} was completed after snapshot time"
            )


def validate_dataset_snapshot(
    data: Any,
    *,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Validate the only authorized public Stage 1A snapshot boundary.

    This function includes integrity, purpose, temporal, restriction, and split
    authorization checks. Callers must not use the private integrity helper.
    """
    snapshot, item_index, created_at = _validate_dataset_snapshot_integrity(
        data, catalog=catalog
    )
    snapshot_date = created_at.date()
    environment = snapshot["environment"]

    for index, assignment in enumerate(snapshot["assignments"]):
        item_id = assignment["datasetItemId"]
        split = assignment["split"]
        item = item_index[item_id]
        _validate_item_at_snapshot_time(
            item,
            snapshot_date=snapshot_date,
            index=index,
        )
        relevant = SPLIT_PURPOSES[split]
        valid_permissions: list[tuple[str, dict[str, Any]]] = []
        for purpose in relevant:
            permission = _permission(
                item["permissions"][purpose],
                f"snapshot.assignments[{index}].permissions.{purpose}",
            )
            if not _permission_valid_on(permission, snapshot_date):
                continue
            split_rule = _restriction_by_type(permission, "split_allowlist")
            if split_rule is not None and split not in split_rule["values"]:
                continue
            storage_rule = _restriction_by_type(
                permission, "storage_class_allowlist"
            )
            if (
                storage_rule is not None
                and item["retention"]["storageClass"] not in storage_rule["values"]
            ):
                continue
            environment_rule = _restriction_by_type(
                permission, "environment_allowlist"
            )
            if (
                environment_rule is not None
                and environment not in environment_rule["values"]
            ):
                continue
            retention_rule = _restriction_by_type(
                permission, "retention_not_after"
            )
            if retention_rule is not None:
                maximum = date.fromisoformat(retention_rule["date"])
                item_expiry = item["retention"]["expiresOn"]
                if item_expiry is None or date.fromisoformat(item_expiry) > maximum:
                    continue
            valid_permissions.append((purpose, permission))

        if not valid_permissions:
            expected = ", ".join(sorted(relevant))
            raise DatasetManifestError(
                "snapshot assignment is not validly authorized at snapshot time: "
                f"assignments[{index}] item={item_id} split={split}; "
                f"requires a current purpose from [{expected}]"
            )

    return snapshot
