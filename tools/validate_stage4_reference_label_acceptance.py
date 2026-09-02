from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_reference_label_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    ACCEPTANCE_DECISION,
    summarize_reference_label_acceptance,
    validate_reference_label_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (ACCEPTANCE, COMPLETION, WORKFLOW):
        require(path.exists(), f"required Stage 4 reference acceptance input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    try:
        acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
        completion = json.loads(COMPLETION.read_text(encoding="utf-8"))
        validated = validate_reference_label_acceptance(acceptance, completion)
        summary = summarize_reference_label_acceptance(validated, completion)
    except Exception as exc:
        print("Stage 4 reference-label acceptance validation: FAIL", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(validated.get("decision") == ACCEPTANCE_DECISION, "reference bundle decision is not acceptance")
    require(summary.get("acceptanceDigest", {}).get("value") == ACCEPTANCE_CANONICAL_SHA256, "acceptance digest drifted")
    require(summary.get("recordCount") == 42, "accepted reference record count drifted")
    require(summary.get("referenceBundleAccepted") is True, "real reference bundle was not accepted")
    require(summary.get("candidateDerivationEligible") is True, "accepted development bundle is not derivation eligible")
    require(summary.get("realDataCalibrationExecutionAuthorized") is False, "acceptance improperly authorized calibration execution")
    require(summary.get("heldOutIncluded") is False, "held-out evidence entered development acceptance")
    require(summary.get("stage4ExitPass") is False, "reference acceptance self-authorized Stage 4 PASS")
    require(summary.get("stage5EntryAuthorized") is False, "reference acceptance self-authorized Stage 5")
    require(
        "python tools/validate_stage4_reference_label_acceptance.py" in workflow,
        "repository validation does not run Stage 4 reference-label acceptance validator",
    )

    if failures:
        print("Stage 4 reference-label acceptance validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 reference-label acceptance validation: PASS")
    print(f"- decision: {ACCEPTANCE_DECISION}")
    print(f"- acceptance digest: {ACCEPTANCE_CANONICAL_SHA256}")
    print("- accepted bundle: 42 human-reviewed development labels")
    print("- candidate derivation: eligible after separate execution authorization")
    print("- real calibration execution: NOT AUTHORIZED")
    print("- held-out tuning: false / Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
