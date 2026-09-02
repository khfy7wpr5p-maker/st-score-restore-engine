from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_reference_labels import (
    REFERENCE_LABEL_CONTRACT_VERSION,
    ReferenceLabelBundle,
    ReferenceLabelRecord,
    Stage4ReferenceLabelError,
    freeze_reference_label_bundle,
    require_candidate_derivation_eligible,
    validate_observation_bindings,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
STAGE3_GRANTS_PATH = ROOT / "evidence/stage3/governance/purpose-grants.v1.json"
STAGE4_START_PATH = ROOT / "evidence/stage4/governance/stage4-entry-start.v1.json"
STAGE4_STATUS_PATH = ROOT / "docs/stage-4-current-status.md"
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"
MODULE_PATH = ROOT / "src/st_score_restore/stage4_reference_labels.py"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def synthetic_record(**overrides) -> ReferenceLabelRecord:
    values = {
        "label_id": "validator-label-001",
        "observation_id": "validator-obs-001",
        "dataset_item_id": "validator.synthetic.item-001",
        "source_family_id": "validator.synthetic.family-a",
        "finding_type": "blur",
        "reference_label": "probable",
        "split": "development",
        "data_class": "synthetic_test",
        "purpose": "synthetic_contract_test",
        "purpose_permission_granted": False,
        "provenance_reference": "synthetic:stage4-reference-validator",
        "reviewer_reference": "reviewer:synthetic-validator",
        "review_method": "synthetic_contract_test",
        "reviewed_on": "2026-09-02",
    }
    values.update(overrides)
    return ReferenceLabelRecord(**values)


def real_record(**overrides) -> ReferenceLabelRecord:
    values = {
        "label_id": "validator-real-label-001",
        "observation_id": "validator-real-obs-001",
        "dataset_item_id": "validator.real.item-001",
        "source_family_id": "validator.real.family-a",
        "finding_type": "glare",
        "reference_label": "possible",
        "split": "development",
        "data_class": "real",
        "purpose": "safety_calibration",
        "purpose_permission_granted": True,
        "provenance_reference": "custody:validator-reference-bundle",
        "reviewer_reference": "expert-reviewer:opaque-validator",
        "review_method": "human_expert_review",
        "reviewed_on": "2026-09-02",
    }
    values.update(overrides)
    return ReferenceLabelRecord(**values)


def rejected_code(callable_obj) -> str | None:
    try:
        callable_obj()
    except Stage4ReferenceLabelError as exc:
        return exc.code
    return None


def main() -> int:
    errors: list[str] = []

    for path in (
        CATALOG_PATH,
        STAGE3_GRANTS_PATH,
        STAGE4_START_PATH,
        STAGE4_STATUS_PATH,
        WORKFLOW_PATH,
        MODULE_PATH,
    ):
        require(path.exists(), f"required Stage 4 reference-label input missing: {path.relative_to(ROOT)}", errors)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    catalog = read_json(CATALOG_PATH)
    stage3_grants = read_json(STAGE3_GRANTS_PATH)
    stage4_start = read_json(STAGE4_START_PATH)
    stage4_status = STAGE4_STATUS_PATH.read_text(encoding="utf-8")
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    module = MODULE_PATH.read_text(encoding="utf-8")

    require(REFERENCE_LABEL_CONTRACT_VERSION == "0.1.0", "Stage 4 reference-label contract version drifted", errors)
    require(
        "no_real_calibration_reference_label_bundle_is_accepted" in stage4_status
        and "Resolved" in stage4_status,
        "Stage 4 status lost the historical reference-bundle blocker/resolution record",
        errors,
    )
    require(
        "realDataCalibrationExecutionAuthorized=true" in stage4_status,
        "Stage 4 status lost the later separate execution authorization",
        errors,
    )
    require(
        "realDataCalibrationExecuted=false" in stage4_status,
        "Stage 4 status falsely claims real calibration execution",
        errors,
    )
    require(
        "private observation metrics" in stage4_status.lower(),
        "Stage 4 status lost the private observation-metric execution dependency",
        errors,
    )

    granted_safety = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(not granted_safety, f"historical catalog was rewritten with later safety_calibration grants: {granted_safety}", errors)
    require(
        (stage3_grants.get("assertions") or {}).get("calibrationAuthorized") is False,
        "Stage 3 purpose grants unexpectedly authorize calibration",
        errors,
    )
    start_scope = stage4_start.get("scope") or {}
    require(
        start_scope.get("realDataCalibrationExecutionAuthorized") is False,
        "Stage 4 historical start decision was rewritten with later real-calibration authorization",
        errors,
    )
    require(
        start_scope.get("productionThresholdChangesAuthorized") is False
        and start_scope.get("productionResourceLimitChangesAuthorized") is False,
        "Stage 4 historical start decision unexpectedly authorizes production calibration changes",
        errors,
    )

    first = synthetic_record()
    second = synthetic_record(
        label_id="validator-label-002",
        observation_id="validator-obs-002",
        dataset_item_id="validator.synthetic.item-002",
        source_family_id="validator.synthetic.family-b",
        finding_type="shadow",
        reference_label="clear",
    )
    bundle_a = ReferenceLabelBundle.from_records("validator.synthetic.bundle.v1", [first, second])
    bundle_b = ReferenceLabelBundle.from_records("validator.synthetic.bundle.v1", [second, first])
    require(bundle_a.digest() == bundle_b.digest(), "reference-label bundle digest depends on record order", errors)

    receipt = freeze_reference_label_bundle(bundle_a)
    assertions = receipt.get("assertions") or {}
    for key in (
        "labelsAutomaticallyGenerated",
        "modelPredictionsUsedAsReferenceLabels",
        "heldOutCandidateDerivationAuthorized",
        "realReferenceBundleAccepted",
        "realDataCalibrationAuthorized",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
    ):
        require(assertions.get(key) is False, f"unsafe reference receipt assertion became true: {key}", errors)

    raw = [
        {
            "observationId": "validator-obs-001",
            "datasetItemId": "validator.synthetic.item-001",
            "sourceFamilyId": "validator.synthetic.family-a",
            "findingType": "blur",
            "split": "development",
            "dataClass": "synthetic_test",
            "purpose": "synthetic_contract_test",
        },
        {
            "observationId": "validator-obs-002",
            "datasetItemId": "validator.synthetic.item-002",
            "sourceFamilyId": "validator.synthetic.family-b",
            "findingType": "shadow",
            "split": "development",
            "dataClass": "synthetic_test",
            "purpose": "synthetic_contract_test",
        },
    ]
    binding_a = validate_observation_bindings(bundle_a, raw)
    binding_b = validate_observation_bindings(bundle_a, [dict(item) for item in raw])
    require(binding_a.get("status") == "bindings_valid", "valid reference bindings were not accepted", errors)
    require(binding_a.get("bindingDigest") == binding_b.get("bindingDigest"), "reference binding digest is not deterministic", errors)
    require(
        (binding_a.get("assertions") or {}).get("predictionFieldsAcceptedAsReferenceEvidence") is False,
        "prediction fields are accepted as reference evidence",
        errors,
    )

    prediction_raw = dict(raw[0])
    prediction_raw["predictedLabel"] = "probable"
    require(
        rejected_code(lambda: validate_observation_bindings(ReferenceLabelBundle.from_records("single", [first]), [prediction_raw]))
        == "invalid_observation_binding",
        "predictedLabel was not rejected from raw reference binding",
        errors,
    )

    require(
        rejected_code(lambda: real_record(purpose_permission_granted=False)) == "purpose_not_granted",
        "real development reference label did not fail closed without safety_calibration grant",
        errors,
    )
    require(
        rejected_code(lambda: real_record(review_method="synthetic_contract_test")) == "real_reference_requires_human_review",
        "real reference label did not require human expert review",
        errors,
    )

    real_bundle = ReferenceLabelBundle.from_records("validator.real.bundle.v1", [real_record()])
    require(
        rejected_code(lambda: freeze_reference_label_bundle(real_bundle)) == "real_reference_bundle_not_accepted",
        "purpose permission alone incorrectly accepted a real reference bundle",
        errors,
    )

    held_out_bundle = ReferenceLabelBundle.from_records(
        "validator.heldout.bundle.v1",
        [
            real_record(
                label_id="validator-held-label-001",
                observation_id="validator-held-obs-001",
                split="held_out",
                purpose="held_out_evaluation",
            )
        ],
    )
    require(
        rejected_code(lambda: require_candidate_derivation_eligible(held_out_bundle, accepted_real_reference_bundle=True))
        == "held_out_reference_derivation_forbidden",
        "held-out reference labels were allowed to derive a candidate",
        errors,
    )

    require("human_expert_review" in module, "reference-label module lost human-review provenance gate", errors)
    require("modelPredictionsUsedAsReferenceLabels" in module, "reference-label module lost model-prediction non-claim", errors)
    require("held_out_reference_derivation_forbidden" in module, "reference-label module lost held-out derivation gate", errors)
    require("purpose_not_granted" in module, "reference-label module lost real-purpose gate", errors)
    require(
        "python tools/validate_stage4_reference_labels.py" in workflow,
        "Repository validation does not run Stage 4 reference-label validator",
        errors,
    )

    stage4_root = ROOT / "evidence/stage4"
    forbidden_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
    if stage4_root.exists():
        forbidden = [
            str(path.relative_to(ROOT))
            for path in stage4_root.rglob("*")
            if path.is_file() and path.suffix.lower() in forbidden_suffixes
        ]
        require(not forbidden, f"Stage 4 evidence contains forbidden artifact/derivative bytes: {forbidden}", errors)

    if errors:
        print("Stage 4 reference-label validation: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Stage 4 reference-label validation: PASS")
    print("- contract version: 0.1.0")
    print("- real labels require purpose grant + human review + separate bundle acceptance")
    print("- historical reference contract/entry evidence remains immutable")
    print("- later exact development execution authorization is separate from reference truth")
    print("- held-out labels cannot derive candidates")
    print("- prediction fields cannot become reference evidence")
    print("- real development execution: authorized separately / not yet executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
