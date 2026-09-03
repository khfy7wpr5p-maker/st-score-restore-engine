from __future__ import annotations

import json
from pathlib import Path

from st_score_restore.stage5_start_authorization import summarize_stage5_start_authorization

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    authorization = load("evidence/stage5/governance/stage5-framework-start-authorization.v1.json")
    entry_authorization = load("evidence/stage5/governance/stage5-entry-authorization.v1.json")
    entry_truth = load("docs/live/ST_SCORE_RESTORE_STAGE5_ENTRY_AUTHORIZATION_CURRENT_TRUTH.json")
    summary = summarize_stage5_start_authorization(authorization, entry_authorization, entry_truth)

    if summary["stage5EntryAuthorized"] is not True:
        raise SystemExit("Stage 5 entry authorization missing")
    if summary["stage5FrameworkAuthorized"] is not True or summary["stage5Started"] is not True:
        raise SystemExit("Stage 5 framework/start authorization missing")
    if summary["teacherReviewInterfaceImplementationAuthorized"] is not True:
        raise SystemExit("Stage 5 implementation authorization missing")
    if summary["teacherReviewInterfaceExecutionAuthorized"] is not True:
        raise SystemExit("Stage 5 local execution authorization missing")
    if summary["productionDeploymentAuthorized"] is not False:
        raise SystemExit("Stage 5 start authorization over-authorized production deployment")
    if summary["stage6EntryAuthorized"] is not False:
        raise SystemExit("Stage 5 start authorization over-authorized Stage 6")

    print("Stage 5 framework/start authorization: VALID")
    print(f"- authorization digest: {summary['authorizationDigest']['value']}")
    print("- Stage 5: entry_authorized=true / framework_authorized=true / started=true")
    print("- teacher review UI implementation/execution: authorized for local Stage 5 work")
    print("- production deployment: false")
    print("- Stage 6 entry: false")
    print(f"- next safe boundary: {summary['nextSafeBoundary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
