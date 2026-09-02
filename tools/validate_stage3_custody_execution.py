#!/usr/bin/env python3
"""Validate the Stage 3 purpose/custody PDF execution boundary."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np

from st_score_restore.dataset_contract_constants import SPLIT_PURPOSES
from st_score_restore.stage3_custody_execution import (
    Stage3CustodyExecutionError,
    run_authorized_pdf_pipeline_execution,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
BEETHOVEN = "dataset.item.imslp799143-beethoven-op48-no3.v1"
BARLEY = "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"
CHOPIN = "dataset.item.imslp82860-chopin-op69.v2"
REAL_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _jpeg_bytes() -> bytes:
    image = np.full((72, 56, 3), 245, dtype=np.uint8)
    for y in range(12, 65, 9):
        cv2.line(image, (4, y), (51, y), (20, 20, 20), 1)
    ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    if not ok:
        raise RuntimeError("validator JPEG encoding failed")
    return bytes(encoded)


def _stream(payload: bytes, extra: bytes = b"") -> bytes:
    suffix = b" " + extra if extra else b""
    return (
        b"<< /Length " + str(len(payload)).encode("ascii") + suffix
        + b" >>\nstream\n" + payload + b"\nendstream"
    )


def _assemble_pdf(objects: list[bytes]) -> bytes:
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(str(index).encode("ascii") + b" 0 obj\n" + body + b"\nendobj\n")
    xref_offset = sum(len(chunk) for chunk in chunks)
    xref = [b"xref\n0 " + str(len(objects) + 1).encode("ascii") + b"\n"]
    xref.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        b"trailer\n<< /Size " + str(len(objects) + 1).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n" + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return b"".join(chunks + xref + [trailer])


def _raster_pdf() -> bytes:
    jpeg = _jpeg_bytes()
    return _assemble_pdf([
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 160 220] /Resources << /XObject << /Im0 4 0 R >> >> /Contents 5 0 R >>",
        _stream(
            jpeg,
            b"/Type /XObject /Subtype /Image /Width 56 /Height 72 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode",
        ),
        _stream(b"q\n160 0 0 220 0 0 cm\n/Im0 Do\nQ"),
    ])


def _catalog_for(item_id: str, data: bytes, *, grant_dev: bool = False) -> dict:
    catalog = _load_catalog()
    item = deepcopy(next(value for value in catalog["items"] if value["datasetItemId"] == item_id))
    digest = hashlib.sha256(data).hexdigest()
    item["artifact"]["sha256"] = digest
    item["artifact"]["byteSize"] = len(data)
    if item["privacy"]["deidentifiedArtifactSha256"] is not None:
        item["privacy"]["deidentifiedArtifactSha256"] = digest
    if grant_dev:
        item["permissions"]["pdf_pipeline_evaluation"] = {
            "status": "granted",
            "authorizationReference": "evidence:opq_11111111111111111111111111111111",
            "authorizedBy": "actor.purpose:opq_22222222222222222222222222222222",
            "authorizedOn": "2026-09-02",
            "expiresOn": None,
            "restrictions": [],
            "revokedOn": None,
            "revocationReference": None,
        }
    catalog["items"] = [item]
    return catalog


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    catalog = _load_catalog()
    items = {item["datasetItemId"]: item for item in catalog["items"]}
    for item_id in (BEETHOVEN, BARLEY, CHOPIN):
        require(item_id in items, f"accepted PDF corpus item missing: {item_id}")

    if BEETHOVEN in items:
        require(items[BEETHOVEN]["split"] == "development", "Beethoven split drifted")
        require(
            items[BEETHOVEN]["permissions"]["pdf_pipeline_evaluation"]["status"] == "not_requested",
            "Beethoven real Stage 3 purpose permission changed without a dedicated authorization slice",
        )
    if BARLEY in items:
        require(items[BARLEY]["split"] == "development", "Barley split drifted")
        require(
            items[BARLEY]["permissions"]["pdf_pipeline_evaluation"]["status"] == "not_requested",
            "Barley real Stage 3 purpose permission changed without a dedicated authorization slice",
        )
    if CHOPIN in items:
        require(items[CHOPIN]["split"] == "held_out", "Chopin split drifted")
        require(
            items[CHOPIN]["permissions"]["held_out_evaluation"]["status"] == "granted",
            "Chopin held-out evaluation permission is not granted",
        )

    require(
        "pdf_pipeline_evaluation" in SPLIT_PURPOSES["development"],
        "development split lost pdf_pipeline_evaluation purpose",
    )
    require(
        SPLIT_PURPOSES["held_out"] == frozenset({"held_out_evaluation"}),
        "held-out split purpose boundary drifted",
    )

    raw = _raster_pdf()
    dev_catalog = _catalog_for(BEETHOVEN, raw, grant_dev=True)
    dev = run_authorized_pdf_pipeline_execution(
        dev_catalog,
        dataset_item_id=BEETHOVEN,
        data=raw,
        purpose="pdf_pipeline_evaluation",
        execution_date="2026-09-02",
    ).to_public_dict()
    require(dev.get("status") == "completed", "synthetic authorized development execution failed")
    require(dev.get("pageSummary", {}).get("renderedPageCount") == 1, "synthetic development raster page did not render")
    require(dev.get("assertions", {}).get("heldOutThresholdTuningUsed") is False, "development receipt lost non-tuning assertion")
    require("pages" not in dev and "metrics" not in dev and "findings" not in dev, "public development receipt leaked detailed evidence")

    held_catalog = _catalog_for(CHOPIN, raw)
    held = run_authorized_pdf_pipeline_execution(
        held_catalog,
        dataset_item_id=CHOPIN,
        data=raw,
        purpose="held_out_evaluation",
        execution_date="2026-09-02",
    ).to_public_dict()
    require(held.get("status") == "completed", "synthetic held-out execution failed")
    require(held.get("split") == "held_out", "held-out receipt split drifted")
    require(held.get("assertions", {}).get("heldOutThresholdTuningUsed") is False, "held-out receipt claims threshold tuning")
    require(held.get("assertions", {}).get("calibrationAuthorized") is False, "held-out receipt authorizes calibration")

    try:
        run_authorized_pdf_pipeline_execution(
            _catalog_for(BEETHOVEN, raw),
            dataset_item_id=BEETHOVEN,
            data=raw,
            purpose="pdf_pipeline_evaluation",
            execution_date="2026-09-02",
        )
    except Stage3CustodyExecutionError as exc:
        require(exc.code == "purpose_permission_not_valid", f"development permission blocker changed: {exc.code}")
    else:
        failures.append("real development permission state did not fail closed")

    binary_paths = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "evidence").rglob("*")
        if path.is_file() and path.suffix.lower() in REAL_SUFFIXES
    ]
    require(not binary_paths, f"real artifact bytes found in ordinary Git evidence tree: {binary_paths}")

    if failures:
        print("Stage 3 authorized PDF execution validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 3 authorized PDF execution validation: PASS")
    print("- development purpose: pdf_pipeline_evaluation / explicit permission required")
    print("- current accepted development PDF permissions: not_requested / fail closed")
    print("- held-out purpose: held_out_evaluation / Chopin permission granted")
    print("- synthetic purpose/custody/exact-byte execution: PASS")
    print("- held-out threshold tuning: false")
    print("- real artifact bytes in ordinary Git: 0")
    print("- real Stage 3 corpus execution: not complete")
    print("- Stage 4: blocked pending Stage 3 exit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
