"""Public Stage 1A dataset governance API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .dataset_catalog_validation import validate_dataset_catalog
from .dataset_contract_common import canonical_sha256
from .dataset_contract_constants import (
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
)
from .dataset_snapshot_validation import validate_dataset_snapshot


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


__all__ = [
    "CATALOG_SCHEMA_VERSION",
    "SNAPSHOT_SCHEMA_VERSION",
    "ENTRY_DECISION_ID",
    "DatasetManifestError",
    "canonical_sha256",
    "validate_dataset_catalog",
    "validate_dataset_snapshot",
    "load_dataset_catalog",
    "load_dataset_snapshot",
]
