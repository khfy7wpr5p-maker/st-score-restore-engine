"""Compatibility wrapper for P4.10 localizer-v2 candidate ceiling.

Fixes OpenCV HoughLinesP shape variance only:
- some builds return (N, 1, 4)
- others return (N, 4)

The pinned diagnostic logic remains otherwise unchanged.
"""
from __future__ import annotations

import urllib.request

PINNED_COMMIT = "ad4a7ba74f6265fc764d23aaeca24557c44a52dd"
URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + PINNED_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_10_localizer_v2_candidate_ceiling.py"
)

OLD = "        for raw in lines[:, 0, :]:\n"
NEW = (
    "        line_rows = np.asarray(lines).reshape(-1, 4)\n"
    "        for raw in line_rows:\n"
)


def main() -> None:
    source = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")
    count = source.count(OLD)
    if count != 1:
        raise RuntimeError(f"Expected exactly one HoughLinesP shape site, found {count}")

    patched = source.replace(OLD, NEW, 1)
    compile(patched, "stage11_v2d_c_clef_p4_10_localizer_v2_candidate_ceiling_compat_exec.py", "exec")

    namespace = {
        "__name__": "__main__",
        "__file__": "stage11_v2d_c_clef_p4_10_localizer_v2_candidate_ceiling_compat_exec.py",
    }
    exec(compile(patched, namespace["__file__"], "exec"), namespace, namespace)


if __name__ == "__main__":
    main()
