from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

FRAMEWORK_MAIN = "4a5c3db2d767dac235fe12a6bd0e18ba500e7362"
FRAMEWORK_RUN_ID = 33659753403
FRAMEWORK_RUN_NUMBER = 259
REFERENCE_MAIN = "b184f5e5b780213671597ffa9f4380aa4a1adb47"
REFERENCE_RUN_ID = 33668750227
REFERENCE_RUN_NUMBER = 263
PUBLIC_EVIDENCE_MAIN = "4c936353ede322f41d009d503bcb4ca7fa64b2b9"
PUBLIC_EVIDENCE_RUN_ID = 33669674783
PUBLIC_EVIDENCE_RUN_NUMBER = 265
READINESS_MAIN = "d4dff6b8c672cec1b2afa864f89bb7a03f29cd75"
READINESS_RUN_ID = 33670331093
READINESS_RUN_NUMBER = 267
ENTRY_DIGEST = "013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8"

READINESS_BLOCKERS = [
    "no_real_artifact_has_granted_safety_calibration_permission",
    "no_real_calibration_reference_label_bundle_is_accepted",
    "no_real_development_calibration_evidence_is_accepted",
    "no_real_held_out_evaluation_evidence_is_accepted",
    "no_stage4_metric_acceptance_target_policy_is_accepted",
]

LEGACY_REAL_CALIBRATION_BLOCKERS = READINESS_BLOCKERS[:2]

DOC_PATHS = (
    "README.md",
    "docs/roadmap.md",
    "docs/technical-specification.md",
    "docs/architecture-consistency-audit.md",
    "docs/stage-4-current-status.md",
)

BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    required_paths = (
        *DOC_PATHS,
        "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json",
        "evidence/stage1c/corpus/catalog.v2.json",
        "evidence/stage3/governance/purpose-grants.v1.json",
        "evidence/stage4/governance/stage4-entry-start.v1.json",
        "src/st_score_restore/stage4_calibration.py",
        "src/st_score_restore/stage4_reference_labels.py",
        "src/st_score_restore/stage4_calibration_evidence.py",
        "src/st_score_restore/stage4_exit_readiness.py",
        "tools/validate_stage4_reference_labels.py",
        "tools/validate_stage4_calibration_evidence.py",
        "tools/validate_stage4_exit_readiness.py",
        ".github/workflows/repository-validation.yml",
    )
    for path in required_paths:
        require((ROOT / path).exists(), f"required current-truth input missing: {path}")

    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    docs = {path: read(path) for path in DOC_PATHS}
    for path, text in docs.items():
        lower = text.lower()
        require("stage 4" in lower, f"{path} lost Stage 4 state")
        require("not_ready" in lower or "not ready" in lower, f"{path} lost Stage 4 NOT_READY state")
        require("stage 5" in lower and "blocked" in lower, f"{path} lost Stage 5 block")
        require(READINESS_MAIN in text, f"{path} lost latest readiness main")
        require(str(READINESS_RUN_NUMBER) in text, f"{path} lost readiness Run #{READINESS_RUN_NUMBER}")
        require(ENTRY_DIGEST in text, f"{path} lost immutable Stage 4 entry/start digest")
        for blocker in READINESS_BLOCKERS:
            require(blocker in text, f"{path} lost readiness blocker {blocker}")

    stage4_status = docs["docs/stage-4-current-status.md"]
    for main_sha, run_number in (
        (FRAMEWORK_MAIN, FRAMEWORK_RUN_NUMBER),
        (REFERENCE_MAIN, REFERENCE_RUN_NUMBER),
        (PUBLIC_EVIDENCE_MAIN, PUBLIC_EVIDENCE_RUN_NUMBER),
        (READINESS_MAIN, READINESS_RUN_NUMBER),
    ):
        require(main_sha in stage4_status, f"Stage 4 status lost production chain main {main_sha}")
        require(str(run_number) in stage4_status, f"Stage 4 status lost production chain Run #{run_number}")

    handoff = load("docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json")
    require(handoff.get("schema_version") == "1.17.0", "live handoff schema version drifted")
    require(handoff.get("main_sha") == FRAMEWORK_MAIN, "historical framework anchor changed unexpectedly")
    require(handoff.get("main_sha_scope", "").startswith("Historical Stage 4 framework-start"), "framework anchor scope is ambiguous")
    require(handoff.get("latest_main_ci_run_id") == FRAMEWORK_RUN_ID, "historical framework CI anchor drifted")
    require(handoff.get("latest_main_ci_run_number") == FRAMEWORK_RUN_NUMBER, "historical framework CI run drifted")
    require(handoff.get("repository_main_sha") == READINESS_MAIN, "latest repository main is not readiness main")
    require(handoff.get("latest_repository_ci_run_id") == READINESS_RUN_ID, "latest repository CI ID drifted")
    require(handoff.get("latest_repository_ci_run_number") == READINESS_RUN_NUMBER, "latest repository CI number drifted")
    require(handoff.get("latest_repository_ci_status") == "success_python_3_11_and_3_12", "latest repository CI is not green")
    require(handoff.get("stage3_exit_state") == "pass_effective", "Stage 3 PASS drifted")
    require(handoff.get("stage4_entry_state") == "active_framework_governance_only", "Stage 4 framework/governance state drifted")
    require(handoff.get("stage4_started") is True, "Stage 4 no longer marked started")
    require(handoff.get("stage5_entry_state") == "blocked_pending_stage4_exit", "Stage 5 block drifted")

    stage4 = handoff.get("stage4", {})
    require(stage4.get("tracking_issue") == 104, "Stage 4 tracking issue drifted")
    require(stage4.get("framework_main_sha") == FRAMEWORK_MAIN, "framework main binding drifted")
    require(stage4.get("framework_postmerge_ci_run_id") == FRAMEWORK_RUN_ID, "framework run ID drifted")
    require(stage4.get("framework_postmerge_ci_run_number") == FRAMEWORK_RUN_NUMBER, "framework run number drifted")
    require(stage4.get("framework_production_effective") is True, "framework no longer production-effective")
    require(stage4.get("reference_label_contract_version") == "0.1.0", "reference-label contract version drifted")
    require(stage4.get("reference_label_contract_merge_pr") == 107, "reference-label PR binding drifted")
    require(stage4.get("reference_label_contract_main_sha") == REFERENCE_MAIN, "reference-label main binding drifted")
    require(stage4.get("reference_label_contract_postmerge_ci_run_id") == REFERENCE_RUN_ID, "reference-label run ID drifted")
    require(stage4.get("reference_label_contract_postmerge_ci_run_number") == REFERENCE_RUN_NUMBER, "reference-label run number drifted")
    require(stage4.get("reference_label_contract_production_effective") is True, "reference-label contract not production-effective")
    require(stage4.get("public_calibration_evidence_contract_version") == "0.1.0", "public-evidence contract version drifted")
    require(stage4.get("public_calibration_evidence_merge_pr") == 108, "public-evidence PR binding drifted")
    require(stage4.get("public_calibration_evidence_main_sha") == PUBLIC_EVIDENCE_MAIN, "public-evidence main binding drifted")
    require(stage4.get("public_calibration_evidence_postmerge_ci_run_id") == PUBLIC_EVIDENCE_RUN_ID, "public-evidence run ID drifted")
    require(stage4.get("public_calibration_evidence_postmerge_ci_run_number") == PUBLIC_EVIDENCE_RUN_NUMBER, "public-evidence run number drifted")
    require(stage4.get("public_calibration_evidence_production_effective") is True, "public-evidence contract not production-effective")
    require(stage4.get("exit_readiness_contract_version") == "0.1.0", "exit-readiness version drifted")
    require(stage4.get("exit_readiness_merge_pr") == 109, "exit-readiness PR binding drifted")
    require(stage4.get("exit_readiness_main_sha") == READINESS_MAIN, "exit-readiness main binding drifted")
    require(stage4.get("exit_readiness_postmerge_ci_run_id") == READINESS_RUN_ID, "exit-readiness run ID drifted")
    require(stage4.get("exit_readiness_postmerge_ci_run_number") == READINESS_RUN_NUMBER, "exit-readiness run number drifted")
    require(stage4.get("exit_readiness_production_effective") is True, "exit-readiness contract not production-effective")
    require(stage4.get("readiness_decision") == "NOT_READY", "readiness decision is not NOT_READY")
    require(stage4.get("readiness_blocker_codes") == READINESS_BLOCKERS, "readiness blocker set drifted")
    require(stage4.get("blocker_codes") == LEGACY_REAL_CALIBRATION_BLOCKERS, "legacy real-calibration blocker set drifted")

    for key in (
        "real_data_calibration_execution_authorized",
        "calibration_authorized",
        "real_data_calibration_executed",
        "thresholds_calibrated",
        "resource_limits_calibrated",
        "production_threshold_changes_authorized",
        "production_resource_limit_changes_authorized",
        "model_training_authorized",
        "publication_authorized",
        "held_out_tuning_used",
        "stage4_exit_pass",
        "stage5_entry_eligible",
        "stage5_entry_authorized",
    ):
        require(stage4.get(key) is False, f"unsafe Stage 4 flag became true: {key}")
    require(stage4.get("stage4_exit_state") == "not_yet_pass", "Stage 4 exited prematurely")
    require(stage4.get("calibration_state") == "uncalibrated_engineering_defaults", "calibration state drifted")

    catalog = load("evidence/stage1c/corpus/catalog.v2.json")
    granted_safety = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(not granted_safety, f"catalog has safety_calibration grants but current truth says none: {granted_safety}")

    stage3_grants = load("evidence/stage3/governance/purpose-grants.v1.json")
    require(stage3_grants.get("assertions", {}).get("calibrationAuthorized") is False, "Stage 3 grants unexpectedly authorize calibration")
    require(all(item.get("purpose") == "pdf_pipeline_evaluation" for item in stage3_grants.get("grants", [])), "Stage 3 grant purposes drifted")

    stage4_entry = load("evidence/stage4/governance/stage4-entry-start.v1.json")
    require(stage4_entry.get("decisionDigest", {}).get("value") == ENTRY_DIGEST, "Stage 4 entry/start digest drifted")
    require(stage4_entry.get("decision") == "APPROVE_FRAMEWORK_START", "Stage 4 entry/start decision drifted")
    require(stage4_entry.get("claims", {}).get("stage4Started") is False, "historical pre-start decision was rewritten")

    reference_code = read("src/st_score_restore/stage4_reference_labels.py")
    for token in (
        "safety_calibration",
        "held_out_evaluation",
        "human",
        "modelPredictionsUsedAsReferenceLabels",
        "held_out_reference_derivation_forbidden",
    ):
        require(token in reference_code, f"reference-label contract lost safety token {token}")

    public_evidence_code = read("src/st_score_restore/stage4_calibration_evidence.py")
    for token in (
        "synthetic_test",
        "realDataCalibrationExecuted",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(token in public_evidence_code, f"public evidence contract lost safety token {token}")

    readiness_code = read("src/st_score_restore/stage4_exit_readiness.py")
    for token in (
        "NOT_READY",
        "READY_FOR_FINAL_ACCEPTANCE_REVIEW",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(token in readiness_code, f"exit-readiness contract lost safety token {token}")

    workflow = read(".github/workflows/repository-validation.yml")
    for validator in (
        "validate_architecture_consistency.py",
        "validate_stage4_entry_start.py",
        "validate_stage4_reference_labels.py",
        "validate_stage4_calibration_evidence.py",
        "validate_stage4_exit_readiness.py",
        "validate_stage4_current_truth.py",
    ):
        require(validator in workflow, f"CI is not wired to {validator}")

    for root_name in ("stage1c", "stage2", "stage3", "stage4"):
        root = ROOT / "evidence" / root_name
        if root.exists():
            binaries = [
                str(path.relative_to(ROOT))
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES
            ]
            require(not binaries, f"artifact-like binary bytes found under evidence/{root_name}: {binaries}")

    if failures:
        print("Stage 4 current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 current-truth validation: PASS")
    print(f"- Framework anchor: {FRAMEWORK_MAIN} / Run #{FRAMEWORK_RUN_NUMBER}")
    print(f"- Reference-label contract: {REFERENCE_MAIN} / Run #{REFERENCE_RUN_NUMBER}")
    print(f"- Public evidence contract: {PUBLIC_EVIDENCE_MAIN} / Run #{PUBLIC_EVIDENCE_RUN_NUMBER}")
    print(f"- Exit-readiness contract: {READINESS_MAIN} / Run #{READINESS_RUN_NUMBER}")
    print("- Readiness: NOT_READY / 5 prerequisite blockers")
    print("- Stage 4 exit PASS: false / Stage 5 entry authorized: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
