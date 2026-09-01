from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_C15_SNAPSHOT = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"
EXPECTED_C16_REPORT = "0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e"
EXPECTED_C17B_ARTIFACT = "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e"
EXPECTED_C17C_ARTIFACT = "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3"
EXPECTED_C17D_ARTIFACT = "abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5"
EXPECTED_V2_CATALOG = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
EXPECTED_V2_SNAPSHOT = "c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7"
EXPECTED_V2_REPORT = "45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834"
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
    package_version = pyproject["project"]["version"]
    api_version = openapi["info"]["version"]
    require(package_version == api_version, f"package/OpenAPI version mismatch: {package_version} != {api_version}")

    docs = {
        "README": _read("README.md"),
        "roadmap": _read("docs/roadmap.md"),
        "technical": _read("docs/technical-specification.md"),
        "current": _read("docs/stage-1c-current-status.md"),
        "exit": _read("docs/stage-1-exit-evidence.md"),
        "dataset_card": _read("docs/stage-1-dataset-card.md"),
        "coverage_register": _read("docs/stage-1-coverage-and-bias-register.md"),
        "audit": _read("docs/architecture-consistency-audit.md"),
    }

    stale_phrases = (
        "C17B/C17C/C17D",
        "C17B standalone guitar TAB and C17D admissible real phone-photo path remain fail-closed",
        "The remaining continuation targets are C17B",
        "C17B standalone guitar TAB and C17D an admissible genuine phone-photo path remain qualified but unadmitted",
    )
    for name, text in docs.items():
        for phrase in stale_phrases:
            require(phrase not in text, f"{name} contains stale pre-admission wording: {phrase}")

    for name in ("README", "roadmap", "technical"):
        text = docs[name]
        require("C17C" in text and "PR #72" in text, f"{name} does not record merged C17C / PR #72")

    for name in ("README", "roadmap", "technical", "current", "exit", "audit"):
        text = docs[name]
        require("C17B" in text and EXPECTED_C17B_ARTIFACT in text, f"{name} does not record admitted C17B exact artifact")
        require("C17D" in text and EXPECTED_C17D_ARTIFACT in text, f"{name} does not record admitted C17D exact artifact")

    for name in ("roadmap", "technical", "current", "exit", "dataset_card", "coverage_register", "audit"):
        lowered = docs[name].lower()
        require("stage 2" in lowered and "blocked" in lowered, f"{name} does not preserve Stage 2 blocked boundary")

    road_stages = _binding_stages(docs["roadmap"])
    technical_stages = _binding_stages(docs["technical"])
    require(bool(road_stages), "roadmap binding stage sequence not found")
    require(bool(technical_stages), "technical-spec binding stage sequence not found")
    if road_stages and technical_stages:
        road_without_stage0 = [line for line in road_stages if not line.startswith("Stage 0 ")]
        require(road_without_stage0 == technical_stages, "roadmap and technical-spec stage sequences diverge")

    taxonomy = _read("docs/stage-1-notation-taxonomy.md")
    taxonomy_lower = taxonomy.lower()
    require("standalone" in taxonomy_lower and "artifact role" in taxonomy_lower, "Stage 1 notation taxonomy does not define standalone as an artifact role")
    require("pure tab-only layout is **not required**" in taxonomy_lower, "Stage 1 notation taxonomy does not allow staff-above/TAB-below guitar scores")
    require("may legitimately carry both `guitar_tab` and `combined_staff_tab`" in taxonomy, "Stage 1 notation taxonomy does not allow independently supported overlapping TAB/layout labels")
    require("do not define `guitar_tab` as \"tab-only\"" in taxonomy_lower, "Stage 1 notation taxonomy permits obsolete TAB-only interpretation")

    c17a = _json("evidence/stage1c/wikimedia-guitar-technical-exercise-no1/catalog.v1.json")["items"][0]
    require(c17a["input"]["notationKinds"] == ["combined_staff_tab"], "C17A accepted notation scope drifted")
    require(c17a["assertions"]["originalBytesInGit"] is False, "C17A claims real artifact bytes are in Git")

    c17b = _json("evidence/stage1c/imslp911664-c17b-guitar-tab/catalog.v1.json")["items"][0]
    require(c17b["artifact"]["sha256"] == EXPECTED_C17B_ARTIFACT, "C17B exact artifact digest drifted")
    require(c17b["input"]["notationKinds"] == ["guitar_tab"], "C17B standalone guitar TAB taxonomy drifted")
    require(c17b["permissions"]["quality_evaluation"]["status"] == "granted", "C17B quality_evaluation permission is not granted")

    c17c = _json("evidence/stage1c/imslp82860-c17c-noise/catalog.v2.json")["items"][0]
    require(c17c["datasetItemId"] == "dataset.item.imslp82860-chopin-op69.v2", "C17C metadata-v2 item id drifted")
    require(c17c["artifact"]["sha256"] == EXPECTED_C17C_ARTIFACT, "C17C exact artifact digest drifted")
    require(c17c["input"]["degradations"] == ["noise"], "C17C degradation classification drifted")
    require(c17c["split"] == "held_out", "C17C held-out split drifted")
    require(c17c["permissions"]["model_training"]["status"] != "granted", "C17C unexpectedly grants model training")

    c17d = _json("evidence/stage1c/nearer-my-god-to-thee-c17d/catalog.v1.json")["items"][0]
    require(c17d["artifact"]["sha256"] == EXPECTED_C17D_ARTIFACT, "C17D exact artifact digest drifted")
    require(c17d["input"]["kind"] == "phone_photo", "C17D input kind drifted")
    require(c17d["privacy"]["classification"] == "deidentified", "C17D privacy classification drifted")
    require(c17d["permissions"]["held_out_evaluation"]["status"] == "granted", "C17D held-out permission is not granted")

    c16 = _json("evidence/stage1c/corpus/coverage-bias-report.v1.json")
    require(c16["snapshotSha256"] == EXPECTED_C15_SNAPSHOT, "historical C16 no longer points at immutable C15 snapshot")
    require(c16["sufficiency"]["state"] == "insufficient", "historical C16 sufficiency was rewritten")
    require(c16["sufficiency"]["stage1ExitSupported"] is False, "historical C16 unexpectedly supports Stage 1 exit")
    require(c16["sufficiency"]["stage2EntrySupported"] is False, "historical C16 unexpectedly supports Stage 2 entry")
    require(c16["counts"]["realItemCount"] == 2 and c16["counts"]["pageCounts"]["total"] == 12, "historical C16 counts drifted")
    require(EXPECTED_C16_REPORT in docs["current"] and EXPECTED_C16_REPORT in docs["exit"], "current docs do not retain historical C16 digest")

    catalog_v2 = _json("evidence/stage1c/corpus/catalog.v2.json")
    snapshot_v2 = _json("evidence/stage1c/corpus/snapshot.expanded.v2.json")
    report_v2 = _json("evidence/stage1c/corpus/coverage-bias-report.v2.json")
    ids = {item["datasetItemId"] for item in catalog_v2["items"]}
    expected_ids = {
        "dataset.item.imslp799143-beethoven-op48-no3.v1",
        "dataset.item.wikimedia-guitar-technical-exercise-no1.v1",
        "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1",
        "dataset.item.imslp82860-chopin-op69.v2",
        "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1",
    }
    require(ids == expected_ids, f"expanded-v2 membership drifted: {sorted(ids)}")
    require("dataset.item.imslp82860-chopin-op69.v1" not in ids, "expanded-v2 double-counts Chopin v1")
    artifact_digests = [item["artifact"]["sha256"] for item in catalog_v2["items"]]
    require(len(artifact_digests) == len(set(artifact_digests)), "expanded-v2 duplicates an exact artifact SHA-256")

    split_counts = report_v2["counts"]["splitItemCounts"]
    family_counts = report_v2["counts"]["sourceFamilyCounts"]
    require(split_counts == {"development": 3, "held_out": 2}, f"expanded-v2 split counts drifted: {split_counts}")
    require(family_counts == {"development": 3, "held_out": 2, "total": 5}, f"expanded-v2 source-family counts drifted: {family_counts}")
    require(report_v2["counts"]["realItemCount"] == 5 and report_v2["counts"]["syntheticItemCount"] == 0, "expanded-v2 real/synthetic counts drifted")
    require(report_v2["gapCodes"] == [], "expanded-v2 coverage gaps reappeared")
    require(report_v2["sufficiency"]["state"] == "review_required", "expanded-v2 sufficiency must remain review_required")
    require(report_v2["sufficiency"]["stage1ExitSupported"] is False, "expanded-v2 must not auto-authorize Stage 1 exit")
    require(report_v2["sufficiency"]["stage2EntrySupported"] is False, "expanded-v2 must not auto-authorize Stage 2")
    require(snapshot_v2["catalogSha256"] == EXPECTED_V2_CATALOG, "expanded-v2 snapshot catalog digest drifted")
    require(report_v2["snapshotSha256"] == EXPECTED_V2_SNAPSHOT, "expanded-v2 report snapshot digest drifted")
    require(report_v2["catalogSha256"] == EXPECTED_V2_CATALOG, "expanded-v2 report catalog digest drifted")
    require(EXPECTED_V2_REPORT in docs["technical"] or "coverage report SHA-256" in docs["technical"], "technical spec does not bind expanded-v2 report evidence")

    current = docs["current"]
    require("must never be double-counted" in current, "current status does not guard C17C v1/v2 de-duplication")
    require("stage1ExitSupported = false" in current, "current status does not preserve expanded-v2 Stage 1 fail-closed state")

    evidence_root = ROOT / "evidence" / "stage1c"
    binary_paths = [str(path.relative_to(ROOT)) for path in evidence_root.rglob("*") if path.is_file() and path.suffix.lower() in REAL_ARTIFACT_SUFFIXES]
    require(not binary_paths, f"real-artifact-like bytes found under evidence/stage1c: {binary_paths}")

    workflow = _read(".github/workflows/repository-validation.yml")
    require("python tools/validate_architecture_consistency.py" in workflow, "architecture consistency validator is not wired into CI")
    require("python tools/build_stage1_expanded_snapshot.py --check" in workflow, "CI does not require committed expanded-v2 evidence")
    require("Generate Stage 1C expanded-v2 evidence candidate" not in workflow, "CI still generates candidate-only v2 evidence")
    require("actions/upload-artifact@v4" not in workflow, "CI still uploads candidate-only expanded-v2 evidence")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print(f"- package/OpenAPI version: {package_version}")
    print("- roadmap/technical stage sequence: aligned")
    print("- C17A/C17B/C17C/C17D admission truth: aligned")
    print("- historical C15/C16 evidence: preserved")
    print("- expanded-v2 evidence: committed / deterministic / fail-closed")
    print("- Stage 2 boundary: blocked")
    print("- evidence/stage1c: metadata-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
