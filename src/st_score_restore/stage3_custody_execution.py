"""Fail-closed Stage 3 approved-custody execution for PDF pipeline evaluation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date
import hashlib
import json
import re
from typing import Any, Mapping

from .dataset_catalog_validation import validate_dataset_catalog
from .dataset_contract_common import _permission, _permission_valid_on, _restriction_by_type
from .dataset_contract_constants import DatasetManifestError, STAGE1_ENVIRONMENT
from .pdf_pipeline import (
    PIPELINE_VERSION,
    RENDERER_BINDING,
    RENDERER_BINDING_VERSION,
    RENDERER_NAME,
    PdfPipelineConfig,
    PdfPipelineError,
    PdfPipelineResult,
    process_pdf_bytes,
)
from .quality_analysis import QualityAnalysisConfig

SCHEMA_VERSION = "1.0.0"
CONTRACT_VERSION = "0.1.0"
APPROVED_CUSTODY_ENVIRONMENT = STAGE1_ENVIRONMENT
_STAGE3_PURPOSE_BY_SPLIT = {
    "development": "pdf_pipeline_evaluation",
    "held_out": "held_out_evaluation",
}
_PDF_INPUT_KINDS = {"digital_pdf", "scanned_pdf", "hybrid_pdf"}
_ENVIRONMENT = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")


class Stage3CustodyExecutionError(ValueError):
    """Stable fail-closed rejection before or during Stage 3 PDF execution."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
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
                "details": deepcopy(self.details),
            },
        }


@dataclass(frozen=True)
class Stage3CustodyExecutionResult:
    """Public-safe receipt plus custody-only Stage 3 manifest and derivatives."""

    public_receipt: Mapping[str, Any]
    _custody_manifest: Mapping[str, Any] | None = field(default=None, repr=False)
    _custody_rendered_pages: Mapping[int, bytes] = field(default_factory=dict, repr=False)

    def to_public_dict(self) -> dict[str, Any]:
        return deepcopy(dict(self.public_receipt))

    def restricted_manifest_for_custody(self) -> dict[str, Any] | None:
        if self._custody_manifest is None:
            return None
        return deepcopy(dict(self._custody_manifest))

    def restricted_page_bytes_for_custody(self, page_index: int) -> bytes | None:
        value = self._custody_rendered_pages.get(page_index)
        return bytes(value) if value is not None else None


def _as_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise Stage3CustodyExecutionError(
            "invalid_execution_date",
            "Execution date must be an ISO date string or datetime.date.",
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Stage3CustodyExecutionError(
            "invalid_execution_date",
            "Execution date must use YYYY-MM-DD.",
        ) from exc


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _receipt_digest(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receiptDigest", None)
    return _canonical_sha256(payload)


def _find_item(catalog: Mapping[str, Any], dataset_item_id: str) -> dict[str, Any]:
    for item in catalog["items"]:
        if item["datasetItemId"] == dataset_item_id:
            return item
    raise Stage3CustodyExecutionError(
        "dataset_item_not_found",
        "Dataset item is not present in the validated catalog.",
        details={"datasetItemId": dataset_item_id},
    )


def _require_restrictions(
    permission: Mapping[str, Any],
    *,
    split: str,
    storage_class: str,
    environment: str,
    execution_date: date,
) -> dict[str, Any]:
    split_rule = _restriction_by_type(dict(permission), "split_allowlist")
    if split_rule is not None and split not in split_rule["values"]:
        raise Stage3CustodyExecutionError(
            "split_restriction_violation",
            "Purpose permission does not allow the assigned split.",
            details={"split": split},
        )

    storage_rule = _restriction_by_type(dict(permission), "storage_class_allowlist")
    if storage_rule is not None and storage_class not in storage_rule["values"]:
        raise Stage3CustodyExecutionError(
            "storage_restriction_violation",
            "Purpose permission does not allow the active storage class.",
            details={"storageClass": storage_class},
        )

    environment_rule = _restriction_by_type(dict(permission), "environment_allowlist")
    if environment_rule is not None and environment not in environment_rule["values"]:
        raise Stage3CustodyExecutionError(
            "environment_restriction_violation",
            "Purpose permission does not allow the requested execution environment.",
            details={"environment": environment},
        )

    retention_rule = _restriction_by_type(dict(permission), "retention_not_after")
    if retention_rule is not None:
        maximum = date.fromisoformat(retention_rule["date"])
        if execution_date > maximum:
            raise Stage3CustodyExecutionError(
                "permission_retention_restriction_expired",
                "Execution date exceeds the permission retention boundary.",
                details={"retentionNotAfter": retention_rule["date"]},
            )

    export_rule = _restriction_by_type(dict(permission), "external_export")
    export_state = (
        "explicitly_blocked"
        if export_rule is not None and export_rule["allowed"] is False
        else "not_authorized_by_stage3_execution"
    )
    return {
        "splitRestrictionSatisfied": True,
        "storageRestrictionSatisfied": True,
        "environmentRestrictionSatisfied": True,
        "retentionRestrictionSatisfied": True,
        "externalExportState": export_state,
    }


def _validate_exact_bytes(item: Mapping[str, Any], data: bytes) -> tuple[str, int]:
    if not isinstance(data, bytes) or not data:
        raise Stage3CustodyExecutionError(
            "invalid_source_bytes",
            "A non-empty immutable byte sequence is required.",
        )
    digest = hashlib.sha256(data).hexdigest()
    size = len(data)
    artifact = item["artifact"]
    if digest != artifact["sha256"]:
        raise Stage3CustodyExecutionError(
            "exact_sha256_mismatch",
            "Custody bytes do not match the admitted artifact SHA-256.",
            details={"expected": artifact["sha256"], "actual": digest},
        )
    if size != artifact["byteSize"]:
        raise Stage3CustodyExecutionError(
            "exact_byte_size_mismatch",
            "Custody bytes do not match the admitted artifact byte size.",
            details={"expected": artifact["byteSize"], "actual": size},
        )
    return digest, size


def _validate_pdf_kind(item: Mapping[str, Any]) -> str:
    kind = item["input"]["kind"]
    if kind not in _PDF_INPUT_KINDS:
        raise Stage3CustodyExecutionError(
            "non_pdf_dataset_item",
            "Stage 3 PDF custody execution accepts admitted PDF items only.",
            details={"catalogInputKind": kind},
        )
    return kind


def _validate_inspection_classification(catalog_kind: str, manifest: Mapping[str, Any]) -> None:
    classification = manifest.get("source", {}).get("inputInspectionClassification")
    allowed = {
        "digital_pdf": {"digital"},
        "scanned_pdf": {"scanned", "hybrid"},
        "hybrid_pdf": {"hybrid"},
    }[catalog_kind]
    if classification not in allowed:
        raise Stage3CustodyExecutionError(
            "catalog_pdf_kind_mismatch",
            "Stage 3 inspection classification does not match the admitted PDF kind.",
            details={
                "catalogInputKind": catalog_kind,
                "inspectionClassification": classification,
                "allowed": sorted(allowed),
            },
        )


def _page_summary(manifest: Mapping[str, Any]) -> dict[str, Any]:
    classification_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    review_required = 0
    for page in manifest.get("pages", []):
        classification = str(page.get("pageClassification"))
        status = str(page.get("status"))
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        if page.get("reviewRequired") is True:
            review_required += 1
    return {
        "pageCount": int(manifest.get("pageCount", 0)),
        "renderedPageCount": int(manifest.get("renderedPageCount", 0)),
        "reviewRequiredCount": review_required,
        "classificationCounts": dict(sorted(classification_counts.items())),
        "statusCounts": dict(sorted(status_counts.items())),
        "pageOrderPreserved": manifest.get("pageOrderPreserved") is True,
        "vectorPagesRasterized": manifest.get("vectorPagesRasterized") is True,
    }


def run_authorized_pdf_pipeline_execution(
    catalog: Mapping[str, Any],
    *,
    dataset_item_id: str,
    data: bytes,
    purpose: str,
    execution_date: date | str,
    environment: str = APPROVED_CUSTODY_ENVIRONMENT,
    config: PdfPipelineConfig | Mapping[str, Any] | None = None,
    quality_config: QualityAnalysisConfig | Mapping[str, Any] | None = None,
) -> Stage3CustodyExecutionResult:
    """Run Stage 3 PDF processing only after purpose, custody, and exact-byte gates."""

    if not isinstance(dataset_item_id, str) or not dataset_item_id:
        raise Stage3CustodyExecutionError(
            "invalid_dataset_item_id",
            "dataset_item_id must be a non-empty string.",
        )
    if not isinstance(environment, str) or _ENVIRONMENT.fullmatch(environment) is None:
        raise Stage3CustodyExecutionError(
            "invalid_execution_environment",
            "Execution environment must be a stable lowercase code.",
        )

    try:
        validated = validate_dataset_catalog(deepcopy(dict(catalog)))
    except (DatasetManifestError, TypeError, KeyError) as exc:
        raise Stage3CustodyExecutionError(
            "catalog_invalid",
            "Dataset catalog failed the canonical governance validator.",
        ) from exc

    item = _find_item(validated, dataset_item_id)
    artifact = item["artifact"]
    split = item["split"]
    storage_class = item["retention"]["storageClass"]
    when = _as_date(execution_date)
    catalog_kind = _validate_pdf_kind(item)

    if artifact["state"] != "external_available":
        raise Stage3CustodyExecutionError(
            "artifact_not_available",
            "Stage 3 execution requires an admitted external_available artifact.",
        )
    if item["review"]["status"] != "approved":
        raise Stage3CustodyExecutionError(
            "dataset_review_not_approved",
            "Stage 3 execution requires approved dataset review.",
        )
    if item["revocation"]["status"] != "not_revoked":
        raise Stage3CustodyExecutionError(
            "artifact_revoked_or_pending",
            "Revoked or pending-deletion artifacts cannot be executed.",
        )
    if item["retention"]["deletionRequired"] is not False:
        raise Stage3CustodyExecutionError(
            "artifact_pending_deletion",
            "Artifacts marked for deletion cannot be executed.",
        )

    retention_expiry = item["retention"]["expiresOn"]
    if retention_expiry is not None and when >= date.fromisoformat(retention_expiry):
        raise Stage3CustodyExecutionError(
            "artifact_retention_expired",
            "Execution date is outside the artifact retention window.",
            details={"expiresOn": retention_expiry},
        )

    expected_purpose = _STAGE3_PURPOSE_BY_SPLIT.get(split)
    if expected_purpose is None:
        raise Stage3CustodyExecutionError(
            "split_not_authorized_for_stage3_execution",
            "Stage 3 corpus execution is limited to development and held-out splits.",
            details={"split": split},
        )
    if purpose != expected_purpose:
        raise Stage3CustodyExecutionError(
            "purpose_not_authorized_for_split",
            "Requested purpose does not match the Stage 3 split boundary.",
            details={
                "split": split,
                "requiredPurpose": expected_purpose,
                "requestedPurpose": purpose,
            },
        )

    permission = _permission(item["permissions"][purpose], f"item.permissions.{purpose}")
    if not _permission_valid_on(permission, when):
        raise Stage3CustodyExecutionError(
            "purpose_permission_not_valid",
            "Stage 3 purpose permission is not granted and valid on the execution date.",
            details={"purpose": purpose, "executionDate": when.isoformat()},
        )

    restriction_state = _require_restrictions(
        permission,
        split=split,
        storage_class=storage_class,
        environment=environment,
        execution_date=when,
    )
    digest, size = _validate_exact_bytes(item, data)

    try:
        pipeline_result: PdfPipelineResult = process_pdf_bytes(
            data,
            source_name=f"{dataset_item_id}.pdf",
            config=config,
            quality_config=quality_config,
        )
    except PdfPipelineError as exc:
        raise Stage3CustodyExecutionError(
            "pdf_pipeline_rejected",
            "Stage 3 PDF pipeline rejected an otherwise authorized artifact.",
            details={"pipelineErrorCode": exc.code},
        ) from exc

    manifest = dict(pipeline_result.manifest)
    _validate_inspection_classification(catalog_kind, manifest)
    summary = _page_summary(manifest)
    manifest_digest = manifest.get("manifestDigest", {}).get("value")
    if not isinstance(manifest_digest, str):
        raise Stage3CustodyExecutionError(
            "pipeline_manifest_digest_missing",
            "Stage 3 pipeline result is missing its deterministic manifest digest.",
        )

    receipt: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "contractVersion": CONTRACT_VERSION,
        "status": "completed",
        "datasetItemId": dataset_item_id,
        "sourceDigest": {"algorithm": "sha256", "value": digest},
        "byteSize": size,
        "catalogInputKind": catalog_kind,
        "purpose": purpose,
        "split": split,
        "storageClass": storage_class,
        "environment": environment,
        "executionDate": when.isoformat(),
        "authorizationReference": permission["authorizationReference"],
        "pipelineVersion": PIPELINE_VERSION,
        "renderer": {
            "name": RENDERER_NAME,
            "binding": RENDERER_BINDING,
            "bindingVersion": RENDERER_BINDING_VERSION,
        },
        "manifestDigest": {"algorithm": "sha256", "value": manifest_digest},
        "pageSummary": summary,
        "reportHandling": {
            "detailedManifestExported": False,
            "detailedManifestPublic": False,
            "derivativeBytesExported": False,
            "custodyOnly": True,
            "externalExportState": restriction_state["externalExportState"],
        },
        "assertions": {
            "exactDigestMatched": True,
            "exactByteSizeMatched": True,
            "purposePermissionValid": True,
            "splitRestrictionSatisfied": restriction_state["splitRestrictionSatisfied"],
            "storageRestrictionSatisfied": restriction_state["storageRestrictionSatisfied"],
            "environmentRestrictionSatisfied": restriction_state["environmentRestrictionSatisfied"],
            "retentionRestrictionSatisfied": restriction_state["retentionRestrictionSatisfied"],
            "heldOutThresholdTuningUsed": False,
            "sourceBytesModified": False,
            "realArtifactBytesInGit": False,
            "trainingAuthorized": False,
            "calibrationAuthorized": False,
            "publicationAuthorized": False,
            "omrPerformed": False,
            "musicalCorrectnessEstablished": False,
        },
        "limitations": [
            "This receipt proves an authorized Stage 3 PDF execution boundary, not musical correctness or restoration effectiveness.",
            "Detailed page manifests, quality findings, metrics, and rendered derivatives remain custody-only unless separately authorized.",
            "Stage 3 engineering limits remain uncalibrated; Stage 4 owns real-data safety calibration.",
        ],
    }
    receipt["receiptDigest"] = {
        "algorithm": "sha256",
        "value": _receipt_digest(receipt),
    }
    return Stage3CustodyExecutionResult(
        public_receipt=receipt,
        _custody_manifest=manifest,
        _custody_rendered_pages=dict(pipeline_result.rendered_pages),
    )


__all__ = [
    "APPROVED_CUSTODY_ENVIRONMENT",
    "CONTRACT_VERSION",
    "SCHEMA_VERSION",
    "Stage3CustodyExecutionError",
    "Stage3CustodyExecutionResult",
    "run_authorized_pdf_pipeline_execution",
]
