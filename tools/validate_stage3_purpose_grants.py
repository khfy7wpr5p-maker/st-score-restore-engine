from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage3_purpose_grants import (
    AUTHORIZED_DATASET_ITEMS,
    CATALOG_CANONICAL_SHA256,
    PURPOSE,
    apply_stage3_purpose_grants,
    validate_stage3_purpose_grants,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
GRANTS_PATH = ROOT / "evidence" / "stage3" / "purpose-grants" / "pdf-pipeline-evaluation.2026-09-02.v1.json"


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    grants = json.loads(GRANTS_PATH.read_text(encoding="utf-8"))
    before = deepcopy(catalog)

    try:
        normalized = validate_stage3_purpose_grants(catalog, grants, execution_date="2026-09-02")
        overlaid = apply_stage3_purpose_grants(catalog, grants, execution_date="2026-09-02")
    except Exception as exc:
        print("Stage 3 purpose-grant validation: FAIL", file=sys.stderr)
        print(f"- {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    require(catalog == before, "historical catalog mutated during grant validation")
    require(canonical_sha256(catalog) == CATALOG_CANONICAL_SHA256, "historical expanded-v2 catalog digest drifted")
    require(
        {item["datasetItemId"] for item in normalized["grants"]} == set(AUTHORIZED_DATASET_ITEMS),
        "purpose grant does not contain exactly Beethoven and Barley",
    )
    require(
        normalized["assertions"] == {
            "historicalCatalogsModified": False,
            "trainingAuthorized": False,
            "calibrationAuthorized": False,
            "publicationAuthorized": False,
            "demonstrationAuthorized": False,
            "externalExportAuthorized": False,
        },
        "grant assertions broaden authorization scope",
    )

    before_by_id = {item["datasetItemId"]: item for item in catalog["items"]}
    after_by_id = {item["datasetItemId"]: item for item in overlaid["items"]}
    for item_id, original in before_by_id.items():
        observed = after_by_id[item_id]
        if item_id not in AUTHORIZED_DATASET_ITEMS:
            require(original == observed, f"non-target item changed: {item_id}")
            continue
        require(original["permissions"][PURPOSE]["status"] == "not_requested", f"historical {item_id} permission baseline drifted")
        require(observed["permissions"][PURPOSE]["status"] == "granted", f"overlay did not grant {item_id}")
        restrictions = {item["type"]: item for item in observed["permissions"][PURPOSE]["restrictions"]}
        require(restrictions.get("split_allowlist") == {"type": "split_allowlist", "values": ["development"]}, f"{item_id} split restriction drifted")
        require(restrictions.get("storage_class_allowlist") == {"type": "storage_class_allowlist", "values": ["managed_standard"]}, f"{item_id} storage restriction drifted")
        require(restrictions.get("environment_allowlist") == {"type": "environment_allowlist", "values": ["stage1_offline"]}, f"{item_id} environment restriction drifted")
        require(restrictions.get("external_export") == {"type": "external_export", "allowed": False}, f"{item_id} external export is not explicitly blocked")
        before_other = deepcopy(original["permissions"])
        after_other = deepcopy(observed["permissions"])
        before_other.pop(PURPOSE)
        after_other.pop(PURPOSE)
        require(before_other == after_other, f"{item_id} unrelated purpose permissions changed")

    if failures:
        print("Stage 3 purpose-grant validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 3 purpose-grant validation: PASS")
    print(f"- accepted historical catalog: {CATALOG_CANONICAL_SHA256}")
    print("- explicit purpose: pdf_pipeline_evaluation")
    print("- authorized items: Beethoven + Barley only")
    print("- historical catalogs: unchanged")
    print("- external export: blocked")
    print("- training/calibration/publication: not authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
