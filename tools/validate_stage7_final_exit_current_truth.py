from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage7_final_exit_current_truth import validate_stage7_final_exit_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    result = validate_stage7_final_exit_current_truth(
        load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json"),
        load("evidence/stage7/governance/stage7-entry-authorization.v1.json"),
        load("api/stage7-preview-contract.v1.json"),
        load("evidence/stage7/final-exit/stage7-final-exit-acceptance.v1.json"),
        load("docs/live/ST_SCORE_RESTORE_STAGE7_FINAL_EXIT_CURRENT_TRUTH.json"),
    )
    print("Stage 7 final-exit current truth: VALID")
    print(f"- state: {result['stage7State']}")
    print(f"- current-truth digest: {result['currentTruthDigest']}")
    print("- Stage 8: eligible=true / authorized=false")
    print("- preview release activation: authorized=false")
    print("- provider selection: UNSELECTED")
    print("- production deployment: authorized=false")
    print(f"- next safe boundary: {result['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
