"""Public Stage 1A dataset governance API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .dataset_catalog_validation import validate_dataset_catalog
from .dataset_contract_common import (
    _strict_json_load,
    canonical_sha256,
)
from .dataset_contract_constants import (
    CATALOG_SCHEMA_VERSION,
    DatasetManifestError,
    ENTRY_DECISION_ID,
    SNAPSHOT_SCHEMA_VERSION,
)
from .dataset_snapshot_validation import validate_dataset_snapshot


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load one strict JSON object with duplicate-key and finite-number checks."""
    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        value = _strict_json_load(handle, str(resolved))
    if not isinstance(value, dict):
        raise DatasetManifestError(f"{resolved} must contain a JSON object")
    return value


def load_dataset_catalog(path: str | Path) -> dict[str, Any]:
    return validate_dataset_catalog(load_json_object(path))


def load_dataset_snapshot(
    path: str | Path,
    *,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    return validate_dataset_snapshot(load_json_object(path), catalog=catalog)


__all__ = [
    "CATALOG_SCHEMA_VERSION",
    "SNAPSHOT_SCHEMA_VERSION",
    "ENTRY_DECISION_ID",
    "DatasetManifestError",
    "canonical_sha256",
    "load_json_object",
    "validate_dataset_catalog",
    "validate_dataset_snapshot",
    "load_dataset_catalog",
    "load_dataset_snapshot",
]
