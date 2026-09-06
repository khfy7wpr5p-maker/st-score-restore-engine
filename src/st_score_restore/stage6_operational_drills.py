"""Synthetic-only Stage 6 operational safety and recovery drills.

The drills are deterministic, bounded, in-memory exercises. They do not call a
cloud/provider API, create live resources, read real corpus bytes, mutate
production state, or authorize production deployment.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from typing import Callable

from .production_storage_deployment import (
    BackupRestoreEvidence,
    CrashRecoveryEvidence,
    DeletionReceiptEvidence,
    DeploymentCandidateEvidence,
    MemoryStorageAuditSink,
    QueueClaimEvidence,
    StorageDeploymentError,
    authorize_crash_recovery,
    authorize_deletion_completion,
    authorize_deployment_candidate,
    authorize_queue_claim,
    authorize_restore_publish,
)

_SYNTHETIC_DIGEST = "a" * 64
_SYNTHETIC_IMAGE = "sha256:" + ("b" * 64)
_SYNTHETIC_ROLLBACK_IMAGE = "sha256:" + ("c" * 64)


class OperationalDrillError(RuntimeError):
    pass


@dataclass(frozen=True)
class DrillResult:
    name: str
    passed: bool
    assertions: tuple[str, ...]
    audit_events: int = 0
    operations: int = 0


@dataclass(frozen=True)
class SyntheticOperationalDrillReport:
    schema_version: str
    synthetic_only: bool
    provider_calls_performed: bool
    production_state_mutated: bool
    production_deployment_performed: bool
    results: tuple[DrillResult, ...]

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(result.passed for result in self.results)

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": self.schema_version,
            "syntheticOnly": self.synthetic_only,
            "providerCallsPerformed": self.provider_calls_performed,
            "productionStateMutated": self.production_state_mutated,
            "productionDeploymentPerformed": self.production_deployment_performed,
            "passed": self.passed,
            "results": [
                {
                    "name": result.name,
                    "passed": result.passed,
                    "assertions": list(result.assertions),
                    "auditEvents": result.audit_events,
                    "operations": result.operations,
                }
                for result in self.results
            ],
        }


class _FencingLedger:
    def __init__(self) -> None:
        self._lock = Lock()
        self.highest = 0
        self.accepted: list[int] = []

    def claim(self, token: int) -> bool:
        with self._lock:
            if token <= self.highest:
                return False
            self.highest = token
            self.accepted.append(token)
            return True


class _IdempotencyLedger:
    def __init__(self) -> None:
        self._lock = Lock()
        self._committed: set[str] = set()

    def commit_once(self, digest: str) -> bool:
        with self._lock:
            if digest in self._committed:
                return False
            self._committed.add(digest)
            return True


def _expect_denial(action: Callable[[], object], reason_code: str) -> bool:
    try:
        action()
    except StorageDeploymentError as exc:
        return exc.reason_code == reason_code
    return False


def _valid_crash_evidence() -> CrashRecoveryEvidence:
    return CrashRecoveryEvidence(
        operation_id="synthetic-op-1",
        metadata_commit_atomic=True,
        artifact_commit_integrity_verified=True,
        queue_ack_after_commit=True,
        replay_idempotent=True,
        partial_write_cleanup_verified=True,
        stale_worker_fenced=True,
    )


def _valid_deletion_evidence() -> DeletionReceiptEvidence:
    return DeletionReceiptEvidence(
        deletion_id="synthetic-delete-1",
        intent_receipt_persisted=True,
        live_references_removed=True,
        object_delete_confirmed=True,
        metadata_tombstone_persisted=True,
        backup_tombstone_propagated=True,
        completion_receipt_persisted=True,
        restore_resurrection_prevented=True,
    )


def _valid_restore_evidence() -> BackupRestoreEvidence:
    return BackupRestoreEvidence(
        backup_id="synthetic-backup-1",
        encrypted=True,
        integrity_manifest_verified=True,
        isolated_restore_target=True,
        database_and_object_generation_consistent=True,
        tombstones_replayed_before_publish=True,
        deleted_data_resurrection_check_passed=True,
        recovery_point_verified=True,
        restore_audit_committed=True,
    )


def _valid_deployment_candidate(*, production_activation_requested: bool = False) -> DeploymentCandidateEvidence:
    return DeploymentCandidateEvidence(
        artifact_digest=_SYNTHETIC_IMAGE,
        rollback_artifact_digest=_SYNTHETIC_ROLLBACK_IMAGE,
        provenance_signed=True,
        artifact_signature_verified=True,
        immutable_artifact=True,
        staging_health_checks_passed=True,
        migration_preflight_passed=True,
        rollback_path_validated=True,
        secrets_not_baked_into_artifact=True,
        environment_config_separated=True,
        privacy_safe_observability_ready=True,
        production_activation_requested=production_activation_requested,
    )


def _drill_queue_redelivery_and_fencing() -> DrillResult:
    sink = MemoryStorageAuditSink()
    first = authorize_queue_claim(
        QueueClaimEvidence(
            queue_alias="synthetic-queue",
            job_id="synthetic-job",
            lease_token="lease-7",
            fencing_token=7,
            idempotency_digest=_SYNTHETIC_DIGEST,
            durable_broker=True,
            worker_identity_authenticated=True,
            lease_expiry_persisted=True,
            state_transition_committed_before_ack=True,
            redelivery_supported=True,
        ),
        previous_fencing_token=6,
        audit_sink=sink,
    )
    stale_rejected = _expect_denial(
        lambda: authorize_queue_claim(
            QueueClaimEvidence(
                queue_alias="synthetic-queue",
                job_id="synthetic-job",
                lease_token="lease-stale",
                fencing_token=7,
                idempotency_digest=_SYNTHETIC_DIGEST,
                durable_broker=True,
                worker_identity_authenticated=True,
                lease_expiry_persisted=True,
                state_transition_committed_before_ack=True,
                redelivery_supported=True,
            ),
            previous_fencing_token=7,
            audit_sink=sink,
        ),
        "stale_or_invalid_fencing_token",
    )
    redelivery = authorize_queue_claim(
        QueueClaimEvidence(
            queue_alias="synthetic-queue",
            job_id="synthetic-job",
            lease_token="lease-8",
            fencing_token=8,
            idempotency_digest=_SYNTHETIC_DIGEST,
            durable_broker=True,
            worker_identity_authenticated=True,
            lease_expiry_persisted=True,
            state_transition_committed_before_ack=True,
            redelivery_supported=True,
        ),
        previous_fencing_token=7,
        audit_sink=sink,
    )
    passed = first.fencing_token == 7 and redelivery.fencing_token == 8 and stale_rejected
    return DrillResult(
        name="queue_redelivery_and_stale_worker_fencing",
        passed=passed,
        assertions=("monotonic_fencing", "stale_claim_denied", "redelivery_allowed"),
        audit_events=len(sink.events),
        operations=3,
    )


def _drill_crash_recovery_and_replay() -> DrillResult:
    sink = MemoryStorageAuditSink()
    authorize_crash_recovery(_valid_crash_evidence(), audit_sink=sink)
    broken = CrashRecoveryEvidence(
        operation_id="synthetic-op-broken",
        metadata_commit_atomic=True,
        artifact_commit_integrity_verified=True,
        queue_ack_after_commit=True,
        replay_idempotent=True,
        partial_write_cleanup_verified=False,
        stale_worker_fenced=True,
    )
    partial_write_rejected = _expect_denial(
        lambda: authorize_crash_recovery(broken, audit_sink=sink),
        "crash_recovery_evidence_missing:partial_write_cleanup_verified",
    )
    return DrillResult(
        name="crash_recovery_and_idempotent_replay",
        passed=partial_write_rejected,
        assertions=("atomic_commit", "commit_before_ack", "idempotent_replay", "partial_write_fail_closed"),
        audit_events=len(sink.events),
        operations=2,
    )


def _drill_deletion_restore_anti_resurrection() -> DrillResult:
    sink = MemoryStorageAuditSink()
    authorize_deletion_completion(_valid_deletion_evidence(), audit_sink=sink)
    authorize_restore_publish(_valid_restore_evidence(), audit_sink=sink)
    unsafe_restore = BackupRestoreEvidence(
        backup_id="synthetic-backup-unsafe",
        encrypted=True,
        integrity_manifest_verified=True,
        isolated_restore_target=True,
        database_and_object_generation_consistent=True,
        tombstones_replayed_before_publish=True,
        deleted_data_resurrection_check_passed=False,
        recovery_point_verified=True,
        restore_audit_committed=True,
    )
    resurrection_rejected = _expect_denial(
        lambda: authorize_restore_publish(unsafe_restore, audit_sink=sink),
        "restore_evidence_missing:deleted_data_resurrection_check_passed",
    )
    return DrillResult(
        name="deletion_restore_anti_resurrection",
        passed=resurrection_rejected,
        assertions=("two_stage_deletion", "tombstone_replay", "resurrection_rejected"),
        audit_events=len(sink.events),
        operations=3,
    )


def _drill_audit_dependency_fail_closed() -> DrillResult:
    sink = MemoryStorageAuditSink(accept=False)
    blocked = _expect_denial(
        lambda: authorize_deletion_completion(_valid_deletion_evidence(), audit_sink=sink),
        "storage_audit_unavailable",
    )
    return DrillResult(
        name="audit_dependency_fail_closed",
        passed=blocked,
        assertions=("sensitive_operation_blocked_when_audit_unavailable",),
        audit_events=len(sink.events),
        operations=1,
    )


def _drill_deployment_candidate_and_rollback_gate() -> DrillResult:
    sink = MemoryStorageAuditSink()
    authorize_deployment_candidate(
        _valid_deployment_candidate(production_activation_requested=False),
        production_deployment_authorized=False,
        audit_sink=sink,
    )
    activation_blocked = _expect_denial(
        lambda: authorize_deployment_candidate(
            _valid_deployment_candidate(production_activation_requested=True),
            production_deployment_authorized=False,
            audit_sink=sink,
        ),
        "production_deployment_not_authorized",
    )
    bad_rollback = DeploymentCandidateEvidence(
        artifact_digest=_SYNTHETIC_IMAGE,
        rollback_artifact_digest=_SYNTHETIC_ROLLBACK_IMAGE,
        provenance_signed=True,
        artifact_signature_verified=True,
        immutable_artifact=True,
        staging_health_checks_passed=True,
        migration_preflight_passed=True,
        rollback_path_validated=False,
        secrets_not_baked_into_artifact=True,
        environment_config_separated=True,
        privacy_safe_observability_ready=True,
        production_activation_requested=False,
    )
    rollback_gap_blocked = _expect_denial(
        lambda: authorize_deployment_candidate(
            bad_rollback,
            production_deployment_authorized=False,
            audit_sink=sink,
        ),
        "deployment_evidence_missing:rollback_path_validated",
    )
    return DrillResult(
        name="deployment_candidate_and_rollback_gate",
        passed=activation_blocked and rollback_gap_blocked,
        assertions=("candidate_allowed_without_activation", "production_activation_blocked", "rollback_gap_blocked"),
        audit_events=len(sink.events),
        operations=3,
    )


def _drill_bounded_concurrency_and_idempotency() -> DrillResult:
    fencing = _FencingLedger()
    idempotency = _IdempotencyLedger()
    tokens = tuple(range(1, 17)) + tuple(range(1, 17))
    digests = tuple([_SYNTHETIC_DIGEST] * 32)
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="s6-07-synthetic") as pool:
        fencing_results = list(pool.map(fencing.claim, tokens))
        idempotency_results = list(pool.map(idempotency.commit_once, digests))
    accepted = fencing.accepted
    monotonic = accepted == sorted(set(accepted)) and all(a < b for a, b in zip(accepted, accepted[1:]))
    passed = (
        fencing.highest == 16
        and monotonic
        and sum(1 for value in idempotency_results if value) == 1
        and any(not value for value in fencing_results)
    )
    return DrillResult(
        name="bounded_concurrency_and_idempotency_stress",
        passed=passed,
        assertions=("highest_fencing_token_wins", "duplicate_tokens_rejected", "idempotent_commit_once"),
        operations=len(tokens) + len(digests),
    )


def run_synthetic_operational_drills() -> SyntheticOperationalDrillReport:
    report = SyntheticOperationalDrillReport(
        schema_version="1.0.0",
        synthetic_only=True,
        provider_calls_performed=False,
        production_state_mutated=False,
        production_deployment_performed=False,
        results=(
            _drill_queue_redelivery_and_fencing(),
            _drill_crash_recovery_and_replay(),
            _drill_deletion_restore_anti_resurrection(),
            _drill_audit_dependency_fail_closed(),
            _drill_deployment_candidate_and_rollback_gate(),
            _drill_bounded_concurrency_and_idempotency(),
        ),
    )
    validate_synthetic_operational_drill_report(report)
    return report


def validate_synthetic_operational_drill_report(report: SyntheticOperationalDrillReport) -> None:
    if report.schema_version != "1.0.0":
        raise OperationalDrillError("synthetic drill schema drifted")
    if report.synthetic_only is not True:
        raise OperationalDrillError("S6-07 drills must remain synthetic-only")
    if report.provider_calls_performed or report.production_state_mutated or report.production_deployment_performed:
        raise OperationalDrillError("S6-07 crossed a live-production boundary")
    expected_names = (
        "queue_redelivery_and_stale_worker_fencing",
        "crash_recovery_and_idempotent_replay",
        "deletion_restore_anti_resurrection",
        "audit_dependency_fail_closed",
        "deployment_candidate_and_rollback_gate",
        "bounded_concurrency_and_idempotency_stress",
    )
    if tuple(result.name for result in report.results) != expected_names:
        raise OperationalDrillError("synthetic drill inventory drifted")
    failed = [result.name for result in report.results if result.passed is not True]
    if failed:
        raise OperationalDrillError("synthetic operational drills failed: " + ", ".join(failed))


__all__ = [
    "DrillResult",
    "OperationalDrillError",
    "SyntheticOperationalDrillReport",
    "run_synthetic_operational_drills",
    "validate_synthetic_operational_drill_report",
]
