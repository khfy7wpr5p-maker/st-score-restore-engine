from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_execution_authorization import validate_stage4_execution_authorization
from st_score_restore.stage4_exit_readiness import (
    BLOCK_NO_DEVELOPMENT_EVIDENCE,
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
    BLOCK_NO_REFERENCE_BUNDLE,
    BLOCK_NO_SAFETY_CALIBRATION_PERMISSION,
    READINESS_VERSION,
    Stage4ReadinessInput,
    evaluate_stage4_exit_readiness,
)
from st_score_restore.stage4_purpose_grants import validate_stage4_purpose_grants
from st_score_restore.stage4_reference_label_acceptance import validate_reference_label_acceptance

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
PURPOSE_GRANTS = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
EXECUTION_AUTHORIZATION = ROOT / "evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json"
REFERENCE_COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
REFERENCE_ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
LIVE_HANDOFF = ROOT / "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"
STATUS = ROOT / "docs/stage-4-current-status.md"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"
MODULE = ROOT / "src/st_score_restore/stage4_exit_readiness.py"
STAGE4_GOVERNANCE = ROOT / "evidence/stage4/governance"

EXPECTED_CANDIDATE_BLOCKERS = {
    BLOCK_NO_DEVELOPMENT_EVIDENCE,
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
}
EXPECTED_GOVERNANCE_FILES = [
    "expanded-development-calibration-execution-authorization.v1.json",
    "purpose-grants.v1.json",
    "real-development-calibration-execution-authorization.v1.json",
    "stage4-entry-start.v1.json",
]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []
    for path in (
        CATALOG,
        PURPOSE_GRANTS,
        EXECUTION_AUTHORIZATION,
        REFERENCE_COMPLETION,
        REFERENCE_ACCEPTANCE,
        LIVE_HANDOFF,
        STATUS,
        WORKFLOW,
        MODULE,
        STAGE4_GOVERNANCE,
    ):
        require(path.exists(), f"required Stage 4 readiness input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    catalog = load(CATALOG)
    purpose_raw = load(PURPOSE_GRANTS)
    completion = load(REFERENCE_COMPLETION)
    acceptance_raw = load(REFERENCE_ACCEPTANCE)
    authorization_raw = load(EXECUTION_AUTHORIZATION)

    purpose_grants = validate_stage4_purpose_grants(purpose_raw)
    acceptance = validate_reference_label_acceptance(acceptance_raw, completion)
    authorization = validate_stage4_execution_authorization(
        authorization_raw, purpose_raw, acceptance_raw, completion
    )
    handoff = load(LIVE_HANDOFF)
    status = STATUS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    module = MODULE.read_text(encoding="utf-8")

    require(READINESS_VERSION == "0.1.0", "Stage 4 exit-readiness version drifted", failures)

    historical_catalog_grants = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(
        not historical_catalog_grants,
        f"historical catalog was rewritten with safety_calibration grants: {historical_catalog_grants}",
        failures,
    )

    overlay_grants = purpose_grants.get("grants", [])
    require(len(overlay_grants) == 2, "Stage 4 safety-calibration overlay must grant exactly two development artifacts", failures)
    require(acceptance.get("decision") == "ACCEPT_REAL_REFERENCE_BUNDLE", "real reference bundle acceptance is not effective", failures)
    require(acceptance.get("assertions", {}).get("referenceBundleAccepted") is True, "reference bundle acceptance assertion missing", failures)
    require(
        acceptance.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is False,
        "historical reference acceptance was rewritten to authorize execution",
        failures,
    )
    require(
        authorization.get("decision") == "AUTHORIZE_REAL_DEVELOPMENT_CALIBRATION_EXECUTION",
        "real development calibration execution authorization decision missing",
        failures,
    )
    require(
        authorization.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is True,
        "execution authorization evidence does not authorize the exact development run",
        failures,
    )
    require(
        authorization.get("assertions", {}).get("realDataCalibrationExecuted") is False,
        "authorization evidence falsely claims execution already occurred",
        failures,
    )
    require(
        authorization.get("scope", {}).get("heldOutIncluded") is False
        and authorization.get("scope", {}).get("heldOutEvaluationAuthorized") is False
        and authorization.get("scope", {}).get("heldOutTuningAuthorized") is False,
        "execution authorization crossed the held-out boundary",
        failures,
    )

    stage4 = handoff.get("stage4", {})
    require(stage4.get("stage4_state") == "active_framework_governance_only", "Stage 4 historical framework state anchor drifted", failures)
    require(
        stage4.get("execution_phase") == "real_development_calibration_authorized_not_executed",
        "Stage 4 current execution phase drifted",
        failures,
    )
    require(stage4.get("real_data_calibration_execution_authorized") is True, "production-effective execution authorization missing", failures)
    require(stage4.get("calibration_authorized") is True, "exact-scope development calibration authorization missing", failures)
    require(stage4.get("real_data_calibration_executed") is False, "real calibration unexpectedly executed", failures)
    require(stage4.get("held_out_tuning_used") is False, "held-out tuning unexpectedly used", failures)
    require(stage4.get("production_threshold_changes_authorized") is False, "production threshold changes unexpectedly authorized", failures)
    require(stage4.get("production_resource_limit_changes_authorized") is False, "production resource changes unexpectedly authorized", failures)
    require(stage4.get("stage4_exit_state") == "not_yet_pass", "Stage 4 exit unexpectedly changed", failures)
    require(stage4.get("stage5_entry_eligible") is False, "Stage 5 unexpectedly eligible", failures)
    require(handoff.get("stage5_entry_state") == "blocked_pending_stage4_exit", "Stage 5 current block drifted", failures)

    current_existing_blockers = set(stage4.get("readiness_blocker_codes", []))
    require(
        current_existing_blockers == EXPECTED_CANDIDATE_BLOCKERS,
        "live handoff readiness blockers do not match the three remaining prerequisites",
        failures,
    )
    require(BLOCK_NO_REFERENCE_BUNDLE not in current_existing_blockers, "accepted reference bundle regressed into blockers", failures)
    require(stage4.get("reference_label_bundle_accepted") is True, "live handoff lost production-effective reference acceptance", failures)
    require(
        stage4.get("current_execution_blocker_codes") == ["private_observation_metrics_not_available"],
        "post-authorization execution dependency drifted",
        failures,
    )
    require(stage4.get("private_observation_metrics_required") is True, "private metric requirement missing", failures)
    require(stage4.get("private_observation_metrics_available") is False, "live handoff falsely claims private metrics are available", failures)
    require(stage4.get("raw_observation_metrics_allowed_in_ordinary_git") is False, "raw metrics were allowed in ordinary Git", failures)
    require("AUTHORIZED" in status and "NOT YET EXECUTED" in status, "Stage 4 status lost post-authorization execution state", failures)
    require("private observation metrics" in status.lower(), "Stage 4 status lost private metric dependency", failures)
    require("uncalibrated_engineering_defaults" in status, "Stage 4 status lost uncalibrated-defaults state", failures)

    governance_files = sorted(path.name for path in STAGE4_GOVERNANCE.iterdir() if path.is_file())
    require(
        governance_files == EXPECTED_GOVERNANCE_FILES,
        f"unexpected Stage 4 governance evidence exists; readiness validator must be updated explicitly: {governance_files}",
        failures,
    )

    candidate = Stage4ReadinessInput(
        safety_calibration_artifact_count=len(overlay_grants),
        accepted_real_reference_bundle_count=1,
        accepted_real_development_evidence_count=0,
        accepted_real_held_out_evaluation_evidence_count=0,
        accepted_metric_target_policy=False,
        held_out_tuning_used=bool(stage4.get("held_out_tuning_used")),
        source_family_leakage_count=0,
        historical_evidence_immutable=True,
        real_or_derivative_bytes_in_ordinary_git=False,
        production_threshold_change_authorized=bool(stage4.get("production_threshold_changes_authorized")),
        production_resource_limit_change_authorized=bool(stage4.get("production_resource_limit_changes_authorized")),
    )
    result = evaluate_stage4_exit_readiness(candidate)
    require(result.get("decision") == "NOT_READY", "execution authorization must not make Stage 4 ready", failures)
    require(set(result.get("blockerCodes", [])) == EXPECTED_CANDIDATE_BLOCKERS, "Stage 4 blocker set drifted", failures)
    require(result.get("blockerCount") == 3, "execution authorization must leave three readiness blockers", failures)
    require(BLOCK_NO_SAFETY_CALIBRATION_PERMISSION not in result.get("blockerCodes", []), "purpose prerequisite regressed", failures)
    require(BLOCK_NO_REFERENCE_BUNDLE not in result.get("blockerCodes", []), "reference prerequisite regressed", failures)
    assertions = result.get("assertions", {})
    require(assertions.get("readinessPrerequisitesSatisfied") is False, "readiness prerequisites unexpectedly satisfied", failures)
    require(assertions.get("finalGovernanceAcceptanceStillRequired") is True, "final governance requirement lost", failures)
    require(assertions.get("stage4ExitPass") is False, "readiness evaluator self-authorized Stage 4 PASS", failures)
    require(assertions.get("stage5EntryAuthorized") is False, "readiness evaluator self-authorized Stage 5", failures)

    hypothetical = evaluate_stage4_exit_readiness(
        Stage4ReadinessInput(
            safety_calibration_artifact_count=2,
            accepted_real_reference_bundle_count=1,
            accepted_real_development_evidence_count=1,
            accepted_real_held_out_evaluation_evidence_count=1,
            accepted_metric_target_policy=True,
            held_out_tuning_used=False,
            source_family_leakage_count=0,
            historical_evidence_immutable=True,
            real_or_derivative_bytes_in_ordinary_git=False,
            production_threshold_change_authorized=False,
            production_resource_limit_change_authorized=False,
        )
    )
    require(
        hypothetical.get("decision") == "READY_FOR_FINAL_ACCEPTANCE_REVIEW",
        "complete hypothetical prerequisites should only reach final-acceptance review readiness",
        failures,
    )
    require(hypothetical.get("blockerCodes") == [], "review-ready hypothetical state has blockers", failures)
    require(hypothetical.get("assertions", {}).get("stage4ExitPass") is False, "review-ready state became Stage 4 PASS", failures)
    require(hypothetical.get("assertions", {}).get("stage5EntryAuthorized") is False, "review-ready state authorized Stage 5", failures)
    require(
        hypothetical.get("assertions", {}).get("finalGovernanceAcceptanceStillRequired") is True,
        "review-ready state bypassed final governance",
        failures,
    )

    for token in (
        "READY_FOR_FINAL_ACCEPTANCE_REVIEW",
        "no_real_development_calibration_evidence_is_accepted",
        "no_real_held_out_evaluation_evidence_is_accepted",
        "no_stage4_metric_acceptance_target_policy_is_accepted",
        '"stage4ExitPass": False',
        '"stage5EntryAuthorized": False',
    ):
        require(token in module, f"Stage 4 readiness module lost safety token: {token}", failures)

    for validator in (
        "python tools/validate_stage4_purpose_grants.py",
        "python tools/validate_stage4_reference_label_completion.py",
        "python tools/validate_stage4_reference_label_acceptance.py",
        "python tools/validate_stage4_execution_authorization.py",
        "python tools/validate_stage4_exit_readiness.py",
        "python tools/validate_stage4_wikimedia_expanded_execution_authorization.py",
    ):
        require(validator in workflow, f"Repository validation does not run required Stage 4 validator: {validator}", failures)

    if failures:
        print("Stage 4 exit-readiness validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 exit-readiness validation: PASS")
    print("- safety_calibration artifacts: 2 exact development items")
    print("- accepted real development reference bundles: 1")
    print("- real development calibration execution: AUTHORIZED / NOT YET EXECUTED")
    print("- immediate execution dependency: private observation metrics not available")
    print("- readiness decision: NOT_READY / 3 remaining blockers")
    for blocker in sorted(EXPECTED_CANDIDATE_BLOCKERS):
        print(f"  - {blocker}")
    print("- held-out tuning: false / Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
