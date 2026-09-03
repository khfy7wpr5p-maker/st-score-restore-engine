from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from st_score_restore.stage4_development_calibration_runner import (
    BARLEY_ID,
    BEETHOVEN_ID,
    EXPECTED_MEASURED_RECORD_COUNT,
    EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
    METRIC_SPECS,
    PRIVATE_METRIC_SCHEMA_VERSION,
    RUNNER_CONTRACT_VERSION,
    Stage4DevelopmentCalibrationRunnerError,
    build_public_preparation_receipt,
    materialize_development_observations,
    validate_private_metric_batch,
)
from st_score_restore.stage4_execution_authorization import AUTHORIZATION_CANONICAL_SHA256
from st_score_restore.stage4_reference_label_completion import BUNDLE_CANONICAL_SHA256
from st_score_restore.stage4_reference_label_work_package import DEVELOPMENT_ITEMS

ROOT = Path(__file__).resolve().parents[1]
AUTH_PATH = ROOT / "evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json"
PURPOSE_PATH = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
ACCEPTANCE_PATH = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
COMPLETION_PATH = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
STAGE3_EXECUTION_PATH = ROOT / "evidence/stage3/corpus/execution-evidence.v1.json"
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"
MODULE_PATH = ROOT / "src/st_score_restore/stage4_development_calibration_runner.py"
STATUS_PATH = ROOT / "docs/stage-4-current-status.md"
APPLICABILITY_DOC_PATH = ROOT / "docs/stage4-metric-applicability-contract.md"

PLACEHOLDER_VALUES = {
    "skew": 0.1,
    "blur": 150.0,
    "glare": 0.01,
    "shadow": 0.02,
    "uneven_lighting": 0.03,
    "noise": 0.01,
    "compression": 0.02,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def applicability(item_id: str, finding: str) -> tuple[str, float | None, str | None]:
    if item_id == BARLEY_ID:
        return "not_applicable", None, "source_vector_only_preserved"
    if item_id == BEETHOVEN_ID and finding == "compression":
        return "not_applicable", None, "metric_not_applicable_to_png_derivative"
    return "measured", PLACEHOLDER_VALUES[finding], None


def synthetic_private_batch(completion: dict) -> dict:
    records = []
    for reference in completion["bundle"]["records"]:
        finding = reference["findingType"]
        item_id = reference["datasetItemId"]
        item = DEVELOPMENT_ITEMS[item_id]
        spec = METRIC_SPECS[finding]
        status, raw_value, reason = applicability(item_id, finding)
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
                "provenanceReference": "custody:synthetic-private-metric-validator",
            }
        )
    return {
        "schemaVersion": PRIVATE_METRIC_SCHEMA_VERSION,
        "contractVersion": RUNNER_CONTRACT_VERSION,
        "batchId": "synthetic.contract-validator.private-metrics.v2",
        "environment": "stage1_offline",
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "referenceBundleDigest": {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "records": records,
    }


def rejected_code(callable_obj) -> str | None:
    try:
        callable_obj()
    except Stage4DevelopmentCalibrationRunnerError as exc:
        return exc.code
    return None


def _receipt_by_item(stage3: dict, item_id: str) -> dict | None:
    return next((item for item in stage3.get("receipts", []) if item.get("datasetItemId") == item_id), None)


def main() -> int:
    failures: list[str] = []
    for path in (
        AUTH_PATH, PURPOSE_PATH, ACCEPTANCE_PATH, COMPLETION_PATH, STAGE3_EXECUTION_PATH,
        WORKFLOW_PATH, MODULE_PATH, STATUS_PATH, APPLICABILITY_DOC_PATH,
    ):
        require(path.exists(), f"required Stage 4 runner input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    auth = read_json(AUTH_PATH)
    purpose = read_json(PURPOSE_PATH)
    acceptance = read_json(ACCEPTANCE_PATH)
    completion = read_json(COMPLETION_PATH)
    stage3 = read_json(STAGE3_EXECUTION_PATH)
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    module = MODULE_PATH.read_text(encoding="utf-8")
    status = STATUS_PATH.read_text(encoding="utf-8")
    applicability_doc = APPLICABILITY_DOC_PATH.read_text(encoding="utf-8")

    beethoven_stage3 = _receipt_by_item(stage3, BEETHOVEN_ID)
    barley_stage3 = _receipt_by_item(stage3, BARLEY_ID)
    require(beethoven_stage3 is not None, "Stage 3 Beethoven execution receipt missing", failures)
    require(barley_stage3 is not None, "Stage 3 Barley execution receipt missing", failures)
    if beethoven_stage3:
        require(
            beethoven_stage3["pageSummary"]["classificationCounts"] == {"raster_only": 4}
            and beethoven_stage3["pageSummary"]["renderedPageCount"] == 4,
            "Stage 3 Beethoven raster applicability truth drifted",
            failures,
        )
    if barley_stage3:
        require(
            barley_stage3["pageSummary"]["classificationCounts"] == {"vector_only": 2}
            and barley_stage3["pageSummary"]["renderedPageCount"] == 0
            and barley_stage3["pageSummary"]["vectorPagesRasterized"] is False,
            "Stage 3 Barley vector-preservation truth drifted",
            failures,
        )

    batch = synthetic_private_batch(completion)
    validated = validate_private_metric_batch(batch, auth, purpose, acceptance, completion)
    require(len(validated["records"]) == 42, "valid private metric contract did not account for 42 records", failures)
    require(
        sum(record["measurementStatus"] == "measured" for record in validated["records"]) == EXPECTED_MEASURED_RECORD_COUNT,
        "valid private metric contract measured-count drifted",
        failures,
    )
    require(
        sum(record["measurementStatus"] == "not_applicable" for record in validated["records"]) == EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
        "valid private metric contract not-applicable-count drifted",
        failures,
    )

    observations = materialize_development_observations(batch, auth, purpose, acceptance, completion)
    require(len(observations) == EXPECTED_MEASURED_RECORD_COUNT, "private runner did not materialize exactly 24 measured observations", failures)
    require({item.dataset_item_id for item in observations} == {BEETHOVEN_ID}, "vector-only Barley entered measured observations", failures)
    require("compression" not in {item.finding_type for item in observations}, "PNG derivative compression entered measured observations", failures)
    require({item.split for item in observations} == {"development"}, "held-out split entered private development runner", failures)
    require({item.data_class for item in observations} == {"real"}, "private runner data class drifted", failures)
    require({item.purpose for item in observations} == {"safety_calibration"}, "private runner purpose drifted", failures)

    receipt = build_public_preparation_receipt(batch, auth, purpose, acceptance, completion)
    rendered = json.dumps(receipt, sort_keys=True)
    require(receipt.get("status") == "development_calibration_input_prepared_with_abstentions", "public preparation receipt status drifted", failures)
    require(receipt.get("recordCount") == 42, "public preparation receipt record count drifted", failures)
    require(receipt.get("measuredRecordCount") == 24, "public preparation measured count drifted", failures)
    require(receipt.get("notApplicableRecordCount") == 18, "public preparation not-applicable count drifted", failures)
    require(receipt.get("measuredSourceFamilyCount") == 1, "measured source-family count drifted", failures)
    require(receipt.get("findingCounts", {}).get("compression") == {"total": 6, "measured": 0, "notApplicable": 6}, "compression applicability count drifted", failures)
    for finding in ("skew", "blur", "glare", "shadow", "uneven_lighting", "noise"):
        require(receipt.get("findingCounts", {}).get(finding) == {"total": 6, "measured": 4, "notApplicable": 2}, f"{finding} applicability count drifted", failures)
    for forbidden in ("rawValue", "observationId", "dataset.item.", "source.family.", "custody:"):
        require(forbidden not in rendered, f"public preparation receipt leaked private token: {forbidden}", failures)
    assertions = receipt.get("assertions") or {}
    require(assertions.get("candidateDerivationInputReady") is True, "validated measured input did not become derivation-ready", failures)
    require(assertions.get("notApplicableMeasurementsPresent") is True, "receipt lost not-applicable measurement truth", failures)
    require(assertions.get("fullMetricCoverage") is False, "receipt falsely claims full metric coverage", failures)
    require(assertions.get("crossFamilyMeasuredSupportSatisfied") is False, "receipt falsely claims cross-family measured support", failures)
    for key in (
        "privateMetricRowsPublic", "rawMetricValuesPublic", "artifactBytesPublic", "derivativeBytesPublic",
        "realDataCalibrationExecuted", "thresholdsCalibrated", "resourceLimitsCalibrated", "heldOutIncluded",
        "heldOutThresholdTuningUsed", "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized", "modelTrainingAuthorized", "publicationAuthorized",
        "stage4ExitPass", "stage5EntryAuthorized",
    ):
        require(assertions.get(key) is False, f"unsafe runner receipt assertion became true: {key}", failures)

    tampered = deepcopy(batch)
    tampered["records"][0]["artifactSha256"] = "0" * 64
    require(
        rejected_code(lambda: validate_private_metric_batch(tampered, auth, purpose, acceptance, completion)) == "artifact_identity_mismatch",
        "artifact identity tampering was not rejected",
        failures,
    )
    tampered = deepcopy(batch)
    tampered["records"][0]["referenceLabel"] = "clear"
    require(
        rejected_code(lambda: validate_private_metric_batch(tampered, auth, purpose, acceptance, completion)) == "reference_truth_in_private_metrics",
        "reference truth was accepted inside private metric rows",
        failures,
    )
    tampered = deepcopy(batch)
    barley = next(record for record in tampered["records"] if record["datasetItemId"] == BARLEY_ID)
    barley["measurementStatus"] = "measured"
    barley["rawValue"] = 0.0
    barley["notApplicableReason"] = None
    require(
        rejected_code(lambda: validate_private_metric_batch(tampered, auth, purpose, acceptance, completion)) == "measurement_applicability_mismatch",
        "vector-only Barley was accepted as a measured raster metric",
        failures,
    )
    tampered = deepcopy(batch)
    beethoven_compression = next(
        record for record in tampered["records"]
        if record["datasetItemId"] == BEETHOVEN_ID and record["findingType"] == "compression"
    )
    beethoven_compression["rawValue"] = 0.0
    require(
        rejected_code(lambda: validate_private_metric_batch(tampered, auth, purpose, acceptance, completion)) == "invented_not_applicable_value",
        "PNG derivative compression accepted an invented numeric value",
        failures,
    )

    require("24 measured" in applicability_doc and "18 not-applicable" in applicability_doc, "applicability documentation lost exact coverage", failures)
    require("not_applicable" in status or "not-applicable" in status, "Stage 4 status does not record applicability limitation", failures)
    require("realDataCalibrationExecuted=false" in status, "Stage 4 status prematurely claims real calibration execution", failures)
    require("crossFamilyMeasuredSupportSatisfied" in module, "runner module lost cross-family support truth", failures)
    require("notApplicableMeasurementsPresent" in module, "runner module lost not-applicable truth", failures)
    require(
        "python tools/validate_stage4_development_calibration_runner.py" in workflow,
        "repository validation does not run Stage 4 development calibration runner validator",
        failures,
    )

    stage4_root = ROOT / "evidence/stage4"
    leaked_raw_value_files: list[str] = []
    for path in stage4_root.rglob("*.json"):
        if '"rawValue"' in path.read_text(encoding="utf-8"):
            leaked_raw_value_files.append(str(path.relative_to(ROOT)))
    require(not leaked_raw_value_files, f"ordinary Git Stage 4 evidence contains raw private metric values: {leaked_raw_value_files}", failures)

    if failures:
        print("Stage 4 development calibration runner validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 development calibration runner validation: PASS")
    print(f"- contract version: {RUNNER_CONTRACT_VERSION}")
    print("- exact development observation identities accounted for: 42")
    print("- measured observations: 24")
    print("- not-applicable observations: 18")
    print("- vector-only Barley metrics: fail-closed not_applicable")
    print("- Beethoven PNG compression metric: fail-closed not_applicable")
    print("- public receipt: digests + aggregate applicability counts only")
    print("- raw private metric values in ordinary Git: 0")
    print("- cross-family measured support: insufficient; candidate methodology must abstain")
    print("- held-out evaluation/tuning, production changes, Stage 4 PASS and Stage 5: not authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
