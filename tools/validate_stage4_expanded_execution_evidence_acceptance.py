from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from st_score_restore.stage4_expanded_execution_evidence_acceptance import (  # noqa: E402
    ACCEPTANCE_CANONICAL_SHA256,
    validate_expanded_execution_evidence_acceptance,
)

ACCEPTANCE_PATH = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
EXECUTION_PATH = ROOT / "evidence/stage4/calibration/expanded-real-development-execution.v1.json"


def main() -> int:
    acceptance = json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))
    execution = json.loads(EXECUTION_PATH.read_text(encoding="utf-8"))
    value = validate_expanded_execution_evidence_acceptance(acceptance, execution)
    assertions = value["assertions"]
    print("Stage 4 expanded development execution evidence acceptance validation: PASS")
    print(f"- acceptance digest: {ACCEPTANCE_CANONICAL_SHA256}")
    print("- execution evidence accepted: true")
    print("- real execution outcome: 0 candidates / 6 abstained / 1 not_applicable")
    print(f"- thresholds calibrated: {str(assertions['thresholdsCalibrated']).lower()}")
    print(f"- held-out evaluation authorized: {str(assertions['heldOutEvaluationAuthorized']).lower()}")
    print(f"- metric acceptance target policy applied: {str(assertions['metricAcceptanceTargetPolicyApplied']).lower()}")
    print(f"- Stage 4 exit PASS: {str(assertions['stage4ExitPass']).lower()}")
    print(f"- Stage 5 entry authorized: {str(assertions['stage5EntryAuthorized']).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
