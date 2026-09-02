"""Fail-closed Stage 4 reference-label evidence contracts.

Reference labels are independent evidence. This module never invents labels from
metrics or model output, never treats general project approval as a dataset
purpose grant, and never authorizes held-out labels for candidate derivation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence

REFERENCE_LABEL_CONTRACT_VERSION = "0.1.0"
REFERENCE_LABEL_SCHEMA_VERSION = "1.0.0"
REFERENCE_LABELS = frozenset({"clear", "possible", "probable", "not_assessed"})
FINDING_TYPES = frozenset(
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
SPLITS = frozenset({"development", "held_out"})
DATA_CLASSES = frozenset({"synthetic_test", "real"})
REVIEW_METHODS = frozenset({"synthetic_contract_test", "human_expert_review"})
OPAQUE_REVIEWER_REFERENCE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")


class Stage4ReferenceLabelError(ValueError):
    """Stable fail-closed rejection for invalid reference-label evidence."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": REFERENCE_LABEL_SCHEMA_VERSION,
            "status": "rejected",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


def _nonempty(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Stage4ReferenceLabelError("invalid_contract", f"{name} must be a non-empty string.")
    return value


def _canonical_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _iso_date(name: str, value: Any) -> str:
    text = _nonempty(name, value)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise Stage4ReferenceLabelError(
            "invalid_review_date",
            f"{name} must use YYYY-MM-DD ISO format.",
            details={"value": text},
        ) from exc
    return text


@dataclass(frozen=True)
class ReferenceLabelRecord:
    label_id: str
    observation_id: str
    dataset_item_id: str
    source_family_id: str
    finding_type: str
    reference_label: str
    split: str
    data_class: str
    purpose: str
    purpose_permission_granted: bool
    provenance_reference: str
    reviewer_reference: str
    review_method: str
    reviewed_on: str

    def __post_init__(self) -> None:
        for name, value in (
            ("label_id", self.label_id),
            ("observation_id", self.observation_id),
            ("dataset_item_id", self.dataset_item_id),
            ("source_family_id", self.source_family_id),
            ("purpose", self.purpose),
            ("provenance_reference", self.provenance_reference),
        ):
            _nonempty(name, value)
        _iso_date("reviewed_on", self.reviewed_on)

        if self.finding_type not in FINDING_TYPES:
            raise Stage4ReferenceLabelError(
                "unsupported_finding",
                "Reference label finding type is not calibratable by Stage 4.",
                details={"findingType": self.finding_type},
            )
        if self.reference_label not in REFERENCE_LABELS:
            raise Stage4ReferenceLabelError(
                "invalid_reference_label",
                "Reference label is not recognized.",
                details={"referenceLabel": self.reference_label},
            )
        if self.split not in SPLITS:
            raise Stage4ReferenceLabelError("invalid_split", "split must be development or held_out.")
        if self.data_class not in DATA_CLASSES:
            raise Stage4ReferenceLabelError("invalid_data_class", "data_class must be synthetic_test or real.")
        if self.review_method not in REVIEW_METHODS:
            raise Stage4ReferenceLabelError(
                "invalid_review_method",
                "review_method is not recognized.",
                details={"reviewMethod": self.review_method},
            )
        if not isinstance(self.purpose_permission_granted, bool):
            raise Stage4ReferenceLabelError(
                "invalid_contract",
                "purpose_permission_granted must be boolean.",
            )
        if not isinstance(self.reviewer_reference, str) or not OPAQUE_REVIEWER_REFERENCE.fullmatch(
            self.reviewer_reference
        ):
            raise Stage4ReferenceLabelError(
                "invalid_reviewer_reference",
                "reviewer_reference must be an opaque non-personal reference token.",
            )

        if self.data_class == "synthetic_test":
            if self.review_method != "synthetic_contract_test":
                raise Stage4ReferenceLabelError(
                    "invalid_synthetic_review_method",
                    "Synthetic reference labels must use synthetic_contract_test review method.",
                )
            if self.purpose != "synthetic_contract_test":
                raise Stage4ReferenceLabelError(
                    "invalid_synthetic_purpose",
                    "Synthetic reference labels are contract-test evidence only.",
                )
            if self.purpose_permission_granted:
                raise Stage4ReferenceLabelError(
                    "invalid_synthetic_permission",
                    "Synthetic contract labels must not claim a real-data purpose grant.",
                )
            return

        if self.review_method != "human_expert_review":
            raise Stage4ReferenceLabelError(
                "real_reference_requires_human_review",
                "Real reference labels require human_expert_review provenance.",
            )
        required_purpose = "safety_calibration" if self.split == "development" else "held_out_evaluation"
        if self.purpose != required_purpose:
            raise Stage4ReferenceLabelError(
                "purpose_mismatch",
                "Real reference-label purpose does not match its split.",
                details={
                    "split": self.split,
                    "requiredPurpose": required_purpose,
                    "actualPurpose": self.purpose,
                },
            )
        if not self.purpose_permission_granted:
            raise Stage4ReferenceLabelError(
                "purpose_not_granted",
                "Real reference labels require an already validated artifact-purpose grant.",
                details={"requiredPurpose": required_purpose},
            )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReferenceLabelRecord":
        if not isinstance(value, Mapping):
            raise Stage4ReferenceLabelError("invalid_contract", "Reference label record must be an object.")
        expected = {
            "labelId",
            "observationId",
            "datasetItemId",
            "sourceFamilyId",
            "findingType",
            "referenceLabel",
            "split",
            "dataClass",
            "purpose",
            "purposePermissionGranted",
            "provenanceReference",
            "reviewerReference",
            "reviewMethod",
            "reviewedOn",
        }
        missing = sorted(key for key in expected if key not in value)
        unknown = sorted(str(key) for key in value if key not in expected)
        if missing or unknown:
            raise Stage4ReferenceLabelError(
                "invalid_contract",
                "Reference label fields do not match the Stage 4 schema.",
                details={"missing": missing, "unknown": unknown},
            )
        return cls(
            label_id=value["labelId"],
            observation_id=value["observationId"],
            dataset_item_id=value["datasetItemId"],
            source_family_id=value["sourceFamilyId"],
            finding_type=value["findingType"],
            reference_label=value["referenceLabel"],
            split=value["split"],
            data_class=value["dataClass"],
            purpose=value["purpose"],
            purpose_permission_granted=value["purposePermissionGranted"],
            provenance_reference=value["provenanceReference"],
            reviewer_reference=value["reviewerReference"],
            review_method=value["reviewMethod"],
            reviewed_on=value["reviewedOn"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "labelId": self.label_id,
            "observationId": self.observation_id,
            "datasetItemId": self.dataset_item_id,
            "sourceFamilyId": self.source_family_id,
            "findingType": self.finding_type,
            "referenceLabel": self.reference_label,
            "split": self.split,
            "dataClass": self.data_class,
            "purpose": self.purpose,
            "purposePermissionGranted": self.purpose_permission_granted,
            "provenanceReference": self.provenance_reference,
            "reviewerReference": self.reviewer_reference,
            "reviewMethod": self.review_method,
            "reviewedOn": self.reviewed_on,
        }


@dataclass(frozen=True)
class ReferenceLabelBundle:
    bundle_id: str
    records: tuple[ReferenceLabelRecord, ...]

    def __post_init__(self) -> None:
        _nonempty("bundle_id", self.bundle_id)
        if not self.records:
            raise Stage4ReferenceLabelError(
                "empty_reference_bundle",
                "Reference-label bundle must contain at least one record.",
            )

        label_ids = [record.label_id for record in self.records]
        observation_ids = [record.observation_id for record in self.records]
        if len(label_ids) != len(set(label_ids)):
            raise Stage4ReferenceLabelError(
                "duplicate_label_id",
                "Reference-label bundle contains duplicate label IDs.",
            )
        if len(observation_ids) != len(set(observation_ids)):
            raise Stage4ReferenceLabelError(
                "duplicate_observation_id",
                "Each calibration observation may have only one frozen reference label per bundle.",
            )

        splits = {record.split for record in self.records}
        data_classes = {record.data_class for record in self.records}
        purposes = {record.purpose for record in self.records}
        if len(splits) != 1 or len(data_classes) != 1 or len(purposes) != 1:
            raise Stage4ReferenceLabelError(
                "mixed_bundle_scope",
                "A reference-label bundle must have one split, data class and purpose.",
                details={
                    "splits": sorted(splits),
                    "dataClasses": sorted(data_classes),
                    "purposes": sorted(purposes),
                },
            )

        by_observation: dict[str, tuple[str, str, str]] = {}
        for record in self.records:
            identity = (record.dataset_item_id, record.source_family_id, record.finding_type)
            previous = by_observation.setdefault(record.observation_id, identity)
            if previous != identity:
                raise Stage4ReferenceLabelError(
                    "observation_identity_conflict",
                    "Observation ID maps to conflicting source identity.",
                    details={"observationId": record.observation_id},
                )

    @classmethod
    def from_records(
        cls,
        bundle_id: str,
        records: Iterable[ReferenceLabelRecord | Mapping[str, Any]],
    ) -> "ReferenceLabelBundle":
        resolved: list[ReferenceLabelRecord] = []
        for record in records:
            resolved.append(
                record if isinstance(record, ReferenceLabelRecord) else ReferenceLabelRecord.from_mapping(record)
            )
        return cls(bundle_id=bundle_id, records=tuple(resolved))

    @property
    def split(self) -> str:
        return self.records[0].split

    @property
    def data_class(self) -> str:
        return self.records[0].data_class

    @property
    def purpose(self) -> str:
        return self.records[0].purpose

    def to_dict(self) -> dict[str, Any]:
        ordered = sorted(self.records, key=lambda item: (item.observation_id, item.label_id))
        return {
            "schemaVersion": REFERENCE_LABEL_SCHEMA_VERSION,
            "contractVersion": REFERENCE_LABEL_CONTRACT_VERSION,
            "bundleId": self.bundle_id,
            "split": self.split,
            "dataClass": self.data_class,
            "purpose": self.purpose,
            "records": [record.to_dict() for record in ordered],
        }

    def digest(self) -> str:
        return _canonical_digest(self.to_dict())


def freeze_reference_label_bundle(
    bundle: ReferenceLabelBundle,
    *,
    accepted_real_reference_bundle: bool = False,
) -> dict[str, Any]:
    """Freeze a public-safe receipt without asserting real-bundle acceptance."""

    if bundle.data_class == "real" and not accepted_real_reference_bundle:
        raise Stage4ReferenceLabelError(
            "real_reference_bundle_not_accepted",
            "Real reference-label evidence requires a separate accepted provenance decision.",
        )

    label_counts = {label: 0 for label in sorted(REFERENCE_LABELS)}
    source_families: set[str] = set()
    dataset_items: set[str] = set()
    review_methods: set[str] = set()
    for record in bundle.records:
        label_counts[record.reference_label] += 1
        source_families.add(record.source_family_id)
        dataset_items.add(record.dataset_item_id)
        review_methods.add(record.review_method)

    receipt = {
        "schemaVersion": REFERENCE_LABEL_SCHEMA_VERSION,
        "contractVersion": REFERENCE_LABEL_CONTRACT_VERSION,
        "status": "reference_bundle_frozen",
        "bundleId": bundle.bundle_id,
        "bundleDigest": {"algorithm": "sha256", "value": bundle.digest()},
        "scope": {
            "split": bundle.split,
            "dataClass": bundle.data_class,
            "purpose": bundle.purpose,
            "recordCount": len(bundle.records),
            "datasetItemCount": len(dataset_items),
            "sourceFamilyCount": len(source_families),
            "labelCounts": label_counts,
            "reviewMethods": sorted(review_methods),
        },
        "assertions": {
            "labelsAutomaticallyGenerated": False,
            "modelPredictionsUsedAsReferenceLabels": False,
            "heldOutCandidateDerivationAuthorized": False,
            "realReferenceBundleAccepted": bool(accepted_real_reference_bundle),
            "realDataCalibrationAuthorized": False,
            "productionThresholdChangeAuthorized": False,
            "productionResourceLimitChangeAuthorized": False,
            "modelTrainingAuthorized": False,
            "publicationAuthorized": False,
        },
    }
    receipt["receiptDigest"] = {"algorithm": "sha256", "value": _canonical_digest(receipt)}
    return receipt


def require_candidate_derivation_eligible(
    bundle: ReferenceLabelBundle,
    *,
    accepted_real_reference_bundle: bool = False,
) -> None:
    """Reject held-out or unaccepted real label bundles before derivation."""

    if bundle.split != "development":
        raise Stage4ReferenceLabelError(
            "held_out_reference_derivation_forbidden",
            "Held-out reference labels may evaluate a frozen candidate but cannot derive one.",
        )
    if bundle.data_class == "real" and not accepted_real_reference_bundle:
        raise Stage4ReferenceLabelError(
            "real_reference_bundle_not_accepted",
            "Real development reference labels require a separate accepted provenance decision.",
        )


def validate_observation_bindings(
    bundle: ReferenceLabelBundle,
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require exact one-to-one binding between raw metric observations and labels.

    The observation mapping intentionally excludes any prediction or label field.
    Expected fields are observationId, datasetItemId, sourceFamilyId, findingType,
    split, dataClass and purpose.
    """

    expected_fields = {
        "observationId",
        "datasetItemId",
        "sourceFamilyId",
        "findingType",
        "split",
        "dataClass",
        "purpose",
    }
    raw_by_id: dict[str, Mapping[str, Any]] = {}
    for observation in observations:
        if not isinstance(observation, Mapping):
            raise Stage4ReferenceLabelError("invalid_observation_binding", "Observation must be an object.")
        missing = sorted(key for key in expected_fields if key not in observation)
        forbidden = sorted(key for key in ("referenceLabel", "predictedLabel") if key in observation)
        if missing or forbidden:
            raise Stage4ReferenceLabelError(
                "invalid_observation_binding",
                "Raw observation binding fields are invalid.",
                details={"missing": missing, "forbidden": forbidden},
            )
        observation_id = _nonempty("observationId", observation["observationId"])
        if observation_id in raw_by_id:
            raise Stage4ReferenceLabelError(
                "duplicate_observation_id",
                "Raw observation binding contains a duplicate observation ID.",
            )
        raw_by_id[observation_id] = observation

    labels_by_id = {record.observation_id: record for record in bundle.records}
    if set(raw_by_id) != set(labels_by_id):
        raise Stage4ReferenceLabelError(
            "observation_set_mismatch",
            "Raw observations and reference labels must bind one-to-one.",
            details={
                "missingLabels": sorted(set(raw_by_id) - set(labels_by_id)),
                "missingObservations": sorted(set(labels_by_id) - set(raw_by_id)),
            },
        )

    for observation_id, raw in raw_by_id.items():
        label = labels_by_id[observation_id]
        expected_identity = {
            "datasetItemId": label.dataset_item_id,
            "sourceFamilyId": label.source_family_id,
            "findingType": label.finding_type,
            "split": label.split,
            "dataClass": label.data_class,
            "purpose": label.purpose,
        }
        for key, expected in expected_identity.items():
            if raw.get(key) != expected:
                raise Stage4ReferenceLabelError(
                    "observation_identity_mismatch",
                    "Raw observation identity does not match frozen reference-label evidence.",
                    details={
                        "observationId": observation_id,
                        "field": key,
                        "expected": expected,
                        "actual": raw.get(key),
                    },
                )

    result = {
        "schemaVersion": REFERENCE_LABEL_SCHEMA_VERSION,
        "status": "bindings_valid",
        "bundleDigest": {"algorithm": "sha256", "value": bundle.digest()},
        "observationCount": len(raw_by_id),
        "assertions": {
            "oneToOneObservationBinding": True,
            "predictionFieldsAcceptedAsReferenceEvidence": False,
            "heldOutCandidateDerivationAuthorized": False,
        },
    }
    result["bindingDigest"] = {"algorithm": "sha256", "value": _canonical_digest(result)}
    return result
