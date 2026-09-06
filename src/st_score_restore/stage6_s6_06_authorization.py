"""Validation for the Stage 6 S6-06 storage/deployment implementation authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_PATH = Path("evidence/stage6/governance/stage6-s6-06-storage-deployment-authorization.v1.json")
AUTHORIZATION_ID = "stage6.s6-06.storage-deployment-implementation-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_S6_06_STORAGE_DEPLOYMENT_IMPLEMENTATION"
EXPECTED_ENTRY_MAIN_SHA = "852e712f0503a594eddb40525b8ac9b76c5939e3"
EXPECTED_S6_05_AUTHORIZATION_DIGEST = "6815772f8f393b2bf281c75cb4500035808ec7ee5dc083d822dcefca1db9716c"
EXPECTED_CANONICAL_SHA256 = "dd31e0460352128ba2ed63e0207e506a305e83fb6b462156cdaa2c9651021a10"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_07_synthetic_operational_drills_authorization"


class Stage6S606AuthorizationError(ValueError):
    pass


def canonical_sha256(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage6_s6_06_authorization(data: Any) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise Stage6S606AuthorizationError("authorization must be a JSON object")
    record = dict(data)
    required_equal = {
        "schema_version": "1.0.0",
        "project": "ST Score Restore API / ST Score Restore Engine",
        "repository": "khfy7wpr5p-maker/st-score-restore-engine",
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorized_on": "2026-09-06",
        "authorization_source_code": "explicit_user_authorization",
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }
    for key, expected in required_equal.items():
        if record.get(key) != expected:
            raise Stage6S606AuthorizationError(f"{key} must equal {expected!r}")

    entry = record.get("entry_checkpoint")
    if not isinstance(entry, Mapping):
        raise Stage6S606AuthorizationError("entry_checkpoint must be an object")
    if entry.get("main_sha") != EXPECTED_ENTRY_MAIN_SHA:
        raise Stage6S606AuthorizationError("entry checkpoint must bind the approved main SHA")
    if entry.get("s6_05_authorization_digest") != EXPECTED_S6_05_AUTHORIZATION_DIGEST:
        raise Stage6S606AuthorizationError("entry checkpoint must bind the S6-05 authorization digest")
    if entry.get("ci_status") != "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows":
        raise Stage6S606AuthorizationError("entry checkpoint must bind successful post-merge CI")

    scope = record.get("authorized_scope")
    required_true = {
        "provider_neutral_metadata_database_contract",
        "migration_compatibility_and_rollback_contract",
        "encrypted_object_storage_contract",
        "content_integrity_and_tenant_scoping_contract",
        "external_durable_queue_contract",
        "lease_fencing_and_idempotency_contract",
        "crash_recovery_state_transition_contract",
        "retention_and_two_stage_deletion_receipt_contract",
        "backup_restore_and_anti_resurrection_contract",
        "durable_append_only_tamper_evident_audit_contract",
        "immutable_deployment_artifact_and_provenance_contract",
        "staging_health_rollback_and_incident_contract",
        "environment_and_tenant_isolation_contract",
        "privacy_safe_observability_contract",
    }
    if not isinstance(scope, Mapping):
        raise Stage6S606AuthorizationError("authorized_scope must be an object")
    for key in required_true:
        if scope.get(key) is not True:
            raise Stage6S606AuthorizationError(f"authorized_scope.{key} must be true")

    denied = record.get("explicitly_not_authorized")
    if not isinstance(denied, Mapping) or not denied:
        raise Stage6S606AuthorizationError("explicitly_not_authorized must be a non-empty object")
    if any(value is not False for value in denied.values()):
        raise Stage6S606AuthorizationError("all explicitly_not_authorized values must remain false")

    safety = record.get("safety_assertions")
    if not isinstance(safety, Mapping):
        raise Stage6S606AuthorizationError("safety_assertions must be an object")
    for key in (
        "historical_evidence_immutable",
        "provider_remains_unselected",
        "local_sqlite_remains_non_production_baseline",
        "storage_queue_audit_dependency_failure_fails_closed",
        "backup_restore_must_prevent_deleted_data_resurrection",
    ):
        if safety.get(key) is not True:
            raise Stage6S606AuthorizationError(f"safety_assertions.{key} must be true")
    for key in (
        "raw_secrets_or_key_material_in_ordinary_git",
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
    ):
        if safety.get(key) is not False:
            raise Stage6S606AuthorizationError(f"safety_assertions.{key} must be false")

    if canonical_sha256(record) != EXPECTED_CANONICAL_SHA256:
        raise Stage6S606AuthorizationError("authorization canonical digest changed")
    return record


def load_and_validate(path: Path = AUTHORIZATION_PATH) -> dict[str, Any]:
    return validate_stage6_s6_06_authorization(json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "EXPECTED_CANONICAL_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage6S606AuthorizationError",
    "canonical_sha256",
    "load_and_validate",
    "validate_stage6_s6_06_authorization",
]
