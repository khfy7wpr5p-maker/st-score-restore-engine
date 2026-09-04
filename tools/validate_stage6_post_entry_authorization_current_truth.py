from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage6_entry_current_truth import summarize_stage6_entry_current_truth

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    overlay = load("docs/live/ST_SCORE_RESTORE_STAGE6_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
    authorization = load("evidence/stage6/governance/stage6-entry-authorization.v1.json")
    stage5_final = load("evidence/stage5/final-exit/stage5-final-exit-acceptance.v1.json")
    stage5_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json")
    summary = summarize_stage6_entry_current_truth(overlay, authorization, stage5_final, stage5_truth)

    if summary["stage5State"] != "COMPLETE_PASS":
        raise SystemExit("Stage 5 COMPLETE/PASS binding missing")
    if summary["stage6EntryEligible"] is not True or summary["stage6EntryAuthorized"] is not True:
        raise SystemExit("Stage 6 entry current truth missing")
    if summary["stage6Started"] is not True:
        raise SystemExit("Stage 6 governance-start current truth missing")
    if summary["providerSpecificStage6WorkAuthorized"] is not False:
        raise SystemExit("Stage 6 current truth exceeded provider-neutral scope")
    if summary["stage7EntryAuthorized"] is not False:
        raise SystemExit("Stage 7 was prematurely authorized")

    print("Stage 6 post-entry current truth: VALID")
    print("- Stage 5: COMPLETE / PASS")
    print("- Stage 6: entry-authorized / governance-started / provider-neutral-only")
    print("- provider-specific Stage 6 work: authorized=false")
    print("- Stage 7: authorized=false")
    print(f"- next safe boundary: {summary['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
