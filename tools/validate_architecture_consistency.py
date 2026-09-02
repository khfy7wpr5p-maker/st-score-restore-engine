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
STAGE2_ENTRY = "936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6"
STAGE2_EVIDENCE_MAIN = "ffea7f5aa618187f3cabcfb49801804e3f6658bf"
STAGE2_EXECUTION = "78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d"
STAGE3_ENTRY = "87198a5a917ab6b3efc277762016a5f5b0dd3aab"
STAGE3_CORE = "29b4244eeaeb2239ff959e6dd6d4128311f005fa"
STAGE3_AUTH = "d834ed42e3f553308aef7f6adb7e8cb873593f0b"
STAGE3_MAIN = "6ebe160309c562e9841a3c313d5ca507592f1386"
PURPOSE_SHA = "3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8"
BRANCH = "stage3-real-corpus-runner"
ACTIVE_PR = 99
CLOSED_PREDECESSOR_PR = 98
RENDERER = "pypdfium2==5.13.0"

BEETHOVEN = ("dataset.item.imslp799143-beethoven-op48-no3.v1", "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c")
BARLEY = ("dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1", "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e")
CHOPIN = "dataset.item.imslp82860-chopin-op69.v2"
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load(path: str) -> dict:
    return json.loads(read(path))


def stage_sequence(text: str) -> list[str]:
    for block in re.findall(r"```text\n(.*?)```", text, flags=re.DOTALL):
        if "Stage 12 Music-application integrations" in block:
            return [line.strip() for line in block.splitlines() if line.strip().startswith("Stage ")]
    return []


def restriction_map(permission: dict) -> dict[str, object]:
    result: dict[str, object] = {}
    for restriction in permission.get("restrictions", []):
        if isinstance(restriction, dict) and isinstance(restriction.get("type"), str):
            result[restriction["type"]] = restriction.get("values") if "values" in restriction else restriction.get("allowed")
    return result


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

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
        "stage1_current": read("docs/stage-1c-current-status.md"),
        "stage1_exit": read("docs/stage-1-exit-evidence.md"),
        "coverage": read("docs/stage-1-coverage-and-bias-register.md"),
        "stage2_current": read("docs/stage-2-current-status.md"),
        "stage2_custody": read("docs/stage-2-approved-custody-execution-contract.md"),
        "stage3_current": read("docs/stage-3-current-status.md"),
        "stage3_grants": read("docs/stage-3-purpose-grants.md"),
        "stage3_adr": read("docs/adr/0017-stage3-pdfium-multipage-pipeline.md"),
    }

    for name in ("README", "roadmap", "technical", "audit", "stage2_current", "stage3_current"):
        lower = docs[name].lower()
        require("stage 2" in lower and ("complete" in lower or "pass" in lower), f"{name} lost Stage 2 COMPLETE/PASS")
        require("stage 3" in lower and "active" in lower, f"{name} lost Stage 3 ACTIVE")
        require("stage 4" in lower and "blocked" in lower, f"{name} lost Stage 4 blocked boundary")
        require(STAGE3_ENTRY in docs[name], f"{name} lost Stage 3 entry main")

    for name in ("README", "roadmap", "technical", "audit", "stage3_current"):
        require(STAGE3_CORE in docs[name] and STAGE3_MAIN in docs[name], f"{name} lost Stage 3 production chain")
        require(PURPOSE_SHA in docs[name], f"{name} lost purpose-grant digest")
        require("PR #99" in docs[name], f"{name} does not identify active replacement PR #99")

    for name in ("README", "roadmap", "technical", "audit", "stage2_current"):
        require(STAGE2_EVIDENCE_MAIN in docs[name] and STAGE2_EXECUTION in docs[name], f"{name} lost Stage 2 evidence binding")

    for name in ("stage1_current", "stage1_exit", "coverage"):
        lower = docs[name].lower()
        require("stage 2" in lower and ("complete" in lower or "pass" in lower), f"{name} still presents Stage 2 as active")
        require("stage 3" in lower and "active" in lower, f"{name} does not reflect Stage 3 ACTIVE")
        require("stage 4" in lower and "blocked" in lower, f"{name} does not reflect Stage 4 blocked")

    require(BRANCH in docs["stage2_current"] and "PR #99" in docs["stage2_current"], "Stage 2 handoff lost active replacement branch/PR")
    require("PR #98" in docs["stage3_current"] and "closed unmerged" in docs["stage3_current"].lower(), "Stage 3 current-status lost predecessor PR closure semantics")
    require("Run #243" in docs["stage3_current"], "Stage 3 current-status lost predecessor exact-head CI evidence")
    require("production-effective" in docs["stage3_grants"].lower() and "PR #96" in docs["stage3_grants"] and "Run #238" in docs["stage3_grants"], "purpose-grant production state drifted")

    historical_custody = docs["stage2_custody"].lower()
    require("active implementation contract" in historical_custody, "historical Stage 2 custody contract status drifted")
    require("stage 2 exit" in historical_custody and "accepted separately" in historical_custody, "historical Stage 2 separate acceptance drifted")
    require("stage 3" in historical_custody and "not started in this slice" in historical_custody, "historical Stage 2 custody slice was rewritten")

    roadmap_stages = stage_sequence(docs["roadmap"])
    technical_stages = stage_sequence(docs["technical"])
    require(bool(roadmap_stages) and bool(technical_stages), "binding stage sequence missing")
    if roadmap_stages and technical_stages:
        require([line for line in roadmap_stages if not line.startswith("Stage 0 ")] == technical_stages, "roadmap/technical stage sequence mismatch")

    c16 = load("evidence/stage1c/corpus/coverage-bias-report.v1.json")
    require(c16.get("snapshotSha256") == C15, "historical C16 snapshot binding drifted")
    require(c16.get("sufficiency", {}).get("state") == "insufficient", "historical C16 was rewritten")
    require(c16.get("sufficiency", {}).get("stage1ExitSupported") is False, "historical C16 unexpectedly supports exit")

    catalog = load("evidence/stage1c/corpus/catalog.v2.json")
    snapshot = load("evidence/stage1c/corpus/snapshot.expanded.v2.json")
    report = load("evidence/stage1c/corpus/coverage-bias-report.v2.json")
    require(canonical_sha256(catalog) == CATALOG, "catalog v2 digest drifted")
    require(canonical_sha256(snapshot) == SNAPSHOT and snapshot.get("catalogSha256") == CATALOG, "snapshot v2 drifted")
    require(canonical_sha256(report) == REPORT and report.get("snapshotSha256") == SNAPSHOT and report.get("catalogSha256") == CATALOG, "report v2 drifted")

    stage1 = load("evidence/stage1c/corpus/stage1-exit-acceptance.v1.json")
    require(stage1.get("decision") == "PASS" and stage1.get("stage2EntryEligible") is True, "Stage 1 acceptance drifted")

    stage2_exec = load("evidence/stage2/corpus/execution-evidence.v1.json")
    stage2_payload = dict(stage2_exec)
    stage2_digest = stage2_payload.pop("evidenceDigest", {}).get("value")
    require(stage2_digest == STAGE2_EXECUTION and canonical_sha256(stage2_payload) == STAGE2_EXECUTION, "Stage 2 execution evidence drifted")
    assertions = stage2_exec.get("assertions", {})
    require(assertions.get("stage2ExitPass") is False and assertions.get("stage3EntryAuthorized") is False, "historical Stage 2 execution assertions were rewritten")
    require(assertions.get("heldOutThresholdTuningUsed") is False, "Stage 2 held-out non-tuning drifted")

    stage2 = load("evidence/stage2/corpus/stage2-exit-acceptance.v1.json")
    require(stage2.get("decision") == "PASS" and stage2.get("stage2ExitPass") is True and stage2.get("stage3EntryEligible") is True, "Stage 2 acceptance drifted")
    require(stage2.get("evidenceMainSha") == STAGE2_EVIDENCE_MAIN and stage2.get("stage3Started") is False, "historical Stage 2 acceptance binding drifted")
    require(stage2.get("blockerCodes") == [], "Stage 2 acceptance gained blockers")
    for claim, value in stage2.get("claims", {}).items():
        require(value is False, f"unsupported Stage 2 positive claim: {claim}")

    grants = load("evidence/stage3/governance/purpose-grants.v1.json")
    require(canonical_sha256(grants) == PURPOSE_SHA, "purpose-grant canonical digest drifted")
    require(grants.get("grantSetId") == "stage3.purpose-grants.beethoven-barley.v1", "purpose-grant set id drifted")
    require(grants.get("authorizationSourceCode") == "explicit_user_authorization", "purpose-grant authorization source drifted")
    grant_map = {item.get("datasetItemId"): item for item in grants.get("grants", []) if isinstance(item, dict)}
    require(set(grant_map) == {BEETHOVEN[0], BARLEY[0]}, "purpose-grant item allowlist drifted")
    for item_id, sha in (BEETHOVEN, BARLEY):
        grant = grant_map.get(item_id, {})
        permission = grant.get("permission", {}) if isinstance(grant, dict) else {}
        r = restriction_map(permission if isinstance(permission, dict) else {})
        require(grant.get("artifactSha256") == sha and grant.get("purpose") == "pdf_pipeline_evaluation", f"grant tuple drifted for {item_id}")
        require(permission.get("status") == "granted", f"grant not active for {item_id}")
        require(r.get("split_allowlist") == ["development"], f"split restriction drifted for {item_id}")
        require(r.get("storage_class_allowlist") == ["managed_standard"], f"storage restriction drifted for {item_id}")
        require(r.get("environment_allowlist") == ["stage1_offline"], f"environment restriction drifted for {item_id}")
        require(r.get("external_export") is False, f"export restriction drifted for {item_id}")
    for key, value in grants.get("assertions", {}).items():
        require(value is False, f"purpose-grant assertion became true: {key}")

    handoff = load("docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json")
    require(handoff.get("main_sha") == STAGE3_MAIN, "live handoff production main drifted")
    require(handoff.get("latest_main_ci_run_number") == 238 and handoff.get("latest_main_ci_run_id") == 33620323970, "live handoff latest main CI drifted")
    require(handoff.get("active_branch") == BRANCH and handoff.get("active_pr") == ACTIVE_PR, "live handoff active PR/branch drifted")
    require(handoff.get("closed_predecessor_pr") == CLOSED_PREDECESSOR_PR and handoff.get("closed_predecessor_pr_merged") is False, "live handoff predecessor PR state drifted")
    require(handoff.get("stage2_exit_state") == "pass_effective", "live handoff lost Stage 2 PASS")
    require(handoff.get("stage3_entry_state") == "satisfied" and handoff.get("stage3_started") is True, "live handoff lost Stage 3 entry")
    require(handoff.get("stage3_exit_state") == "not_yet_pass", "live handoff prematurely passes Stage 3")
    require(handoff.get("stage4_entry_state") == "blocked_pending_stage3_exit", "live handoff does not block Stage 4")

    s3 = handoff.get("stage3", {})
    require(s3.get("entry_main_sha") == STAGE3_ENTRY and s3.get("entry_ci_run_number") == 228, "live handoff Stage 3 entry evidence drifted")
    require(s3.get("core_merge_main_sha") == STAGE3_CORE and s3.get("core_postmerge_ci_run_number") == 232, "live handoff Stage 3 core evidence drifted")
    require(s3.get("authorized_execution_main_sha") == STAGE3_AUTH and s3.get("authorized_execution_postmerge_ci_run_number") == 235, "live handoff authorized execution drifted")
    require(s3.get("purpose_grant_main_sha") == STAGE3_MAIN and s3.get("purpose_grant_postmerge_ci_run_number") == 238, "live handoff purpose-grant production chain drifted")
    require(s3.get("purpose_grant_canonical_sha256") == PURPOSE_SHA and s3.get("purpose_grant_production_effective") is True, "live handoff purpose-grant state drifted")
    require(s3.get("active_pr") == ACTIVE_PR and s3.get("closed_predecessor_pr") == CLOSED_PREDECESSOR_PR, "live handoff Stage 3 PR transition drifted")
    require(s3.get("renderer") == "pdfium" and s3.get("renderer_binding_version") == "5.13.0", "live handoff renderer drifted")
    require(s3.get("vector_pages_rasterized") is False and s3.get("hybrid_pages_rasterized") is False, "live handoff allows silent rasterization")
    require(s3.get("held_out_tuning_used") is False, "live handoff claims held-out tuning")
    require(s3.get("beethoven_permission_state") == "granted_via_stage3_overlay" and s3.get("barley_permission_state") == "granted_via_stage3_overlay", "live handoff development grant state drifted")
    require(s3.get("held_out_chopin_permission_state") == "granted_existing_held_out", "live handoff Chopin state drifted")
    require(s3.get("real_corpus_execution_complete") is False, "live handoff prematurely claims real corpus completion")

    pdf = read("src/st_score_restore/pdf_pipeline.py")
    custody = read("src/st_score_restore/stage3_custody_execution.py")
    purpose = read("src/st_score_restore/stage3_purpose_grants.py")
    runner = read("src/st_score_restore/stage3_real_corpus_execution.py")
    workflow = read(".github/workflows/repository-validation.yml")

    for token in ("process_pdf_bytes", "pypdfium2", "preserved_vector_page", "render_raster_only", "vectorPagesRasterized", "originalFallbackAvailable", "heldOutTuningUsed"):
        require(token in pdf, f"Stage 3 PDF pipeline lost {token}")
    require('"development": "pdf_pipeline_evaluation"' in custody and '"held_out": "held_out_evaluation"' in custody, "Stage 3 split-purpose mapping drifted")
    for token in ("exact_sha256_mismatch", "detailedManifestPublic", "heldOutThresholdTuningUsed"):
        require(token in custody, f"Stage 3 custody executor lost {token}")
    require("run_purpose_granted_pdf_pipeline_execution" in purpose and PURPOSE_SHA in purpose, "Stage 3 purpose-grant runtime drifted")
    require("execute_stage3_real_corpus_batch" in runner, "Stage 3 real-corpus runner entry point missing")
    require("REQUIRED_RENDERER_BINDING_VERSION" in runner and "5.13.0" in runner, "Stage 3 runner renderer gate drifted")
    require(all(token in runner for token in (BEETHOVEN[0], BARLEY[0], CHOPIN)), "Stage 3 runner exact item allowlist drifted")
    require('"stage3ExitPass": False' in runner and '"stage4EntryAuthorized": False' in runner and '"heldOutThresholdTuningUsed": False' in runner, "Stage 3 runner safety assertions drifted")

    for validator in (
        "validate_stage2_quality_analysis.py",
        "validate_stage2_custody_execution.py",
        "validate_stage2_corpus_execution_evidence.py",
        "validate_stage2_exit_acceptance.py",
        "validate_stage3_pdf_pipeline.py",
        "validate_stage3_custody_execution.py",
        "validate_stage3_real_corpus_runner.py",
    ):
        require(validator in workflow, f"CI is not wired to {validator}")
    require("pypdfium2" in workflow and "5.13.0" in workflow, "CI renderer-version check drifted")
    require("pypdfium2==5.13.0" in docs["stage3_adr"] and "accepted" in docs["stage3_adr"].lower(), "ADR 0017 renderer/acceptance binding drifted")
    require("not silently rasterized" in docs["stage3_adr"].lower(), "ADR 0017 lost no-silent-rasterization rule")

    for root_name in ("stage1c", "stage2", "stage3"):
        root = ROOT / "evidence" / root_name
        if root.exists():
            binaries = [str(path.relative_to(ROOT)) for path in root.rglob("*") if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES]
            require(not binaries, f"real-artifact-like bytes found under evidence/{root_name}: {binaries}")

    combined = "\n".join(docs.values())
    for digest in (C15, C16, CATALOG, SNAPSHOT, REPORT, STAGE2_EXECUTION, PURPOSE_SHA):
        require(digest in combined, f"architecture/status docs lost evidence binding {digest}")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print("- Stage 1: PASS / historical evidence preserved")
    print("- Stage 2: PASS / production-effective")
    print(f"- Stage 3 production main: {STAGE3_MAIN} / Run #238 PASS")
    print(f"- Stage 3 purpose grant: production-effective / {PURPOSE_SHA}")
    print("- Draft PR #98: closed unmerged after connector transition failure")
    print("- Active replacement: non-draft PR #99 / fresh exact-head CI required after head movement")
    print("- Beethoven/Barley: exact Stage 3 overlay only")
    print("- Chopin: held-out evaluation only / non-tuning")
    print("- Stage 3 real corpus execution: not complete")
    print("- Stage 4: blocked pending Stage 3 final exit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
