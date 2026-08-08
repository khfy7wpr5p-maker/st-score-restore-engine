from __future__ import annotations

import unittest

from st_score_restore.stage1b_reference_drill import (
    DrillError,
    InMemoryCustodyReference,
    ROLE_CONFLICTS,
    audit_event_digest,
    validate_audit_chain,
)


MARKER = b"stage1b-project-authored-non-musical-marker"
ACCESS = "actor_access"
AUTHORITY = "actor_deletion_authority"
EXECUTOR = "actor_deletion_executor"
VERIFIER = "actor_deletion_verifier"
EMERGENCY_REQUESTER = "actor_emergency_requester"
EMERGENCY_APPROVER_1 = "actor_emergency_approver_1"
EMERGENCY_APPROVER_2 = "actor_emergency_approver_2"


def register_standard_identities(adapter: InMemoryCustodyReference) -> None:
    adapter.register_identity(ACCESS, "person_access", {"artifact_access_operator"})
    adapter.register_identity(AUTHORITY, "person_authority", {"deletion_authority"})
    adapter.register_identity(EXECUTOR, "person_executor", {"deletion_executor"})
    adapter.register_identity(VERIFIER, "person_verifier", {"deletion_receipt_verifier"})
    adapter.register_identity(EMERGENCY_REQUESTER, "person_emergency_requester", {"emergency_requester"})
    adapter.register_identity(EMERGENCY_APPROVER_1, "person_emergency_approver_1", {"emergency_approver"})
    adapter.register_identity(EMERGENCY_APPROVER_2, "person_emergency_approver_2", {"emergency_approver"})


def available_adapter() -> InMemoryCustodyReference:
    adapter = InMemoryCustodyReference()
    register_standard_identities(adapter)
    adapter.ingest(MARKER)
    adapter.promote(expected_version=1)
    return adapter


def ordinary_emergency_conditions() -> dict[str, bool]:
    return {
        "digest_matches": True,
        "byte_size_matches": True,
        "retention_valid": True,
        "purpose_authorized": True,
        "rights_approved": True,
        "privacy_approved": True,
        "purpose_blocking_hold": False,
        "deletion_or_revocation_active": False,
        "incident_lock_active": False,
        "environment_allowed": True,
        "storage_class_allowed": True,
        "audit_durable": True,
    }


class Stage1BReferenceDrillTests(unittest.TestCase):
    def test_positive_quarantine_promotion_and_narrow_read(self) -> None:
        adapter = InMemoryCustodyReference()
        register_standard_identities(adapter)
        adapter.ingest(MARKER)
        self.assertEqual(adapter.state, "quarantined")
        adapter.promote(expected_version=1)
        self.assertEqual(adapter.state, "available")
        token = adapter.grant_read(
            ACCESS,
            purpose=adapter.allowed_purpose,
            environment=adapter.allowed_environment,
            storage_class=adapter.allowed_storage_class,
        )
        self.assertEqual(adapter.read(token), MARKER)
        validate_audit_chain(
            adapter.audit_events,
            anchor_sequence=adapter.anchor_sequence,
            anchor_digest=adapter.anchor_digest,
        )

    def test_positive_immediate_revocation_idempotency_and_two_stage_deletion(self) -> None:
        adapter = available_adapter()
        token = adapter.grant_read(
            ACCESS,
            purpose=adapter.allowed_purpose,
            environment=adapter.allowed_environment,
            storage_class=adapter.allowed_storage_class,
        )
        pending = adapter.begin_revocation(
            "request-revoke-1",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
            access_authorizer_allows=False,
        )
        self.assertEqual(adapter.state, "deletion_pending")
        self.assertEqual(pending["type"], "revocation_pending_backup")
        self.assertFalse(pending["completed"])
        with self.assertRaises(DrillError):
            adapter.read(token)
        repeated = adapter.begin_revocation(
            "request-revoke-1",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
            access_authorizer_allows=False,
        )
        self.assertEqual(repeated, pending)
        adapter.confirm_revoked(expected_version=3)
        self.assertEqual(adapter.state, "revoked")
        final = adapter.finalize_deletion(
            expected_version=4,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
            backup_complete=True,
        )
        self.assertEqual(adapter.state, "tombstoned")
        self.assertEqual(final["type"], "final_deletion_complete")
        self.assertTrue(final["completed"])
        self.assertIsNone(adapter.backup)
        validate_audit_chain(
            adapter.audit_events,
            anchor_sequence=adapter.anchor_sequence,
            anchor_digest=adapter.anchor_digest,
        )

    def test_positive_restore_of_still_eligible_current_snapshot(self) -> None:
        adapter = available_adapter()
        snapshot = adapter.create_snapshot()
        restored = adapter.restore(
            snapshot,
            live_anchor_sequence=adapter.anchor_sequence,
            live_anchor_digest=adapter.anchor_digest,
            retention_valid=True,
        )
        self.assertEqual(restored, MARKER)

    def test_every_prohibited_role_collision_is_rejected_by_real_person(self) -> None:
        for index, (left, right) in enumerate(ROLE_CONFLICTS):
            with self.subTest(left=left, right=right):
                adapter = InMemoryCustodyReference()
                adapter.register_identity(f"actor_left_{index}", "person_same", {left})
                with self.assertRaisesRegex(DrillError, "role collision"):
                    adapter.register_identity(f"actor_right_{index}", "person_same", {right})

    def test_stale_and_disabled_identity_are_rejected(self) -> None:
        for active, fresh in ((False, True), (True, False)):
            with self.subTest(active=active, fresh=fresh):
                adapter = InMemoryCustodyReference()
                adapter.register_identity(ACCESS, "person_access", {"artifact_access_operator"}, active=active, fresh=fresh)
                adapter.ingest(MARKER)
                adapter.promote(expected_version=1)
                with self.assertRaisesRegex(DrillError, "stale, disabled"):
                    adapter.grant_read(
                        ACCESS,
                        purpose=adapter.allowed_purpose,
                        environment=adapter.allowed_environment,
                        storage_class=adapter.allowed_storage_class,
                    )

    def test_access_authorizer_cannot_delay_or_veto_valid_revocation(self) -> None:
        adapter = available_adapter()
        receipt = adapter.begin_revocation(
            "request-veto-proof",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
            access_authorizer_allows=False,
        )
        self.assertEqual(adapter.state, "deletion_pending")
        self.assertTrue(receipt["grantsInvalidated"])
        self.assertTrue(receipt["workFenced"])

    def test_emergency_access_cannot_bypass_any_ordinary_denial(self) -> None:
        required_true = (
            "digest_matches",
            "byte_size_matches",
            "retention_valid",
            "purpose_authorized",
            "rights_approved",
            "privacy_approved",
            "environment_allowed",
            "storage_class_allowed",
            "audit_durable",
        )
        required_false = (
            "purpose_blocking_hold",
            "deletion_or_revocation_active",
            "incident_lock_active",
        )
        for field in required_true:
            with self.subTest(field=field):
                adapter = available_adapter()
                conditions = ordinary_emergency_conditions()
                conditions[field] = False
                with self.assertRaises(DrillError):
                    adapter.emergency_read(
                        EMERGENCY_REQUESTER,
                        (EMERGENCY_APPROVER_1, EMERGENCY_APPROVER_2),
                        **conditions,
                    )
        for field in required_false:
            with self.subTest(field=field):
                adapter = available_adapter()
                conditions = ordinary_emergency_conditions()
                conditions[field] = True
                with self.assertRaises(DrillError):
                    adapter.emergency_read(
                        EMERGENCY_REQUESTER,
                        (EMERGENCY_APPROVER_1, EMERGENCY_APPROVER_2),
                        **conditions,
                    )
        quarantined = InMemoryCustodyReference()
        register_standard_identities(quarantined)
        quarantined.ingest(MARKER)
        with self.assertRaisesRegex(DrillError, "custody state"):
            quarantined.emergency_read(
                EMERGENCY_REQUESTER,
                (EMERGENCY_APPROVER_1, EMERGENCY_APPROVER_2),
                **ordinary_emergency_conditions(),
            )

    def test_unauthorized_environment_and_storage_class_are_rejected(self) -> None:
        adapter = available_adapter()
        with self.assertRaisesRegex(DrillError, "environment"):
            adapter.grant_read(
                ACCESS,
                purpose=adapter.allowed_purpose,
                environment="wrong_environment",
                storage_class=adapter.allowed_storage_class,
            )
        with self.assertRaisesRegex(DrillError, "storage class"):
            adapter.grant_read(
                ACCESS,
                purpose=adapter.allowed_purpose,
                environment=adapter.allowed_environment,
                storage_class="wrong_storage_class",
            )

    def test_read_is_denied_during_deletion_pending(self) -> None:
        adapter = available_adapter()
        token = adapter.grant_read(
            ACCESS,
            purpose=adapter.allowed_purpose,
            environment=adapter.allowed_environment,
            storage_class=adapter.allowed_storage_class,
        )
        adapter.begin_revocation(
            "request-read-block",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
        )
        with self.assertRaisesRegex(DrillError, "read is denied"):
            adapter.read(token)

    def test_inspection_timeout_crash_expansion_and_network_attempt_fail_closed(self) -> None:
        cases = (
            {"inspection_timeout": True},
            {"inspection_crash": True},
            {"expansion_ratio": InMemoryCustodyReference.MAX_EXPANSION_RATIO + 1.0},
            {"network_attempt": True},
        )
        for case in cases:
            with self.subTest(case=case):
                adapter = InMemoryCustodyReference()
                adapter.ingest(MARKER)
                with self.assertRaises(DrillError):
                    adapter.promote(expected_version=1, **case)
                self.assertEqual(adapter.state, "quarantined")

    def test_compare_and_swap_version_conflict_is_rejected(self) -> None:
        adapter = InMemoryCustodyReference()
        adapter.ingest(MARKER)
        with self.assertRaisesRegex(DrillError, "compare-and-swap"):
            adapter.promote(expected_version=0)

    def test_audit_failure_leaves_access_blocked(self) -> None:
        adapter = available_adapter()
        token = adapter.grant_read(
            ACCESS,
            purpose=adapter.allowed_purpose,
            environment=adapter.allowed_environment,
            storage_class=adapter.allowed_storage_class,
        )
        with self.assertRaisesRegex(DrillError, "audit durability"):
            adapter.begin_revocation(
                "request-audit-fail",
                expected_version=2,
                authority_actor=AUTHORITY,
                executor_actor=EXECUTOR,
                verifier_actor=VERIFIER,
                audit_durable=False,
            )
        self.assertEqual(adapter.state, "deletion_pending")
        self.assertTrue(adapter.work_fenced)
        with self.assertRaises(DrillError):
            adapter.read(token)

    def test_incomplete_work_fencing_leaves_access_blocked(self) -> None:
        adapter = available_adapter()
        token = adapter.grant_read(
            ACCESS,
            purpose=adapter.allowed_purpose,
            environment=adapter.allowed_environment,
            storage_class=adapter.allowed_storage_class,
        )
        with self.assertRaisesRegex(DrillError, "fencing"):
            adapter.begin_revocation(
                "request-fence-fail",
                expected_version=2,
                authority_actor=AUTHORITY,
                executor_actor=EXECUTOR,
                verifier_actor=VERIFIER,
                fencing_complete=False,
            )
        self.assertEqual(adapter.state, "deletion_pending")
        with self.assertRaises(DrillError):
            adapter.read(token)

    def test_duplicate_broken_nonmonotonic_forked_and_truncated_audit_are_rejected(self) -> None:
        adapter = available_adapter()
        events = adapter.audit_events
        duplicate = [dict(event) for event in events] + [dict(events[-1])]
        with self.assertRaises(DrillError):
            validate_audit_chain(duplicate, anchor_sequence=len(duplicate), anchor_digest=duplicate[-1]["digest"])

        broken = [dict(event) for event in events]
        broken[-1]["previousDigest"] = "0" * 64
        broken[-1]["digest"] = audit_event_digest(broken[-1])
        with self.assertRaises(DrillError):
            validate_audit_chain(broken, anchor_sequence=len(broken), anchor_digest=broken[-1]["digest"])

        nonmonotonic = [dict(event) for event in events]
        nonmonotonic[-1]["sequence"] += 1
        nonmonotonic[-1]["digest"] = audit_event_digest(nonmonotonic[-1])
        with self.assertRaises(DrillError):
            validate_audit_chain(nonmonotonic, anchor_sequence=adapter.anchor_sequence, anchor_digest=nonmonotonic[-1]["digest"])

        forked = [dict(event) for event in events]
        forked[-1]["operation"] = "forked_operation"
        forked[-1]["digest"] = audit_event_digest(forked[-1])
        with self.assertRaisesRegex(DrillError, "live anchor"):
            validate_audit_chain(forked, anchor_sequence=adapter.anchor_sequence, anchor_digest=adapter.anchor_digest)

        truncated = [dict(event) for event in events[:-1]]
        with self.assertRaisesRegex(DrillError, "live anchor"):
            validate_audit_chain(truncated, anchor_sequence=adapter.anchor_sequence, anchor_digest=adapter.anchor_digest)

    def test_conflicting_idempotency_replay_is_rejected(self) -> None:
        adapter = available_adapter()
        adapter.begin_revocation(
            "request-idempotent",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
            trigger="purpose_revocation",
        )
        with self.assertRaisesRegex(DrillError, "conflicting idempotency"):
            adapter.begin_revocation(
                "request-idempotent",
                expected_version=2,
                authority_actor=AUTHORITY,
                executor_actor=EXECUTOR,
                verifier_actor=VERIFIER,
                trigger="incident_lock",
            )

    def test_incomplete_replica_or_cache_deletion_is_rejected(self) -> None:
        for field in ("remove_replica", "remove_cache"):
            with self.subTest(field=field):
                adapter = available_adapter()
                kwargs = {field: False}
                with self.assertRaisesRegex(DrillError, "replica or cache"):
                    adapter.begin_revocation(
                        f"request-incomplete-{field}",
                        expected_version=2,
                        authority_actor=AUTHORITY,
                        executor_actor=EXECUTOR,
                        verifier_actor=VERIFIER,
                        **kwargs,
                    )
                self.assertEqual(adapter.state, "deletion_pending")

    def test_missing_backup_tombstone_is_rejected(self) -> None:
        adapter = available_adapter()
        with self.assertRaisesRegex(DrillError, "backup tombstone"):
            adapter.begin_revocation(
                "request-no-backup-tombstone",
                expected_version=2,
                authority_actor=AUTHORITY,
                executor_actor=EXECUTOR,
                verifier_actor=VERIFIER,
                backup_tombstone=False,
            )

    def test_pending_receipt_cannot_claim_completion(self) -> None:
        adapter = available_adapter()
        receipt = adapter.begin_revocation(
            "request-pending-receipt",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
        )
        receipt["completed"] = True
        receipt["deletionStatus"] = "completed"
        with self.assertRaisesRegex(DrillError, "cannot claim completion"):
            adapter.validate_receipt(receipt, backup_complete=False)

    def test_final_receipt_before_backup_completion_is_rejected(self) -> None:
        adapter = available_adapter()
        adapter.begin_revocation(
            "request-final-too-soon",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
        )
        adapter.confirm_revoked(expected_version=3)
        with self.assertRaisesRegex(DrillError, "before backup completion"):
            adapter.finalize_deletion(
                expected_version=4,
                executor_actor=EXECUTOR,
                verifier_actor=VERIFIER,
                backup_complete=False,
            )

    def test_restore_cannot_resurrect_revoked_data(self) -> None:
        adapter = available_adapter()
        snapshot = adapter.create_snapshot()
        adapter.begin_revocation(
            "request-restore-block",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
        )
        adapter.confirm_revoked(expected_version=3)
        with self.assertRaisesRegex(DrillError, "cannot resurrect"):
            adapter.restore(
                snapshot,
                live_anchor_sequence=adapter.anchor_sequence,
                live_anchor_digest=adapter.anchor_digest,
                retention_valid=True,
            )

    def test_restore_rejects_missing_stale_or_unanchored_checkpoint(self) -> None:
        adapter = available_adapter()
        snapshot = adapter.create_snapshot()
        with self.assertRaisesRegex(DrillError, "live independent anchor"):
            adapter.restore(snapshot, live_anchor_sequence=None, live_anchor_digest=None, retention_valid=True)
        with self.assertRaisesRegex(DrillError, "live anchor"):
            adapter.restore(
                snapshot,
                live_anchor_sequence=max(0, adapter.anchor_sequence - 1),
                live_anchor_digest=adapter.anchor_digest,
                retention_valid=True,
            )
        with self.assertRaisesRegex(DrillError, "live anchor"):
            adapter.restore(
                snapshot,
                live_anchor_sequence=adapter.anchor_sequence,
                live_anchor_digest="0" * 64,
                retention_valid=True,
            )

    def test_deletion_executor_cannot_finalize_without_independent_verifier(self) -> None:
        adapter = available_adapter()
        adapter.begin_revocation(
            "request-independent-final",
            expected_version=2,
            authority_actor=AUTHORITY,
            executor_actor=EXECUTOR,
            verifier_actor=VERIFIER,
        )
        adapter.confirm_revoked(expected_version=3)
        with self.assertRaises(DrillError):
            adapter.finalize_deletion(
                expected_version=4,
                executor_actor=EXECUTOR,
                verifier_actor=EXECUTOR,
                backup_complete=True,
            )


if __name__ == "__main__":
    unittest.main()
