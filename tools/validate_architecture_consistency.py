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
STAGE3_PURPOSE_MAIN = "6ebe160309c562e9841a3c313d5ca507592f1386"
STAGE3_RUNNER_MAIN = "5e682f1933a7167fc142689306352fe53b4b1833"
STAGE3_EVIDENCE_MAIN = "b15d91ff3fbf21b47a0e484b5a337c4611a17355"
STAGE3_ACCEPTANCE_MAIN = "c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0"
PURPOSE_SHA = "3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8"
EXECUTION_SHA = "a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6"
LIMITATIONS_SHA = "5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d"
ACCEPTANCE_SHA = "e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90"
RENDERER = "pypdfium2==5.13.0"

BEETHOVEN = (
    "dataset.item.imslp799143-beethoven-op48-no3.v1",
    "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
    1182561,
)
BARLEY = (
    "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
    "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
    84689,
)
CHOPIN = (
    "dataset.item.imslp82860-chopin-op69.v2",
    "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3",
    1114479,
)
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


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


def restriction_map(permission: dict) -> dict[str, object]:
    result: dict[str, object] = {}
    for restriction in permission.get("restrictions", []):
        if isinstance(restriction, dict) and isinstance(restriction.get("type"), str):
            result[restriction["type"]] = (
                restriction.get("values")
                if "values" in restriction
                else restriction.get("allowed")
            )
    return result


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    pyproject = tomllib.loads(read("pyproject.toml"))
    openapi = load("api/openapi.v1.json")
    require(
        pyproject["project"]["version"] == openapi["info"]["version"],
        "package/OpenAPI version mismatch",
    )
    require(
        RENDERER in set(pyproject["project"].get("dependencies", [])),
        "exact Stage 3 renderer dependency missing",
    )
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

    current_names = (
        "README",
        "roadmap",
        "technical",
        "audit",
        "stage1_current",
        "stage1_exit",
        "coverage",
        "stage2_current",
        "stage3_current",
    )
    for name in current_names:
        lower = docs[name].lower()
        require(
            "stage 2" in lower and ("complete" in lower or "pass" in lower),
            f"{name} lost Stage 2 COMPLETE/PASS",
        )
        require(
            "stage 3" in lower and "pass" in lower and "production-effective" in lower,
            f"{name} does not reflect Stage 3 PASS / production-effective",
        )
        require(
            "stage 4" in lower and "entry eligible" in lower and "not started" in lower,
            f"{name} does not reflect Stage 4 ENTRY ELIGIBLE / NOT STARTED",
        )
        require(
            STAGE3_ACCEPTANCE_MAIN in docs[name],
            f"{name} lost Stage 3 acceptance production main",
        )

    for name in ("README", "roadmap", "technical", "audit", "stage3_current"):
        require(
            STAGE3_CORE in docs[name]
            and STAGE3_RUNNER_MAIN in docs[name]
            and STAGE3_EVIDENCE_MAIN in docs[name]
            and STAGE3_ACCEPTANCE_MAIN in docs[name],
            f"{name} lost Stage 3 production chain",
        )
        require(PURPOSE_SHA in docs[name], f"{name} lost purpose-grant digest")
        require(EXECUTION_SHA in docs[name], f"{name} lost execution-evidence digest")
        require(LIMITATIONS_SHA in docs[name], f"{name} lost limitations-review digest")
        require(ACCEPTANCE_SHA in docs[name], f"{name} lost final-acceptance digest")

    for name in ("README", "roadmap", "technical", "audit", "stage2_current"):
        require(
            STAGE2_EVIDENCE_MAIN in docs[name] and STAGE2_EXECUTION in docs[name],
            f"{name} lost Stage 2 evidence binding",
        )

    require(
        "production-effective" in docs["stage3_grants"].lower()
        and "PR #96" in docs["stage3_grants"]
        and "Run #238" in docs["stage3_grants"],
        "purpose-grant production state drifted",
    )

    historical_custody = docs["stage2_custody"].lower()
    require(
        "active implementation contract" in historical_custody,
        "historical Stage 2 custody contract status drifted",
    )
    require(
        "stage 2 exit" in historical_custody and "accepted separately" in historical_custody,
        "historical Stage 2 separate acceptance drifted",
    )
    require(
        "stage 3" in historical_custody and "not started in this slice" in historical_custody,
        "historical Stage 2 custody slice was rewritten",
    )

    roadmap_stages = stage_sequence(docs["roadmap"])
    technical_stages = stage_sequence(docs["technical"])
    require(bool(roadmap_stages) and bool(technical_stages), "binding stage sequence missing")
    if roadmap_stages and technical_stages:
        require(
            [line for line in roadmap_stages if not line.startswith("Stage 0 ")]
            == technical_stages,
            "roadmap/technical stage sequence mismatch",
        )

    c16 = load("evidence/stage1c/corpus/coverage-bias-report.v1.json")
    require(c16.get("snapshotSha256") == C15, "historical C16 snapshot binding drifted")
    require(
        c16.get("sufficiency", {}).get("state") == "insufficient",
        "historical C16 was rewritten",
    )
    require(
        c16.get("sufficiency", {}).get("stage1ExitSupported") is False,
        "historical C16 unexpectedly supports exit",
    )

    catalog = load("evidence/stage1c/corpus/catalog.v2.json")
    snapshot = load("evidence/stage1c/corpus/snapshot.expanded.v2.json")
    report = load("evidence/stage1c/corpus/coverage-bias-report.v2.json")
    require(canonical_sha256(catalog) == CATALOG, "catalog v2 digest drifted")
    require(
        canonical_sha256(snapshot) == SNAPSHOT and snapshot.get("catalogSha256") == CATALOG,
        "snapshot v2 drifted",
    )
    require(
        canonical_sha256(report) == REPORT
        and report.get("snapshotSha256") == SNAPSHOT
        and report.get("catalogSha256") == CATALOG,
        "report v2 drifted",
    )

    stage1 = load("evidence/stage1c/corpus/stage1-exit-acceptance.v1.json")
    require(
        stage1.get("decision") == "PASS" and stage1.get("stage2EntryEligible") is True,
        "Stage 1 acceptance drifted",
    )

    stage2_exec = load("evidence/stage2/corpus/execution-evidence.v1.json")
    stage2_payload = dict(stage2_exec)
    stage2_digest = stage2_payload.pop("evidenceDigest", {}).get("value")
    require(
        stage2_digest == STAGE2_EXECUTION
        and canonical_sha256(stage2_payload) == STAGE2_EXECUTION,
        "Stage 2 execution evidence drifted",
    )
    stage2_assertions = stage2_exec.get("assertions", {})
    require(
        stage2_assertions.get("stage2ExitPass") is False
        and stage2_assertions.get("stage3EntryAuthorized") is False,
        "historical Stage 2 execution assertions were rewritten",
    )
    require(
        stage2_assertions.get("heldOutThresholdTuningUsed") is False,
        "Stage 2 held-out non-tuning drifted",
    )

    stage2 = load("evidence/stage2/corpus/stage2-exit-acceptance.v1.json")
    require(
        stage2.get("decision") == "PASS"
        and stage2.get("stage2ExitPass") is True
        and stage2.get("stage3EntryEligible") is True,
        "Stage 2 acceptance drifted",
    )
    require(
        stage2.get("evidenceMainSha") == STAGE2_EVIDENCE_MAIN
        and stage2.get("stage3Started") is False,
        "historical Stage 2 acceptance binding drifted",
    )
    require(stage2.get("blockerCodes") == [], "Stage 2 acceptance gained blockers")
    for claim, value in stage2.get("claims", {}).items():
        require(value is False, f"unsupported Stage 2 positive claim: {claim}")

    grants = load("evidence/stage3/governance/purpose-grants.v1.json")
    require(canonical_sha256(grants) == PURPOSE_SHA, "purpose-grant canonical digest drifted")
    require(
        grants.get("grantSetId") == "stage3.purpose-grants.beethoven-barley.v1",
        "purpose-grant set id drifted",
    )
    require(
        grants.get("authorizationSourceCode") == "explicit_user_authorization",
        "purpose-grant authorization source drifted",
    )
    grant_map = {
        item.get("datasetItemId"): item
        for item in grants.get("grants", [])
        if isinstance(item, dict)
    }
    require(set(grant_map) == {BEETHOVEN[0], BARLEY[0]}, "purpose-grant item allowlist drifted")
    for item_id, sha, _size in (BEETHOVEN, BARLEY):
        grant = grant_map.get(item_id, {})
        permission = grant.get("permission", {}) if isinstance(grant, dict) else {}
        restrictions = restriction_map(permission if isinstance(permission, dict) else {})
        require(
            grant.get("artifactSha256") == sha
            and grant.get("purpose") == "pdf_pipeline_evaluation",
            f"grant tuple drifted for {item_id}",
        )
        require(permission.get("status") == "granted", f"grant not active for {item_id}")
        require(
            restrictions.get("split_allowlist") == ["development"],
            f"split restriction drifted for {item_id}",
        )
        require(
            restrictions.get("storage_class_allowlist") == ["managed_standard"],
            f"storage restriction drifted for {item_id}",
        )
        require(
            restrictions.get("environment_allowlist") == ["stage1_offline"],
            f"environment restriction drifted for {item_id}",
        )
        require(
            restrictions.get("external_export") is False,
            f"export restriction drifted for {item_id}",
        )
    for key, value in grants.get("assertions", {}).items():
        require(value is False, f"purpose-grant assertion became true: {key}")

    execution = load("evidence/stage3/corpus/execution-evidence.v1.json")
    require(
        execution.get("evidenceDigest", {}).get("value") == EXECUTION_SHA
        and digest_without(execution, "evidenceDigest") == EXECUTION_SHA,
        "Stage 3 execution-evidence canonical digest drifted",
    )
    require(execution.get("status") == "executed", "Stage 3 execution status drifted")
    require(
        execution.get("repositoryMainSha") == STAGE3_RUNNER_MAIN
        and execution.get("postMergeValidation") == {"runId": 33641537118, "runNumber": 246},
        "Stage 3 runner production binding drifted",
    )
    require(
        execution.get("rendererBindingVersion") == "5.13.0"
        and execution.get("runnerVersion") == "0.1.0",
        "Stage 3 execution runtime binding drifted",
    )

    expected_items = {BEETHOVEN[0], BARLEY[0], CHOPIN[0]}
    require(set(execution.get("itemIds", [])) == expected_items, "Stage 3 execution item set drifted")
    receipts = {
        receipt.get("datasetItemId"): receipt
        for receipt in execution.get("receipts", [])
        if isinstance(receipt, dict)
    }
    require(set(receipts) == expected_items, "Stage 3 receipt set drifted")
    for item_id, sha, size in (BEETHOVEN, BARLEY, CHOPIN):
        receipt = receipts.get(item_id, {})
        expected_purpose = "held_out_evaluation" if item_id == CHOPIN[0] else "pdf_pipeline_evaluation"
        expected_split = "held_out" if item_id == CHOPIN[0] else "development"
        require(receipt.get("byteSize") == size, f"receipt byte size drifted for {item_id}")
        require(
            receipt.get("sourceDigest", {}).get("value") == sha,
            f"receipt SHA-256 drifted for {item_id}",
        )
        require(
            receipt.get("purpose") == expected_purpose and receipt.get("split") == expected_split,
            f"receipt purpose/split drifted for {item_id}",
        )
        require(
            receipt.get("renderer") == {
                "binding": "pypdfium2",
                "bindingVersion": "5.13.0",
                "name": "pdfium",
            },
            f"receipt renderer drifted for {item_id}",
        )
        receipt_assertions = receipt.get("assertions", {})
        require(
            receipt_assertions.get("exactDigestMatched") is True
            and receipt_assertions.get("exactByteSizeMatched") is True
            and receipt_assertions.get("sourceBytesModified") is False
            and receipt_assertions.get("heldOutThresholdTuningUsed") is False
            and receipt_assertions.get("realArtifactBytesInGit") is False,
            f"receipt safety assertions drifted for {item_id}",
        )
        page = receipt.get("pageSummary", {})
        require(page.get("pageOrderPreserved") is True, f"page order drifted for {item_id}")
        require(page.get("vectorPagesRasterized") is False, f"vector rasterization drifted for {item_id}")
        handling = receipt.get("reportHandling", {})
        require(
            handling.get("custodyOnly") is True
            and handling.get("derivativeBytesExported") is False
            and handling.get("detailedManifestExported") is False
            and handling.get("detailedManifestPublic") is False,
            f"receipt public/private boundary drifted for {item_id}",
        )

    summary = execution.get("summary", {})
    require(
        summary.get("itemCount") == 3
        and summary.get("pageCount") == 14
        and summary.get("renderedPageCount") == 12
        and summary.get("reviewRequiredCount") == 0
        and summary.get("developmentCount") == 2
        and summary.get("heldOutCount") == 1,
        "Stage 3 execution summary drifted",
    )
    require(
        summary.get("classificationCounts") == {"raster_only": 12, "vector_only": 2},
        "Stage 3 classification summary drifted",
    )
    require(
        summary.get("statusCounts") == {"preserved_vector_page": 2, "rendered_raster_page": 12},
        "Stage 3 status summary drifted",
    )
    require(summary.get("allPageOrderPreserved") is True, "Stage 3 page order not preserved")
    require(summary.get("anyVectorPagesRasterized") is False, "Stage 3 vector rasterization occurred")
    execution_assertions = execution.get("assertions", {})
    require(
        execution_assertions.get("heldOutThresholdTuningUsed") is False
        and execution_assertions.get("realCorpusBytesInGit") is False
        and execution_assertions.get("sourceBytesModified") is False,
        "Stage 3 execution safety assertions drifted",
    )
    require(
        execution_assertions.get("stage3ExitPass") is False
        and execution_assertions.get("stage4EntryAuthorized") is False,
        "historical Stage 3 execution evidence was rewritten to authorize exit",
    )
    for key in ("trainingAuthorized", "calibrationAuthorized", "publicationAuthorized"):
        require(execution_assertions.get(key) is False, f"Stage 3 execution unexpectedly authorizes {key}")

    limitations = load("evidence/stage3/corpus/limitations-review.v1.json")
    require(
        limitations.get("reviewDigest", {}).get("value") == LIMITATIONS_SHA
        and digest_without(limitations, "reviewDigest") == LIMITATIONS_SHA,
        "Stage 3 limitations-review canonical digest drifted",
    )
    require(
        limitations.get("decision") == "PASS_WITH_ACCEPTED_LIMITATIONS",
        "Stage 3 limitations decision drifted",
    )
    require(
        limitations.get("executionEvidenceCanonicalSha256") == EXECUTION_SHA,
        "Stage 3 limitations execution binding drifted",
    )
    observed = limitations.get("observedCoverage", {})
    require(
        observed.get("itemCount") == 3
        and observed.get("pageCount") == 14
        and observed.get("rasterOnlyPageCount") == 12
        and observed.get("vectorOnlyPageCount") == 2
        and observed.get("hybridPageCount") == 0
        and observed.get("reviewRequiredCount") == 0,
        "Stage 3 limitations observed coverage drifted",
    )
    verified = limitations.get("verifiedInvariants", {})
    require(
        verified.get("exactSourceIdentity") is True
        and verified.get("pageOrderPreserved") is True
        and verified.get("vectorPagesRasterized") is False
        and verified.get("heldOutThresholdTuningUsed") is False
        and verified.get("realCorpusBytesInGit") is False,
        "Stage 3 limitations invariant verification drifted",
    )
    for claim, value in limitations.get("claims", {}).items():
        require(value is False, f"unsupported Stage 3 limitations positive claim: {claim}")

    acceptance = load("evidence/stage3/corpus/stage3-exit-acceptance.v1.json")
    require(canonical_sha256(acceptance) == ACCEPTANCE_SHA, "Stage 3 acceptance canonical digest drifted")
    require(
        acceptance.get("decisionId") == "stage3.exit.acceptance.v1"
        and acceptance.get("decision") == "PASS"
        and acceptance.get("acceptanceAuthority") == "issue-90-autonomous-objective-gates",
        "Stage 3 acceptance identity/decision drifted",
    )
    require(acceptance.get("evidenceMainSha") == STAGE3_EVIDENCE_MAIN, "Stage 3 evidence-main binding drifted")
    require(
        acceptance.get("exactHeadPrVerification") == {
            "prNumber": 101,
            "headSha": "88737a8dec70e8c84075e141dd9364794b3605bf",
            "runId": 33645447424,
            "runNumber": 250,
            "python311": "success",
            "python312": "success",
        },
        "Stage 3 evidence exact-head verification drifted",
    )
    require(
        acceptance.get("postMergeCi") == {
            "runId": 33645607053,
            "runNumber": 251,
            "event": "push",
            "python311": "success",
            "python312": "success",
        },
        "Stage 3 evidence post-merge binding drifted",
    )
    require(
        acceptance.get("evidenceDigests") == {
            "realCorpusExecutionEvidenceCanonicalSha256": EXECUTION_SHA,
            "limitationsReviewCanonicalSha256": LIMITATIONS_SHA,
            "purposeGrantCanonicalSha256": PURPOSE_SHA,
            "catalogV2CanonicalSha256": CATALOG,
        },
        "Stage 3 acceptance evidence-digest set drifted",
    )
    require(
        acceptance.get("acceptedLimitations") == limitations.get("acceptedLimitations"),
        "Stage 3 accepted limitations do not match review",
    )
    require(
        acceptance.get("stage3ExitPass") is True
        and acceptance.get("stage4EntryEligible") is True
        and acceptance.get("stage4Started") is False
        and acceptance.get("blockerCodes") == [],
        "Stage 3 final transition flags drifted",
    )
    require(
        acceptance.get("acceptedPurpose") == "stage4-safety-calibration-entry",
        "Stage 3 accepted purpose drifted",
    )
    for claim, value in acceptance.get("claims", {}).items():
        require(value is False, f"unsupported Stage 3 acceptance positive claim: {claim}")

    handoff = load("docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json")
    require(
        handoff.get("main_sha") == STAGE3_ACCEPTANCE_MAIN,
        "live handoff Stage 3 acceptance main drifted",
    )
    require(
        handoff.get("latest_main_ci_run_number") == 253
        and handoff.get("latest_main_ci_run_id") == 33646323461
        and handoff.get("latest_main_ci_status") == "success_python_3_11_and_3_12",
        "live handoff latest acceptance-main CI drifted",
    )
    require(
        handoff.get("active_branch") == "main" and handoff.get("active_pr") is None,
        "live handoff production checkpoint should not claim an active runtime PR",
    )
    require(handoff.get("stage2_exit_state") == "pass_effective", "live handoff lost Stage 2 PASS")
    require(handoff.get("stage3_exit_state") == "pass_effective", "live handoff lost Stage 3 PASS")
    require(
        handoff.get("stage4_entry_state") == "eligible_not_started"
        and handoff.get("stage4_started") is False,
        "live handoff Stage 4 state drifted",
    )

    s3 = handoff.get("stage3", {})
    require(
        s3.get("entry_main_sha") == STAGE3_ENTRY and s3.get("entry_ci_run_number") == 228,
        "live handoff Stage 3 entry evidence drifted",
    )
    require(
        s3.get("core_merge_main_sha") == STAGE3_CORE
        and s3.get("authorized_execution_main_sha") == STAGE3_AUTH
        and s3.get("purpose_grant_main_sha") == STAGE3_PURPOSE_MAIN
        and s3.get("real_corpus_runner_main_sha") == STAGE3_RUNNER_MAIN,
        "live handoff Stage 3 production chain drifted",
    )
    require(
        s3.get("purpose_grant_canonical_sha256") == PURPOSE_SHA
        and s3.get("purpose_grant_production_effective") is True,
        "live handoff purpose-grant state drifted",
    )
    require(
        s3.get("renderer") == "pdfium"
        and s3.get("renderer_binding") == "pypdfium2"
        and s3.get("renderer_binding_version") == "5.13.0",
        "live handoff renderer drifted",
    )
    require(
        s3.get("vector_pages_rasterized") is False
        and s3.get("hybrid_pages_rasterized") is False
        and s3.get("held_out_tuning_used") is False,
        "live handoff rasterization/non-tuning boundary drifted",
    )
    require(
        s3.get("beethoven_exact_bytes_verified") is True
        and s3.get("barley_exact_bytes_verified") is True
        and s3.get("chopin_exact_bytes_verified") is True
        and s3.get("source_bytes_in_ordinary_git") is False,
        "live handoff exact-byte/Git boundary drifted",
    )
    require(
        s3.get("real_corpus_execution_complete") is True
        and s3.get("execution_evidence_main_sha") == STAGE3_EVIDENCE_MAIN
        and s3.get("real_corpus_execution_evidence_canonical_sha256") == EXECUTION_SHA
        and s3.get("limitations_review_canonical_sha256") == LIMITATIONS_SHA,
        "live handoff Stage 3 evidence state drifted",
    )
    require(
        s3.get("execution_evidence_merge_pr") == 101
        and s3.get("execution_evidence_exact_head_sha") == "88737a8dec70e8c84075e141dd9364794b3605bf"
        and s3.get("execution_evidence_exact_head_ci_run_number") == 250
        and s3.get("execution_evidence_postmerge_ci_run_number") == 251,
        "live handoff Stage 3 evidence CI chain drifted",
    )
    require(
        s3.get("final_acceptance_merge_pr") == 102
        and s3.get("final_acceptance_exact_head_sha") == "959474ac8487eb15dfcaf27b3a1224872182f03b"
        and s3.get("final_acceptance_exact_head_ci_run_number") == 252
        and s3.get("final_acceptance_main_sha") == STAGE3_ACCEPTANCE_MAIN
        and s3.get("final_acceptance_postmerge_ci_run_number") == 253
        and s3.get("final_acceptance_canonical_sha256") == ACCEPTANCE_SHA
        and s3.get("final_acceptance_decision") == "PASS"
        and s3.get("final_acceptance_production_effective") is True,
        "live handoff Stage 3 final acceptance chain drifted",
    )
    require(
        s3.get("stage3_exit_state") == "pass_effective"
        and s3.get("stage4_entry_eligible") is True
        and s3.get("stage4_started") is False,
        "live handoff Stage 3/4 transition drifted",
    )

    pdf = read("src/st_score_restore/pdf_pipeline.py")
    custody = read("src/st_score_restore/stage3_custody_execution.py")
    purpose = read("src/st_score_restore/stage3_purpose_grants.py")
    runner = read("src/st_score_restore/stage3_real_corpus_execution.py")
    workflow = read(".github/workflows/repository-validation.yml")

    for token in (
        "process_pdf_bytes",
        "pypdfium2",
        "preserved_vector_page",
        "render_raster_only",
        "vectorPagesRasterized",
        "originalFallbackAvailable",
        "heldOutTuningUsed",
    ):
        require(token in pdf, f"Stage 3 PDF pipeline lost {token}")
    require(
        '"development": "pdf_pipeline_evaluation"' in custody
        and '"held_out": "held_out_evaluation"' in custody,
        "Stage 3 split-purpose mapping drifted",
    )
    for token in ("exact_sha256_mismatch", "detailedManifestPublic", "heldOutThresholdTuningUsed"):
        require(token in custody, f"Stage 3 custody executor lost {token}")
    require(
        "run_purpose_granted_pdf_pipeline_execution" in purpose and PURPOSE_SHA in purpose,
        "Stage 3 purpose-grant runtime drifted",
    )
    require("execute_stage3_real_corpus_batch" in runner, "Stage 3 real-corpus runner entry point missing")
    require(
        "REQUIRED_RENDERER_BINDING_VERSION" in runner and "5.13.0" in runner,
        "Stage 3 runner renderer gate drifted",
    )
    require(
        all(item_id in runner for item_id in (BEETHOVEN[0], BARLEY[0], CHOPIN[0])),
        "Stage 3 runner exact item allowlist drifted",
    )
    require(
        '"stage3ExitPass": False' in runner
        and '"stage4EntryAuthorized": False' in runner
        and '"heldOutThresholdTuningUsed": False' in runner,
        "Stage 3 runner historical safety assertions drifted",
    )

    for validator in (
        "validate_stage2_quality_analysis.py",
        "validate_stage2_custody_execution.py",
        "validate_stage2_corpus_execution_evidence.py",
        "validate_stage2_exit_acceptance.py",
        "validate_stage3_pdf_pipeline.py",
        "validate_stage3_custody_execution.py",
        "validate_stage3_real_corpus_runner.py",
        "validate_stage3_real_corpus_execution_evidence.py",
        "validate_stage3_exit_acceptance.py",
    ):
        require(validator in workflow, f"CI is not wired to {validator}")
    require("pypdfium2" in workflow and "5.13.0" in workflow, "CI renderer-version check drifted")
    require(
        "pypdfium2==5.13.0" in docs["stage3_adr"]
        and "accepted" in docs["stage3_adr"].lower(),
        "ADR 0017 renderer/acceptance binding drifted",
    )
    require(
        "not silently rasterized" in docs["stage3_adr"].lower(),
        "ADR 0017 lost no-silent-rasterization rule",
    )

    for root_name in ("stage1c", "stage2", "stage3"):
        root = ROOT / "evidence" / root_name
        if root.exists():
            binaries = [
                str(path.relative_to(ROOT))
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES
            ]
            require(
                not binaries,
                f"real-artifact-like bytes found under evidence/{root_name}: {binaries}",
            )

    combined = "\n".join(docs.values())
    for digest in (
        C15,
        C16,
        CATALOG,
        SNAPSHOT,
        REPORT,
        STAGE2_EXECUTION,
        PURPOSE_SHA,
        EXECUTION_SHA,
        LIMITATIONS_SHA,
        ACCEPTANCE_SHA,
    ):
        require(digest in combined, f"architecture/status docs lost evidence binding {digest}")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print("- Stage 1: PASS / historical evidence preserved")
    print("- Stage 2: PASS / production-effective")
    print(f"- Stage 3: PASS / production-effective at {STAGE3_ACCEPTANCE_MAIN} / Run #253")
    print(f"- Stage 3 execution evidence: {EXECUTION_SHA}")
    print("- Real batch: 3 items / 14 pages / 12 raster rendered / 2 vector preserved / 0 review-required")
    print("- Held-out tuning: false / real or derivative bytes in ordinary Git: false")
    print("- Stage 4: ENTRY ELIGIBLE / NOT STARTED")
    print("- Calibration/training/publication authorization: not inferred")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
