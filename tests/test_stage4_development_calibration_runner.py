from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import unittest

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


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


AUTH = read_json("evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json")
PURPOSE = read_json("evidence/stage4/governance/purpose-grants.v1.json")
ACCEPTANCE = read_json("evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json")
COMPLETION = read_json("evidence/stage4/reference-labels/development-human-label-completion.v1.json")


PLACEHOLDER_VALUES = {
    "skew": 0.1,
    "blur": 150.0,
    "glare": 0.01,
    "shadow": 0.02,
    "uneven_lighting": 0.03,
    "noise": 0.01,
    "compression": 0.02,
}


def _applicability(item_id: str, finding: str) -> tuple[str, float | None, str | None]:
    if item_id == BARLEY_ID:
        return "not_applicable", None, "source_vector_only_preserved"
    if item_id == BEETHOVEN_ID and finding == "compression":
        return "not_applicable", None, "metric_not_applicable_to_png_derivative"
    return "measured", PLACEHOLDER_VALUES[finding], None


def synthetic_private_batch() -> dict:
    records = []
    for reference in COMPLETION["bundle"]["records"]:
        finding = reference["findingType"]
        item_id = reference["datasetItemId"]
        item = DEVELOPMENT_ITEMS[item_id]
        spec = METRIC_SPECS[finding]
        status, raw_value, reason = _applicability(item_id, finding)
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
                "provenanceReference": "custody:synthetic-private-metric-contract-test",
            }
        )
    return {
        "schemaVersion": PRIVATE_METRIC_SCHEMA_VERSION,
        "contractVersion": RUNNER_CONTRACT_VERSION,
        "batchId": "synthetic.contract-test.private-metrics.v2",
        "environment": "stage1_offline",
        "authorizationDigest": {"algorithm": "sha256", "value": AUTHORIZATION_CANONICAL_SHA256},
        "referenceBundleDigest": {"algorithm": "sha256", "value": BUNDLE_CANONICAL_SHA256},
        "records": records,
    }


class Stage4DevelopmentCalibrationRunnerTests(unittest.TestCase):
    def validate(self, batch: dict) -> dict:
        return validate_private_metric_batch(batch, AUTH, PURPOSE, ACCEPTANCE, COMPLETION)

    def test_valid_private_batch_accounts_for_all_42_reference_observations(self) -> None:
        batch = synthetic_private_batch()
        validated = self.validate(batch)
        self.assertEqual(42, len(validated["records"]))
        self.assertEqual(
            {record["observationId"] for record in COMPLETION["bundle"]["records"]},
            {record["observationId"] for record in validated["records"]},
        )
        self.assertEqual(
            EXPECTED_MEASURED_RECORD_COUNT,
            sum(record["measurementStatus"] == "measured" for record in validated["records"]),
        )
        self.assertEqual(
            EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
            sum(record["measurementStatus"] == "not_applicable" for record in validated["records"]),
        )

    def test_materialization_joins_only_measured_rows_to_human_labels(self) -> None:
        observations = materialize_development_observations(
            synthetic_private_batch(), AUTH, PURPOSE, ACCEPTANCE, COMPLETION
        )
        self.assertEqual(EXPECTED_MEASURED_RECORD_COUNT, len(observations))
        self.assertEqual({BEETHOVEN_ID}, {item.dataset_item_id for item in observations})
        self.assertNotIn("compression", {item.finding_type for item in observations})
        expected_labels = {
            record["observationId"]: record["referenceLabel"]
            for record in COMPLETION["bundle"]["records"]
        }
        for observation in observations:
            self.assertEqual(expected_labels[observation.observation_id], observation.reference_label)
            self.assertEqual("development", observation.split)
            self.assertEqual("real", observation.data_class)
            self.assertEqual("safety_calibration", observation.purpose)
            self.assertTrue(observation.purpose_permission_granted)

    def test_public_receipt_redacts_rows_values_and_reports_applicability(self) -> None:
        receipt = build_public_preparation_receipt(
            synthetic_private_batch(), AUTH, PURPOSE, ACCEPTANCE, COMPLETION
        )
        rendered = json.dumps(receipt, sort_keys=True)
        self.assertEqual("development_calibration_input_prepared_with_abstentions", receipt["status"])
        self.assertEqual(42, receipt["recordCount"])
        self.assertEqual(EXPECTED_MEASURED_RECORD_COUNT, receipt["measuredRecordCount"])
        self.assertEqual(EXPECTED_NOT_APPLICABLE_RECORD_COUNT, receipt["notApplicableRecordCount"])
        self.assertEqual(1, receipt["measuredSourceFamilyCount"])
        for finding in sorted(METRIC_SPECS):
            self.assertEqual(6, receipt["findingCounts"][finding]["total"])
        self.assertEqual({"total": 6, "measured": 0, "notApplicable": 6}, receipt["findingCounts"]["compression"])
        for finding in ("skew", "blur", "glare", "shadow", "uneven_lighting", "noise"):
            self.assertEqual({"total": 6, "measured": 4, "notApplicable": 2}, receipt["findingCounts"][finding])
        for forbidden in (
            "rawValue",
            "observationId",
            "dataset.item.imslp799143",
            "dataset.item.barley",
            "source.family.",
            "custody:synthetic-private-metric-contract-test",
        ):
            self.assertNotIn(forbidden, rendered)
        assertions = receipt["assertions"]
        self.assertTrue(assertions["candidateDerivationInputReady"])
        self.assertTrue(assertions["notApplicableMeasurementsPresent"])
        self.assertFalse(assertions["fullMetricCoverage"])
        self.assertFalse(assertions["crossFamilyMeasuredSupportSatisfied"])
        self.assertFalse(assertions["realDataCalibrationExecuted"])
        self.assertFalse(assertions["heldOutIncluded"])
        self.assertFalse(assertions["productionThresholdChangeAuthorized"])
        self.assertFalse(assertions["stage5EntryAuthorized"])

    def assert_rejected(self, batch: dict, code: str) -> None:
        with self.assertRaises(Stage4DevelopmentCalibrationRunnerError) as caught:
            self.validate(batch)
        self.assertEqual(code, caught.exception.code)

    def test_missing_record_fails_closed(self) -> None:
        batch = synthetic_private_batch()
        batch["records"].pop()
        self.assert_rejected(batch, "record_count_mismatch")

    def test_duplicate_observation_fails_closed(self) -> None:
        batch = synthetic_private_batch()
        batch["records"][-1] = deepcopy(batch["records"][0])
        self.assert_rejected(batch, "duplicate_observation")

    def test_wrong_artifact_sha_fails_closed(self) -> None:
        batch = synthetic_private_batch()
        batch["records"][0]["artifactSha256"] = "0" * 64
        self.assert_rejected(batch, "artifact_identity_mismatch")

    def test_metric_name_and_direction_are_finding_bound(self) -> None:
        batch = synthetic_private_batch()
        batch["records"][0]["metricName"] = "inventedMetric"
        self.assert_rejected(batch, "metric_name_mismatch")
        batch = synthetic_private_batch()
        measured = next(record for record in batch["records"] if record["measurementStatus"] == "measured")
        expected = METRIC_SPECS[measured["findingType"]]["direction"]
        measured["direction"] = "higher_is_worse" if expected == "lower_is_worse" else "lower_is_worse"
        self.assert_rejected(batch, "metric_direction_mismatch")

    def test_nonfinite_and_out_of_range_measured_values_fail_closed(self) -> None:
        batch = synthetic_private_batch()
        measured = next(record for record in batch["records"] if record["measurementStatus"] == "measured")
        measured["rawValue"] = math.inf
        self.assert_rejected(batch, "invalid_metric_value")
        batch = synthetic_private_batch()
        glare = next(record for record in batch["records"] if record["findingType"] == "glare" and record["measurementStatus"] == "measured")
        glare["rawValue"] = 1.1
        self.assert_rejected(batch, "invalid_metric_value")

    def test_vector_only_barley_cannot_be_faked_as_measured(self) -> None:
        batch = synthetic_private_batch()
        barley = next(record for record in batch["records"] if record["datasetItemId"] == BARLEY_ID)
        barley["measurementStatus"] = "measured"
        barley["rawValue"] = 0.0
        barley["notApplicableReason"] = None
        self.assert_rejected(batch, "measurement_applicability_mismatch")

    def test_beethoven_png_compression_cannot_be_faked_as_numeric_zero(self) -> None:
        batch = synthetic_private_batch()
        compression = next(
            record for record in batch["records"]
            if record["datasetItemId"] == BEETHOVEN_ID and record["findingType"] == "compression"
        )
        compression["rawValue"] = 0.0
        self.assert_rejected(batch, "invented_not_applicable_value")

    def test_not_applicable_reason_is_exact_and_measured_reason_is_null(self) -> None:
        batch = synthetic_private_batch()
        unavailable = next(record for record in batch["records"] if record["measurementStatus"] == "not_applicable")
        unavailable["notApplicableReason"] = "invented_reason"
        self.assert_rejected(batch, "invalid_not_applicable_reason")
        batch = synthetic_private_batch()
        measured = next(record for record in batch["records"] if record["measurementStatus"] == "measured")
        measured["notApplicableReason"] = "source_vector_only_preserved"
        self.assert_rejected(batch, "invalid_measurement_status")

    def test_held_out_or_wrong_purpose_cannot_enter_batch(self) -> None:
        batch = synthetic_private_batch()
        batch["records"][0]["split"] = "held_out"
        self.assert_rejected(batch, "held_out_in_development_batch")
        batch = synthetic_private_batch()
        batch["records"][0]["purpose"] = "held_out_evaluation"
        self.assert_rejected(batch, "purpose_mismatch")

    def test_private_rows_cannot_carry_reference_or_prediction_truth(self) -> None:
        batch = synthetic_private_batch()
        batch["records"][0]["referenceLabel"] = "clear"
        self.assert_rejected(batch, "reference_truth_in_private_metrics")
        batch = synthetic_private_batch()
        batch["records"][0]["predictedLabel"] = "probable"
        self.assert_rejected(batch, "reference_truth_in_private_metrics")

    def test_authorization_and_reference_digests_are_exact(self) -> None:
        batch = synthetic_private_batch()
        batch["authorizationDigest"]["value"] = "0" * 64
        self.assert_rejected(batch, "authorization_mismatch")
        batch = synthetic_private_batch()
        batch["referenceBundleDigest"]["value"] = "0" * 64
        self.assert_rejected(batch, "reference_bundle_mismatch")


if __name__ == "__main__":
    unittest.main()
