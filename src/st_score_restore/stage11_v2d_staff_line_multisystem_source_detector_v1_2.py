"""Stage 11 V2d v1.2 source-only multi-system staff-line detector.

Development-only. V1/v1.1 remain immutable. V1.2 preserves the frozen v1.1
source-only detector and adds bounded deterministic recovery from source pixels and
source-derived parent geometry only. It never loads teacher coordinates, restored
outputs, held-out data, training state, page identities, or page-specific rules.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np

from . import stage11_v2d_staff_line_multisystem_source_detector_v1_1 as parent
from ._stage11_v2d_staff_line_multisystem_source_detector_v1_2_template import DetectorConfig, RecoveryConfigError, _RecoveryCandidate
from ._stage11_v2d_staff_line_multisystem_source_detector_v1_2_secondary import _recovery_candidates

DETECTOR_VERSION = "stage11-v2d-staff-multisystem-source.v1.2"
RAW_ARTIFACT_SCHEMA_VERSION = "stage11.v2d.staff-line-multisystem-source-raw.v1.2"
PARENT_DETECTOR_VERSION = parent.DETECTOR_VERSION
StaffLineDetection = parent.StaffLineDetection
StaffSystemDetection = parent.StaffSystemDetection


StaffLineMultiSystemDetectorV12Error = RecoveryConfigError

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StaffLineMultiSystemDetectorV12Error(message)


def _candidate_to_detection(candidate: _RecoveryCandidate, *, image_height: int) -> StaffSystemDetection:
    lines = []
    for line_index, y in enumerate(candidate.ys, start=1):
        yi = int(round(y))
        lines.append(StaffLineDetection(line_index, float(y), (candidate.x1, candidate.x2), ((candidate.x1, yi, candidate.x2, yi),)))
    y1 = max(0, int(math.floor(candidate.ys[0] - max(2.0, candidate.spacing * 0.35))))
    y2 = min(image_height, int(math.ceil(candidate.ys[-1] + max(2.0, candidate.spacing * 0.35))) + 1)
    confidence = max(0.50, min(0.97, 0.50 + 0.47 * candidate.score))
    return StaffSystemDetection(0, (candidate.x1, y1, candidate.x2, y2), float(candidate.spacing), float(confidence), tuple(lines), candidate.provenance, DETECTOR_VERSION)


def detect_staff_systems_with_diagnostics(image: np.ndarray, *, config: DetectorConfig | None = None) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    cfg = config or DetectorConfig()
    cfg.validate()
    gray = parent._as_grayscale(image)
    height, _width = gray.shape
    parent_detections, parent_diagnostics = parent.detect_staff_systems_with_diagnostics(gray)
    recovery, recovery_diagnostics = _recovery_candidates(gray, parent_detections, cfg)
    detections: list[StaffSystemDetection] = [
        StaffSystemDetection(0, item.bbox, item.staff_spacing, item.confidence, item.lines,
                             f"source-only:v1.2-parent-preserved:{item.provenance}", DETECTOR_VERSION)
        for item in parent_detections
    ]
    detections.extend(_candidate_to_detection(item, image_height=height) for item in recovery)
    detections.sort(key=lambda item: (item.lines[0].center_y, item.bbox[0], item.staff_spacing, item.provenance))
    reindexed = []
    for index, item in enumerate(detections, start=1):
        lines = tuple(StaffLineDetection(i, line.center_y, line.x_extent, line.segments) for i, line in enumerate(item.lines, start=1))
        reindexed.append(StaffSystemDetection(index, item.bbox, item.staff_spacing, item.confidence, lines, item.provenance, DETECTOR_VERSION))
    diagnostics = {
        "sourceOnly": True,
        "teacherCoordinatesUsed": False,
        "restoredOutputsUsed": False,
        "heldOutAccessed": False,
        "trainingUsed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "parentSystemCount": len(parent_detections),
        "parentDiagnostics": parent_diagnostics,
        "recovery": recovery_diagnostics,
        "finalSystemCount": len(reindexed),
    }
    return reindexed, diagnostics


def detect_staff_systems(image: np.ndarray, *, config: DetectorConfig | None = None) -> list[StaffSystemDetection]:
    return detect_staff_systems_with_diagnostics(image, config=config)[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def freeze_source_folder(source_dir: Path, output_path: Path, *, config: DetectorConfig | None = None,
                         expected_source_sha256: Mapping[str, str] | None = None) -> dict[str, Any]:
    cfg = config or DetectorConfig()
    cfg.validate()
    source_dir, output_path = Path(source_dir), Path(output_path)
    paths = sorted(source_dir.glob("*.png"), key=lambda path: path.name)
    _require(bool(paths), "source folder has no PNG pages")
    pages, identity_matches = [], 0
    for path in paths:
        source_sha = sha256_file(path)
        if expected_source_sha256 is not None:
            _require(path.name in expected_source_sha256, f"unregistered source page: {path.name}")
            _require(source_sha == expected_source_sha256[path.name], f"source SHA-256 mismatch: {path.name}")
            identity_matches += 1
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        _require(image is not None, f"unreadable source page: {path.name}")
        detections, diagnostics = detect_staff_systems_with_diagnostics(image, config=cfg)
        height, width = image.shape
        pages.append({
            "pageId": path.stem, "sourceFileName": path.name, "sourceSha256": source_sha,
            "width": int(width), "height": int(height), "systemCount": len(detections),
            "systems": [item.as_dict() for item in detections],
            "abstentionReason": None if detections else "NO_SOURCE_SUPPORTED_STANDARD_FIVE_LINE_STAFF_SYSTEM",
            "diagnostics": diagnostics,
        })
    if expected_source_sha256 is not None:
        _require(len(paths) == len(expected_source_sha256), "source page count differs from frozen identity manifest")
    helper_template = Path(__file__).with_name("_stage11_v2d_staff_line_multisystem_source_detector_v1_2_template.py")
    helper_secondary = Path(__file__).with_name("_stage11_v2d_staff_line_multisystem_source_detector_v1_2_secondary.py")
    payload: dict[str, Any] = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "parentV1AndV1_1Immutable": True,
        "developmentOnly": True,
        "qualificationEvidence": False,
        "sourceOnly": True,
        "teacherArtifactLoadedDuringInference": False,
        "teacherCoordinatesUsedDuringInference": False,
        "restoredOutputsLoadedDuringInference": False,
        "heldOutAccessed": False,
        "trainingOrFineTuningPerformed": False,
        "pageSpecificRulesUsed": False,
        "detectorSourceSha256": sha256_file(Path(__file__)),
        "recoveryHelperSourceSha256": {"template": sha256_file(helper_template), "secondary": sha256_file(helper_secondary)},
        "parentDetectorSourceSha256": sha256_file(Path(parent.__file__)),
        "config": asdict(cfg),
        "sourceIdentityExpectedCount": len(expected_source_sha256) if expected_source_sha256 is not None else None,
        "sourceIdentityMatchedCount": identity_matches if expected_source_sha256 is not None else None,
        "pageCount": len(pages),
        "pages": pages,
        "claimBoundary": {
            "detectorQualified": False, "semanticPreservationEstablished": False,
            "overallStage11PassAuthorized": False, "restoredImageTopologyComparisonAuthorized": False,
            "productionReady": False, "productionPromotionAuthorized": False, "stage12EntryAuthorized": False,
        },
    }
    canonical = _canonical_bytes(payload)
    artifact_sha = hashlib.sha256(canonical).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical)
    Path(str(output_path) + ".sha256").write_text(artifact_sha + "\n", encoding="utf-8")
    return {"artifactSha256": artifact_sha, "artifact": payload}


__all__ = [
    "DETECTOR_VERSION", "RAW_ARTIFACT_SCHEMA_VERSION", "DetectorConfig", "StaffLineDetection",
    "StaffSystemDetection", "StaffLineMultiSystemDetectorV12Error", "detect_staff_systems",
    "detect_staff_systems_with_diagnostics", "freeze_source_folder", "sha256_file",
]
