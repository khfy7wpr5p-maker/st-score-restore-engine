"""Conservative structural validator for music-score and guitar-TAB candidates."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
import math
import re
from typing import Any, Iterable, Mapping

import cv2
import numpy as np

from .input_inspection import InputInspectionError, inspect_bytes
from .music_safety_types import (
    MusicSafetyConfig,
    MusicSafetyValidationError,
    SCHEMA_VERSION,
    TeacherDecision,
    VALIDATOR_VERSION,
)


def validate_candidate(
    source_bytes: bytes,
    candidate_bytes: bytes,
    *,
    source_name: str | None = None,
    candidate_name: str | None = None,
    candidate_manifest: Mapping[str, Any] | None = None,
    config: MusicSafetyConfig | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare a source image with a restoration candidate and return a veto-capable report."""

    resolved = config if isinstance(config, MusicSafetyConfig) else MusicSafetyConfig.from_mapping(config)
    _preflight_bytes(source_bytes, role="source", config=resolved)
    _preflight_bytes(candidate_bytes, role="candidate", config=resolved)
    source = _decode_image(source_bytes, role="source", config=resolved)
    candidate = _decode_image(candidate_bytes, role="candidate", config=resolved)
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    candidate_digest = hashlib.sha256(candidate_bytes).hexdigest()
    integrity_findings = _validate_candidate_manifest(candidate_manifest, source_digest, candidate_digest)

    registered, registration = _register_candidate(source, candidate, resolved)
    source_threshold = _estimate_dark_threshold(source, resolved)
    candidate_threshold = _estimate_dark_threshold(registered, resolved)
    comparison_threshold = source_threshold
    source_dark = source <= comparison_threshold
    candidate_dark = registered <= comparison_threshold

    source_lines = _detect_horizontal_systems(source_dark, resolved)
    candidate_lines = _detect_horizontal_systems(candidate_dark, resolved)
    geometry = _compare_geometry(source_lines, candidate_lines, source_dark, candidate_dark, resolved)

    source_line_mask = _line_mask(source_dark.shape, source_lines)
    candidate_line_mask = _line_mask(candidate_dark.shape, candidate_lines)
    shared_line_mask = source_line_mask | candidate_line_mask
    source_symbols = source_dark & ~shared_line_mask
    candidate_symbols = candidate_dark & ~shared_line_mask

    symbol_metrics, symbol_findings = _compare_symbol_pixels(source_symbols, candidate_symbols, resolved)
    component_metrics, component_findings = _compare_components(source_symbols, candidate_symbols, resolved)
    region_findings = _regional_findings(source_symbols, candidate_symbols, resolved)

    findings = integrity_findings + geometry["findings"] + symbol_findings + component_findings + region_findings
    review_reasons: list[str] = []
    reject_reasons: list[str] = []

    if not registration["reliable"]:
        review_reasons.append("registration_uncertain")
    if geometry["unknownSystems"]["source"] or geometry["unknownSystems"]["candidate"]:
        review_reasons.append("unknown_system_geometry")
    if geometry["staff"]["sourceSystemCount"] + geometry["tab"]["sourceSystemCount"] == 0:
        review_reasons.append("no_recognized_music_systems")
    if geometry["rejectReasons"]:
        reject_reasons.extend(geometry["rejectReasons"])
    review_reasons.extend(geometry["reviewReasons"])
    _classify_metric(symbol_metrics["lossFraction"], resolved.symbol_loss_review_fraction, resolved.symbol_loss_reject_fraction, "symbol_loss", review_reasons, reject_reasons)
    _classify_metric(symbol_metrics["inventionFraction"], resolved.symbol_invention_review_fraction, resolved.symbol_invention_reject_fraction, "symbol_invention", review_reasons, reject_reasons)
    _classify_metric(component_metrics["lossFraction"], resolved.component_loss_review_fraction, resolved.component_loss_reject_fraction, "component_loss", review_reasons, reject_reasons)
    _classify_metric(component_metrics["inventionFraction"], resolved.component_invention_review_fraction, resolved.component_invention_reject_fraction, "component_invention", review_reasons, reject_reasons)
    if component_metrics["maxMatchedShiftPixels"] >= resolved.component_shift_reject_pixels:
        reject_reasons.append("component_shift_severe")
    elif component_metrics["maxMatchedShiftPixels"] >= resolved.component_shift_review_pixels:
        review_reasons.append("component_shift_detected")
    for item in integrity_findings:
        reject_reasons.append(item["code"])
    if candidate_manifest and candidate_manifest.get("status") == "review_required":
        review_reasons.append("candidate_engine_requires_review")

    reject_reasons = sorted(set(reject_reasons))
    review_reasons = sorted(set(review_reasons) - set(reject_reasons))
    verdict = "reject" if reject_reasons else "review_required" if review_reasons else "pass"
    risk_score = _risk_score(geometry, symbol_metrics, component_metrics, registration, verdict)
    report_id = _report_id(source_digest, candidate_digest, resolved.digest(), VALIDATOR_VERSION)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "validatorVersion": VALIDATOR_VERSION,
        "reportId": report_id,
        "status": "completed",
        "verdict": verdict,
        "automaticApproval": False,
        "source": {
            "artifactId": f"sha256:{source_digest}",
            "name": _safe_name(source_name, "source"),
            "digest": {"algorithm": "sha256", "value": source_digest},
            "widthPixels": int(source.shape[1]),
            "heightPixels": int(source.shape[0]),
        },
        "candidate": {
            "artifactId": f"sha256:{candidate_digest}",
            "name": _safe_name(candidate_name, "candidate"),
            "digest": {"algorithm": "sha256", "value": candidate_digest},
            "widthPixels": int(candidate.shape[1]),
            "heightPixels": int(candidate.shape[0]),
        },
        "configuration": asdict(resolved),
        "configurationDigest": {"algorithm": "sha256", "value": resolved.digest()},
        "registration": registration,
        "thresholds": {"sourceDarkThreshold": source_threshold, "candidateDarkThreshold": candidate_threshold},
        "geometry": {"staff": geometry["staff"], "tab": geometry["tab"], "unknownSystems": geometry["unknownSystems"]},
        "metrics": {"symbols": symbol_metrics, "components": component_metrics, "riskScore": risk_score},
        "findings": sorted(findings, key=lambda item: (item["severity"], item["code"], item["region"]["y"] if item.get("region") else -1)),
        "decision": {
            "rejectReasons": reject_reasons,
            "reviewRequiredReasons": review_reasons,
            "teacherReviewRequired": verdict != "pass",
        },
        "fallback": {"originalAvailable": True, "recommendedAction": "return_original" if verdict == "reject" else "retain_original"},
        "teacherReview": {
            "decision": None,
            "reviewerId": None,
            "notes": None,
            "trainingLabelCreated": False,
            "trainingUseConsent": None,
        },
        "comparator": {
            "eligible": verdict != "reject",
            "tier": {"pass": 0, "review_required": 1, "reject": 2}[verdict],
            "riskScore": risk_score,
        },
    }


def compare_candidate_reports(reports: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Rank validated candidates without converting selection into approval."""

    items = [dict(item) for item in reports]
    if not items:
        raise MusicSafetyValidationError("no_candidate_reports", "At least one report is required.")
    normalized: list[dict[str, Any]] = []
    source_ids: set[str] = set()
    for item in items:
        verdict = item.get("verdict")
        if item.get("status") != "completed" or verdict not in {"pass", "review_required", "reject"}:
            raise MusicSafetyValidationError("invalid_candidate_report", "Every comparator input must be a completed validator report.")
        if item.get("automaticApproval") is not False:
            raise MusicSafetyValidationError("invalid_candidate_report", "Candidate reports must prohibit automatic approval.")
        source_id = ((item.get("source") or {}).get("artifactId"))
        candidate_id = ((item.get("candidate") or {}).get("artifactId"))
        risk_score = ((item.get("metrics") or {}).get("riskScore"))
        if not isinstance(source_id, str) or not isinstance(candidate_id, str) or not isinstance(risk_score, (int, float)) or not 0 <= float(risk_score) <= 100:
            raise MusicSafetyValidationError("invalid_candidate_report", "Candidate report identity or risk score is invalid.")
        source_ids.add(source_id)
        normalized.append({"report": item, "tier": {"pass": 0, "review_required": 1, "reject": 2}[verdict], "riskScore": float(risk_score), "candidateId": candidate_id})
    if len(source_ids) != 1:
        raise MusicSafetyValidationError("candidate_source_mismatch", "All compared candidates must derive from the same source artifact.")
    ranked_entries = sorted(normalized, key=lambda entry: (entry["tier"], entry["riskScore"], entry["candidateId"]))
    ranked = [entry["report"] for entry in ranked_entries]
    eligible = [item for item in ranked if item["verdict"] != "reject"]
    recommended = eligible[0] if eligible else None
    return {
        "schemaVersion": SCHEMA_VERSION,
        "validatorVersion": VALIDATOR_VERSION,
        "selectionStatus": "pass_candidate_available" if recommended and recommended["verdict"] == "pass" else "review_only" if recommended else "no_safe_candidate",
        "recommendedCandidateArtifactId": recommended["candidate"]["artifactId"] if recommended else None,
        "automaticApproval": False,
        "teacherReviewRequired": not recommended or recommended["verdict"] != "pass",
        "fallbackOriginalRequired": recommended is None,
        "ranking": [
            {
                "candidateArtifactId": item["candidate"]["artifactId"],
                "verdict": item["verdict"],
                "riskScore": item["metrics"]["riskScore"],
                "eligible": item["verdict"] != "reject",
            }
            for item in ranked
        ],
    }


def record_teacher_review(
    report: Mapping[str, Any],
    decision: TeacherDecision,
    *,
    reviewer_id: str,
    notes: str = "",
) -> dict[str, Any]:
    """Record review without producing a training label or training consent."""

    if report.get("status") != "completed" or report.get("automaticApproval") is not False:
        raise MusicSafetyValidationError("invalid_candidate_report", "Teacher review requires a completed non-approving validator report.")
    if decision not in {"approved", "rejected", "reprocess"}:
        raise MusicSafetyValidationError("invalid_teacher_decision", "Unsupported teacher decision.")
    if not reviewer_id.strip():
        raise MusicSafetyValidationError("invalid_reviewer", "A reviewer identifier is required.")
    updated = deepcopy(dict(report))
    updated["teacherReview"] = {
        "decision": decision,
        "reviewerId": reviewer_id.strip(),
        "notes": notes,
        "trainingLabelCreated": False,
        "trainingUseConsent": None,
    }
    return updated


def _decode_image(data: bytes, *, role: str, config: MusicSafetyConfig) -> np.ndarray:
    if not isinstance(data, bytes) or not data:
        raise MusicSafetyValidationError(f"invalid_{role}", f"A non-empty {role} byte sequence is required.")
    payload = _extract_pdf_jpeg(data) if data.startswith(b"%PDF-") else data
    image = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise MusicSafetyValidationError(f"{role}_decode_failed", f"The {role} could not be decoded.")
    decoded_pixels = int(image.shape[0]) * int(image.shape[1])
    if decoded_pixels > config.max_decode_pixels:
        raise MusicSafetyValidationError(f"{role}_decoded_image_too_large", f"The decoded {role} exceeds the configured pixel limit.", details={"decodedPixels": decoded_pixels, "maxDecodePixels": config.max_decode_pixels})
    return image


def _preflight_bytes(data: bytes, *, role: str, config: MusicSafetyConfig) -> None:
    if not isinstance(data, bytes) or not data:
        raise MusicSafetyValidationError(f"invalid_{role}", f"A non-empty {role} byte sequence is required.")
    if len(data) > config.max_input_bytes:
        raise MusicSafetyValidationError(f"{role}_input_too_large", f"The {role} exceeds the configured byte limit.", details={"byteSize": len(data), "maxInputBytes": config.max_input_bytes})
    if data.startswith(b"%PDF-"):
        image_count = len(re.findall(rb"/Subtype\s*/Image\b", data))
        if image_count != 1:
            raise MusicSafetyValidationError("unsupported_candidate_pdf", "Only one-image deterministic PDF artifacts are supported.", details={"imageCount": image_count})
        dimensions = re.search(rb"/Width\s+(\d+)\s+/Height\s+(\d+)", data)
        if not dimensions:
            raise MusicSafetyValidationError("malformed_candidate_pdf", "Candidate PDF image dimensions are missing.")
        declared_pixels = int(dimensions.group(1)) * int(dimensions.group(2))
        if declared_pixels > config.max_decode_pixels:
            raise MusicSafetyValidationError(f"{role}_decoded_image_too_large", f"The declared PDF image exceeds the configured pixel limit.", details={"declaredPixels": declared_pixels, "maxDecodePixels": config.max_decode_pixels})
        return
    try:
        inspected = inspect_bytes(data, source_name=f"{role}.bin", max_bytes=config.max_input_bytes)
    except InputInspectionError as error:
        raise MusicSafetyValidationError(f"{role}_inspection_failed", f"The {role} failed structural inspection.", details={"inspectionCode": error.code}) from error
    metadata = inspected["analysis"].get("imageMetadata") or {}
    width = metadata.get("encodedWidthPixels")
    height = metadata.get("encodedHeightPixels")
    if width and height and int(width) * int(height) > config.max_decode_pixels:
        raise MusicSafetyValidationError(f"{role}_decoded_image_too_large", f"The declared {role} dimensions exceed the configured pixel limit.", details={"declaredPixels": int(width) * int(height), "maxDecodePixels": config.max_decode_pixels})


def _extract_pdf_jpeg(data: bytes) -> bytes:
    marker = re.search(rb"/Subtype\s*/Image.*?/Filter\s*/DCTDecode.*?stream\r?\n", data, re.S)
    if not marker:
        raise MusicSafetyValidationError("unsupported_candidate_pdf", "Only deterministic single-image DCT PDF candidates are supported.")
    start = marker.end()
    end = data.find(b"\nendstream", start)
    if end < 0:
        raise MusicSafetyValidationError("malformed_candidate_pdf", "Candidate PDF image stream is incomplete.")
    return data[start:end]


def _register_candidate(source: np.ndarray, candidate: np.ndarray, config: MusicSafetyConfig) -> tuple[np.ndarray, dict[str, Any]]:
    source_h, source_w = source.shape
    if candidate.shape != source.shape:
        candidate = cv2.resize(candidate, (source_w, source_h), interpolation=cv2.INTER_AREA)
        resized = True
    else:
        resized = False
    source_float = source.astype(np.float32)
    candidate_float = candidate.astype(np.float32)
    shift, response = cv2.phaseCorrelate(source_float, candidate_float)
    dx, dy = float(shift[0]), float(shift[1])
    max_shift = max(source_h, source_w) * config.registration_max_translation_fraction
    reliable = math.isfinite(response) and response >= config.registration_min_response and abs(dx) <= max_shift and abs(dy) <= max_shift
    if reliable and (abs(dx) > 0.05 or abs(dy) > 0.05):
        matrix = np.array([[1.0, 0.0, -dx], [0.0, 1.0, -dy]], dtype=np.float32)
        candidate = cv2.warpAffine(candidate, matrix, (source_w, source_h), flags=cv2.INTER_LINEAR, borderValue=255)
    return candidate, {
        "method": "phase_correlation_translation",
        "resizedToSource": resized,
        "translationX": round(dx, 6),
        "translationY": round(dy, 6),
        "response": round(float(response), 8),
        "reliable": bool(reliable),
    }


def _estimate_dark_threshold(image: np.ndarray, config: MusicSafetyConfig) -> int:
    otsu, _ = cv2.threshold(cv2.GaussianBlur(image, (3, 3), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return int(min(config.dark_threshold_ceiling, max(60, otsu)))


def _detect_horizontal_systems(mask: np.ndarray, config: MusicSafetyConfig) -> list[dict[str, Any]]:
    width = mask.shape[1]
    kernel_width = max(15, int(width * config.horizontal_kernel_fraction))
    opened = cv2.morphologyEx(mask.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((1, kernel_width), np.uint8)) > 0
    coverage = opened.mean(axis=1)
    active = coverage >= config.horizontal_line_min_fraction
    centers: list[tuple[int, float]] = []
    start: int | None = None
    for index, value in enumerate(active.tolist() + [False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            end = index
            rows = np.arange(start, end)
            weights = coverage[start:end]
            center = int(round(float(np.average(rows, weights=weights)))) if weights.sum() else (start + end - 1) // 2
            centers.append((center, float(coverage[start:end].max())))
            start = None
    if not centers:
        return []
    ys = [item[0] for item in centers]
    gaps = np.diff(ys)
    normal_gaps = gaps[gaps <= np.percentile(gaps, 75)] if gaps.size else np.array([], dtype=float)
    base_gap = float(np.median(normal_gaps)) if normal_gaps.size else 12.0
    split_gap = max(base_gap * config.system_gap_multiplier, 18.0)
    groups: list[list[tuple[int, float]]] = [[centers[0]]]
    for previous, item in zip(centers, centers[1:]):
        if item[0] - previous[0] > split_gap:
            groups.append([])
        groups[-1].append(item)
    systems: list[dict[str, Any]] = []
    for group in groups:
        count = len(group)
        kind = "staff" if count == config.expected_staff_lines else "tab" if count == config.expected_tab_lines else "unknown"
        systems.append({
            "kind": kind,
            "lineCount": count,
            "lineCenters": [int(item[0]) for item in group],
            "coverage": [round(float(item[1]), 6) for item in group],
            "top": int(group[0][0]),
            "bottom": int(group[-1][0]),
        })
    return systems


def _compare_geometry(source_systems, candidate_systems, source_dark, candidate_dark, config):
    findings: list[dict[str, Any]] = []
    review: list[str] = []
    reject: list[str] = []
    results: dict[str, Any] = {}
    for kind, expected in (("staff", config.expected_staff_lines), ("tab", config.expected_tab_lines)):
        source_kind = [item for item in source_systems if item["kind"] == kind]
        candidate_kind = [item for item in candidate_systems if item["kind"] == kind]
        count_match = len(source_kind) == len(candidate_kind)
        if not count_match:
            reject.append(f"{kind}_system_count_changed")
            findings.append(_finding(f"{kind}_system_count_changed", "high", None, {"sourceSystems": len(source_kind), "candidateSystems": len(candidate_kind)}))
        line_break_pixels = 0
        line_source_pixels = 0
        compared = min(len(source_kind), len(candidate_kind))
        for index in range(compared):
            source_group = source_kind[index]
            candidate_group = candidate_kind[index]
            if source_group["lineCount"] != expected or candidate_group["lineCount"] != expected:
                reject.append(f"{kind}_line_count_changed")
            for source_y, candidate_y in zip(source_group["lineCenters"], candidate_group["lineCenters"]):
                source_band = source_dark[max(0, source_y - 1):source_y + 2]
                candidate_band = candidate_dark[max(0, candidate_y - 1):candidate_y + 2]
                source_projection = source_band.any(axis=0)
                candidate_projection = candidate_band.any(axis=0)
                relevant = source_projection
                missing = relevant & ~candidate_projection
                line_break_pixels += int(np.count_nonzero(missing))
                line_source_pixels += int(np.count_nonzero(relevant))
                if np.count_nonzero(missing):
                    xs = np.where(missing)[0]
                    findings.append(_finding(f"{kind}_line_break", "medium", _region(int(xs.min()), max(0, candidate_y - 2), int(xs.max() - xs.min() + 1), 5, candidate_dark.shape), {"missingPixels": int(xs.size)}))
        break_fraction = line_break_pixels / max(1, line_source_pixels)
        if break_fraction >= config.line_break_reject_fraction:
            reject.append(f"{kind}_line_break_severe")
        elif break_fraction >= config.line_break_review_fraction:
            review.append(f"{kind}_line_break_detected")
        results[kind] = {
            "expectedLinesPerSystem": expected,
            "sourceSystemCount": len(source_kind),
            "candidateSystemCount": len(candidate_kind),
            "systemCountPreserved": count_match,
            "sourceLineCounts": [item["lineCount"] for item in source_kind],
            "candidateLineCounts": [item["lineCount"] for item in candidate_kind],
            "lineBreakFraction": round(float(break_fraction), 8),
        }
    return {
        "staff": results["staff"],
        "tab": results["tab"],
        "unknownSystems": {"source": sum(item["kind"] == "unknown" for item in source_systems), "candidate": sum(item["kind"] == "unknown" for item in candidate_systems)},
        "findings": findings,
        "reviewReasons": review,
        "rejectReasons": reject,
    }


def _line_mask(shape: tuple[int, int], systems: list[dict[str, Any]]) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    for system in systems:
        for center in system["lineCenters"]:
            mask[max(0, center - 1):min(shape[0], center + 2), :] = True
    return mask


def _compare_symbol_pixels(source: np.ndarray, candidate: np.ndarray, config: MusicSafetyConfig):
    loss = source & ~candidate
    invention = candidate & ~source
    source_count = int(np.count_nonzero(source))
    candidate_count = int(np.count_nonzero(candidate))
    loss_count = int(np.count_nonzero(loss))
    invention_count = int(np.count_nonzero(invention))
    metrics = {
        "sourceDarkPixels": source_count,
        "candidateDarkPixels": candidate_count,
        "lostDarkPixels": loss_count,
        "inventedDarkPixels": invention_count,
        "lossFraction": round(loss_count / max(1, source_count), 8),
        "inventionFraction": round(invention_count / max(1, source_count), 8),
    }
    findings: list[dict[str, Any]] = []
    if loss_count:
        findings.append(_finding("symbol_dark_pixel_loss", "medium", _bounding_region(loss, source.shape), {"pixels": loss_count}))
    if invention_count:
        findings.append(_finding("symbol_dark_pixel_invention", "medium", _bounding_region(invention, source.shape), {"pixels": invention_count}))
    return metrics, findings


def _components(mask: np.ndarray, config: MusicSafetyConfig) -> list[dict[str, Any]]:
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    result = []
    for index in range(1, count):
        x, y, width, height, area = [int(value) for value in stats[index]]
        if config.min_component_area <= area <= config.max_component_area:
            result.append({"x": x, "y": y, "width": width, "height": height, "area": area, "cx": float(centroids[index][0]), "cy": float(centroids[index][1])})
    return result


def _compare_components(source_mask, candidate_mask, config):
    source = _components(source_mask, config)
    candidate = _components(candidate_mask, config)
    unmatched_candidate = set(range(len(candidate)))
    lost = 0
    shifts: list[float] = []
    findings: list[dict[str, Any]] = []
    diagonal = math.hypot(*source_mask.shape)
    match_limit = max(4.0, diagonal * 0.008)
    for item in source:
        best = None
        for index in unmatched_candidate:
            other = candidate[index]
            distance = math.hypot(item["cx"] - other["cx"], item["cy"] - other["cy"])
            area_ratio = min(item["area"], other["area"]) / max(item["area"], other["area"])
            if distance <= match_limit and area_ratio >= 0.35 and (best is None or distance < best[0]):
                best = (distance, index)
        if best is None:
            lost += 1
            findings.append(_finding("thin_component_loss", "medium", _region(item["x"], item["y"], item["width"], item["height"], source_mask.shape), {"area": item["area"]}))
        else:
            shifts.append(best[0])
            unmatched_candidate.remove(best[1])
            if best[0] >= config.component_shift_review_pixels:
                findings.append(_finding("component_shift", "medium", _region(item["x"], item["y"], item["width"], item["height"], source_mask.shape), {"distancePixels": round(best[0], 6)}))
    for index in sorted(unmatched_candidate):
        item = candidate[index]
        findings.append(_finding("thin_component_invention", "medium", _region(item["x"], item["y"], item["width"], item["height"], source_mask.shape), {"area": item["area"]}))
    metrics = {
        "sourceComponentCount": len(source),
        "candidateComponentCount": len(candidate),
        "lostComponentCount": lost,
        "inventedComponentCount": len(unmatched_candidate),
        "lossFraction": round(lost / max(1, len(source)), 8),
        "inventionFraction": round(len(unmatched_candidate) / max(1, len(source)), 8),
        "maxMatchedShiftPixels": round(max(shifts, default=0.0), 6),
        "meanMatchedShiftPixels": round(float(np.mean(shifts)) if shifts else 0.0, 6),
    }
    return metrics, findings


def _regional_findings(source, candidate, config):
    findings = []
    height, width = source.shape
    for row in range(config.region_grid_rows):
        y0 = height * row // config.region_grid_rows
        y1 = height * (row + 1) // config.region_grid_rows
        for column in range(config.region_grid_columns):
            x0 = width * column // config.region_grid_columns
            x1 = width * (column + 1) // config.region_grid_columns
            source_tile = source[y0:y1, x0:x1]
            candidate_tile = candidate[y0:y1, x0:x1]
            base = int(np.count_nonzero(source_tile))
            loss = int(np.count_nonzero(source_tile & ~candidate_tile))
            invention = int(np.count_nonzero(candidate_tile & ~source_tile))
            if base and loss / base >= config.symbol_loss_review_fraction:
                findings.append(_finding("regional_symbol_loss", "medium", _region(x0, y0, x1 - x0, y1 - y0, source.shape), {"fraction": round(loss / base, 8)}))
            if base and invention / base >= config.symbol_invention_review_fraction:
                findings.append(_finding("regional_symbol_invention", "medium", _region(x0, y0, x1 - x0, y1 - y0, source.shape), {"fraction": round(invention / base, 8)}))
    return findings


def _validate_candidate_manifest(manifest, source_digest, candidate_digest):
    if manifest is None:
        return []
    findings = []
    if ((manifest.get("sourceDigest") or {}).get("value")) != source_digest:
        findings.append(_finding("candidate_manifest_source_digest_mismatch", "critical", None, {}))
    if ((((manifest.get("candidate") or {}).get("digest") or {}).get("value")) != candidate_digest):
        findings.append(_finding("candidate_manifest_digest_mismatch", "critical", None, {}))
    if ((manifest.get("candidate") or {}).get("teacherApproved")) is not False:
        findings.append(_finding("candidate_manifest_approval_boundary_invalid", "critical", None, {}))
    return findings


def _classify_metric(value, review_threshold, reject_threshold, code, review, reject):
    if value >= reject_threshold:
        reject.append(f"{code}_severe")
    elif value >= review_threshold:
        review.append(f"{code}_detected")


def _risk_score(geometry, symbols, components, registration, verdict):
    score = 0.0
    score += min(1.0, geometry["staff"]["lineBreakFraction"] * 10) * 20
    score += min(1.0, geometry["tab"]["lineBreakFraction"] * 10) * 20
    score += min(1.0, symbols["lossFraction"] * 8) * 20
    score += min(1.0, symbols["inventionFraction"] * 8) * 15
    score += min(1.0, components["lossFraction"] * 2) * 10
    score += min(1.0, components["inventionFraction"] * 2) * 10
    if not registration["reliable"]:
        score += 5
    if verdict == "reject":
        score = max(score, 80)
    elif verdict == "review_required":
        score = max(score, 30)
    return round(min(100.0, score), 6)


def _finding(code: str, severity: str, region: dict[str, Any] | None, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"code": code, "severity": severity, "region": region, "evidence": evidence, "semanticCertainty": "not_claimed"}


def _region(x: int, y: int, width: int, height: int, shape: tuple[int, int]) -> dict[str, Any]:
    image_h, image_w = shape
    return {"x": max(0, x), "y": max(0, y), "width": max(1, min(width, image_w - max(0, x))), "height": max(1, min(height, image_h - max(0, y))), "normalized": {"x": round(max(0, x) / image_w, 8), "y": round(max(0, y) / image_h, 8), "width": round(max(1, width) / image_w, 8), "height": round(max(1, height) / image_h, 8)}}


def _bounding_region(mask: np.ndarray, shape: tuple[int, int]) -> dict[str, Any] | None:
    ys, xs = np.where(mask)
    if not xs.size:
        return None
    return _region(int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1), shape)


def _safe_name(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    normalized = value.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    return name or fallback


def _report_id(source_digest: str, candidate_digest: str, config_digest: str, version: str) -> str:
    raw = "|".join((source_digest, candidate_digest, config_digest, version)).encode("ascii")
    return "safety-report:" + hashlib.sha256(raw).hexdigest()


__all__ = [
    "MusicSafetyConfig",
    "MusicSafetyValidationError",
    "SCHEMA_VERSION",
    "VALIDATOR_VERSION",
    "compare_candidate_reports",
    "record_teacher_review",
    "validate_candidate",
]
