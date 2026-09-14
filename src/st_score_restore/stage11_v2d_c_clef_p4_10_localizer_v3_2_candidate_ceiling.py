"""P4.10 development-only C-clef localizer-v3.2 candidate-ceiling runner.

v3.2 pins the official v3.1 runner and changes only the no-primary-staff
fallback. If P4.5 yields no sane staff, a source-only staff-spacing prior is
estimated from long horizontal-line projection gaps before v3.1 lattice
scoring. All v3.1 candidate geometry and rescue hypotheses remain unchanged.

P4.9 is spent qualification evidence and is reused only as development data.
This runner cannot qualify the detector or authorize Stage 11/production.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
import statistics
import types
import urllib.request
from typing import Any, Dict, Tuple

import cv2
import numpy as np

V31_COMMIT = "670c1c0a4aa5670d066e769e43eddec49607021a"
V31_BLOB_SHA1 = "97183191f9265b53c19894827f987741bee9ce81"
V31_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + V31_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_10_localizer_v3_1_candidate_ceiling.py"
)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def grouped_runs(indices: np.ndarray):
    if indices.size == 0:
        return []
    out = []
    start = prev = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value > prev + 1:
            out.append((start, prev))
            start = value
        prev = value
    out.append((start, prev))
    return out


def source_spacing_hint_v32(gray: np.ndarray) -> Tuple[float | None, Dict[str, Any]]:
    """Infer a scale-aware staff spacing from source image horizontal lines."""
    height, width = gray.shape[:2]
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    x0 = max(0, int(round(0.04 * width)))
    x1 = min(width, int(round(0.96 * width)))
    central = ink[:, x0:x1]
    kernel_width = max(35, int(round(0.04 * width)))
    horizontal = cv2.morphologyEx(
        central,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1)),
    )
    projection = np.count_nonzero(horizontal > 0, axis=1).astype(float) / max(
        1, horizontal.shape[1]
    )

    peak = float(np.max(projection)) if projection.size else 0.0
    threshold = max(0.10, 0.40 * peak)
    runs = grouped_runs(np.flatnonzero(projection >= threshold))
    centers = np.asarray([(a + b) / 2.0 for a, b in runs], dtype=float)

    diagnostics: Dict[str, Any] = {
        "projectionPeak": peak,
        "projectionThreshold": threshold,
        "strongHorizontalRunCount": int(centers.size),
    }
    if centers.size < 6:
        diagnostics["status"] = "INSUFFICIENT_HORIZONTAL_RUNS"
        return None, diagnostics

    gaps = np.diff(centers)
    min_spacing = max(4.0, 0.0015 * float(height))
    max_spacing = max(20.0, 0.02 * float(height))
    valid = gaps[(gaps >= min_spacing) & (gaps <= max_spacing)]
    diagnostics.update(
        {
            "validGapCount": int(valid.size),
            "minSpacing": float(min_spacing),
            "maxSpacing": float(max_spacing),
        }
    )
    if valid.size < 4:
        diagnostics["status"] = "INSUFFICIENT_VALID_GAPS"
        return None, diagnostics

    bins = [float(round(float(value) / 2.0) * 2.0) for value in valid]
    mode, mode_count = Counter(bins).most_common(1)[0]
    tolerance = max(2.5, 0.10 * mode)
    cluster = valid[np.abs(valid - mode) <= tolerance]
    diagnostics.update(
        {
            "modeBin": float(mode),
            "modeCount": int(mode_count),
            "clusterCount": int(cluster.size),
            "clusterTolerance": float(tolerance),
        }
    )
    if cluster.size < 3:
        diagnostics["status"] = "INSUFFICIENT_MODE_SUPPORT"
        return None, diagnostics

    hint = float(np.median(cluster))
    diagnostics["status"] = "SOURCE_PROJECTION_HINT"
    diagnostics["spacingHint"] = hint
    return hint, diagnostics


def load_module_from_pinned_source(name: str, source: bytes, filename: str):
    module = types.ModuleType(name)
    module.__file__ = filename
    module.__dict__["__name__"] = name
    exec(compile(source.decode("utf-8"), filename, "exec"), module.__dict__)
    return module


def install_v32_staff_override(base, v31) -> None:
    """Install v3.1 first, then replace only sparse-staff selection."""
    v31.install_overrides(base)
    original_sane_staff = base.sane_staff

    def select_staffs_v32(gray: np.ndarray, p45):
        height = int(gray.shape[0])
        primary = []
        for raw in p45.detect_staffs(gray):
            item = dict(raw)
            item["source"] = "p45"
            if original_sane_staff(item, height):
                primary.append(item)

        if len(primary) >= 3:
            return primary, {
                "path": "p45_sane",
                "p45Sane": len(primary),
                "latticeFallback": 0,
            }

        spacing_hint = None
        spacing_source = "none"
        spacing_diagnostics: Dict[str, Any] = {}
        if primary:
            spacing_hint = float(
                statistics.median(float(staff["spacing"]) for staff in primary)
            )
            spacing_source = "p45_sane_median"
        else:
            spacing_hint, spacing_diagnostics = source_spacing_hint_v32(gray)
            if spacing_hint is not None and math.isfinite(spacing_hint):
                spacing_source = "source_horizontal_projection"

        fallback = v31.lattice_staffs_v31(gray, spacing_hint)
        merged = v31.merge_staffs_v31(primary, fallback)
        return merged, {
            "path": "p45_plus_spacing_prior_lattice",
            "p45Sane": len(primary),
            "spacingHint": spacing_hint,
            "spacingHintSource": spacing_source,
            "spacingDiagnostics": spacing_diagnostics,
            "latticeFallback": len(fallback),
            "merged": len(merged),
        }

    base.select_staffs = select_staffs_v32


def main() -> None:
    v31_source = urllib.request.urlopen(V31_URL, timeout=60).read()
    actual_v31_blob = git_blob_sha1(v31_source)
    if actual_v31_blob != V31_BLOB_SHA1:
        raise RuntimeError(f"Pinned v3.1 blob SHA mismatch: {actual_v31_blob}")
    v31 = load_module_from_pinned_source(
        "p410_localizer_v31",
        v31_source,
        "stage11_v2d_c_clef_p4_10_localizer_v3_1_candidate_ceiling.py",
    )

    base_source = urllib.request.urlopen(v31.BASE_URL, timeout=60).read()
    actual_base_blob = git_blob_sha1(base_source)
    if actual_base_blob != v31.BASE_BLOB_SHA1:
        raise RuntimeError(f"Pinned v3 base blob SHA mismatch: {actual_base_blob}")
    base = load_module_from_pinned_source(
        "p410_localizer_v3_base",
        base_source,
        "stage11_v2d_c_clef_p4_10_localizer_v3_candidate_ceiling.py",
    )

    install_v32_staff_override(base, v31)

    out = base.ROOT / "_P4_10_LOCALIZER_V3_2_DEV_DIAGNOSTIC"
    base.OUT = out
    base.RAW_PATH = out / "p4_10_localizer_v3_2_candidates_before_teacher.v1.json"
    base.RESULT_PATH = out / "p4_10_localizer_v3_2_candidate_ceiling_result.v1.json"
    base.main()

    result = json.loads(base.RESULT_PATH.read_text(encoding="utf-8"))
    result["schemaVersion"] = (
        "stage11.v2d.c-clef-p4_10-localizer-v3_2-candidate-ceiling-result.v1"
    )
    result["localizerVersion"] = "p4_10_localizer_v3_2"
    result["baseV31Commit"] = V31_COMMIT
    result["changes"] = [
        "retain frozen v3.1 candidate geometry and rescue hypotheses",
        "when no sane P4.5 staff exists, infer staff spacing from source-only long-horizontal-line projection gaps",
        "feed the inferred spacing prior into the existing v3.1 five-line lattice fallback",
    ]
    base.atomic_json(base.RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.10 LOCALIZER-V3.2 CANDIDATE CEILING COMPLETE")
    print("=" * 76)
    print("POOLED:", result.get("pooledCandidateCeiling"))
    print(
        "SUBTYPE:",
        {
            k: v.get("candidateRecall")
            for k, v in result.get("perSubtype", {}).items()
        },
    )
    print("CANDIDATE COUNT TOTAL:", result.get("candidateCountTotal"))
    print(
        "TARGET MET:",
        result.get("developmentCandidateCeilingTarget", {}).get("met"),
    )
    print("SAVED:", base.RESULT_PATH)
    print("SHA-256:", base.sha256_file(base.RESULT_PATH))
    print("detectorQualified: False — development candidate ceiling only")


if __name__ == "__main__":
    main()
