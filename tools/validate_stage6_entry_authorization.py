from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_entry_authorization import summarize_stage6_entry_authorization

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    authorization = load("evidence/stage6/governance/stage6-entry-authorization.v1.json")
    stage5_final = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
    stage5_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")
    summary = summarize_stage6_entry_authorization(authorization, stage5_final, stage5_truth)

    if summary["stage5ExitPass"] is not True:
        raise SystemExit("Stage 5 PASS binding missing")
    if summary["stage6EntryEligible"] is not True or summary["stage6EntryAuthorized"] is not True:
        raise SystemExit("Stage 6 entry authorization missing")
    if summary["stage6Started"] is not True:
        raise SystemExit("Stage 6 governance start authorization missing")
    if summary["providerSpecificStage6WorkAuthorized"] is not False:
        raise SystemExit("Stage 6 entry authorization exceeded provider-neutral scope")

    print("Stage 6 entry governance authorization: VALID")
    print(f"- authorization digest: {summary['authorizationDigest']['value']}")
    print("- Stage 5: COMPLETE / PASS")
    print("- Stage 6: eligible=true / authorized=true / governance-started=true")
    print("- provider-specific Stage 6 work: authorized=false")
    print(f"- next safe boundary: {summary['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
