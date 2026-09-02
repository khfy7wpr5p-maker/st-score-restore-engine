"""Abstain-first Stage 4 development candidate-derivation methodology.

This module defines deterministic mechanics for deriving a threshold candidate
from already-authorized development observations. It does not obtain private
metrics, authorize real-data execution, use held-out evidence, set metric
acceptance targets, change production thresholds/resources, train a model,
publish private rows, grant Stage 4 PASS, or open Stage 5.

A full two-threshold candidate is produced only when development evidence has
all three assessed reference classes (clear / possible / probable), at least two
source families, and strictly ordered non-overlapping metric ranges. Otherwise
this methodology abstains rather than inventing a threshold.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .stage4_calibration import (
    CalibrationObservation,
    Stage4CalibrationError,
    ThresholdCandidate,
    freeze_candidate,
)

DERIVATION_CONTRACT_VERSION = "0.1.0"
DERIVATION_METHODOLOGY_ID = "strict_empirical_midpoint_boundary_v1"
SCHEMA_VERSION = "1.0.0"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class Stage4CandidateDerivationError(ValueError):
    """Stable fail-closed rejection for invalid candidate derivation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise Stage4CandidateDerivationError(code, message)


def _digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _coerce(values: Iterable[CalibrationObservation | Mapping[str, Any]]) -> list[CalibrationObservation]:
    observations: list[CalibrationObservation] = []
    for value in values:
        try:
            observations.append(value if isinstance(value, CalibrationObservation) else CalibrationObservation.from_mapping(value))
        except Stage4CalibrationError as exc:
            raise Stage4CandidateDerivationError(exc.code, exc.message) from exc
    _require(bool(observations), "insufficient_observations", "candidate derivation requires observations")
    return observations


def _midpoint(a: float, b: float) -> float:
    return a + (b - a) / 2.0


def _abstention_report(
    *,
    finding_type: str,
    metric_name: str,
    direction: str,
    observations: list[CalibrationObservation],
    reason_codes: list[str],
) -> dict[str, Any]:
    counts = {label: 0 for label in ("clear", "possible", "probable", "not_assessed")}
    for observation in observations:
        counts[observation.reference_label] += 1
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "contractVersion": DERIVATION_CONTRACT_VERSION,
        "methodologyId": DERIVATION_METHODOLOGY_ID,
        "status": "abstained",
        "findingType": finding_type,
        "metricName": metric_name,
        "direction": direction,
        "derivationSummary": {
            "split": "development",
            "dataClass": "real",
            "observationCount": len(observations),
            "sourceFamilyCount": len({item.source_family_id for item in observations}),
            "referenceClassCounts": counts,
        },
        "reasonCodes": sorted(set(reason_codes)),
        "assertions": _assertions(),
    }
    report["reportDigest"] = {"algorithm": "sha256", "value": _digest(report)}
    return report


def _assertions() -> dict[str, bool]:
    return {
        "developmentEvidenceOnly": True,
        "heldOutThresholdTuningUsed": False,
        "heldOutEvaluationUsed": False,
        "notAssessedUsedForThresholds": False,
        "overlappingSeverityRangesAccepted": False,
        "missingSeverityClassThresholdInvented": False,
        "metricAcceptanceTargetPolicyApplied": False,
        "productionThresholdChangeAuthorized": False,
        "productionResourceLimitChangeAuthorized": False,
        "modelTrainingAuthorized": False,
        "publicationAuthorized": False,
        "stage4ExitPass": False,
        "stage5EntryAuthorized": False,
    }


def derive_candidate(
    observations: Iterable[CalibrationObservation | Mapping[str, Any]],
    *,
    finding_type: str,
    metric_name: str,
    direction: str,
    parent_configuration_digest: str,
    real_data_execution_authorized: bool = False,
) -> dict[str, Any]:
    """Derive one full two-boundary candidate or abstain deterministically.

    Higher-is-worse evidence must satisfy clear < possible < probable with
    strictly non-overlapping observed ranges. Lower-is-worse evidence must
    satisfy clear > possible > probable. Boundaries are the midpoints between
    the nearest adjacent observed class edges. Missing classes or overlap cause
    abstention; held-out evidence is rejected.
    """

    resolved = _coerce(observations)
    _require(real_data_execution_authorized is True, "real_data_calibration_not_authorized", "candidate derivation requires accepted real development execution authorization")
    _require(isinstance(parent_configuration_digest, str) and bool(_SHA256_RE.fullmatch(parent_configuration_digest)), "invalid_parent_configuration_digest", "parent configuration digest must be lowercase SHA-256")
    _require(direction in {"higher_is_worse", "lower_is_worse"}, "invalid_direction", "direction must be higher_is_worse or lower_is_worse")

    for observation in resolved:
        _require(observation.split == "development", "held_out_tuning_forbidden", "held-out observations cannot derive candidates")
        _require(observation.data_class == "real", "invalid_data_class", "real development candidate derivation requires real observations")
        _require(observation.purpose == "safety_calibration" and observation.purpose_permission_granted, "purpose_not_granted", "candidate derivation requires granted safety_calibration purpose")
        _require(observation.finding_type == finding_type, "candidate_observation_mismatch", "all observations must match the requested finding")
        _require(observation.metric_name == metric_name, "candidate_observation_mismatch", "all observations must match the requested metric")

    source_families = sorted({item.source_family_id for item in resolved})
    reasons: list[str] = []
    if len(source_families) < 2:
        reasons.append("insufficient_source_family_support")

    by_label: dict[str, list[float]] = {"clear": [], "possible": [], "probable": [], "not_assessed": []}
    for observation in resolved:
        by_label[observation.reference_label].append(float(observation.raw_value))

    if by_label["not_assessed"]:
        reasons.append("not_assessed_reference_present")
    if any(not by_label[label] for label in ("clear", "possible", "probable")):
        reasons.append("insufficient_reference_class_support")

    if reasons:
        return _abstention_report(
            finding_type=finding_type,
            metric_name=metric_name,
            direction=direction,
            observations=resolved,
            reason_codes=reasons,
        )

    clear_values = by_label["clear"]
    possible_values = by_label["possible"]
    probable_values = by_label["probable"]

    if direction == "higher_is_worse":
        clear_edge = max(clear_values)
        possible_low = min(possible_values)
        possible_high = max(possible_values)
        probable_edge = min(probable_values)
        if not clear_edge < possible_low:
            reasons.append("clear_possible_metric_overlap")
        if not possible_high < probable_edge:
            reasons.append("possible_probable_metric_overlap")
        possible_threshold = _midpoint(clear_edge, possible_low)
        probable_threshold = _midpoint(possible_high, probable_edge)
    else:
        clear_edge = min(clear_values)
        possible_high = max(possible_values)
        possible_low = min(possible_values)
        probable_edge = max(probable_values)
        if not clear_edge > possible_high:
            reasons.append("clear_possible_metric_overlap")
        if not possible_low > probable_edge:
            reasons.append("possible_probable_metric_overlap")
        possible_threshold = _midpoint(clear_edge, possible_high)
        probable_threshold = _midpoint(possible_low, probable_edge)

    if reasons:
        return _abstention_report(
            finding_type=finding_type,
            metric_name=metric_name,
            direction=direction,
            observations=resolved,
            reason_codes=reasons,
        )

    candidate = ThresholdCandidate(
        candidate_id=f"stage4.candidate.{finding_type}.{DERIVATION_METHODOLOGY_ID}",
        finding_type=finding_type,
        metric_name=metric_name,
        direction=direction,
        possible_threshold=possible_threshold,
        probable_threshold=probable_threshold,
        derivation_data_class="real",
        derived_from_split="development",
        derived_from_source_families=tuple(source_families),
        parent_configuration_digest=parent_configuration_digest,
    )
    try:
        manifest = freeze_candidate(candidate, resolved, real_data_execution_authorized=True)
    except Stage4CalibrationError as exc:
        raise Stage4CandidateDerivationError(exc.code, exc.message) from exc

    counts = {label: len(by_label[label]) for label in ("clear", "possible", "probable", "not_assessed")}
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "contractVersion": DERIVATION_CONTRACT_VERSION,
        "methodologyId": DERIVATION_METHODOLOGY_ID,
        "status": "candidate_derived",
        "findingType": finding_type,
        "metricName": metric_name,
        "direction": direction,
        "candidateManifest": manifest,
        "derivationSummary": {
            "split": "development",
            "dataClass": "real",
            "observationCount": len(resolved),
            "sourceFamilyCount": len(source_families),
            "referenceClassCounts": counts,
        },
        "reasonCodes": [],
        "assertions": _assertions(),
    }
    report["reportDigest"] = {"algorithm": "sha256", "value": _digest(report)}
    return report


def build_public_derivation_receipt(report: Mapping[str, Any]) -> dict[str, Any]:
    """Redact a private derivation report to digest/count/status evidence only."""

    _require(isinstance(report, Mapping), "invalid_derivation_report", "derivation report must be an object")
    report_value = dict(report)
    _require(report_value.get("contractVersion") == DERIVATION_CONTRACT_VERSION, "invalid_derivation_report", "derivation contract version mismatch")
    _require(report_value.get("methodologyId") == DERIVATION_METHODOLOGY_ID, "invalid_derivation_report", "derivation methodology mismatch")
    status = report_value.get("status")
    _require(status in {"candidate_derived", "abstained"}, "invalid_derivation_report", "derivation status is invalid")
    digest_obj = report_value.get("reportDigest")
    _require(isinstance(digest_obj, Mapping) and digest_obj.get("algorithm") == "sha256" and isinstance(digest_obj.get("value"), str), "invalid_derivation_report", "derivation report digest missing")
    without_digest = dict(report_value)
    without_digest.pop("reportDigest", None)
    _require(_digest(without_digest) == digest_obj.get("value"), "derivation_report_digest_mismatch", "derivation report digest is invalid")

    summary = report_value.get("derivationSummary")
    _require(isinstance(summary, Mapping), "invalid_derivation_report", "derivation summary missing")
    receipt: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "contractVersion": DERIVATION_CONTRACT_VERSION,
        "methodologyId": DERIVATION_METHODOLOGY_ID,
        "status": "development_candidate_derivation_public_receipt",
        "derivationStatus": status,
        "findingType": report_value.get("findingType"),
        "metricName": report_value.get("metricName"),
        "direction": report_value.get("direction"),
        "privateDerivationReportDigest": {"algorithm": "sha256", "value": digest_obj.get("value")},
        "derivationSummary": {
            "split": "development",
            "dataClass": "real",
            "observationCount": summary.get("observationCount"),
            "sourceFamilyCount": summary.get("sourceFamilyCount"),
            "referenceClassCounts": dict(summary.get("referenceClassCounts") or {}),
        },
        "reasonCodes": list(report_value.get("reasonCodes") or []),
        "assertions": {
            "rawObservationRowsPublic": False,
            "rawMetricValuesPublic": False,
            "datasetItemIdentityPublic": False,
            "sourceFamilyIdentityPublic": False,
            "provenanceReferencePublic": False,
            "candidateThresholdValuesPublic": False,
            "heldOutThresholdTuningUsed": False,
            "heldOutEvaluationUsed": False,
            "metricAcceptanceTargetPolicyApplied": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
            "stage4ExitPass": False,
            "stage5EntryAuthorized": False,
        },
    }
    if status == "candidate_derived":
        manifest = report_value.get("candidateManifest")
        _require(isinstance(manifest, Mapping), "invalid_derivation_report", "derived report is missing candidate manifest")
        candidate_digest = manifest.get("candidateDigest")
        manifest_digest = manifest.get("manifestDigest")
        _require(isinstance(candidate_digest, Mapping) and candidate_digest.get("algorithm") == "sha256", "invalid_derivation_report", "candidate digest missing")
        _require(isinstance(manifest_digest, Mapping) and manifest_digest.get("algorithm") == "sha256", "invalid_derivation_report", "candidate manifest digest missing")
        receipt["candidateDigest"] = dict(candidate_digest)
        receipt["candidateManifestDigest"] = dict(manifest_digest)
    receipt["publicReceiptDigest"] = {"algorithm": "sha256", "value": _digest(receipt)}
    return receipt


__all__ = [
    "DERIVATION_CONTRACT_VERSION",
    "DERIVATION_METHODOLOGY_ID",
    "Stage4CandidateDerivationError",
    "build_public_derivation_receipt",
    "derive_candidate",
]
