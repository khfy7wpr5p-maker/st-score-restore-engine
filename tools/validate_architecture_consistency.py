from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_C15_SNAPSHOT = "b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476"
EXPECTED_C17C_ARTIFACT = "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3"
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
    }

    stale_phrase = "C17B/C17C/C17D"
    for name, text in docs.items():
        require(stale_phrase not in text, f"{name} still contains stale C17B/C17C/C17D continuation wording")

    for name in ("README", "roadmap", "technical", "current", "exit"):
        text = docs[name]
        require("C17C" in text and "PR #72" in text, f"{name} does not record merged C17C / PR #72")

    for name in ("roadmap", "technical", "current", "exit"):
        lowered = docs[name].lower()
        require("stage 2" in lowered and "blocked" in lowered, f"{name} does not preserve the Stage 2 blocked boundary")

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
    require("pure tab-only layout is **not required**" in taxonomy_lower, "Stage 1 notation taxonomy does not explicitly allow staff-above/TAB-below guitar scores")
    require("may legitimately carry both `guitar_tab` and `combined_staff_tab`" in taxonomy, "Stage 1 notation taxonomy does not allow independently supported overlapping TAB/layout labels")
    require("do not define `guitar_tab` as \"tab-only\"" in taxonomy_lower, "Stage 1 notation taxonomy permits the obsolete TAB-only interpretation")

    c17a = _json("evidence/stage1c/wikimedia-guitar-technical-exercise-no1/catalog.v1.json")["items"][0]
    notation_kinds = c17a["input"]["notationKinds"]
    require(notation_kinds == ["combined_staff_tab"], f"C17A notation taxonomy drifted: {notation_kinds}")
    require("guitar_tab" not in notation_kinds, "C17A accepted admission scope was retroactively widened")
    require(c17a["assertions"]["originalBytesInGit"] is False, "C17A claims real artifact bytes are in Git")

    c17c = _json("evidence/stage1c/imslp82860-c17c-noise/catalog.v2.json")["items"][0]
    require(c17c["datasetItemId"] == "dataset.item.imslp82860-chopin-op69.v2", "C17C metadata-v2 item id drifted")
    require(c17c["artifact"]["sha256"] == EXPECTED_C17C_ARTIFACT, "C17C exact artifact digest drifted")
    require(c17c["input"]["degradations"] == ["noise"], f"C17C degradation classification drifted: {c17c['input']['degradations']}")
    require(c17c["split"] == "held_out", "C17C held-out split drifted")
    require(c17c["permissions"]["held_out_evaluation"]["status"] == "granted", "C17C held-out evaluation permission is not granted")
    require(c17c["permissions"]["model_training"]["status"] != "granted", "C17C unexpectedly grants model training")

    c16 = _json("evidence/stage1c/corpus/coverage-bias-report.v1.json")
    require(c16["snapshotSha256"] == EXPECTED_C15_SNAPSHOT, "historical C16 no longer points at the immutable C15 snapshot")
    require(c16["sufficiency"]["state"] == "insufficient", "historical C16 sufficiency was rewritten")
    require(c16["sufficiency"]["stage1ExitSupported"] is False, "historical C16 unexpectedly supports Stage 1 exit")
    require(c16["sufficiency"]["stage2EntrySupported"] is False, "historical C16 unexpectedly supports Stage 2 entry")
    require(c16["counts"]["realItemCount"] == 2 and c16["counts"]["pageCounts"]["total"] == 12, "historical C16 counts drifted")

    current = docs["current"]
    exit_doc = docs["exit"]
    require("must never be double-counted" in current, "current status does not guard C17C v1/v2 de-duplication")
    require("must not count the two metadata versions as separate artifacts" in exit_doc or "must never be treated as independent" in exit_doc, "exit evidence does not guard C17C v1/v2 de-duplication")

    evidence_root = ROOT / "evidence" / "stage1c"
    binary_paths = [str(path.relative_to(ROOT)) for path in evidence_root.rglob("*") if path.is_file() and path.suffix.lower() in REAL_ARTIFACT_SUFFIXES]
    require(not binary_paths, f"real-artifact-like bytes found under evidence/stage1c: {binary_paths}")

    workflow = _read(".github/workflows/repository-validation.yml")
    require("python tools/validate_architecture_consistency.py" in workflow, "architecture consistency validator is not wired into CI")
    require("Require Stage 1C C17C exact-byte degradation reclassification" in workflow, "CI no longer requires C17C admission validation")
    require("Require Stage 1C C17 guitar TAB combined admission" in workflow, "CI no longer requires C17A combined staff/TAB admission validation")

    if failures:
        print("Architecture consistency validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Architecture consistency validation: PASS")
    print(f"- package/OpenAPI version: {package_version}")
    print("- roadmap/technical stage sequence: aligned")
    print("- Stage 1 TAB taxonomy: standalone is an artifact role; TAB-only layout is not required")
    print("- C17A accepted scope: combined_staff_tab only, unchanged")
    print("- C17C exact-byte metadata-v2: noise / held_out / no training")
    print("- historical C15/C16 freeze: unchanged and insufficient")
    print("- Stage 2 boundary: blocked")
    print("- evidence/stage1c: metadata-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
