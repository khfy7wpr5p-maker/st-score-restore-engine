from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_reference_label_work_package import (
    DEVELOPMENT_ITEMS,
    HELD_OUT_ITEM,
    WORK_PACKAGE_CANONICAL_SHA256,
    summarize_reference_label_work_package,
    validate_reference_label_work_package,
)
from st_score_restore.stage4_purpose_grants import APPROVED_GRANT_CANONICAL_SHA256, validate_stage4_purpose_grants

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "evidence/stage4/reference-labels/work-package.v1.json"
PURPOSE_GRANTS = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
GUIDE = ROOT / "docs/stage4-reference-label-review-guide.md"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
FORBIDDEN_KEYS = {"modelPrediction", "prediction", "metricScore", "engineLabel", "custodyPath", "sourcePath"}


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (PACKAGE, PURPOSE_GRANTS, GUIDE, WORKFLOW):
        require(path.exists(), f"required reference-label work-package input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    raw = json.loads(PACKAGE.read_text(encoding="utf-8"))
    try:
        package = validate_reference_label_work_package(raw)
        summary = summarize_reference_label_work_package(package)
        grants = validate_stage4_purpose_grants(json.loads(PURPOSE_GRANTS.read_text(encoding="utf-8")))
    except Exception as exc:
        print(f"Stage 4 reference-label work-package validation: FAIL\n- {exc}", file=sys.stderr)
        return 1

    require(summary["packageDigest"]["value"] == WORK_PACKAGE_CANONICAL_SHA256, "work-package digest drifted")
    require(package["purposeGrantDigest"] == APPROVED_GRANT_CANONICAL_SHA256, "work package lost purpose-grant binding")
    require(len(grants.get("grants", [])) == 2, "purpose-grant artifact count drifted")
    require(summary["developmentItemCount"] == 2, "work package must contain exactly two development items")
    require(summary["pageCount"] == 6, "work package must expose exactly six development pages")
    require(summary["reviewSlotCount"] == 42, "work package must expose exactly 42 human-review slots")
    require(summary["humanLabelsPresent"] is False, "work package unexpectedly contains human labels")
    require(summary["referenceBundleAccepted"] is False, "work package prematurely accepts reference evidence")
    require(summary["realDataCalibrationExecutionAuthorized"] is False, "work package prematurely authorizes calibration")
    require(summary["heldOutIncluded"] is False, "held-out data entered development review")

    item_ids = {item["datasetItemId"] for item in package["items"]}
    require(item_ids == set(DEVELOPMENT_ITEMS), "development review item set drifted")
    require(HELD_OUT_ITEM["datasetItemId"] not in item_ids, "Chopin entered development review items")
    require(package["heldOutExclusions"] == [HELD_OUT_ITEM], "held-out exclusion drifted")

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                require(key not in FORBIDDEN_KEYS, f"forbidden automatic/private field found in work package: {key}")
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            lowered = value.lower()
            require("custody:" not in lowered, "custody locator leaked into work package")
            require("/mnt/" not in lowered and "\\" not in value, "filesystem path leaked into work package")
    walk(package)

    guide = GUIDE.read_text(encoding="utf-8")
    for token in (
        "human_expert_review",
        "Model predictions",
        "Chopin is excluded",
        "Completing review slots does **not** automatically accept the bundle",
        "real calibration execution remains NOT AUTHORIZED",
    ):
        require(token in guide, f"review guide lost safety instruction: {token}")

    binaries = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "evidence/stage4/reference-labels").rglob("*")
        if path.is_file() and path.suffix.lower() in BINARY_SUFFIXES
    ]
    require(not binaries, f"artifact/image bytes found in reference-label evidence directory: {binaries}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(
        "python tools/validate_stage4_reference_label_work_package.py" in workflow,
        "Repository validation does not run reference-label work-package validator",
    )

    if failures:
        print("Stage 4 reference-label work-package validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 reference-label work-package validation: PASS")
    print(f"- canonical package digest: {WORK_PACKAGE_CANONICAL_SHA256}")
    print("- development review scope: Beethoven 4 pages + Barley 2 pages")
    print("- empty human-review slots: 42")
    print("- human labels present: false / reference bundle accepted: false")
    print("- Chopin: excluded from development review / held-out evaluation only")
    print("- real calibration execution: not authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
