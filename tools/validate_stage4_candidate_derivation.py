from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.stage4_calibration import CalibrationObservation
from st_score_restore.stage4_candidate_derivation import (
    DERIVATION_CONTRACT_VERSION,
    DERIVATION_METHODOLOGY_ID,
    Stage4CandidateDerivationError,
    build_public_derivation_receipt,
    derive_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src/st_score_restore/stage4_candidate_derivation.py"
WORKFLOW_PATH = ROOT / ".github/workflows/repository-validation.yml"
STATUS_PATH = ROOT / "docs/stage-4-current-status.md"


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def obs(oid: str, value: float, label: str, family: str) -> CalibrationObservation:
    return CalibrationObservation(
        observation_id=oid,
        dataset_item_id=f"validator.item.{family}",
        source_family_id=family,
        finding_type="glare",
        metric_name="score",
        raw_value=value,
        reference_label=label,
        split="development",
        data_class="real",
        purpose="safety_calibration",
        purpose_permission_granted=True,
        provenance_reference=f"custody:validator-{oid}",
    )


def ordered() -> list[CalibrationObservation]:
    return [
        obs("c1", 0.10, "clear", "family-a"),
        obs("c2", 0.20, "clear", "family-b"),
        obs("p1", 0.40, "possible", "family-a"),
        obs("p2", 0.50, "possible", "family-b"),
        obs("r1", 0.80, "probable", "family-a"),
        obs("r2", 0.90, "probable", "family-b"),
    ]


def rejected_code(callable_obj) -> str | None:
    try:
        callable_obj()
    except Stage4CandidateDerivationError as exc:
        return exc.code
    return None


def main() -> int:
    failures: list[str] = []
    for path in (MODULE_PATH, WORKFLOW_PATH, STATUS_PATH):
        require(path.exists(), f"required candidate-derivation input missing: {path.relative_to(ROOT)}", failures)
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    module = MODULE_PATH.read_text(encoding="utf-8")
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    status = STATUS_PATH.read_text(encoding="utf-8")

    require(DERIVATION_CONTRACT_VERSION == "0.1.0", "candidate derivation contract version drifted", failures)
    require(DERIVATION_METHODOLOGY_ID == "strict_empirical_midpoint_boundary_v1", "candidate derivation methodology drifted", failures)

    report = derive_candidate(
        ordered(),
        finding_type="glare",
        metric_name="score",
        direction="higher_is_worse",
        parent_configuration_digest="1" * 64,
        real_data_execution_authorized=True,
    )
    require(report.get("status") == "candidate_derived", "strict ordered synthetic contract evidence did not derive a candidate", failures)
    candidate = ((report.get("candidateManifest") or {}).get("candidate") or {})
    require(candidate.get("possibleThreshold") == 0.30000000000000004 or candidate.get("possibleThreshold") == 0.3, "possible midpoint derivation drifted", failures)
    require(candidate.get("probableThreshold") == 0.65, "probable midpoint derivation drifted", failures)
    assertions = report.get("assertions") or {}
    for key in (
        "heldOutThresholdTuningUsed",
        "heldOutEvaluationUsed",
        "notAssessedUsedForThresholds",
        "overlappingSeverityRangesAccepted",
        "missingSeverityClassThresholdInvented",
        "metricAcceptanceTargetPolicyApplied",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(assertions.get(key) is False, f"unsafe candidate derivation assertion became true: {key}", failures)

    sparse = [item for item in ordered() if item.reference_label != "probable"]
    abstained = derive_candidate(
        sparse,
        finding_type="glare",
        metric_name="score",
        direction="higher_is_worse",
        parent_configuration_digest="1" * 64,
        real_data_execution_authorized=True,
    )
    require(abstained.get("status") == "abstained", "missing probable class did not abstain", failures)
    require("insufficient_reference_class_support" in (abstained.get("reasonCodes") or []), "missing class abstention reason drifted", failures)
    require("candidateManifest" not in abstained, "abstained derivation still emitted a candidate", failures)

    overlapping = ordered()
    overlapping[2] = obs("p1", 0.15, "possible", "family-a")
    overlap_report = derive_candidate(
        overlapping,
        finding_type="glare",
        metric_name="score",
        direction="higher_is_worse",
        parent_configuration_digest="1" * 64,
        real_data_execution_authorized=True,
    )
    require(overlap_report.get("status") == "abstained", "overlapping severity ranges did not abstain", failures)
    require("clear_possible_metric_overlap" in (overlap_report.get("reasonCodes") or []), "overlap abstention reason drifted", failures)

    require(
        rejected_code(
            lambda: derive_candidate(
                ordered(),
                finding_type="glare",
                metric_name="score",
                direction="higher_is_worse",
                parent_configuration_digest="1" * 64,
                real_data_execution_authorized=False,
            )
        ) == "real_data_calibration_not_authorized",
        "candidate derivation did not fail closed without execution authorization",
        failures,
    )

    receipt = build_public_derivation_receipt(report)
    rendered = json.dumps(receipt, sort_keys=True)
    require(receipt.get("derivationStatus") == "candidate_derived", "public derivation receipt status drifted", failures)
    for forbidden in ("possibleThreshold", "probableThreshold", "rawValue", "observationId", "validator.item.", "family-a", "custody:"):
        require(forbidden not in rendered, f"public derivation receipt leaked private token: {forbidden}", failures)
    receipt_assertions = receipt.get("assertions") or {}
    require(receipt_assertions.get("candidateThresholdValuesPublic") is False, "candidate threshold values became public", failures)
    require(receipt_assertions.get("metricAcceptanceTargetPolicyApplied") is False, "candidate derivation applied an acceptance target policy", failures)

    require("realDataCalibrationExecuted=false" in status, "Stage 4 status prematurely claims real calibration execution", failures)
    require("private observation metrics" in status, "Stage 4 status lost private observation metric dependency", failures)
    require("missingSeverityClassThresholdInvented" in module, "candidate derivation lost missing-class abstention invariant", failures)
    require("overlappingSeverityRangesAccepted" in module, "candidate derivation lost overlap abstention invariant", failures)
    require("metricAcceptanceTargetPolicyApplied" in module, "candidate derivation lost acceptance-policy non-claim", failures)
    require(
        "python tools/validate_stage4_candidate_derivation.py" in workflow,
        "repository validation does not run Stage 4 candidate derivation validator",
        failures,
    )

    if failures:
        print("Stage 4 candidate derivation methodology validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 candidate derivation methodology validation: PASS")
    print("- methodology: strict_empirical_midpoint_boundary_v1")
    print("- development-only / real execution authorization required")
    print("- all clear/possible/probable classes + two source families required")
    print("- missing class or overlapping metric ranges: abstain")
    print("- held-out tuning/evaluation: forbidden")
    print("- public receipt redacts rows, identities, raw metrics and candidate threshold values")
    print("- metric acceptance target policy / production changes / Stage 4 PASS / Stage 5: not authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
