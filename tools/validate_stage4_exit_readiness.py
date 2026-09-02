from __future__ import annotations

import json
from pathlib import Path
import sys

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

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
PURPOSE_GRANTS = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
LIVE_HANDOFF = ROOT / "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json"
STATUS = ROOT / "docs/stage-4-current-status.md"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"
MODULE = ROOT / "src/st_score_restore/stage4_exit_readiness.py"
STAGE4_GOVERNANCE = ROOT / "evidence/stage4/governance"

EXPECTED_CANDIDATE_BLOCKERS = {
    BLOCK_NO_REFERENCE_BUNDLE,
    BLOCK_NO_DEVELOPMENT_EVIDENCE,
    BLOCK_NO_HELDOUT_EVIDENCE,
    BLOCK_NO_METRIC_TARGET_POLICY,
}


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    for path in (CATALOG, PURPOSE_GRANTS, LIVE_HANDOFF, STATUS, WORKFLOW, MODULE, STAGE4_GOVERNANCE):
        require(path.exists(), f"required Stage 4 readiness input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    purpose_grants = validate_stage4_purpose_grants(json.loads(PURPOSE_GRANTS.read_text(encoding="utf-8")))
    handoff = json.loads(LIVE_HANDOFF.read_text(encoding="utf-8"))
    status = STATUS.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    module = MODULE.read_text(encoding="utf-8")

    require(READINESS_VERSION == "0.1.0", "Stage 4 exit-readiness version drifted", failures)

    historical_catalog_grants = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(not historical_catalog_grants, f"historical catalog was rewritten with safety_calibration grants: {historical_catalog_grants}", failures)
    overlay_grants = purpose_grants.get("grants", [])
    require(len(overlay_grants) == 2, "Stage 4 safety-calibration overlay must grant exactly two development artifacts", failures)

    stage4 = handoff.get("stage4", {})
    require(stage4.get("stage4_state") == "active_framework_governance_only", "Stage 4 current state drifted", failures)
    require(stage4.get("real_data_calibration_execution_authorized") is False, "real calibration unexpectedly authorized", failures)
    require(stage4.get("calibration_authorized") is False, "execution-level calibration authorization unexpectedly true", failures)
    require(stage4.get("real_data_calibration_executed") is False, "real calibration unexpectedly executed", failures)
    require(stage4.get("held_out_tuning_used") is False, "held-out tuning unexpectedly used", failures)
    require(stage4.get("production_threshold_changes_authorized") is False, "production threshold changes unexpectedly authorized", failures)
    require(stage4.get("production_resource_limit_changes_authorized") is False, "production resource changes unexpectedly authorized", failures)
    require(stage4.get("stage4_exit_state") == "not_yet_pass", "Stage 4 exit unexpectedly changed", failures)
    require(stage4.get("stage5_entry_eligible") is False, "Stage 5 unexpectedly eligible", failures)
    require(handoff.get("stage5_entry_state") == "blocked_pending_stage4_exit", "Stage 5 current block drifted", failures)

    # The live handoff is the last production checkpoint and is intentionally not
    # rewritten inside this grant PR. It may still list the pre-grant blocker until
    # this slice merges and a separate current-truth checkpoint becomes effective.
    current_existing_blockers = set(stage4.get("blocker_codes", []))
    require(
        BLOCK_NO_SAFETY_CALIBRATION_PERMISSION in current_existing_blockers
        and BLOCK_NO_REFERENCE_BUNDLE in current_existing_blockers,
        "pre-grant production handoff lost its frozen blockers before grant production-effectiveness",
        failures,
    )
    require("BLOCKED / NOT AUTHORIZED" in status, "Stage 4 status lost real-calibration execution block", failures)
    require("uncalibrated_engineering_defaults" in status, "Stage 4 status lost uncalibrated-defaults state", failures)

    governance_files = sorted(path.name for path in STAGE4_GOVERNANCE.iterdir() if path.is_file())
    require(
        governance_files == ["purpose-grants.v1.json", "stage4-entry-start.v1.json"],
        f"unexpected Stage 4 governance evidence exists; readiness validator must be updated explicitly: {governance_files}",
        failures,
    )

    candidate = Stage4ReadinessInput(
        safety_calibration_artifact_count=len(overlay_grants),
        accepted_real_reference_bundle_count=0,
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
    require(result.get("decision") == "NOT_READY", "Stage 4 grant candidate must remain NOT_READY", failures)
    require(set(result.get("blockerCodes", [])) == EXPECTED_CANDIDATE_BLOCKERS, "Stage 4 grant-candidate blocker set drifted", failures)
    require(result.get("blockerCount") == 4, "Stage 4 grant candidate must have four remaining blockers", failures)
    require(BLOCK_NO_SAFETY_CALIBRATION_PERMISSION not in result.get("blockerCodes", []), "validated safety-calibration overlay did not resolve the purpose prerequisite", failures)
    assertions = result.get("assertions", {})
    require(assertions.get("readinessPrerequisitesSatisfied") is False, "readiness prerequisites unexpectedly satisfied", failures)
    require(assertions.get("finalGovernanceAcceptanceStillRequired") is True, "final governance acceptance requirement lost", failures)
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
    hypothetical_assertions = hypothetical.get("assertions", {})
    require(hypothetical_assertions.get("stage4ExitPass") is False, "review-ready state became Stage 4 PASS", failures)
    require(hypothetical_assertions.get("stage5EntryAuthorized") is False, "review-ready state authorized Stage 5", failures)
    require(hypothetical_assertions.get("finalGovernanceAcceptanceStillRequired") is True, "review-ready state bypassed final governance", failures)

    for token in (
        "READY_FOR_FINAL_ACCEPTANCE_REVIEW",
        "no_real_development_calibration_evidence_is_accepted",
        "no_real_held_out_evaluation_evidence_is_accepted",
        "no_stage4_metric_acceptance_target_policy_is_accepted",
        '"stage4ExitPass": False',
        '"stage5EntryAuthorized": False',
    ):
        require(token in module, f"Stage 4 readiness module lost safety token: {token}", failures)
    require(
        "python tools/validate_stage4_exit_readiness.py" in workflow,
        "Repository validation does not run Stage 4 exit-readiness validator",
        failures,
    )
    require(
        "python tools/validate_stage4_purpose_grants.py" in workflow,
        "Repository validation does not run Stage 4 purpose-grant validator",
        failures,
    )

    if failures:
        print("Stage 4 exit-readiness validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 exit-readiness validation: PASS")
    print("- grant candidate decision: NOT_READY")
    print("- safety_calibration artifacts: 2 exact development items")
    print("- remaining blockers: 4")
    for blocker in sorted(EXPECTED_CANDIDATE_BLOCKERS):
        print(f"  - {blocker}")
    print("- real calibration execution: still blocked pending accepted reference-label evidence")
    print("- hypothetical complete prerequisites: READY_FOR_FINAL_ACCEPTANCE_REVIEW only")
    print("- Stage 4 PASS: false / Stage 5 entry: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
