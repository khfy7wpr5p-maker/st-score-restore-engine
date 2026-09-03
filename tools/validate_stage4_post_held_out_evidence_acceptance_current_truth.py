from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_held_out_evaluation_evidence_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    POST_ACCEPTANCE_READINESS_DIGEST,
    validate_held_out_evaluation_evidence_acceptance,
)

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "docs/live/ST_SCORE_RESTORE_HELD_OUT_EVIDENCE_ACCEPTANCE_CURRENT_TRUTH.json"
ACCEPTANCE = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-acceptance.v1.json"
CANDIDATE = ROOT / "evidence/stage4/calibration/held-out-evaluation-evidence-candidate.v1.json"
AUTHORIZATION = ROOT / "evidence/stage4/governance/held-out-evaluation-evidence-review-authorization.v1.json"
STAGE3_EXECUTION = ROOT / "evidence/stage3/corpus/execution-evidence.v1.json"
STAGE3_EXIT_ACCEPTANCE = ROOT / "evidence/stage3/corpus/stage3-exit-acceptance.v1.json"
DEVELOPMENT_ACCEPTANCE = ROOT / "evidence/stage4/calibration/expanded-real-development-execution-acceptance.v1.json"
METRIC_POLICY_ACCEPTANCE = ROOT / "evidence/stage4/calibration/metric-acceptance-target-policy-acceptance.v1.json"

EXPECTED_MAIN = "25e89d1fbdc1cdd73dddaba82e34257ed3f220cb"
EXPECTED_EXACT_HEAD = "971c606c5ddee4f201df677c0c4f9b01a8040182"
EXPECTED_CANDIDATE_DIGEST = "45dc380effe34d7f35ec9af2f05f802eaca9194fa8a889d1aaefae87c5221219"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    for path in (
        OVERLAY,
        ACCEPTANCE,
        CANDIDATE,
        AUTHORIZATION,
        STAGE3_EXECUTION,
        STAGE3_EXIT_ACCEPTANCE,
        DEVELOPMENT_ACCEPTANCE,
        METRIC_POLICY_ACCEPTANCE,
    ):
        require(path.exists(), f"required current-truth input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    overlay = load(OVERLAY)
    acceptance = load(ACCEPTANCE)
    candidate = load(CANDIDATE)
    authorization = load(AUTHORIZATION)
    stage3 = load(STAGE3_EXECUTION)
    stage3_exit = load(STAGE3_EXIT_ACCEPTANCE)
    development = load(DEVELOPMENT_ACCEPTANCE)
    metric_policy = load(METRIC_POLICY_ACCEPTANCE)

    try:
        accepted = validate_held_out_evaluation_evidence_acceptance(
            acceptance,
            candidate,
            authorization,
            stage3,
            stage3_exit,
            development,
            metric_policy,
        )
    except Exception as exc:
        failures.append(f"held-out evidence acceptance no longer validates: {exc}")
        accepted = {}

    production = overlay.get("production_checkpoint", {})
    require(production.get("main_sha") == EXPECTED_MAIN, "PR146 production main SHA drifted", failures)
    require(production.get("merge_pr") == 146, "PR146 merge number drifted", failures)
    require(production.get("exact_head_sha") == EXPECTED_EXACT_HEAD, "PR146 exact head drifted", failures)
    require(
        production.get("exact_head_run") == {
            "run_number": 386,
            "run_id": 33774353423,
            "python_311": "success",
            "python_312": "success",
        },
        "PR146 exact-head CI checkpoint drifted",
        failures,
    )
    require(
        production.get("postmerge_run") == {
            "run_number": 387,
            "run_id": 33774503172,
            "python_311": "success",
            "python_312": "success",
        },
        "PR146 postmerge CI checkpoint drifted",
        failures,
    )

    evidence = overlay.get("accepted_held_out_evidence", {})
    require(evidence.get("decision") == "ACCEPT_STAGE4_HELD_OUT_EVALUATION_EVIDENCE", "held-out acceptance decision drifted", failures)
    require(evidence.get("acceptance_digest") == ACCEPTANCE_CANONICAL_SHA256, "held-out acceptance digest drifted", failures)
    require(evidence.get("evidence_candidate_digest") == EXPECTED_CANDIDATE_DIGEST, "held-out candidate digest drifted", failures)
    require(evidence.get("held_out_evaluation_evidence_accepted") is True, "held-out evidence is not recorded as accepted", failures)
    require(evidence.get("historical_candidate_rewritten") is False, "historical held-out candidate was marked rewritten", failures)
    require(accepted.get("assertions", {}).get("heldOutEvaluationEvidenceAccepted") is True, "validated acceptance is not effective", failures)
    require(candidate.get("assertions", {}).get("heldOutEvaluationEvidenceAccepted") is False, "historical candidate was retroactively rewritten", failures)

    scope = overlay.get("held_out_scope", {})
    require(scope.get("mode") == "zero_candidate_safe_abstention", "held-out mode drifted", failures)
    require(scope.get("new_held_out_execution_performed") is False, "overlay falsely claims a second held-out execution", failures)
    require(scope.get("candidate_derived_count") == 0, "held-out candidate count drifted", failures)
    require(scope.get("assessed_candidate_count") == 0, "held-out assessed count drifted", failures)
    require(scope.get("coverage_rate") == 0.0, "held-out coverage drifted", failures)
    for key in ("not_assessed_rate", "exact_match_rate", "false_negative_rate", "false_positive_rate"):
        require(scope.get(key) == "not_applicable", f"{key} must remain not_applicable", failures)
    require(scope.get("source_family_leakage_count") == 0, "source-family leakage detected", failures)
    require(scope.get("held_out_threshold_tuning_used") is False, "held-out tuning appeared", failures)
    require(scope.get("evaluation_fed_back_into_candidate") is False, "held-out evaluation feedback appeared", failures)

    readiness = overlay.get("stage4_readiness", {})
    require(readiness.get("decision") == "READY_FOR_FINAL_ACCEPTANCE_REVIEW", "Stage 4 is not final-review ready", failures)
    require(readiness.get("readiness_digest") == POST_ACCEPTANCE_READINESS_DIGEST, "readiness digest drifted", failures)
    require(readiness.get("readiness_prerequisites_satisfied") is True, "readiness prerequisites not satisfied", failures)
    require(readiness.get("blocker_count") == 0, "Stage 4 blocker count is not zero", failures)
    require(readiness.get("blocker_codes") == [], "Stage 4 blocker list is not empty", failures)
    require(readiness.get("final_governance_acceptance_still_required") is True, "final governance acceptance requirement disappeared", failures)
    require(
        readiness.get("next_safe_boundary") == "separate_explicit_stage4_final_exit_governance_acceptance",
        "next safe boundary drifted",
        failures,
    )

    calibration = overlay.get("calibration_and_production_state", {})
    require(calibration.get("candidate_thresholds_accepted") is False, "candidate thresholds became accepted", failures)
    require(calibration.get("thresholds_calibrated") is False, "thresholds became calibrated", failures)
    require(calibration.get("resource_limits_calibrated") is False, "resource limits became calibrated", failures)
    require(calibration.get("production_configuration_state") == "uncalibrated_engineering_defaults", "production configuration state drifted", failures)
    require(calibration.get("production_threshold_change_authorized") is False, "production threshold change became authorized", failures)
    require(calibration.get("production_resource_limit_change_authorized") is False, "production resource change became authorized", failures)

    assertions = overlay.get("assertions", {})
    require(assertions.get("historical_evidence_immutable") is True, "historical immutability lost", failures)
    require(assertions.get("real_or_derivative_bytes_in_ordinary_git") is False, "real/derivative bytes appeared in ordinary Git", failures)
    require(assertions.get("held_out_evaluation_evidence_accepted") is True, "acceptance assertion missing", failures)
    require(assertions.get("readiness_prerequisites_satisfied") is True, "readiness assertion missing", failures)
    require(assertions.get("final_governance_acceptance_still_required") is True, "final governance boundary missing", failures)
    for key in ("stage4_exit_pass", "stage5_entry_authorized", "model_training_authorized", "publication_authorized"):
        require(assertions.get(key) is False, f"unsafe downstream assertion became true: {key}", failures)

    if failures:
        print("Stage 4 post-held-out-acceptance current truth: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 post-held-out-acceptance current truth: PASS")
    print(f"- production main: {EXPECTED_MAIN}")
    print(f"- held-out acceptance digest: {ACCEPTANCE_CANONICAL_SHA256}")
    print(f"- readiness digest: {POST_ACCEPTANCE_READINESS_DIGEST}")
    print("- readiness: READY_FOR_FINAL_ACCEPTANCE_REVIEW / blockers=0")
    print("- final governance acceptance still required: true")
    print("- Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
