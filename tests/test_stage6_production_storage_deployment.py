from __future__ import annotations

from dataclasses import replace
import unittest

from st_score_restore.production_storage_deployment import (
    AuditStoreEvidence,
    BackupRestoreEvidence,
    CrashRecoveryEvidence,
    DeletionReceiptEvidence,
    DeploymentCandidateEvidence,
    EnvironmentIsolationEvidence,
    MemoryStorageAuditSink,
    MetadataDatabaseEvidence,
    ObjectStorageEvidence,
    QueueClaimEvidence,
    StorageDeploymentError,
    authorize_audit_store,
    authorize_crash_recovery,
    authorize_deletion_completion,
    authorize_deployment_candidate,
    authorize_environment_isolation,
    authorize_metadata_database,
    authorize_object_storage,
    authorize_queue_claim,
    authorize_restore_publish,
)

HEX_A = "a" * 64
HEX_B = "b" * 64


class ProductionStorageDeploymentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = MemoryStorageAuditSink()

    def test_metadata_database_requires_full_durability_and_isolation_evidence(self) -> None:
        evidence = MetadataDatabaseEvidence(
            database_alias="metadata-primary",
            managed_external_service=True,
            encryption_at_rest=True,
            transport_encryption=True,
            transactional_writes=True,
            migration_plan_validated=True,
            backward_compatibility_validated=True,
            rollback_path_validated=True,
            tenant_scope_enforced=True,
            workload_identity_required=True,
            point_in_time_recovery_capable=True,
            schema_version_monotonic=True,
        )
        authorize_metadata_database(evidence, audit_sink=self.audit)
        with self.assertRaisesRegex(StorageDeploymentError, "metadata_database"):
            authorize_metadata_database(replace(evidence, tenant_scope_enforced=False), audit_sink=self.audit)

    def test_object_storage_requires_encryption_integrity_lifecycle_and_no_public_access(self) -> None:
        evidence = ObjectStorageEvidence(
            bucket_alias="artifacts-primary",
            encrypted_at_rest=True,
            kms_or_equivalent_key_separation=True,
            transport_encryption=True,
            content_address_integrity=True,
            tenant_namespace_enforced=True,
            versioning_or_equivalent_recovery=True,
            lifecycle_policy_bound=True,
            public_access_blocked=True,
            workload_identity_required=True,
        )
        authorize_object_storage(evidence, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_object_storage(replace(evidence, public_access_blocked=False), audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "object_storage_evidence_missing:public_access_blocked")

    def test_queue_claim_requires_new_fence_and_valid_idempotency_digest(self) -> None:
        evidence = QueueClaimEvidence(
            queue_alias="jobs-primary",
            job_id="job-123",
            lease_token="opaque-lease",
            fencing_token=8,
            idempotency_digest=HEX_A,
            durable_broker=True,
            worker_identity_authenticated=True,
            lease_expiry_persisted=True,
            state_transition_committed_before_ack=True,
            redelivery_supported=True,
        )
        claim = authorize_queue_claim(evidence, previous_fencing_token=7, audit_sink=self.audit)
        self.assertEqual(claim.fencing_token, 8)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_queue_claim(replace(evidence, fencing_token=7), previous_fencing_token=7, audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "stale_or_invalid_fencing_token")
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_queue_claim(replace(evidence, idempotency_digest="not-a-digest"), previous_fencing_token=7, audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "idempotency_digest_invalid")

    def test_queue_ack_before_commit_is_rejected(self) -> None:
        evidence = QueueClaimEvidence(
            queue_alias="jobs-primary",
            job_id="job-123",
            lease_token="opaque-lease",
            fencing_token=2,
            idempotency_digest=HEX_A,
            durable_broker=True,
            worker_identity_authenticated=True,
            lease_expiry_persisted=True,
            state_transition_committed_before_ack=False,
            redelivery_supported=True,
        )
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_queue_claim(evidence, previous_fencing_token=1, audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "queue_evidence_missing:state_transition_committed_before_ack")

    def test_crash_recovery_requires_replay_cleanup_and_stale_worker_fencing(self) -> None:
        evidence = CrashRecoveryEvidence(
            operation_id="op-1",
            metadata_commit_atomic=True,
            artifact_commit_integrity_verified=True,
            queue_ack_after_commit=True,
            replay_idempotent=True,
            partial_write_cleanup_verified=True,
            stale_worker_fenced=True,
        )
        authorize_crash_recovery(evidence, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_crash_recovery(replace(evidence, stale_worker_fenced=False), audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "crash_recovery_evidence_missing:stale_worker_fenced")

    def test_two_stage_deletion_requires_backup_tombstone_and_anti_resurrection(self) -> None:
        evidence = DeletionReceiptEvidence(
            deletion_id="delete-1",
            intent_receipt_persisted=True,
            live_references_removed=True,
            object_delete_confirmed=True,
            metadata_tombstone_persisted=True,
            backup_tombstone_propagated=True,
            completion_receipt_persisted=True,
            restore_resurrection_prevented=True,
        )
        authorize_deletion_completion(evidence, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_deletion_completion(replace(evidence, backup_tombstone_propagated=False), audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "deletion_evidence_missing:backup_tombstone_propagated")

    def test_restore_publish_fails_if_deleted_data_can_resurrect(self) -> None:
        evidence = BackupRestoreEvidence(
            backup_id="backup-1",
            encrypted=True,
            integrity_manifest_verified=True,
            isolated_restore_target=True,
            database_and_object_generation_consistent=True,
            tombstones_replayed_before_publish=True,
            deleted_data_resurrection_check_passed=True,
            recovery_point_verified=True,
            restore_audit_committed=True,
        )
        authorize_restore_publish(evidence, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_restore_publish(replace(evidence, deleted_data_resurrection_check_passed=False), audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "restore_evidence_missing:deleted_data_resurrection_check_passed")

    def test_audit_store_requires_independent_anti_rollback_anchor(self) -> None:
        evidence = AuditStoreEvidence(
            store_alias="audit-primary",
            append_only=True,
            hash_chain_validated=True,
            independent_anti_rollback_anchor=True,
            immutable_retention=True,
            tenant_scope_enforced=True,
            workload_identity_required=True,
            privacy_safe_payload_policy=True,
        )
        authorize_audit_store(evidence, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_audit_store(replace(evidence, independent_anti_rollback_anchor=False), audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "audit_store_evidence_missing:independent_anti_rollback_anchor")

    def test_environment_isolation_is_deny_by_default(self) -> None:
        evidence = EnvironmentIsolationEvidence(
            environment="production",
            account_or_project_isolated=True,
            credentials_isolated=True,
            network_namespace_isolated=True,
            storage_namespace_isolated=True,
            queue_namespace_isolated=True,
            audit_namespace_isolated=True,
            cross_environment_write_forbidden=True,
        )
        authorize_environment_isolation(evidence, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_environment_isolation(replace(evidence, credentials_isolated=False), audit_sink=self.audit)
        self.assertEqual(ctx.exception.reason_code, "environment_isolation_missing:credentials_isolated")

    def test_deployment_candidate_is_validated_but_live_activation_remains_blocked(self) -> None:
        evidence = DeploymentCandidateEvidence(
            artifact_digest="sha256:" + HEX_A,
            rollback_artifact_digest="sha256:" + HEX_B,
            provenance_signed=True,
            artifact_signature_verified=True,
            immutable_artifact=True,
            staging_health_checks_passed=True,
            migration_preflight_passed=True,
            rollback_path_validated=True,
            secrets_not_baked_into_artifact=True,
            environment_config_separated=True,
            privacy_safe_observability_ready=True,
            production_activation_requested=False,
        )
        authorize_deployment_candidate(evidence, production_deployment_authorized=False, audit_sink=self.audit)
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_deployment_candidate(
                replace(evidence, production_activation_requested=True),
                production_deployment_authorized=False,
                audit_sink=self.audit,
            )
        self.assertEqual(ctx.exception.reason_code, "production_deployment_not_authorized")

    def test_audit_dependency_failure_fails_closed(self) -> None:
        evidence = EnvironmentIsolationEvidence(
            environment="staging",
            account_or_project_isolated=True,
            credentials_isolated=True,
            network_namespace_isolated=True,
            storage_namespace_isolated=True,
            queue_namespace_isolated=True,
            audit_namespace_isolated=True,
            cross_environment_write_forbidden=True,
        )
        with self.assertRaises(StorageDeploymentError) as ctx:
            authorize_environment_isolation(evidence, audit_sink=MemoryStorageAuditSink(accept=False))
        self.assertEqual(ctx.exception.reason_code, "storage_audit_unavailable")


if __name__ == "__main__":
    unittest.main()
