from __future__ import annotations

import json
import unittest

from st_score_restore.stage4_calibration import CalibrationObservation
from st_score_restore.stage4_candidate_derivation import (
    DERIVATION_CONTRACT_VERSION,
    DERIVATION_METHODOLOGY_ID,
    Stage4CandidateDerivationError,
    build_public_derivation_receipt,
    derive_candidate,
)

PARENT = "1" * 64


def observation(
    oid: str,
    value: float,
    label: str,
    *,
    family: str,
    direction_finding: str = "glare",
    metric_name: str = "score",
    split: str = "development",
) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=oid,
        dataset_item_id=f"test.item.{family}",
        source_family_id=family,
        finding_type=direction_finding,
        metric_name=metric_name,
        raw_value=value,
        reference_label=label,
        split=split,
        data_class="real",
        purpose="safety_calibration" if split == "development" else "held_out_evaluation",
        purpose_permission_granted=True,
        provenance_reference=f"custody:test-{oid}",
    )


def higher_evidence() -> list[CalibrationObservation]:
    return [
        observation("c1", 0.10, "clear", family="family-a"),
        observation("c2", 0.20, "clear", family="family-b"),
        observation("p1", 0.40, "possible", family="family-a"),
        observation("p2", 0.50, "possible", family="family-b"),
        observation("r1", 0.80, "probable", family="family-a"),
        observation("r2", 0.90, "probable", family="family-b"),
    ]


def lower_evidence() -> list[CalibrationObservation]:
    return [
        observation("c1", 100.0, "clear", family="family-a", direction_finding="blur", metric_name="laplacianVariance"),
        observation("c2", 90.0, "clear", family="family-b", direction_finding="blur", metric_name="laplacianVariance"),
        observation("p1", 70.0, "possible", family="family-a", direction_finding="blur", metric_name="laplacianVariance"),
        observation("p2", 60.0, "possible", family="family-b", direction_finding="blur", metric_name="laplacianVariance"),
        observation("r1", 40.0, "probable", family="family-a", direction_finding="blur", metric_name="laplacianVariance"),
        observation("r2", 30.0, "probable", family="family-b", direction_finding="blur", metric_name="laplacianVariance"),
    ]


class Stage4CandidateDerivationTests(unittest.TestCase):
    def test_contract_identity_is_fixed(self) -> None:
        self.assertEqual("0.1.0", DERIVATION_CONTRACT_VERSION)
        self.assertEqual("strict_empirical_midpoint_boundary_v1", DERIVATION_METHODOLOGY_ID)

    def test_higher_is_worse_derives_only_from_strict_ordered_classes(self) -> None:
        report = derive_candidate(
            higher_evidence(),
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        self.assertEqual("candidate_derived", report["status"])
        candidate = report["candidateManifest"]["candidate"]
        self.assertAlmostEqual(0.30, candidate["possibleThreshold"])
        self.assertAlmostEqual(0.65, candidate["probableThreshold"])
        self.assertEqual("development", candidate["derivedFromSplit"])
        self.assertEqual("real", candidate["derivationDataClass"])
        self.assertFalse(report["assertions"]["heldOutThresholdTuningUsed"])
        self.assertFalse(report["assertions"]["metricAcceptanceTargetPolicyApplied"])

    def test_lower_is_worse_derives_ordered_midpoints(self) -> None:
        report = derive_candidate(
            lower_evidence(),
            finding_type="blur",
            metric_name="laplacianVariance",
            direction="lower_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        candidate = report["candidateManifest"]["candidate"]
        self.assertAlmostEqual(80.0, candidate["possibleThreshold"])
        self.assertAlmostEqual(50.0, candidate["probableThreshold"])

    def test_missing_reference_class_abstains_instead_of_inventing_threshold(self) -> None:
        evidence = [item for item in higher_evidence() if item.reference_label != "probable"]
        report = derive_candidate(
            evidence,
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        self.assertEqual("abstained", report["status"])
        self.assertIn("insufficient_reference_class_support", report["reasonCodes"])
        self.assertNotIn("candidateManifest", report)
        self.assertTrue(report["assertions"]["missingSeverityClassThresholdInvented"] is False)

    def test_overlapping_reference_ranges_abstain(self) -> None:
        evidence = higher_evidence()
        evidence[2] = observation("p1", 0.15, "possible", family="family-a")
        report = derive_candidate(
            evidence,
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        self.assertEqual("abstained", report["status"])
        self.assertIn("clear_possible_metric_overlap", report["reasonCodes"])
        self.assertNotIn("candidateManifest", report)

    def test_one_source_family_abstains(self) -> None:
        evidence = [
            observation(item.observation_id, item.raw_value, item.reference_label, family="family-a")
            for item in higher_evidence()
        ]
        report = derive_candidate(
            evidence,
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        self.assertEqual("abstained", report["status"])
        self.assertIn("insufficient_source_family_support", report["reasonCodes"])

    def test_real_derivation_requires_execution_authorization(self) -> None:
        with self.assertRaises(Stage4CandidateDerivationError) as caught:
            derive_candidate(
                higher_evidence(),
                finding_type="glare",
                metric_name="score",
                direction="higher_is_worse",
                parent_configuration_digest=PARENT,
                real_data_execution_authorized=False,
            )
        self.assertEqual("real_data_calibration_not_authorized", caught.exception.code)

    def test_held_out_observation_is_rejected_not_used(self) -> None:
        evidence = higher_evidence()
        evidence[-1] = observation("held-r2", 0.90, "probable", family="family-b", split="held_out")
        with self.assertRaises(Stage4CandidateDerivationError) as caught:
            derive_candidate(
                evidence,
                finding_type="glare",
                metric_name="score",
                direction="higher_is_worse",
                parent_configuration_digest=PARENT,
                real_data_execution_authorized=True,
            )
        self.assertEqual("held_out_tuning_forbidden", caught.exception.code)

    def test_public_receipt_redacts_thresholds_rows_and_private_identity(self) -> None:
        report = derive_candidate(
            higher_evidence(),
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        receipt = build_public_derivation_receipt(report)
        rendered = json.dumps(receipt, sort_keys=True)
        self.assertEqual("development_candidate_derivation_public_receipt", receipt["status"])
        self.assertEqual("candidate_derived", receipt["derivationStatus"])
        self.assertIn("candidateDigest", receipt)
        self.assertIn("candidateManifestDigest", receipt)
        for forbidden in (
            "possibleThreshold",
            "probableThreshold",
            "rawValue",
            "observationId",
            "test.item.",
            "family-a",
            "custody:",
        ):
            self.assertNotIn(forbidden, rendered)
        assertions = receipt["assertions"]
        self.assertFalse(assertions["candidateThresholdValuesPublic"])
        self.assertFalse(assertions["heldOutThresholdTuningUsed"])
        self.assertFalse(assertions["metricAcceptanceTargetPolicyApplied"])
        self.assertFalse(assertions["stage5EntryAuthorized"])

    def test_public_abstention_receipt_contains_reason_not_threshold(self) -> None:
        report = derive_candidate(
            [item for item in higher_evidence() if item.reference_label != "probable"],
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            parent_configuration_digest=PARENT,
            real_data_execution_authorized=True,
        )
        receipt = build_public_derivation_receipt(report)
        self.assertEqual("abstained", receipt["derivationStatus"])
        self.assertIn("insufficient_reference_class_support", receipt["reasonCodes"])
        self.assertNotIn("candidateDigest", receipt)


if __name__ == "__main__":
    unittest.main()
