from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from st_score_restore.stage4_development_calibration_runner import METRIC_SPECS
from st_score_restore.stage4_reference_label_completion import (
    BUNDLE_CANONICAL_SHA256 as BB_BUNDLE_SHA256,
)
from st_score_restore.stage4_wikimedia_expanded_execution_authorization import (
    AUTHORIZATION_CANONICAL_SHA256,
    EXPECTED_ITEMS,
)
from st_score_restore.stage4_wikimedia_reference_acceptance import (
    WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
)
from st_score_restore.stage4_expanded_development_calibration_runner import (
    BARLEY_ID,
    BEETHOVEN_ID,
    EXPECTED_MEASURED_RECORD_COUNT,
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

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "evidence/stage4/governance/expanded-development-calibration-execution-authorization.v1.json"
BB_PURPOSE = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
BB_ACCEPTANCE = ROOT / "evidence/stage4/reference-labels/development-reference-bundle-acceptance.v1.json"
BB_COMPLETION = ROOT / "evidence/stage4/reference-labels/development-human-label-completion.v1.json"
WIKI_PURPOSE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/purpose-grant.v1.json"
WIKI_ACCEPTANCE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-bundle-acceptance.v1.json"
WIKI_COMPLETION = ROOT / "evidence/stage4/corpus-expansion/wikimedia/human-label-completion.v1.json"
WIKI_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"

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


class Stage4ExpandedDevelopmentCalibrationRunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auth = load(AUTH)
        cls.bb_purpose = load(BB_PURPOSE)
        cls.bb_acceptance = load(BB_ACCEPTANCE)
        cls.bb_completion = load(BB_COMPLETION)
        cls.wiki_purpose = load(WIKI_PURPOSE)
        cls.wiki_acceptance = load(WIKI_ACCEPTANCE)
        cls.wiki_completion = load(WIKI_COMPLETION)
        cls.wiki_package = load(WIKI_PACKAGE)

    def _references(self) -> list[dict]:
        return [
            *self.bb_completion["bundle"]["records"],
            *self.wiki_completion["bundle"]["records"],
        ]

    def _applicability(
        self,
        item_id: str,
        finding: str,
    ) -> tuple[str, float | None, str | None]:
        if item_id == BARLEY_ID:
            return "not_applicable", None, "source_vector_only_preserved"
        if item_id in {BEETHOVEN_ID, WIKIMEDIA_ID} and finding == "compression":
            return "not_applicable", None, "metric_not_applicable_to_png_derivative"
        return "measured", PLACEHOLDER_VALUES[finding], None

    def _batch(self) -> dict:
        records = []
        for reference in self._references():
            item_id = reference["datasetItemId"]
            finding = reference["findingType"]
            status, raw_value, reason = self._applicability(item_id, finding)
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
                    "provenanceReference": "custody:synthetic-expanded-runner-unit-test",
                }
            )
        return {
            "schemaVersion": PRIVATE_METRIC_SCHEMA_VERSION,
            "contractVersion": RUNNER_CONTRACT_VERSION,
            "batchId": "synthetic.contract-only.expanded-private-metrics.v1",
            "environment": "stage1_offline",
            "authorizationDigest": {
                "algorithm": "sha256",
                "value": AUTHORIZATION_CANONICAL_SHA256,
            },
            "referenceBundleDigests": {
                "beethovenBarley": {
                    "algorithm": "sha256",
                    "value": BB_BUNDLE_SHA256,
                },
                "wikimedia": {
                    "algorithm": "sha256",
                    "value": WIKIMEDIA_BUNDLE_CANONICAL_SHA256,
                },
            },
            "records": records,
        }

    def _validate(self, batch: dict) -> dict:
        return validate_expanded_private_metric_batch(
            batch,
            self.auth,
            self.bb_purpose,
            self.bb_acceptance,
            self.bb_completion,
            self.wiki_purpose,
            self.wiki_acceptance,
            self.wiki_completion,
            self.wiki_package,
        )

    def test_exact_49_record_contract_accepts_only_synthetic_contract_input(self) -> None:
        validated = self._validate(self._batch())
        self.assertEqual(EXPECTED_RECORD_COUNT, len(validated["records"]))
        self.assertEqual(
            EXPECTED_MEASURED_RECORD_COUNT,
            sum(row["measurementStatus"] == "measured" for row in validated["records"]),
        )
        self.assertEqual(
            EXPECTED_NOT_APPLICABLE_RECORD_COUNT,
            sum(
                row["measurementStatus"] == "not_applicable"
                for row in validated["records"]
            ),
        )

    def test_wikimedia_has_six_measured_metrics_and_png_compression_abstention(self) -> None:
        validated = self._validate(self._batch())
        rows = [
            row
            for row in validated["records"]
            if row["datasetItemId"] == WIKIMEDIA_ID
        ]
        self.assertEqual(7, len(rows))
        compression = next(row for row in rows if row["findingType"] == "compression")
        self.assertEqual("not_applicable", compression["measurementStatus"])
        self.assertIsNone(compression["rawValue"])
        self.assertEqual(
            "metric_not_applicable_to_png_derivative",
            compression["notApplicableReason"],
        )
        measured = [row for row in rows if row["measurementStatus"] == "measured"]
        self.assertEqual(6, len(measured))
        self.assertEqual(
            set(METRIC_SPECS) - {"compression"},
            {row["findingType"] for row in measured},
        )

    def test_materialized_observations_cover_beethoven_and_wikimedia_only(self) -> None:
        observations = materialize_expanded_development_observations(
            self._batch(),
            self.auth,
            self.bb_purpose,
            self.bb_acceptance,
            self.bb_completion,
            self.wiki_purpose,
            self.wiki_acceptance,
            self.wiki_completion,
            self.wiki_package,
        )
        self.assertEqual(30, len(observations))
        self.assertEqual(
            {BEETHOVEN_ID, WIKIMEDIA_ID},
            {item.dataset_item_id for item in observations},
        )
        self.assertNotIn(BARLEY_ID, {item.dataset_item_id for item in observations})
        self.assertFalse(
            any(
                item.dataset_item_id == WIKIMEDIA_ID
                and item.finding_type == "compression"
                for item in observations
            )
        )

    def test_public_receipt_is_aggregate_only_and_cross_family_measured(self) -> None:
        receipt = build_expanded_public_preparation_receipt(
            self._batch(),
            self.auth,
            self.bb_purpose,
            self.bb_acceptance,
            self.bb_completion,
            self.wiki_purpose,
            self.wiki_acceptance,
            self.wiki_completion,
            self.wiki_package,
        )
        self.assertEqual(49, receipt["recordCount"])
        self.assertEqual(30, receipt["measuredRecordCount"])
        self.assertEqual(19, receipt["notApplicableRecordCount"])
        self.assertEqual(2, receipt["measuredSourceFamilyCount"])
        self.assertTrue(receipt["assertions"]["crossFamilyMeasuredSupportSatisfied"])
        self.assertFalse(receipt["assertions"]["realDataCalibrationExecuted"])
        self.assertEqual(
            {"total": 7, "measured": 0, "notApplicable": 7},
            receipt["findingCounts"]["compression"],
        )
        for finding in (
            "skew",
            "blur",
            "glare",
            "shadow",
            "uneven_lighting",
            "noise",
        ):
            self.assertEqual(
                {"total": 7, "measured": 5, "notApplicable": 2},
                receipt["findingCounts"][finding],
            )
        rendered = json.dumps(receipt, sort_keys=True)
        for forbidden in (
            "rawValue",
            "observationId",
            "dataset.item.",
            "source.family.",
            "custody:",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_reference_truth_inside_private_row_is_rejected(self) -> None:
        batch = self._batch()
        batch["records"][0]["referenceLabel"] = "clear"
        with self.assertRaises(Stage4ExpandedDevelopmentCalibrationRunnerError) as caught:
            self._validate(batch)
        self.assertEqual("reference_truth_in_private_metrics", caught.exception.code)

    def test_wikimedia_non_compression_metric_cannot_be_marked_not_applicable(self) -> None:
        batch = self._batch()
        row = next(
            row
            for row in batch["records"]
            if row["datasetItemId"] == WIKIMEDIA_ID
            and row["findingType"] != "compression"
        )
        row["measurementStatus"] = "not_applicable"
        row["rawValue"] = None
        row["notApplicableReason"] = "metric_not_applicable_to_png_derivative"
        with self.assertRaises(Stage4ExpandedDevelopmentCalibrationRunnerError) as caught:
            self._validate(batch)
        self.assertEqual("measurement_applicability_mismatch", caught.exception.code)

    def test_wikimedia_compression_cannot_carry_invented_numeric_value(self) -> None:
        batch = self._batch()
        row = next(
            row
            for row in batch["records"]
            if row["datasetItemId"] == WIKIMEDIA_ID
            and row["findingType"] == "compression"
        )
        row["measurementStatus"] = "measured"
        row["rawValue"] = 0.0
        row["notApplicableReason"] = None
        with self.assertRaises(Stage4ExpandedDevelopmentCalibrationRunnerError) as caught:
            self._validate(batch)
        self.assertEqual("measurement_applicability_mismatch", caught.exception.code)

    def test_held_out_substitution_is_rejected(self) -> None:
        batch = self._batch()
        batch["records"][0]["datasetItemId"] = "dataset.item.imslp82860-chopin-op69.v2"
        with self.assertRaises(Stage4ExpandedDevelopmentCalibrationRunnerError) as caught:
            self._validate(batch)
        self.assertEqual("observation_identity_mismatch", caught.exception.code)

    def test_wrong_authorization_digest_is_rejected(self) -> None:
        batch = self._batch()
        batch["authorizationDigest"]["value"] = "0" * 64
        with self.assertRaises(Stage4ExpandedDevelopmentCalibrationRunnerError) as caught:
            self._validate(batch)
        self.assertEqual("authorization_mismatch", caught.exception.code)

    def test_contract_version_records_applicability_correction(self) -> None:
        self.assertEqual("0.3.1", RUNNER_CONTRACT_VERSION)
        self.assertEqual(30, EXPECTED_MEASURED_RECORD_COUNT)
        self.assertEqual(19, EXPECTED_NOT_APPLICABLE_RECORD_COUNT)


if __name__ == "__main__":
    unittest.main()
