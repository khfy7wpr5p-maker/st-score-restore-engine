from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

from st_score_restore.dataset_manifest import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_C15_SNAPSHOT = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"
EXPECTED_C16_REPORT = "0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e"
EXPECTED_V2_CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
EXPECTED_V2_SNAPSHOT = "c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7"
EXPECTED_V2_REPORT = "45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834"
STAGE2_ENTRY_MAIN = "936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6"
STAGE2_EVIDENCE_MAIN = "ffea7f5aa618187f3cabcfb49801804e3f6658bf"
STAGE2_EXECUTION_EVIDENCE = "78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d"
REAL_ARTIFACT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _json(path: str) -> dict:
    return json.loads(_read(path))


def _binding_stages(text: str) -> list[str]:
    blocks = re.findall(r"```text\n(.*?)```", text, flags=re.DOTALL)
    for block in blocks:
        if "Stage 12 Music-application integrations" in block:
            return [line.strip() for line in block.splitlines() if line.strip().startswith("Stage ")]
    return []


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    pyproject = tomllib.loads(_read("pyproject.toml"))
    openapi = _json("api/openapi.v1.json")
    require(pyproject["project"]["version"] == openapi["info"]["version"], "package/OpenAPI version mismatch")

    docs = {
        "README": _read("README.md"),
        "roadmap": _read("docs/roadmap.md"),
        "technical": _read("docs/technical-specification.md"),
        "stage1_current": _read("docs/stage-1c-current-status.md"),
        "stage1_exit": _read("docs/stage-1-exit-evidence.md"),
        "dataset_card": _read("docs/stage-1-dataset-card.md"),
        "coverage_register": _read("docs/stage-1-coverage-and-bias-register.md"),
        "stage2_current": _read("docs/stage-2-current-status.md"),
        "stage2_custody": _read("docs/stage-2-approved-custody-execution-contract.md"),
        "audit": _read("docs/architecture-consistency-audit.md"),
    }

    for name in ("README", "roadmap", "technical", "stage2_current", "audit"):
        lowered = docs[name].lower()
        require("stage 2" in lowered and ("complete" in lowered or "pass" in lowered), f"{name} does not record Stage 2 COMPLETE/PASS acceptance state")
        require("stage 3" in lowered and "eligible" in lowered and "not started" in lowered, f"{name} does not record Stage 3 ENTRY ELIGIBLE / NOT STARTED")
        require(STAGE2_EVIDENCE_MAIN in docs[name], f"{name} does not bind Stage 2 evidence main")
        require(STAGE2_EXECUTION_EVIDENCE in docs[name], f"{name} does not bind frozen Stage 2 execution evidence")

    custody_lower = docs["stage2_custody"].lower()
    require("active implementation contract" in custody_lower, "Stage 2 custody contract lost active implementation status")
    require("stage 2 exit" in custody_lower and "accepted separately" in custody_lower, "Stage 2 custody contract does not preserve separate acceptance semantics")
    require("stage 3" in custody_lower and "not started" in custody_lower, "Stage 2 custody contract does not preserve Stage 3 not-started state")

    for name in ("stage1_current", "stage1_exit", "dataset_card", "coverage_register"):
        lowered = docs[name].lower()
        require("pass" in lowered or "complete" in lowered, f"{name} does not preserve accepted Stage 1 state")
        require("stage 2" in lowered, f"{name} lost Stage 2 transition/use boundary")

    road_stages = _binding_stages(docs["roadmap"])
    technical_stages = _binding_stages(docs["technical"])
    require(bool(road_stages), "roadmap binding stage sequence not found")
    require(bool(technical_stages), "technical-spec binding stage sequence not found")
    if road_stages and technical_stages:
        road_without_stage0 = [line for line in road_stages if not line.startswith("Stage 0 ")]
        require(road_without_stage0 == technical_stages, "roadmap and technical-spec stage sequences diverge")

    c16 = _json("evidence/stage1c/corpus/coverage-bias-report.v1.json")
    require(c16["snapshotSha256"] == EXPECTED_C15_SNAPSHOT, "historical C16 no longer points at immutable C15 snapshot")
    require(c16["sufficiency"]["state"] == "insufficient", "historical C16 sufficiency was rewritten")
    require(c16["sufficiency"]["stage1ExitSupported"] is False, "historical C16 unexpectedly supports Stage 1 exit")

    catalog_v2 = _json("evidence/stage1c/corpus/catalog.v2.json")
    snapshot_v2 = _json("evidence/stage1c/corpus/snapshot.expanded.v2.json")
    report_v2 = _json("evidence/stage1c/corpus/coverage-bias-report.v2.json")
    stage1_acceptance = _json("evidence/stage1c/corpus/stage1-exit-acceptance.v1.json")
    execution = _json("evidence/stage2/corpus/execution-evidence.v1.json")
    stage2_acceptance = _json("evidence/stage2/corpus/stage2-exit-acceptance.v1.json")
    handoff = _json("docs/live/ST_SCORE_RESTORE_LIVE_HANDOFF.json")

    require(canonical_sha256(catalog_v2) == EXPECTED_V2_CATALOG, "expanded-v2 catalog canonical digest drifted")
    require(snapshot_v2["catalogSha256"] == EXPECTED_V2_CATALOG, "expanded-v2 snapshot catalog digest drifted")
    require(report_v2["snapshotSha256"] == EXPECTED_V2_SNAPSHOT, "expanded-v2 report snapshot digest drifted")
    require(report_v2["catalogSha256"] == EXPECTED_V2_CATALOG, "expanded-v2 report catalog digest drifted")
    require(canonical_sha256(snapshot_v2) == EXPECTED_V2_SNAPSHOT, "expanded-v2 snapshot canonical digest drifted")
    require(canonical_sha256(report_v2) == EXPECTED_V2_REPORT, "expanded-v2 report canonical digest drifted")

    require(stage1_acceptance.get("decision") == "PASS", "Stage 1 exit acceptance is not PASS")
    require(stage1_acceptance.get("stage2EntryEligible") is True, "Stage 1 acceptance no longer authorizes Stage 2 entry")

    execution_payload = dict(execution)
    execution_digest = execution_payload.pop("evidenceDigest", {}).get("value")
    require(execution_digest == STAGE2_EXECUTION_EVIDENCE, "Stage 2 execution evidence digest drifted")
    require(canonical_sha256(execution_payload) == STAGE2_EXECUTION_EVIDENCE, "Stage 2 execution evidence content drifted")
    require(execution.get("assertions", {}).get("stage2ExitPass") is False, "historical execution evidence was retroactively changed")
    require(execution.get("assertions", {}).get("stage3EntryAuthorized") is False, "historical execution evidence retroactively authorizes Stage 3")
    require(execution.get("assertions", {}).get("heldOutThresholdTuningUsed") is False, "Stage 2 execution evidence lost held-out non-tuning")

    require(stage2_acceptance.get("decision") == "PASS", "Stage 2 final exit acceptance is not PASS")
    require(stage2_acceptance.get("evidenceMainSha") == STAGE2_EVIDENCE_MAIN, "Stage 2 acceptance main binding drifted")
    require(stage2_acceptance.get("stage2ExitPass") is True, "Stage 2 acceptance does not explicitly pass exit")
    require(stage2_acceptance.get("stage3EntryEligible") is True, "Stage 3 is not marked entry eligible")
    require(stage2_acceptance.get("stage3Started") is False, "Stage 3 started inside Stage 2 acceptance slice")
    require(stage2_acceptance.get("blockerCodes") == [], "Stage 2 acceptance contains blockers")
    require(stage2_acceptance.get("evidenceDigests", {}).get("corpusExecutionEvidenceCanonicalSha256") == STAGE2_EXECUTION_EVIDENCE, "Stage 2 acceptance lost execution-evidence binding")

    for name, value in stage2_acceptance.get("claims", {}).items():
        require(value is False, f"Stage 2 acceptance contains unsupported positive claim: {name}")

    require(handoff.get("main_sha") == STAGE2_EVIDENCE_MAIN, "live handoff does not bind latest evidence main")
    require(handoff.get("stage2_exit_state") == "pass_candidate_pending_acceptance_pr_merge", "live handoff Stage 2 exit state drifted")
    require(handoff.get("stage3_started") is False, "live handoff claims Stage 3 started")
    require("eligible" in str(handoff.get("stage3_entry_state", "")), "live handoff does not record Stage 3 eligibility")

    require(STAGE2_ENTRY_MAIN in docs["README"], "README lost accepted Stage 2 entry main")

    workflow = _read(".github/workflows/repository-validation.yml")
    for validator in (
        "validate_stage2_quality_analysis.py",
        "validate_stage2_custody_execution.py",
        "validate_stage2_corpus_execution_evidence.py",
        "validate_stage2_exit_acceptance.py",
    ):
        require(validator in workflow, f"CI is not wired to {validator}")

    for root_name in ("stage1c", "stage2"):
        evidence_root = ROOT / "evidence" / root_name
        binary_paths = [
            str(path.relative_to(ROOT))
            for path in evidence_root.rglob("*")
            if path.is_file() and path.suffix.lower() in REAL_ARTIFACT_SUFFIXES
        ]
        require(not binary_paths, f"real-artifact-like bytes found under evidence/{root_name}: {binary_paths}")

    combined_docs = "\n".join(docs.values())
    for digest in (
        EXPECTED_C15_SNAPSHOT,
        EXPECTED_C16_REPORT,
        EXPECTED_V2_CATALOG,
        EXPECTED_V2_SNAPSHOT,
        EXPECTED_V2_REPORT,
        STAGE2_EXECUTION_EVIDENCE,
    ):
        require(digest in combined_docs, f"architecture/status docs lost evidence binding {digest}")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print(f"- package/OpenAPI version: {pyproject['project']['version']}")
    print("- Stage 1 final exit: PASS / immutable evidence preserved")
    print("- Stage 2 final exit: PASS acceptance recorded")
    print("- Stage 2 thresholds: uncalibrated / held-out non-tuning")
    print("- Stage 3: entry eligible / not started")
    print("- Stage 2 quality/custody/execution/exit validators: wired")
    print("- evidence/stage1c + evidence/stage2: metadata-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
