from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from st_score_restore.stage4_calibration import (
    CalibrationObservation,
    FRAMEWORK_VERSION,
    Stage4CalibrationError,
    ThresholdCandidate,
    evaluate_candidate,
    freeze_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "evidence/stage4/governance/stage4-entry-start.v1.json"
STAGE3_ACCEPTANCE_PATH = ROOT / "evidence/stage3/corpus/stage3-exit-acceptance.v1.json"
CATALOG_PATH = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
STAGE3_GRANTS_PATH = ROOT / "evidence/stage3/governance/purpose-grants.v1.json"
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"

EXPECTED_DECISION_DIGEST = "013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8"
EXPECTED_STAGE3_ACCEPTANCE_DIGEST = "e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90"
EXPECTED_STAGE3_ACCEPTANCE_MAIN = "c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0"
EXPECTED_PRODUCTION_TRUTH_MAIN = "2aac96faffcf46e71c41cfb2a37b36597e95e664"
EXPECTED_PRODUCTION_TRUTH_RUN_ID = 33655490406
EXPECTED_PRODUCTION_TRUTH_RUN_NUMBER = 257


def canonical_digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def synthetic_observation(
    observation_id: str,
    family: str,
    value: float,
    label: str,
    *,
    split: str = "development",
) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=observation_id,
        dataset_item_id=f"synthetic.{observation_id}",
        source_family_id=family,
        finding_type="glare",
        metric_name="score",
        raw_value=value,
        reference_label=label,
        split=split,
        data_class="synthetic_test",
        purpose="synthetic_contract_test",
        purpose_permission_granted=False,
        provenance_reference=f"synthetic:{observation_id}",
    )


def main() -> int:
    errors: list[str] = []

    for path in (
        DECISION_PATH,
        STAGE3_ACCEPTANCE_PATH,
        CATALOG_PATH,
        STAGE3_GRANTS_PATH,
        WORKFLOW_PATH,
    ):
        require(path.exists(), f"required Stage 4 validation input missing: {path.relative_to(ROOT)}", errors)
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1

    decision = read_json(DECISION_PATH)
    stage3_acceptance = read_json(STAGE3_ACCEPTANCE_PATH)
    catalog = read_json(CATALOG_PATH)
    stage3_grants = read_json(STAGE3_GRANTS_PATH)
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    embedded_digest = ((decision.get("decisionDigest") or {}).get("value"))
    digest_payload = dict(decision)
    digest_payload.pop("decisionDigest", None)
    actual_decision_digest = canonical_digest(digest_payload)
    require(embedded_digest == EXPECTED_DECISION_DIGEST, "Stage 4 decision embedded digest drifted", errors)
    require(actual_decision_digest == EXPECTED_DECISION_DIGEST, "Stage 4 decision canonical digest drifted", errors)

    require(stage3_acceptance.get("decision") == "PASS", "Stage 3 final acceptance is not PASS", errors)
    require(stage3_acceptance.get("stage3ExitPass") is True, "Stage 3 exit PASS binding missing", errors)
    require(stage3_acceptance.get("stage4EntryEligible") is True, "Stage 3 did not authorize Stage 4 entry eligibility", errors)
    require(stage3_acceptance.get("stage4Started") is False, "Historical Stage 3 acceptance must retain stage4Started=false", errors)
    require(canonical_digest(stage3_acceptance) == EXPECTED_STAGE3_ACCEPTANCE_DIGEST, "Stage 3 final acceptance digest drifted", errors)

    require(decision.get("decision") == "APPROVE_FRAMEWORK_START", "Stage 4 entry decision changed", errors)
    require(decision.get("trackingIssue") == 104, "Stage 4 tracking issue binding changed", errors)
    stage3_binding = decision.get("stage3Binding") or {}
    require(stage3_binding.get("finalAcceptanceMainSha") == EXPECTED_STAGE3_ACCEPTANCE_MAIN, "Stage 4 lost Stage 3 acceptance main binding", errors)
    require(stage3_binding.get("finalAcceptanceCanonicalSha256") == EXPECTED_STAGE3_ACCEPTANCE_DIGEST, "Stage 4 lost Stage 3 acceptance digest binding", errors)
    require(stage3_binding.get("productionTruthMainSha") == EXPECTED_PRODUCTION_TRUTH_MAIN, "Stage 4 lost production-truth main binding", errors)
    require(stage3_binding.get("productionTruthPostMergeCiRunId") == EXPECTED_PRODUCTION_TRUTH_RUN_ID, "Stage 4 lost Run #257 id binding", errors)
    require(stage3_binding.get("productionTruthPostMergeCiRunNumber") == EXPECTED_PRODUCTION_TRUTH_RUN_NUMBER, "Stage 4 lost Run #257 number binding", errors)
    require(stage3_binding.get("python311") == "success" and stage3_binding.get("python312") == "success", "Stage 4 entry is not bound to successful Python 3.11/3.12 production CI", errors)

    scope = decision.get("scope") or {}
    require(scope.get("frameworkImplementationAuthorized") is True, "Stage 4 framework implementation is not authorized", errors)
    require(scope.get("syntheticContractTestingAuthorized") is True, "Stage 4 synthetic contract testing is not authorized", errors)
    for key in (
        "realDataCalibrationExecutionAuthorized",
        "productionThresholdChangesAuthorized",
        "productionResourceLimitChangesAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
    ):
        require(scope.get(key) is False, f"Stage 4 unsafe scope flag became authorized: {key}", errors)

    policy = decision.get("dataUsePolicy") or {}
    require(policy.get("realDevelopmentRequiredPurpose") == "safety_calibration", "Stage 4 development purpose drifted", errors)
    require(policy.get("realHeldOutRequiredPurpose") == "held_out_evaluation", "Stage 4 held-out purpose drifted", errors)
    require(policy.get("currentSafetyCalibrationPermissionState") == "none_granted", "Stage 4 permission-state claim drifted", errors)
    require(policy.get("generalProjectApprovalIsDatasetPurposeGrant") is False, "Stage 4 inferred dataset permission from general approval", errors)
    require(policy.get("heldOutMaySelectOrTuneThresholds") is False, "Stage 4 allowed held-out threshold tuning", errors)
    require(policy.get("heldOutMaySelectOrTuneResourceLimits") is False, "Stage 4 allowed held-out resource-limit tuning", errors)
    require(policy.get("realCorpusBytesInOrdinaryGit") is False, "Stage 4 claims real corpus bytes in ordinary Git", errors)

    granted_safety_calibration = []
    for item in catalog.get("items", []):
        permission = ((item.get("permissions") or {}).get("safety_calibration") or {})
        if permission.get("status") == "granted":
            granted_safety_calibration.append(item.get("datasetItemId"))
    require(not granted_safety_calibration, f"Catalog now has safety_calibration grants but Stage 4 decision still says none: {granted_safety_calibration}", errors)

    grant_assertions = stage3_grants.get("assertions") or {}
    require(grant_assertions.get("calibrationAuthorized") is False, "Stage 3 purpose overlay unexpectedly grants calibration", errors)
    require(all(grant.get("purpose") == "pdf_pipeline_evaluation" for grant in stage3_grants.get("grants", [])), "Stage 3 purpose overlay scope drifted", errors)

    anti_leakage = decision.get("antiLeakageRules") or {}
    require(anti_leakage.get("candidateDerivationSplit") == "development_only", "Stage 4 derivation split is not development-only", errors)
    require(anti_leakage.get("heldOutTuningForbidden") is True, "Stage 4 held-out tuning protection disabled", errors)
    require(anti_leakage.get("crossSplitSourceFamilyOverlapForbidden") is True, "Stage 4 source-family leakage protection disabled", errors)
    require(anti_leakage.get("thresholdProposalFromHeldOutForbidden") is True, "Stage 4 held-out threshold proposal protection disabled", errors)
    require(anti_leakage.get("resourceLimitProposalFromHeldOutForbidden") is True, "Stage 4 held-out resource-limit proposal protection disabled", errors)

    claims = decision.get("claims") or {}
    require(claims.get("stage4EntryEligible") is True, "Stage 4 entry eligibility claim missing", errors)
    require(claims.get("frameworkStartAuthorized") is True, "Stage 4 framework start authorization claim missing", errors)
    for key in (
        "stage4Started",
        "calibrationAuthorized",
        "realDataCalibrationExecuted",
        "thresholdsCalibrated",
        "resourceLimitsCalibrated",
        "stage4ExitPass",
        "stage5EntryEligible",
    ):
        require(claims.get(key) is False, f"Stage 4 candidate prematurely claims {key}", errors)

    require(FRAMEWORK_VERSION == "0.1.0", "Stage 4 framework version drifted", errors)
    candidate = ThresholdCandidate(
        candidate_id="validator.glare.synthetic.v1",
        finding_type="glare",
        metric_name="score",
        direction="higher_is_worse",
        possible_threshold=0.10,
        probable_threshold=0.20,
        derivation_data_class="synthetic_test",
        derived_from_split="development",
        derived_from_source_families=("validator.dev.family",),
        parent_configuration_digest="0" * 64,
    )
    development = [
        synthetic_observation("validator-dev-1", "validator.dev.family", 0.05, "clear"),
        synthetic_observation("validator-dev-2", "validator.dev.family", 0.15, "possible"),
    ]
    frozen = freeze_candidate(candidate, development)
    require(frozen["assertions"]["heldOutThresholdTuningUsed"] is False, "Stage 4 freeze used held-out tuning", errors)
    require(frozen["assertions"]["productionThresholdChangeAuthorized"] is False, "Stage 4 freeze authorized production thresholds", errors)

    held_out = [
        synthetic_observation("validator-heldout-1", "validator.heldout.family", 0.25, "probable", split="held_out")
    ]
    report = evaluate_candidate(candidate, held_out, evaluation_split="held_out")
    require(report["assertions"]["heldOutThresholdTuningUsed"] is False, "Stage 4 evaluation used held-out tuning", errors)
    require(report["assertions"]["evaluationFedBackIntoCandidate"] is False, "Stage 4 evaluation fed held-out data into candidate", errors)
    require(report["evaluation"]["metrics"]["sourceFamilyLeakageCount"] == 0, "Stage 4 synthetic validator found source-family leakage", errors)

    real_without_grant_rejected = False
    try:
        CalibrationObservation(
            observation_id="validator-real-no-grant",
            dataset_item_id="dataset.validator.real",
            source_family_id="family.validator.real",
            finding_type="glare",
            metric_name="score",
            raw_value=0.20,
            reference_label="probable",
            split="development",
            data_class="real",
            purpose="safety_calibration",
            purpose_permission_granted=False,
            provenance_reference="evidence:validator-real-no-grant",
        )
    except Stage4CalibrationError as exc:
        real_without_grant_rejected = exc.code == "purpose_not_granted"
    require(real_without_grant_rejected, "Stage 4 framework did not fail closed on missing real-data purpose grant", errors)

    require("python tools/validate_stage4_entry_start.py" in workflow, "Repository validation does not run Stage 4 entry/start validator", errors)

    stage4_evidence_root = ROOT / "evidence/stage4"
    forbidden_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
    if stage4_evidence_root.exists():
        forbidden = [
            str(path.relative_to(ROOT))
            for path in stage4_evidence_root.rglob("*")
            if path.is_file() and path.suffix.lower() in forbidden_suffixes
        ]
        require(not forbidden, f"Stage 4 ordinary Git contains forbidden artifact/derivative bytes: {forbidden}", errors)

    if errors:
        print("Stage 4 entry/start validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Stage 4 entry/start validation: PASS")
    print(f"- decision digest: {EXPECTED_DECISION_DIGEST}")
    print("- framework start authorized; real-data calibration remains blocked")
    print("- held-out tuning and source-family leakage protections active")
    return 0


if __name__ == "__main__":
    sys.exit(main())
