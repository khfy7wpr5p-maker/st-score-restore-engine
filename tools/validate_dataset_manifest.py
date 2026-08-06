#!/usr/bin/env python3
"""Validate Stage 1A dataset governance metadata and repository contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import (  # noqa: E402
    ARTIFACT_STATES,
    CATALOG_FIELDS,
    CATALOG_SCHEMA_VERSION,
    CUSTODIAN_ACTOR_ID,
    CUSTODY_ID,
    DATASET_ACTOR_ID,
    DatasetManifestError,
    ENTRY_DECISION_ID,
    EVIDENCE_ID,
    ITEM_FIELDS,
    PERMISSION_STATES,
    POLICY_ID,
    PRIVACY_ACTOR_ID,
    PRIVACY_CLASSES,
    PURPOSES,
    PURPOSE_ACTOR_ID,
    RECEIPT_ID,
    RESTRICTION_TYPES,
    RIGHTS_ACTOR_ID,
    SNAPSHOT_FIELDS,
    SNAPSHOT_SCHEMA_VERSION,
    SOURCE_KINDS,
    SPLITS,
    STAGE1_ENVIRONMENT,
    SUBJECT_ID,
    load_dataset_catalog,
    validate_dataset_snapshot,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Validate purpose-specific dataset governance metadata. "
            "This tool never reads document artifacts."
        )
    )
    result.add_argument(
        "catalog",
        nargs="?",
        type=Path,
        default=ROOT / "examples" / "dataset-catalog.metadata-only.v1.json",
    )
    result.add_argument("--snapshot", type=Path)
    return result


def _load_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise DatasetManifestError(f"{path} must contain a JSON object")
    return value


def _required(schema: dict[str, Any], where: str) -> set[str]:
    raw = schema.get("required")
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise DatasetManifestError(f"{where}.required must be a string array")
    return set(raw)


def _enum(schema: dict[str, Any], where: str) -> set[str]:
    raw = schema.get("enum")
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise DatasetManifestError(f"{where}.enum must be a string array")
    return set(raw)


def _pattern(schema: dict[str, Any], expected: str, where: str) -> None:
    if schema.get("pattern") != expected:
        raise DatasetManifestError(f"{where} pattern drift")


def validate_schema_parity(
    catalog_schema: dict[str, Any],
    snapshot_schema: dict[str, Any],
) -> None:
    """Fail when structural schema and Python contract constants drift."""
    draft = "https://json-schema.org/draft/2020-12/schema"
    if catalog_schema.get("$schema") != draft:
        raise DatasetManifestError("dataset catalog schema must use Draft 2020-12")
    if snapshot_schema.get("$schema") != draft:
        raise DatasetManifestError("dataset snapshot schema must use Draft 2020-12")

    catalog_properties = catalog_schema.get("properties", {})
    snapshot_properties = snapshot_schema.get("properties", {})
    if _required(catalog_schema, "catalog") != CATALOG_FIELDS:
        raise DatasetManifestError("dataset catalog required-field drift")
    if _required(snapshot_schema, "snapshot") != SNAPSHOT_FIELDS:
        raise DatasetManifestError("dataset snapshot required-field drift")
    if catalog_properties.get("schemaVersion", {}).get("const") != CATALOG_SCHEMA_VERSION:
        raise DatasetManifestError("dataset catalog schema version mismatch")
    if snapshot_properties.get("schemaVersion", {}).get("const") != SNAPSHOT_SCHEMA_VERSION:
        raise DatasetManifestError("dataset snapshot schema version mismatch")
    if catalog_properties.get("entryDecisionId", {}).get("const") != ENTRY_DECISION_ID:
        raise DatasetManifestError("dataset catalog entry-decision drift")
    if snapshot_properties.get("entryDecisionId", {}).get("const") != ENTRY_DECISION_ID:
        raise DatasetManifestError("dataset snapshot entry-decision drift")
    if snapshot_properties.get("environment", {}).get("const") != STAGE1_ENVIRONMENT:
        raise DatasetManifestError("dataset snapshot environment drift")
    if snapshot_properties.get("trainingUseActivated", {}).get("const") is not False:
        raise DatasetManifestError("Stage 1A snapshot schema must prohibit training activation")

    definitions = catalog_schema.get("$defs", {})
    item_schema = definitions.get("item", {})
    item_properties = item_schema.get("properties", {})
    if _required(item_schema, "catalog.$defs.item") != ITEM_FIELDS:
        raise DatasetManifestError("dataset item required-field drift")

    permissions = item_properties.get("permissions", {})
    if _required(permissions, "item.permissions") != set(PURPOSES):
        raise DatasetManifestError("dataset purpose required-field drift")
    if set(permissions.get("properties", {})) != set(PURPOSES):
        raise DatasetManifestError("dataset purpose property drift")

    permission = definitions.get("permission", {})
    permission_states = _enum(
        permission.get("properties", {}).get("status", {}),
        "permission.status",
    )
    if permission_states != PERMISSION_STATES:
        raise DatasetManifestError("permission-state drift")

    if _enum(item_properties.get("split", {}), "item.split") != SPLITS:
        raise DatasetManifestError("dataset split drift")
    if _enum(
        item_properties.get("artifact", {}).get("properties", {}).get("state", {}),
        "item.artifact.state",
    ) != ARTIFACT_STATES:
        raise DatasetManifestError("artifact-state drift")
    if _enum(
        item_properties.get("provenance", {})
        .get("properties", {})
        .get("sourceKind", {}),
        "item.provenance.sourceKind",
    ) != SOURCE_KINDS:
        raise DatasetManifestError("source-kind drift")
    if _enum(
        item_properties.get("privacy", {})
        .get("properties", {})
        .get("classification", {}),
        "item.privacy.classification",
    ) != PRIVACY_CLASSES:
        raise DatasetManifestError("privacy-class drift")

    restriction_variants = definitions.get("restriction", {}).get("oneOf", [])
    restriction_types = {
        variant.get("properties", {}).get("type", {}).get("const")
        for variant in restriction_variants
    }
    if restriction_types != RESTRICTION_TYPES:
        raise DatasetManifestError("typed-restriction drift")

    _pattern(
        item_properties["provenance"]["properties"]["sourceReference"],
        EVIDENCE_ID.pattern,
        "provenance.sourceReference",
    )
    _pattern(
        item_properties["provenance"]["properties"]["rightsHolderId"],
        SUBJECT_ID.pattern,
        "provenance.rightsHolderId",
    )
    _pattern(
        item_properties["provenance"]["properties"]["rightsReview"]["properties"]["verifiedBy"],
        RIGHTS_ACTOR_ID.pattern,
        "rightsReview.verifiedBy",
    )
    _pattern(
        item_properties["privacy"]["properties"]["reviewedBy"],
        PRIVACY_ACTOR_ID.pattern,
        "privacy.reviewedBy",
    )
    _pattern(
        permission["properties"]["authorizedBy"],
        PURPOSE_ACTOR_ID.pattern,
        "permission.authorizedBy",
    )
    _pattern(
        item_properties["review"]["properties"]["reviewedBy"],
        DATASET_ACTOR_ID.pattern,
        "review.reviewedBy",
    )
    artifact_properties = item_properties["artifact"]["properties"]
    _pattern(
        artifact_properties["custodianId"],
        CUSTODIAN_ACTOR_ID.pattern,
        "artifact.custodianId",
    )
    _pattern(
        artifact_properties["storageLocator"],
        CUSTODY_ID.pattern,
        "artifact.storageLocator",
    )
    _pattern(
        artifact_properties["custodyProfileId"],
        POLICY_ID.pattern,
        "artifact.custodyProfileId",
    )
    _pattern(
        item_properties["retention"]["properties"]["deletionReceiptReference"],
        RECEIPT_ID.pattern,
        "retention.deletionReceiptReference",
    )


def validate_repository_contract() -> None:
    required = (
        ROOT / "schemas" / "dataset-catalog.schema.json",
        ROOT / "schemas" / "dataset-snapshot.schema.json",
        ROOT / "docs" / "stage-1a-dataset-governance-contract.md",
        ROOT / "docs" / "adr" / "0012-stage-1a-purpose-bound-dataset-governance.md",
        ROOT / "docs" / "adr" / "0013-stage-1-entry-decision-record.md",
        ROOT / "src" / "st_score_restore" / "dataset_contract_constants.py",
        ROOT / "src" / "st_score_restore" / "dataset_contract_common.py",
        ROOT / "src" / "st_score_restore" / "dataset_item_core.py",
        ROOT / "src" / "st_score_restore" / "dataset_item_policy.py",
        ROOT / "src" / "st_score_restore" / "dataset_item_final.py",
        ROOT / "src" / "st_score_restore" / "dataset_item_validation.py",
        ROOT / "src" / "st_score_restore" / "dataset_catalog_validation.py",
        ROOT / "src" / "st_score_restore" / "dataset_snapshot_validation.py",
        ROOT / "src" / "st_score_restore" / "dataset_manifest.py",
        ROOT / "src" / "st_score_restore" / "dataset_snapshot_policy.py",
        ROOT / "tests" / "dataset_test_item_helpers.py",
        ROOT / "tests" / "dataset_test_snapshot_helpers.py",
        ROOT / "tests" / "test_dataset_manifest.py",
        ROOT / "tests" / "test_dataset_snapshot_policy.py",
        ROOT / "tests" / "test_dataset_schema_parity.py",
    )
    missing = [
        str(path.relative_to(ROOT))
        for path in required
        if not path.is_file()
    ]
    if missing:
        raise DatasetManifestError(
            "missing Stage 1A contract files: " + ", ".join(missing)
        )

    validate_schema_parity(
        _load_object(required[0]),
        _load_object(required[1]),
    )

    private_boundary = "_validate_dataset_snapshot_integrity"
    owner = ROOT / "src" / "st_score_restore" / "dataset_snapshot_validation.py"
    for search_root in (ROOT / "src", ROOT / "tools", ROOT / "tests"):
        for path in search_root.rglob("*.py"):
            if path in {owner, Path(__file__).resolve()}:
                continue
            if private_boundary in path.read_text(encoding="utf-8"):
                raise DatasetManifestError(
                    "private snapshot-integrity helper referenced outside "
                    "dataset_snapshot_validation.py"
                )


def main() -> None:
    args = parser().parse_args()
    try:
        validate_repository_contract()
        catalog = load_dataset_catalog(args.catalog)
        if args.snapshot is not None:
            validate_dataset_snapshot(
                _load_object(args.snapshot),
                catalog=catalog,
            )
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
        DatasetManifestError,
    ) as error:
        print(
            f"ERROR: dataset metadata validation failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
    suffix = " and authorized snapshot" if args.snapshot is not None else ""
    print(
        "Dataset metadata validation passed: "
        f"{len(catalog['items'])} catalog item(s){suffix}; "
        f"Stage 1A contract {CATALOG_SCHEMA_VERSION} bound to {ENTRY_DECISION_ID}."
    )


if __name__ == "__main__":
    main()
