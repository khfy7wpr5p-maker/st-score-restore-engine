"""Stage 11 V2d v1.4 source-only staff-line weak-evidence suppression successor.

Development-only. Frozen v1.3 remains immutable. V1.4 applies one additional
bounded source-only evidence floor after v1.3 spacing-consensus filtering:

* anchor-grade v1.2 provenance is always preserved;
* other systems are retained when confidence or horizontal page coverage is
  strong enough;
* if a non-empty parent page would otherwise become empty, the strongest
  source-only parent candidate is retained (fail-open page coverage).

The candidate never loads teacher coordinates, restored outputs, held-out data,
page identities, filenames, training state, or source-family-specific rules.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from . import stage11_v2d_staff_line_multisystem_source_detector_v1_3 as parent

DETECTOR_VERSION = "stage11-v2d-staff-multisystem-source.v1.4"
RAW_ARTIFACT_SCHEMA_VERSION = "stage11.v2d.staff-line-multisystem-source-raw.v1.4"
PARENT_DETECTOR_VERSION = parent.DETECTOR_VERSION
GRANDPARENT_DETECTOR_VERSION = parent.PARENT_DETECTOR_VERSION

ParentDetectorConfig = parent.ParentDetectorConfig
SpacingConsensusConfig = parent.SpacingConsensusConfig
StaffLineDetection = parent.StaffLineDetection
StaffSystemDetection = parent.StaffSystemDetection

_ANCHOR_PROVENANCE = frozenset({
    "source-only:v1.2-parent-preserved:source-only:v1-compatibility+v1.1-local-spacing-topology",
    "source-only:v1.2-parent-anchored-morph-ridge",
})


class StaffLineMultiSystemDetectorV14Error(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise StaffLineMultiSystemDetectorV14Error(message)


@dataclass(frozen=True)
class WeakEvidenceConfig:
    """Source-only evidence floor for non-anchor v1.3 systems."""

    weak_confidence_min: float = 0.91
    weak_page_width_fraction_min: float = 0.75
    fail_open_if_parent_nonempty: bool = True

    def validate(self) -> None:
        _require(
            math.isfinite(self.weak_confidence_min)
            and 0.50 <= self.weak_confidence_min <= 1.0,
            "invalid weak confidence floor",
        )
        _require(
            math.isfinite(self.weak_page_width_fraction_min)
            and 0.25 <= self.weak_page_width_fraction_min <= 1.0,
            "invalid weak page-width fraction floor",
        )
        _require(
            isinstance(self.fail_open_if_parent_nonempty, bool),
            "invalid fail-open flag",
        )


def _is_anchor_provenance(provenance: str) -> bool:
    return provenance in _ANCHOR_PROVENANCE


def _validate_detection(item: StaffSystemDetection, page_width: int) -> None:
    _require(page_width > 0, "page width must be positive")
    _require(len(item.lines) == 5, "parent detection must contain exactly five lines")
    ys = [float(line.center_y) for line in item.lines]
    _require(all(math.isfinite(y) for y in ys), "parent detection has non-finite line geometry")
    _require(all(a < b for a, b in zip(ys, ys[1:])), "parent detection line order is invalid")
    _require(len(item.bbox) == 4, "parent detection bbox invalid")
    left, _top, right, _bottom = [float(value) for value in item.bbox]
    _require(math.isfinite(left) and math.isfinite(right) and right > left, "parent detection width invalid")
    confidence = float(item.confidence)
    _require(math.isfinite(confidence) and 0.0 <= confidence <= 1.0, "parent confidence invalid")


def _width_fraction_bbox(bbox: Sequence[float], page_width: int) -> float:
    _require(page_width > 0, "page width must be positive")
    _require(len(bbox) == 4, "bbox must have four values")
    left, _top, right, _bottom = [float(value) for value in bbox]
    _require(math.isfinite(left) and math.isfinite(right) and right > left, "bbox width invalid")
    fraction = (right - left) / float(page_width)
    _require(math.isfinite(fraction) and fraction > 0.0, "bbox width fraction invalid")
    return fraction


def _passes_weak_evidence(
    provenance: str,
    confidence: float,
    bbox: Sequence[float],
    page_width: int,
    config: WeakEvidenceConfig,
) -> tuple[bool, float]:
    config.validate()
    if _is_anchor_provenance(provenance):
        return True, _width_fraction_bbox(bbox, page_width)
    width_fraction = _width_fraction_bbox(bbox, page_width)
    return (
        confidence >= config.weak_confidence_min
        or width_fraction >= config.weak_page_width_fraction_min
    ), width_fraction


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


def _fail_open_rank(item: StaffSystemDetection, page_width: int) -> tuple[int, float, float, int]:
    width_fraction = _width_fraction_bbox(item.bbox, page_width)
    return (
        1 if _is_anchor_provenance(item.provenance) else 0,
        float(item.confidence),
        width_fraction,
        -int(item.system_index),
    )


def _apply_source_evidence_floor(
    detections: Sequence[StaffSystemDetection],
    page_width: int,
    config: WeakEvidenceConfig,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    config.validate()
    ordered = list(detections)
    for item in ordered:
        _validate_detection(item, page_width)

    accepted: list[StaffSystemDetection] = []
    rejected: list[StaffSystemDetection] = []
    rejected_by_provenance: dict[str, int] = {}
    evidence_rows: list[dict[str, Any]] = []
    for item in ordered:
        accept, width_fraction = _passes_weak_evidence(
            item.provenance,
            float(item.confidence),
            item.bbox,
            page_width,
            config,
        )
        evidence_rows.append({
            "parentSystemIndex": int(item.system_index),
            "provenance": item.provenance,
            "confidence": float(item.confidence),
            "pageWidthFraction": width_fraction,
            "anchorGrade": _is_anchor_provenance(item.provenance),
            "acceptedBeforeFailOpen": bool(accept),
        })
        if accept:
            accepted.append(item)
        else:
            rejected.append(item)
            rejected_by_provenance[item.provenance] = rejected_by_provenance.get(item.provenance, 0) + 1

    fail_open_restored: StaffSystemDetection | None = None
    if ordered and not accepted and config.fail_open_if_parent_nonempty:
        fail_open_restored = max(ordered, key=lambda item: _fail_open_rank(item, page_width))
        accepted = [fail_open_restored]
        rejected = [item for item in rejected if item is not fail_open_restored]
        provenance = fail_open_restored.provenance
        if rejected_by_provenance.get(provenance, 0) > 0:
            rejected_by_provenance[provenance] -= 1
            if rejected_by_provenance[provenance] == 0:
                del rejected_by_provenance[provenance]

    reindexed = [_reindexed_detection(item, index) for index, item in enumerate(accepted, start=1)]
    diagnostics = {
        "parentSystemCount": len(ordered),
        "acceptedBeforeFailOpenCount": sum(1 for row in evidence_rows if row["acceptedBeforeFailOpen"]),
        "failOpenRestoredSystemCount": 1 if fail_open_restored is not None else 0,
        "failOpenRestoredParentSystemIndex": (
            int(fail_open_restored.system_index) if fail_open_restored is not None else None
        ),
        "suppressedWeakSystemCount": len(ordered) - len(reindexed),
        "suppressedByProvenance": dict(sorted(rejected_by_provenance.items())),
        "finalSystemCount": len(reindexed),
        "weakConfidenceMin": config.weak_confidence_min,
        "weakPageWidthFractionMin": config.weak_page_width_fraction_min,
        "failOpenIfParentNonempty": config.fail_open_if_parent_nonempty,
        "evidenceRows": evidence_rows,
    }
    return reindexed, diagnostics


def detect_staff_systems_with_diagnostics(
    image: np.ndarray,
    *,
    parent_config: ParentDetectorConfig | None = None,
    consensus_config: SpacingConsensusConfig | None = None,
    evidence_config: WeakEvidenceConfig | None = None,
) -> tuple[list[StaffSystemDetection], dict[str, Any]]:
    e_cfg = evidence_config or WeakEvidenceConfig()
    e_cfg.validate()
    parent_detections, parent_diagnostics = parent.detect_staff_systems_with_diagnostics(
        image,
        parent_config=parent_config,
        consensus_config=consensus_config,
    )
    _require(isinstance(image, np.ndarray) and image.ndim == 2, "image must be grayscale")
    page_width = int(image.shape[1])
    detections, evidence_diagnostics = _apply_source_evidence_floor(
        parent_detections,
        page_width,
        e_cfg,
    )
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
        "sourceEvidenceFloor": evidence_diagnostics,
        "finalSystemCount": len(detections),
    }
    return detections, diagnostics


def detect_staff_systems(
    image: np.ndarray,
    *,
    parent_config: ParentDetectorConfig | None = None,
    consensus_config: SpacingConsensusConfig | None = None,
    evidence_config: WeakEvidenceConfig | None = None,
) -> list[StaffSystemDetection]:
    return detect_staff_systems_with_diagnostics(
        image,
        parent_config=parent_config,
        consensus_config=consensus_config,
        evidence_config=evidence_config,
    )[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _claim_boundary() -> dict[str, bool]:
    return {
        "detectorQualified": False,
        "sourceDetectorAdequacyEstablished": False,
        "staffLinePass": False,
        "semanticPreservationEstablished": False,
        "overallStage11PassAuthorized": False,
        "restoredImageTopologyComparisonAuthorized": False,
        "productionReady": False,
        "productionPromotionAuthorized": False,
        "stage12EntryAuthorized": False,
        "prReadyForMerge": False,
    }


def freeze_source_folder(
    source_dir: Path,
    output_path: Path,
    *,
    parent_config: ParentDetectorConfig | None = None,
    consensus_config: SpacingConsensusConfig | None = None,
    evidence_config: WeakEvidenceConfig | None = None,
    expected_source_sha256: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    p_cfg = parent_config or ParentDetectorConfig()
    p_cfg.validate()
    c_cfg = consensus_config or SpacingConsensusConfig()
    c_cfg.validate()
    e_cfg = evidence_config or WeakEvidenceConfig()
    e_cfg.validate()
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
            image,
            parent_config=p_cfg,
            consensus_config=c_cfg,
            evidence_config=e_cfg,
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
        "grandparentDetectorVersion": GRANDPARENT_DETECTOR_VERSION,
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
        "config": {
            "parentDetector": asdict(p_cfg),
            "spacingConsensus": asdict(c_cfg),
            "sourceEvidence": asdict(e_cfg),
        },
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


def _validate_parent_system_dict(system: Mapping[str, Any], page_width: int) -> tuple[str, float, float]:
    provenance = system.get("provenance")
    _require(isinstance(provenance, str) and provenance, "parent raw system provenance missing")
    confidence = float(system.get("confidence"))
    _require(math.isfinite(confidence) and 0.0 <= confidence <= 1.0, "parent raw confidence invalid")
    lines = system.get("lines")
    _require(isinstance(lines, list) and len(lines) == 5, "parent raw system must contain exactly five lines")
    ys = [float(line["centerY"]) for line in lines]
    _require(all(math.isfinite(y) for y in ys), "parent raw system has non-finite line geometry")
    _require(all(a < b for a, b in zip(ys, ys[1:])), "parent raw system line order invalid")
    bbox = system.get("bbox")
    _require(isinstance(bbox, list) and len(bbox) == 4, "parent raw bbox invalid")
    width_fraction = _width_fraction_bbox(bbox, page_width)
    return provenance, confidence, width_fraction


def _filter_system_dicts(
    systems: Sequence[Mapping[str, Any]],
    page_width: int,
    config: WeakEvidenceConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config.validate()
    _require(page_width > 0, "page width must be positive")
    rows: list[tuple[Mapping[str, Any], str, float, float, bool]] = []
    rejected_by_provenance: dict[str, int] = {}
    accepted_sources: list[Mapping[str, Any]] = []
    for system in systems:
        provenance, confidence, width_fraction = _validate_parent_system_dict(system, page_width)
        accept = (
            _is_anchor_provenance(provenance)
            or confidence >= config.weak_confidence_min
            or width_fraction >= config.weak_page_width_fraction_min
        )
        rows.append((system, provenance, confidence, width_fraction, accept))
        if accept:
            accepted_sources.append(system)
        else:
            rejected_by_provenance[provenance] = rejected_by_provenance.get(provenance, 0) + 1

    fail_open_source: Mapping[str, Any] | None = None
    if systems and not accepted_sources and config.fail_open_if_parent_nonempty:
        def rank(row: tuple[Mapping[str, Any], str, float, float, bool]) -> tuple[int, float, float, int]:
            source, provenance, confidence, width_fraction, _accept = row
            return (
                1 if _is_anchor_provenance(provenance) else 0,
                confidence,
                width_fraction,
                -int(source.get("systemIndex", 0)),
            )
        chosen = max(rows, key=rank)
        fail_open_source = chosen[0]
        accepted_sources = [fail_open_source]
        provenance = chosen[1]
        if rejected_by_provenance.get(provenance, 0) > 0:
            rejected_by_provenance[provenance] -= 1
            if rejected_by_provenance[provenance] == 0:
                del rejected_by_provenance[provenance]

    kept: list[dict[str, Any]] = []
    for source in accepted_sources:
        item = json.loads(json.dumps(source))
        item["systemIndex"] = len(kept) + 1
        item["detectorVersion"] = DETECTOR_VERSION
        kept.append(item)

    diagnostics = {
        "parentSystemCount": len(systems),
        "acceptedBeforeFailOpenCount": sum(1 for row in rows if row[4]),
        "failOpenRestoredSystemCount": 1 if fail_open_source is not None else 0,
        "failOpenRestoredParentSystemIndex": (
            int(fail_open_source.get("systemIndex", 0)) if fail_open_source is not None else None
        ),
        "suppressedWeakSystemCount": len(systems) - len(kept),
        "suppressedByProvenance": dict(sorted(rejected_by_provenance.items())),
        "finalSystemCount": len(kept),
        "weakConfidenceMin": config.weak_confidence_min,
        "weakPageWidthFractionMin": config.weak_page_width_fraction_min,
        "failOpenIfParentNonempty": config.fail_open_if_parent_nonempty,
    }
    return kept, diagnostics


def _validate_source_only_parent_payload(payload: Mapping[str, Any], expected_version: str) -> None:
    _require(payload.get("detectorVersion") == expected_version, "unexpected parent detector version")
    _require(payload.get("sourceOnly") is True, "parent raw artifact is not source-only")
    _require(payload.get("teacherArtifactLoadedDuringInference") is False, "parent raw artifact loaded teacher truth")
    _require(payload.get("teacherCoordinatesUsedDuringInference") is False, "parent raw artifact used teacher coordinates")
    _require(payload.get("restoredOutputsLoadedDuringInference") is False, "parent raw artifact used restored outputs")
    _require(payload.get("heldOutAccessed") is False, "parent raw artifact accessed held-out data")
    _require(payload.get("pageSpecificRulesUsed") is False, "parent raw artifact used page-specific rules")


def freeze_frozen_parent_artifact(
    parent_artifact_path: Path,
    output_path: Path,
    *,
    evidence_config: WeakEvidenceConfig | None = None,
    expected_parent_artifact_sha256: str | None = None,
) -> dict[str, Any]:
    """Freeze v1.4 by deterministic post-filtering of frozen v1.3 raw output."""

    cfg = evidence_config or WeakEvidenceConfig()
    cfg.validate()
    parent_artifact_path, output_path = Path(parent_artifact_path), Path(output_path)
    parent_bytes = parent_artifact_path.read_bytes()
    parent_sha = hashlib.sha256(parent_bytes).hexdigest()
    if expected_parent_artifact_sha256 is not None:
        _require(parent_sha == expected_parent_artifact_sha256, "parent raw artifact SHA-256 mismatch")
    parent_payload = json.loads(parent_bytes.decode("utf-8"))
    _validate_source_only_parent_payload(parent_payload, PARENT_DETECTOR_VERSION)

    pages_in = parent_payload.get("pages")
    _require(isinstance(pages_in, list) and pages_in, "parent raw artifact has no pages")
    pages: list[dict[str, Any]] = []
    total_suppressed = 0
    total_fail_open = 0
    for page in pages_in:
        _require(isinstance(page, dict), "invalid parent page")
        page_width = int(page.get("width"))
        systems_in = page.get("systems")
        _require(isinstance(systems_in, list), "parent page systems missing")
        systems, evidence_diagnostics = _filter_system_dicts(systems_in, page_width, cfg)
        total_suppressed += evidence_diagnostics["suppressedWeakSystemCount"]
        total_fail_open += evidence_diagnostics["failOpenRestoredSystemCount"]
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
                "sourceEvidenceFloor": evidence_diagnostics,
                "finalSystemCount": len(systems),
            },
        })

    payload: dict[str, Any] = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "generationMode": "deterministic-successor-filter-over-frozen-v1.3-source-output",
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
        "config": {"sourceEvidence": asdict(cfg)},
        "sourceIdentityExpectedCount": parent_payload.get("sourceIdentityExpectedCount"),
        "sourceIdentityMatchedCount": parent_payload.get("sourceIdentityMatchedCount"),
        "pageCount": len(pages),
        "suppressedWeakSystemCount": total_suppressed,
        "failOpenRestoredSystemCount": total_fail_open,
        "pages": pages,
        "claimBoundary": _claim_boundary(),
    }
    canonical = _canonical_bytes(payload)
    artifact_sha = hashlib.sha256(canonical).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(canonical)
    Path(str(output_path) + ".sha256").write_text(artifact_sha + "\n", encoding="utf-8")
    return {"artifactSha256": artifact_sha, "artifact": payload}


def freeze_frozen_v1_2_artifact(
    v1_2_artifact_path: Path,
    output_path: Path,
    *,
    consensus_config: SpacingConsensusConfig | None = None,
    evidence_config: WeakEvidenceConfig | None = None,
    expected_v1_2_artifact_sha256: str | None = None,
) -> dict[str, Any]:
    """Development convenience path: frozen v1.2 -> frozen v1.3 logic -> v1.4.

    This never loads teacher truth. It exists because the exact v1.2 development
    raw artifact is the long-lived immutable source-only development anchor.
    """

    c_cfg = consensus_config or SpacingConsensusConfig()
    c_cfg.validate()
    e_cfg = evidence_config or WeakEvidenceConfig()
    e_cfg.validate()
    v1_2_artifact_path, output_path = Path(v1_2_artifact_path), Path(output_path)
    parent_bytes = v1_2_artifact_path.read_bytes()
    parent_sha = hashlib.sha256(parent_bytes).hexdigest()
    if expected_v1_2_artifact_sha256 is not None:
        _require(parent_sha == expected_v1_2_artifact_sha256, "v1.2 raw artifact SHA-256 mismatch")
    payload_v12 = json.loads(parent_bytes.decode("utf-8"))
    _validate_source_only_parent_payload(payload_v12, GRANDPARENT_DETECTOR_VERSION)

    pages_in = payload_v12.get("pages")
    _require(isinstance(pages_in, list) and pages_in, "v1.2 raw artifact has no pages")
    pages: list[dict[str, Any]] = []
    total_spacing_suppressed = 0
    total_evidence_suppressed = 0
    total_fail_open = 0
    for page in pages_in:
        _require(isinstance(page, dict), "invalid v1.2 page")
        systems_in = page.get("systems")
        _require(isinstance(systems_in, list), "v1.2 page systems missing")
        v13_systems, spacing_diagnostics = parent._filter_system_dicts(systems_in, c_cfg)
        page_width = int(page.get("width"))
        systems, evidence_diagnostics = _filter_system_dicts(v13_systems, page_width, e_cfg)
        total_spacing_suppressed += spacing_diagnostics["suppressedWeakSystemCount"]
        total_evidence_suppressed += evidence_diagnostics["suppressedWeakSystemCount"]
        total_fail_open += evidence_diagnostics["failOpenRestoredSystemCount"]
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
                "grandparentDetectorVersion": GRANDPARENT_DETECTOR_VERSION,
                "grandparentRawDiagnostics": page.get("diagnostics"),
                "spacingConsensus": spacing_diagnostics,
                "sourceEvidenceFloor": evidence_diagnostics,
                "finalSystemCount": len(systems),
            },
        })

    payload: dict[str, Any] = {
        "schemaVersion": RAW_ARTIFACT_SCHEMA_VERSION,
        "detectorVersion": DETECTOR_VERSION,
        "parentDetectorVersion": PARENT_DETECTOR_VERSION,
        "grandparentDetectorVersion": GRANDPARENT_DETECTOR_VERSION,
        "generationMode": "deterministic-v1.4-successor-over-frozen-v1.2-via-frozen-v1.3-spacing-consensus",
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
        "grandparentRawArtifactSha256": parent_sha,
        "grandparentDetectorSourceSha256": payload_v12.get("detectorSourceSha256"),
        "config": {
            "spacingConsensus": asdict(c_cfg),
            "sourceEvidence": asdict(e_cfg),
        },
        "sourceIdentityExpectedCount": payload_v12.get("sourceIdentityExpectedCount"),
        "sourceIdentityMatchedCount": payload_v12.get("sourceIdentityMatchedCount"),
        "pageCount": len(pages),
        "spacingConsensusSuppressedWeakSystemCount": total_spacing_suppressed,
        "sourceEvidenceSuppressedWeakSystemCount": total_evidence_suppressed,
        "failOpenRestoredSystemCount": total_fail_open,
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
    "GRANDPARENT_DETECTOR_VERSION",
    "ParentDetectorConfig",
    "SpacingConsensusConfig",
    "WeakEvidenceConfig",
    "StaffLineDetection",
    "StaffSystemDetection",
    "StaffLineMultiSystemDetectorV14Error",
    "detect_staff_systems",
    "detect_staff_systems_with_diagnostics",
    "freeze_source_folder",
    "freeze_frozen_parent_artifact",
    "freeze_frozen_v1_2_artifact",
    "sha256_file",
]
