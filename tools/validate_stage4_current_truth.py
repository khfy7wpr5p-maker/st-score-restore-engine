from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage4_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    validate_stage4_execution_authorization,
)
from st_score_restore.stage4_purpose_grants import (
    APPROVED_GRANT_CANONICAL_SHA256,
    APPROVED_ITEMS,
    HELD_OUT_ITEM,
    validate_stage4_purpose_grants,
)
from st_score_restore.stage4_reference_label_acceptance import (
    ACCEPTANCE_CANONICAL_SHA256,
    REFERENCE_RECEIPT_CANONICAL_SHA256,
    validate_reference_label_acceptance,
)
from st_score_restore.stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256,
    COMPLETION_CANONICAL_SHA256,
)
from st_score_restore.stage4_reference_label_work_package import WORK_PACKAGE_CANONICAL_SHA256

ROOT = Path(__file__).resolve().parents[1]

FRAMEWORK_MAIN = "4a5c3db2d767dac235fe12a6bd0e18ba500e7362"
FRAMEWORK_RUN_NUMBER = 259
REFERENCE_MAIN = "b184f5e5b780213671597ffa9f4380aa4a1adb47"
REFERENCE_RUN_NUMBER = 263
PUBLIC_EVIDENCE_MAIN = "4c936353ede322f41d009d503bcb4ca7fa64b2b9"
PUBLIC_EVIDENCE_RUN_NUMBER = 265
READINESS_MAIN = "d4dff6b8c672cec1b2afa864f89bb7a03f29cd75"
READINESS_RUN_NUMBER = 267
PURPOSE_MAIN = "c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd"
PURPOSE_RUN_ID = 33672903071
PURPOSE_RUN_NUMBER = 272
PURPOSE_EXACT_HEAD = "dce3da9184d5995fa57534e1bd978ea4dfd614a5"
PURPOSE_EXACT_RUN_ID = 33672712230
PURPOSE_EXACT_RUN_NUMBER = 271
WORK_PACKAGE_MAIN = "7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12"
WORK_PACKAGE_RUN_ID = 33677035152
WORK_PACKAGE_RUN_NUMBER = 278
COMPLETION_MAIN = "58266dffed529a5d7d247e58651865bbda83981e"
COMPLETION_RUN_ID = 33677635302
COMPLETION_RUN_NUMBER = 280
ACCEPTANCE_EXACT_HEAD = "af0910f1542971576aabb98a66fddb163e9a5767"
ACCEPTANCE_EXACT_RUN_ID = 33680370670
ACCEPTANCE_EXACT_RUN_NUMBER = 281
ACCEPTANCE_MAIN = "4f663d0c11339b98fd89639fd8f3d5afc8047fb3"
ACCEPTANCE_RUN_ID = 33680628749
ACCEPTANCE_RUN_NUMBER = 282
REFERENCE_TRUTH_MAIN = "0c267cb9489cfe023a4d5e26104f5ae684cb95fb"
REFERENCE_TRUTH_RUN_ID = 33681777851
REFERENCE_TRUTH_RUN_NUMBER = 285
AUTH_EXACT_HEAD = "b42ad45656299651897be33b7ea98d940217095c"
AUTH_EXACT_RUN_ID = 33685839142
AUTH_EXACT_RUN_NUMBER = 286
AUTH_MAIN = "76f5643dde72c8cc4b02b517133331e9dea00146"
AUTH_RUN_ID = 33686039783
AUTH_RUN_NUMBER = 287
ENTRY_DIGEST = "013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8"
CATALOG_DIGEST = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"

READINESS_BLOCKERS = [
    "no_real_development_calibration_evidence_is_accepted",
    "no_real_held_out_evaluation_evidence_is_accepted",
    "no_stage4_metric_acceptance_target_policy_is_accepted",
]
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

    required = (
        *DOC_PATHS,
        "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json",
        "evidence/stage1c/corpus/catalog.v2.json",
        "evidence/stage4/governance/stage4-entry-start.v1.json",
        "evidence/stage4/governance/purpose-grants.v1.json",
        "evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json",
        "evidence/stage4/reference-labels/development-human-label-completion.v1.json",
        "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json",
        "src/st_score_restore/stage4_purpose_grants.py",
        "src/st_score_restore/stage4_reference_labels.py",
        "src/st_score_restore/stage4_reference_label_completion.py",
        "src/st_score_restore/stage4_reference_label_acceptance.py",
        "src/st_score_restore/stage4_execution_authorization.py",
        "src/st_score_restore/stage4_calibration.py",
        "src/st_score_restore/stage4_calibration_evidence.py",
        "src/st_score_restore/stage4_exit_readiness.py",
        "tools/validate_stage4_purpose_grants.py",
        "tools/validate_stage4_reference_labels.py",
        "tools/validate_stage4_reference_label_completion.py",
        "tools/validate_stage4_reference_label_acceptance.py",
        "tools/validate_stage4_execution_authorization.py",
        "tools/validate_stage4_calibration_evidence.py",
        "tools/validate_stage4_exit_readiness.py",
        ".github/workflows/repository-validation.yml",
    )
    for path in required:
        require((ROOT / path).exists(), f"required Stage 4 current-truth input missing: {path}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    docs = {path: read(path) for path in DOC_PATHS}
    for path, text in docs.items():
        lower = text.lower()
        require("stage 4" in lower and "active" in lower, f"{path} lost Stage 4 ACTIVE state")
        require("not_ready" in lower or "not ready" in lower, f"{path} lost NOT_READY state")
        require("stage 5" in lower and "blocked" in lower, f"{path} lost Stage 5 block")
        require(PURPOSE_MAIN in text, f"{path} lost purpose-grant production main")
        require(str(PURPOSE_RUN_NUMBER) in text, f"{path} lost purpose-grant post-merge Run #{PURPOSE_RUN_NUMBER}")
        require(ACCEPTANCE_MAIN in text, f"{path} lost reference-acceptance production main")
        require(str(ACCEPTANCE_RUN_NUMBER) in text, f"{path} lost reference-acceptance post-merge Run #{ACCEPTANCE_RUN_NUMBER}")
        require(AUTH_MAIN in text, f"{path} lost execution-authorization production main")
        require(str(AUTH_RUN_NUMBER) in text, f"{path} lost execution-authorization post-merge Run #{AUTH_RUN_NUMBER}")
        require(ENTRY_DIGEST in text, f"{path} lost Stage 4 entry digest")
        require(APPROVED_GRANT_CANONICAL_SHA256 in text, f"{path} lost Stage 4 purpose-grant digest")
        require(BUNDLE_CANONICAL_SHA256 in text, f"{path} lost accepted reference-bundle digest")
        require(ACCEPTANCE_CANONICAL_SHA256 in text, f"{path} lost reference-bundle acceptance digest")
        require(AUTHORIZATION_CANONICAL_SHA256 in text, f"{path} lost execution-authorization digest")
        require("authorized" in lower, f"{path} lost execution authorization state")
        require("not yet executed" in lower or "executed=false" in lower, f"{path} lost not-executed state")
        require("private" in lower and "metric" in lower, f"{path} lost private observation-metric dependency")
        for blocker in READINESS_BLOCKERS:
            require(blocker in text, f"{path} lost readiness blocker {blocker}")
        require(
            "no_real_calibration_reference_label_bundle_is_accepted" not in text
            or "resolved" in lower
            or "historical" in lower,
            f"{path} still presents the accepted-reference blocker as current",
        )

    status = docs["docs/stage-4-current-status.md"]
    for main_sha, run_number in (
        (FRAMEWORK_MAIN, FRAMEWORK_RUN_NUMBER),
        (REFERENCE_MAIN, REFERENCE_RUN_NUMBER),
        (PUBLIC_EVIDENCE_MAIN, PUBLIC_EVIDENCE_RUN_NUMBER),
        (READINESS_MAIN, READINESS_RUN_NUMBER),
        (PURPOSE_MAIN, PURPOSE_RUN_NUMBER),
        (WORK_PACKAGE_MAIN, WORK_PACKAGE_RUN_NUMBER),
        (COMPLETION_MAIN, COMPLETION_RUN_NUMBER),
        (ACCEPTANCE_MAIN, ACCEPTANCE_RUN_NUMBER),
        (REFERENCE_TRUTH_MAIN, REFERENCE_TRUTH_RUN_NUMBER),
        (AUTH_MAIN, AUTH_RUN_NUMBER),
    ):
        require(main_sha in status, f"Stage 4 status lost production chain main {main_sha}")
        require(str(run_number) in status, f"Stage 4 status lost production chain Run #{run_number}")

    catalog = load("evidence/stage1c/corpus/catalog.v2.json")
    require(canonical_sha256(catalog) == CATALOG_DIGEST, "historical Stage 1 catalog digest drifted")
    historical_safety = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(not historical_safety, f"historical catalog was rewritten with safety_calibration grants: {historical_safety}")

    entry = load("evidence/stage4/governance/stage4-entry-start.v1.json")
    require(entry.get("decision") == "APPROVE_FRAMEWORK_START", "historical Stage 4 entry decision drifted")
    require(entry.get("decisionDigest", {}).get("value") == ENTRY_DIGEST, "historical Stage 4 entry digest drifted")
    require(entry.get("scope", {}).get("realDataCalibrationExecutionAuthorized") is False, "historical Stage 4 entry was rewritten")
    require(entry.get("claims", {}).get("stage4Started") is False, "historical Stage 4 entry start claim was rewritten")
    require(entry.get("claims", {}).get("calibrationAuthorized") is False, "historical Stage 4 entry calibration claim was rewritten")

    purpose_raw = load("evidence/stage4/governance/purpose-grants.v1.json")
    purpose = validate_stage4_purpose_grants(purpose_raw)
    require(canonical_sha256(purpose) == APPROVED_GRANT_CANONICAL_SHA256, "purpose-grant canonical digest drifted")
    require(len(purpose.get("grants", [])) == 2, "purpose-grant artifact count drifted")
    require({g.get("datasetItemId") for g in purpose.get("grants", [])} == set(APPROVED_ITEMS), "purpose-grant item set drifted")
    require(purpose.get("heldOutBinding", {}).get("datasetItemId") == HELD_OUT_ITEM, "Chopin held-out binding drifted")
    require(purpose.get("heldOutBinding", {}).get("candidateDerivationAuthorized") is False, "Chopin derivation became authorized")
    purpose_assertions = purpose.get("assertions", {})
    require(purpose_assertions.get("safetyCalibrationPurposeAuthorized") is True, "purpose grant authorization missing")
    require(purpose_assertions.get("realDataCalibrationExecutionAuthorized") is False, "historical purpose grant was rewritten with later execution authorization")
    require(purpose_assertions.get("referenceLabelBundleAccepted") is False, "historical purpose grant was rewritten with later acceptance")
    require(purpose_assertions.get("heldOutTuningAuthorized") is False, "purpose grant authorized held-out tuning")

    completion = load("evidence/stage4/reference-labels/development-human-label-completion.v1.json")
    acceptance_raw = load("evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json")
    acceptance = validate_reference_label_acceptance(acceptance_raw, completion)
    require(canonical_sha256(completion) == COMPLETION_CANONICAL_SHA256, "human completion canonical digest drifted")
    require(acceptance.get("decision") == "ACCEPT_REAL_REFERENCE_BUNDLE", "reference-bundle acceptance decision drifted")
    require(acceptance.get("assertions", {}).get("referenceBundleAccepted") is True, "real reference bundle is not accepted")
    require(acceptance.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is False, "historical acceptance was rewritten with later execution authorization")
    require(acceptance.get("scope", {}).get("heldOutIncluded") is False, "held-out entered accepted development bundle")

    auth_raw = load("evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json")
    auth = validate_stage4_execution_authorization(auth_raw, purpose_raw, acceptance_raw, completion)
    require(canonical_sha256(auth) == AUTHORIZATION_CANONICAL_SHA256, "execution authorization canonical digest drifted")
    require(auth.get("decision") == "AUTHORIZE_REAL_DEVELOPMENT_CALIBRATION_EXECUTION", "execution authorization decision drifted")
    require(auth.get("assertions", {}).get("realDataCalibrationExecutionAuthorized") is True, "execution authorization is not effective")
    require(auth.get("assertions", {}).get("realDataCalibrationExecuted") is False, "authorization falsely claims execution")
    require(auth.get("scope", {}).get("datasetItemCount") == 2, "execution authorization item count drifted")
    require(auth.get("scope", {}).get("referenceRecordCount") == 42, "execution authorization reference count drifted")
    require(auth.get("scope", {}).get("heldOutIncluded") is False, "held-out entered execution authorization")
    require(auth.get("scope", {}).get("heldOutEvaluationAuthorized") is False, "held-out evaluation was prematurely authorized")
    require(auth.get("scope", {}).get("heldOutTuningAuthorized") is False, "held-out tuning was authorized")
    require(auth.get("scope", {}).get("privateObservationMetricsRequired") is True, "private metric requirement missing")
    require(auth.get("scope", {}).get("rawObservationMetricsAllowedInOrdinaryGit") is False, "raw metrics were allowed in ordinary Git")

    handoff = load("docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json")
    require(handoff.get("schema_version") == "1.19.0", "live handoff schema drifted")
    require(handoff.get("main_sha") == FRAMEWORK_MAIN, "historical framework anchor drifted")
    require(handoff.get("latest_main_ci_run_number") == FRAMEWORK_RUN_NUMBER, "historical framework CI anchor drifted")
    require(handoff.get("repository_main_sha") == AUTH_MAIN, "live handoff latest repository main drifted")
    require(handoff.get("latest_repository_ci_run_id") == AUTH_RUN_ID, "live handoff authorization post-merge run ID drifted")
    require(handoff.get("latest_repository_ci_run_number") == AUTH_RUN_NUMBER, "live handoff authorization post-merge run number drifted")
    require(handoff.get("latest_repository_ci_status") == "success_python_3_11_and_3_12", "latest repository CI is not green")
    require(handoff.get("stage3_exit_state") == "pass_effective", "Stage 3 PASS drifted")
    require(handoff.get("stage4_entry_state") == "active_framework_governance_only", "historical Stage 4 entry-state anchor drifted")
    require(handoff.get("stage4_started") is True, "Stage 4 no longer started")
    require(handoff.get("stage5_entry_state") == "blocked_pending_stage4_exit", "Stage 5 block drifted")

    digests = handoff.get("latest_evidence_digests", {})
    require(digests.get("stage4_reference_work_package_canonical_sha256") == WORK_PACKAGE_CANONICAL_SHA256, "live handoff work-package digest drifted")
    require(digests.get("stage4_human_label_completion_canonical_sha256") == COMPLETION_CANONICAL_SHA256, "live handoff completion digest drifted")
    require(digests.get("stage4_reference_bundle_canonical_sha256") == BUNDLE_CANONICAL_SHA256, "live handoff bundle digest drifted")
    require(digests.get("stage4_accepted_reference_receipt_canonical_sha256") == REFERENCE_RECEIPT_CANONICAL_SHA256, "live handoff accepted receipt digest drifted")
    require(digests.get("stage4_reference_bundle_acceptance_canonical_sha256") == ACCEPTANCE_CANONICAL_SHA256, "live handoff acceptance digest drifted")
    require(digests.get("stage4_real_development_execution_authorization_canonical_sha256") == AUTHORIZATION_CANONICAL_SHA256, "live handoff authorization digest drifted")

    s4 = handoff.get("stage4", {})
    require(s4.get("tracking_issue") == 104, "Stage 4 issue binding drifted")
    require(s4.get("framework_main_sha") == FRAMEWORK_MAIN, "framework main drifted")
    require(s4.get("purpose_grant_merge_pr") == 111, "purpose-grant PR binding drifted")
    require(s4.get("purpose_grant_exact_head_sha") == PURPOSE_EXACT_HEAD, "purpose-grant exact head drifted")
    require(s4.get("purpose_grant_exact_head_ci_run_id") == PURPOSE_EXACT_RUN_ID, "purpose-grant exact-head run ID drifted")
    require(s4.get("purpose_grant_exact_head_ci_run_number") == PURPOSE_EXACT_RUN_NUMBER, "purpose-grant exact-head run number drifted")
    require(s4.get("purpose_grant_main_sha") == PURPOSE_MAIN, "purpose-grant main drifted")
    require(s4.get("purpose_grant_postmerge_ci_run_id") == PURPOSE_RUN_ID, "purpose-grant post-merge run ID drifted")
    require(s4.get("purpose_grant_postmerge_ci_run_number") == PURPOSE_RUN_NUMBER, "purpose-grant post-merge run number drifted")
    require(s4.get("purpose_grant_canonical_sha256") == APPROVED_GRANT_CANONICAL_SHA256, "live handoff purpose digest drifted")
    require(s4.get("purpose_grant_production_effective") is True, "purpose grants not production-effective")
    require(s4.get("safety_calibration_purpose_granted_artifact_count") == 2, "live handoff purpose-granted count drifted")

    require(s4.get("reference_work_package_merge_pr") == 113, "work-package PR binding drifted")
    require(s4.get("reference_work_package_main_sha") == WORK_PACKAGE_MAIN, "work-package main drifted")
    require(s4.get("reference_work_package_postmerge_ci_run_id") == WORK_PACKAGE_RUN_ID, "work-package run ID drifted")
    require(s4.get("reference_work_package_postmerge_ci_run_number") == WORK_PACKAGE_RUN_NUMBER, "work-package run number drifted")
    require(s4.get("reference_work_package_canonical_sha256") == WORK_PACKAGE_CANONICAL_SHA256, "work-package digest drifted")

    require(s4.get("human_label_completion_merge_pr") == 114, "human-completion PR binding drifted")
    require(s4.get("human_label_completion_main_sha") == COMPLETION_MAIN, "human-completion main drifted")
    require(s4.get("human_label_completion_postmerge_ci_run_id") == COMPLETION_RUN_ID, "human-completion run ID drifted")
    require(s4.get("human_label_completion_postmerge_ci_run_number") == COMPLETION_RUN_NUMBER, "human-completion run number drifted")
    require(s4.get("human_label_completion_canonical_sha256") == COMPLETION_CANONICAL_SHA256, "human-completion digest drifted")
    require(s4.get("human_label_record_count") == 42, "human-label record count drifted")
    require(s4.get("human_label_counts") == {"clear": 36, "possible": 5, "probable": 1, "not_assessed": 0}, "human-label counts drifted")

    require(s4.get("reference_bundle_acceptance_merge_pr") == 115, "acceptance PR binding drifted")
    require(s4.get("reference_bundle_acceptance_exact_head_sha") == ACCEPTANCE_EXACT_HEAD, "acceptance exact head drifted")
    require(s4.get("reference_bundle_acceptance_exact_head_ci_run_id") == ACCEPTANCE_EXACT_RUN_ID, "acceptance exact-head run ID drifted")
    require(s4.get("reference_bundle_acceptance_exact_head_ci_run_number") == ACCEPTANCE_EXACT_RUN_NUMBER, "acceptance exact-head run number drifted")
    require(s4.get("reference_bundle_acceptance_main_sha") == ACCEPTANCE_MAIN, "acceptance main drifted")
    require(s4.get("reference_bundle_acceptance_postmerge_ci_run_id") == ACCEPTANCE_RUN_ID, "acceptance post-merge run ID drifted")
    require(s4.get("reference_bundle_acceptance_postmerge_ci_run_number") == ACCEPTANCE_RUN_NUMBER, "acceptance post-merge run number drifted")
    require(s4.get("accepted_reference_receipt_canonical_sha256") == REFERENCE_RECEIPT_CANONICAL_SHA256, "accepted receipt digest drifted")
    require(s4.get("reference_bundle_acceptance_canonical_sha256") == ACCEPTANCE_CANONICAL_SHA256, "acceptance digest drifted")
    require(s4.get("reference_bundle_acceptance_production_effective") is True, "reference bundle acceptance not production-effective")

    require(s4.get("execution_authorization_merge_pr") == 117, "execution-authorization PR binding drifted")
    require(s4.get("execution_authorization_exact_head_sha") == AUTH_EXACT_HEAD, "execution-authorization exact head drifted")
    require(s4.get("execution_authorization_exact_head_ci_run_id") == AUTH_EXACT_RUN_ID, "execution-authorization exact-head run ID drifted")
    require(s4.get("execution_authorization_exact_head_ci_run_number") == AUTH_EXACT_RUN_NUMBER, "execution-authorization exact-head run number drifted")
    require(s4.get("execution_authorization_main_sha") == AUTH_MAIN, "execution-authorization main drifted")
    require(s4.get("execution_authorization_postmerge_ci_run_id") == AUTH_RUN_ID, "execution-authorization post-merge run ID drifted")
    require(s4.get("execution_authorization_postmerge_ci_run_number") == AUTH_RUN_NUMBER, "execution-authorization post-merge run number drifted")
    require(s4.get("execution_authorization_canonical_sha256") == AUTHORIZATION_CANONICAL_SHA256, "execution-authorization digest drifted")
    require(s4.get("execution_authorization_production_effective") is True, "execution authorization not production-effective")

    require(s4.get("held_out_item_id") == HELD_OUT_ITEM, "Chopin live held-out binding drifted")
    require(s4.get("held_out_candidate_derivation_authorized") is False, "Chopin candidate derivation became authorized")
    require(s4.get("held_out_evaluation_authorized_by_development_execution_decision") is False, "development decision opened held-out evaluation")
    require(s4.get("readiness_decision") == "NOT_READY", "Stage 4 readiness decision drifted")
    require(s4.get("readiness_blocker_count") == 3, "Stage 4 readiness blocker count drifted")
    require(s4.get("readiness_blocker_codes") == READINESS_BLOCKERS, "Stage 4 readiness blocker set drifted")
    require(s4.get("reference_label_bundle_accepted") is True, "accepted reference bundle current truth drifted")
    require(s4.get("execution_phase") == "real_development_calibration_authorized_not_executed", "execution phase drifted")
    require(s4.get("real_data_calibration_execution_authorized") is True, "real development execution current truth is not authorized")
    require(s4.get("calibration_authorized") is True, "development calibration authorization current truth drifted")
    require(s4.get("real_data_calibration_executed") is False, "current truth falsely claims execution")
    require(s4.get("thresholds_calibrated") is False, "current truth falsely claims calibrated thresholds")
    require(s4.get("resource_limits_calibrated") is False, "current truth falsely claims calibrated resource limits")
    require(s4.get("production_threshold_changes_authorized") is False, "production threshold changes became authorized")
    require(s4.get("production_resource_limit_changes_authorized") is False, "production resource-limit changes became authorized")
    require(s4.get("model_training_authorized") is False, "model training became authorized")
    require(s4.get("publication_authorized") is False, "publication became authorized")
    require(s4.get("held_out_tuning_used") is False, "held-out tuning was used")
    require(s4.get("calibration_state") == "uncalibrated_engineering_defaults", "calibration state drifted")
    require(s4.get("current_execution_blocker_codes") == ["private_observation_metrics_not_available"], "execution dependency drifted")
    require(s4.get("private_observation_metrics_required") is True, "private metric requirement missing")
    require(s4.get("private_observation_metrics_available") is False, "private metrics falsely marked available")
    require(s4.get("raw_observation_metrics_allowed_in_ordinary_git") is False, "raw metrics allowed in ordinary Git")
    require(s4.get("stage4_exit_state") == "not_yet_pass" and s4.get("stage4_exit_pass") is False, "Stage 4 prematurely passed")
    require(s4.get("stage5_entry_eligible") is False and s4.get("stage5_entry_authorized") is False, "Stage 5 prematurely opened")

    workflow = read(".github/workflows/repository-validation.yml")
    for validator in (
        "python tools/validate_stage4_purpose_grants.py",
        "python tools/validate_stage4_reference_labels.py",
        "python tools/validate_stage4_reference_label_completion.py",
        "python tools/validate_stage4_reference_label_acceptance.py",
        "python tools/validate_stage4_execution_authorization.py",
        "python tools/validate_stage4_calibration_evidence.py",
        "python tools/validate_stage4_exit_readiness.py",
        "python tools/validate_stage4_current_truth.py",
    ):
        require(validator in workflow, f"repository validation does not run {validator}")

    for root_name in ("stage1c", "stage2", "stage3", "stage4"):
        root = ROOT / "evidence" / root_name
        if root.exists():
            binaries = [
                str(path.relative_to(ROOT))
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES
            ]
            require(not binaries, f"artifact-like binary bytes found under evidence/{root_name}: {binaries}")

    calibration_code = read("src/st_score_restore/stage4_calibration.py")
    auth_code = read("src/st_score_restore/stage4_execution_authorization.py")
    for token in (
        "real_data_calibration_not_authorized",
        "held_out_tuning_forbidden",
        "source_family_leakage",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
    ):
        require(token in calibration_code, f"Stage 4 calibration contract lost safety token {token}")
    for token in (
        "privateObservationMetricsRequired",
        "rawObservationMetricsAllowedInOrdinaryGit",
        "heldOutEvaluationAuthorized",
        "heldOutTuningAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(token in auth_code, f"execution authorization contract lost safety token {token}")

    if failures:
        print("Stage 4 current-truth validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 current-truth validation: PASS")
    print(f"- current production authorization main: {AUTH_MAIN} / Run #{AUTH_RUN_NUMBER} ({AUTH_RUN_ID})")
    print(f"- execution authorization digest: {AUTHORIZATION_CANONICAL_SHA256}")
    print("- Beethoven + Barley development execution: AUTHORIZED / NOT YET EXECUTED")
    print("- private observation metrics: required / not available / forbidden in ordinary Git")
    print("- accepted reference bundle: true / historical earlier evidence immutable")
    print("- readiness: NOT_READY / 3 blockers")
    print("- held-out evaluation/tuning not opened by development decision")
    print("- production thresholds/resources unchanged; Stage 4 PASS false; Stage 5 blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
