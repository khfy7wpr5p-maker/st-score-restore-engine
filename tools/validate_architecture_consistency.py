from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_C15_SNAPSHOT = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"
EXPECTED_C16_REPORT = "0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e"
EXPECTED_C17A_ARTIFACT = "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb"
EXPECTED_C17B_ARTIFACT = "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e"
EXPECTED_C17C_ARTIFACT = "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3"
EXPECTED_C17D_ARTIFACT = "abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5"
EXPECTED_V2_CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
EXPECTED_V2_SNAPSHOT = "c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7"
EXPECTED_V2_REPORT = "45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834"
STAGE2_ENTRY_MAIN = "936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6"
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
    require(
        pyproject["project"]["version"] == openapi["info"]["version"],
        "package/OpenAPI version mismatch",
    )

    docs = {
        "README": _read("README.md"),
        "roadmap": _read("docs/roadmap.md"),
        "technical": _read("docs/technical-specification.md"),
        "stage1_current": _read("docs/stage-1c-current-status.md"),
        "stage1_exit": _read("docs/stage-1-exit-evidence.md"),
        "dataset_card": _read("docs/stage-1-dataset-card.md"),
        "coverage_register": _read("docs/stage-1-coverage-and-bias-register.md"),
        "stage2_current": _read("docs/stage-2-current-status.md"),
        "audit": _read("docs/architecture-consistency-audit.md"),
    }

    for name in ("README", "roadmap", "technical", "stage2_current", "audit"):
        lowered = docs[name].lower()
        require("stage 2" in lowered and "active" in lowered, f"{name} does not record Stage 2 ACTIVE")
        require("stage 3" in lowered and "blocked" in lowered, f"{name} does not preserve Stage 3 BLOCKED boundary")

    for name in ("stage1_current", "stage1_exit", "dataset_card", "coverage_register"):
        lowered = docs[name].lower()
        require("pass" in lowered or "complete" in lowered, f"{name} does not record accepted Stage 1 exit")
        require("stage 2" in lowered, f"{name} does not record Stage 2 transition/use boundary")

    stale_current_phrases = (
        "Stage 1 final exit: not yet accepted",
        "Stage 2 — complete quality analysis: blocked until explicit Stage 1 final PASS",
        "Stage 1 final exit: BLOCKED",
        "Stage 2 entry: BLOCKED",
        "Stage 1 exit is a separate acceptance decision after PR #81 merge",
        "Stage 2 / OpenCV Complete Quality Analysis remains blocked until that final Stage 1 exit acceptance is PASS",
    )
    for name, text in docs.items():
        for phrase in stale_current_phrases:
            require(phrase not in text, f"{name} contains stale pre-Stage-2 wording: {phrase}")

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
    acceptance = _json("evidence/stage1c/corpus/stage1-exit-acceptance.v1.json")

    require(snapshot_v2["catalogSha256"] == EXPECTED_V2_CATALOG, "expanded-v2 catalog digest drifted")
    require(report_v2["snapshotSha256"] == EXPECTED_V2_SNAPSHOT, "expanded-v2 snapshot digest drifted")
    require(report_v2["catalogSha256"] == EXPECTED_V2_CATALOG, "expanded-v2 report catalog digest drifted")
    require(report_v2["sufficiency"]["state"] == "review_required", "expanded-v2 automatic report must remain review_required")
    require(report_v2["sufficiency"]["stage1ExitSupported"] is False, "expanded-v2 automatic report must not auto-authorize Stage 1 exit")
    require(report_v2["sufficiency"]["stage2EntrySupported"] is False, "expanded-v2 automatic report must not auto-authorize Stage 2")
    require(report_v2["gapCodes"] == [], "expanded-v2 gap codes reappeared")

    ids = {item["datasetItemId"] for item in catalog_v2["items"]}
    require("dataset.item.imslp82860-chopin-op69.v1" not in ids, "expanded-v2 double-counts Chopin v1")
    require("dataset.item.imslp82860-chopin-op69.v2" in ids, "expanded-v2 does not select Chopin v2")
    artifact_digests = [item["artifact"]["sha256"] for item in catalog_v2["items"]]
    require(len(artifact_digests) == len(set(artifact_digests)), "expanded-v2 duplicates exact artifact SHA-256")

    require(acceptance["decision"] == "PASS", "Stage 1 exit acceptance is not PASS")
    require(acceptance["stage2EntryEligible"] is True, "Stage 1 acceptance does not authorize Stage 2 entry")
    require(acceptance["blockerCodes"] == [], "Stage 1 acceptance contains blocker codes")
    require(acceptance["claims"]["trainingAuthorized"] is False, "Stage 1 acceptance unexpectedly authorizes training")
    require(acceptance["claims"]["calibrationAuthorized"] is False, "Stage 1 acceptance unexpectedly authorizes calibration")

    combined_docs = "\n".join(docs.values())
    for digest in (
        EXPECTED_C17A_ARTIFACT,
        EXPECTED_C17B_ARTIFACT,
        EXPECTED_C17C_ARTIFACT,
        EXPECTED_C17D_ARTIFACT,
        EXPECTED_V2_CATALOG,
        EXPECTED_V2_SNAPSHOT,
        EXPECTED_V2_REPORT,
        EXPECTED_C15_SNAPSHOT,
        EXPECTED_C16_REPORT,
    ):
        require(digest in combined_docs, f"architecture/status docs lost evidence binding {digest}")

    require(STAGE2_ENTRY_MAIN in docs["README"], "README does not bind accepted Stage 2 entry main")
    require(STAGE2_ENTRY_MAIN in docs["stage2_current"], "Stage 2 status does not bind accepted entry main")

    quality_source = _read("src/st_score_restore/quality_analysis.py")
    stage2_validator = _read("tools/validate_stage2_quality_analysis.py")
    workflow = _read(".github/workflows/repository-validation.yml")
    require("analyze_quality_bytes" in quality_source, "Stage 2 quality analyzer entry point missing")
    require("heldOutThresholdTuningUsed" in quality_source, "Stage 2 report does not declare held-out tuning state")
    require("CALIBRATION_STATE" in quality_source, "Stage 2 report does not declare calibration state")
    require("validate_stage2_quality_analysis.py" in workflow, "Stage 2 validator is not wired into CI")
    require("from st_score_restore.quality_analysis" in stage2_validator, "Stage 2 validator does not bind analyzer module")

    require("python tools/build_stage1_expanded_snapshot.py --check" in workflow, "CI no longer checks committed expanded-v2 evidence")
    require("python tools/validate_stage1_exit_acceptance.py" in workflow, "CI no longer validates Stage 1 exit acceptance")

    evidence_root = ROOT / "evidence" / "stage1c"
    binary_paths = [
        str(path.relative_to(ROOT))
        for path in evidence_root.rglob("*")
        if path.is_file() and path.suffix.lower() in REAL_ARTIFACT_SUFFIXES
    ]
    require(not binary_paths, f"real-artifact-like bytes found under evidence/stage1c: {binary_paths}")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print(f"- package/OpenAPI version: {pyproject['project']['version']}")
    print("- Stage 1 final exit: PASS / immutable evidence preserved")
    print("- Stage 2 boundary: ACTIVE / uncalibrated / held-out non-tuning")
    print("- Stage 3 boundary: BLOCKED pending Stage 2 exit PASS")
    print("- Stage 2 analyzer/validator/CI: wired")
    print("- evidence/stage1c: metadata-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
