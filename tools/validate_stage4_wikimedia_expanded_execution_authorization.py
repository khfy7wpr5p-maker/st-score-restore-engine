from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage4_wikimedia_expanded_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    EXPECTED_ITEMS,
    summarize_wikimedia_expanded_execution_authorization,
    validate_wikimedia_expanded_execution_authorization,
)

AUTHORIZATION = ROOT / "evidence/stage4/governance/expanded-development-calibration-execution-authorization.v1.json"
BB_PURPOSE = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
BB_ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
BB_COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
WIKI_PURPOSE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/purpose-grant.v1.json"
WIKI_ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"
WIKI_COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
WIKI_WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    paths = (
        AUTHORIZATION,
        BB_PURPOSE,
        BB_ACCEPTANCE,
        BB_COMPLETION,
        WIKI_PURPOSE,
        WIKI_ACCEPTANCE,
        WIKI_COMPLETION,
        WIKI_WORK_PACKAGE,
    )
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.exists()]
    if missing:
        print("Stage 4 Wikimedia-expanded execution authorization validation: FAIL", file=sys.stderr)
        for path in missing:
            print(f"- missing required input: {path}", file=sys.stderr)
        return 1

    raw = load(AUTHORIZATION)
    try:
        validated = validate_wikimedia_expanded_execution_authorization(
            raw,
            load(BB_PURPOSE),
            load(BB_ACCEPTANCE),
            load(BB_COMPLETION),
            load(WIKI_PURPOSE),
            load(WIKI_ACCEPTANCE),
            load(WIKI_COMPLETION),
            load(WIKI_WORK_PACKAGE),
        )
        summary = summarize_wikimedia_expanded_execution_authorization(
            raw,
            load(BB_PURPOSE),
            load(BB_ACCEPTANCE),
            load(BB_COMPLETION),
            load(WIKI_PURPOSE),
            load(WIKI_ACCEPTANCE),
            load(WIKI_COMPLETION),
            load(WIKI_WORK_PACKAGE),
        )
    except Exception as error:
        print("Stage 4 Wikimedia-expanded execution authorization validation: FAIL", file=sys.stderr)
        print(f"- {error}", file=sys.stderr)
        return 1

    if canonical_sha256(validated) != AUTHORIZATION_CANONICAL_SHA256:
        print("Stage 4 Wikimedia-expanded execution authorization validation: FAIL", file=sys.stderr)
        print("- authorization canonical digest mismatch", file=sys.stderr)
        return 1
    if set(EXPECTED_ITEMS) != {
        "dataset.item.imslp799143-beethoven-op48-no3.v1",
        "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
        "dataset.item.wikimedia-guitar-technical-exercise-no1.v1",
    }:
        print("Stage 4 Wikimedia-expanded execution authorization validation: FAIL", file=sys.stderr)
        print("- exact three-item development scope drifted", file=sys.stderr)
        return 1
    if not summary.get("realDataCalibrationExecutionAuthorized"):
        print("Stage 4 Wikimedia-expanded execution authorization validation: FAIL", file=sys.stderr)
        print("- execution authorization did not become true", file=sys.stderr)
        return 1
    for key in (
        "realDataCalibrationExecuted",
        "heldOutEvaluationAuthorized",
        "heldOutTuningAuthorized",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        if summary.get(key) is not False:
            print("Stage 4 Wikimedia-expanded execution authorization validation: FAIL", file=sys.stderr)
            print(f"- unsafe downstream summary flag is not false: {key}", file=sys.stderr)
            return 1

    print("Stage 4 Wikimedia-expanded execution authorization validation: PASS")
    print(f"- authorization digest: {AUTHORIZATION_CANONICAL_SHA256}")
    print("- exact development scope: Beethoven + Barley + Wikimedia / 3 source families / 49 human reference records")
    print("- real development calibration execution authorized: true")
    print("- execution performed: false / held-out evaluation: false / production changes: false")
    print("- Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
