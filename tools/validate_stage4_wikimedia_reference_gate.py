from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_wikimedia_reference_gate import (
    EXPECTED_REVIEW_COUNT,
    Stage4WikimediaReferenceGateError,
    build_wikimedia_reference_completion_candidate,
    validate_wikimedia_review_work_package,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"


def main() -> int:
    failures: list[str] = []

    if not WORK_PACKAGE.exists():
        print("Stage 4 Wikimedia reference gate validation: FAIL", file=sys.stderr)
        print("- Wikimedia work package is missing", file=sys.stderr)
        return 1

    package_raw = json.loads(WORK_PACKAGE.read_text(encoding="utf-8"))
    try:
        package = validate_wikimedia_review_work_package(package_raw)
    except Stage4WikimediaReferenceGateError as exc:
        failures.append(f"work-package rejection [{exc.code}]: {exc.message}")
    else:
        reviews = package["item"]["pages"][0]["reviews"]
        if len(reviews) != EXPECTED_REVIEW_COUNT:
            failures.append("Wikimedia work package no longer has exactly seven review slots")

    try:
        build_wikimedia_reference_completion_candidate(package_raw, [])
    except Stage4WikimediaReferenceGateError as exc:
        if exc.code != "human_labels_incomplete":
            failures.append(f"empty external review input failed for unexpected reason: {exc.code}")
    else:
        failures.append("reference completion became possible without seven external human labels")

    if failures:
        print("Stage 4 Wikimedia reference gate validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 Wikimedia reference gate validation: PASS")
    print("- committed work package remains pristine / awaiting_human_labels")
    print("- exact external human rows required: 7")
    print("- reference acceptance: false / execution authorization: false")
    print("- held-out development use: false / Stage 5: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
