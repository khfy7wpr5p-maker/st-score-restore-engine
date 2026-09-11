"""P4.10 development-only C-clef localizer-v3.1 candidate-ceiling runner.

This wrapper pins the official v3 runner and changes only two development behaviors:
1) when P4.5 staff detection is sparse, preserve sane P4.5 staffs and augment them
   with a spacing-prior horizontal-lattice fallback instead of replacing them;
2) add one negative x-offset rescue hypothesis for glyph groups whose connected
   ink centroid is biased toward following notation.

P4.9 is spent qualification evidence and is reused only as development data.
This runner cannot qualify the detector or authorize Stage 11/production.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import types
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import cv2
import numpy as np

BASE_COMMIT = "3f9b6594b802e2a385a2466cfaee6c7d63f232d9"
BASE_BLOB_SHA1 = "9b48f81ceff7643876779926e09caa59cc967e55"
BASE_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + BASE_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_10_localizer_v3_candidate_ceiling.py"
)


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def grouped_runs(indices: np.ndarray) -> List[Tuple[int, int]]:
    if indices.size == 0:
        return []
    out: List[Tuple[int, int]] = []
    start = prev = int(indices[0])
    for raw in indices[1:]:
        value = int(raw)
        if value > prev + 1:
            out.append((start, prev))
            start = value
        prev = value
    out.append((start, prev))
    return out


def lattice_staffs_v31(gray: np.ndarray, spacing_hint: float | None) -> List[Dict[str, Any]]:
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
    projection = np.count_nonzero(horizontal > 0, axis=1).astype(float) / max(1, horizontal.shape[1])

    evidence = projection.copy()
    for delta in (-1, 1):
        shifted = np.roll(projection, delta)
        if delta < 0:
            shifted[delta:] = 0.0
        else:
            shifted[:delta] = 0.0
        evidence = np.maximum(evidence, shifted)

    min_spacing = max(4.0, 0.0015 * float(height))
    max_spacing = max(20.0, 0.02 * float(height))
    if spacing_hint is not None and math.isfinite(spacing_hint):
        low = max(min_spacing, 0.70 * spacing_hint)
        high = min(max_spacing, 1.35 * spacing_hint)
    else:
        low = max(min_spacing, 6.0)
        high = min(max_spacing, 14.0)

    hypotheses = []
    spacing = low
    while spacing <= high + 1e-9:
        if spacing_hint is not None and math.isfinite(spacing_hint):
            sigma = max(0.8, 0.20 * spacing_hint)
            spacing_prior = 0.75 + 0.25 * math.exp(-0.5 * ((spacing - spacing_hint) / sigma) ** 2)
        else:
            spacing_prior = 1.0

        max_y0 = int(height - 4.0 * spacing - 1.0)
        for y0 in range(max(0, max_y0)):
            ys = [int(round(y0 + k * spacing)) for k in range(5)]
            vals = [float(evidence[y]) for y in ys]
            if sum(value >= 0.03 for value in vals) < 4:
                continue
            base_score = float(np.mean(vals) + 0.60 * np.median(vals) + 0.15 * min(vals))
            hypotheses.append((base_score * spacing_prior, y0, float(spacing), vals))
        spacing += 0.25

    hypotheses.sort(reverse=True, key=lambda row: row[0])
    selected = []
    for candidate in hypotheses:
        score, y0, spacing, vals = candidate
        center = y0 + 2.0 * spacing
        if any(
            abs(center - (existing_y0 + 2.0 * existing_spacing)) <= 4.3 * max(spacing, existing_spacing)
            for _, existing_y0, existing_spacing, _ in selected
        ):
            continue
        selected.append(candidate)

    out = []
    for score, y0, spacing, vals in sorted(selected, key=lambda row: row[1]):
        center = y0 + 2.0 * spacing
        if center < 0.04 * height or center > 0.96 * height:
            continue
        out.append({
            "lines": [float(y0 + k * spacing) for k in range(5)],
            "spacing": float(spacing),
            "source": "spacing_prior_lattice",
            "support": float(score),
        })
    return out


def merge_staffs_v31(primary: Sequence[Dict[str, Any]], fallback: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for staff in [*primary, *fallback]:
        center = float(np.mean(np.asarray(staff["lines"], dtype=float)))
        spacing = float(staff["spacing"])
        duplicate_index = None
        for index, existing in enumerate(selected):
            existing_center = float(np.mean(np.asarray(existing["lines"], dtype=float)))
            existing_spacing = float(existing["spacing"])
            if (
                abs(center - existing_center) <= 1.25 * max(spacing, existing_spacing)
                and abs(spacing - existing_spacing) <= 0.35 * max(spacing, existing_spacing)
            ):
                duplicate_index = index
                break
        if duplicate_index is None:
            selected.append(dict(staff))
        else:
            old = selected[duplicate_index]
            if str(staff.get("source")) == "p45" and str(old.get("source")) != "p45":
                selected[duplicate_index] = dict(staff)
    return sorted(selected, key=lambda staff: float(np.mean(np.asarray(staff["lines"], dtype=float))))


def install_overrides(module) -> None:
    original_sane_staff = module.sane_staff

    def select_staffs_v31(gray: np.ndarray, p45):
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
        if primary:
            spacing_hint = float(statistics.median(float(staff["spacing"]) for staff in primary))
        fallback = lattice_staffs_v31(gray, spacing_hint)
        merged = merge_staffs_v31(primary, fallback)
        return merged, {
            "path": "p45_plus_spacing_prior_lattice",
            "p45Sane": len(primary),
            "spacingHint": spacing_hint,
            "latticeFallback": len(fallback),
            "merged": len(merged),
        }

    def full_width_candidates_v31(gray: np.ndarray, staffs: Sequence[Dict[str, Any]]):
        height, width = gray.shape[:2]
        _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        out = []
        for staff_index, staff in enumerate(staffs):
            lines = np.asarray(staff["lines"], dtype=float)
            spacing = float(staff["spacing"])
            y0 = max(0, int(math.floor(lines[0] - 2.8 * spacing)))
            y1 = min(height, int(math.ceil(lines[-1] + 2.8 * spacing)))
            if y1 <= y0:
                continue

            roi = ink[y0:y1, :].copy()
            line_width = max(7, int(round(2.2 * spacing)))
            horizontal = cv2.morphologyEx(
                roi,
                cv2.MORPH_OPEN,
                cv2.getStructuringElement(cv2.MORPH_RECT, (line_width, 1)),
            )
            removal = cv2.dilate(
                horizontal,
                cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(1, int(round(0.20 * spacing))))),
            )
            clean = roi.copy()
            clean[removal > 0] = 0

            x_profile = np.count_nonzero(clean > 0, axis=0)
            active = np.flatnonzero(x_profile >= max(1, int(round(0.20 * spacing))))
            runs = grouped_runs(active)
            groups: List[Tuple[int, int]] = []
            for a, b in runs:
                if (b - a + 1) < max(1.0, 0.10 * spacing):
                    continue
                if groups and (a - groups[-1][1]) <= 0.65 * spacing:
                    groups[-1] = (groups[-1][0], b)
                else:
                    groups.append((a, b))

            centers = []
            for a, b in groups:
                group_width = b - a + 1
                if group_width <= 5.0 * spacing:
                    centers.append((a + b) / 2.0)
                else:
                    x = a + 1.5 * spacing
                    while x <= b - 1.5 * spacing:
                        centers.append(float(x))
                        x += 1.25 * spacing

            dedup_centers = []
            for x in sorted(centers):
                if not dedup_centers or x - dedup_centers[-1] >= 0.35 * spacing:
                    dedup_centers.append(float(x))

            sizes = [(3.2, 5.2, "base")]
            if spacing < 10.0:
                sizes.append((3.0, 4.8, "small_spacing"))
            if spacing < 9.0 and (float(width) / spacing) > 180.0:
                sizes.append((3.4, 5.4, "dense_wide_page"))

            for base_x in dedup_centers:
                for x_offset_spaces in (-1.0, 0.0, 1.25):
                    x_center = base_x + x_offset_spaces * spacing
                    for line_index, anchor in ((4, "C1"), (2, "C3"), (1, "C4")):
                        y_center = float(lines[line_index])
                        for width_spaces, height_spaces, size_tag in sizes:
                            x1 = max(0.0, x_center - 0.5 * width_spaces * spacing)
                            x2 = min(float(width), x_center + 0.5 * width_spaces * spacing)
                            yy1 = max(0.0, y_center - 0.5 * height_spaces * spacing)
                            yy2 = min(float(height), y_center + 0.5 * height_spaces * spacing)
                            if x2 <= x1 or yy2 <= yy1:
                                continue
                            out.append({
                                "bbox": [x1, yy1, x2, yy2],
                                "staffIndex": int(staff_index),
                                "staffSource": str(staff.get("source", "unknown")),
                                "staffSpacing": spacing,
                                "anchor": anchor,
                                "xOffsetStaffSpaces": x_offset_spaces,
                                "sizeTag": size_tag,
                            })
        return out

    module.select_staffs = select_staffs_v31
    module.full_width_candidates = full_width_candidates_v31


def main() -> None:
    source = urllib.request.urlopen(BASE_URL, timeout=60).read()
    actual_blob = git_blob_sha1(source)
    if actual_blob != BASE_BLOB_SHA1:
        raise RuntimeError(f"Pinned v3 base blob SHA mismatch: {actual_blob}")

    module = types.ModuleType("p410_localizer_v3_base")
    module.__file__ = "stage11_v2d_c_clef_p4_10_localizer_v3_candidate_ceiling.py"
    module.__dict__["__name__"] = "p410_localizer_v3_base"
    exec(compile(source.decode("utf-8"), module.__file__, "exec"), module.__dict__)

    install_overrides(module)

    out = module.ROOT / "_P4_10_LOCALIZER_V3_1_DEV_DIAGNOSTIC"
    module.OUT = out
    module.RAW_PATH = out / "p4_10_localizer_v3_1_candidates_before_teacher.v1.json"
    module.RESULT_PATH = out / "p4_10_localizer_v3_1_candidate_ceiling_result.v1.json"

    module.main()

    result = json.loads(module.RESULT_PATH.read_text(encoding="utf-8"))
    result["schemaVersion"] = "stage11.v2d.c-clef-p4_10-localizer-v3_1-candidate-ceiling-result.v1"
    result["localizerVersion"] = "p4_10_localizer_v3_1"
    result["baseV3Commit"] = BASE_COMMIT
    result["changes"] = [
        "preserve sane P4.5 staffs when fallback is needed",
        "spacing-prior horizontal-lattice fallback",
        "negative x-offset rescue hypothesis -1.0 staff-space"
    ]
    module.atomic_json(module.RESULT_PATH, result)

    print()
    print("=" * 76)
    print("P4.10 LOCALIZER-V3.1 CANDIDATE CEILING COMPLETE")
    print("=" * 76)
    print("POOLED:", result.get("pooledCandidateCeiling"))
    print("SUBTYPE:", {k: v.get("candidateRecall") for k, v in result.get("perSubtype", {}).items()})
    print("CANDIDATE COUNT TOTAL:", result.get("candidateCountTotal"))
    print("TARGET MET:", result.get("developmentCandidateCeilingTarget", {}).get("met"))
    print("SAVED:", module.RESULT_PATH)
    print("SHA-256:", module.sha256_file(module.RESULT_PATH))
    print("detectorQualified: False — development candidate ceiling only")


if __name__ == "__main__":
    main()
