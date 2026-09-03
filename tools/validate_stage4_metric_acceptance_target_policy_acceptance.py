from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_metric_acceptance_target_policy_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    summarize_metric_acceptance_target_policy_acceptance,
    validate_metric_acceptance_target_policy_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"
CANDIDATE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-candidate.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    try:
        summary = summarize_metric_acceptance_target_policy_acceptance(load(ACCEPTANCE), load(CANDIDATE))
    except Exception as exc:
        print(f"Stage 4 metric-policy acceptance INVALID: {exc}", file=sys.stderr)
        return 1
    print("Stage 4 metric-policy acceptance VALID")
    print(f"- acceptance digest: {ACCEPTANCE_CANONICAL_SHA256}")
    print("- metric target policy accepted: true")
    print("- remaining readiness blocker: no_real_held_out_evaluation_evidence_is_accepted")
    print("- held-out evaluation authorized: false")
    print("- Stage 4 PASS: false")
    print("- Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
