"""Stage 1A/1C dataset contract constants and opaque identifier patterns."""

from __future__ import annotations

import re

CATALOG_SCHEMA_VERSION = "1.3.0"
LEGACY_CATALOG_SCHEMA_VERSION = "1.2.0"
SNAPSHOT_SCHEMA_VERSION = "1.2.0"
ENTRY_DECISION_ID = "adr-0013-stage-1-entry-v1"
STAGE1_ENVIRONMENT = "stage1_offline"

OPAQUE_TOKEN_TEXT = r"opq_[0-9a-f]{32}"
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
CODE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
EVIDENCE_ID = re.compile(rf"^evidence:{OPAQUE_TOKEN_TEXT}$")
SUBJECT_ID = re.compile(rf"^subject:{OPAQUE_TOKEN_TEXT}$")
RIGHTS_ACTOR_ID = re.compile(rf"^actor\.rights:{OPAQUE_TOKEN_TEXT}$")
PRIVACY_ACTOR_ID = re.compile(rf"^actor\.privacy:{OPAQUE_TOKEN_TEXT}$")
PURPOSE_ACTOR_ID = re.compile(rf"^actor\.purpose:{OPAQUE_TOKEN_TEXT}$")
DATASET_ACTOR_ID = re.compile(rf"^actor\.dataset:{OPAQUE_TOKEN_TEXT}$")
CUSTODIAN_ACTOR_ID = re.compile(rf"^actor\.custodian:{OPAQUE_TOKEN_TEXT}$")
POLICY_ID = re.compile(rf"^policy:{OPAQUE_TOKEN_TEXT}$")
CUSTODY_ID = re.compile(rf"^custody:{OPAQUE_TOKEN_TEXT}$")
RECEIPT_ID = re.compile(rf"^receipt:{OPAQUE_TOKEN_TEXT}$")

PURPOSES = (
    "fixture_validation",
    "quality_evaluation",
    "quality_calibration",
    "pdf_pipeline_evaluation",
    "safety_calibration",
    "held_out_evaluation",
    "synthetic_derivation",
    "model_training",
    "publication",
    "demonstration",
)
PERMISSION_STATES = {
    "not_requested",
    "pending",
    "granted",
    "denied",
    "expired",
    "withdrawn",
    "not_applicable",
}
SPLITS = {"unassigned", "development", "calibration", "held_out", "training_reserved"}
ASSIGNED_SPLITS = SPLITS - {"unassigned"}
SOURCE_KINDS = {"project_authored", "public_domain", "licensed", "user_provided", "synthetic"}
ARTIFACT_STATES = {"metadata_only", "external_available", "revoked"}
PRIVACY_CLASSES = {"none", "deidentified", "personal", "student"}
PRIVACY_REVIEW_STATES = {"not_required", "pending", "approved", "rejected"}
RIGHTS_REVIEW_STATES = {"pending", "approved", "rejected"}
DATASET_REVIEW_STATES = {"planned", "pending", "approved", "rejected", "revoked"}
RETENTION_POLICIES = {"metadata_only", "external_until_date", "delete_after_validation", "prohibited"}
ELIGIBILITY_CLASSES = {
    "blocked",
    "open_corpus",
    "restricted_corpus",
    "sensitive_custody",
}
STORAGE_CLASSES = {
    "not_assigned",
    "managed_standard",
    "managed_restricted",
    "high_assurance_vault",
}
LEGACY_STORAGE_CLASS = "custody_external"
PROFILE_BY_ELIGIBILITY = {
    "open_corpus": "managed_standard",
    "restricted_corpus": "managed_restricted",
    "sensitive_custody": "high_assurance_vault",
}
DELETION_STATES = {"not_required", "pending", "completed", "failed"}
REVOCATION_STATES = {"not_revoked", "pending_deletion", "completed"}
USAGE_BASIS_CODES = {
    "project_authored",
    "public_domain",
    "license_grant",
    "user_authorization",
    "synthetic_derivation",
}
DEIDENTIFICATION_METHODS = {
    "metadata_scrub",
    "visual_redaction",
    "metadata_scrub_and_visual_redaction",
}
RESTRICTION_TYPES = {
    "split_allowlist",
    "storage_class_allowlist",
    "environment_allowlist",
    "external_export",
    "retention_not_after",
}
INPUT_MEDIA = {
    "digital_pdf": "application/pdf",
    "scanned_pdf": "application/pdf",
    "hybrid_pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "phone_photo": "image/jpeg",
}
NOTATION_KINDS = {"staff", "guitar_tab", "combined_staff_tab"}
DEGRADATIONS = {
    "none",
    "skew",
    "perspective",
    "page_curl",
    "shadow",
    "glare",
    "uneven_lighting",
    "blur",
    "noise",
    "compression",
    "low_resolution",
}
SPLIT_PURPOSES = {
    "development": frozenset(
        {"fixture_validation", "quality_evaluation", "pdf_pipeline_evaluation"}
    ),
    "calibration": frozenset({"quality_calibration", "safety_calibration"}),
    "held_out": frozenset({"held_out_evaluation"}),
    "training_reserved": frozenset({"model_training"}),
}

CATALOG_FIELDS = {"schemaVersion", "entryDecisionId", "catalogId", "descriptionCode", "items"}
ITEM_FIELDS = {
    "datasetItemId",
    "sourceFamilyId",
    "parentItemId",
    "eligibilityClass",
    "artifact",
    "provenance",
    "privacy",
    "input",
    "permissions",
    "split",
    "retention",
    "revocation",
    "syntheticGeneration",
    "review",
    "assertions",
}
SNAPSHOT_FIELDS = {
    "schemaVersion",
    "entryDecisionId",
    "snapshotId",
    "datasetId",
    "version",
    "createdAt",
    "environment",
    "catalogSha256",
    "assignments",
    "heldOutFrozen",
    "trainingUseActivated",
    "revokedItemIds",
    "coverage",
    "review",
}


class DatasetManifestError(ValueError):
    """Dataset metadata violates the approved Stage 1A/1C contract."""
