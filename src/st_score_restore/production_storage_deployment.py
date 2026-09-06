"""Provider-neutral Stage 6 production storage/deployment boundary.

This module does not provision databases, object stores, queues, backup systems,
audit stores or deployment platforms. It validates evidence supplied by a later
approved provider adapter and fails closed when durability, isolation, recovery,
retention or deployment-safety evidence is missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Mapping, Protocol

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class StorageDeploymentError(ValueError):
    """Raised when the production storage/deployment boundary rejects evidence."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class StorageAuditSink(Protocol):
    def record(self, event: Mapping[str, object]) -> bool:
        """Return True only when privacy-safe audit evidence was durably accepted."""


@dataclass
class MemoryStorageAuditSink:
    """Test-only sink; production must supply its separately approved audit store."""

    accept: bool = True
    events: list[dict[str, object]] = field(default_factory=list)

    def record(self, event: Mapping[str, object]) -> bool:
        if not self.accept:
            return False
        self.events.append(dict(event))
        return True


def _audit_or_fail(sink: StorageAuditSink, event: Mapping[str, object]) -> None:
    try:
        accepted = sink.record(event)
    except Exception as exc:  # pragma: no cover - defensive provider boundary
        raise StorageDeploymentError("storage_audit_unavailable", "storage audit dependency failed") from exc
    if accepted is not True:
        raise StorageDeploymentError("storage_audit_unavailable", "storage audit evidence was not accepted")


def _deny(sink: StorageAuditSink, reason_code: str, *, category: str, subject: str) -> None:
    _audit_or_fail(
        sink,
        {
            "event": "storage_deployment_security_decision",
            "category": category,
            "subject": subject,
            "decision": "deny",
            "reason_code": reason_code,
        },
    )
    raise StorageDeploymentError(reason_code, f"storage/deployment policy denied {category}")


def _allow(sink: StorageAuditSink, *, category: str, subject: str, reason_code: str) -> None:
    _audit_or_fail(
        sink,
        {
            "event": "storage_deployment_security_decision",
            "category": category,
            "subject": subject,
            "decision": "allow",
            "reason_code": reason_code,
        },
    )


@dataclass(frozen=True)
class MetadataDatabaseEvidence:
    database_alias: str
    managed_external_service: bool
    encryption_at_rest: bool
    transport_encryption: bool
    transactional_writes: bool
    migration_plan_validated: bool
    backward_compatibility_validated: bool
    rollback_path_validated: bool
    tenant_scope_enforced: bool
    workload_identity_required: bool
    point_in_time_recovery_capable: bool
    schema_version_monotonic: bool


def authorize_metadata_database(evidence: MetadataDatabaseEvidence, *, audit_sink: StorageAuditSink) -> None:
    checks = {
        "managed_external_service": evidence.managed_external_service,
        "encryption_at_rest": evidence.encryption_at_rest,
        "transport_encryption": evidence.transport_encryption,
        "transactional_writes": evidence.transactional_writes,
        "migration_plan_validated": evidence.migration_plan_validated,
        "backward_compatibility_validated": evidence.backward_compatibility_validated,
        "rollback_path_validated": evidence.rollback_path_validated,
        "tenant_scope_enforced": evidence.tenant_scope_enforced,
        "workload_identity_required": evidence.workload_identity_required,
        "point_in_time_recovery_capable": evidence.point_in_time_recovery_capable,
        "schema_version_monotonic": evidence.schema_version_monotonic,
    }
    if not evidence.database_alias.strip():
        _deny(audit_sink, "database_alias_missing", category="metadata_database", subject="unknown")
    for name, passed in checks.items():
        if passed is not True:
            _deny(audit_sink, f"database_evidence_missing:{name}", category="metadata_database", subject=evidence.database_alias)
    _allow(audit_sink, category="metadata_database", subject=evidence.database_alias, reason_code="database_contract_satisfied")


@dataclass(frozen=True)
class ObjectStorageEvidence:
    bucket_alias: str
    encrypted_at_rest: bool
    kms_or_equivalent_key_separation: bool
    transport_encryption: bool
    content_address_integrity: bool
    tenant_namespace_enforced: bool
    versioning_or_equivalent_recovery: bool
    lifecycle_policy_bound: bool
    public_access_blocked: bool
    workload_identity_required: bool


def authorize_object_storage(evidence: ObjectStorageEvidence, *, audit_sink: StorageAuditSink) -> None:
    checks = {
        "encrypted_at_rest": evidence.encrypted_at_rest,
        "kms_or_equivalent_key_separation": evidence.kms_or_equivalent_key_separation,
        "transport_encryption": evidence.transport_encryption,
        "content_address_integrity": evidence.content_address_integrity,
        "tenant_namespace_enforced": evidence.tenant_namespace_enforced,
        "versioning_or_equivalent_recovery": evidence.versioning_or_equivalent_recovery,
        "lifecycle_policy_bound": evidence.lifecycle_policy_bound,
        "public_access_blocked": evidence.public_access_blocked,
        "workload_identity_required": evidence.workload_identity_required,
    }
    if not evidence.bucket_alias.strip():
        _deny(audit_sink, "object_store_alias_missing", category="object_storage", subject="unknown")
    for name, passed in checks.items():
        if passed is not True:
            _deny(audit_sink, f"object_storage_evidence_missing:{name}", category="object_storage", subject=evidence.bucket_alias)
    _allow(audit_sink, category="object_storage", subject=evidence.bucket_alias, reason_code="object_storage_contract_satisfied")


@dataclass(frozen=True)
class QueueClaimEvidence:
    queue_alias: str
    job_id: str
    lease_token: str
    fencing_token: int
    idempotency_digest: str
    durable_broker: bool
    worker_identity_authenticated: bool
    lease_expiry_persisted: bool
    state_transition_committed_before_ack: bool
    redelivery_supported: bool


@dataclass(frozen=True)
class FencedQueueClaim:
    queue_alias: str
    job_id: str
    lease_token: str
    fencing_token: int
    idempotency_digest: str


def authorize_queue_claim(
    evidence: QueueClaimEvidence,
    *,
    previous_fencing_token: int,
    audit_sink: StorageAuditSink,
) -> FencedQueueClaim:
    subject = evidence.job_id or "unknown"
    if not evidence.queue_alias.strip() or not evidence.job_id.strip() or not evidence.lease_token.strip():
        _deny(audit_sink, "queue_claim_identity_missing", category="queue_claim", subject=subject)
    if evidence.fencing_token <= previous_fencing_token or evidence.fencing_token < 1:
        _deny(audit_sink, "stale_or_invalid_fencing_token", category="queue_claim", subject=subject)
    if not _SHA256_RE.fullmatch(evidence.idempotency_digest):
        _deny(audit_sink, "idempotency_digest_invalid", category="queue_claim", subject=subject)
    checks = {
        "durable_broker": evidence.durable_broker,
        "worker_identity_authenticated": evidence.worker_identity_authenticated,
        "lease_expiry_persisted": evidence.lease_expiry_persisted,
        "state_transition_committed_before_ack": evidence.state_transition_committed_before_ack,
        "redelivery_supported": evidence.redelivery_supported,
    }
    for name, passed in checks.items():
        if passed is not True:
            _deny(audit_sink, f"queue_evidence_missing:{name}", category="queue_claim", subject=subject)
    _allow(audit_sink, category="queue_claim", subject=subject, reason_code="fenced_durable_claim_allowed")
    return FencedQueueClaim(
        queue_alias=evidence.queue_alias,
        job_id=evidence.job_id,
        lease_token=evidence.lease_token,
        fencing_token=evidence.fencing_token,
        idempotency_digest=evidence.idempotency_digest,
    )


@dataclass(frozen=True)
class CrashRecoveryEvidence:
    operation_id: str
    metadata_commit_atomic: bool
    artifact_commit_integrity_verified: bool
    queue_ack_after_commit: bool
    replay_idempotent: bool
    partial_write_cleanup_verified: bool
    stale_worker_fenced: bool


def authorize_crash_recovery(evidence: CrashRecoveryEvidence, *, audit_sink: StorageAuditSink) -> None:
    for name in (
        "metadata_commit_atomic",
        "artifact_commit_integrity_verified",
        "queue_ack_after_commit",
        "replay_idempotent",
        "partial_write_cleanup_verified",
        "stale_worker_fenced",
    ):
        if getattr(evidence, name) is not True:
            _deny(audit_sink, f"crash_recovery_evidence_missing:{name}", category="crash_recovery", subject=evidence.operation_id)
    _allow(audit_sink, category="crash_recovery", subject=evidence.operation_id, reason_code="crash_recovery_contract_satisfied")


@dataclass(frozen=True)
class DeletionReceiptEvidence:
    deletion_id: str
    intent_receipt_persisted: bool
    live_references_removed: bool
    object_delete_confirmed: bool
    metadata_tombstone_persisted: bool
    backup_tombstone_propagated: bool
    completion_receipt_persisted: bool
    restore_resurrection_prevented: bool


def authorize_deletion_completion(evidence: DeletionReceiptEvidence, *, audit_sink: StorageAuditSink) -> None:
    for name in (
        "intent_receipt_persisted",
        "live_references_removed",
        "object_delete_confirmed",
        "metadata_tombstone_persisted",
        "backup_tombstone_propagated",
        "completion_receipt_persisted",
        "restore_resurrection_prevented",
    ):
        if getattr(evidence, name) is not True:
            _deny(audit_sink, f"deletion_evidence_missing:{name}", category="deletion", subject=evidence.deletion_id)
    _allow(audit_sink, category="deletion", subject=evidence.deletion_id, reason_code="two_stage_deletion_complete")


@dataclass(frozen=True)
class BackupRestoreEvidence:
    backup_id: str
    encrypted: bool
    integrity_manifest_verified: bool
    isolated_restore_target: bool
    database_and_object_generation_consistent: bool
    tombstones_replayed_before_publish: bool
    deleted_data_resurrection_check_passed: bool
    recovery_point_verified: bool
    restore_audit_committed: bool


def authorize_restore_publish(evidence: BackupRestoreEvidence, *, audit_sink: StorageAuditSink) -> None:
    for name in (
        "encrypted",
        "integrity_manifest_verified",
        "isolated_restore_target",
        "database_and_object_generation_consistent",
        "tombstones_replayed_before_publish",
        "deleted_data_resurrection_check_passed",
        "recovery_point_verified",
        "restore_audit_committed",
    ):
        if getattr(evidence, name) is not True:
            _deny(audit_sink, f"restore_evidence_missing:{name}", category="restore", subject=evidence.backup_id)
    _allow(audit_sink, category="restore", subject=evidence.backup_id, reason_code="restore_publish_allowed")


@dataclass(frozen=True)
class AuditStoreEvidence:
    store_alias: str
    append_only: bool
    hash_chain_validated: bool
    independent_anti_rollback_anchor: bool
    immutable_retention: bool
    tenant_scope_enforced: bool
    workload_identity_required: bool
    privacy_safe_payload_policy: bool


def authorize_audit_store(evidence: AuditStoreEvidence, *, audit_sink: StorageAuditSink) -> None:
    for name in (
        "append_only",
        "hash_chain_validated",
        "independent_anti_rollback_anchor",
        "immutable_retention",
        "tenant_scope_enforced",
        "workload_identity_required",
        "privacy_safe_payload_policy",
    ):
        if getattr(evidence, name) is not True:
            _deny(audit_sink, f"audit_store_evidence_missing:{name}", category="audit_store", subject=evidence.store_alias)
    _allow(audit_sink, category="audit_store", subject=evidence.store_alias, reason_code="tamper_evident_audit_contract_satisfied")


@dataclass(frozen=True)
class EnvironmentIsolationEvidence:
    environment: str
    account_or_project_isolated: bool
    credentials_isolated: bool
    network_namespace_isolated: bool
    storage_namespace_isolated: bool
    queue_namespace_isolated: bool
    audit_namespace_isolated: bool
    cross_environment_write_forbidden: bool


def authorize_environment_isolation(evidence: EnvironmentIsolationEvidence, *, audit_sink: StorageAuditSink) -> None:
    if evidence.environment not in {"development", "staging", "production"}:
        _deny(audit_sink, "environment_invalid", category="environment_isolation", subject=evidence.environment)
    for name in (
        "account_or_project_isolated",
        "credentials_isolated",
        "network_namespace_isolated",
        "storage_namespace_isolated",
        "queue_namespace_isolated",
        "audit_namespace_isolated",
        "cross_environment_write_forbidden",
    ):
        if getattr(evidence, name) is not True:
            _deny(audit_sink, f"environment_isolation_missing:{name}", category="environment_isolation", subject=evidence.environment)
    _allow(audit_sink, category="environment_isolation", subject=evidence.environment, reason_code="environment_isolation_satisfied")


@dataclass(frozen=True)
class DeploymentCandidateEvidence:
    artifact_digest: str
    rollback_artifact_digest: str
    provenance_signed: bool
    artifact_signature_verified: bool
    immutable_artifact: bool
    staging_health_checks_passed: bool
    migration_preflight_passed: bool
    rollback_path_validated: bool
    secrets_not_baked_into_artifact: bool
    environment_config_separated: bool
    privacy_safe_observability_ready: bool
    production_activation_requested: bool = False


def authorize_deployment_candidate(
    evidence: DeploymentCandidateEvidence,
    *,
    production_deployment_authorized: bool,
    audit_sink: StorageAuditSink,
) -> None:
    if not _IMAGE_DIGEST_RE.fullmatch(evidence.artifact_digest):
        _deny(audit_sink, "deployment_artifact_digest_invalid", category="deployment_candidate", subject="artifact")
    if not _IMAGE_DIGEST_RE.fullmatch(evidence.rollback_artifact_digest):
        _deny(audit_sink, "rollback_artifact_digest_invalid", category="deployment_candidate", subject=evidence.artifact_digest)
    if evidence.production_activation_requested and not production_deployment_authorized:
        _deny(audit_sink, "production_deployment_not_authorized", category="deployment_candidate", subject=evidence.artifact_digest)
    for name in (
        "provenance_signed",
        "artifact_signature_verified",
        "immutable_artifact",
        "staging_health_checks_passed",
        "migration_preflight_passed",
        "rollback_path_validated",
        "secrets_not_baked_into_artifact",
        "environment_config_separated",
        "privacy_safe_observability_ready",
    ):
        if getattr(evidence, name) is not True:
            _deny(audit_sink, f"deployment_evidence_missing:{name}", category="deployment_candidate", subject=evidence.artifact_digest)
    _allow(audit_sink, category="deployment_candidate", subject=evidence.artifact_digest, reason_code="deployment_candidate_contract_satisfied")


__all__ = [
    "AuditStoreEvidence",
    "BackupRestoreEvidence",
    "CrashRecoveryEvidence",
    "DeletionReceiptEvidence",
    "DeploymentCandidateEvidence",
    "EnvironmentIsolationEvidence",
    "FencedQueueClaim",
    "MemoryStorageAuditSink",
    "MetadataDatabaseEvidence",
    "ObjectStorageEvidence",
    "QueueClaimEvidence",
    "StorageAuditSink",
    "StorageDeploymentError",
    "authorize_audit_store",
    "authorize_crash_recovery",
    "authorize_deletion_completion",
    "authorize_deployment_candidate",
    "authorize_environment_isolation",
    "authorize_metadata_database",
    "authorize_object_storage",
    "authorize_queue_claim",
    "authorize_restore_publish",
]
