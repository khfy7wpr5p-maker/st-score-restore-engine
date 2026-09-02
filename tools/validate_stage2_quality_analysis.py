from __future__ import annotations

import hashlib
import sys

import cv2
import numpy as np

from st_score_restore.quality_analysis import (
    ANALYZER_VERSION,
    CALIBRATION_STATE,
    FINDING_TYPES,
    analyze_quality_bytes,
)


def _encode_png(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("validator PNG encoding failed")
    return bytes(payload)


def _staff_page() -> np.ndarray:
    image = np.full((800, 1000), 245, dtype=np.uint8)
    for start in (180, 430):
        for offset in range(5):
            y = start + offset * 12
            cv2.line(image, (80, y), (920, y), 0, 2)
    cv2.rectangle(image, (30, 30), (969, 769), 80, 3)
    return image


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    raw = _encode_png(_staff_page())
    first = analyze_quality_bytes(raw, source_name="stage2-validator.png")
    second = analyze_quality_bytes(raw, source_name="stage2-validator.png")

    require(first == second, "quality analysis is not deterministic for identical bytes")
    require(first.get("status") == "analyzed", "raster analysis did not complete")
    require(
        first.get("analyzerVersion") == ANALYZER_VERSION,
        "analyzer version binding drifted",
    )
    require(
        first.get("sourceDigest", {}).get("value") == hashlib.sha256(raw).hexdigest(),
        "quality report is not bound to the exact source SHA-256",
    )
    require(
        first.get("sourceReturnedUnmodified") is True,
        "quality analysis does not preserve immutable source bytes",
    )
    calibration = first.get("calibration", {})
    require(
        calibration.get("state") == CALIBRATION_STATE,
        "Stage 2 calibration boundary drifted",
    )
    require(
        calibration.get("heldOutThresholdTuningUsed") is False,
        "Stage 2 unexpectedly claims held-out threshold tuning",
    )
    finding_types = {item.get("type") for item in first.get("findings", [])}
    require(
        finding_types == set(FINDING_TYPES),
        f"Stage 2 finding taxonomy drifted: {sorted(finding_types)}",
    )
    assertions = first.get("assertions", {})
    for key in (
        "sourceBytesModified",
        "generativeOperationsUsed",
        "symbolCompletionUsed",
        "omrPerformed",
        "musicalCorrectnessAssessed",
        "restorationEffectivenessAssessed",
        "trainingPermissionInferred",
        "calibrationPermissionInferred",
    ):
        require(assertions.get(key) is False, f"unsafe/unsupported Stage 2 assertion: {key}")

    visibility = first.get("metrics", {}).get("visibility", {})
    require(
        visibility.get("staffLikeGroupCount", 0) >= 1,
        "synthetic staff geometry was not detected",
    )
    require(
        visibility.get("evidenceOnly") is True,
        "staff/TAB visibility is not marked evidence-only",
    )
    compression = first.get("metrics", {}).get("compression", {})
    require(
        compression.get("applicable") is False,
        "PNG unexpectedly received JPEG compression scoring",
    )

    digital_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Page /Font << >> >> endobj\n"
        b"%%EOF\n"
    )
    vector_report = analyze_quality_bytes(digital_pdf, source_name="vector.pdf")
    require(
        vector_report.get("status") == "not_applicable_vector_pdf",
        "digital PDF was not preserved at the Stage 2 vector boundary",
    )
    require(
        vector_report.get("sourceReturnedUnmodified") is True,
        "digital PDF source identity was not preserved",
    )

    if failures:
        print("Stage 2 quality-analysis validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 2 quality-analysis validation: PASS")
    print(f"- analyzer version: {ANALYZER_VERSION}")
    print(f"- finding taxonomy count: {len(FINDING_TYPES)}")
    print("- deterministic exact-source binding: PASS")
    print("- calibration boundary: uncalibrated engineering defaults")
    print("- digital PDF vector boundary: preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
