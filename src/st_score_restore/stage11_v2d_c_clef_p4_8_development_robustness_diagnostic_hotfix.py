"""P4.8 provenance-only hotfix wrapper.

Loads the immutable P4.8 diagnostic from commit a43dc0a..., corrects the single
mistyped frozen P4.6 source SHA suffix (...99e -> ...99a), then executes the
otherwise unchanged diagnostic. No detector thresholds, corpus paths, holdout
access rules, or evaluation logic are modified.
"""
from __future__ import annotations

import urllib.request

SOURCE_COMMIT = "a43dc0aab223d3e882c09889ddba326b41c594aa"
SOURCE_URL = (
    "https://raw.githubusercontent.com/khfy7wpr5p-maker/st-score-restore-engine/"
    + SOURCE_COMMIT
    + "/src/st_score_restore/stage11_v2d_c_clef_p4_8_development_robustness_diagnostic.py"
)

WRONG = "33e05d64cdfdb32952887daae08cf623eb337a0ae544c154be763c923337e99e"
CORRECT = "33e05d64cdfdb32952887daae08cf623eb337a0ae544c154be763c923337e99a"


def main() -> None:
    code = urllib.request.urlopen(SOURCE_URL, timeout=60).read().decode("utf-8")
    if code.count(WRONG) != 1:
        raise RuntimeError("P4.8 hotfix fail-closed: expected exactly one frozen-P4.6 SHA typo")
    if CORRECT in code:
        raise RuntimeError("P4.8 hotfix fail-closed: source unexpectedly already contains corrected SHA")

    patched = code.replace(WRONG, CORRECT, 1)
    print("P4.8 provenance hotfix applied: frozen P4.6 SHA ...99e -> ...99a")
    print("Detector thresholds/evaluation logic unchanged")
    print("P4.7 holdout remains inaccessible to this diagnostic")
    print()

    namespace = {
        "__name__": "__main__",
        "__file__": "stage11_v2d_c_clef_p4_8_development_robustness_diagnostic.py",
    }
    exec(compile(patched, namespace["__file__"], "exec"), namespace, namespace)


if __name__ == "__main__":
    main()
