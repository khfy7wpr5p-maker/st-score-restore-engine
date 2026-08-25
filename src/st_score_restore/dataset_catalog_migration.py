"""Fail-closed migration from the legacy Stage 1A catalog to Stage 1C profiles."""

from __future__ import annotations

import copy
from typing import Any

from .dataset_contract_constants import (
    CATALOG_FIELDS,
    CATALOG_SCHEMA_VERSION,
    DatasetManifestError,
    ITEM_FIELDS,
    LEGACY_CATALOG_SCHEMA_VERSION,
    LEGACY_STORAGE_CLASS,
)


def migrate_dataset_catalog_v1_2_to_v1_3(data: Any) -> dict[str, Any]:
    """Migrate legacy metadata without ever lowering a recorded custody state.

    Legacy `custody_external` artifacts are conservatively mapped to
    `sensitive_custody` + `high_assurance_vault`. This migration never infers
    `open_corpus` or `restricted_corpus`; those classifications require the
    separately planned deterministic eligibility resolver and current evidence.
    """
    if not isinstance(data, dict):
        raise DatasetManifestError("legacy catalog must be an object")
    if set(data) != CATALOG_FIELDS:
        raise DatasetManifestError("legacy catalog top-level fields do not match v1.2")
    if data.get("schemaVersion") != LEGACY_CATALOG_SCHEMA_VERSION:
        raise DatasetManifestError(
            f"legacy catalog schemaVersion must be {LEGACY_CATALOG_SCHEMA_VERSION}"
        )
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise DatasetManifestError("legacy catalog items must be a non-empty array")

    migrated = copy.deepcopy(data)
    migrated["schemaVersion"] = CATALOG_SCHEMA_VERSION
    legacy_item_fields = ITEM_FIELDS - {"eligibilityClass"}

    for index, item in enumerate(migrated["items"]):
        where = f"items[{index}]"
        if not isinstance(item, dict) or set(item) != legacy_item_fields:
            raise DatasetManifestError(f"{where} does not match the legacy v1.2 item shape")
        artifact = item.get("artifact")
        retention = item.get("retention")
        if not isinstance(artifact, dict) or not isinstance(retention, dict):
            raise DatasetManifestError(f"{where} legacy artifact/retention must be objects")
        state = artifact.get("state")
        storage = retention.get("storageClass")
        if state == "metadata_only":
            if storage != "not_assigned":
                raise DatasetManifestError(
                    f"{where} legacy metadata_only item cannot claim external custody"
                )
            item["eligibilityClass"] = "blocked"
        elif state in {"external_available", "revoked"}:
            if storage != LEGACY_STORAGE_CLASS:
                raise DatasetManifestError(
                    f"{where} legacy external/revoked item must use {LEGACY_STORAGE_CLASS}"
                )
            item["eligibilityClass"] = "sensitive_custody"
            retention["storageClass"] = "high_assurance_vault"
        else:
            raise DatasetManifestError(f"{where}.artifact.state is not a legacy state")

        permissions = item.get("permissions")
        if not isinstance(permissions, dict):
            raise DatasetManifestError(f"{where}.permissions must be an object")
        for purpose, permission in permissions.items():
            if not isinstance(permission, dict):
                raise DatasetManifestError(
                    f"{where}.permissions.{purpose} must be an object"
                )
            restrictions = permission.get("restrictions")
            if not isinstance(restrictions, list):
                raise DatasetManifestError(
                    f"{where}.permissions.{purpose}.restrictions must be an array"
                )
            for restriction in restrictions:
                if not isinstance(restriction, dict):
                    raise DatasetManifestError(
                        f"{where}.permissions.{purpose}.restrictions must contain objects"
                    )
                if restriction.get("type") != "storage_class_allowlist":
                    continue
                values = restriction.get("values")
                if values != [LEGACY_STORAGE_CLASS]:
                    raise DatasetManifestError(
                        f"{where}.permissions.{purpose} has unsupported legacy storage restriction"
                    )
                restriction["values"] = ["high_assurance_vault"]

    # Import lazily to avoid a module cycle at import time.
    from .dataset_catalog_validation import validate_dataset_catalog

    return validate_dataset_catalog(migrated)
