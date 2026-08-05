#!/usr/bin/env python3
"""Validate Stage 1A dataset governance metadata and repository contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import (  # noqa: E402
    CATALOG_SCHEMA_VERSION,
    SNAPSHOT_SCHEMA_VERSION,
    DatasetManifestError,
    load_dataset_catalog,
    load_dataset_snapshot,
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


def _load_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise DatasetManifestError(f"{path} must contain a JSON object")
    return value


def validate_repository_contract() -> None:
    required = (
        ROOT / "schemas" / "dataset-catalog.schema.json",
        ROOT / "schemas" / "dataset-snapshot.schema.json",
        ROOT / "docs" / "stage-1a-dataset-governance-contract.md",
        ROOT
        / "docs"
        / "adr"
        / "0012-stage-1a-purpose-bound-dataset-governance.md",
        ROOT / "src" / "st_score_restore" / "dataset_manifest.py",
        ROOT / "tests" / "test_dataset_manifest.py",
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

    catalog_schema = _load_object(required[0])
    snapshot_schema = _load_object(required[1])
    draft = "https://json-schema.org/draft/2020-12/schema"
    if catalog_schema.get("$schema") != draft:
        raise DatasetManifestError(
            "dataset catalog schema must use Draft 2020-12"
        )
    if snapshot_schema.get("$schema") != draft:
        raise DatasetManifestError(
            "dataset snapshot schema must use Draft 2020-12"
        )
    if (
        catalog_schema.get("properties", {})
        .get("schemaVersion", {})
        .get("const")
        != CATALOG_SCHEMA_VERSION
    ):
        raise DatasetManifestError(
            "dataset catalog schema version mismatch"
        )
    if (
        snapshot_schema.get("properties", {})
        .get("schemaVersion", {})
        .get("const")
        != SNAPSHOT_SCHEMA_VERSION
    ):
        raise DatasetManifestError(
            "dataset snapshot schema version mismatch"
        )
    if (
        snapshot_schema.get("properties", {})
        .get("trainingUseActivated", {})
        .get("const")
        is not False
    ):
        raise DatasetManifestError(
            "Stage 1A snapshot schema must prohibit training activation"
        )

    assertions = (
        catalog_schema.get("$defs", {})
        .get("item", {})
        .get("properties", {})
        .get("assertions", {})
        .get("properties", {})
    )
    for name in (
        "teacherApprovalImpliedDatasetPermission",
        "teacherApprovalImpliedTrainingPermission",
        "originalBytesInGit",
    ):
        if assertions.get(name, {}).get("const") is not False:
            raise DatasetManifestError(
                f"dataset catalog assertion {name} must remain false"
            )


def main() -> None:
    args = parser().parse_args()
    try:
        validate_repository_contract()
        catalog = load_dataset_catalog(args.catalog)
        if args.snapshot is not None:
            load_dataset_snapshot(args.snapshot, catalog=catalog)
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
    suffix = " and snapshot" if args.snapshot is not None else ""
    print(
        "Dataset metadata validation passed: "
        f"{len(catalog['items'])} catalog item(s){suffix}; "
        "Stage 1A repository contract present."
    )


if __name__ == "__main__":
    main()
