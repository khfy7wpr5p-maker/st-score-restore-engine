from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.stage4_purpose_grants import (
    APPROVED_GRANT_CANONICAL_SHA256,
    APPROVED_ITEMS,
    HELD_OUT_ITEM,
    HELD_OUT_SHA256,
    validate_stage4_purpose_grants,
)

ROOT = Path(__file__).resolve().parents[1]
GRANTS = ROOT / "evidence" / "stage4" / "governance" / "purpose-grants.v1.json"
CATALOG = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
CHOPIN_CATALOG = ROOT / "evidence" / "stage1c" / "imslp82860-c17c-noise" / "catalog.v2.json"
CATALOG_DIGEST = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (GRANTS, CATALOG, CHOPIN_CATALOG):
        require(path.exists(), f"required Stage 4 purpose-grant input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    raw = load(GRANTS)
    try:
        grants = validate_stage4_purpose_grants(raw)
    except Exception as exc:
        print(f"Stage 4 purpose-grant validation: FAIL\n- {exc}", file=sys.stderr)
        return 1

    require(canonical_sha256(grants) == APPROVED_GRANT_CANONICAL_SHA256, "Stage 4 purpose-grant digest drifted")

    catalog = load(CATALOG)
    require(canonical_sha256(catalog) == CATALOG_DIGEST, "historical Stage 1 catalog was modified")
    catalog_items = {item.get("datasetItemId"): item for item in catalog.get("items", [])}
    for item_id, sha256 in APPROVED_ITEMS.items():
        item = catalog_items.get(item_id)
        require(item is not None, f"approved Stage 4 development item missing from historical catalog: {item_id}")
        if item is not None:
            require(item.get("split") == "development", f"Stage 4 grant item is not development: {item_id}")
            require(item.get("artifact", {}).get("sha256") == sha256, f"Stage 4 grant artifact identity drifted: {item_id}")
            require(
                item.get("permissions", {}).get("safety_calibration", {}).get("status") == "not_requested",
                f"historical safety_calibration state was rewritten instead of overlaid: {item_id}",
            )

    chopin_catalog = load(CHOPIN_CATALOG)
    chopin = next((item for item in chopin_catalog.get("items", []) if item.get("datasetItemId") == HELD_OUT_ITEM), None)
    require(chopin is not None, "Chopin held-out item missing")
    if chopin is not None:
        require(chopin.get("artifact", {}).get("sha256") == HELD_OUT_SHA256, "Chopin held-out artifact identity drifted")
        require(chopin.get("split") == "held_out", "Chopin is no longer held-out")
        require(
            chopin.get("permissions", {}).get("held_out_evaluation", {}).get("status") == "granted",
            "Chopin held-out evaluation authorization is not granted",
        )
        require(
            chopin.get("permissions", {}).get("safety_calibration", {}).get("status") == "not_requested",
            "Chopin must not receive safety_calibration permission",
        )

    assertions = grants.get("assertions", {})
    require(assertions.get("safetyCalibrationPurposeAuthorized") is True, "Stage 4 purpose authorization claim missing")
    require(assertions.get("realDataCalibrationExecutionAuthorized") is False, "purpose grant prematurely authorizes calibration execution")
    require(assertions.get("referenceLabelBundleAccepted") is False, "purpose grant prematurely accepts reference labels")
    require(assertions.get("trainingAuthorized") is False, "purpose grant unexpectedly authorizes training")
    require(assertions.get("publicationAuthorized") is False, "purpose grant unexpectedly authorizes publication")
    require(assertions.get("heldOutTuningAuthorized") is False, "purpose grant unexpectedly authorizes held-out tuning")

    if failures:
        print("Stage 4 purpose-grant validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 purpose-grant validation: PASS")
    print(f"- grant digest: {APPROVED_GRANT_CANONICAL_SHA256}")
    print("- Beethoven + Barley: safety_calibration purpose granted, development-only")
    print("- Chopin: held_out_evaluation preserved; candidate derivation forbidden")
    print("- real calibration execution: still not authorized pending accepted reference-label evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
