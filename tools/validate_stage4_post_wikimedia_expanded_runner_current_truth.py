from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_WIKIMEDIA_EXPANDED_RUNNER_CURRENT_TRUTH.json"
RUNNER = ROOT / "src/st_score_restore/stage4_expanded_development_calibration_runner.py"
ANALYZER = ROOT / "src/st_score_restore/quality_analysis.py"
AUTHORIZATION = ROOT / "evidence/stage4/governance/expanded-development-calibration-execution-authorization.v1.json"

MAIN_SHA = "a594503fc4eee1c7d7172eec3cc35c4de38610d3"
PR_NUMBER = 134
RUN_ID = 33751772802
RUN_NUMBER = 358
AUTH_DIGEST = "47027774b8f8258bcbe9ff633d58f9eb3e85edb4e83abf549facd778d6ecdad9"
BLOCKERS = {
    "no_real_development_calibration_evidence_is_accepted",
    "no_real_held_out_evaluation_evidence_is_accepted",
    "no_stage4_metric_acceptance_target_policy_is_accepted",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (OVERLAY, RUNNER, ANALYZER, AUTHORIZATION):
        require(
            path.exists(),
            f"required expanded-runner current-truth input missing: {path.relative_to(ROOT)}",
        )
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    overlay = load(OVERLAY)
    checkpoint = overlay.get("production_checkpoint", {})
    require(checkpoint.get("main_sha") == MAIN_SHA, "expanded runner historical main SHA drifted")
    require(checkpoint.get("merge_pr") == PR_NUMBER, "expanded runner historical PR drifted")
    require(checkpoint.get("postmerge_ci_run_id") == RUN_ID, "expanded runner historical Run ID drifted")
    require(checkpoint.get("postmerge_ci_run_number") == RUN_NUMBER, "expanded runner historical Run number drifted")
    require(
        checkpoint.get("postmerge_ci_status") == "success_python_3_11_and_3_12",
        "expanded runner historical postmerge CI is not green",
    )
    require(
        checkpoint.get("role") == "historical_runner_introduction_checkpoint",
        "expanded runner checkpoint role drifted",
    )

    runner = overlay.get("runner", {})
    require(runner.get("contract_version") == "0.3.1", "expanded runner contract version drifted")
    require(runner.get("private_metric_schema_version") == "1.2.0", "expanded private metric schema drifted")
    require(runner.get("expanded_runner_support_present") is True, "expanded runner support is not present")
    require(runner.get("reference_record_count") == 49, "expanded runner reference count drifted")
    require(runner.get("measured_record_count") == 30, "expanded runner measured count drifted")
    require(runner.get("not_applicable_record_count") == 19, "expanded runner not-applicable count drifted")
    require(runner.get("measured_source_family_count") == 2, "expanded runner measured source-family count drifted")
    require(
        runner.get("wikimedia_source_png_measurable_metric_count") == 6,
        "Wikimedia source PNG measurable metric count drifted",
    )
    require(
        runner.get("wikimedia_source_png_compression_not_applicable") is True,
        "Wikimedia PNG compression applicability drifted",
    )
    require(
        runner.get("beethoven_pdf_derived_png_compression_not_applicable") is True,
        "Beethoven compression applicability drifted",
    )
    require(
        runner.get("barley_vector_metrics_not_applicable") is True,
        "Barley vector applicability drifted",
    )

    correction = overlay.get("applicability_correction", {})
    require(
        correction.get("supersedes_runner_contract_version") == "0.3.0",
        "expanded runner applicability correction predecessor drifted",
    )
    require(
        correction.get("reason_code")
        == "png_compression_metric_not_supported_by_quality_analyzer",
        "expanded runner applicability correction reason drifted",
    )
    require(correction.get("previous_measured_record_count") == 31, "previous measured count record drifted")
    require(correction.get("previous_not_applicable_record_count") == 18, "previous N/A count record drifted")
    require(correction.get("corrected_measured_record_count") == 30, "corrected measured count drifted")
    require(correction.get("corrected_not_applicable_record_count") == 19, "corrected N/A count drifted")
    require(correction.get("wikimedia_compression_status") == "not_applicable", "Wikimedia compression status correction drifted")
    require(
        correction.get("wikimedia_compression_reason")
        == "metric_not_applicable_to_png_derivative",
        "Wikimedia compression reason correction drifted",
    )
    for key in (
        "human_reference_truth_changed",
        "authorization_scope_changed",
        "held_out_scope_changed",
    ):
        require(correction.get(key) is False, f"applicability correction widened scope: {key}")

    authorization = overlay.get("authorization", {})
    require(authorization.get("authorization_digest") == AUTH_DIGEST, "expanded authorization digest drifted")
    require(
        authorization.get("expanded_development_calibration_execution_authorized") is True,
        "expanded calibration execution authorization lost",
    )

    execution = overlay.get("execution", {})
    require(execution.get("real_private_metric_batch_present") is False, "overlay falsely claims a real private metric batch")
    require(execution.get("real_development_calibration_executed") is False, "overlay falsely claims calibration execution")
    require(
        execution.get("real_development_calibration_evidence_accepted") is False,
        "overlay falsely claims accepted development evidence",
    )
    require(
        execution.get("raw_private_metrics_allowed_in_ordinary_git") is False,
        "overlay allows raw private metrics in ordinary Git",
    )
    require(
        execution.get("next_dependency")
        == "custody_only_real_private_metric_acquisition_and_expanded_development_calibration_execution",
        "expanded runner next dependency drifted",
    )

    held_out = overlay.get("held_out", {})
    require(
        held_out.get("dataset_item_id") == "dataset.item.imslp82860-chopin-op69.v2",
        "held-out identity drifted",
    )
    require(held_out.get("included") is False, "held-out entered expanded development scope")
    require(held_out.get("evaluation_authorized") is False, "held-out evaluation was prematurely authorized")
    require(held_out.get("tuning_authorized") is False, "held-out tuning was authorized")

    assertions = overlay.get("assertions", {})
    for key in (
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "thresholds_calibrated",
        "resource_limits_calibrated",
        "model_training_authorized",
        "publication_authorized",
        "stage4_exit_pass",
        "stage5_entry_authorized",
    ):
        require(
            assertions.get(key) is False,
            f"unsafe expanded runner current-truth flag became true: {key}",
        )

    stage4 = overlay.get("stage4", {})
    require(stage4.get("state") == "ACTIVE_NOT_READY", "Stage 4 state drifted")
    require(
        set(stage4.get("readiness_blocker_codes", [])) == BLOCKERS,
        "Stage 4 blocker set drifted",
    )

    runner_text = RUNNER.read_text(encoding="utf-8")
    for token in (
        'RUNNER_CONTRACT_VERSION = "0.3.1"',
        "EXPECTED_RECORD_COUNT = 49",
        "EXPECTED_MEASURED_RECORD_COUNT = 30",
        "EXPECTED_NOT_APPLICABLE_RECORD_COUNT = 19",
        "EXPECTED_MEASURED_SOURCE_FAMILY_COUNT = 2",
    ):
        require(token in runner_text, f"production expanded runner lost contract token: {token}")
    require(
        'item_id in {BEETHOVEN_ID, WIKIMEDIA_ID} and finding == "compression"'
        in runner_text,
        "expanded runner lost PNG compression abstention binding",
    )

    analyzer_text = ANALYZER.read_text(encoding="utf-8")
    require(
        'if kind != "jpeg" or min(gray.shape) < 24:' in analyzer_text,
        "quality analyzer no longer proves JPEG-only compression applicability",
    )

    auth = load(AUTHORIZATION)
    require(
        auth.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is True,
        "production authorization is not active",
    )
    require(
        auth.get("assertions", {}).get("realDataCalibrationExecuted") is False,
        "production authorization artifact was retroactively marked executed",
    )

    leaked_raw_value_files = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "evidence/stage4").rglob("*.json")
        if '"rawValue"' in path.read_text(encoding="utf-8")
    ]
    require(
        not leaked_raw_value_files,
        f"ordinary Git Stage 4 evidence contains raw private metric values: {leaked_raw_value_files}",
    )

    if failures:
        print("Stage 4 post-Wikimedia expanded-runner current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-Wikimedia expanded-runner current-truth validation: PASS")
    print(f"- historical introduction checkpoint: PR #{PR_NUMBER} / main {MAIN_SHA} / Run #{RUN_NUMBER}")
    print("- corrected expanded runner: v0.3.1 / 49 reference identities / 30 measured / 19 not_applicable")
    print("- Wikimedia PNG: 6 measurable / compression not_applicable")
    print("- measured source-family support: 2")
    print("- real private metrics: absent / calibration execution: false")
    print("- held-out excluded / production changes false / Stage 4 NOT_READY / Stage 5 BLOCKED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
