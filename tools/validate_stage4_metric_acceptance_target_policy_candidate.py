from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from st_score_restore.stage4_metric_acceptance_target_policy import (  # noqa: E402
    POLICY_CANDIDATE_CANONICAL_SHA256,
    summarize_metric_acceptance_target_policy_candidate,
    validate_metric_acceptance_target_policy_candidate,
)

POLICY = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-candidate.v1.json"


def main() -> int:
    raw = json.loads(POLICY.read_text(encoding="utf-8"))
    value = validate_metric_acceptance_target_policy_candidate(raw)
    summary = summarize_metric_acceptance_target_policy_candidate(value)
    print("Stage 4 metric acceptance-target policy candidate validation: PASS")
    print(f"- policy candidate digest: {POLICY_CANDIDATE_CANONICAL_SHA256}")
    print(f"- current mode: {summary['currentMode']}")
    print("- accepted real development evidence count: 1")
    print("- development candidate count: 0")
    print("- source-family leakage target: exactly 0")
    print("- held-out tuning/feedback: forbidden")
    print("- numerical performance target fabrication: forbidden")
    print("- future candidate-present mode: requires separate numeric-target addendum")
    print("- metric policy accepted: false / held-out evaluation authorized: false")
    print("- Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
