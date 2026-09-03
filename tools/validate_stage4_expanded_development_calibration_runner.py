from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage4_development_calibration_runner import METRIC_SPECS
from st_score_restore.stage4_reference_label_completion import BUNDLE_CANONICAL_SHA256 as BB_BUNDLE_SHA256
from st_score_restore.stage4_wikimedia_expanded_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    EXPECTED_ITEMS,
)
from st_score_restore.stage4_wikimedia_reference_acceptance import WIKIMEDIA_BUNDLE_CANONICAL_SHA256
from st_score_restore.stage4_expanded_development_calibration_runner import (
    BARLEY_ID,
    BEETHOVEN_ID,
    EXPECTED_MEASURED_RECORD_COUNT,
    EXPECTED_MEASURED_SOURCE_FAMILY_COUNT,
    EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
    EXPECTED_RECORD_COUNT,
    PRIVATE_METRIC_SCHEMA_VERSION,
    RUNNER_CONTRACT_VERSION,
    Stage4ExpandedDevelopmentCalibrationRunnerError,
    WIKIMEDIA_ID,
    build_expanded_public_preparation_receipt,
    materialize_expanded_development_observations,
    validate_expanded_private_metric_batch,
)

AUTH = ROOT / "evidence/stage4/governance/expanded-development-calibration-execution-authorization.v1.json"
BB_PURPOSE = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
BB_ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
BB_COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
WIKI_PURPOSE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/purpose-grant.v1.json"
WIKI_ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"
WIKI_COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
WIKI_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"
MODULE = ROOT / "src/st_score_restore/stage4_expanded_development_calibration_runner.py"

PLACEHOLDER_VALUES = {
    "skew": 0.1,
    "blur": 150.0,
    "glare": 0.01,
    "shadow": 0.02,
    "uneven_lighting": 0.03,
    "noise": 0.01,
    "compression": 0.02,
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def applicability(item_id: str, finding: str) -> tuple[str, float | None, str | None]:
    if item_id == BARLEY_ID:
        return "not_applicable", None, "source_vector_only_preserved"
    if item_id == BEETHOVEN_ID and finding == "compression":
        return "not_applicable", None, "metric_not_applicable_to_png_derivative"
    return "measured", PLACEHOLDER_VALUES[finding], None


def synthetic_batch(bb_completion: dict, wiki_completion: dict) -> dict:
    records = []
    references = [*bb_completion["bundle"]["records"], *wiki_completion["bundle"]["records"]]
    for reference in references:
        item_id = reference["datasetItemId"]
        finding = reference["findingType"]
        status, raw_value, reason = applicability(item_id, finding)
        item = EXPECTED_ITEMS[item_id]
        spec = METRIC_SPECS[finding]
        records.append(
            {
                "observationId": reference["observationId"],
                "datasetItemId": item_id,
                "artifactSha256": item["artifactSha256"],
                "sourceFamilyId": reference["sourceFamilyId"],
                "findingType": finding,
                "metricName": spec["metricName"],
                "direction": spec["direction"],
                "measurementStatus": status,
                "rawValue": raw_value,
                "notApplicableReason": reason,
                "split": "development",
                "dataClass": "real",
                "purpose": "safety_calibration",
                "provenanceReference": "custody:synthetic-expanded-runner-validator",
            }
        )
    return {
        "schemaVersion": PRIVATE_METRIC_SCHEMA_VERSION,
        "contractVersion": RUNNER_CONTRACT_VERSION,
        "batchId": "synthetic.contract-only.expanded-private-metrics.validator.v1",
        "environment": "stage1_offline",
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "referenceBundleDigests": {
            "beethovenBarley": {"algorithm": "sha256", "value": BB_BUNDLE_SHA256},
            "wikimedia": {"algorithm": "sha256", "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256},
        },
        "records": records,
    }


def main() -> int:
    required = (AUTH, BB_PURPOSE, BB_ACCEPTANCE, BB_COMPLETION, WIKI_PURPOSE, WIKI_ACCEPTANCE, WIKI_COMPLETION, WIKI_PACKAGE, WORKFLOW, MODULE)
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        print("Stage 4 expanded development calibration runner validation: FAIL", file=sys.stderr)
        for path in missing:
            print(f"- missing required input: {path}", file=sys.stderr)
        return 1

    auth = load(AUTH)
    bb_purpose = load(BB_PURPOSE)
    bb_acceptance = load(BB_ACCEPTANCE)
    bb_completion = load(BB_COMPLETION)
    wiki_purpose = load(WIKI_PURPOSE)
    wiki_acceptance = load(WIKI_ACCEPTANCE)
    wiki_completion = load(WIKI_COMPLETION)
    wiki_package = load(WIKI_PACKAGE)
    batch = synthetic_batch(bb_completion, wiki_completion)

    try:
        validated = validate_expanded_private_metric_batch(
            batch, auth, bb_purpose, bb_acceptance, bb_completion,
            wiki_purpose, wiki_acceptance, wiki_completion, wiki_package,
        )
        observations = materialize_expanded_development_observations(
            batch, auth, bb_purpose, bb_acceptance, bb_completion,
            wiki_purpose, wiki_acceptance, wiki_completion, wiki_package,
        )
        receipt = build_expanded_public_preparation_receipt(
            batch, auth, bb_purpose, bb_acceptance, bb_completion,
            wiki_purpose, wiki_acceptance, wiki_completion, wiki_package,
        )
    except Exception as error:
        print("Stage 4 expanded development calibration runner validation: FAIL", file=sys.stderr)
        print(f"- {error}", file=sys.stderr)
        return 1

    failures: list[str] = []
    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(len(validated["records"]) == EXPECTED_RECORD_COUNT == 49, "expanded record count drifted")
    require(sum(row["measurementStatus"] == "measured" for row in validated["records"]) == EXPECTED_MEASURED_RECORD_COUNT == 31, "expanded measured count drifted")
    require(sum(row["measurementStatus"] == "not_applicable" for row in validated["records"]) == EXPECTED_NOT_APPLICABLE_RECORD_COUNT == 18, "expanded not-applicable count drifted")
    wiki_rows = [row for row in validated["records"] if row["datasetItemId"] == WIKIMEDIA_ID]
    require(len(wiki_rows) == 7 and all(row["measurementStatus"] == "measured" for row in wiki_rows), "Wikimedia seven-metric measured applicability drifted")
    require(len(observations) == 31, "expanded materialized observation count drifted")
    require({item.dataset_item_id for item in observations} == {BEETHOVEN_ID, WIKIMEDIA_ID}, "expanded measured observation source set drifted")

    require(receipt.get("recordCount") == 49, "public receipt record count drifted")
    require(receipt.get("measuredRecordCount") == 31, "public receipt measured count drifted")
    require(receipt.get("notApplicableRecordCount") == 18, "public receipt not-applicable count drifted")
    require(receipt.get("measuredSourceFamilyCount") == EXPECTED_MEASURED_SOURCE_FAMILY_COUNT == 2, "public receipt measured source-family count drifted")
    require(receipt.get("assertions", {}).get("crossFamilyMeasuredSupportSatisfied") is True, "expanded cross-family measured support was not satisfied")
    for key in (
        "privateMetricRowsPublic", "rawMetricValuesPublic", "artifactBytesPublic", "derivativeBytesPublic",
        "realDataCalibrationExecuted", "thresholdsCalibrated", "resourceLimitsCalibrated", "heldOutIncluded",
        "heldOutThresholdTuningUsed", "productionThresholdChangeAuthorized", "productionResourceLimitChangeAuthorized",
        "modelTrainingAuthorized", "publicationAuthorized", "stage4ExitPass", "stage5EntryAuthorized",
    ):
        require(receipt.get("assertions", {}).get(key) is False, f"unsafe public receipt assertion became true: {key}")

    rendered = json.dumps(receipt, sort_keys=True)
    for forbidden in ("rawValue", "observationId", "dataset.item.", "source.family.", "custody:"):
        require(forbidden not in rendered, f"public receipt leaked private token: {forbidden}")

    tampered = deepcopy(batch)
    wiki_row = next(row for row in tampered["records"] if row["datasetItemId"] == WIKIMEDIA_ID)
    wiki_row["measurementStatus"] = "not_applicable"
    wiki_row["rawValue"] = None
    wiki_row["notApplicableReason"] = "metric_not_applicable_to_png_derivative"
    try:
        validate_expanded_private_metric_batch(
            tampered, auth, bb_purpose, bb_acceptance, bb_completion,
            wiki_purpose, wiki_acceptance, wiki_completion, wiki_package,
        )
        failures.append("Wikimedia source PNG was incorrectly accepted as not_applicable")
    except Stage4ExpandedDevelopmentCalibrationRunnerError as error:
        require(error.code == "measurement_applicability_mismatch", "Wikimedia applicability tampering returned wrong error code")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("python tools/validate_stage4_expanded_development_calibration_runner.py" in workflow, "repository validation does not run expanded runner validator")

    leaked_raw_value_files: list[str] = []
    for path in (ROOT / "evidence/stage4").rglob("*.json"):
        if '"rawValue"' in path.read_text(encoding="utf-8"):
            leaked_raw_value_files.append(str(path.relative_to(ROOT)))
    require(not leaked_raw_value_files, f"ordinary Git Stage 4 evidence contains raw private metric values: {leaked_raw_value_files}")

    if failures:
        print("Stage 4 expanded development calibration runner validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 expanded development calibration runner validation: PASS")
    print(f"- contract version: {RUNNER_CONTRACT_VERSION}")
    print("- exact development reference identities: 49")
    print("- measured observations: 31 / not_applicable: 18")
    print("- measured source families: Beethoven + Wikimedia = 2")
    print("- Wikimedia source PNG: 7/7 metrics measurable")
    print("- Barley remains vector-preserved not_applicable; Beethoven derivative compression remains not_applicable")
    print("- raw private metric values in ordinary Git: 0")
    print("- real calibration execution: false / held-out: excluded / Stage 4 PASS: false / Stage 5: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
