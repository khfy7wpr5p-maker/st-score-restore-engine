from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

from st_score_restore.dataset_contract_common import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]

C15 = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"
C16 = "0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e"
CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
SNAPSHOT = "c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7"
REPORT = "45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834"
STAGE2_EXECUTION = "78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d"
STAGE3_PURPOSE = "3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8"
STAGE3_EXECUTION = "a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6"
STAGE3_LIMITATIONS = "5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d"
STAGE3_ACCEPTANCE = "e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90"
STAGE4_ENTRY_START = "013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8"
STAGE3_ACCEPTANCE_MAIN = "c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0"
STAGE3_TRUTH_MAIN = "2aac96faffcf46e71c41cfb2a37b36597e95e664"
STAGE4_FRAMEWORK_MAIN = "4a5c3db2d767dac235fe12a6bd0e18ba500e7362"
STAGE4_RUN_ID = 33659753403
STAGE4_RUN_NUMBER = 259
RENDERER = "pypdfium2==5.13.0"
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def digest_without(value: dict, field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return canonical_sha256(payload)


def stage_sequence(text: str) -> list[str]:
    for block in re.findall(r"```text\n(.*?)```", text, flags=re.DOTALL):
        if "Stage 12 Music-application integrations" in block:
            return [line.strip() for line in block.splitlines() if line.strip().startswith("Stage ")]
    return []


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    required_paths = (
        "README.md",
        "docs/roadmap.md",
        "docs/technical-specification.md",
        "docs/architecture-consistency-audit.md",
        "docs/stage-3-current-status.md",
        "docs/stage-4-current-status.md",
        "docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json",
        "evidence/stage1c/corpus/coverage-bias-report.v1.json",
        "evidence/stage1c/corpus/catalog.v2.json",
        "evidence/stage1c/corpus/snapshot.expanded.v2.json",
        "evidence/stage1c/corpus/coverage-bias-report.v2.json",
        "evidence/stage1c/corpus/stage1-exit-acceptance.v1.json",
        "evidence/stage2/corpus/execution-evidence.v1.json",
        "evidence/stage2/corpus/stage2-exit-acceptance.v1.json",
        "evidence/stage3/governance/purpose-grants.v1.json",
        "evidence/stage3/corpus/execution-evidence.v1.json",
        "evidence/stage3/corpus/limitations-review.v1.json",
        "evidence/stage3/corpus/stage3-exit-acceptance.v1.json",
        "evidence/stage4/governance/stage4-entry-start.v1.json",
        ".github/workflows/repository-validation.yml",
    )
    for path in required_paths:
        require((ROOT / path).exists(), f"required architecture input missing: {path}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    pyproject = tomllib.loads(read("pyproject.toml"))
    openapi = load("api/openapi.v1.json")
    require(pyproject["project"]["version"] == openapi["info"]["version"], "package/OpenAPI version mismatch")
    require(RENDERER in set(pyproject["project"].get("dependencies", [])), "exact Stage 3 renderer dependency missing")
    require(RENDERER in read("requirements.lock"), "exact Stage 3 renderer lock missing")

    docs = {
        "README": read("README.md"),
        "roadmap": read("docs/roadmap.md"),
        "technical": read("docs/technical-specification.md"),
        "audit": read("docs/architecture-consistency-audit.md"),
        "stage3": read("docs/stage-3-current-status.md"),
        "stage4": read("docs/stage-4-current-status.md"),
    }
    for name, text in docs.items():
        lower = text.lower()
        require("stage 3" in lower and "pass" in lower, f"{name} lost Stage 3 PASS")
        require("stage 4" in lower and "active" in lower, f"{name} lost Stage 4 ACTIVE state")
        require(
            "framework" in lower and ("governance" in lower or "framework/governance" in lower),
            f"{name} does not constrain Stage 4 to framework/governance scope",
        )
        require(
            "not authorized" in lower or "calibrationauthorized=false" in lower or "calibration_authorized" in lower,
            f"{name} lost real-calibration non-authorization",
        )
        require(STAGE4_FRAMEWORK_MAIN in text, f"{name} lost Stage 4 framework production main")
        require(STAGE4_ENTRY_START in text, f"{name} lost Stage 4 entry/start digest")

    for name in ("README", "roadmap", "technical", "audit", "stage3"):
        for digest in (STAGE3_PURPOSE, STAGE3_EXECUTION, STAGE3_LIMITATIONS, STAGE3_ACCEPTANCE):
            require(digest in docs[name], f"{name} lost Stage 3 evidence binding {digest}")

    require("stage 5" in docs["roadmap"].lower() and "blocked" in docs["roadmap"].lower(), "roadmap lost Stage 5 block")
    require("stage 5" in docs["stage4"].lower() and "blocked" in docs["stage4"].lower(), "Stage 4 status lost Stage 5 block")

    roadmap_sequence = stage_sequence(docs["roadmap"])
    technical_sequence = stage_sequence(docs["technical"])
    require(bool(roadmap_sequence) and bool(technical_sequence), "binding stage sequence missing")
    if roadmap_sequence and technical_sequence:
        require(
            [line for line in roadmap_sequence if not line.startswith("Stage 0 ")] == technical_sequence,
            "roadmap/technical stage sequence mismatch",
        )

    c16 = load("evidence/stage1c/corpus/coverage-bias-report.v1.json")
    require(c16.get("snapshotSha256") == C15, "historical C16 snapshot binding drifted")
    require(c16.get("sufficiency", {}).get("state") == "insufficient", "historical C16 was rewritten")
    require(c16.get("sufficiency", {}).get("stage1ExitSupported") is False, "historical C16 unexpectedly supports exit")

    catalog = load("evidence/stage1c/corpus/catalog.v2.json")
    snapshot = load("evidence/stage1c/corpus/snapshot.expanded.v2.json")
    report = load("evidence/stage1c/corpus/coverage-bias-report.v2.json")
    require(canonical_sha256(catalog) == CATALOG, "catalog v2 digest drifted")
    require(canonical_sha256(snapshot) == SNAPSHOT and snapshot.get("catalogSha256") == CATALOG, "snapshot v2 digest/binding drifted")
    require(
        canonical_sha256(report) == REPORT and report.get("snapshotSha256") == SNAPSHOT and report.get("catalogSha256") == CATALOG,
        "coverage report v2 digest/binding drifted",
    )

    stage1 = load("evidence/stage1c/corpus/stage1-exit-acceptance.v1.json")
    require(stage1.get("decision") == "PASS" and stage1.get("stage2EntryEligible") is True, "Stage 1 acceptance drifted")

    stage2_exec = load("evidence/stage2/corpus/execution-evidence.v1.json")
    require(
        stage2_exec.get("evidenceDigest", {}).get("value") == STAGE2_EXECUTION
        and digest_without(stage2_exec, "evidenceDigest") == STAGE2_EXECUTION,
        "Stage 2 execution evidence drifted",
    )
    require(stage2_exec.get("assertions", {}).get("heldOutThresholdTuningUsed") is False, "Stage 2 held-out non-tuning drifted")
    stage2_acceptance = load("evidence/stage2/corpus/stage2-exit-acceptance.v1.json")
    require(
        stage2_acceptance.get("decision") == "PASS"
        and stage2_acceptance.get("stage2ExitPass") is True
        and stage2_acceptance.get("stage3EntryEligible") is True,
        "Stage 2 final acceptance drifted",
    )

    grants = load("evidence/stage3/governance/purpose-grants.v1.json")
    require(canonical_sha256(grants) == STAGE3_PURPOSE, "Stage 3 purpose-grant digest drifted")
    require(grants.get("assertions", {}).get("calibrationAuthorized") is False, "Stage 3 purpose grants unexpectedly authorize calibration")
    require(all(item.get("purpose") == "pdf_pipeline_evaluation" for item in grants.get("grants", [])), "Stage 3 purpose grant scope drifted")

    execution = load("evidence/stage3/corpus/execution-evidence.v1.json")
    require(
        execution.get("evidenceDigest", {}).get("value") == STAGE3_EXECUTION
        and digest_without(execution, "evidenceDigest") == STAGE3_EXECUTION,
        "Stage 3 execution evidence digest drifted",
    )
    summary = execution.get("summary", {})
    require(
        summary.get("itemCount") == 3
        and summary.get("pageCount") == 14
        and summary.get("renderedPageCount") == 12
        and summary.get("reviewRequiredCount") == 0
        and summary.get("anyVectorPagesRasterized") is False
        and summary.get("allPageOrderPreserved") is True,
        "Stage 3 execution summary drifted",
    )
    exec_assertions = execution.get("assertions", {})
    require(exec_assertions.get("heldOutThresholdTuningUsed") is False, "Stage 3 held-out tuning drifted")
    require(exec_assertions.get("realCorpusBytesInGit") is False, "Stage 3 real corpus Git boundary drifted")
    require(exec_assertions.get("stage3ExitPass") is False, "historical Stage 3 execution evidence was rewritten")

    limitations = load("evidence/stage3/corpus/limitations-review.v1.json")
    require(
        limitations.get("reviewDigest", {}).get("value") == STAGE3_LIMITATIONS
        and digest_without(limitations, "reviewDigest") == STAGE3_LIMITATIONS
        and limitations.get("decision") == "PASS_WITH_ACCEPTED_LIMITATIONS",
        "Stage 3 limitations review drifted",
    )

    stage3_acceptance = load("evidence/stage3/corpus/stage3-exit-acceptance.v1.json")
    require(canonical_sha256(stage3_acceptance) == STAGE3_ACCEPTANCE, "Stage 3 final acceptance digest drifted")
    require(
        stage3_acceptance.get("decision") == "PASS"
        and stage3_acceptance.get("stage3ExitPass") is True
        and stage3_acceptance.get("stage4EntryEligible") is True
        and stage3_acceptance.get("stage4Started") is False,
        "Stage 3 final acceptance semantics drifted",
    )

    stage4_decision = load("evidence/stage4/governance/stage4-entry-start.v1.json")
    require(
        stage4_decision.get("decisionDigest", {}).get("value") == STAGE4_ENTRY_START
        and digest_without(stage4_decision, "decisionDigest") == STAGE4_ENTRY_START,
        "Stage 4 entry/start decision digest drifted",
    )
    require(stage4_decision.get("decision") == "APPROVE_FRAMEWORK_START", "Stage 4 entry/start decision drifted")
    scope = stage4_decision.get("scope", {})
    require(scope.get("frameworkImplementationAuthorized") is True, "Stage 4 framework authorization missing")
    for key in (
        "realDataCalibrationExecutionAuthorized",
        "productionThresholdChangesAuthorized",
        "productionResourceLimitChangesAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
    ):
        require(scope.get(key) is False, f"Stage 4 historical start decision unexpectedly authorizes {key}")
    decision_claims = stage4_decision.get("claims", {})
    require(decision_claims.get("stage4Started") is False, "historical Stage 4 pre-start decision was rewritten")
    require(decision_claims.get("calibrationAuthorized") is False, "Stage 4 decision unexpectedly claims calibration authorization")

    granted_safety = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(not granted_safety, f"catalog now has safety_calibration grants but current truth says blocked: {granted_safety}")

    handoff = load("docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json")
    require(handoff.get("main_sha") == STAGE4_FRAMEWORK_MAIN, "live handoff lost Stage 4 framework main")
    require(
        handoff.get("latest_main_ci_run_number") == STAGE4_RUN_NUMBER
        and handoff.get("latest_main_ci_run_id") == STAGE4_RUN_ID
        and handoff.get("latest_main_ci_status") == "success_python_3_11_and_3_12",
        "live handoff lost Stage 4 framework post-merge CI",
    )
    require(handoff.get("stage3_exit_state") == "pass_effective", "live handoff lost Stage 3 PASS")
    require(handoff.get("stage4_entry_state") == "active_framework_governance_only", "live handoff Stage 4 state drifted")
    require(handoff.get("stage4_started") is True, "live handoff does not mark Stage 4 framework started")
    require(handoff.get("stage5_entry_state") == "blocked_pending_stage4_exit", "live handoff Stage 5 block drifted")

    s4 = handoff.get("stage4", {})
    require(s4.get("tracking_issue") == 104, "live handoff Stage 4 issue binding drifted")
    require(s4.get("framework_merge_pr") == 105, "live handoff Stage 4 PR binding drifted")
    require(s4.get("framework_exact_head_sha") == "f1582cccd95e42a1e466ce634ea7019a7f1671d1", "live handoff Stage 4 exact head drifted")
    require(s4.get("framework_exact_head_ci_run_number") == 258, "live handoff Stage 4 exact-head CI drifted")
    require(s4.get("framework_main_sha") == STAGE4_FRAMEWORK_MAIN, "live handoff Stage 4 framework main drifted")
    require(s4.get("framework_postmerge_ci_run_number") == STAGE4_RUN_NUMBER, "live handoff Stage 4 post-merge run drifted")
    require(s4.get("framework_production_effective") is True, "live handoff Stage 4 framework not production-effective")
    require(s4.get("stage4_state") == "active_framework_governance_only" and s4.get("stage4_started") is True, "live handoff Stage 4 active semantics drifted")
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
        "stage5_entry_eligible",
    ):
        require(s4.get(key) is False, f"live handoff unsafe Stage 4 flag became true: {key}")
    require(s4.get("calibration_state") == "uncalibrated_engineering_defaults", "live handoff calibration state drifted")
    require(
        s4.get("blocker_codes") == [
            "no_real_artifact_has_granted_safety_calibration_permission",
            "no_real_calibration_reference_label_bundle_is_accepted",
        ],
        "live handoff Stage 4 blocker set drifted",
    )
    require(s4.get("stage4_exit_state") == "not_yet_pass", "live handoff prematurely exits Stage 4")

    stage4_code = read("src/st_score_restore/stage4_calibration.py")
    for token in (
        "CalibrationObservation",
        "ThresholdCandidate",
        "held_out_tuning_forbidden",
        "source_family_leakage",
        "real_data_calibration_not_authorized",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
    ):
        require(token in stage4_code, f"Stage 4 framework lost safety token {token}")

    workflow = read(".github/workflows/repository-validation.yml")
    validators = (
        "validate_stage1_exit_acceptance.py",
        "validate_stage2_quality_analysis.py",
        "validate_stage2_custody_execution.py",
        "validate_stage2_corpus_execution_evidence.py",
        "validate_stage2_exit_acceptance.py",
        "validate_stage3_pdf_pipeline.py",
        "validate_stage3_custody_execution.py",
        "validate_stage3_real_corpus_runner.py",
        "validate_stage3_real_corpus_execution_evidence.py",
        "validate_stage3_exit_acceptance.py",
        "validate_stage4_entry_start.py",
    )
    for validator in validators:
        require(validator in workflow, f"CI is not wired to {validator}")
    require("pypdfium2" in workflow and "5.13.0" in workflow, "CI renderer-version check drifted")

    for root_name in ("stage1c", "stage2", "stage3", "stage4"):
        root = ROOT / "evidence" / root_name
        if root.exists():
            binaries = [
                str(path.relative_to(ROOT))
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES
            ]
            require(not binaries, f"artifact-like binary bytes found under evidence/{root_name}: {binaries}")

    combined = "\n".join(docs.values())
    for digest in (
        C15,
        C16,
        CATALOG,
        SNAPSHOT,
        REPORT,
        STAGE2_EXECUTION,
        STAGE3_PURPOSE,
        STAGE3_EXECUTION,
        STAGE3_LIMITATIONS,
        STAGE3_ACCEPTANCE,
        STAGE4_ENTRY_START,
    ):
        require(digest in combined, f"current architecture docs lost evidence binding {digest}")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print("- Stage 1: PASS / historical evidence preserved")
    print("- Stage 2: PASS / production-effective")
    print(f"- Stage 3: PASS / production-effective; acceptance {STAGE3_ACCEPTANCE_MAIN}")
    print(f"- Stage 4: ACTIVE framework/governance only at {STAGE4_FRAMEWORK_MAIN} / Run #{STAGE4_RUN_NUMBER}")
    print("- Real-data calibration: blocked / calibrationAuthorized=false")
    print("- Held-out tuning: false / production thresholds and resource limits unchanged")
    print("- Stage 5: blocked pending Stage 4 exit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
