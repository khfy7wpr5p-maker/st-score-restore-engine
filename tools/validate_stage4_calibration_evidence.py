from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_calibration import CalibrationObservation, ThresholdCandidate, evaluate_candidate, freeze_candidate
from st_score_restore.stage4_calibration_evidence import (
    EVIDENCE_CONTRACT_VERSION,
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

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs/stage-4-current-status.md"
CATALOG = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
WORKFLOW = ROOT / ".github/workflows/repository-validation.yml"
MODULE = ROOT / "src/st_score_restore/stage4_calibration_evidence.py"


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def obs(oid: str, item: str, family: str, value: float, label: str, split: str) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=oid,
        dataset_item_id=item,
        source_family_id=family,
        finding_type="blur",
        metric_name="laplacian_variance_inverse",
        raw_value=value,
        reference_label=label,
        split=split,
        data_class="synthetic_test",
        purpose="synthetic_contract_test",
        purpose_permission_granted=False,
        provenance_reference=f"custody:metric-{oid}",
    )


def label_record(item: CalibrationObservation) -> ReferenceLabelRecord:
    return ReferenceLabelRecord(
        label_id=f"label-{item.observation_id}",
        observation_id=item.observation_id,
        dataset_item_id=item.dataset_item_id,
        source_family_id=item.source_family_id,
        finding_type=item.finding_type,
        reference_label=item.reference_label,
        split=item.split,
        data_class=item.data_class,
        purpose=item.purpose,
        purpose_permission_granted=False,
        provenance_reference=f"custody:reference-{item.observation_id}",
        reviewer_reference=f"reviewer:validator-{item.observation_id}",
        review_method="synthetic_contract_test",
        reviewed_on="2026-09-02",
    )


def binding(item: CalibrationObservation) -> dict:
    return {
        "observationId": item.observation_id,
        "datasetItemId": item.dataset_item_id,
        "sourceFamilyId": item.source_family_id,
        "findingType": item.finding_type,
        "split": item.split,
        "dataClass": item.data_class,
        "purpose": item.purpose,
    }


def build_bundle(bundle_id: str, observations: list[CalibrationObservation]):
    bundle = ReferenceLabelBundle.from_records(bundle_id, [label_record(item) for item in observations])
    return (
        freeze_reference_label_bundle(bundle),
        validate_observation_bindings(bundle, [binding(item) for item in observations]),
    )


def rejected_code(callable_obj) -> str | None:
    try:
        callable_obj()
    except Stage4CalibrationEvidenceError as exc:
        return exc.code
    return None


def main() -> int:
    failures: list[str] = []
    for path in (STATUS, CATALOG, WORKFLOW, MODULE):
        require(path.exists(), f"required input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    status = STATUS.read_text(encoding="utf-8")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")
    module = MODULE.read_text(encoding="utf-8")

    require(EVIDENCE_CONTRACT_VERSION == "0.1.0", "calibration evidence contract version drifted", failures)
    # This validator owns the historical synthetic/public-evidence contract. A
    # later, separate exact-scope real-development execution authorization must
    # not rewrite this synthetic contract or imply that real execution occurred.
    require(
        "realDataCalibrationExecutionAuthorized=true" in status,
        "Stage 4 status lost the later separate development execution authorization",
        failures,
    )
    require(
        "realDataCalibrationExecuted=false" in status,
        "Stage 4 status falsely claims real calibration execution",
        failures,
    )
    require(
        "no_real_calibration_reference_label_bundle_is_accepted" in status
        and "Resolved" in status,
        "Stage 4 status lost the historical reference-bundle blocker/resolution record",
        failures,
    )
    require(
        "private observation metrics" in status.lower(),
        "Stage 4 status lost the private observation-metric execution dependency",
        failures,
    )
    granted = [
        item.get("datasetItemId")
        for item in catalog.get("items", [])
        if ((item.get("permissions") or {}).get("safety_calibration") or {}).get("status") == "granted"
    ]
    require(not granted, f"historical Stage 1 catalog was rewritten with later safety_calibration grants: {granted}", failures)

    dev = [
        obs("dev-a", "dev-item-a", "dev-family-a", 0.2, "clear", "development"),
        obs("dev-b", "dev-item-b", "dev-family-b", 0.8, "probable", "development"),
    ]
    candidate = ThresholdCandidate(
        candidate_id="validator-candidate-v1",
        finding_type="blur",
        metric_name="laplacian_variance_inverse",
        direction="higher_is_worse",
        possible_threshold=0.4,
        probable_threshold=0.7,
        derivation_data_class="synthetic_test",
        derived_from_split="development",
        derived_from_source_families=("dev-family-a", "dev-family-b"),
        parent_configuration_digest="0" * 64,
    )
    candidate_manifest = freeze_candidate(candidate, dev)
    dev_receipt, dev_binding = build_bundle("validator-dev-labels-v1", dev)
    public_candidate = build_public_candidate_evidence(candidate_manifest, dev_receipt, dev_binding)

    held = [
        obs("held-a", "held-item-a", "held-family-a", 0.5, "possible", "held_out"),
        obs("held-b", "held-item-b", "held-family-b", 0.9, "probable", "held_out"),
    ]
    held_receipt, held_binding = build_bundle("validator-held-labels-v1", held)
    evaluation_report = evaluate_candidate(candidate, held, evaluation_split="held_out")
    public_evaluation = build_public_evaluation_evidence(
        public_candidate, evaluation_report, held_receipt, held_binding
    )

    require(public_candidate.get("status") == "synthetic_candidate_evidence_frozen", "candidate public evidence not frozen", failures)
    require(public_evaluation.get("status") == "synthetic_evaluation_evidence_frozen", "evaluation public evidence not frozen", failures)
    require(
        public_evaluation.get("evaluationSummary", {}).get("split") == "held_out",
        "held-out evaluation split was not retained",
        failures,
    )
    require(
        "results" not in public_evaluation.get("evaluationSummary", {}),
        "row-level results leaked into public evaluation summary",
        failures,
    )
    require(
        public_evaluation.get("evaluationSummary", {}).get("metrics", {}).get("sourceFamilyLeakageCount") == 0,
        "source-family leakage present in public evaluation evidence",
        failures,
    )

    for receipt_name, receipt in (("candidate", public_candidate), ("evaluation", public_evaluation)):
        assertions = receipt.get("assertions", {})
        require(assertions.get("syntheticContractEvidenceOnly") is True, f"{receipt_name} lost synthetic-only assertion", failures)
        for key in (
            "rawObservationRowsPublic",
            "rowLevelEvaluationResultsPublic",
            "reviewerReferencePublic",
            "provenanceReferencePublic",
            "datasetItemIdentityPublic",
            "sourceFamilyIdentityPublic",
            "artifactBytesPublic",
            "derivativeBytesPublic",
            "realReferenceBundleAccepted",
            "realDataCalibrationExecuted",
            "heldOutThresholdTuningUsed",
            "evaluationFedBackIntoCandidate",
            "productionThresholdChangeAuthorized",
            "productionResourceLimitChangeAuthorized",
            "modelTrainingAuthorized",
            "publicationAuthorized",
            "stage4ExitPass",
            "stage5EntryAuthorized",
        ):
            require(assertions.get(key) is False, f"unsafe public evidence assertion became true: {receipt_name}.{key}", failures)

    rendered = json.dumps({"candidate": public_candidate, "evaluation": public_evaluation}, sort_keys=True)
    for forbidden in (
        "dev-item-a",
        "dev-family-a",
        "held-item-a",
        "held-family-a",
        "reviewer:validator-dev-a",
        "custody:reference-dev-a",
        "custody:metric-dev-a",
    ):
        require(forbidden not in rendered, f"private identity leaked into public evidence: {forbidden}", failures)

    tampered_candidate = json.loads(json.dumps(public_candidate))
    tampered_candidate["derivationSummary"]["observationCount"] = 99
    require(
        rejected_code(
            lambda: build_public_evaluation_evidence(
                tampered_candidate, evaluation_report, held_receipt, held_binding
            )
        )
        == "candidate_public_digest_mismatch",
        "tampered candidate public evidence was not rejected",
        failures,
    )

    require("syntheticContractEvidenceOnly" in module, "module lost synthetic-only public assertion", failures)
    require("realDataCalibrationExecuted" in module, "module lost real-calibration non-claim", failures)
    require("rowLevelEvaluationResultsPublic" in module, "module lost row-level redaction assertion", failures)
    require("stage5EntryAuthorized" in module, "module lost Stage 5 non-authorization assertion", failures)
    require(
        "python tools/validate_stage4_calibration_evidence.py" in workflow,
        "Repository validation does not run Stage 4 calibration evidence validator",
        failures,
    )

    if failures:
        print("Stage 4 calibration evidence validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 calibration evidence validation: PASS")
    print("- public evidence contract version: 0.1.0")
    print("- candidate + held-out evaluation evidence in this contract remain synthetic-only")
    print("- public receipts expose digests and aggregates, not row/private identity data")
    print("- later real development execution authorization is separate; actual execution remains false")
    print("- production changes / Stage 4 exit / Stage 5 entry remain false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
