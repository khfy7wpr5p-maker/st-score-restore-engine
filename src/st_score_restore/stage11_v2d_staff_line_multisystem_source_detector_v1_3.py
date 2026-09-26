"""Stage 11 V2d v1.3 source-only staff-line false-positive suppression candidate.

Development-only. V1.2 remains immutable. V1.3 deterministically post-filters the
frozen v1.2 source-only detector using page-local staff-spacing consensus derived
only from v1.2 source-supported predictions. It never loads teacher coordinates,
restored outputs, held-out data, training state, page identities, filenames, or
source-family-specific rules.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from . import stage11_v2d_staff_line_multisystem_source_detector_v1_2 as parent

DETECTOR_VERSION = "stage11-v2d-staff-multisystem-source.v1.3"
RAW_ARTIFACT_SCHEMA_VERSION = "stage11.v2d.staff-line-multisystem-source-raw.v1.3"
PARENT_DETECTOR_VERSION = parent.DETECTOR_VERSION
ParentDetectorConfig = parent.DetectorConfig
StaffLineDetection = parent.StaffLineDetection
StaffSystemDetection = parent.StaffSystemDetection

_ANCHOR_PROVENANCE = frozenset({
    "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology",
    "source-only:v1.2-parent-anchored-morph-ridge",
})


class StaffLineMultiSystemDetectorV13Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StaffLineMultiSystemDetectorV13Error(message)


@dataclass(frozen=True)
class SpacingConsensusConfig:
    """Bounded source-only post-filter configuration for weak v1.2 candidates."""

    min_anchor_systems: int = 2
    min_fallback_systems: int = 2
    weak_spacing_ratio_min: float = 0.82
    weak_spacing_ratio_max: float = 1.18

    def validate(self) -> None:
        _require(2 <= self.min_anchor_systems <= 32, "invalid minimum anchor count")
        _require(2 <= self.min_fallback_systems <= 32, "invalid minimum fallback count")
        _require(0.50 <= self.weak_spacing_ratio_min < 1.0, "invalid lower spacing ratio")
        _require(1.0 < self.weak_spacing_ratio_max <= 1.50, "invalid upper spacing ratio")
        _require(self.weak_spacing_ratio_min < self.weak_spacing_ratio_max, "invalid spacing ratio interval")


def _is_anchor_provenance(provenance: str) -> bool:
    return provenance in _ANCHOR_PROVENANCE


def _valid_spacing(value: Any) -> float | None:
    try:
        spacing = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(spacing) or spacing <= 0.0:
        return None
    return spacing


def _reference_spacing_from_values(
    items: Sequence[tuple[str, float]], config: SpacingConsensusConfig
) -> tuple[float | None, str, int]:
    config.validate()
    anchor_values = [spacing for provenance, spacing in items if _is_anchor_provenance(provenance)]
    if len(anchor_values) >= config.min_anchor_systems:
        return float(median(anchor_values)), "anchor-grade-median", len(anchor_values)
    all_values = [spacing for _provenance, spacing in items]
    if len(all_values) >= config.min_fallback_systems:
        return float(median(all_values)), "all-source-candidate-median", len(anchor_values)
    return None, "insufficient-source-consensus-fail-open", len(anchor_values)


def _validate_parent_detection(item: StaffSystemDetection) -> None:
    _require(len(item.lines) == 5, "parent detection must contain exactly five lines")
    ys = [float(line.center_y) for line in item.lines]
    _require(all(math.isfinite(y) for y in ys), "parent detection has non-finite line geometry")
    _require(all(a < b for a, b in zip(ys, ys[1:])), "parent detection line order is invalid")
    _require(_valid_spacing(item.staff_spacing) is not None, "parent detection spacing is invalid")


def _reindexed_detection(item: StaffSystemDetection, index: int) -> StaffSystemDetection:
    lines = tuple(
        StaffLineDetection(i, float(line.center_y), line.x_extent, line.segments)
        for i, line in enumerate(item.lines, start=1)
    )
    return StaffSystemDetection(
        index,
        item.bbox,
        float(item.staff_spacing),
        float(item.confidence),
        lines,
        item.provenance,
        DETECTOR_VERSION,
    )


def _apply_spacing_consensus(
    detections: Sequence[StaffSystemDetection], config: SpacingConsensusConfig
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    config.validate()
    ordered = list(detections)
    for item in ordered:
        _validate_parent_detection(item)
    spacing_items = [(item.provenance, float(item.staff_spacing)) for item in ordered]
    reference_spacing, reference_source, anchor_count = _reference_spacing_from_values(spacing_items, config)
    kept: list[StaffSystemDetection] = []
    suppressed_by_provenance: dict[str, int] = {}
    for item in ordered:
        if _is_anchor_provenance(item.provenance) or reference_spacing is None:
            kept.append(item)
            continue
        ratio = float(item.staff_spacing) / reference_spacing
        if config.weak_spacing_ratio_min <= ratio <= config.weak_spacing_ratio_max:
            kept.append(item)
        else:
            suppressed_by_provenance[item.provenance] = suppressed_by_provenance.get(item.provenance, 0) + 1
    reindexed = [_reindexed_detection(item, index) for index, item in enumerate(kept, start=1)]
    diagnostics = {
        "referenceSpacing": reference_spacing,
        "referenceSpacingSource": reference_source,
        "anchorSystemCount": anchor_count,
        "parentSystemCount": len(ordered),
        "suppressedWeakSystemCount": len(ordered) - len(reindexed),
        "suppressedByProvenance": dict(sorted(suppressed_by_provenance.items())),
        "finalSystemCount": len(reindexed),
        "weakSpacingRatioMin": config.weak_spacing_ratio_min,
        "weakSpacingRatioMax": config.weak_spacing_ratio_max,
    }
    return reindexed, diagnostics


def detect_staff_systems_with_diagnostics(
    image: np.ndarray,
    *,
    parent_config: ParentDetectorConfig | None = None,
    consensus_config: SpacingConsensusConfig | None = None,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    cfg = consensus_config or SpacingConsensusConfig()
    cfg.validate()
    parent_detections, parent_diagnostics = parent.detect_staff_systems_with_diagnostics(image, config=parent_config)
    detections, filter_diagnostics = _apply_spacing_consensus(parent_detections, cfg)
    diagnostics = {
        "sourceOnly": True,
        "teacherCoordinatesUsed": False,
        "restoredOutputsUsed": False,
        "heldOutAccessed": False,
        "trainingUsed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "parentDiagnostics": parent_diagnostics,
        "spacingConsensus": filter_diagnostics,
        "finalSystemCount": len(detections),
    }
    return detections, diagnostics


def detect_staff_systems(
    image: np.ndarray,
    *,
    parent_config: ParentDetectorConfig | None = None,
    consensus_config: SpacingConsensusConfig | None = None,
) -> list[StaffSystemDetection]:
    return detect_staff_systems_with_diagnostics(
        image,
        parent_config=parent_config,
        consensus_config=consensus_config,
    )[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _claim_boundary() -> dict[str, bool]:
    return {
        "detectorQualified": False,
        "semanticPreservationEstablished": False,
        "overallStage11PassAuthorized": False,
        "restoredImageTopologyComparisonAuthorized": False,
        "productionReady": False,
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
    }


def freeze_source_folder(
    source_dir: Path,
    output_path: Path,
    *,
    parent_config: ParentDetectorConfig | None = None,
    consensus_config: SpacingConsensusConfig | None = None,
    expected_source_sha256: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    p_cfg = parent_config or ParentDetectorConfig()
    p_cfg.validate()
    c_cfg = consensus_config or SpacingConsensusConfig()
    c_cfg.validate()
    source_dir, output_path = Path(source_dir), Path(output_path)
    paths = sorted(source_dir.glob("*.png"), key=lambda path: path.name)
    _require(bool(paths), "source folder has no PNG pages")
    pages: list[dict[str, Any]] = []
    identity_matches = 0
    for path in paths:
        source_sha = sha256_file(path)
        if expected_source_sha256 is not None:
            _require(path.name in expected_source_sha256, f"unregistered source page: {path.name}")
            _require(source_sha == expected_source_sha256[path.name], f"source SHA-256 mismatch: {path.name}")
            identity_matches += 1
        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        _require(image is not None, f"unreadable source page: {path.name}")
        detections, diagnostics = detect_staff_systems_with_diagnostics(
            image, parent_config=p_cfg, consensus_config=c_cfg
        )
        height, width = image.shape
        pages.append({
            "pageId": path.stem,
            "sourceFileName": path.name,
            "sourceSha256": source_sha,
            "width": int(width),
            "height": int(height),
            "systemCount": len(detections),
            "systems": [item.as_dict() for item in detections],
            "abstentionReason": None if detections else "NO_SOURCE_SUPPORTED_STANDARD_FIVE_LINE_STAFF_SYSTEM",
            "diagnostics": diagnostics,
        })
    if expected_source_sha256 is not None:
        _require(len(paths) == len(expected_source_sha256), "source page count differs from frozen identity manifest")
    payload: dict[str, Any] = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "developmentOnly": True,
        "qualificationEvidence": False,
        "sourceOnly": True,
        "teacherArtifactLoadedDuringInference": False,
        "teacherCoordinatesUsedDuringInference": False,
        "restoredOutputsLoadedDuringInference": False,
        "heldOutAccessed": False,
        "trainingOrFineTuningPerformed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "detectorSourceSha256": sha256_file(Path(__file__)),
        "parentDetectorSourceSha256": sha256_file(Path(parent.__file__)),
        "config": {"parentDetector": asdict(p_cfg), "spacingConsensus": asdict(c_cfg)},
        "sourceIdentityExpectedCount": len(expected_source_sha256) if expected_source_sha256 is not None else None,
        "sourceIdentityMatchedCount": identity_matches if expected_source_sha256 is not None else None,
        "pageCount": len(pages),
        "pages": pages,
        "claimBoundary": _claim_boundary(),
    }
    canonical = _canonical_bytes(payload)
    artifact_sha = hashlib.sha256(canonical).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical)
    Path(str(output_path) + ".sha256").write_text(artifact_sha + "\n", encoding="utf-8")
    return {"artifactSha256": artifact_sha, "artifact": payload}


def _system_dict_reference(system: Mapping[str, Any]) -> tuple[str, float]:
    provenance = system.get("provenance")
    _require(isinstance(provenance, str) and provenance, "parent raw system provenance missing")
    spacing = _valid_spacing(system.get("staffSpacing"))
    _require(spacing is not None, "parent raw system spacing invalid")
    lines = system.get("lines")
    _require(isinstance(lines, list) and len(lines) == 5, "parent raw system must contain exactly five lines")
    ys = [float(line["centerY"]) for line in lines]
    _require(all(math.isfinite(y) for y in ys), "parent raw system has non-finite line geometry")
    _require(all(a < b for a, b in zip(ys, ys[1:])), "parent raw system line order invalid")
    return provenance, spacing


def _filter_system_dicts(
    systems: Sequence[Mapping[str, Any]], config: SpacingConsensusConfig
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config.validate()
    refs = [_system_dict_reference(system) for system in systems]
    reference_spacing, reference_source, anchor_count = _reference_spacing_from_values(refs, config)
    kept: list[dict[str, Any]] = []
    suppressed_by_provenance: dict[str, int] = {}
    for source, (provenance, spacing) in zip(systems, refs):
        if _is_anchor_provenance(provenance) or reference_spacing is None:
            accept = True
        else:
            ratio = spacing / reference_spacing
            accept = config.weak_spacing_ratio_min <= ratio <= config.weak_spacing_ratio_max
        if accept:
            item = json.loads(json.dumps(source))
            item["systemIndex"] = len(kept) + 1
            item["detectorVersion"] = DETECTOR_VERSION
            kept.append(item)
        else:
            suppressed_by_provenance[provenance] = suppressed_by_provenance.get(provenance, 0) + 1
    diagnostics = {
        "referenceSpacing": reference_spacing,
        "referenceSpacingSource": reference_source,
        "anchorSystemCount": anchor_count,
        "parentSystemCount": len(systems),
        "suppressedWeakSystemCount": len(systems) - len(kept),
        "suppressedByProvenance": dict(sorted(suppressed_by_provenance.items())),
        "finalSystemCount": len(kept),
        "weakSpacingRatioMin": config.weak_spacing_ratio_min,
        "weakSpacingRatioMax": config.weak_spacing_ratio_max,
    }
    return kept, diagnostics


def freeze_frozen_parent_artifact(
    parent_artifact_path: Path,
    output_path: Path,
    *,
    consensus_config: SpacingConsensusConfig | None = None,
    expected_parent_artifact_sha256: str | None = None,
) -> dict[str, Any]:
    """Freeze v1.3 by deterministic post-filtering of an already-frozen v1.2 raw artifact.

    This path is intended for development re-scoring when the exact v1.2 source-only
    raw output is already frozen. It does not load teacher truth and is mathematically
    equivalent to applying the v1.3 post-filter to those same v1.2 detections.
    """

    cfg = consensus_config or SpacingConsensusConfig()
    cfg.validate()
    parent_artifact_path, output_path = Path(parent_artifact_path), Path(output_path)
    parent_bytes = parent_artifact_path.read_bytes()
    parent_sha = hashlib.sha256(parent_bytes).hexdigest()
    if expected_parent_artifact_sha256 is not None:
        _require(parent_sha == expected_parent_artifact_sha256, "parent raw artifact SHA-256 mismatch")
    parent_payload = json.loads(parent_bytes.decode("utf-8"))
    _require(parent_payload.get("detectorVersion") == PARENT_DETECTOR_VERSION, "unexpected parent detector version")
    _require(parent_payload.get("sourceOnly") is True, "parent raw artifact is not source-only")
    _require(parent_payload.get("teacherArtifactLoadedDuringInference") is False, "parent raw artifact loaded teacher truth")
    _require(parent_payload.get("teacherCoordinatesUsedDuringInference") is False, "parent raw artifact used teacher coordinates")
    _require(parent_payload.get("restoredOutputsLoadedDuringInference") is False, "parent raw artifact used restored outputs")
    _require(parent_payload.get("heldOutAccessed") is False, "parent raw artifact accessed held-out data")
    _require(parent_payload.get("pageSpecificRulesUsed") is False, "parent raw artifact used page-specific rules")
    pages_in = parent_payload.get("pages")
    _require(isinstance(pages_in, list) and pages_in, "parent raw artifact has no pages")
    pages: list[dict[str, Any]] = []
    total_suppressed = 0
    for page in pages_in:
        _require(isinstance(page, dict), "invalid parent page")
        systems_in = page.get("systems")
        _require(isinstance(systems_in, list), "parent page systems missing")
        systems, filter_diagnostics = _filter_system_dicts(systems_in, cfg)
        total_suppressed += filter_diagnostics["suppressedWeakSystemCount"]
        pages.append({
            "pageId": page.get("pageId"),
            "sourceFileName": page.get("sourceFileName"),
            "sourceSha256": page.get("sourceSha256"),
            "width": page.get("width"),
            "height": page.get("height"),
            "systemCount": len(systems),
            "systems": systems,
            "abstentionReason": None if systems else "NO_SOURCE_SUPPORTED_STANDARD_FIVE_LINE_STAFF_SYSTEM",
            "diagnostics": {
                "sourceOnly": True,
                "teacherCoordinatesUsed": False,
                "restoredOutputsUsed": False,
                "heldOutAccessed": False,
                "trainingUsed": False,
                "pageIdentityUsed": False,
                "pageSpecificRulesUsed": False,
                "parentDetectorVersion": PARENT_DETECTOR_VERSION,
                "parentRawDiagnostics": page.get("diagnostics"),
                "spacingConsensus": filter_diagnostics,
                "finalSystemCount": len(systems),
            },
        })
    payload: dict[str, Any] = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "generationMode": "deterministic-successor-filter-over-frozen-v1.2-source-output",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "sourceOnly": True,
        "teacherArtifactLoadedDuringInference": False,
        "teacherCoordinatesUsedDuringInference": False,
        "restoredOutputsLoadedDuringInference": False,
        "heldOutAccessed": False,
        "trainingOrFineTuningPerformed": False,
        "pageIdentityUsed": False,
        "pageSpecificRulesUsed": False,
        "detectorSourceSha256": sha256_file(Path(__file__)),
        "parentRawArtifactSha256": parent_sha,
        "parentDetectorSourceSha256": parent_payload.get("detectorSourceSha256"),
        "config": {"spacingConsensus": asdict(cfg)},
        "sourceIdentityExpectedCount": parent_payload.get("sourceIdentityExpectedCount"),
        "sourceIdentityMatchedCount": parent_payload.get("sourceIdentityMatchedCount"),
        "pageCount": len(pages),
        "suppressedWeakSystemCount": total_suppressed,
        "pages": pages,
        "claimBoundary": _claim_boundary(),
    }
    canonical = _canonical_bytes(payload)
    artifact_sha = hashlib.sha256(canonical).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical)
    Path(str(output_path) + ".sha256").write_text(artifact_sha + "\n", encoding="utf-8")
    return {"artifactSha256": artifact_sha, "artifact": payload}


__all__ = [
    "DETECTOR_VERSION",
    "RAW_ARTIFACT_SCHEMA_VERSION",
    "PARENT_DETECTOR_VERSION",
    "ParentDetectorConfig",
    "SpacingConsensusConfig",
    "StaffLineDetection",
    "StaffSystemDetection",
    "StaffLineMultiSystemDetectorV13Error",
    "detect_staff_systems",
    "detect_staff_systems_with_diagnostics",
    "freeze_source_folder",
    "freeze_frozen_parent_artifact",
    "sha256_file",
]
