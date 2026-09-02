from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

from st_score_restore.stage4_development_calibration_runner import (
    METRIC_SPECS,
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
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"
MODULE_PATH = ROOT / "src/st_score_restore/stage4_development_calibration_runner.py"
STATUS_PATH = ROOT / "docs/stage-4-current-status.md"

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


def synthetic_private_batch(completion: dict) -> dict:
    records = []
    for reference in completion["bundle"]["records"]:
        finding = reference["findingType"]
        item = DEVELOPMENT_ITEMS[reference["datasetItemId"]]
        spec = METRIC_SPECS[finding]
        records.append(
            {
                "observationId": reference["observationId"],
                "datasetItemId": reference["datasetItemId"],
                "artifactSha256": item["artifactSha256"],
                "sourceFamilyId": reference["sourceFamilyId"],
                "findingType": finding,
                "metricName": spec["metricName"],
                "direction": spec["direction"],
                "rawValue": PLACEHOLDER_VALUES[finding],
                "split": "development",
                "dataClass": "real",
                "purpose": "safety_calibration",
                "provenanceReference": "custody:synthetic-private-metric-validator",
            }
        )
    return {
        "schemaVersion": "1.0.0",
        "contractVersion": RUNNER_CONTRACT_VERSION,
        "batchId": "synthetic.contract-validator.private-metrics.v1",
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


def main() -> int:
    failures: list[str] = []
    for path in (AUTH_PATH, PURPOSE_PATH, ACCEPTANCE_PATH, COMPLETION_PATH, WORKFLOW_PATH, MODULE_PATH, STATUS_PATH):
        require(path.exists(), f"required Stage 4 runner input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    auth = read_json(AUTH_PATH)
    purpose = read_json(PURPOSE_PATH)
    acceptance = read_json(ACCEPTANCE_PATH)
    completion = read_json(COMPLETION_PATH)
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    module = MODULE_PATH.read_text(encoding="utf-8")
    status = STATUS_PATH.read_text(encoding="utf-8")

    batch = synthetic_private_batch(completion)
    validated = validate_private_metric_batch(batch, auth, purpose, acceptance, completion)
    require(len(validated["records"]) == 42, "valid private metric contract did not bind 42 records", failures)
    observations = materialize_development_observations(batch, auth, purpose, acceptance, completion)
    require(len(observations) == 42, "private runner did not materialize 42 observations", failures)
    require({item.split for item in observations} == {"development"}, "held-out split entered private development runner", failures)
    require({item.data_class for item in observations} == {"real"}, "private runner data class drifted", failures)
    require({item.purpose for item in observations} == {"safety_calibration"}, "private runner purpose drifted", failures)

    receipt = build_public_preparation_receipt(batch, auth, purpose, acceptance, completion)
    rendered = json.dumps(receipt, sort_keys=True)
    require(receipt.get("status") == "development_calibration_input_prepared", "public preparation receipt status drifted", failures)
    require(receipt.get("recordCount") == 42, "public preparation receipt record count drifted", failures)
    require(receipt.get("findingCounts") == {finding: 6 for finding in sorted(METRIC_SPECS)}, "public preparation finding counts drifted", failures)
    for forbidden in ("rawValue", "observationId", "dataset.item.", "source.family.", "custody:"):
        require(forbidden not in rendered, f"public preparation receipt leaked private token: {forbidden}", failures)
    assertions = receipt.get("assertions") or {}
    require(assertions.get("candidateDerivationInputReady") is True, "validated private input did not become derivation-ready", failures)
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
    tampered["records"][0]["split"] = "held_out"
    require(
        rejected_code(lambda: validate_private_metric_batch(tampered, auth, purpose, acceptance, completion)) == "held_out_in_development_batch",
        "held-out row entered development metric batch",
        failures,
    )

    require("private observation metrics" in status, "Stage 4 status lost private metric dependency", failures)
    require("realDataCalibrationExecuted=false" in status, "Stage 4 status prematurely claims real calibration execution", failures)
    require("candidateDerivationInputReady" in module, "runner module lost preparation-only boundary", failures)
    require("heldOutIncluded" in module, "runner module lost held-out non-claim", failures)
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
    print("- contract version: 0.1.0")
    print("- exact private development metric rows required: 42")
    print("- metric/finding/direction + artifact/source/reference/authorization bindings: enforced")
    print("- public receipt: digests + aggregate counts only")
    print("- raw private metric values in ordinary Git: 0")
    print("- candidate derivation input can be prepared; numerical threshold selection is not performed")
    print("- held-out evaluation/tuning, production changes, Stage 4 PASS and Stage 5: not authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
