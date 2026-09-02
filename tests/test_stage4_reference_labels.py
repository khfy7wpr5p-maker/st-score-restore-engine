from __future__ import annotations

import unittest

from st_score_restore.stage4_reference_labels import (
    ReferenceLabelBundle,
    ReferenceLabelRecord,
    Stage4ReferenceLabelError,
    freeze_reference_label_bundle,
    require_candidate_derivation_eligible,
    validate_observation_bindings,
)


def synthetic_record(**overrides):
    values = {
        "label_id": "label-001",
        "observation_id": "obs-001",
        "dataset_item_id": "synthetic-item-001",
        "source_family_id": "synthetic-family-a",
        "finding_type": "blur",
        "reference_label": "probable",
        "split": "development",
        "data_class": "synthetic_test",
        "purpose": "synthetic_contract_test",
        "purpose_permission_granted": False,
        "provenance_reference": "synthetic-fixture:v1",
        "reviewer_reference": "reviewer:synthetic-001",
        "review_method": "synthetic_contract_test",
        "reviewed_on": "2026-09-02",
    }
    values.update(overrides)
    return ReferenceLabelRecord(**values)


def real_record(**overrides):
    values = {
        "label_id": "label-real-001",
        "observation_id": "obs-real-001",
        "dataset_item_id": "real-item-001",
        "source_family_id": "real-family-a",
        "finding_type": "skew",
        "reference_label": "possible",
        "split": "development",
        "data_class": "real",
        "purpose": "safety_calibration",
        "purpose_permission_granted": True,
        "provenance_reference": "custody:review-bundle-001",
        "reviewer_reference": "expert-reviewer:opaque-001",
        "review_method": "human_expert_review",
        "reviewed_on": "2026-09-02",
    }
    values.update(overrides)
    return ReferenceLabelRecord(**values)


class Stage4ReferenceLabelTests(unittest.TestCase):
    def test_synthetic_bundle_digest_is_order_independent(self):
        first = synthetic_record()
        second = synthetic_record(
            label_id="label-002",
            observation_id="obs-002",
            dataset_item_id="synthetic-item-002",
            source_family_id="synthetic-family-b",
            finding_type="glare",
            reference_label="clear",
        )
        bundle_a = ReferenceLabelBundle.from_records("bundle-synthetic-v1", [first, second])
        bundle_b = ReferenceLabelBundle.from_records("bundle-synthetic-v1", [second, first])
        self.assertEqual(bundle_a.digest(), bundle_b.digest())

    def test_synthetic_bundle_freezes_without_real_permission_claim(self):
        bundle = ReferenceLabelBundle.from_records("bundle-synthetic-v1", [synthetic_record()])
        receipt = freeze_reference_label_bundle(bundle)
        self.assertEqual(receipt["status"], "reference_bundle_frozen")
        self.assertFalse(receipt["assertions"]["labelsAutomaticallyGenerated"])
        self.assertFalse(receipt["assertions"]["modelPredictionsUsedAsReferenceLabels"])
        self.assertFalse(receipt["assertions"]["realReferenceBundleAccepted"])
        self.assertFalse(receipt["assertions"]["realDataCalibrationAuthorized"])
        self.assertFalse(receipt["assertions"]["productionThresholdChangeAuthorized"])

    def test_real_development_requires_safety_calibration_purpose(self):
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            real_record(purpose="pdf_pipeline_evaluation")
        self.assertEqual(caught.exception.code, "purpose_mismatch")

    def test_real_development_requires_granted_purpose(self):
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            real_record(purpose_permission_granted=False)
        self.assertEqual(caught.exception.code, "purpose_not_granted")

    def test_real_reference_requires_human_expert_review(self):
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            real_record(review_method="synthetic_contract_test")
        self.assertEqual(caught.exception.code, "real_reference_requires_human_review")

    def test_real_held_out_requires_held_out_evaluation_purpose(self):
        held_out = real_record(
            split="held_out",
            purpose="held_out_evaluation",
            label_id="held-label-001",
            observation_id="held-obs-001",
        )
        self.assertEqual(held_out.purpose, "held_out_evaluation")
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            real_record(split="held_out", purpose="safety_calibration")
        self.assertEqual(caught.exception.code, "purpose_mismatch")

    def test_real_bundle_cannot_be_frozen_as_accepted_implicitly(self):
        bundle = ReferenceLabelBundle.from_records("real-bundle-v1", [real_record()])
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            freeze_reference_label_bundle(bundle)
        self.assertEqual(caught.exception.code, "real_reference_bundle_not_accepted")

    def test_held_out_bundle_cannot_derive_candidate(self):
        bundle = ReferenceLabelBundle.from_records(
            "held-out-bundle-v1",
            [
                real_record(
                    split="held_out",
                    purpose="held_out_evaluation",
                    label_id="held-label-001",
                    observation_id="held-obs-001",
                )
            ],
        )
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            require_candidate_derivation_eligible(bundle, accepted_real_reference_bundle=True)
        self.assertEqual(caught.exception.code, "held_out_reference_derivation_forbidden")

    def test_duplicate_observation_ids_are_rejected(self):
        first = synthetic_record()
        second = synthetic_record(label_id="label-002", reference_label="clear")
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            ReferenceLabelBundle.from_records("duplicate-observation-v1", [first, second])
        self.assertEqual(caught.exception.code, "duplicate_observation_id")

    def test_prediction_fields_cannot_enter_reference_binding(self):
        bundle = ReferenceLabelBundle.from_records("bundle-synthetic-v1", [synthetic_record()])
        raw = {
            "observationId": "obs-001",
            "datasetItemId": "synthetic-item-001",
            "sourceFamilyId": "synthetic-family-a",
            "findingType": "blur",
            "split": "development",
            "dataClass": "synthetic_test",
            "purpose": "synthetic_contract_test",
            "predictedLabel": "probable",
        }
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            validate_observation_bindings(bundle, [raw])
        self.assertEqual(caught.exception.code, "invalid_observation_binding")

    def test_exact_one_to_one_binding_is_required(self):
        bundle = ReferenceLabelBundle.from_records("bundle-synthetic-v1", [synthetic_record()])
        with self.assertRaises(Stage4ReferenceLabelError) as caught:
            validate_observation_bindings(bundle, [])
        self.assertEqual(caught.exception.code, "observation_set_mismatch")

    def test_valid_binding_has_deterministic_digest(self):
        bundle = ReferenceLabelBundle.from_records("bundle-synthetic-v1", [synthetic_record()])
        raw = {
            "observationId": "obs-001",
            "datasetItemId": "synthetic-item-001",
            "sourceFamilyId": "synthetic-family-a",
            "findingType": "blur",
            "split": "development",
            "dataClass": "synthetic_test",
            "purpose": "synthetic_contract_test",
        }
        first = validate_observation_bindings(bundle, [raw])
        second = validate_observation_bindings(bundle, [dict(raw)])
        self.assertEqual(first["status"], "bindings_valid")
        self.assertEqual(first["bindingDigest"], second["bindingDigest"])
        self.assertTrue(first["assertions"]["oneToOneObservationBinding"])
        self.assertFalse(first["assertions"]["predictionFieldsAcceptedAsReferenceEvidence"])
        self.assertFalse(first["assertions"]["heldOutCandidateDerivationAuthorized"])


if __name__ == "__main__":
    unittest.main()
