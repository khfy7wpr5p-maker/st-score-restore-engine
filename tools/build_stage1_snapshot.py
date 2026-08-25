"""Build and verify the deterministic Stage 1C digest-addressed snapshot freeze."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_manifest import (  # noqa: E402
    canonical_sha256,
    load_dataset_catalog,
    load_dataset_snapshot,
)
from tools.evaluate_stage1_corpus_readiness import evaluate_corpus_readiness  # noqa: E402

CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v1.json"
SNAPSHOT_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "snapshot.freeze.v1.json"
AS_OF = date(2026, 8, 25)
CREATED_AT = "2026-08-25T15:40:00Z"
REVIEWED_ON = "2026-08-25"
REVIEWED_BY = "actor.dataset:opq_543323ff2e140749c8f6ee4f839e1bd6"
REVIEW_EVIDENCE = "evidence:opq_519827b4ec96be85e73e0581de8b8c0d"
SNAPSHOT_ID = "dataset.snapshot.stage1c-freeze.v1"
SNAPSHOT_VERSION = "1.0.0"
GAP_CODES = ["coverage.single-item-per-split", "coverage.two-item-corpus"]


class SnapshotFreezeError(ValueError):
    """Raised when the deterministic C15 snapshot freeze cannot be produced."""


def _build_assignments(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    items = sorted(catalog["items"], key=lambda item: item["datasetItemId"])
    return [
        {
            "datasetItemId": item["datasetItemId"],
            "sourceFamilyId": item["sourceFamilyId"],
            "split": item["split"],
            "itemSha256": canonical_sha256(item),
        }
        for item in items
    ]


def build_snapshot(catalog: dict[str, Any]) -> dict[str, Any]:
    readiness = evaluate_corpus_readiness(catalog, as_of=AS_OF)
    if readiness != {
        "state": "ready",
        "reasonCodes": [],
        "counts": {"development": 1, "held_out": 1},
        "sourceFamilyCounts": {"development": 1, "held_out": 1},
    }:
        raise SnapshotFreezeError(f"unexpected corpus readiness: {readiness}")

    real_count = sum(
        item["provenance"]["sourceKind"] != "synthetic" for item in catalog["items"]
    )
    synthetic_count = len(catalog["items"]) - real_count
    revoked = sorted(
        item["datasetItemId"]
        for item in catalog["items"]
        if item["artifact"]["state"] == "revoked"
        or item["review"]["status"] == "revoked"
    )

    snapshot = {
        "schemaVersion": "1.2.0",
        "entryDecisionId": "adr-0013-stage-1-entry-v1",
        "snapshotId": SNAPSHOT_ID,
        "datasetId": catalog["catalogId"],
        "version": SNAPSHOT_VERSION,
        "createdAt": CREATED_AT,
        "environment": "stage1_offline",
        "catalogSha256": canonical_sha256(catalog),
        "assignments": _build_assignments(catalog),
        "heldOutFrozen": True,
        "trainingUseActivated": False,
        "revokedItemIds": revoked,
        "coverage": {
            "realItemCount": real_count,
            "syntheticItemCount": synthetic_count,
            "gapCodes": GAP_CODES,
        },
        "review": {
            "status": "approved",
            "reviewedBy": REVIEWED_BY,
            "reviewedOn": REVIEWED_ON,
            "evidenceReference": REVIEW_EVIDENCE,
            "noteCodes": ["c15-digest-freeze", "coverage-not-yet-accepted"],
        },
    }
    return load_dataset_snapshot_from_object(snapshot, catalog=catalog)


def load_dataset_snapshot_from_object(
    snapshot: dict[str, Any], *, catalog: dict[str, Any]
) -> dict[str, Any]:
    """Validate one in-memory snapshot through the public Stage 1 boundary."""
    from st_score_restore.dataset_manifest import validate_dataset_snapshot

    return validate_dataset_snapshot(snapshot, catalog=catalog)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def verify_committed_snapshot(
    expected: dict[str, Any], *, catalog: dict[str, Any], path: Path = SNAPSHOT_PATH
) -> dict[str, Any]:
    if not path.is_file():
        raise SnapshotFreezeError(f"missing committed snapshot: {path.relative_to(ROOT)}")
    committed = load_dataset_snapshot(path, catalog=catalog)
    if canonical_json(committed) != canonical_json(expected):
        raise SnapshotFreezeError("committed snapshot differs from deterministic C15 freeze")
    return committed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", action="store_true")
    mode.add_argument("--check", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    try:
        catalog = load_dataset_catalog(CATALOG_PATH)
        snapshot = build_snapshot(catalog)
        if args.check:
            snapshot = verify_committed_snapshot(snapshot, catalog=catalog)
        print(f"catalogSha256={canonical_sha256(catalog)}")
        for assignment in snapshot["assignments"]:
            print(
                "itemSha256="
                f"{assignment['datasetItemId']}:{assignment['itemSha256']}"
            )
        print(f"snapshotSha256={canonical_sha256(snapshot)}")
        print(f"snapshotJson={canonical_json(snapshot)}")
    except (OSError, ValueError) as error:
        print(f"ERROR: Stage 1C C15 snapshot freeze failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
