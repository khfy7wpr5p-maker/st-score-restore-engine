from __future__ import annotations

import unittest

from st_score_restore.stage4_calibration import (
    CalibrationObservation,
    Stage4CalibrationError,
    ThresholdCandidate,
    evaluate_candidate,
    freeze_candidate,
)


def synthetic_observation(
    *,
    observation_id: str,
    source_family_id: str,
    raw_value: float,
    reference_label: str,
    split: str = "development",
) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=observation_id,
        dataset_item_id=f"dataset.{observation_id}",
        source_family_id=source_family_id,
        finding_type="glare",
        metric_name="score",
        raw_value=raw_value,
        reference_label=reference_label,
        split=split,
        data_class="synthetic_test",
        purpose="synthetic_contract_test",
        purpose_permission_granted=False,
        provenance_reference=f"synthetic:{observation_id}",
    )


def candidate(*, families: tuple[str, ...] = ("family.dev.a",)) -> ThresholdCandidate:
    return ThresholdCandidate(
        candidate_id="candidate.glare.v1",
        finding_type="glare",
        metric_name="score",
        direction="higher_is_worse",
        possible_threshold=0.10,
        probable_threshold=0.20,
        derivation_data_class="synthetic_test",
        derived_from_split="development",
        derived_from_source_families=families,
        parent_configuration_digest="0" * 64,
    )


class Stage4CalibrationTests(unittest.TestCase):
    def test_synthetic_candidate_freeze_is_deterministic_and_non_production(self) -> None:
        observations = [
            synthetic_observation(
                observation_id="dev-a-1",
                source_family_id="family.dev.a",
                raw_value=0.05,
                reference_label="clear",
            ),
            synthetic_observation(
                observation_id="dev-a-2",
                source_family_id="family.dev.a",
                raw_value=0.16,
                reference_label="possible",
            ),
        ]
        first = freeze_candidate(candidate(), observations)
        second = freeze_candidate(candidate(), observations)

        self.assertEqual(first, second)
        self.assertEqual("candidate_frozen", first["status"])
        self.assertFalse(first["assertions"]["heldOutThresholdTuningUsed"])
        self.assertFalse(first["assertions"]["realDataExecutionAuthorized"])
        self.assertFalse(first["assertions"]["productionThresholdChangeAuthorized"])
        self.assertFalse(first["assertions"]["productionResourceLimitChangeAuthorized"])

    def test_held_out_observation_cannot_derive_candidate(self) -> None:
        observations = [
            synthetic_observation(
                observation_id="heldout-1",
                source_family_id="family.heldout.a",
                raw_value=0.30,
                reference_label="probable",
                split="held_out",
            )
        ]
        with self.assertRaises(Stage4CalibrationError) as context:
            freeze_candidate(candidate(families=("family.heldout.a",)), observations)
        self.assertEqual("held_out_tuning_forbidden", context.exception.code)

    def test_real_development_without_safety_calibration_grant_is_rejected(self) -> None:
        with self.assertRaises(Stage4CalibrationError) as context:
            CalibrationObservation(
                observation_id="real-dev-1",
                dataset_item_id="dataset.real.dev",
                source_family_id="family.real.dev",
                finding_type="glare",
                metric_name="score",
                raw_value=0.20,
                reference_label="probable",
                split="development",
                data_class="real",
                purpose="safety_calibration",
                purpose_permission_granted=False,
                provenance_reference="evidence:real-dev-1",
            )
        self.assertEqual("purpose_not_granted", context.exception.code)

    def test_real_development_with_claimed_grant_still_requires_execution_authorization(self) -> None:
        observation = CalibrationObservation(
            observation_id="real-dev-2",
            dataset_item_id="dataset.real.dev",
            source_family_id="family.real.dev",
            finding_type="glare",
            metric_name="score",
            raw_value=0.20,
            reference_label="probable",
            split="development",
            data_class="real",
            purpose="safety_calibration",
            purpose_permission_granted=True,
            provenance_reference="evidence:real-dev-2",
        )
        real_candidate = ThresholdCandidate(
            candidate_id="candidate.real.glare.v1",
            finding_type="glare",
            metric_name="score",
            direction="higher_is_worse",
            possible_threshold=0.10,
            probable_threshold=0.20,
            derivation_data_class="real",
            derived_from_split="development",
            derived_from_source_families=("family.real.dev",),
            parent_configuration_digest="1" * 64,
        )
        with self.assertRaises(Stage4CalibrationError) as context:
            freeze_candidate(real_candidate, [observation])
        self.assertEqual("real_data_calibration_not_authorized", context.exception.code)

    def test_held_out_source_family_leakage_is_rejected(self) -> None:
        observation = synthetic_observation(
            observation_id="heldout-overlap",
            source_family_id="family.dev.a",
            raw_value=0.30,
            reference_label="probable",
            split="held_out",
        )
        with self.assertRaises(Stage4CalibrationError) as context:
            evaluate_candidate(candidate(), [observation], evaluation_split="held_out")
        self.assertEqual("source_family_leakage", context.exception.code)

    def test_held_out_evaluation_reports_false_negative_without_tuning(self) -> None:
        observations = [
            synthetic_observation(
                observation_id="heldout-clear",
                source_family_id="family.heldout.a",
                raw_value=0.05,
                reference_label="clear",
                split="held_out",
            ),
            synthetic_observation(
                observation_id="heldout-fn",
                source_family_id="family.heldout.b",
                raw_value=0.15,
                reference_label="probable",
                split="held_out",
            ),
            synthetic_observation(
                observation_id="heldout-na",
                source_family_id="family.heldout.c",
                raw_value=0.12,
                reference_label="not_assessed",
                split="held_out",
            ),
        ]
        report = evaluate_candidate(candidate(), observations, evaluation_split="held_out")
        metrics = report["evaluation"]["metrics"]

        self.assertEqual(3, metrics["observationCount"])
        self.assertEqual(2, metrics["assessedCount"])
        self.assertEqual(1, metrics["notAssessedCount"])
        self.assertEqual(1, metrics["falseNegativeCount"])
        self.assertEqual(0, metrics["falsePositiveCount"])
        self.assertEqual(0.5, metrics["falseNegativeRate"])
        self.assertFalse(report["assertions"]["heldOutThresholdTuningUsed"])
        self.assertFalse(report["assertions"]["evaluationFedBackIntoCandidate"])
        self.assertFalse(report["assertions"]["productionThresholdChangeAuthorized"])

    def test_lower_is_worse_threshold_order_is_enforced(self) -> None:
        with self.assertRaises(Stage4CalibrationError) as context:
            ThresholdCandidate(
                candidate_id="candidate.blur.invalid",
                finding_type="blur",
                metric_name="laplacianVariance",
                direction="lower_is_worse",
                possible_threshold=60.0,
                probable_threshold=120.0,
                derivation_data_class="synthetic_test",
                derived_from_split="development",
                derived_from_source_families=("family.dev.blur",),
                parent_configuration_digest="2" * 64,
            )
        self.assertEqual("invalid_threshold_order", context.exception.code)


if __name__ == "__main__":
    unittest.main()
