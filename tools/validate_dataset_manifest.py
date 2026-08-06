"""Validate Stage 1A dataset governance metadata and repository contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from jsonschema.exceptions import SchemaError, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_constants import (  # noqa: E402
    CATALOG_SCHEMA_VERSION,
    ENTRY_DECISION_ID,
)
from st_score_restore.dataset_manifest import (  # noqa: E402
    DatasetManifestError,
    load_dataset_catalog,
    load_json_object,
    validate_dataset_snapshot,
)
from tools.dataset_schema_helpers import validate_with_schema  # noqa: E402
from tools.dataset_schema_parity import validate_schema_parity  # noqa: E402


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
    return load_json_object(path)


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
        ROOT / "tools" / "dataset_schema_helpers.py",
        ROOT / "tools" / "dataset_schema_parity.py",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise DatasetManifestError(
            "missing Stage 1A contract files: " + ", ".join(missing)
        )
    catalog_schema = _load_object(required[0])
    snapshot_schema = _load_object(required[1])
    validate_schema_parity(catalog_schema, snapshot_schema)
    example = _load_object(ROOT / "examples" / "dataset-catalog.metadata-only.v1.json")
    validate_with_schema(example, catalog_schema, "metadata-only catalog example")
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
        catalog_schema = _load_object(
            ROOT / "schemas" / "dataset-catalog.schema.json"
        )
        snapshot_schema = _load_object(
            ROOT / "schemas" / "dataset-snapshot.schema.json"
        )
        raw_catalog = _load_object(args.catalog)
        validate_with_schema(raw_catalog, catalog_schema, str(args.catalog))
        catalog = load_dataset_catalog(args.catalog)
        if args.snapshot is not None:
            raw_snapshot = _load_object(args.snapshot)
            validate_with_schema(raw_snapshot, snapshot_schema, str(args.snapshot))
            validate_dataset_snapshot(raw_snapshot, catalog=catalog)
    except (
        OSError,
        ValueError,
        DatasetManifestError,
        SchemaError,
        ValidationError,
    ) as error:
        print(f"ERROR: dataset metadata validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    suffix = " and authorized snapshot" if args.snapshot is not None else ""
    print(
        "Dataset metadata validation passed: "
        f"{len(catalog['items'])} catalog item(s){suffix}; Stage 1A contract "
        f"{CATALOG_SCHEMA_VERSION} bound to {ENTRY_DECISION_ID}."
    )


if __name__ == "__main__":
    main()
