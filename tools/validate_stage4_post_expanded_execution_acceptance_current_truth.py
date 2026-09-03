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
from st_score_restore.stage4_exit_readiness import (  # noqa: E402
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
    Stage4ReadinessInput,
    evaluate_stage4_exit_readiness,
)

OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_EXPANDED_EXECUTION_ACCEPTANCE_CURRENT_TRUTH.json"
ACCEPTANCE = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
EXECUTION = ROOT / "evidence/stage4/calibration/expanded-real-development-execution.v1.json"

EXPECTED_MAIN = "a6493f6501d133a1b646046062489fe0a65d2991"
EXPECTED_RUN_ID = 33763391302
EXPECTED_RUN_NUMBER = 370
EXPECTED_BLOCKERS = {BLOCK_NO_HELDOUT_EVIDENCE, BLOCK_NO_METRIC_TARGET_POLICY}


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []
    for path in (OVERLAY, ACCEPTANCE, EXECUTION):
        require(path.exists(), f"required current-truth input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    overlay = load(OVERLAY)
    acceptance = load(ACCEPTANCE)
    execution = load(EXECUTION)
    accepted = validate_expanded_execution_evidence_acceptance(acceptance, execution)

    checkpoint = overlay.get("production_checkpoint", {})
    require(checkpoint.get("main_sha") == EXPECTED_MAIN, "current-truth main SHA drifted", failures)
    require(checkpoint.get("merge_pr") == 138, "current-truth PR checkpoint drifted", failures)
    require(checkpoint.get("postmerge_ci_run_id") == EXPECTED_RUN_ID, "current-truth Run ID drifted", failures)
    require(checkpoint.get("postmerge_ci_run_number") == EXPECTED_RUN_NUMBER, "current-truth Run number drifted", failures)
    require(checkpoint.get("postmerge_ci_status") == "success_python_3_11_and_3_12", "postmerge CI is not recorded green", failures)

    evidence = overlay.get("accepted_execution_evidence", {})
    require(evidence.get("acceptance_digest") == ACCEPTANCE_CANONICAL_SHA256, "acceptance digest drifted", failures)
    require(evidence.get("execution_evidence_accepted") is True, "development execution evidence acceptance missing", failures)
    require(evidence.get("candidate_derived_count") == 0, "current truth invented a threshold candidate", failures)
    require(evidence.get("measured_record_count") == 30, "measured record count drifted", failures)
    require(evidence.get("not_applicable_record_count") == 19, "not-applicable record count drifted", failures)
    require(accepted.get("assertions", {}).get("executionEvidenceAccepted") is True, "acceptance artifact is not effective", failures)

    calibration = overlay.get("calibration_state", {})
    require(calibration.get("real_development_calibration_executed") is True, "execution state regressed", failures)
    require(calibration.get("thresholds_calibrated") is False, "thresholds were falsely marked calibrated", failures)
    require(calibration.get("resource_limits_calibrated") is False, "resources were falsely marked calibrated", failures)
    require(calibration.get("candidate_thresholds_accepted") is False, "candidate thresholds were falsely accepted", failures)
    require(calibration.get("production_configuration_state") == "uncalibrated_engineering_defaults", "production configuration state drifted", failures)

    held_out = overlay.get("held_out", {})
    require(held_out.get("evaluation_authorized") is False, "held-out evaluation was prematurely authorized", failures)
    require(held_out.get("evaluation_used") is False, "held-out evaluation was prematurely used", failures)
    require(held_out.get("tuning_used") is False, "held-out tuning was used", failures)
    require(overlay.get("metric_policy", {}).get("acceptance_target_policy_accepted") is False, "metric policy was prematurely accepted", failures)

    readiness = evaluate_stage4_exit_readiness(
        Stage4ReadinessInput(
            safety_calibration_artifact_count=3,
            accepted_real_reference_bundle_count=1,
            accepted_real_development_evidence_count=1,
            accepted_real_held_out_evaluation_evidence_count=0,
            accepted_metric_target_policy=False,
            held_out_tuning_used=False,
            source_family_leakage_count=0,
            historical_evidence_immutable=True,
            real_or_derivative_bytes_in_ordinary_git=False,
            production_threshold_change_authorized=False,
            production_resource_limit_change_authorized=False,
        )
    )
    require(readiness.get("decision") == "NOT_READY", "Stage 4 unexpectedly became ready", failures)
    require(set(readiness.get("blockerCodes", [])) == EXPECTED_BLOCKERS, "post-acceptance blocker set drifted", failures)
    require(readiness.get("blockerCount") == 2, "post-acceptance blocker count must be two", failures)

    overlay_readiness = overlay.get("readiness", {})
    require(overlay_readiness.get("accepted_real_development_evidence_count") == 1, "overlay lost accepted development evidence", failures)
    require(set(overlay_readiness.get("remaining_blocker_codes", [])) == EXPECTED_BLOCKERS, "overlay blocker set drifted", failures)
    require(overlay_readiness.get("remaining_blocker_count") == 2, "overlay blocker count drifted", failures)

    assertions = overlay.get("assertions", {})
    require(assertions.get("development_evidence_blocker_resolved") is True, "development evidence blocker was not resolved", failures)
    require(assertions.get("held_out_evaluation_authorized") is False, "held-out authorization boundary crossed", failures)
    require(assertions.get("production_threshold_changes_authorized") is False, "production threshold changes were authorized", failures)
    require(assertions.get("production_resource_limit_changes_authorized") is False, "production resource changes were authorized", failures)
    require(assertions.get("stage4_exit_pass") is False, "Stage 4 PASS was self-authorized", failures)
    require(assertions.get("stage5_entry_authorized") is False, "Stage 5 entry was self-authorized", failures)

    if failures:
        print("Stage 4 post-expanded-execution-acceptance current truth: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-expanded-execution-acceptance current truth: PASS")
    print(f"- production checkpoint: PR #138 / main {EXPECTED_MAIN} / Run #{EXPECTED_RUN_NUMBER}")
    print("- real development execution evidence: accepted")
    print("- execution outcome: 0 candidates / 6 abstained / 1 not_applicable")
    print("- readiness: NOT_READY / 2 blockers")
    print(f"  - {BLOCK_NO_HELDOUT_EVIDENCE}")
    print(f"  - {BLOCK_NO_METRIC_TARGET_POLICY}")
    print("- thresholds/resources: uncalibrated_engineering_defaults")
    print("- held-out evaluation: not authorized / Stage 4 PASS: false / Stage 5: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
