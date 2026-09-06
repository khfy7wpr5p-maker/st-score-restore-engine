from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage7_entry_authorization import summarize_stage7_entry_authorization

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    authorization = load("evidence/stage7/governance/stage7-entry-authorization.v1.json")
    stage6_truth = load("docs/live/ST_SCORE_RESTORE_STAGE6_FINAL_EXIT_CURRENT_TRUTH.json")
    summary = summarize_stage7_entry_authorization(authorization, stage6_truth)

    if summary["stage6ExitPass"] is not True:
        raise SystemExit("Stage 6 final PASS binding missing")
    if summary["stage7EntryEligible"] is not True or summary["stage7EntryAuthorized"] is not True:
        raise SystemExit("Stage 7 entry authorization missing")
    if summary["stage7Started"] is not True:
        raise SystemExit("Stage 7 start authorization missing")
    if summary["providerNeutralPreviewReadinessAuthorized"] is not True:
        raise SystemExit("Provider-neutral preview readiness scope missing")
    if summary["previewReleaseActivationAuthorized"] is not False:
        raise SystemExit("Preview release activation was over-authorized")
    if summary["stage8EntryAuthorized"] is not False:
        raise SystemExit("Stage 8 was over-authorized")

    print("Stage 7 entry authorization: VALID")
    print(f"- authorization digest: {summary['authorizationDigest']['value']}")
    print("- Stage 6: COMPLETE_PASS_PROVIDER_NEUTRAL")
    print("- Stage 7: eligible=true / authorized=true / started=true")
    print("- preview release activation: authorized=false")
    print("- Stage 8 entry: authorized=false")
    print(f"- next safe boundary: {summary['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
