from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage7_final_exit import validate_stage7_final_exit

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    result = validate_stage7_final_exit(
        load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json"),
        load("evidence/stage7/governance/stage7-entry-authorization.v1.json"),
        load("api/stage7-preview-contract.v1.json"),
        load("evidence/stage7/final-exit/stage7-final-exit-acceptance.v1.json"),
    )
    if result["stage7ExitPass"] is not True:
        raise SystemExit("Stage 7 final exit PASS missing")
    if result["stage8EntryEligible"] is not True:
        raise SystemExit("Stage 8 entry eligibility missing")
    if result["stage8EntryAuthorized"] is not False:
        raise SystemExit("Stage 8 entry was over-authorized")
    if result["previewReleaseActivationAuthorized"] is not False:
        raise SystemExit("Preview activation was over-authorized")
    print("Stage 7 final exit: VALID")
    print(f"- state: {result['stage7State']}")
    print(f"- acceptance digest: {result['acceptanceDigest']}")
    print("- Stage 8: eligible=true / authorized=false / started=false")
    print("- preview release activation: authorized=false")
    print(f"- next safe boundary: {result['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
