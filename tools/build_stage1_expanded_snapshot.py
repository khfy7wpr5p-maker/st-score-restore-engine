"""Build/check the post-C17 Stage 1 expanded catalog, snapshot, and coverage report.

Historical C15/C16 files are immutable. This tool only owns version-2 aggregate
outputs and deliberately keeps Stage 1 exit / Stage 2 authorization separate.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_constants import (  # noqa: E402
    DEGRADATIONS,
    INPUT_MEDIA,
    NOTATION_KINDS,
    SOURCE_KINDS,
)
from st_score_restore.dataset_manifest import (  # noqa: E402
    canonical_sha256,
    load_json_object,
    validate_dataset_catalog,
    validate_dataset_snapshot,
)
from tools.evaluate_stage1_corpus_readiness import evaluate_corpus_readiness  # noqa: E402

OUT_DIR = ROOT / "evidence" / "stage1c" / "corpus"
CATALOG_PATH = OUT_DIR / "catalog.v2.json"
SNAPSHOT_PATH = OUT_DIR / "snapshot.expanded.v2.json"
REPORT_PATH = OUT_DIR / "coverage-bias-report.v2.json"

HISTORICAL_CATALOG_PATH = OUT_DIR / "catalog.v1.json"
C17A_CATALOG_PATH = ROOT / "evidence" / "stage1c" / "wikimedia-guitar-technical-exercise-no1" / "catalog.v1.json"
C17B_CATALOG_PATH = ROOT / "evidence" / "stage1c" / "imslp911664-c17b-guitar-tab" / "catalog.v1.json"
C17C_CATALOG_PATH = ROOT / "evidence" / "stage1c" / "imslp82860-c17c-noise" / "catalog.v2.json"
C17D_CATALOG_PATH = ROOT / "evidence" / "stage1c" / "nearer-my-god-to-thee-c17d" / "catalog.v1.json"

AS_OF = date(2026, 9, 2)
CREATED_AT = "2026-09-01T23:10:00Z"
REVIEWED_ON = "2026-09-02"
REVIEWED_BY = "actor.dataset:opq_543323ff2e140749c8f6ee4f839e1bd6"
REVIEW_EVIDENCE = "evidence:opq_07f1e704e60b0fdf88670d5115b32360"

CATALOG_ID = "dataset.catalog.stage1c-expanded-corpus.v2"
SNAPSHOT_ID = "dataset.snapshot.stage1c-expanded.v2"
REPORT_ID = "dataset.coverage-bias.stage1c-expanded.v2"

SELECTED_IDS = (
    "dataset.item.imslp799143-beethoven-op48-no3.v1",
    "dataset.item.wikimedia-guitar-technical-exercise-no1.v1",
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
    "dataset.item.imslp82860-chopin-op69.v2",
    "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1",
)


class ExpandedSnapshotError(ValueError):
    """Raised when expanded Stage 1 evidence cannot be derived safely."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _item_from(path: Path, item_id: str) -> dict[str, Any]:
    catalog = load_json_object(path)
    matches = [item for item in catalog["items"] if item["datasetItemId"] == item_id]
    if len(matches) != 1:
        raise ExpandedSnapshotError(f"expected exactly one {item_id} in {path.relative_to(ROOT)}")
    return matches[0]


def build_catalog() -> dict[str, Any]:
    items = [
        _item_from(HISTORICAL_CATALOG_PATH, SELECTED_IDS[0]),
        _item_from(C17A_CATALOG_PATH, SELECTED_IDS[1]),
        _item_from(C17B_CATALOG_PATH, SELECTED_IDS[2]),
        _item_from(C17C_CATALOG_PATH, SELECTED_IDS[3]),
        _item_from(C17D_CATALOG_PATH, SELECTED_IDS[4]),
    ]
    if [item["datasetItemId"] for item in items] != list(SELECTED_IDS):
        raise ExpandedSnapshotError("selected item order drifted")
    if any(item["datasetItemId"] == "dataset.item.imslp82860-chopin-op69.v1" for item in items):
        raise ExpandedSnapshotError("historical Chopin v1 must not enter expanded catalog")

    digests = [item["artifact"]["sha256"] for item in items]
    if len(digests) != len(set(digests)):
        raise ExpandedSnapshotError("duplicate artifact digest in expanded catalog")

    catalog = {
        "schemaVersion": "1.3.0",
        "entryDecisionId": "adr-0013-stage-1-entry-v1",
        "catalogId": CATALOG_ID,
        "descriptionCode": "stage1c-expanded-corpus-v2",
        "items": items,
    }
    return validate_dataset_catalog(catalog)


def _assignments(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "datasetItemId": item["datasetItemId"],
            "sourceFamilyId": item["sourceFamilyId"],
            "split": item["split"],
            "itemSha256": canonical_sha256(item),
        }
        for item in sorted(catalog["items"], key=lambda item: item["datasetItemId"])
    ]


def build_snapshot(catalog: dict[str, Any]) -> dict[str, Any]:
    readiness = evaluate_corpus_readiness(catalog, as_of=AS_OF)
    expected = {
        "state": "ready",
        "reasonCodes": [],
        "counts": {"development": 3, "held_out": 2},
        "sourceFamilyCounts": {"development": 3, "held_out": 2},
    }
    if readiness != expected:
        raise ExpandedSnapshotError(f"unexpected expanded readiness: {readiness}")

    snapshot = {
        "schemaVersion": "1.2.0",
        "entryDecisionId": "adr-0013-stage-1-entry-v1",
        "snapshotId": SNAPSHOT_ID,
        "datasetId": catalog["catalogId"],
        "version": "2.0.0",
        "createdAt": CREATED_AT,
        "environment": "stage1_offline",
        "catalogSha256": canonical_sha256(catalog),
        "assignments": _assignments(catalog),
        "heldOutFrozen": True,
        "trainingUseActivated": False,
        "revokedItemIds": [],
        "coverage": {
            "realItemCount": 5,
            "syntheticItemCount": 0,
            "gapCodes": [],
        },
        "review": {
            "status": "approved",
            "reviewedBy": REVIEWED_BY,
            "reviewedOn": REVIEWED_ON,
            "evidenceReference": REVIEW_EVIDENCE,
            "noteCodes": [
                "c17-expanded-snapshot",
                "c17c-v2-replaces-v1",
                "coverage-review-required",
            ],
        },
    }
    return validate_dataset_snapshot(snapshot, catalog=catalog)


def _coverage_target(code: str, observed: int) -> dict[str, Any]:
    return {"code": code, "observedItemCount": observed, "state": "covered" if observed > 0 else "missing"}


def build_report(catalog: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    items_by_id = {item["datasetItemId"]: item for item in catalog["items"]}
    assigned = [items_by_id[a["datasetItemId"]] for a in snapshot["assignments"]]

    split_counts = Counter(item["split"] for item in assigned)
    source_family_counts = {
        split: len({item["sourceFamilyId"] for item in assigned if item["split"] == split})
        for split in ("development", "held_out")
    }
    page_counts = {
        split: sum(item["input"]["pageCount"] for item in assigned if item["split"] == split)
        for split in ("development", "held_out")
    }
    notation = {kind: 0 for kind in sorted(NOTATION_KINDS)}
    input_kind = {kind: 0 for kind in sorted(INPUT_MEDIA)}
    degradation = {kind: 0 for kind in sorted(DEGRADATIONS)}
    source_kind = {kind: 0 for kind in sorted(SOURCE_KINDS)}
    non_none = 0
    for item in assigned:
        for kind in item["input"]["notationKinds"]:
            notation[kind] += 1
        input_kind[item["input"]["kind"]] += 1
        if any(value != "none" for value in item["input"]["degradations"]):
            non_none += 1
        for value in item["input"]["degradations"]:
            degradation[value] += 1
        source_kind[item["provenance"]["sourceKind"]] += 1

    targets = [
        _coverage_target("notation.staff", notation["staff"]),
        _coverage_target("notation.guitar_tab", notation["guitar_tab"]),
        _coverage_target("notation.combined_staff_tab", notation["combined_staff_tab"]),
        _coverage_target("capture.scanned_pdf", input_kind["scanned_pdf"]),
        _coverage_target("capture.phone_photo", input_kind["phone_photo"]),
        _coverage_target("degradation.non_none", non_none),
    ]
    gaps: list[str] = []
    missing_to_gap = {
        "notation.guitar_tab": "coverage.missing-guitar-tab",
        "notation.combined_staff_tab": "coverage.missing-combined-staff-tab",
        "capture.phone_photo": "coverage.missing-phone-photo",
        "degradation.non_none": "coverage.missing-degraded-source",
    }
    for target in targets:
        if target["state"] == "missing" and target["code"] in missing_to_gap:
            gaps.append(missing_to_gap[target["code"]])
    if split_counts["development"] < 2:
        gaps.append("coverage.single-item-development")
    if split_counts["held_out"] < 2:
        gaps.append("coverage.single-item-held-out")
    if len(assigned) <= 2:
        gaps.append("coverage.two-item-corpus")
    gaps = sorted(set(gaps))
    if gaps:
        raise ExpandedSnapshotError(f"expanded corpus still has Stage 1 coverage gaps: {gaps}")

    return {
        "schemaVersion": "1.0.0",
        "reportId": REPORT_ID,
        "snapshotId": snapshot["snapshotId"],
        "snapshotSha256": canonical_sha256(snapshot),
        "catalogSha256": canonical_sha256(catalog),
        "evaluatedOn": "2026-09-02",
        "measurementBasis": "validated_catalog_snapshot_metadata",
        "counts": {
            "itemCount": len(assigned),
            "realItemCount": 5,
            "syntheticItemCount": 0,
            "splitItemCounts": {"development": split_counts["development"], "held_out": split_counts["held_out"]},
            "sourceFamilyCounts": {
                "development": source_family_counts["development"],
                "held_out": source_family_counts["held_out"],
                "total": len({item["sourceFamilyId"] for item in assigned}),
            },
            "pageCounts": {"development": page_counts["development"], "held_out": page_counts["held_out"], "total": sum(page_counts.values())},
            "notationItemCounts": notation,
            "inputKindItemCounts": input_kind,
            "degradationItemCounts": degradation,
            "sourceKindItemCounts": source_kind,
        },
        "coverageTargets": targets,
        "gapCodes": [],
        "biasFindings": [
            {"code": "capture_condition_concentration", "state": "controlled", "evidenceCode": "multiple-capture-kinds"},
            {"code": "degradation_coverage_gap", "state": "controlled", "evidenceCode": "non-none-degradation-present"},
            {"code": "held_out_coverage_limit", "state": "controlled", "evidenceCode": "two-held-out-source-families"},
            {"code": "notation_layout_concentration", "state": "controlled", "evidenceCode": "staff-tab-and-combined-layouts-present"},
            {"code": "source_family_leakage_risk", "state": "controlled", "evidenceCode": "distinct-source-families-and-digests-across-splits"},
            {"code": "source_selection_concentration", "state": "observed", "evidenceCode": "public-domain-majority-with-one-licensed-item"},
        ],
        "sufficiency": {
            "state": "review_required",
            "reasonCodes": [],
            "requiresCorpusExpansion": False,
            "stage1ExitSupported": False,
            "stage2EntrySupported": False,
        },
        "assertions": {
            "heldOutFrozen": True,
            "trainingUseActivated": False,
            "representativenessEstablished": False,
            "absenceOfBiasEstablished": False,
            "restorationEffectivenessEstablished": False,
            "omrImprovementEstablished": False,
        },
    }


def build_all() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    catalog = build_catalog()
    snapshot = build_snapshot(catalog)
    report = build_report(catalog, snapshot)
    return catalog, snapshot, report


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _check(path: Path, expected: dict[str, Any]) -> None:
    if not path.is_file():
        raise ExpandedSnapshotError(f"missing committed expanded evidence: {path.relative_to(ROOT)}")
    actual = load_json_object(path)
    if canonical_json(actual) != canonical_json(expected):
        raise ExpandedSnapshotError(f"committed expanded evidence drifted: {path.relative_to(ROOT)}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--summary", action="store_true")
    return p


def main() -> None:
    args = parser().parse_args()
    try:
        catalog, snapshot, report = build_all()
        if args.write:
            _write(CATALOG_PATH, catalog)
            _write(SNAPSHOT_PATH, snapshot)
            _write(REPORT_PATH, report)
        elif args.check:
            _check(CATALOG_PATH, catalog)
            _check(SNAPSHOT_PATH, snapshot)
            _check(REPORT_PATH, report)
        print(f"catalogSha256={canonical_sha256(catalog)}")
        print(f"snapshotSha256={canonical_sha256(snapshot)}")
        print(f"coverageReportSha256={canonical_sha256(report)}")
        print(f"gapCodes={','.join(report['gapCodes'])}")
        print(f"coverageState={report['sufficiency']['state']}")
        print(f"splitCounts={report['counts']['splitItemCounts']}")
        print(f"sourceFamilyCounts={report['counts']['sourceFamilyCounts']}")
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: expanded Stage 1 snapshot build failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
