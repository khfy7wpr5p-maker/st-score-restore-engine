"""Deterministic Stage 4 safety-calibration framework.

This module does not grant dataset permission and does not change production
thresholds. Real-data execution stays fail-closed until a separate purpose-bound
runner explicitly authorizes it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

FRAMEWORK_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"

TUNABLE_FINDINGS = frozenset(
    {
        "skew",
        "blur",
        "glare",
        "shadow",
        "uneven_lighting",
        "noise",
        "compression",
    }
)
REFERENCE_LABELS = ("clear", "possible", "probable", "not_assessed")
LABEL_RANK = {"clear": 0, "possible": 1, "probable": 2}
DIRECTIONS = frozenset({"higher_is_worse", "lower_is_worse"})
DATA_CLASSES = frozenset({"synthetic_test", "real"})
SPLITS = frozenset({"development", "held_out"})


class Stage4CalibrationError(ValueError):
    """Stable fail-closed rejection for invalid calibration operations."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "rejected",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


def _require_nonempty_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Stage4CalibrationError(
            "invalid_contract",
            f"{name} must be a non-empty string.",
        )
    return value


def _require_finite(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Stage4CalibrationError(
            "invalid_contract",
            f"{name} must be a finite number.",
        )
    number = float(value)
    if not math.isfinite(number):
        raise Stage4CalibrationError(
            "invalid_contract",
            f"{name} must be a finite number.",
        )
    return number


def _canonical_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CalibrationObservation:
    observation_id: str
    dataset_item_id: str
    source_family_id: str
    finding_type: str
    metric_name: str
    raw_value: float
    reference_label: str
    split: str
    data_class: str
    purpose: str
    purpose_permission_granted: bool
    provenance_reference: str

    def __post_init__(self) -> None:
        _require_nonempty_string("observation_id", self.observation_id)
        _require_nonempty_string("dataset_item_id", self.dataset_item_id)
        _require_nonempty_string("source_family_id", self.source_family_id)
        _require_nonempty_string("metric_name", self.metric_name)
        _require_nonempty_string("provenance_reference", self.provenance_reference)
        _require_finite("raw_value", self.raw_value)

        if self.finding_type not in TUNABLE_FINDINGS:
            raise Stage4CalibrationError(
                "unsupported_finding",
                "Observation finding type is not Stage 4 threshold-calibratable.",
                details={"findingType": self.finding_type},
            )
        if self.reference_label not in REFERENCE_LABELS:
            raise Stage4CalibrationError(
                "invalid_reference_label",
                "Observation reference label is not recognized.",
                details={"referenceLabel": self.reference_label},
            )
        if self.split not in SPLITS:
            raise Stage4CalibrationError(
                "invalid_split",
                "Observation split must be development or held_out.",
                details={"split": self.split},
            )
        if self.data_class not in DATA_CLASSES:
            raise Stage4CalibrationError(
                "invalid_data_class",
                "Observation data class must be synthetic_test or real.",
                details={"dataClass": self.data_class},
            )
        if not isinstance(self.purpose_permission_granted, bool):
            raise Stage4CalibrationError(
                "invalid_contract",
                "purpose_permission_granted must be boolean.",
            )

        if self.data_class == "synthetic_test":
            if self.purpose != "synthetic_contract_test":
                raise Stage4CalibrationError(
                    "invalid_synthetic_purpose",
                    "Synthetic calibration observations are contract-test evidence only.",
                )
            if self.purpose_permission_granted:
                raise Stage4CalibrationError(
                    "invalid_synthetic_permission",
                    "Synthetic contract tests must not pretend to hold a real dataset purpose grant.",
                )
            return

        required_purpose = (
            "safety_calibration" if self.split == "development" else "held_out_evaluation"
        )
        if self.purpose != required_purpose:
            raise Stage4CalibrationError(
                "purpose_mismatch",
                "Real calibration observation purpose does not match its split.",
                details={
                    "split": self.split,
                    "requiredPurpose": required_purpose,
                    "actualPurpose": self.purpose,
                },
            )
        if not self.purpose_permission_granted:
            raise Stage4CalibrationError(
                "purpose_not_granted",
                "Real calibration observations require an already validated purpose grant.",
                details={"requiredPurpose": required_purpose},
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CalibrationObservation":
        if not isinstance(value, Mapping):
            raise Stage4CalibrationError(
                "invalid_contract",
                "Calibration observation must be an object.",
            )
        expected = {
            "observationId",
            "datasetItemId",
            "sourceFamilyId",
            "findingType",
            "metricName",
            "rawValue",
            "referenceLabel",
            "split",
            "dataClass",
            "purpose",
            "purposePermissionGranted",
            "provenanceReference",
        }
        unknown = sorted(str(key) for key in value if key not in expected)
        missing = sorted(key for key in expected if key not in value)
        if unknown or missing:
            raise Stage4CalibrationError(
                "invalid_contract",
                "Calibration observation fields do not match the Stage 4 schema.",
                details={"unknown": unknown, "missing": missing},
            )
        return cls(
            observation_id=value["observationId"],
            dataset_item_id=value["datasetItemId"],
            source_family_id=value["sourceFamilyId"],
            finding_type=value["findingType"],
            metric_name=value["metricName"],
            raw_value=value["rawValue"],
            reference_label=value["referenceLabel"],
            split=value["split"],
            data_class=value["dataClass"],
            purpose=value["purpose"],
            purpose_permission_granted=value["purposePermissionGranted"],
            provenance_reference=value["provenanceReference"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observationId": self.observation_id,
            "datasetItemId": self.dataset_item_id,
            "sourceFamilyId": self.source_family_id,
            "findingType": self.finding_type,
            "metricName": self.metric_name,
            "rawValue": float(self.raw_value),
            "referenceLabel": self.reference_label,
            "split": self.split,
            "dataClass": self.data_class,
            "purpose": self.purpose,
            "purposePermissionGranted": self.purpose_permission_granted,
            "provenanceReference": self.provenance_reference,
        }


@dataclass(frozen=True)
class ThresholdCandidate:
    candidate_id: str
    finding_type: str
    metric_name: str
    direction: str
    possible_threshold: float
    probable_threshold: float
    derivation_data_class: str
    derived_from_split: str
    derived_from_source_families: tuple[str, ...]
    parent_configuration_digest: str

    def __post_init__(self) -> None:
        _require_nonempty_string("candidate_id", self.candidate_id)
        _require_nonempty_string("metric_name", self.metric_name)
        _require_nonempty_string("parent_configuration_digest", self.parent_configuration_digest)
        possible = _require_finite("possible_threshold", self.possible_threshold)
        probable = _require_finite("probable_threshold", self.probable_threshold)

        if self.finding_type not in TUNABLE_FINDINGS:
            raise Stage4CalibrationError(
                "unsupported_finding",
                "Candidate finding type is not Stage 4 threshold-calibratable.",
            )
        if self.direction not in DIRECTIONS:
            raise Stage4CalibrationError(
                "invalid_direction",
                "Candidate direction must be higher_is_worse or lower_is_worse.",
            )
        if self.derivation_data_class not in DATA_CLASSES:
            raise Stage4CalibrationError(
                "invalid_data_class",
                "Candidate derivation data class is invalid.",
            )
        if self.derived_from_split != "development":
            raise Stage4CalibrationError(
                "held_out_tuning_forbidden",
                "Threshold candidates may be derived only from development evidence.",
            )
        if (
            not isinstance(self.derived_from_source_families, tuple)
            or not self.derived_from_source_families
            or any(not isinstance(item, str) or not item for item in self.derived_from_source_families)
        ):
            raise Stage4CalibrationError(
                "invalid_candidate_provenance",
                "Candidate requires at least one source-family provenance binding.",
            )
        if len(set(self.derived_from_source_families)) != len(self.derived_from_source_families):
            raise Stage4CalibrationError(
                "invalid_candidate_provenance",
                "Candidate source-family provenance must be unique.",
            )

        if self.direction == "higher_is_worse" and possible > probable:
            raise Stage4CalibrationError(
                "invalid_threshold_order",
                "Higher-is-worse candidate requires possible <= probable.",
            )
        if self.direction == "lower_is_worse" and probable > possible:
            raise Stage4CalibrationError(
                "invalid_threshold_order",
                "Lower-is-worse candidate requires probable <= possible.",
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ThresholdCandidate":
        if not isinstance(value, Mapping):
            raise Stage4CalibrationError(
                "invalid_contract",
                "Threshold candidate must be an object.",
            )
        expected = {
            "candidateId",
            "findingType",
            "metricName",
            "direction",
            "possibleThreshold",
            "probableThreshold",
            "derivationDataClass",
            "derivedFromSplit",
            "derivedFromSourceFamilies",
            "parentConfigurationDigest",
        }
        unknown = sorted(str(key) for key in value if key not in expected)
        missing = sorted(key for key in expected if key not in value)
        if unknown or missing:
            raise Stage4CalibrationError(
                "invalid_contract",
                "Threshold candidate fields do not match the Stage 4 schema.",
                details={"unknown": unknown, "missing": missing},
            )
        families = value["derivedFromSourceFamilies"]
        if not isinstance(families, Sequence) or isinstance(families, (str, bytes)):
            raise Stage4CalibrationError(
                "invalid_candidate_provenance",
                "derivedFromSourceFamilies must be an array.",
            )
        return cls(
            candidate_id=value["candidateId"],
            finding_type=value["findingType"],
            metric_name=value["metricName"],
            direction=value["direction"],
            possible_threshold=value["possibleThreshold"],
            probable_threshold=value["probableThreshold"],
            derivation_data_class=value["derivationDataClass"],
            derived_from_split=value["derivedFromSplit"],
            derived_from_source_families=tuple(families),
            parent_configuration_digest=value["parentConfigurationDigest"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidateId": self.candidate_id,
            "findingType": self.finding_type,
            "metricName": self.metric_name,
            "direction": self.direction,
            "possibleThreshold": float(self.possible_threshold),
            "probableThreshold": float(self.probable_threshold),
            "derivationDataClass": self.derivation_data_class,
            "derivedFromSplit": self.derived_from_split,
            "derivedFromSourceFamilies": list(self.derived_from_source_families),
            "parentConfigurationDigest": self.parent_configuration_digest,
        }

    def digest(self) -> str:
        return _canonical_digest(self.to_dict())


def _coerce_observations(
    values: Iterable[CalibrationObservation | Mapping[str, Any]],
) -> list[CalibrationObservation]:
    resolved: list[CalibrationObservation] = []
    for value in values:
        if isinstance(value, CalibrationObservation):
            resolved.append(value)
        else:
            resolved.append(CalibrationObservation.from_mapping(value))
    if not resolved:
        raise Stage4CalibrationError(
            "insufficient_observations",
            "At least one calibration observation is required.",
        )
    return resolved


def freeze_candidate(
    candidate: ThresholdCandidate | Mapping[str, Any],
    derivation_observations: Iterable[CalibrationObservation | Mapping[str, Any]],
    *,
    real_data_execution_authorized: bool = False,
) -> dict[str, Any]:
    """Freeze candidate provenance without selecting thresholds from held-out data."""

    resolved_candidate = (
        candidate if isinstance(candidate, ThresholdCandidate) else ThresholdCandidate.from_mapping(candidate)
    )
    observations = _coerce_observations(derivation_observations)

    for observation in observations:
        if observation.split != "development":
            raise Stage4CalibrationError(
                "held_out_tuning_forbidden",
                "Held-out observations cannot participate in threshold candidate derivation.",
                details={"observationId": observation.observation_id},
            )
        if observation.finding_type != resolved_candidate.finding_type:
            raise Stage4CalibrationError(
                "candidate_observation_mismatch",
                "Candidate and derivation observation finding types differ.",
            )
        if observation.metric_name != resolved_candidate.metric_name:
            raise Stage4CalibrationError(
                "candidate_observation_mismatch",
                "Candidate and derivation observation metric names differ.",
            )
        if observation.data_class == "real" and not real_data_execution_authorized:
            raise Stage4CalibrationError(
                "real_data_calibration_not_authorized",
                "Real-data Stage 4 calibration remains fail-closed.",
            )

    data_classes = {observation.data_class for observation in observations}
    if data_classes != {resolved_candidate.derivation_data_class}:
        raise Stage4CalibrationError(
            "candidate_observation_mismatch",
            "Candidate derivation data class does not match its observations.",
        )

    observed_families = {observation.source_family_id for observation in observations}
    if observed_families != set(resolved_candidate.derived_from_source_families):
        raise Stage4CalibrationError(
            "candidate_provenance_mismatch",
            "Candidate source-family provenance does not exactly match derivation observations.",
            details={
                "candidateFamilies": sorted(resolved_candidate.derived_from_source_families),
                "observedFamilies": sorted(observed_families),
            },
        )

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "frameworkVersion": FRAMEWORK_VERSION,
        "status": "candidate_frozen",
        "candidate": resolved_candidate.to_dict(),
        "candidateDigest": {
            "algorithm": "sha256",
            "value": resolved_candidate.digest(),
        },
        "derivation": {
            "split": "development",
            "dataClass": resolved_candidate.derivation_data_class,
            "observationCount": len(observations),
            "sourceFamilyCount": len(observed_families),
            "sourceFamilies": sorted(observed_families),
        },
        "assertions": {
            "heldOutThresholdTuningUsed": False,
            "realDataExecutionAuthorized": bool(real_data_execution_authorized),
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
    }
    manifest["manifestDigest"] = {
        "algorithm": "sha256",
        "value": _canonical_digest(manifest),
    }
    return manifest


def _classify(candidate: ThresholdCandidate, raw_value: float) -> str:
    value = _require_finite("raw_value", raw_value)
    if candidate.direction == "higher_is_worse":
        if value >= candidate.probable_threshold:
            return "probable"
        if value >= candidate.possible_threshold:
            return "possible"
        return "clear"

    if value <= candidate.probable_threshold:
        return "probable"
    if value <= candidate.possible_threshold:
        return "possible"
    return "clear"


def evaluate_candidate(
    candidate: ThresholdCandidate | Mapping[str, Any],
    observations: Iterable[CalibrationObservation | Mapping[str, Any]],
    *,
    evaluation_split: str,
    real_data_execution_authorized: bool = False,
) -> dict[str, Any]:
    """Evaluate a frozen candidate without feeding evaluation data back into it."""

    resolved_candidate = (
        candidate if isinstance(candidate, ThresholdCandidate) else ThresholdCandidate.from_mapping(candidate)
    )
    resolved_observations = _coerce_observations(observations)

    if evaluation_split not in SPLITS:
        raise Stage4CalibrationError(
            "invalid_split",
            "Evaluation split must be development or held_out.",
        )

    candidate_families = set(resolved_candidate.derived_from_source_families)
    assessed = 0
    not_assessed = 0
    exact = 0
    false_negative = 0
    false_positive = 0
    result_rows: list[dict[str, Any]] = []

    for observation in resolved_observations:
        if observation.split != evaluation_split:
            raise Stage4CalibrationError(
                "evaluation_split_mismatch",
                "All evaluation observations must match the requested split.",
                details={"observationId": observation.observation_id},
            )
        if observation.finding_type != resolved_candidate.finding_type:
            raise Stage4CalibrationError(
                "candidate_observation_mismatch",
                "Candidate and evaluation observation finding types differ.",
            )
        if observation.metric_name != resolved_candidate.metric_name:
            raise Stage4CalibrationError(
                "candidate_observation_mismatch",
                "Candidate and evaluation observation metric names differ.",
            )
        if observation.data_class == "real" and not real_data_execution_authorized:
            raise Stage4CalibrationError(
                "real_data_calibration_not_authorized",
                "Real-data Stage 4 evaluation remains fail-closed until separately authorized.",
            )
        if evaluation_split == "held_out" and observation.source_family_id in candidate_families:
            raise Stage4CalibrationError(
                "source_family_leakage",
                "Held-out evaluation source family overlaps candidate derivation provenance.",
                details={"sourceFamilyId": observation.source_family_id},
            )

        predicted = _classify(resolved_candidate, observation.raw_value)
        row = {
            "observationId": observation.observation_id,
            "referenceLabel": observation.reference_label,
            "predictedLabel": predicted,
        }
        if observation.reference_label == "not_assessed":
            not_assessed += 1
            row["comparison"] = "not_assessed"
        else:
            assessed += 1
            predicted_rank = LABEL_RANK[predicted]
            reference_rank = LABEL_RANK[observation.reference_label]
            if predicted_rank == reference_rank:
                exact += 1
                row["comparison"] = "exact"
            elif predicted_rank < reference_rank:
                false_negative += 1
                row["comparison"] = "false_negative"
            else:
                false_positive += 1
                row["comparison"] = "false_positive"
        result_rows.append(row)

    total = len(resolved_observations)
    metrics = {
        "observationCount": total,
        "assessedCount": assessed,
        "notAssessedCount": not_assessed,
        "coverageRate": round(assessed / total, 8),
        "notAssessedRate": round(not_assessed / total, 8),
        "exactMatchCount": exact,
        "falseNegativeCount": false_negative,
        "falsePositiveCount": false_positive,
        "exactMatchRate": round(exact / assessed, 8) if assessed else None,
        "falseNegativeRate": round(false_negative / assessed, 8) if assessed else None,
        "falsePositiveRate": round(false_positive / assessed, 8) if assessed else None,
        "sourceFamilyLeakageCount": 0,
    }
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "frameworkVersion": FRAMEWORK_VERSION,
        "status": "evaluated",
        "candidateDigest": {
            "algorithm": "sha256",
            "value": resolved_candidate.digest(),
        },
        "evaluation": {
            "split": evaluation_split,
            "dataClasses": sorted({item.data_class for item in resolved_observations}),
            "metrics": metrics,
            "results": result_rows,
        },
        "assertions": {
            "heldOutThresholdTuningUsed": False,
            "evaluationFedBackIntoCandidate": False,
            "realDataExecutionAuthorized": bool(real_data_execution_authorized),
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
        "limitations": [
            "This framework evaluates supplied threshold candidates; it does not authorize or perform real-data threshold selection.",
            "Numerical Stage 4 acceptance targets require separate purpose-authorized real calibration evidence.",
        ],
    }
    report["reportDigest"] = {
        "algorithm": "sha256",
        "value": _canonical_digest(report),
    }
    return report
