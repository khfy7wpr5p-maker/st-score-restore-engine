from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage5_entry_authorization import summarize_stage5_entry_authorization

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    authorization = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
    stage4_final = load("evidence/stage4/final-exit/stage4-final-exit-acceptance.v1.json")
    stage4_truth = load("docs/live/ST_SCORE_RESTORE_STAGE4_FINAL_EXIT_CURRENT_TRUTH.json")
    summary = summarize_stage5_entry_authorization(authorization, stage4_final, stage4_truth)

    if summary["stage4ExitPass"] is not True:
        raise SystemExit("Stage 4 PASS binding missing")
    if summary["stage5EntryEligible"] is not True or summary["stage5EntryAuthorized"] is not True:
        raise SystemExit("Stage 5 entry authorization missing")
    if summary["stage5Started"] is not False:
        raise SystemExit("Stage 5 was started by entry authorization")

    print("Stage 5 entry governance authorization: VALID")
    print(f"- authorization digest: {summary['authorizationDigest']['value']}")
    print("- Stage 4: COMPLETE / PASS")
    print("- Stage 5: eligible=true / authorized=true / started=false")
    print(f"- next safe boundary: {summary['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
