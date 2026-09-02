from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage4_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    summarize_stage4_execution_authorization,
    validate_stage4_execution_authorization,
)
from st_score_restore.stage4_purpose_grants import APPROVED_GRANT_CANONICAL_SHA256
from st_score_restore.stage4_reference_label_acceptance import ACCEPTANCE_CANONICAL_SHA256

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json"
PURPOSE = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (AUTH, PURPOSE, ACCEPTANCE, COMPLETION):
        require(path.exists(), f"required Stage 4 authorization input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    auth_raw = json.loads(AUTH.read_text(encoding="utf-8"))
    purpose_raw = json.loads(PURPOSE.read_text(encoding="utf-8"))
    acceptance_raw = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    completion_raw = json.loads(COMPLETION.read_text(encoding="utf-8"))

    try:
        value = validate_stage4_execution_authorization(
            auth_raw, purpose_raw, acceptance_raw, completion_raw
        )
        summary = summarize_stage4_execution_authorization(
            auth_raw, purpose_raw, acceptance_raw, completion_raw
        )
    except Exception as exc:
        print(f"Stage 4 execution-authorization validation: FAIL\n- {exc}", file=sys.stderr)
        return 1

    require(canonical_sha256(value) == AUTHORIZATION_CANONICAL_SHA256, "authorization canonical digest drifted")
    require(value["purposeGrantDigest"]["value"] == APPROVED_GRANT_CANONICAL_SHA256, "purpose-grant binding drifted")
    require(value["referenceBundleAcceptanceDigest"]["value"] == ACCEPTANCE_CANONICAL_SHA256, "reference acceptance binding drifted")
    require(summary["realDataCalibrationExecutionAuthorized"] is True, "real development calibration execution is not authorized")
    require(summary["heldOutEvaluationAuthorized"] is False, "held-out evaluation was prematurely authorized")
    require(summary["heldOutTuningAuthorized"] is False, "held-out tuning was authorized")
    require(summary["productionThresholdChangeAuthorized"] is False, "production threshold changes were authorized")
    require(summary["productionResourceLimitChangeAuthorized"] is False, "production resource-limit changes were authorized")
    require(summary["stage4ExitPass"] is False, "authorization self-granted Stage 4 PASS")
    require(summary["stage5EntryAuthorized"] is False, "authorization self-granted Stage 5 entry")

    serialized = json.dumps(value, sort_keys=True)
    for forbidden in (
        '"possibleThreshold"',
        '"probableThreshold"',
        '"metricAcceptanceTarget"',
        '"acceptedMetricTargetPolicy"',
    ):
        require(forbidden not in serialized, f"execution authorization improperly embeds numerical calibration policy: {forbidden}")

    require(value["scope"]["privateObservationMetricsRequired"] is True, "private observation metrics are not required")
    require(value["scope"]["rawObservationMetricsAllowedInOrdinaryGit"] is False, "raw observation metrics were allowed in ordinary Git")
    require(value["assertions"]["realDataCalibrationExecuted"] is False, "authorization falsely claims execution already occurred")
    require(value["assertions"]["thresholdsCalibrated"] is False, "authorization falsely claims calibrated thresholds")
    require(value["assertions"]["resourceLimitsCalibrated"] is False, "authorization falsely claims calibrated resource limits")

    if failures:
        print("Stage 4 execution-authorization validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 execution-authorization validation: PASS")
    print(f"- authorization digest: {AUTHORIZATION_CANONICAL_SHA256}")
    print("- Beethoven + Barley: exact development-only real calibration execution authorized")
    print("- accepted 42-label reference bundle: bound")
    print("- private observation metrics: required / ordinary Git: forbidden")
    print("- held-out evaluation/tuning: NOT AUTHORIZED")
    print("- production threshold/resource changes: NOT AUTHORIZED")
    print("- Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
