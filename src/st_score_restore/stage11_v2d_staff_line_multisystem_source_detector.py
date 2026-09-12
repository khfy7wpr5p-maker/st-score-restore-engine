"""Stage 11 V2d source-only multi-system staff-line detector.

This module is development-only and intentionally independent of teacher coordinates,
restored outputs, held-out data, training, and page-specific hints.  It replaces none of
the frozen V2c evidence; the rejected ``stage11-v2c-line-system.v1`` detector remains
immutable historical evidence.

The detector emits source-supported horizontal segments grouped into standard five-line
staff systems.  It does not qualify ``staff_line`` by itself and cannot authorize any
Stage 11/12 or production transition.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np

DETECTOR_VERSION = "stage11-v2d-staff-multisystem-source.v1"
RAW_ARTIFACT_SCHEMA_VERSION = "stage11.v2d.staff-line-multisystem-source-raw.v1"


class StaffLineMultiSystemDetectorError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StaffLineMultiSystemDetectorError(message)


@dataclass(frozen=True)
class DetectorConfig:
    min_spacing_px: float = 3.0
    max_spacing_px: float = 72.0
    spacing_tolerance_fraction: float = 0.20
    min_segment_width_fraction: float = 0.055
    min_common_extent_fraction: float = 0.045
    horizontal_kernel_fraction: float = 0.035
    max_horizontal_kernel_px: int = 151
    row_merge_tolerance_px: float = 2.5
    six_line_rejection_tolerance_fraction: float = 0.22

    def validate(self) -> None:
        _require(1.0 <= self.min_spacing_px < self.max_spacing_px, "invalid staff spacing bounds")
        _require(0.05 <= self.spacing_tolerance_fraction <= 0.40, "invalid spacing tolerance")
        _require(0.01 <= self.min_segment_width_fraction <= 0.50, "invalid segment width fraction")
        _require(0.01 <= self.min_common_extent_fraction <= 0.50, "invalid common extent fraction")
        _require(0.005 <= self.horizontal_kernel_fraction <= 0.20, "invalid horizontal kernel fraction")
        _require(15 <= self.max_horizontal_kernel_px <= 511, "invalid horizontal kernel cap")
        _require(0.5 <= self.row_merge_tolerance_px <= 8.0, "invalid row merge tolerance")
        _require(0.05 <= self.six_line_rejection_tolerance_fraction <= 0.50, "invalid six-line tolerance")


@dataclass(frozen=True)
class _Segment:
    x1: int
    x2: int
    y: float
    height: int
    width: int
    pixel_count: int


@dataclass(frozen=True)
class _Row:
    row_id: int
    y: float
    segments: tuple[_Segment, ...]
    x1: int
    x2: int
    supported_width: int


@dataclass(frozen=True)
class StaffLineDetection:
    line_index: int
    center_y: float
    x_extent: tuple[int, int]
    segments: tuple[tuple[int, int, int, int], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "lineIndex": self.line_index,
            "centerY": self.center_y,
            "xExtent": list(self.x_extent),
            "segments": [list(item) for item in self.segments],
        }


@dataclass(frozen=True)
class StaffSystemDetection:
    system_index: int
    bbox: tuple[int, int, int, int]
    staff_spacing: float
    confidence: float
    lines: tuple[StaffLineDetection, ...]
    provenance: str = "source-only:horizontal-segment-regularity"
    detector_version: str = DETECTOR_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "systemIndex": self.system_index,
            "bbox": list(self.bbox),
            "staffSpacing": self.staff_spacing,
            "confidence": self.confidence,
            "lineCount": 5,
            "lines": [line.as_dict() for line in self.lines],
            "provenance": self.provenance,
            "detectorVersion": self.detector_version,
        }


def _as_grayscale(image: np.ndarray) -> np.ndarray:
    _require(isinstance(image, np.ndarray), "image must be a numpy array")
    _require(image.size > 0, "image must be non-empty")
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.ndim == 3 and image.shape[2] == 4:
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    else:
        raise StaffLineMultiSystemDetectorError("image must be grayscale, BGR, or BGRA")
    if gray.dtype != np.uint8:
        if np.issubdtype(gray.dtype, np.floating):
            _require(bool(np.isfinite(gray).all()), "image contains non-finite pixels")
        gray = np.clip(gray, 0, 255).astype(np.uint8)
    return gray


def _binary_horizontal_support(gray: np.ndarray, config: DetectorConfig) -> np.ndarray:
    height, width = gray.shape
    _require(height >= 16 and width >= 32, "image too small for staff detection")
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, ink = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    kernel_len = int(round(width * config.horizontal_kernel_fraction))
    kernel_len = max(15, min(config.max_horizontal_kernel_px, kernel_len))
    if kernel_len % 2 == 0:
        kernel_len += 1
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
    support = cv2.morphologyEx(ink, cv2.MORPH_OPEN, horizontal_kernel)
    close_len = max(3, kernel_len // 5)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_len, 1))
    support = cv2.morphologyEx(support, cv2.MORPH_CLOSE, close_kernel)
    return support


def _extract_segments(support: np.ndarray, config: DetectorConfig) -> list[_Segment]:
    height, width = support.shape
    minimum_width = max(12, int(round(width * config.min_segment_width_fraction)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(support, 8)
    segments: list[_Segment] = []
    for component in range(1, count):
        x, y, w, h, area = (int(v) for v in stats[component])
        if w < minimum_width:
            continue
        if h > max(10, int(round(config.max_spacing_px * 0.35))):
            continue
        center_y = float(centroids[component][1])
        if not math.isfinite(center_y):
            continue
        segments.append(
            _Segment(
                x1=x,
                x2=x + w,
                y=center_y,
                height=h,
                width=w,
                pixel_count=area,
            )
        )
    segments.sort(key=lambda item: (item.y, item.x1, item.x2))
    return segments


def _union_width(intervals: Iterable[tuple[int, int]]) -> int:
    ordered = sorted((int(a), int(b)) for a, b in intervals if b > a)
    if not ordered:
        return 0
    total = 0
    start, end = ordered[0]
    for left, right in ordered[1:]:
        if left <= end:
            end = max(end, right)
        else:
            total += end - start
            start, end = left, right
    return total + end - start


def _merge_rows(segments: list[_Segment], config: DetectorConfig) -> list[_Row]:
    if not segments:
        return []
    clusters: list[list[_Segment]] = []
    for segment in segments:
        if not clusters:
            clusters.append([segment])
            continue
        current_y = float(np.average(
            [item.y for item in clusters[-1]],
            weights=[max(1, item.pixel_count) for item in clusters[-1]],
        ))
        if abs(segment.y - current_y) <= config.row_merge_tolerance_px:
            clusters[-1].append(segment)
        else:
            clusters.append([segment])

    rows: list[_Row] = []
    for row_id, cluster in enumerate(clusters):
        weighted_y = float(np.average(
            [item.y for item in cluster],
            weights=[max(1, item.pixel_count) for item in cluster],
        ))
        x1 = min(item.x1 for item in cluster)
        x2 = max(item.x2 for item in cluster)
        supported_width = _union_width((item.x1, item.x2) for item in cluster)
        rows.append(
            _Row(
                row_id=row_id,
                y=weighted_y,
                segments=tuple(cluster),
                x1=x1,
                x2=x2,
                supported_width=supported_width,
            )
        )
    return rows


def _x_overlap(a: _Row, b: _Row) -> int:
    return max(0, min(a.x2, b.x2) - max(a.x1, b.x1))


def _nearest_row(rows: list[_Row], target_y: float, tolerance: float, used: set[int]) -> _Row | None:
    candidates = [row for row in rows if row.row_id not in used and abs(row.y - target_y) <= tolerance]
    if not candidates:
        return None
    return min(candidates, key=lambda row: (abs(row.y - target_y), -row.supported_width, row.row_id))


def _looks_like_six_line_system(rows: list[_Row], selected: list[_Row], spacing: float, config: DetectorConfig) -> bool:
    tolerance = max(1.5, spacing * config.six_line_rejection_tolerance_fraction)
    first, last = selected[0], selected[-1]
    selected_span = max(1, min(row.x2 for row in selected) - max(row.x1 for row in selected))
    for target in (first.y - spacing, last.y + spacing):
        for row in rows:
            if row in selected or abs(row.y - target) > tolerance:
                continue
            overlap = min(_x_overlap(row, item) for item in selected)
            if overlap >= max(8, int(selected_span * 0.45)):
                return True
    return False


def _candidate_hypotheses(rows: list[_Row], width: int, config: DetectorConfig) -> list[tuple[float, list[_Row], float]]:
    hypotheses: list[tuple[float, list[_Row], float]] = []
    minimum_common = max(16, int(round(width * config.min_common_extent_fraction)))
    for first_index, first in enumerate(rows):
        for second in rows[first_index + 1 :]:
            spacing = second.y - first.y
            if spacing < config.min_spacing_px:
                continue
            if spacing > config.max_spacing_px:
                break
            tolerance = max(1.5, spacing * config.spacing_tolerance_fraction)
            selected = [first, second]
            used = {first.row_id, second.row_id}
            for line_index in range(2, 5):
                row = _nearest_row(rows, first.y + spacing * line_index, tolerance, used)
                if row is None:
                    selected = []
                    break
                selected.append(row)
                used.add(row.row_id)
            if len(selected) != 5:
                continue
            selected.sort(key=lambda item: item.y)
            spacings = np.diff(np.asarray([row.y for row in selected], dtype=np.float64))
            median_spacing = float(np.median(spacings))
            if not (config.min_spacing_px <= median_spacing <= config.max_spacing_px):
                continue
            if float(np.max(np.abs(spacings - median_spacing))) > max(
                1.5, median_spacing * config.spacing_tolerance_fraction
            ):
                continue
            common_x1 = max(row.x1 for row in selected)
            common_x2 = min(row.x2 for row in selected)
            common_width = max(0, common_x2 - common_x1)
            if common_width < minimum_common:
                continue
            if _looks_like_six_line_system(rows, selected, median_spacing, config):
                continue
            regularity = 1.0 - min(
                1.0,
                float(np.mean(np.abs(spacings - median_spacing))) / max(median_spacing, 1.0),
            )
            support_fraction = min(
                1.0,
                float(np.mean([row.supported_width / max(width, 1) for row in selected])) / 0.60,
            )
            common_fraction = min(1.0, common_width / max(width * 0.35, 1.0))
            score = 0.45 * regularity + 0.35 * support_fraction + 0.20 * common_fraction
            hypotheses.append((score, selected, median_spacing))
    hypotheses.sort(key=lambda item: (-item[0], item[1][0].y, item[1][0].x1))
    return hypotheses


def _deduplicate_hypotheses(
    hypotheses: list[tuple[float, list[_Row], float]]
) -> list[tuple[float, list[_Row], float]]:
    kept: list[tuple[float, list[_Row], float]] = []
    used_row_sets: list[set[int]] = []
    for hypothesis in hypotheses:
        row_set = {row.row_id for row in hypothesis[1]}
        if any(len(row_set & existing) >= 3 for existing in used_row_sets):
            continue
        kept.append(hypothesis)
        used_row_sets.append(row_set)
    kept.sort(key=lambda item: (item[1][0].y, item[1][0].x1))
    return kept


def detect_staff_systems(
    image: np.ndarray,
    *,
    config: DetectorConfig | None = None,
) -> list[StaffSystemDetection]:
    """Return all source-supported standard five-line staff systems on a page.

    The function has no page identifier argument and no teacher/restored input channel.
    Six equally spaced line systems are rejected to avoid silently treating TAB as staff.
    """
    cfg = config or DetectorConfig()
    cfg.validate()
    gray = _as_grayscale(image)
    height, width = gray.shape
    support = _binary_horizontal_support(gray, cfg)
    segments = _extract_segments(support, cfg)
    rows = _merge_rows(segments, cfg)
    hypotheses = _deduplicate_hypotheses(_candidate_hypotheses(rows, width, cfg))

    detections: list[StaffSystemDetection] = []
    for system_index, (score, selected, spacing) in enumerate(hypotheses, start=1):
        lines: list[StaffLineDetection] = []
        for line_index, row in enumerate(selected, start=1):
            raw_segments = tuple(
                (segment.x1, int(round(row.y)), segment.x2, int(round(row.y)))
                for segment in row.segments
            )
            lines.append(
                StaffLineDetection(
                    line_index=line_index,
                    center_y=float(row.y),
                    x_extent=(row.x1, row.x2),
                    segments=raw_segments,
                )
            )
        x1 = min(line.x_extent[0] for line in lines)
        x2 = max(line.x_extent[1] for line in lines)
        y1 = max(0, int(math.floor(lines[0].center_y - max(2.0, spacing * 0.35))))
        y2 = min(height, int(math.ceil(lines[-1].center_y + max(2.0, spacing * 0.35))) + 1)
        confidence = max(0.50, min(0.99, 0.50 + 0.49 * float(score)))
        detections.append(
            StaffSystemDetection(
                system_index=system_index,
                bbox=(int(x1), int(y1), int(x2), int(y2)),
                staff_spacing=float(spacing),
                confidence=confidence,
                lines=tuple(lines),
            )
        )
    return detections


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def freeze_source_folder(
    source_dir: Path,
    output_path: Path,
    *,
    config: DetectorConfig | None = None,
) -> dict[str, Any]:
    """Run and freeze source-only detections without loading any teacher artifact."""
    cfg = config or DetectorConfig()
    cfg.validate()
    source_dir = Path(source_dir)
    output_path = Path(output_path)
    _require(source_dir.is_dir(), "source directory does not exist")
    pages = sorted(path for path in source_dir.glob("*.png") if path.is_file())
    _require(bool(pages), "no source PNG pages found")

    page_records: list[dict[str, Any]] = []
    for path in pages:
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        _require(image is not None and image.ndim == 2, f"failed to decode source page: {path.name}")
        detections = detect_staff_systems(image, config=cfg)
        page_records.append(
            {
                "pageId": path.stem,
                "sourceFileName": path.name,
                "sourceSha256": sha256_file(path),
                "width": int(image.shape[1]),
                "height": int(image.shape[0]),
                "systemCount": len(detections),
                "systems": [item.as_dict() for item in detections],
                "abstentionReason": None if detections else "no_supported_five_line_system",
            }
        )

    artifact = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "developmentOnly": True,
        "qualificationEvidence": False,
        "sourceOnly": True,
        "teacherArtifactLoadedDuringInference": False,
        "restoredOutputsLoadedDuringInference": False,
        "heldOutAccessed": False,
        "trainingOrFineTuningPerformed": False,
        "pageSpecificRulesUsed": False,
        "config": asdict(cfg),
        "pageCount": len(page_records),
        "pages": page_records,
        "claimBoundary": {
            "detectorQualified": False,
            "semanticPreservationEstablished": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
    }
    digest = hashlib.sha256(_canonical_json_bytes(artifact)).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(str(output_path) + ".tmp")
    temp.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(output_path)
    Path(str(output_path) + ".sha256").write_text(digest + "\n", encoding="utf-8")
    return {"artifact": artifact, "artifactSha256": digest, "outputPath": str(output_path)}


def _main() -> None:
    parser = argparse.ArgumentParser(description="Freeze Stage 11 V2d source-only multi-system staff detections")
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = freeze_source_folder(args.source_dir, args.output)
    print(f"detectorVersion={DETECTOR_VERSION}")
    print(f"pageCount={result['artifact']['pageCount']}")
    print(f"artifactSha256={result['artifactSha256']}")
    print(f"output={result['outputPath']}")


if __name__ == "__main__":
    _main()
