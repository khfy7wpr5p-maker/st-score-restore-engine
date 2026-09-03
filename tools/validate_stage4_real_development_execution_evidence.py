from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_real_development_execution_evidence import (
    EVIDENCE_CANONICAL_SHA256,
    PRIVATE_METRIC_BATCH_SHA256,
    Stage4RealDevelopmentExecutionEvidenceError,
    validate_real_development_execution_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "evidence/stage4/calibration/real-development-execution.v1.json"
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"


def main() -> int:
    failures: list[str] = []
    if not EVIDENCE_PATH.exists():
        failures.append("real development execution evidence is missing")
    if not WORKFLOW_PATH.exists():
        failures.append("repository validation workflow is missing")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    try:
        value = validate_real_development_execution_evidence(
            json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        )
    except (ValueError, Stage4RealDevelopmentExecutionEvidenceError) as exc:
        print("Stage 4 real development execution evidence validation: FAIL", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    if "python tools/validate_stage4_real_development_execution_evidence.py" not in workflow:
        print("Stage 4 real development execution evidence validation: FAIL", file=sys.stderr)
        print("- repository validation does not run the real execution evidence validator", file=sys.stderr)
        return 1

    print("Stage 4 real development execution evidence validation: PASS")
    print(f"- evidence digest: {EVIDENCE_CANONICAL_SHA256}")
    print(f"- private metric batch digest: {PRIVATE_METRIC_BATCH_SHA256}")
    print("- execution: real development / executed / abstained")
    print("- records: 42 total / 24 measured / 18 not-applicable")
    print("- candidate thresholds derived: 0")
    print("- held-out tuning/evaluation: false")
    print("- execution evidence acceptance: false / Stage 4 PASS: false / Stage 5: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
