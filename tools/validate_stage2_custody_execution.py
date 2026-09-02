from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np

from st_score_restore.dataset_catalog_validation import validate_dataset_catalog
from st_score_restore.stage2_custody_execution import (
    APPROVED_CUSTODY_ENVIRONMENT,
    CONTRACT_VERSION,
    CustodyExecutionError,
    run_authorized_quality_execution,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"

EXPECTED_ITEMS = {
    "dataset.item.imslp799143-beethoven-op48-no3.v1": ("development", "quality_evaluation"),
    "dataset.item.wikimedia-guitar-technical-exercise-no1.v1": ("development", "quality_evaluation"),
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1": ("development", "quality_evaluation"),
    "dataset.item.imslp82860-chopin-op69.v2": ("held_out", "held_out_evaluation"),
    "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1": ("held_out", "held_out_evaluation"),
}
C17A = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
C17D = "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1"


def _encode_png() -> bytes:
    image = np.full((800, 1000), 245, dtype=np.uint8)
    for start in (180, 430):
        for offset in range(5):
            y = start + offset * 12
            cv2.line(image, (80, y), (920, y), 0, 2)
    cv2.rectangle(image, (30, 30), (969, 769), 80, 3)
    ok, payload = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("validator PNG encoding failed")
    return bytes(payload)


def _encode_jpeg() -> bytes:
    image = np.full((800, 1000), 245, dtype=np.uint8)
    for start in (180, 430):
        for offset in range(5):
            y = start + offset * 12
            cv2.line(image, (80, y), (920, y), 0, 2)
    ok, payload = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise RuntimeError("validator JPEG encoding failed")
    return bytes(payload)


def _synthetic_catalog(catalog: dict, item_id: str, raw: bytes) -> dict:
    source = next(item for item in catalog["items"] if item["datasetItemId"] == item_id)
    item = deepcopy(source)
    item["artifact"]["sha256"] = hashlib.sha256(raw).hexdigest()
    item["artifact"]["byteSize"] = len(raw)
    result = deepcopy(catalog)
    result["items"] = [item]
    return result


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    validate_dataset_catalog(catalog)
    by_id = {item["datasetItemId"]: item for item in catalog["items"]}

    require(set(by_id) == set(EXPECTED_ITEMS), "expanded-v2 Stage 2 execution item set drifted")
    for item_id, (split, purpose) in EXPECTED_ITEMS.items():
        item = by_id.get(item_id)
        if item is None:
            continue
        require(item["split"] == split, f"{item_id} split drifted")
        require(
            item["permissions"][purpose]["status"] == "granted",
            f"{item_id} Stage 2 purpose permission is not granted",
        )
        require(
            item["artifact"]["state"] == "external_available",
            f"{item_id} is not an admitted external artifact",
        )
        require(
            item["review"]["status"] == "approved",
            f"{item_id} dataset review is not approved",
        )
        require(
            item["revocation"]["status"] == "not_revoked",
            f"{item_id} is revoked or pending deletion",
        )
        require(
            item["assertions"]["originalBytesInGit"] is False,
            f"{item_id} unexpectedly claims original bytes in Git",
        )

    c17d = by_id.get(C17D)
    if c17d is not None:
        restrictions = c17d["permissions"]["held_out_evaluation"]["restrictions"]
        export = next(
            (item for item in restrictions if item["type"] == "external_export"),
            None,
        )
        require(
            export is not None and export["allowed"] is False,
            "C17D held-out external_export=false restriction drifted",
        )
        require(
            c17d["retention"]["storageClass"] == "managed_restricted",
            "C17D managed_restricted custody drifted",
        )

    png = _encode_png()
    development = run_authorized_quality_execution(
        _synthetic_catalog(catalog, C17A, png),
        dataset_item_id=C17A,
        data=png,
        purpose="quality_evaluation",
        execution_date="2026-09-02",
        environment=APPROVED_CUSTODY_ENVIRONMENT,
    )
    receipt = development.to_public_dict()
    require(receipt.get("status") == "analyzed", "development execution contract did not analyze")
    require(
        receipt.get("assertions", {}).get("exactDigestMatched") is True,
        "development execution did not bind exact SHA-256",
    )
    require(
        receipt.get("assertions", {}).get("purposePermissionValid") is True,
        "development execution did not bind purpose permission",
    )
    require("metrics" not in receipt and "findings" not in receipt, "public receipt leaked metrics/findings")
    require(
        receipt.get("reportHandling", {}).get("detailedReportExported") is False,
        "public receipt unexpectedly exports detailed report",
    )

    jpeg = _encode_jpeg()
    held_out = run_authorized_quality_execution(
        _synthetic_catalog(catalog, C17D, jpeg),
        dataset_item_id=C17D,
        data=jpeg,
        purpose="held_out_evaluation",
        execution_date="2026-09-02",
        environment=APPROVED_CUSTODY_ENVIRONMENT,
    )
    held_receipt = held_out.to_public_dict()
    require(held_receipt.get("split") == "held_out", "held-out execution split drifted")
    require(
        held_receipt.get("reportHandling", {}).get("externalExportState") == "explicitly_blocked",
        "held-out restricted export boundary drifted",
    )
    require(
        held_receipt.get("assertions", {}).get("heldOutThresholdTuningUsed") is False,
        "held-out execution unexpectedly claims threshold tuning",
    )
    require(
        held_receipt.get("assertions", {}).get("trainingAuthorized") is False,
        "Stage 2 execution unexpectedly authorizes training",
    )

    bad = bytearray(png)
    bad[-1] ^= 1
    try:
        run_authorized_quality_execution(
            _synthetic_catalog(catalog, C17A, png),
            dataset_item_id=C17A,
            data=bytes(bad),
            purpose="quality_evaluation",
            execution_date="2026-09-02",
        )
        failures.append("exact-byte mismatch did not fail closed")
    except CustodyExecutionError as exc:
        require(exc.code == "exact_sha256_mismatch", "exact-byte mismatch returned wrong error code")

    if failures:
        print("Stage 2 approved-custody execution validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 2 approved-custody execution validation: PASS")
    print(f"- contract version: {CONTRACT_VERSION}")
    print(f"- accepted corpus metadata items: {len(EXPECTED_ITEMS)}")
    print("- exact digest/byte-size gate: enforced")
    print("- development/held-out purpose split: enforced")
    print("- C17D external export: blocked")
    print("- public receipt: metrics/findings redacted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
