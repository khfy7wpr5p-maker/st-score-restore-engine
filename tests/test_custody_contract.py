from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from st_score_restore.custody_contract import (
    CustodyContractError,
    canonical_barrier_fingerprint,
    canonical_event_digest,
    canonical_receipt_digest,
    validate_audit_evidence,
    validate_custody_record,
    validate_deletion_receipt,
    validate_restore,
    validate_schema_contracts,
    validate_state_transition,
)


def opaque(prefix: str, digit: str) -> str:
    return f"{prefix}:opq_{digit * 32}"


def record(state: str = "available", version: int = 2) -> dict:
    active = state in {"quarantined", "available", "deletion_pending"}
    value = {
        "schemaVersion": "1.0.0", "custodyRecordId": opaque("custody", "1"),
        "artifactSha256": "a" * 64, "byteSize": 17, "state": state,
        "recordVersion": version, "storageClassRef": opaque("policy", "2"),
        "environmentRef": opaque("policy", "3"), "locatorRef": opaque("locator", "4") if active else None,
        "encryptionPolicyRef": opaque("policy", "5"), "keyPolicyRef": opaque("policy", "6"),
        "custodianRef": opaque("actor", "7"), "accessPolicyRef": opaque("policy", "8"),
        "createdAt": "2026-08-08T00:00:00Z", "retainedUntil": "2027-08-08T00:00:00Z",
        "stateTransitionAt": "2026-08-08T01:00:00Z", "revocationStatus": "not_revoked",
        "deletionStatus": "not_started", "holdStatus": "none", "lastAuditEventDigest": "b" * 64,
        "auditPartitionSequence": version, "minimumCheckpointRef": opaque("checkpoint", "9"),
        "liveAnchorRef": opaque("anchor", "a"), "backupStatus": "none", "tombstoneStatus": "none",
        "pendingBackupReceiptRef": None, "finalDeletionReceiptRef": None,
    }
    if state == "deletion_pending":
        value.update(revocationStatus="pending", deletionStatus="pending", tombstoneStatus="intent_recorded", pendingBackupReceiptRef=opaque("receipt", "1"))
    elif state == "revoked":
        value.update(revocationStatus="effective", deletionStatus="active_boundaries_complete", backupStatus="tombstone_active", tombstoneStatus="active", pendingBackupReceiptRef=opaque("receipt", "b"))
    elif state == "tombstoned":
        value.update(revocationStatus="effective", deletionStatus="completed", backupStatus="complete", tombstoneStatus="final", finalDeletionReceiptRef=opaque("receipt", "1"))
    return value


def audit_evidence() -> dict:
    actor1, actor2, actor3 = opaque("actor", "1"), opaque("actor", "2"), opaque("actor", "3")
    events = []
    for index, operation in enumerate(("quarantine", "promote"), 1):
        event = {
            "eventId": opaque("event", str(index)), "eventDigest": "0" * 64,
            "custodyRecordId": opaque("custody", "1"), "recordVersion": index,
            "artifactSha256": "c" * 64, "operationCode": operation, "resultCode": "success",
            "actorRef": actor1, "roleCode": "custody_operator", "authorizationRef": opaque("authorization", "4"),
            "occurredAt": f"2026-08-08T00:00:0{index}Z", "previousEventDigest": None if index == 1 else events[-1]["eventDigest"],
            "partitionSequence": index, "requestFingerprint": str(index) * 64,
            "idempotencyRef": opaque("request", str(index)), "policyDecisionCode": "policy_allow", "failureCode": None,
        }
        event["eventDigest"] = canonical_event_digest(event)
        events.append(event)
    head = events[-1]["eventDigest"]
    return {
        "schemaVersion": "1.0.0", "events": events,
        "checkpoint": {"checkpointRef": opaque("checkpoint", "5"), "acceptedPartitionSequence": 2, "chainHeadDigest": head, "custodyRecordVersion": 2, "integrityEvidenceRef": opaque("evidence", "6")},
        "liveAnchor": {"anchorRef": opaque("anchor", "7"), "minimumAcceptedSequence": 2, "chainHeadDigest": head, "custodyRecordVersion": 2, "witnessEvidenceRef": opaque("witness", "8"), "source": "live_independent", "fresh": True, "valid": True},
        "identities": [
            {"actorRef": actor1, "personRef": opaque("person", "1"), "status": "active", "fresh": True},
            {"actorRef": actor2, "personRef": opaque("person", "2"), "status": "active", "fresh": True},
            {"actorRef": actor3, "personRef": opaque("person", "3"), "status": "active", "fresh": True},
        ],
        "roleAssignments": [{"actorRef": actor1, "roleCode": "custody_operator"}],
        "emergencyAccess": None,
    }


def receipt_identity_evidence(value: dict | None = None) -> dict:
    value = receipt() if value is None else value
    evidence = audit_evidence()
    evidence["identities"].extend([
        {"actorRef": value["executorRef"], "personRef": value["executorPersonRef"], "status": "active", "fresh": True},
        {"actorRef": value["verifierRef"], "personRef": value["verifierPersonRef"], "status": "active", "fresh": True},
    ])
    evidence["roleAssignments"].extend([
        {"actorRef": value["executorRef"], "roleCode": "deletion_executor"},
        {"actorRef": value["verifierRef"], "roleCode": "deletion_receipt_verifier"},
    ])
    return evidence


def barrier(value_record: dict, evidence: dict, *, removal_type: str = "none", minimum_version: int | None = None) -> dict:
    value = {
        "schemaVersion": "1.0.0",
        "artifactSha256": value_record["artifactSha256"],
        "custodyRecordId": value_record["custodyRecordId"],
        "minimumForbiddenRecordVersion": minimum_version,
        "removalType": removal_type,
        "authoritativeTime": "2026-08-08T02:00:00Z",
        "validUntil": "2026-08-08T02:05:00Z",
        "partitionSequence": evidence["checkpoint"]["acceptedPartitionSequence"],
        "chainHeadDigest": evidence["checkpoint"]["chainHeadDigest"],
        "checkpointRef": evidence["checkpoint"]["checkpointRef"],
        "anchorRef": evidence["liveAnchor"]["anchorRef"],
        "barrierSequence": 7,
        "barrierDigest": "0" * 64,
        "source": "live_independent", "fresh": True, "valid": True,
        "independentlyAuthenticated": True,
    }
    value["barrierDigest"] = canonical_barrier_fingerprint(value)
    return value


def receipt(kind: str = "revocation_pending_backup") -> dict:
    final = kind == "final_deletion_complete"
    value = {
        "schemaVersion": "1.0.0", "receiptType": kind, "receiptId": opaque("receipt", "1"),
        "requestId": opaque("request", "2"), "artifactSha256": "d" * 64, "custodyRecordId": opaque("custody", "3"),
        "recordVersion": 4, "revocationAuthorityRef": opaque("authority", "4"), "revocationTriggerRole": "purpose_authorizer", "deletionPendingAt": "2026-08-08T00:00:00Z",
        "grantsInvalidated": True, "workFenced": True, "tombstoneIntentRecorded": True, "auditDurable": True, "primaryDisposition": "removed", "replicaDisposition": "removed",
        "cacheDisposition": "not_present", "transientDisposition": "removed", "backupTombstoneStatus": "complete" if final else "active",
        "maximumBackupExpiry": "2026-09-08T00:00:00Z", "backupDisposition": "expired" if final else "pending_expiry",
        "keyEnvelopeDisposition": "destroyed", "executorRef": opaque("actor", "5"), "executorPersonRef": opaque("person", "5"), "verifierRef": opaque("actor", "6"), "verifierPersonRef": opaque("person", "6"),
        "finalAuditEventDigest": "e" * 64, "checkpointRef": opaque("checkpoint", "7"), "anchorRef": opaque("anchor", "8"),
        "removalEventDigest": "1" * 64, "barrierSequence": 7, "barrierDigest": "2" * 64,
        "deletionStatus": "completed" if final else "pending", "completedAt": "2026-09-08T00:00:01Z" if final else None,
        "receiptSha256": "f" * 64,
    }
    value["receiptSha256"] = canonical_receipt_digest(value)
    return value


def retention_evidence() -> dict:
    sources = ["primary_replica", "replica", "cache", "transient_store", "backup", "archive"]
    return {
        "schemaVersion": "1.0.0", "observedAt": "2026-08-08T02:00:00Z", "validUntil": "2026-08-08T03:00:00Z",
        "restoreSources": [{"sourceClass": name, "expiresAt": "2026-08-09T02:00:00Z", "maximumLifetimeSeconds": 86400, "verified": True} for name in sources],
        "safetyMarginSeconds": 86400, "antiResurrectionHorizon": "2026-08-10T02:00:00Z",
        "barrierValidThrough": "2026-08-10T02:00:00Z", "auditValidThrough": "2026-08-10T02:00:00Z",
        "checkpointValidThrough": "2026-08-10T02:00:00Z", "tombstoneValidThrough": "2026-08-10T02:00:00Z",
    }


def removal_bundle(value_record: dict, operation: str) -> tuple[dict, dict, dict, dict]:
    evidence = audit_evidence()
    evidence["identities"].extend([
        {"actorRef": opaque("actor", "5"), "personRef": opaque("person", "5"), "status": "active", "fresh": True},
        {"actorRef": opaque("actor", "6"), "personRef": opaque("person", "6"), "status": "active", "fresh": True},
    ])
    evidence["roleAssignments"].extend([
        {"actorRef": opaque("actor", "5"), "roleCode": "deletion_executor"},
        {"actorRef": opaque("actor", "6"), "roleCode": "deletion_receipt_verifier"},
    ])
    template = evidence["events"][0]
    evidence["events"] = []
    for index in range(1, value_record["recordVersion"] + 1):
        last = dict(template)
        last.update(eventId=opaque("event", str(index)), recordVersion=index,
                    artifactSha256=value_record["artifactSha256"], custodyRecordId=value_record["custodyRecordId"],
                    operationCode=(operation if index == value_record["recordVersion"] else
                                   "begin_deletion" if operation == "revoke" and index == value_record["recordVersion"] - 1 else
                                   "checkpoint"),
                    occurredAt=f"2026-08-08T00:00:0{index}Z", previousEventDigest=evidence["events"][-1]["eventDigest"] if evidence["events"] else None,
                    partitionSequence=index, requestFingerprint=str(index) * 64, idempotencyRef=opaque("request", str(index)))
        last["eventDigest"] = canonical_event_digest(last)
        evidence["events"].append(last)
    evidence["checkpoint"].update(acceptedPartitionSequence=last["partitionSequence"], chainHeadDigest=last["eventDigest"], custodyRecordVersion=last["recordVersion"], checkpointRef=value_record["minimumCheckpointRef"])
    evidence["liveAnchor"].update(minimumAcceptedSequence=last["partitionSequence"], chainHeadDigest=last["eventDigest"], custodyRecordVersion=last["recordVersion"], anchorRef=value_record["liveAnchorRef"])
    value_record["lastAuditEventDigest"] = last["eventDigest"]
    live = barrier(value_record, evidence, removal_type="deletion_tombstone", minimum_version=value_record["recordVersion"])
    prior = dict(live); prior["barrierSequence"] -= 1; prior["barrierDigest"] = canonical_barrier_fingerprint(prior)
    return evidence, last, live, prior


class CustodyContractTests(unittest.TestCase):
    def test_positive_contract_cases(self) -> None:
        validate_schema_contracts()
        validate_custody_record(record())
        validate_audit_evidence(audit_evidence())
        pending = receipt()
        final = receipt("final_deletion_complete")
        validate_deletion_receipt(pending, backup_complete=False, identity_evidence=receipt_identity_evidence(pending))
        validate_deletion_receipt(final, backup_complete=True, identity_evidence=receipt_identity_evidence(final))

    def test_schemas_enforce_runtime_state_and_receipt_semantics(self) -> None:
        root = Path(__file__).resolve().parents[1]
        record_validator = Draft202012Validator(json.loads((root / "schemas/custody-record.schema.json").read_text()))
        receipt_validator = Draft202012Validator(json.loads((root / "schemas/deletion-receipt.schema.json").read_text()))
        invalid_record = record("revoked", 4); invalid_record["backupStatus"] = "tombstone_pending"
        invalid_receipt = receipt(); invalid_receipt["auditDurable"] = False
        self.assertTrue(list(record_validator.iter_errors(invalid_record)))
        self.assertTrue(list(receipt_validator.iter_errors(invalid_receipt)))
        with self.assertRaises(CustodyContractError): validate_custody_record(invalid_record)
        with self.assertRaises(CustodyContractError): validate_deletion_receipt(invalid_receipt, backup_complete=False, identity_evidence=receipt_identity_evidence(invalid_receipt))

    def test_unknown_field_rejected(self) -> None:
        value = record(); value["providerUrl"] = "https://provider.invalid/object"
        with self.assertRaisesRegex(CustodyContractError, "Additional properties"):
            validate_custody_record(value)

    def test_missing_required_field_rejected(self) -> None:
        value = record(); del value["keyPolicyRef"]
        with self.assertRaisesRegex(CustodyContractError, "required property"):
            validate_custody_record(value)

    def test_free_text_identity_and_provider_url_rejected(self) -> None:
        value = record(); value["custodianRef"] = "teacher@example.com"
        with self.assertRaises(CustodyContractError): validate_custody_record(value)
        value = record(); value["locatorRef"] = "https://storage.example/bucket/key"
        with self.assertRaises(CustodyContractError): validate_custody_record(value)

    def test_legal_transition_and_versions(self) -> None:
        old = record("available", 2); new = record("deletion_pending", 3)
        new["auditPartitionSequence"] = 3
        pending = receipt(); pending.update(custodyRecordId=new["custodyRecordId"], artifactSha256=new["artifactSha256"], recordVersion=3, finalAuditEventDigest=new["lastAuditEventDigest"], checkpointRef=new["minimumCheckpointRef"], anchorRef=new["liveAnchorRef"])
        evidence, event, live, prior = removal_bundle(new, "begin_deletion")
        pending.update(finalAuditEventDigest=new["lastAuditEventDigest"], removalEventDigest=event["eventDigest"], barrierSequence=live["barrierSequence"], barrierDigest=live["barrierDigest"]); pending["receiptSha256"] = canonical_receipt_digest(pending)
        validate_state_transition(old, new, receipt=pending, audit_evidence=evidence, removal_event=event, barrier_evidence=live, trusted_live_barrier=live, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")

    def test_revocation_transition_requires_atomic_receipt(self) -> None:
        new = record("deletion_pending", 3); new["auditPartitionSequence"] = 3
        with self.assertRaisesRegex(CustodyContractError, "atomic pending-receipt"):
            validate_state_transition(record("available", 2), new)

    def test_illegal_state_transition_rejected(self) -> None:
        with self.assertRaisesRegex(CustodyContractError, "illegal custody"):
            validate_state_transition(record("available", 2), record("quarantined", 3))

    def test_revoked_to_available_rejected(self) -> None:
        with self.assertRaisesRegex(CustodyContractError, "revoked -> available"):
            validate_state_transition(record("revoked", 4), record("available", 5))

    def test_tombstoned_reactivation_rejected(self) -> None:
        old = record("tombstoned", 5); old.update(deletionStatus="completed", finalDeletionReceiptRef=opaque("receipt", "1"), tombstoneStatus="final")
        with self.assertRaisesRegex(CustodyContractError, "tombstoned ->"):
            validate_state_transition(old, record("quarantined", 6))

    def test_non_monotonic_record_version_rejected(self) -> None:
        new = record("deletion_pending", 2); new["auditPartitionSequence"] = 3
        with self.assertRaisesRegex(CustodyContractError, "record version"):
            validate_state_transition(record("available", 2), new)

    def test_stale_and_disabled_identity_rejected(self) -> None:
        for key, value in (("fresh", False), ("status", "disabled")):
            evidence = audit_evidence(); evidence["identities"][0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(CustodyContractError, "stale, disabled"):
                validate_audit_evidence(evidence)

    def test_prohibited_role_collision_uses_real_person(self) -> None:
        pairs = (
            ("access_authorizer", "custody_operator"),
            ("key_custodian", "artifact_access_operator"),
            ("key_policy_approver", "key_operation_executor"),
            ("deletion_authority", "deletion_executor"),
            ("deletion_executor", "deletion_receipt_verifier"),
            ("audit_reviewer", "reviewed_operation_executor"),
            ("emergency_requester", "emergency_approver"),
        )
        for left, right in pairs:
            evidence = audit_evidence(); first, second = evidence["identities"][1:]
            evidence["roleAssignments"].extend([
                {"actorRef": first["actorRef"], "roleCode": left},
                {"actorRef": second["actorRef"], "roleCode": right},
            ])
            second["personRef"] = first["personRef"]
            with self.subTest(left=left, right=right), self.assertRaisesRegex(CustodyContractError, "prohibited role collision"):
                validate_audit_evidence(evidence)

    def test_conflicting_replay_rejected(self) -> None:
        evidence = audit_evidence(); evidence["events"][1]["idempotencyRef"] = evidence["events"][0]["idempotencyRef"]
        evidence["events"][1]["eventDigest"] = canonical_event_digest(evidence["events"][1])
        with self.assertRaisesRegex(CustodyContractError, "conflicting idempotency"):
            validate_audit_evidence(evidence)

    def test_broken_audit_chain_rejected(self) -> None:
        evidence = audit_evidence(); evidence["events"][1]["previousEventDigest"] = "f" * 64
        evidence["events"][1]["eventDigest"] = canonical_event_digest(evidence["events"][1])
        with self.assertRaisesRegex(CustodyContractError, "broken audit chain"):
            validate_audit_evidence(evidence)

    def test_truncated_audit_chain_rejected(self) -> None:
        evidence = audit_evidence(); evidence["events"] = evidence["events"][1:]
        evidence["events"][0]["previousEventDigest"] = None
        evidence["events"][0]["eventDigest"] = canonical_event_digest(evidence["events"][0])
        with self.assertRaisesRegex(CustodyContractError, "truncated"):
            validate_audit_evidence(evidence)

    def test_non_monotonic_audit_sequence_rejected(self) -> None:
        evidence = audit_evidence(); evidence["events"][1]["partitionSequence"] = 1
        evidence["events"][1]["eventDigest"] = canonical_event_digest(evidence["events"][1])
        with self.assertRaisesRegex(CustodyContractError, "not monotonic"):
            validate_audit_evidence(evidence)

    def test_incomplete_audit_record_versions_rejected(self) -> None:
        evidence = audit_evidence(); evidence["events"][1]["recordVersion"] = 3
        evidence["events"][1]["eventDigest"] = canonical_event_digest(evidence["events"][1])
        evidence["checkpoint"]["custodyRecordVersion"] = 3; evidence["liveAnchor"]["custodyRecordVersion"] = 3
        with self.assertRaisesRegex(CustodyContractError, "contiguous"):
            validate_audit_evidence(evidence)

    def test_stale_checkpoint_rejected(self) -> None:
        evidence = audit_evidence(); evidence["liveAnchor"]["minimumAcceptedSequence"] = 3
        with self.assertRaisesRegex(CustodyContractError, "stale"):
            validate_audit_evidence(evidence)

    def test_anchor_mismatch_rejected(self) -> None:
        evidence = audit_evidence(); evidence["liveAnchor"]["chainHeadDigest"] = "f" * 64
        with self.assertRaisesRegex(CustodyContractError, "anchor mismatch"):
            validate_audit_evidence(evidence)

    def test_every_audit_event_field_is_covered_by_canonical_digest(self) -> None:
        original = audit_evidence()
        mutations = {
            "eventId": opaque("event", "9"), "custodyRecordId": opaque("custody", "9"),
            "recordVersion": 9, "artifactSha256": "9" * 64,
            "operationCode": "checkpoint", "resultCode": "failure",
            "actorRef": opaque("actor", "9"), "roleCode": "audit_reviewer",
            "authorizationRef": opaque("authorization", "9"),
            "occurredAt": "2026-08-08T00:09:00Z", "previousEventDigest": "9" * 64,
            "partitionSequence": 9, "requestFingerprint": "9" * 64,
            "idempotencyRef": opaque("request", "9"),
            "policyDecisionCode": "policy_deny", "failureCode": "denied",
        }
        for field, value in mutations.items():
            evidence = audit_evidence()
            evidence["events"][1][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(CustodyContractError, "canonical event content"):
                validate_audit_evidence(evidence)

    def test_self_consistent_forged_chain_rejected_by_live_anchor(self) -> None:
        evidence = audit_evidence()
        evidence["events"][0]["operationCode"] = "checkpoint"
        evidence["events"][0]["eventDigest"] = canonical_event_digest(evidence["events"][0])
        evidence["events"][1]["previousEventDigest"] = evidence["events"][0]["eventDigest"]
        evidence["events"][1]["eventDigest"] = canonical_event_digest(evidence["events"][1])
        evidence["checkpoint"]["chainHeadDigest"] = evidence["events"][1]["eventDigest"]
        with self.assertRaisesRegex(CustodyContractError, "anchor mismatch"):
            validate_audit_evidence(evidence)

    def test_missing_stale_invalid_and_snapshot_anchor_rejected(self) -> None:
        for key, value in (("fresh", False), ("valid", False), ("source", "snapshot")):
            evidence = audit_evidence(); evidence["liveAnchor"][key] = value
            with self.subTest(key=key), self.assertRaises(CustodyContractError):
                validate_audit_evidence(evidence)
        evidence = audit_evidence(); del evidence["liveAnchor"]
        with self.assertRaises(CustodyContractError): validate_audit_evidence(evidence)

    def test_emergency_access_cannot_bypass_denial(self) -> None:
        evidence = audit_evidence(); actors = [item["actorRef"] for item in evidence["identities"]]
        evidence["emergencyAccess"] = {"requesterRef": actors[0], "approverRefs": actors[1:], "state": "available", "digestMatches": True, "byteSizeMatches": True, "retentionValid": True, "purposeAuthorized": True, "rightsApproved": True, "privacyApproved": True, "purposeBlockingHold": True, "deletionOrRevocationActive": False, "incidentLockActive": False, "environmentAllowed": True, "storageClassAllowed": True, "auditDurable": True, "postEventReviewRequired": True}
        with self.assertRaises(CustodyContractError):
            validate_audit_evidence(evidence)

    def test_emergency_access_requires_real_roles(self) -> None:
        evidence = audit_evidence(); actors = [item["actorRef"] for item in evidence["identities"]]
        evidence["emergencyAccess"] = {"requesterRef": actors[0], "approverRefs": actors[1:], "state": "available", "digestMatches": True, "byteSizeMatches": True, "retentionValid": True, "purposeAuthorized": True, "rightsApproved": True, "privacyApproved": True, "purposeBlockingHold": False, "deletionOrRevocationActive": False, "incidentLockActive": False, "environmentAllowed": True, "storageClassAllowed": True, "auditDurable": True, "postEventReviewRequired": True}
        with self.assertRaisesRegex(CustodyContractError, "missing required roles"):
            validate_audit_evidence(evidence)

    def test_every_emergency_denial_fails_closed(self) -> None:
        true_gates = ("digestMatches", "byteSizeMatches", "retentionValid", "purposeAuthorized", "rightsApproved", "privacyApproved", "environmentAllowed", "storageClassAllowed", "auditDurable")
        false_gates = ("purposeBlockingHold", "deletionOrRevocationActive", "incidentLockActive")
        for key in (*true_gates, *false_gates, "state"):
            evidence = audit_evidence(); actors = [item["actorRef"] for item in evidence["identities"]]
            evidence["roleAssignments"].extend([{"actorRef": actors[0], "roleCode": "emergency_requester"}, *({"actorRef": actor, "roleCode": "emergency_approver"} for actor in actors[1:])])
            emergency = {"requesterRef": actors[0], "approverRefs": actors[1:], "state": "available", **{name: True for name in true_gates}, **{name: False for name in false_gates}, "postEventReviewRequired": True}
            emergency[key] = "revoked" if key == "state" else not emergency[key]
            evidence["emergencyAccess"] = emergency
            with self.subTest(key=key), self.assertRaises(CustodyContractError): validate_audit_evidence(evidence)

    def test_pending_receipt_cannot_claim_completion(self) -> None:
        value = receipt(); value["deletionStatus"] = "completed"
        with self.assertRaises(CustodyContractError):
            validate_deletion_receipt(value, backup_complete=False, identity_evidence=receipt_identity_evidence(value))

    def test_final_receipt_forbidden_before_backup_completion(self) -> None:
        with self.assertRaisesRegex(CustodyContractError, "forbidden before backup"):
            value = receipt("final_deletion_complete")
            validate_deletion_receipt(value, backup_complete=False, identity_evidence=receipt_identity_evidence(value))

    def test_revocation_atomic_evidence_and_authorizer_veto_rejected(self) -> None:
        for key, value in (("grantsInvalidated", False), ("workFenced", False), ("tombstoneIntentRecorded", False), ("auditDurable", False), ("revocationTriggerRole", "access_authorizer")):
            value_receipt = receipt(); value_receipt[key] = value
            with self.subTest(key=key), self.assertRaises(CustodyContractError):
                validate_deletion_receipt(value_receipt, backup_complete=False, identity_evidence=receipt_identity_evidence(value_receipt))

    def test_partial_or_unknown_boundary_disposition_rejected(self) -> None:
        for key in ("primaryDisposition", "replicaDisposition", "cacheDisposition", "transientDisposition", "keyEnvelopeDisposition", "backupDisposition"):
            value = receipt(); value[key] = "unknown"
            with self.subTest(key=key), self.assertRaises(CustodyContractError): validate_deletion_receipt(value, backup_complete=False, identity_evidence=receipt_identity_evidence(value))

    def test_receipt_real_person_collision_rejected(self) -> None:
        value = receipt(); value["verifierPersonRef"] = value["executorPersonRef"]
        value["receiptSha256"] = canonical_receipt_digest(value)
        with self.assertRaisesRegex(CustodyContractError, "role collision|independent"):
            validate_deletion_receipt(value, backup_complete=False, identity_evidence=receipt_identity_evidence(value))

    def test_receipt_independence_uses_verified_actor_identity_and_roles(self) -> None:
        value = receipt()
        validate_deletion_receipt(
            value, backup_complete=False, identity_evidence=receipt_identity_evidence(value)
        )

        same_actor = dict(value)
        same_actor["verifierRef"] = same_actor["executorRef"]
        same_actor["receiptSha256"] = canonical_receipt_digest(same_actor)
        with self.assertRaises(CustodyContractError):
            validate_deletion_receipt(same_actor, backup_complete=False, identity_evidence=receipt_identity_evidence(value))

        same_person_evidence = receipt_identity_evidence(value)
        same_person_evidence["identities"][-1]["personRef"] = same_person_evidence["identities"][-2]["personRef"]
        with self.assertRaises(CustodyContractError):
            validate_deletion_receipt(value, backup_complete=False, identity_evidence=same_person_evidence)

        claimed_person = dict(value)
        claimed_person["verifierPersonRef"] = opaque("person", "9")
        claimed_person["receiptSha256"] = canonical_receipt_digest(claimed_person)
        with self.assertRaisesRegex(CustodyContractError, "verified actor identity"):
            validate_deletion_receipt(claimed_person, backup_complete=False, identity_evidence=receipt_identity_evidence(value))

        for mutation in ("missing_identity", "stale_identity", "revoked_identity", "missing_role", "wrong_role"):
            evidence = receipt_identity_evidence(value)
            if mutation == "missing_identity":
                evidence["identities"] = evidence["identities"][:-1]
            elif mutation == "stale_identity":
                evidence["identities"][-1]["fresh"] = False
            elif mutation == "revoked_identity":
                evidence["identities"][-1]["status"] = "revoked"
            elif mutation == "missing_role":
                evidence["roleAssignments"] = evidence["roleAssignments"][:-1]
            else:
                evidence["roleAssignments"][-1]["roleCode"] = "audit_reviewer"
            with self.subTest(mutation=mutation), self.assertRaises(CustodyContractError):
                validate_deletion_receipt(value, backup_complete=False, identity_evidence=evidence)

    def test_receipt_record_binding_rejected_on_every_mismatch(self) -> None:
        value_record = record("revoked", 4)
        value_record.update(artifactSha256="d" * 64, lastAuditEventDigest="e" * 64, minimumCheckpointRef=opaque("checkpoint", "7"), liveAnchorRef=opaque("anchor", "8"))
        for key, value in (("custodyRecordId", opaque("custody", "9")), ("artifactSha256", "9" * 64), ("recordVersion", 3), ("finalAuditEventDigest", "9" * 64), ("checkpointRef", opaque("checkpoint", "9")), ("anchorRef", opaque("anchor", "9"))):
            value_receipt = receipt(); value_receipt[key] = value
            value_receipt["receiptSha256"] = canonical_receipt_digest(value_receipt)
            with self.subTest(key=key), self.assertRaisesRegex(CustodyContractError, "does not match"):
                validate_deletion_receipt(value_receipt, backup_complete=False, record=value_record, identity_evidence=receipt_identity_evidence(value_receipt))

    def test_tombstone_requires_related_valid_final_receipt(self) -> None:
        old = record("revoked", 4); new = record("tombstoned", 5)
        new.update(deletionStatus="completed", backupStatus="complete", tombstoneStatus="final", finalDeletionReceiptRef=opaque("receipt", "1"), auditPartitionSequence=5)
        with self.assertRaisesRegex(CustodyContractError, "requires the referenced"):
            validate_state_transition(old, new)
        final = receipt("final_deletion_complete")
        final.update(custodyRecordId=new["custodyRecordId"], artifactSha256=new["artifactSha256"], recordVersion=5, finalAuditEventDigest=new["lastAuditEventDigest"], checkpointRef=new["minimumCheckpointRef"], anchorRef=new["liveAnchorRef"])
        evidence, event, live, prior = removal_bundle(new, "finalize_deletion")
        final.update(finalAuditEventDigest=new["lastAuditEventDigest"], removalEventDigest=event["eventDigest"], barrierSequence=live["barrierSequence"], barrierDigest=live["barrierDigest"]); final["receiptSha256"] = canonical_receipt_digest(final)
        validate_state_transition(old, new, receipt=final, audit_evidence=evidence, removal_event=event, barrier_evidence=live, trusted_live_barrier=live, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")
        final["receiptId"] = opaque("receipt", "9")
        final["receiptSha256"] = canonical_receipt_digest(final)
        with self.assertRaisesRegex(CustodyContractError, "not the record's final receipt"):
            validate_state_transition(old, new, receipt=final, audit_evidence=evidence, removal_event=event, barrier_evidence=live, trusted_live_barrier=live, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")

    def test_restore_rejects_revoked_stale_and_unknown_retention_evidence(self) -> None:
        value_record = record("available", 2); value_record.update(artifactSha256="c" * 64)
        evidence = audit_evidence()
        value_record.update(
            lastAuditEventDigest=evidence["events"][-1]["eventDigest"],
            minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"],
            liveAnchorRef=evidence["liveAnchor"]["anchorRef"],
        )
        live_barrier = barrier(value_record, evidence)
        common = {"barrier_evidence": live_barrier, "trusted_live_barrier": live_barrier, "retention_evidence": retention_evidence(), "authoritative_time": "2026-08-08T02:01:00Z"}
        validate_restore(value_record, evidence, snapshot_record_version=2, **common)
        for kwargs in ({"snapshot_record_version": 1}, {"snapshot_record_version": 2, "retention_valid": True}, {"snapshot_record_version": 2, "evidence_retained": True}):
            with self.assertRaises(CustodyContractError): validate_restore(value_record, evidence, **kwargs, **common)
        revoked = record("revoked", 2); revoked.update(
            artifactSha256="c" * 64,
            lastAuditEventDigest=evidence["events"][-1]["eventDigest"],
            minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"],
            liveAnchorRef=evidence["liveAnchor"]["anchorRef"],
        )
        revoked_barrier = barrier(revoked, evidence)
        with self.assertRaisesRegex(CustodyContractError, "cannot resurrect"):
            validate_restore(revoked, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=revoked_barrier, trusted_live_barrier=revoked_barrier, authoritative_time="2026-08-08T02:01:00Z")

    def test_restore_rejects_pre_removal_backup_from_valid_current_barrier(self) -> None:
        value_record = record("available", 2); evidence = audit_evidence()
        value_record.update(artifactSha256="c" * 64, lastAuditEventDigest=evidence["events"][-1]["eventDigest"], minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"], liveAnchorRef=evidence["liveAnchor"]["anchorRef"])
        removal = barrier(value_record, evidence, removal_type="privacy_revocation", minimum_version=3)
        with self.assertRaisesRegex(CustodyContractError, "cannot resurrect"):
            validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=removal, trusted_live_barrier=removal, authoritative_time="2026-08-08T02:01:00Z")

    def test_restore_fails_closed_for_unavailable_or_stale_barrier(self) -> None:
        value_record = record("available", 2); evidence = audit_evidence()
        value_record.update(artifactSha256="c" * 64, lastAuditEventDigest=evidence["events"][-1]["eventDigest"], minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"], liveAnchorRef=evidence["liveAnchor"]["anchorRef"])
        for changed, now in ((None, "2026-08-08T02:01:00Z"), ({"valid": False}, "2026-08-08T02:01:00Z"), ({"source": "snapshot"}, "2026-08-08T02:01:00Z"), ({}, "2026-08-08T02:06:00Z")):
            live = None if changed is None else barrier(value_record, evidence)
            if live is not None: live.update(changed)
            with self.subTest(changed=changed, now=now), self.assertRaises(CustodyContractError):
                validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=live, trusted_live_barrier=live, authoritative_time=now)

    def test_restore_rejects_every_barrier_binding_mismatch(self) -> None:
        value_record = record("available", 2); evidence = audit_evidence()
        value_record.update(artifactSha256="c" * 64, lastAuditEventDigest=evidence["events"][-1]["eventDigest"], minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"], liveAnchorRef=evidence["liveAnchor"]["anchorRef"])
        changes = {
            "artifactSha256": "9" * 64, "custodyRecordId": opaque("custody", "9"),
            "minimumForbiddenRecordVersion": 1, "partitionSequence": 1,
            "chainHeadDigest": "9" * 64, "checkpointRef": opaque("checkpoint", "9"),
            "anchorRef": opaque("anchor", "9"),
        }
        for field, changed in changes.items():
            live = barrier(value_record, evidence)
            live[field] = changed
            if field == "minimumForbiddenRecordVersion": live["removalType"] = "incident_lock"
            live["barrierDigest"] = canonical_barrier_fingerprint(live)
            with self.subTest(field=field), self.assertRaises(CustodyContractError):
                validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=live, trusted_live_barrier=live, authoritative_time="2026-08-08T02:01:00Z")


    def test_every_receipt_field_is_bound_by_canonical_digest(self) -> None:
        original = receipt()
        for field, old_value in original.items():
            if field == "receiptSha256": continue
            changed = dict(original)
            if isinstance(old_value, bool): changed[field] = not old_value
            elif isinstance(old_value, int): changed[field] = old_value + 1
            elif old_value is None: changed[field] = "2026-08-08T00:00:01Z"
            else: changed[field] = old_value + "x"
            with self.subTest(field=field), self.assertRaises(CustodyContractError):
                validate_deletion_receipt(changed, backup_complete=False, identity_evidence=receipt_identity_evidence(original))

    def test_barrier_digest_substitution_replay_rollback_and_fork_rejected(self) -> None:
        value_record = record("available", 2); evidence = audit_evidence()
        value_record.update(artifactSha256="c" * 64, lastAuditEventDigest=evidence["events"][-1]["eventDigest"], minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"], liveAnchorRef=evidence["liveAnchor"]["anchorRef"])
        live = barrier(value_record, evidence)
        forged = dict(live); forged["barrierSequence"] += 1
        with self.assertRaisesRegex(CustodyContractError, "canonical digest"):
            validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=forged, trusted_live_barrier=forged, authoritative_time="2026-08-08T02:01:00Z")
        for sequence in (live["barrierSequence"], live["barrierSequence"] - 1):
            candidate = dict(live); candidate["barrierSequence"] = sequence; candidate["barrierDigest"] = canonical_barrier_fingerprint(candidate)
            with self.subTest(sequence=sequence), self.assertRaisesRegex(CustodyContractError, "replay or rollback"):
                validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=candidate, trusted_live_barrier=candidate, prior_trusted_barrier=live, authoritative_time="2026-08-08T02:01:00Z")
        fork = dict(live); fork["barrierSequence"] += 1; fork["custodyRecordId"] = opaque("custody", "9"); fork["barrierDigest"] = canonical_barrier_fingerprint(fork)
        with self.assertRaisesRegex(CustodyContractError, "fork"):
            validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=fork, trusted_live_barrier=fork, prior_trusted_barrier=live, authoritative_time="2026-08-08T02:01:00Z")

    def test_pending_to_revoked_binds_pending_receipt_event_checkpoint_and_barrier(self) -> None:
        old = record("deletion_pending", 3); current = record("revoked", 4)
        current.update(auditPartitionSequence=4, pendingBackupReceiptRef=old["pendingBackupReceiptRef"])
        evidence, event, live, prior = removal_bundle(current, "revoke")
        pending_event = evidence["events"][-2]
        old["lastAuditEventDigest"] = pending_event["eventDigest"]
        pending = receipt(); pending.update(receiptId=old["pendingBackupReceiptRef"], custodyRecordId=old["custodyRecordId"], artifactSha256=old["artifactSha256"], recordVersion=3, finalAuditEventDigest=pending_event["eventDigest"], checkpointRef=old["minimumCheckpointRef"], anchorRef=old["liveAnchorRef"], removalEventDigest=pending_event["eventDigest"], barrierSequence=prior["barrierSequence"], barrierDigest=prior["barrierDigest"]); pending["receiptSha256"] = canonical_receipt_digest(pending)
        validate_state_transition(old, current, pending_receipt=pending, audit_evidence=evidence, removal_event=event, barrier_evidence=live, trusted_live_barrier=live, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")
        unrelated = dict(pending); unrelated["receiptId"] = opaque("receipt", "9"); unrelated["receiptSha256"] = canonical_receipt_digest(unrelated)
        with self.assertRaisesRegex(CustodyContractError, "referenced pending receipt"):
            validate_state_transition(old, current, pending_receipt=unrelated, audit_evidence=evidence, removal_event=event, barrier_evidence=live, trusted_live_barrier=live, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")

        for mutation in ("missing", "unrelated", "forged", "stale", "artifact"):
            bad = dict(pending)
            bad_evidence = json.loads(json.dumps(evidence))
            if mutation == "missing":
                bad["removalEventDigest"] = "9" * 64
            elif mutation == "unrelated":
                bad["removalEventDigest"] = bad_evidence["events"][0]["eventDigest"]
            elif mutation == "forged":
                bad_evidence["events"][-2]["operationCode"] = "checkpoint"
            elif mutation == "stale":
                bad["recordVersion"] = 2
            else:
                bad["artifactSha256"] = "9" * 64
            bad["receiptSha256"] = canonical_receipt_digest(bad)
            with self.subTest(mutation=mutation), self.assertRaises(CustodyContractError):
                validate_state_transition(old, current, pending_receipt=bad, audit_evidence=bad_evidence, removal_event=event, barrier_evidence=live, trusted_live_barrier=live, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")

    def test_deletion_pending_requires_fresh_post_ack_live_barrier(self) -> None:
        old = record("available", 2); current = record("deletion_pending", 3); current["auditPartitionSequence"] = 3
        pending = receipt(); evidence, event, live, prior = removal_bundle(current, "begin_deletion")
        pending.update(custodyRecordId=current["custodyRecordId"], artifactSha256=current["artifactSha256"], recordVersion=3,
                       finalAuditEventDigest=current["lastAuditEventDigest"], checkpointRef=current["minimumCheckpointRef"], anchorRef=current["liveAnchorRef"],
                       removalEventDigest=event["eventDigest"], barrierSequence=live["barrierSequence"], barrierDigest=live["barrierDigest"])
        pending["receiptSha256"] = canonical_receipt_digest(pending)
        with self.assertRaisesRegex(CustodyContractError, "fresh live"):
            validate_state_transition(old, current, receipt=pending, audit_evidence=evidence, removal_event=event, authoritative_time="2026-08-08T02:01:00Z")
        pre_ack = dict(live); pre_ack["authoritativeTime"] = "2026-08-08T00:00:01Z"; pre_ack["barrierDigest"] = canonical_barrier_fingerprint(pre_ack)
        with self.assertRaisesRegex(CustodyContractError, "predates removal acknowledgement"):
            validate_state_transition(old, current, receipt=pending, audit_evidence=evidence, removal_event=event, barrier_evidence=pre_ack, trusted_live_barrier=pre_ack, prior_trusted_barrier=prior, authoritative_time="2026-08-08T02:01:00Z")

    def test_restore_horizon_rejects_unknown_unbounded_inconsistent_and_short_evidence(self) -> None:
        value_record = record("available", 2); evidence = audit_evidence()
        value_record.update(artifactSha256="c" * 64, lastAuditEventDigest=evidence["events"][-1]["eventDigest"], minimumCheckpointRef=evidence["checkpoint"]["checkpointRef"], liveAnchorRef=evidence["liveAnchor"]["anchorRef"])
        live = barrier(value_record, evidence)
        for mutation in ("unknown", "unbounded", "inconsistent", "short"):
            retention = retention_evidence()
            if mutation == "unknown": retention["restoreSources"][0]["sourceClass"] = "unknown"
            elif mutation == "unbounded": retention["restoreSources"][0]["maximumLifetimeSeconds"] = 0
            elif mutation == "inconsistent": retention["restoreSources"][0]["expiresAt"] = "2026-08-10T02:00:00Z"
            else: retention["barrierValidThrough"] = "2026-08-09T02:00:00Z"
            with self.subTest(mutation=mutation), self.assertRaises(CustodyContractError):
                validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention, barrier_evidence=live, trusted_live_barrier=live, authoritative_time="2026-08-08T02:01:00Z")

    def test_new_schema_runtime_structural_parity(self) -> None:
        root = Path(__file__).resolve().parents[1]
        barrier_validator = Draft202012Validator(json.loads((root / "schemas/live-removal-barrier.schema.json").read_text()))
        retention_validator = Draft202012Validator(json.loads((root / "schemas/restore-source-retention.schema.json").read_text()))
        value_record = record("available", 2); evidence = audit_evidence(); value_record["artifactSha256"] = "c" * 64
        live = barrier(value_record, evidence); bad_barrier = dict(live); bad_barrier["provider"] = "specific"
        bad_retention = retention_evidence(); del bad_retention["checkpointValidThrough"]
        self.assertTrue(list(barrier_validator.iter_errors(bad_barrier)))
        self.assertTrue(list(retention_validator.iter_errors(bad_retention)))
        with self.assertRaises(CustodyContractError):
            validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=retention_evidence(), barrier_evidence=bad_barrier, trusted_live_barrier=bad_barrier, authoritative_time="2026-08-08T02:01:00Z")
        with self.assertRaises(CustodyContractError):
            validate_restore(value_record, evidence, snapshot_record_version=2, retention_evidence=bad_retention, barrier_evidence=live, trusted_live_barrier=live, authoritative_time="2026-08-08T02:01:00Z")


if __name__ == "__main__":
    unittest.main()
