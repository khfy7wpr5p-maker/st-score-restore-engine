"""P4.10 localizer-v3.1 development candidate-ceiling wrapper.

Patches the pinned v3 runner with two source-independent development changes:
1) periodic five-line projection staff hypotheses when strict projection returns <8 staffs;
2) an additional -0.75 staff-space horizontal candidate hypothesis.

P4.9 is spent holdout evidence and is reused only for development diagnosis.
This runner cannot qualify the detector or authorize Stage 11/production.
"""
from __future__ import annotations

import urllib.request

PINNED_V3_COMMIT = "3f9b6594b802e2a385a2466cfaee6c7d63f232d9"
URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + PINNED_V3_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_10_localizer_v3_candidate_ceiling.py"
)

PERIODIC_FN = r'''
def periodic_projection_staffs(gray: np.ndarray) -> List[Dict[str, Any]]:
    height, width = gray.shape[:2]
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel_len = max(40, int(round(0.025 * width)))
    horizontal = cv2.morphologyEx(
        ink,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1)),
    )
    row_support = np.count_nonzero(horizontal > 0, axis=1).astype(float) / float(width)
    pooled = np.maximum.reduce([np.roll(row_support, d) for d in (-1, 0, 1)])

    min_spacing = max(7, int(round(0.004 * height)))
    max_spacing = min(18, max(min_spacing, int(round(0.012 * height))))
    found = []

    for spacing in range(min_spacing, max_spacing + 1):
        top_start = max(20, 2 * spacing)
        top_stop = height - max(20, 6 * spacing)
        for y0 in range(top_start, top_stop):
            values = [float(pooled[y0 + k * spacing]) for k in range(5)]
            support = float(np.mean(values))
            if support < 0.12:
                continue
            if sum(v >= 0.06 for v in values) < 4:
                continue
            found.append({
                "lines": [float(y0 + k * spacing) for k in range(5)],
                "spacing": float(spacing),
                "source": "periodic_projection",
                "support": support,
                "gapCv": 0.0,
            })

    found.sort(key=lambda s: (-float(s["support"]), -float(s["spacing"])))
    selected = []
    for staff in found:
        center = float(np.mean(staff["lines"]))
        spacing = float(staff["spacing"])
        duplicate = False
        for existing in selected:
            ec = float(np.mean(existing["lines"]))
            es = float(existing["spacing"])
            if abs(center - ec) < 2.3 * max(spacing, es):
                duplicate = True
                break
        if not duplicate:
            selected.append(staff)
        if len(selected) >= 20:
            break
    return sorted(selected, key=lambda s: float(np.mean(s["lines"])))
'''

NEW_SELECT = r'''
def select_staffs(gray: np.ndarray, p45) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    height = int(gray.shape[0])
    primary = []
    for raw in p45.detect_staffs(gray):
        item = dict(raw)
        item["source"] = "p45"
        if sane_staff(item, height):
            primary.append(item)
    if len(primary) >= 3:
        return primary, {
            "path": "p45_sane",
            "p45Sane": len(primary),
            "projectionFallback": 0,
            "periodicProjection": 0,
        }

    fallback = strict_projection_staffs(gray)
    periodic = []
    if len(fallback) < 8:
        periodic = periodic_projection_staffs(gray)

    combined = [*fallback, *periodic]
    return combined, {
        "path": "projection_v3_1_fallback",
        "p45Sane": len(primary),
        "projectionFallback": len(fallback),
        "periodicProjection": len(periodic),
    }
'''


def replace_function(source: str, name: str, replacement: str, next_name: str) -> str:
    start_marker = f"def {name}("
    next_marker = f"def {next_name}("
    start = source.index(start_marker)
    end = source.index(next_marker, start)
    return source[:start] + replacement.strip() + "\n\n" + source[end:]


def main() -> None:
    source = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")

    if source.count("def select_staffs(") != 1:
        raise RuntimeError("Unexpected v3 select_staffs layout")
    if source.count("for x_offset_spaces in (0.0, 1.25):") != 1:
        raise RuntimeError("Unexpected v3 x-offset layout")
    if source.count("_P4_10_LOCALIZER_V3_DEV_DIAGNOSTIC") != 1:
        raise RuntimeError("Unexpected v3 output-folder layout")

    insert_at = source.index("def select_staffs(")
    patched = source[:insert_at] + PERIODIC_FN.strip() + "\n\n" + source[insert_at:]
    patched = replace_function(patched, "select_staffs", NEW_SELECT, "full_width_candidates")

    patched = patched.replace(
        "for x_offset_spaces in (0.0, 1.25):",
        "for x_offset_spaces in (-0.75, 0.0, 1.25):",
        1,
    )
    patched = patched.replace(
        "_P4_10_LOCALIZER_V3_DEV_DIAGNOSTIC",
        "_P4_10_LOCALIZER_V3_1_DEV_DIAGNOSTIC",
        1,
    )
    patched = patched.replace(
        "p4_10_localizer_v3_candidates_before_teacher.v1.json",
        "p4_10_localizer_v3_1_candidates_before_teacher.v1.json",
        1,
    )
    patched = patched.replace(
        "p4_10_localizer_v3_candidate_ceiling_result.v1.json",
        "p4_10_localizer_v3_1_candidate_ceiling_result.v1.json",
        1,
    )
    patched = patched.replace("LOCALIZER-V3", "LOCALIZER-V3.1")
    patched = patched.replace("localizer-v3", "localizer-v3_1")

    filename = "stage11_v2d_c_clef_p4_10_localizer_v3_1_candidate_ceiling_exec.py"
    compile(patched, filename, "exec")
    namespace = {"__name__": "__main__", "__file__": filename}
    exec(compile(patched, filename, "exec"), namespace, namespace)


if __name__ == "__main__":
    main()
