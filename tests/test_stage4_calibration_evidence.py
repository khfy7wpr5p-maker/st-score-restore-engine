from __future__ import annotations

import copy
import json
import unittest

from st_score_restore.stage4_calibration import (
    CalibrationObservation,
    ThresholdCandidate,
    evaluate_candidate,
    freeze_candidate,
)
from st_score_restore.stage4_calibration_evidence import (
    Stage4CalibrationEvidenceError,
    build_public_candidate_evidence,
    build_public_evaluation_evidence,
)
from st_score_restore.stage4_reference_labels import (
    ReferenceLabelBundle,
    ReferenceLabelRecord,
    freeze_reference_label_bundle,
    validate_observation_bindings,
)


def calibration_observation(
    observation_id: str,
    dataset_item_id: str,
    source_family_id: str,
    raw_value: float,
    reference_label: str,
    *,
    split: str = "development",
    data_class: str = "synthetic_test",
    purpose: str = "synthetic_contract_test",
    permission: bool = False,
) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=observation_id,
        dataset_item_id=dataset_item_id,
        source_family_id=source_family_id,
        finding_type="blur",
        metric_name="laplacian_variance_inverse",
        raw_value=raw_value,
        reference_label=reference_label,
        split=split,
        data_class=data_class,
        purpose=purpose,
        purpose_permission_granted=permission,
        provenance_reference=f"custody:metric-{observation_id}",
    )


def reference_record(observation: CalibrationObservation) -> ReferenceLabelRecord:
    review_method = "synthetic_contract_test" if observation.data_class == "synthetic_test" else "human_expert_review"
    return ReferenceLabelRecord(
        label_id=f"label-{observation.observation_id}",
        observation_id=observation.observation_id,
        dataset_item_id=observation.dataset_item_id,
        source_family_id=observation.source_family_id,
        finding_type=observation.finding_type,
        reference_label=observation.reference_label,
        split=observation.split,
        data_class=observation.data_class,
        purpose=observation.purpose,
        purpose_permission_granted=observation.purpose_permission_granted,
        provenance_reference=f"custody:reference-{observation.observation_id}",
        reviewer_reference=f"reviewer:opaque-{observation.observation_id}",
        review_method=review_method,
        reviewed_on="2026-09-02",
    )


def binding_row(observation: CalibrationObservation) -> dict:
    return {
        "observationId": observation.observation_id,
        "datasetItemId": observation.dataset_item_id,
        "sourceFamilyId": observation.source_family_id,
        "findingType": observation.finding_type,
        "split": observation.split,
        "dataClass": observation.data_class,
        "purpose": observation.purpose,
    }


def candidate() -> ThresholdCandidate:
    return ThresholdCandidate(
        candidate_id="synthetic-blur-candidate-v1",
        finding_type="blur",
        metric_name="laplacian_variance_inverse",
        direction="higher_is_worse",
        possible_threshold=0.4,
        probable_threshold=0.7,
        derivation_data_class="synthetic_test",
        derived_from_split="development",
        derived_from_source_families=("synthetic-dev-family-a", "synthetic-dev-family-b"),
        parent_configuration_digest="0" * 64,
    )


def build_fixture():
    dev = [
        calibration_observation("dev-001", "synthetic-dev-item-a", "synthetic-dev-family-a", 0.2, "clear"),
        calibration_observation("dev-002", "synthetic-dev-item-b", "synthetic-dev-family-b", 0.8, "probable"),
    ]
    dev_labels = ReferenceLabelBundle.from_records("synthetic-dev-reference-v1", [reference_record(item) for item in dev])
    dev_receipt = freeze_reference_label_bundle(dev_labels)
    dev_binding = validate_observation_bindings(dev_labels, [binding_row(item) for item in dev])
    candidate_manifest = freeze_candidate(candidate(), dev)
    public_candidate = build_public_candidate_evidence(candidate_manifest, dev_receipt, dev_binding)

    held = [
        calibration_observation(
            "held-001",
            "synthetic-held-item-a",
            "synthetic-held-family-a",
            0.5,
            "possible",
            split="held_out",
        ),
        calibration_observation(
            "held-002",
            "synthetic-held-item-b",
            "synthetic-held-family-b",
            0.9,
            "probable",
            split="held_out",
        ),
    ]
    held_labels = ReferenceLabelBundle.from_records("synthetic-held-reference-v1", [reference_record(item) for item in held])
    held_receipt = freeze_reference_label_bundle(held_labels)
    held_binding = validate_observation_bindings(held_labels, [binding_row(item) for item in held])
    report = evaluate_candidate(candidate(), held, evaluation_split="held_out")
    public_evaluation = build_public_evaluation_evidence(public_candidate, report, held_receipt, held_binding)
    return {
        "dev": dev,
        "candidateManifest": candidate_manifest,
        "devReceipt": dev_receipt,
        "devBinding": dev_binding,
        "publicCandidate": public_candidate,
        "held": held,
        "heldReceipt": held_receipt,
        "heldBinding": held_binding,
        "report": report,
        "publicEvaluation": public_evaluation,
    }


class Stage4CalibrationEvidenceTests(unittest.TestCase):
    def test_candidate_public_evidence_is_deterministic(self):
        fixture = build_fixture()
        second = build_public_candidate_evidence(
            fixture["candidateManifest"], fixture["devReceipt"], fixture["devBinding"]
        )
        self.assertEqual(fixture["publicCandidate"], second)

    def test_candidate_public_evidence_is_non_authorizing(self):
        assertions = build_fixture()["publicCandidate"]["assertions"]
        self.assertTrue(assertions["syntheticContractEvidenceOnly"])
        for key in (
            "realReferenceBundleAccepted",
            "realDataCalibrationExecuted",
            "heldOutThresholdTuningUsed",
            "productionThresholdChangeAuthorized",
            "productionResourceLimitChangeAuthorized",
            "modelTrainingAuthorized",
            "publicationAuthorized",
            "stage4ExitPass",
            "stage5EntryAuthorized",
        ):
            self.assertFalse(assertions[key])

    def test_evaluation_public_evidence_is_aggregate_only(self):
        evidence = build_fixture()["publicEvaluation"]
        self.assertEqual(evidence["evaluationSummary"]["split"], "held_out")
        self.assertNotIn("results", evidence["evaluationSummary"])
        self.assertEqual(evidence["evaluationSummary"]["metrics"]["observationCount"], 2)
        self.assertEqual(evidence["evaluationSummary"]["metrics"]["sourceFamilyLeakageCount"], 0)

    def test_public_evidence_does_not_expose_private_identity_values(self):
        fixture = build_fixture()
        rendered = json.dumps(
            {"candidate": fixture["publicCandidate"], "evaluation": fixture["publicEvaluation"]},
            sort_keys=True,
        )
        for private_value in (
            "synthetic-dev-item-a",
            "synthetic-dev-family-a",
            "synthetic-held-item-a",
            "synthetic-held-family-a",
            "reviewer:opaque-dev-001",
            "custody:reference-dev-001",
            "custody:metric-dev-001",
        ):
            self.assertNotIn(private_value, rendered)

    def test_candidate_reference_count_mismatch_fails_closed(self):
        fixture = build_fixture()
        one_label_bundle = ReferenceLabelBundle.from_records(
            "one-label-v1", [reference_record(fixture["dev"][0])]
        )
        one_receipt = freeze_reference_label_bundle(one_label_bundle)
        one_binding = validate_observation_bindings(one_label_bundle, [binding_row(fixture["dev"][0])])
        with self.assertRaises(Stage4CalibrationEvidenceError) as caught:
            build_public_candidate_evidence(fixture["candidateManifest"], one_receipt, one_binding)
        self.assertEqual(caught.exception.code, "evidence_count_mismatch")

    def test_real_candidate_manifest_is_rejected_even_if_simulated_authorized(self):
        real_observation = calibration_observation(
            "real-001",
            "real-item-001",
            "real-family-a",
            0.8,
            "probable",
            data_class="real",
            purpose="safety_calibration",
            permission=True,
        )
        real_candidate = ThresholdCandidate(
            candidate_id="real-simulated-v1",
            finding_type="blur",
            metric_name="laplacian_variance_inverse",
            direction="higher_is_worse",
            possible_threshold=0.4,
            probable_threshold=0.7,
            derivation_data_class="real",
            derived_from_split="development",
            derived_from_source_families=("real-family-a",),
            parent_configuration_digest="1" * 64,
        )
        manifest = freeze_candidate(real_candidate, [real_observation], real_data_execution_authorized=True)
        fixture = build_fixture()
        with self.assertRaises(Stage4CalibrationEvidenceError) as caught:
            build_public_candidate_evidence(manifest, fixture["devReceipt"], fixture["devBinding"])
        self.assertEqual(caught.exception.code, "real_or_heldout_candidate_evidence_forbidden")

    def test_real_reference_receipt_is_rejected(self):
        real_observation = calibration_observation(
            "real-002",
            "real-item-002",
            "real-family-b",
            0.5,
            "possible",
            data_class="real",
            purpose="safety_calibration",
            permission=True,
        )
        real_bundle = ReferenceLabelBundle.from_records("real-reference-v1", [reference_record(real_observation)])
        real_receipt = freeze_reference_label_bundle(real_bundle, accepted_real_reference_bundle=True)
        real_binding = validate_observation_bindings(real_bundle, [binding_row(real_observation)])
        fixture = build_fixture()
        with self.assertRaises(Stage4CalibrationEvidenceError) as caught:
            build_public_candidate_evidence(fixture["candidateManifest"], real_receipt, real_binding)
        self.assertEqual(caught.exception.code, "real_reference_evidence_forbidden")

    def test_tampered_candidate_manifest_digest_is_rejected(self):
        fixture = build_fixture()
        tampered = copy.deepcopy(fixture["candidateManifest"])
        tampered["derivation"]["observationCount"] = 99
        with self.assertRaises(Stage4CalibrationEvidenceError) as caught:
            build_public_candidate_evidence(tampered, fixture["devReceipt"], fixture["devBinding"])
        self.assertEqual(caught.exception.code, "candidate_manifest_digest_mismatch")

    def test_tampered_candidate_public_evidence_is_rejected_by_evaluation(self):
        fixture = build_fixture()
        tampered = copy.deepcopy(fixture["publicCandidate"])
        tampered["derivationSummary"]["observationCount"] = 999
        with self.assertRaises(Stage4CalibrationEvidenceError) as caught:
            build_public_evaluation_evidence(
                tampered, fixture["report"], fixture["heldReceipt"], fixture["heldBinding"]
            )
        self.assertEqual(caught.exception.code, "candidate_public_digest_mismatch")

    def test_evaluation_reference_count_mismatch_fails_closed(self):
        fixture = build_fixture()
        one_held_bundle = ReferenceLabelBundle.from_records(
            "held-one-v1", [reference_record(fixture["held"][0])]
        )
        one_receipt = freeze_reference_label_bundle(one_held_bundle)
        one_binding = validate_observation_bindings(one_held_bundle, [binding_row(fixture["held"][0])])
        with self.assertRaises(Stage4CalibrationEvidenceError) as caught:
            build_public_evaluation_evidence(
                fixture["publicCandidate"], fixture["report"], one_receipt, one_binding
            )
        self.assertEqual(caught.exception.code, "evidence_count_mismatch")


if __name__ == "__main__":
    unittest.main()
