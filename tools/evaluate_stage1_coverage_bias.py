"""Build and verify the Stage 1C frozen-snapshot coverage and bias report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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
    load_dataset_catalog,
    load_dataset_snapshot,
    load_json_object,
)

CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v1.json"
SNAPSHOT_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "snapshot.freeze.v1.json"
REPORT_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "coverage-bias-report.v1.json"
REPORT_ID = "dataset.coverage-bias.stage1c-freeze.v1"
EVALUATED_ON = "2026-08-25"
EXPECTED_SNAPSHOT_SHA256 = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"


class CoverageBiasError(ValueError):
    """Raised when C16 coverage/bias evidence cannot be derived safely."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _coverage_target(code: str, observed: int) -> dict[str, Any]:
    return {
        "code": code,
        "observedItemCount": observed,
        "state": "covered" if observed > 0 else "missing",
    }


def build_coverage_bias_report(
    catalog: dict[str, Any], snapshot: dict[str, Any]
) -> dict[str, Any]:
    catalog_sha = canonical_sha256(catalog)
    snapshot_sha = canonical_sha256(snapshot)
    if snapshot["catalogSha256"] != catalog_sha:
        raise CoverageBiasError("snapshot catalog digest does not match current catalog")
    if snapshot_sha != EXPECTED_SNAPSHOT_SHA256:
        raise CoverageBiasError("unexpected frozen snapshot digest")
    if snapshot["heldOutFrozen"] is not True:
        raise CoverageBiasError("held-out split is not frozen")
    if snapshot["trainingUseActivated"] is not False:
        raise CoverageBiasError("Stage 1 training must remain disabled")
    if snapshot["revokedItemIds"]:
        raise CoverageBiasError("revoked items are present in the frozen snapshot")

    items_by_id = {item["datasetItemId"]: item for item in catalog["items"]}
    assigned_items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for assignment in snapshot["assignments"]:
        item_id = assignment["datasetItemId"]
        if item_id in seen_ids:
            raise CoverageBiasError("duplicate snapshot assignment")
        seen_ids.add(item_id)
        item = items_by_id.get(item_id)
        if item is None:
            raise CoverageBiasError("snapshot assignment references an unknown item")
        if canonical_sha256(item) != assignment["itemSha256"]:
            raise CoverageBiasError("snapshot item digest does not match catalog metadata")
        if item["sourceFamilyId"] != assignment["sourceFamilyId"]:
            raise CoverageBiasError("snapshot source-family binding drifted")
        if item["split"] != assignment["split"]:
            raise CoverageBiasError("snapshot split binding drifted")
        assigned_items.append(item)

    if set(items_by_id) != seen_ids:
        raise CoverageBiasError("catalog contains items outside the frozen snapshot")

    split_counts = Counter(item["split"] for item in assigned_items)
    source_family_by_split = {
        split: len(
            {
                item["sourceFamilyId"]
                for item in assigned_items
                if item["split"] == split
            }
        )
        for split in ("development", "held_out")
    }
    page_counts = {
        split: sum(
            item["input"]["pageCount"]
            for item in assigned_items
            if item["split"] == split
        )
        for split in ("development", "held_out")
    }

    notation_counts = {kind: 0 for kind in sorted(NOTATION_KINDS)}
    input_kind_counts = {kind: 0 for kind in sorted(INPUT_MEDIA)}
    degradation_counts = {kind: 0 for kind in sorted(DEGRADATIONS)}
    source_kind_counts = {kind: 0 for kind in sorted(SOURCE_KINDS)}
    non_none_degradation_items = 0

    for item in assigned_items:
        for kind in item["input"]["notationKinds"]:
            notation_counts[kind] += 1
        input_kind_counts[item["input"]["kind"]] += 1
        if any(degradation != "none" for degradation in item["input"]["degradations"]):
            non_none_degradation_items += 1
        for degradation in item["input"]["degradations"]:
            degradation_counts[degradation] += 1
        source_kind_counts[item["provenance"]["sourceKind"]] += 1

    coverage_targets = [
        _coverage_target("notation.staff", notation_counts["staff"]),
        _coverage_target("notation.guitar_tab", notation_counts["guitar_tab"]),
        _coverage_target(
            "notation.combined_staff_tab", notation_counts["combined_staff_tab"]
        ),
        _coverage_target("capture.scanned_pdf", input_kind_counts["scanned_pdf"]),
        _coverage_target("capture.phone_photo", input_kind_counts["phone_photo"]),
        _coverage_target("degradation.non_none", non_none_degradation_items),
    ]

    gap_codes: list[str] = []
    missing_to_gap = {
        "notation.guitar_tab": "coverage.missing-guitar-tab",
        "notation.combined_staff_tab": "coverage.missing-combined-staff-tab",
        "capture.phone_photo": "coverage.missing-phone-photo",
        "degradation.non_none": "coverage.missing-degraded-source",
    }
    for target in coverage_targets:
        if target["state"] == "missing" and target["code"] in missing_to_gap:
            gap_codes.append(missing_to_gap[target["code"]])
    if split_counts["development"] < 2:
        gap_codes.append("coverage.single-item-development")
    if split_counts["held_out"] < 2:
        gap_codes.append("coverage.single-item-held-out")
    if len(assigned_items) <= 2:
        gap_codes.append("coverage.two-item-corpus")
    gap_codes = sorted(set(gap_codes))

    source_family_total = len({item["sourceFamilyId"] for item in assigned_items})
    real_count = sum(
        item["provenance"]["sourceKind"] != "synthetic" for item in assigned_items
    )
    synthetic_count = len(assigned_items) - real_count

    report = {
        "schemaVersion": "1.0.0",
        "reportId": REPORT_ID,
        "snapshotId": snapshot["snapshotId"],
        "snapshotSha256": snapshot_sha,
        "catalogSha256": catalog_sha,
        "evaluatedOn": EVALUATED_ON,
        "measurementBasis": "validated_catalog_snapshot_metadata",
        "counts": {
            "itemCount": len(assigned_items),
            "realItemCount": real_count,
            "syntheticItemCount": synthetic_count,
            "splitItemCounts": {
                "development": split_counts["development"],
                "held_out": split_counts["held_out"],
            },
            "sourceFamilyCounts": {
                "development": source_family_by_split["development"],
                "held_out": source_family_by_split["held_out"],
                "total": source_family_total,
            },
            "pageCounts": {
                "development": page_counts["development"],
                "held_out": page_counts["held_out"],
                "total": sum(page_counts.values()),
            },
            "notationItemCounts": notation_counts,
            "inputKindItemCounts": input_kind_counts,
            "degradationItemCounts": degradation_counts,
            "sourceKindItemCounts": source_kind_counts,
        },
        "coverageTargets": coverage_targets,
        "gapCodes": gap_codes,
        "biasFindings": [
            {
                "code": "capture_condition_concentration",
                "state": "observed",
                "evidenceCode": "all-items-scanned-pdf",
            },
            {
                "code": "degradation_coverage_gap",
                "state": "observed",
                "evidenceCode": "no-non-none-degradation",
            },
            {
                "code": "held_out_coverage_limit",
                "state": "observed",
                "evidenceCode": "one-held-out-source-family",
            },
            {
                "code": "notation_layout_concentration",
                "state": "observed",
                "evidenceCode": "all-items-staff-only",
            },
            {
                "code": "source_family_leakage_risk",
                "state": "controlled",
                "evidenceCode": "distinct-source-families-and-digests",
            },
            {
                "code": "source_selection_concentration",
                "state": "observed",
                "evidenceCode": "all-items-public-domain",
            },
        ],
        "sufficiency": {
            "state": "insufficient" if gap_codes else "review_required",
            "reasonCodes": gap_codes,
            "requiresCorpusExpansion": bool(gap_codes),
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
    return report


def verify_committed_report(
    expected: dict[str, Any], *, path: Path = REPORT_PATH
) -> dict[str, Any]:
    if not path.is_file():
        raise CoverageBiasError(f"missing committed report: {path.relative_to(ROOT)}")
    try:
        committed = load_json_object(path)
    except ValueError as error:
        raise CoverageBiasError("committed C16 report is not strict JSON") from error
    if canonical_json(committed) != canonical_json(expected):
        raise CoverageBiasError("committed C16 report differs from deterministic evaluation")
    return committed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit", action="store_true")
    mode.add_argument("--check", action="store_true")
    result.add_argument("--require-insufficient", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    try:
        catalog = load_dataset_catalog(CATALOG_PATH)
        snapshot = load_dataset_snapshot(SNAPSHOT_PATH, catalog=catalog)
        report = build_coverage_bias_report(catalog, snapshot)
        if args.check:
            report = verify_committed_report(report)
        if args.require_insufficient and report["sufficiency"]["state"] != "insufficient":
            raise CoverageBiasError("current C16 corpus must remain explicitly insufficient")
        print(f"coverageReportSha256={canonical_sha256(report)}")
        print(f"sufficiency={report['sufficiency']['state']}")
        print(f"gapCodes={','.join(report['gapCodes'])}")
        print(f"coverageReportJson={canonical_json(report)}")
    except (OSError, ValueError, KeyError) as error:
        print(f"ERROR: Stage 1C C16 coverage/bias evaluation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
