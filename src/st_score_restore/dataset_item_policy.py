"""Retention, revocation, permission, and restriction validation."""

from __future__ import annotations

from datetime import date
from typing import Any

from .dataset_contract_common import _bool, _date, _enum, _fields, _match, _obj, _permission, _restriction_by_type
from .dataset_contract_constants import (
    DELETION_STATES, DatasetManifestError, EVIDENCE_ID, PURPOSES, RECEIPT_ID,
    RETENTION_POLICIES, REVOCATION_STATES, SHA, STORAGE_CLASSES,
)


def validate_item_policy(value: dict[str, Any], ctx: dict[str, Any]) -> None:
    where, state, split = ctx["where"], ctx["artifact"], ctx["split"]
    retention = _obj(value["retention"], f"{where}.retention")
    _fields(retention, {"policy", "expiresOn", "storageClass", "deletionRequired", "deletionStatus", "deletionReceiptReference", "deletionReceiptSha256"}, f"{where}.retention")
    policy = _enum(retention["policy"], RETENTION_POLICIES, f"{where}.retention.policy")
    expires = _date(retention["expiresOn"], f"{where}.retention.expiresOn", null=True)
    storage = _enum(retention["storageClass"], STORAGE_CLASSES, f"{where}.retention.storageClass")
    deletion_required = _bool(retention["deletionRequired"], f"{where}.retention.deletionRequired")
    deletion_status = _enum(retention["deletionStatus"], DELETION_STATES, f"{where}.retention.deletionStatus")
    receipt = _match(retention["deletionReceiptReference"], RECEIPT_ID, f"{where}.retention.deletionReceiptReference", null=True)
    receipt_sha = _match(retention["deletionReceiptSha256"], SHA, f"{where}.retention.deletionReceiptSha256", null=True)
    if (policy == "external_until_date") != (expires is not None):
        raise DatasetManifestError(f"{where}.retention expiry does not match policy")
    if state == "metadata_only" and (policy not in {"metadata_only", "prohibited"} or storage != "not_assigned" or deletion_required or deletion_status != "not_required" or receipt is not None or receipt_sha is not None):
        raise DatasetManifestError(f"{where}.retention does not match metadata-only artifact")
    if state == "external_available" and (policy in {"metadata_only", "prohibited"} or storage != "custody_external" or deletion_status not in {"not_required", "pending", "failed"} or receipt is not None or receipt_sha is not None):
        raise DatasetManifestError(f"{where}.retention external artifact has invalid custody/deletion state")
    if state == "revoked" and (not deletion_required or deletion_status != "completed" or receipt is None or receipt_sha is None or storage != "custody_external"):
        raise DatasetManifestError(f"{where}.retention revoked item requires completed deletion receipt")

    revocation = _obj(value["revocation"], f"{where}.revocation")
    _fields(revocation, {"status", "effectiveOn", "reference"}, f"{where}.revocation")
    revocation_status = _enum(revocation["status"], REVOCATION_STATES, f"{where}.revocation.status")
    effective = _date(revocation["effectiveOn"], f"{where}.revocation.effectiveOn", null=True)
    reference = _match(revocation["reference"], EVIDENCE_ID, f"{where}.revocation.reference", null=True)
    if revocation_status == "not_revoked" and (effective is not None or reference is not None):
        raise DatasetManifestError(f"{where}.revocation not_revoked cannot claim evidence")
    if revocation_status != "not_revoked" and (effective is None or reference is None):
        raise DatasetManifestError(f"{where}.revocation active state requires date and evidence")
    if (state == "revoked") != (revocation_status == "completed"):
        raise DatasetManifestError(f"{where}.revocation completed status must match revoked artifact")

    if state == "external_available" and (ctx["rights"] != "approved" or ctx["privacy"] in {"pending", "rejected"}):
        raise DatasetManifestError(f"{where} external artifact requires approved rights and privacy review")

    permissions = _obj(value["permissions"], f"{where}.permissions")
    _fields(permissions, set(PURPOSES), f"{where}.permissions")
    parsed = {purpose: _permission(permissions[purpose], f"{where}.permissions.{purpose}") for purpose in PURPOSES}
    granted = {purpose for purpose, permission in parsed.items() if permission["status"] == "granted"}
    snapshot_grants = granted - {"synthetic_derivation"}
    if split == "unassigned" and granted:
        raise DatasetManifestError(f"{where} unassigned item cannot activate purpose permissions")
    if split == "held_out" and snapshot_grants != {"held_out_evaluation"}:
        raise DatasetManifestError(f"{where} held_out item may grant only held_out_evaluation")
    if split in {"development", "calibration"} and snapshot_grants & {"held_out_evaluation", "model_training"}:
        raise DatasetManifestError(f"{where} {split} item cannot be held-out or training data")
    if split == "training_reserved" and snapshot_grants != {"model_training"}:
        raise DatasetManifestError(f"{where} training_reserved item may grant only model_training")
    if split in {"held_out", "training_reserved"} and "synthetic_derivation" in granted:
        raise DatasetManifestError(f"{where} frozen or training-reserved data cannot enable synthetic derivation")
    if granted and (state != "external_available" or ctx["rights"] != "approved" or ctx["privacy"] in {"pending", "rejected"}):
        raise DatasetManifestError(f"{where} active permission requires rights/privacy-approved external artifact")
    if ctx["privacyClass"] in {"personal", "student"} and granted & {"model_training", "publication", "demonstration", "synthetic_derivation"}:
        raise DatasetManifestError(f"{where} identifiable personal/student data cannot be trained, exported, or derived")
    if ctx["source"] == "user_provided" and "model_training" in granted and ctx["privacyClass"] != "deidentified":
        raise DatasetManifestError(f"{where} user-provided training requires deidentified data")

    for purpose, permission in parsed.items():
        if permission["status"] != "granted":
            continue
        split_rule = _restriction_by_type(permission, "split_allowlist")
        storage_rule = _restriction_by_type(permission, "storage_class_allowlist")
        export_rule = _restriction_by_type(permission, "external_export")
        retention_rule = _restriction_by_type(permission, "retention_not_after")
        if split_rule is not None and split not in split_rule["values"]:
            raise DatasetManifestError(f"{where}.permissions.{purpose} restriction excludes assigned split")
        if storage_rule is not None and storage not in storage_rule["values"]:
            raise DatasetManifestError(f"{where}.permissions.{purpose} restriction excludes storage class")
        if export_rule is not None and export_rule["allowed"] is False and purpose in {"publication", "demonstration"}:
            raise DatasetManifestError(f"{where}.permissions.{purpose} external-export restriction blocks grant")
        if retention_rule is not None:
            maximum = date.fromisoformat(retention_rule["date"])
            if expires is None or expires > maximum:
                raise DatasetManifestError(f"{where}.permissions.{purpose} retention restriction is not enforced")

    ctx["permissions"] = parsed
    ctx["retention"] = {"policy": policy, "storageClass": storage, "expiresOn": expires}
