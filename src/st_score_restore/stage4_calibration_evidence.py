"""Public-safe Stage 4 calibration evidence receipts.

This slice is intentionally synthetic-only. It can freeze redacted evidence for
contract tests, but it cannot publish real calibration evidence, authorize real
calibration, or change production thresholds/resource limits.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Mapping

EVIDENCE_CONTRACT_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Stage4CalibrationEvidenceError(ValueError):
    """Stable fail-closed error for invalid public evidence construction."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "rejected",
            "error": {"code": self.code, "message": self.message, "details": self.details},
        }


def _canonical_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _require_mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise Stage4CalibrationEvidenceError("invalid_contract", f"{name} must be an object.")
    return value


def _require_digest(name: str, value: Any) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise Stage4CalibrationEvidenceError("invalid_digest", f"{name} must be a lowercase SHA-256 hex digest.")
    return value


def _digest_value(name: str, value: Any) -> str:
    mapping = _require_mapping(name, value)
    if set(mapping) != {"algorithm", "value"} or mapping.get("algorithm") != "sha256":
        raise Stage4CalibrationEvidenceError("invalid_digest", f"{name} must be a sha256 digest object.")
    return _require_digest(f"{name}.value", mapping.get("value"))


def _require_false(name: str, value: Any) -> None:
    if value is not False:
        raise Stage4CalibrationEvidenceError(
            "unsafe_authorization_claim",
            f"{name} must remain false in the synthetic public-evidence contract.",
        )


def _safe_count(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Stage4CalibrationEvidenceError("invalid_metric", f"{name} must be a non-negative integer.")
    return value


def _safe_rate(name: str, value: Any, *, allow_none: bool = False) -> float | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Stage4CalibrationEvidenceError("invalid_metric", f"{name} must be a finite rate.")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise Stage4CalibrationEvidenceError("invalid_metric", f"{name} must be within [0, 1].")
    return number


def _require_synthetic_candidate_manifest(candidate_manifest: Mapping[str, Any]) -> tuple[str, str, int, int]:
    manifest = _require_mapping("candidate_manifest", candidate_manifest)
    if manifest.get("status") != "candidate_frozen":
        raise Stage4CalibrationEvidenceError("invalid_candidate_manifest", "Candidate manifest is not frozen.")
    candidate_digest = _digest_value("candidateDigest", manifest.get("candidateDigest"))
    manifest_digest = _digest_value("manifestDigest", manifest.get("manifestDigest"))
    without_digest = dict(manifest)
    without_digest.pop("manifestDigest", None)
    if _canonical_digest(without_digest) != manifest_digest:
        raise Stage4CalibrationEvidenceError("candidate_manifest_digest_mismatch", "Candidate manifest digest is invalid.")

    derivation = _require_mapping("candidate_manifest.derivation", manifest.get("derivation"))
    if derivation.get("split") != "development" or derivation.get("dataClass") != "synthetic_test":
        raise Stage4CalibrationEvidenceError(
            "real_or_heldout_candidate_evidence_forbidden",
            "This evidence slice accepts only synthetic development candidate manifests.",
        )
    observation_count = _safe_count("derivation.observationCount", derivation.get("observationCount"))
    source_family_count = _safe_count("derivation.sourceFamilyCount", derivation.get("sourceFamilyCount"))
    if observation_count < 1 or source_family_count < 1:
        raise Stage4CalibrationEvidenceError("invalid_candidate_manifest", "Candidate derivation counts must be positive.")

    assertions = _require_mapping("candidate_manifest.assertions", manifest.get("assertions"))
    for key in (
        "heldOutThresholdTuningUsed",
        "realDataExecutionAuthorized",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
    ):
        _require_false(f"candidate.{key}", assertions.get(key))
    return candidate_digest, manifest_digest, observation_count, source_family_count


def _require_reference_receipt(reference_receipt: Mapping[str, Any]) -> tuple[str, str, int]:
    receipt = _require_mapping("reference_receipt", reference_receipt)
    if receipt.get("status") != "reference_bundle_frozen":
        raise Stage4CalibrationEvidenceError("invalid_reference_receipt", "Reference-label receipt is not frozen.")
    scope = _require_mapping("reference_receipt.scope", receipt.get("scope"))
    if scope.get("dataClass") != "synthetic_test":
        raise Stage4CalibrationEvidenceError(
            "real_reference_evidence_forbidden",
            "This public-evidence slice accepts only synthetic reference-label receipts.",
        )
    if scope.get("split") != "development" or scope.get("purpose") != "synthetic_contract_test":
        raise Stage4CalibrationEvidenceError(
            "reference_scope_mismatch",
            "Candidate evidence requires a synthetic development reference-label bundle.",
        )
    bundle_digest = _digest_value("bundleDigest", receipt.get("bundleDigest"))
    receipt_digest = _digest_value("receiptDigest", receipt.get("receiptDigest"))
    without_digest = dict(receipt)
    without_digest.pop("receiptDigest", None)
    if _canonical_digest(without_digest) != receipt_digest:
        raise Stage4CalibrationEvidenceError("reference_receipt_digest_mismatch", "Reference receipt digest is invalid.")
    label_count = _safe_count("reference_receipt.scope.recordCount", scope.get("recordCount"))
    if label_count < 1:
        raise Stage4CalibrationEvidenceError("invalid_reference_receipt", "Reference receipt must contain labels.")
    assertions = _require_mapping("reference_receipt.assertions", receipt.get("assertions"))
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
        _require_false(f"reference.{key}", assertions.get(key))
    return bundle_digest, receipt_digest, label_count


def _require_binding_receipt(binding_receipt: Mapping[str, Any], reference_bundle_digest: str) -> tuple[str, int]:
    receipt = _require_mapping("binding_receipt", binding_receipt)
    if receipt.get("status") != "bindings_valid":
        raise Stage4CalibrationEvidenceError("invalid_binding_receipt", "Observation bindings are not valid.")
    if _digest_value("binding.bundleDigest", receipt.get("bundleDigest")) != reference_bundle_digest:
        raise Stage4CalibrationEvidenceError("binding_reference_mismatch", "Binding receipt references another label bundle.")
    binding_digest = _digest_value("bindingDigest", receipt.get("bindingDigest"))
    without_digest = dict(receipt)
    without_digest.pop("bindingDigest", None)
    if _canonical_digest(without_digest) != binding_digest:
        raise Stage4CalibrationEvidenceError("binding_digest_mismatch", "Observation binding digest is invalid.")
    observation_count = _safe_count("binding.observationCount", receipt.get("observationCount"))
    if observation_count < 1:
        raise Stage4CalibrationEvidenceError("invalid_binding_receipt", "Binding receipt must contain observations.")
    assertions = _require_mapping("binding.assertions", receipt.get("assertions"))
    if assertions.get("oneToOneObservationBinding") is not True:
        raise Stage4CalibrationEvidenceError("invalid_binding_receipt", "One-to-one observation binding is not asserted.")
    _require_false("binding.predictionFieldsAcceptedAsReferenceEvidence", assertions.get("predictionFieldsAcceptedAsReferenceEvidence"))
    _require_false("binding.heldOutCandidateDerivationAuthorized", assertions.get("heldOutCandidateDerivationAuthorized"))
    return binding_digest, observation_count


def build_public_candidate_evidence(
    candidate_manifest: Mapping[str, Any],
    reference_receipt: Mapping[str, Any],
    binding_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a redacted synthetic-only candidate evidence receipt."""

    candidate_digest, manifest_digest, observation_count, source_family_count = _require_synthetic_candidate_manifest(candidate_manifest)
    reference_bundle_digest, reference_receipt_digest, label_count = _require_reference_receipt(reference_receipt)
    binding_digest, binding_count = _require_binding_receipt(binding_receipt, reference_bundle_digest)
    if observation_count != label_count or observation_count != binding_count:
        raise Stage4CalibrationEvidenceError(
            "evidence_count_mismatch",
            "Candidate, reference-label and observation-binding counts must match exactly.",
        )

    evidence = {
        "schemaVersion": SCHEMA_VERSION,
        "evidenceContractVersion": EVIDENCE_CONTRACT_VERSION,
        "evidenceType": "calibration_candidate_public_receipt",
        "status": "synthetic_candidate_evidence_frozen",
        "candidateDigest": {"algorithm": "sha256", "value": candidate_digest},
        "candidateManifestDigest": {"algorithm": "sha256", "value": manifest_digest},
        "referenceLabelBundleDigest": {"algorithm": "sha256", "value": reference_bundle_digest},
        "referenceReceiptDigest": {"algorithm": "sha256", "value": reference_receipt_digest},
        "observationBindingDigest": {"algorithm": "sha256", "value": binding_digest},
        "derivationSummary": {
            "split": "development",
            "dataClass": "synthetic_test",
            "observationCount": observation_count,
            "sourceFamilyCount": source_family_count,
        },
        "assertions": _public_assertions(),
    }
    evidence["publicEvidenceDigest"] = {"algorithm": "sha256", "value": _canonical_digest(evidence)}
    return evidence


def _require_synthetic_evaluation_report(
    evaluation_report: Mapping[str, Any], candidate_digest: str
) -> tuple[str, str, dict[str, Any]]:
    report = _require_mapping("evaluation_report", evaluation_report)
    if report.get("status") != "evaluated":
        raise Stage4CalibrationEvidenceError("invalid_evaluation_report", "Evaluation report is not completed.")
    if _digest_value("evaluation.candidateDigest", report.get("candidateDigest")) != candidate_digest:
        raise Stage4CalibrationEvidenceError("evaluation_candidate_mismatch", "Evaluation report references another candidate.")
    report_digest = _digest_value("reportDigest", report.get("reportDigest"))
    without_digest = dict(report)
    without_digest.pop("reportDigest", None)
    if _canonical_digest(without_digest) != report_digest:
        raise Stage4CalibrationEvidenceError("evaluation_report_digest_mismatch", "Evaluation report digest is invalid.")

    evaluation = _require_mapping("evaluation", report.get("evaluation"))
    split = evaluation.get("split")
    if split not in {"development", "held_out"}:
        raise Stage4CalibrationEvidenceError("invalid_evaluation_report", "Evaluation split is invalid.")
    if evaluation.get("dataClasses") != ["synthetic_test"]:
        raise Stage4CalibrationEvidenceError(
            "real_evaluation_evidence_forbidden",
            "This public-evidence slice accepts only synthetic evaluation reports.",
        )
    metrics_in = _require_mapping("evaluation.metrics", evaluation.get("metrics"))
    metrics = {
        "observationCount": _safe_count("observationCount", metrics_in.get("observationCount")),
        "assessedCount": _safe_count("assessedCount", metrics_in.get("assessedCount")),
        "notAssessedCount": _safe_count("notAssessedCount", metrics_in.get("notAssessedCount")),
        "coverageRate": _safe_rate("coverageRate", metrics_in.get("coverageRate")),
        "notAssessedRate": _safe_rate("notAssessedRate", metrics_in.get("notAssessedRate")),
        "exactMatchCount": _safe_count("exactMatchCount", metrics_in.get("exactMatchCount")),
        "falseNegativeCount": _safe_count("falseNegativeCount", metrics_in.get("falseNegativeCount")),
        "falsePositiveCount": _safe_count("falsePositiveCount", metrics_in.get("falsePositiveCount")),
        "exactMatchRate": _safe_rate("exactMatchRate", metrics_in.get("exactMatchRate"), allow_none=True),
        "falseNegativeRate": _safe_rate("falseNegativeRate", metrics_in.get("falseNegativeRate"), allow_none=True),
        "falsePositiveRate": _safe_rate("falsePositiveRate", metrics_in.get("falsePositiveRate"), allow_none=True),
        "sourceFamilyLeakageCount": _safe_count("sourceFamilyLeakageCount", metrics_in.get("sourceFamilyLeakageCount")),
    }
    if metrics["sourceFamilyLeakageCount"] != 0:
        raise Stage4CalibrationEvidenceError("source_family_leakage", "Evaluation evidence contains source-family leakage.")
    if metrics["assessedCount"] + metrics["notAssessedCount"] != metrics["observationCount"]:
        raise Stage4CalibrationEvidenceError("invalid_metric", "Evaluation aggregate counts are inconsistent.")
    if metrics["exactMatchCount"] + metrics["falseNegativeCount"] + metrics["falsePositiveCount"] != metrics["assessedCount"]:
        raise Stage4CalibrationEvidenceError("invalid_metric", "Evaluation comparison counts are inconsistent.")

    assertions = _require_mapping("evaluation_report.assertions", report.get("assertions"))
    for key in (
        "heldOutThresholdTuningUsed",
        "evaluationFedBackIntoCandidate",
        "realDataExecutionAuthorized",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "modelTrainingAuthorized",
        "publicationAuthorized",
    ):
        _require_false(f"evaluation.{key}", assertions.get(key))
    return split, report_digest, metrics


def build_public_evaluation_evidence(
    candidate_public_evidence: Mapping[str, Any],
    evaluation_report: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a redacted aggregate evaluation receipt without row-level results."""

    candidate_evidence = _require_mapping("candidate_public_evidence", candidate_public_evidence)
    if candidate_evidence.get("status") != "synthetic_candidate_evidence_frozen":
        raise Stage4CalibrationEvidenceError("invalid_candidate_evidence", "Candidate public evidence is not frozen.")
    candidate_public_digest = _digest_value("candidate.publicEvidenceDigest", candidate_evidence.get("publicEvidenceDigest"))
    candidate_without_digest = dict(candidate_evidence)
    candidate_without_digest.pop("publicEvidenceDigest", None)
    if _canonical_digest(candidate_without_digest) != candidate_public_digest:
        raise Stage4CalibrationEvidenceError("candidate_public_digest_mismatch", "Candidate public evidence digest is invalid.")
    candidate_digest = _digest_value("candidate.candidateDigest", candidate_evidence.get("candidateDigest"))
    split, report_digest, metrics = _require_synthetic_evaluation_report(evaluation_report, candidate_digest)

    evidence = {
        "schemaVersion": SCHEMA_VERSION,
        "evidenceContractVersion": EVIDENCE_CONTRACT_VERSION,
        "evidenceType": "calibration_evaluation_public_receipt",
        "status": "synthetic_evaluation_evidence_frozen",
        "candidateDigest": {"algorithm": "sha256", "value": candidate_digest},
        "candidatePublicEvidenceDigest": {"algorithm": "sha256", "value": candidate_public_digest},
        "evaluationReportDigest": {"algorithm": "sha256", "value": report_digest},
        "evaluationSummary": {"split": split, "dataClass": "synthetic_test", "metrics": metrics},
        "assertions": _public_assertions(),
        "limitations": [
            "Synthetic contract evidence does not establish real-data calibration performance.",
            "No numerical Stage 4 acceptance threshold is authorized by this receipt.",
        ],
    }
    evidence["publicEvidenceDigest"] = {"algorithm": "sha256", "value": _canonical_digest(evidence)}
    return evidence


def _public_assertions() -> dict[str, bool]:
    return {
        "syntheticContractEvidenceOnly": True,
        "rawObservationRowsPublic": False,
        "rowLevelEvaluationResultsPublic": False,
        "reviewerReferencePublic": False,
        "provenanceReferencePublic": False,
        "datasetItemIdentityPublic": False,
        "sourceFamilyIdentityPublic": False,
        "artifactBytesPublic": False,
        "derivativeBytesPublic": False,
        "realReferenceBundleAccepted": False,
        "realDataCalibrationExecuted": False,
        "heldOutThresholdTuningUsed": False,
        "evaluationFedBackIntoCandidate": False,
        "productionThresholdChangeAuthorized": False,
        "productionResourceLimitChangeAuthorized": False,
        "modelTrainingAuthorized": False,
        "publicationAuthorized": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }
