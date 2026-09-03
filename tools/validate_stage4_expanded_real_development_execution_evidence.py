from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage4_expanded_real_development_execution_evidence import (
    EVIDENCE_CANONICAL_SHA256,
    PRIVATE_METRIC_BATCH_SHA256,
    Stage4ExpandedRealDevelopmentExecutionEvidenceError,
    validate_expanded_real_development_execution_evidence,
)

EVIDENCE_PATH = ROOT / "evidence/stage4/calibration/expanded-real-development-execution.v1.json"
HISTORICAL_EVIDENCE_PATH = ROOT / "evidence/stage4/calibration/real-development-execution.v1.json"
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"


def main() -> int:
    failures: list[str] = []
    for path, label in (
        (EVIDENCE_PATH, "expanded real development execution evidence"),
        (HISTORICAL_EVIDENCE_PATH, "historical Beethoven+Barley execution evidence"),
        (WORKFLOW_PATH, "repository validation workflow"),
    ):
        if not path.exists():
            failures.append(f"{label} is missing")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    try:
        value = validate_expanded_real_development_execution_evidence(
            json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        )
    except (ValueError, Stage4ExpandedRealDevelopmentExecutionEvidenceError) as exc:
        print("Stage 4 expanded real development execution evidence validation: FAIL", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    command = "python tools/validate_stage4_expanded_real_development_execution_evidence.py"
    if command not in workflow:
        failures.append("repository validation does not run expanded real execution evidence validator")

    rendered = EVIDENCE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        '"rawValue"',
        '"observationId"',
        '"datasetItemId"',
        '"sourceFamilyId"',
        '"provenanceReference"',
        '"possibleThreshold"',
        '"probableThreshold"',
        '"candidateManifest"',
    ):
        if forbidden in rendered:
            failures.append(f"expanded public evidence leaked private field: {forbidden}")

    forbidden_private_paths = [
        ROOT / "evidence/stage4/calibration/expanded-private-metric-batch.v1.json",
        ROOT / "evidence/stage4/calibration/candidate-derivation-private-reports.v1.json",
    ]
    for path in forbidden_private_paths:
        if path.exists():
            failures.append(f"private custody artifact entered ordinary Git: {path.relative_to(ROOT)}")

    assertions = value.get("assertions", {})
    if assertions.get("executionEvidenceAccepted") is not False:
        failures.append("expanded execution evidence was prematurely accepted")
    if assertions.get("stage4ExitPass") is not False or assertions.get("stage5EntryAuthorized") is not False:
        failures.append("expanded execution evidence prematurely advanced stage gates")

    if failures:
        print("Stage 4 expanded real development execution evidence validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 expanded real development execution evidence validation: PASS")
    print(f"- evidence digest: {EVIDENCE_CANONICAL_SHA256}")
    print(f"- private metric batch digest: {PRIVATE_METRIC_BATCH_SHA256}")
    print("- records: 49 total / 30 measured / 19 not-applicable / 2 measured source families")
    print("- candidate thresholds derived: 0 / abstained findings: 6 / not-applicable findings: 1")
    print("- private metric rows and candidate threshold values in ordinary Git: 0")
    print("- held-out tuning/evaluation: false")
    print("- execution evidence acceptance: false / Stage 4 PASS: false / Stage 5: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
