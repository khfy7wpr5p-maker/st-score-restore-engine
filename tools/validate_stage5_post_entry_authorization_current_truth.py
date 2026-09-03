from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage5_entry_current_truth import summarize_stage5_entry_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    overlay = load("docs/live/ST_SCORE_RESTORE_STAGE5_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
    authorization = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
    stage4_final = load("evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json")
    historical_stage4_truth = load("docs/live/ST_SCORE_RESTORE_STAGE4_FINAL_EXIT_CURRENT_TRUTH.json")

    summary = summarize_stage5_entry_current_truth(
        overlay,
        authorization,
        stage4_final,
        historical_stage4_truth,
    )

    historical_stage5 = historical_stage4_truth["stage5"]
    if historical_stage5["entry_authorized"] is not False or historical_stage5["started"] is not False:
        raise SystemExit("historical Stage 4 final current truth was retroactively rewritten")
    if summary["stage5EntryEligible"] is not True or summary["stage5EntryAuthorized"] is not True:
        raise SystemExit("production-effective Stage 5 entry authorization missing")
    if summary["stage5Started"] is not False:
        raise SystemExit("Stage 5 was started by current-truth alignment")
    if summary["stage6EntryAuthorized"] is not False:
        raise SystemExit("Stage 6 was prematurely authorized")

    print("Stage 5 post-entry current truth: VALID")
    print("- Stage 4: COMPLETE / PASS")
    print("- Stage 5: eligible=true / authorized=true / started=false")
    print("- historical Stage 4 final checkpoint: immutable")
    print(f"- next safe boundary: {summary['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
