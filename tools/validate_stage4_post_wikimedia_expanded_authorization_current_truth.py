from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

MAIN = "21787355ba2af2d3a1db596d05c2baca51005e7d"
PR = 132
RUN_ID = 33750473465
RUN_NUMBER = 354
AUTHORIZATION_DIGEST = "47027774b8f8258bcbe9ff633d58f9eb3e85edb4e83abf549facd778d6ecdad9"
WIKIMEDIA_ACCEPTANCE_DIGEST = "79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3"
BB_ACCEPTANCE_DIGEST = "88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c"
HELD_OUT_ID = "dataset.item.imslp82860-chopin-op69.v2"
READINESS_BLOCKERS = {
    "no_real_development_calibration_evidence_is_accepted",
    "no_real_held_out_evaluation_evidence_is_accepted",
    "no_stage4_metric_acceptance_target_policy_is_accepted",
}
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_WIKIMEDIA_EXPANDED_AUTHORIZATION_CURRENT_TRUTH.json"
AUTHORIZATION = ROOT / "evidence/stage4/governance/expanded-development-calibration-execution-authorization.v1.json"
ACCEPTANCE_OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_WIKIMEDIA_ACCEPTANCE_CURRENT_TRUTH.json"
RUNNER = ROOT / "src/st_score_restore/stage4_development_calibration_runner.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (OVERLAY, AUTHORIZATION, ACCEPTANCE_OVERLAY, RUNNER):
        require(path.exists(), f"required post-authorization current-truth input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    overlay = load(OVERLAY)
    checkpoint = overlay.get("production_checkpoint", {})
    require(checkpoint.get("main_sha") == MAIN, "expanded authorization overlay main SHA drifted")
    require(checkpoint.get("merge_pr") == PR, "expanded authorization overlay PR drifted")
    require(checkpoint.get("postmerge_ci_run_id") == RUN_ID, "expanded authorization overlay run ID drifted")
    require(checkpoint.get("postmerge_ci_run_number") == RUN_NUMBER, "expanded authorization overlay run number drifted")
    require(checkpoint.get("postmerge_ci_status") == "success_python_3_11_and_3_12", "expanded authorization overlay CI is not green")

    authorization = overlay.get("authorization", {})
    require(authorization.get("decision") == "AUTHORIZE_EXPANDED_REAL_DEVELOPMENT_CALIBRATION_EXECUTION", "expanded authorization decision drifted")
    require(authorization.get("authorization_digest") == AUTHORIZATION_DIGEST, "expanded authorization digest drifted")
    require(authorization.get("real_data_calibration_execution_authorized") is True, "expanded execution authorization is not true")
    require(authorization.get("real_data_calibration_executed") is False, "expanded execution was falsely claimed")

    scope = overlay.get("scope", {})
    require(scope.get("dataset_item_count") == 3, "expanded scope dataset item count drifted")
    require(scope.get("source_family_count") == 3, "expanded scope source-family count drifted")
    require(scope.get("reference_record_count") == 49, "expanded scope reference count drifted")
    require(scope.get("held_out_item_id") == HELD_OUT_ID, "expanded scope held-out identity drifted")
    require(scope.get("held_out_included") is False, "held-out data entered expanded development scope")
    require(scope.get("held_out_evaluation_authorized") is False, "held-out evaluation was prematurely authorized")
    require(scope.get("held_out_tuning_authorized") is False, "held-out tuning was authorized")
    require(scope.get("private_observation_metrics_required") is True, "private metrics are not required")
    require(scope.get("raw_observation_metrics_allowed_in_ordinary_git") is False, "raw private metrics were allowed in ordinary Git")

    bindings = overlay.get("reference_bindings", {})
    require(bindings.get("beethoven_barley_reference_record_count") == 42, "Beethoven+Barley reference count drifted")
    require(bindings.get("wikimedia_reference_record_count") == 7, "Wikimedia reference count drifted")
    require(bindings.get("beethoven_barley_acceptance_digest") == BB_ACCEPTANCE_DIGEST, "Beethoven+Barley acceptance binding drifted")
    require(bindings.get("wikimedia_acceptance_digest") == WIKIMEDIA_ACCEPTANCE_DIGEST, "Wikimedia acceptance binding drifted")

    assertions = overlay.get("assertions", {})
    require(assertions.get("reference_bundles_accepted") is True, "expanded overlay lost accepted reference bundles")
    require(assertions.get("candidate_derivation_authorized") is True, "expanded candidate derivation not authorized")
    require(assertions.get("development_evaluation_authorized") is True, "expanded development evaluation not authorized")
    require(assertions.get("calibration_execution_authorized") is True, "expanded calibration execution authorization not true")
    for key in (
        "calibration_executed",
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "thresholds_calibrated",
        "resource_limits_calibrated",
        "held_out_evaluation_authorized",
        "held_out_tuning_authorized",
        "external_export_authorized",
        "model_training_authorized",
        "publication_authorized",
        "stage4_exit_pass",
        "stage5_entry_authorized",
    ):
        require(assertions.get(key) is False, f"unsafe post-authorization flag became true: {key}")

    stage4 = overlay.get("stage4", {})
    require(stage4.get("state") == "ACTIVE_NOT_READY", "Stage 4 state drifted after authorization")
    require(set(stage4.get("readiness_blocker_codes", [])) == READINESS_BLOCKERS, "Stage 4 readiness blocker set drifted")
    require(stage4.get("next_dependency") == "expanded_development_calibration_runner_contract_and_custody_only_private_metrics", "post-authorization next dependency drifted")

    runner_truth = overlay.get("runner_current_truth", {})
    require(runner_truth.get("existing_runner_contract_version") == "0.2.0", "existing runner contract version drifted")
    require(runner_truth.get("existing_runner_scope") == "beethoven_barley_only", "existing runner scope drifted")
    require(runner_truth.get("existing_runner_reference_record_count") == 42, "existing runner record count drifted")
    require(runner_truth.get("expanded_runner_support_present") is False, "overlay falsely claims expanded runner support")

    auth_evidence = load(AUTHORIZATION)
    require(auth_evidence.get("decision") == "AUTHORIZE_EXPANDED_REAL_DEVELOPMENT_CALIBRATION_EXECUTION", "committed expanded authorization decision drifted")
    require(auth_evidence.get("scope", {}).get("datasetItemCount") == 3, "committed expanded authorization item count drifted")
    require(auth_evidence.get("scope", {}).get("sourceFamilyCount") == 3, "committed expanded authorization source-family count drifted")
    require(auth_evidence.get("scope", {}).get("referenceRecordCount") == 49, "committed expanded authorization reference count drifted")
    require(auth_evidence.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is True, "committed expanded authorization is not effective")
    require(auth_evidence.get("assertions", {}).get("realDataCalibrationExecuted") is False, "committed expanded authorization falsely claims execution")
    require(auth_evidence.get("assertions", {}).get("stage4ExitPass") is False, "committed expanded authorization improperly grants Stage 4 PASS")
    require(auth_evidence.get("assertions", {}).get("stage5EntryAuthorized") is False, "committed expanded authorization improperly opens Stage 5")

    historical_acceptance = load(ACCEPTANCE_OVERLAY)
    require(historical_acceptance.get("assertions", {}).get("calibration_execution_authorized") is False, "historical PR #130 acceptance overlay was retroactively rewritten")
    require(historical_acceptance.get("stage4", {}).get("next_dependency") == "separate_exact_wikimedia_expanded_development_calibration_execution_authorization", "historical PR #130 next dependency was retroactively rewritten")

    runner = RUNNER.read_text(encoding="utf-8")
    require('RUNNER_CONTRACT_VERSION = "0.2.0"' in runner, "existing private-metric runner version drifted")
    require("EXPECTED_RECORD_COUNT = 42" in runner, "existing runner no longer exposes the 42-record historical scope")
    require("BEETHOVEN_ID" in runner and "BARLEY_ID" in runner, "existing runner lost Beethoven+Barley scope tokens")
    require("WIKIMEDIA" not in runner, "expanded runner support appeared without a separate reviewed contract")

    if failures:
        print("Stage 4 post-Wikimedia expanded-authorization current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-Wikimedia expanded-authorization current-truth validation: PASS")
    print(f"- authorization: PR #{PR} / main {MAIN} / Run #{RUN_NUMBER}")
    print("- exact development scope: 3 items / 3 source families / 49 human reference records")
    print("- execution authorized: true / executed: false")
    print("- existing private-metric runner remains Beethoven+Barley-only / 42 records")
    print("- next dependency: expanded runner contract + custody-only private metrics")
    print("- held-out false / production changes false / Stage 4 NOT_READY / Stage 5 BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
