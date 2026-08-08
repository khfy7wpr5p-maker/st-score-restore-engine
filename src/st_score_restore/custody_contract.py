"""Provider-neutral Stage 1B custody contract validation.

This module validates metadata evidence only.  It is deliberately not a storage,
identity, key-management, deletion, or restore adapter.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError


SCHEMA_VERSION = "1.0.0"
_ROOT = Path(__file__).resolve().parents[2]
_SCHEMAS = {
    "custody_record": "custody-record.schema.json",
    "audit_evidence": "custody-audit-evidence.schema.json",
    "deletion_receipt": "deletion-receipt.schema.json",
    "live_removal_barrier": "live-removal-barrier.schema.json",
    "restore_retention": "restore-source-retention.schema.json",
}
_ALLOWED_TRANSITIONS = {
    ("absent", "quarantined"),
    ("quarantined", "available"),
    ("quarantined", "deletion_pending"),
    ("available", "deletion_pending"),
    ("deletion_pending", "revoked"),
    ("revoked", "tombstoned"),
}
_ROLE_CONFLICTS = (
    ("access_authorizer", "custody_operator"),
    ("key_custodian", "artifact_access_operator"),
    ("key_policy_approver", "key_operation_executor"),
    ("deletion_authority", "deletion_executor"),
    ("deletion_executor", "deletion_receipt_verifier"),
    ("audit_reviewer", "reviewed_operation_executor"),
    ("emergency_requester", "emergency_approver"),
)


class CustodyContractError(ValueError):
    """Raised when Stage 1B evidence fails closed."""


def canonical_event_digest(event: dict[str, Any]) -> str:
    """Digest an audit event's complete canonical content, excluding its digest."""
    if not isinstance(event, dict):
        raise CustodyContractError("audit event must be an object")
    content = {key: value for key, value in event.items() if key != "eventDigest"}
    try:
        encoded = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CustodyContractError("audit event is not canonical JSON encodable") from error
    return hashlib.sha256(encoded).hexdigest()


def canonical_barrier_fingerprint(barrier: dict[str, Any]) -> str:
    """Digest authoritative barrier content, never a caller-supplied digest."""
    try:
        content = {key: value for key, value in barrier.items() if key != "barrierDigest"}
        encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (KeyError, TypeError, ValueError) as error:
        raise CustodyContractError("security-removal barrier fingerprint content is malformed") from error
    return hashlib.sha256(encoded).hexdigest()


def canonical_receipt_digest(receipt: dict[str, Any]) -> str:
    """Digest all receipt fields except the digest itself as canonical JSON."""
    if not isinstance(receipt, dict):
        raise CustodyContractError("deletion receipt must be an object")
    try:
        encoded = json.dumps(
            {key: value for key, value in receipt.items() if key != "receiptSha256"},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CustodyContractError("deletion receipt is not canonical JSON encodable") from error
    return hashlib.sha256(encoded).hexdigest()


def _schema(name: str) -> dict[str, Any]:
    path = _ROOT / "schemas" / _SCHEMAS[name]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(value)
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        raise CustodyContractError(f"invalid {name} schema: {error}") from error
    return value


def _validate_schema(value: dict[str, Any], name: str) -> None:
    if not isinstance(value, dict):
        raise CustodyContractError(f"{name} must be an object")
    try:
        Draft202012Validator(_schema(name)).validate(value)
    except ValidationError as error:
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        raise CustodyContractError(
            f"{name} schema validation failed at {location}: {error.message}"
        ) from error


def validate_custody_record(record: dict[str, Any]) -> None:
    _validate_schema(record, "custody_record")
    state = record["state"]
    locator = record["locatorRef"]
    if state in {"quarantined", "available", "deletion_pending"} and locator is None:
        raise CustodyContractError(f"{state} record requires an opaque locator")
    if state in {"absent", "revoked", "tombstoned"} and locator is not None:
        raise CustodyContractError(f"{state} record must not retain a locator")
    if state == "tombstoned" and (
        record["deletionStatus"] != "completed"
        or record["backupStatus"] != "complete"
        or record["finalDeletionReceiptRef"] is None
        or record["tombstoneStatus"] != "final"
    ):
        raise CustodyContractError("tombstoned record requires final deletion evidence")
    if record["deletionStatus"] == "completed" and record["finalDeletionReceiptRef"] is None:
        raise CustodyContractError("completed deletion requires a final receipt reference")
    if state == "revoked" and (
        record["revocationStatus"] != "effective"
        or record["deletionStatus"] != "active_boundaries_complete"
        or record["backupStatus"] not in {"tombstone_active", "complete"}
        or record["pendingBackupReceiptRef"] is None
    ):
        raise CustodyContractError("revoked record requires active-copy and backup-tombstone evidence")
    if state == "deletion_pending" and (
        record["deletionStatus"] != "pending"
        or record["revocationStatus"] != "pending"
        or record["tombstoneStatus"] != "intent_recorded"
        or record["pendingBackupReceiptRef"] is None
    ):
        raise CustodyContractError("deletion_pending record requires atomic revocation evidence")


def validate_state_transition(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    receipt: dict[str, Any] | None = None,
    pending_receipt: dict[str, Any] | None = None,
    removal_event: dict[str, Any] | None = None,
    audit_evidence: dict[str, Any] | None = None,
    barrier_evidence: dict[str, Any] | None = None,
    trusted_live_barrier: dict[str, Any] | None = None,
    prior_trusted_barrier: dict[str, Any] | None = None,
    authoritative_time: str | None = None,
) -> None:
    validate_custody_record(previous)
    validate_custody_record(current)
    immutable = ("custodyRecordId", "artifactSha256", "byteSize", "createdAt")
    if any(previous[field] != current[field] for field in immutable):
        raise CustodyContractError("custody identity fields are immutable")
    transition = (previous["state"], current["state"])
    if transition not in _ALLOWED_TRANSITIONS:
        raise CustodyContractError(f"illegal custody state transition: {transition[0]} -> {transition[1]}")
    if current["recordVersion"] != previous["recordVersion"] + 1:
        raise CustodyContractError("record version must increase by exactly one")
    if current["auditPartitionSequence"] <= previous["auditPartitionSequence"]:
        raise CustodyContractError("audit partition sequence must increase")
    if transition in {("available", "deletion_pending"), ("quarantined", "deletion_pending")}:
        if receipt is None:
            raise CustodyContractError("revocation requires atomic pending-receipt evidence")
        validate_deletion_receipt(
            receipt, backup_complete=False, record=current, identity_evidence=audit_evidence
        )
        if current["pendingBackupReceiptRef"] != receipt["receiptId"]:
            raise CustodyContractError("revocation receipt is not the record's pending receipt")
    removal_transitions = {
        ("available", "deletion_pending"), ("quarantined", "deletion_pending"),
        ("deletion_pending", "revoked"), ("revoked", "tombstoned"),
    }
    if transition == ("revoked", "tombstoned") and receipt is None:
        raise CustodyContractError("tombstoning requires the referenced final receipt")
    if transition in removal_transitions:
        if audit_evidence is None or removal_event is None:
            raise CustodyContractError("removal transition requires checkpoint and removal-event evidence")
        validate_audit_evidence(audit_evidence)
        _validate_removal_bindings(current, audit_evidence, removal_event)
        _validate_live_barrier(
            barrier_evidence, trusted_live_barrier=trusted_live_barrier,
            prior_trusted_barrier=prior_trusted_barrier, authoritative_time=authoritative_time,
            record=current, evidence=audit_evidence, require_advancement=True,
        )
        if _utc_timestamp(barrier_evidence["authoritativeTime"], "authoritativeTime") < _utc_timestamp(removal_event["occurredAt"], "removal event occurredAt"):
            raise CustodyContractError("security-removal barrier predates removal acknowledgement")
        bound_receipt = pending_receipt if transition == ("deletion_pending", "revoked") else receipt
        expected_barrier = prior_trusted_barrier if transition == ("deletion_pending", "revoked") else barrier_evidence
        if bound_receipt is not None and (
            expected_barrier is None
            or bound_receipt["barrierDigest"] != expected_barrier["barrierDigest"]
            or bound_receipt["barrierSequence"] != expected_barrier["barrierSequence"]
            or (transition != ("deletion_pending", "revoked") and bound_receipt["removalEventDigest"] != removal_event["eventDigest"])
        ):
            raise CustodyContractError("receipt, removal event, and live barrier bindings mismatch")
    if transition == ("deletion_pending", "revoked"):
        if pending_receipt is None:
            raise CustodyContractError("revocation requires the referenced pending receipt")
        validate_deletion_receipt(
            pending_receipt,
            backup_complete=False,
            record=previous,
            identity_evidence=audit_evidence,
        )
        _validate_receipt_removal_event(pending_receipt, audit_evidence)
        if previous["pendingBackupReceiptRef"] != pending_receipt["receiptId"] or current["pendingBackupReceiptRef"] != pending_receipt["receiptId"]:
            raise CustodyContractError("revocation does not bind the referenced pending receipt")
    if transition == ("revoked", "tombstoned"):
        if receipt is None:
            raise CustodyContractError("tombstoning requires the referenced final receipt")
        validate_deletion_receipt(
            receipt, backup_complete=True, record=current, identity_evidence=audit_evidence
        )
        if current["finalDeletionReceiptRef"] != receipt["receiptId"]:
            raise CustodyContractError("tombstoning receipt is not the record's final receipt")


def _validate_removal_bindings(record: dict[str, Any], evidence: dict[str, Any], event: dict[str, Any]) -> None:
    if event not in evidence["events"] or event is not evidence["events"][-1]:
        raise CustodyContractError("removal event is unrelated or not checkpointed as the chain head")
    expected_operation = {"deletion_pending": "begin_deletion", "revoked": "revoke", "tombstoned": "finalize_deletion"}[record["state"]]
    if (
        event["operationCode"] != expected_operation or event["resultCode"] != "success"
        or event["custodyRecordId"] != record["custodyRecordId"]
        or event["artifactSha256"] != record["artifactSha256"]
        or event["recordVersion"] != record["recordVersion"]
        or event["eventDigest"] != record["lastAuditEventDigest"]
        or evidence["checkpoint"]["checkpointRef"] != record["minimumCheckpointRef"]
        or evidence["liveAnchor"]["anchorRef"] != record["liveAnchorRef"]
    ):
        raise CustodyContractError("removal event, custody record, artifact, version, or checkpoint mismatch")


def _validate_receipt_removal_event(receipt: dict[str, Any], evidence: dict[str, Any]) -> None:
    """Authenticate a pending receipt's removal event from the validated audit chain."""
    matching = [
        event for event in evidence["events"]
        if event["eventDigest"] == receipt["removalEventDigest"]
    ]
    if len(matching) != 1:
        raise CustodyContractError("pending receipt removal event is missing or unrelated")
    event = matching[0]
    if (
        event["eventDigest"] != canonical_event_digest(event)
        or event["operationCode"] != "begin_deletion"
        or event["resultCode"] != "success"
        or event["custodyRecordId"] != receipt["custodyRecordId"]
        or event["artifactSha256"] != receipt["artifactSha256"]
        or event["recordVersion"] != receipt["recordVersion"]
        or receipt["finalAuditEventDigest"] != event["eventDigest"]
        or receipt["checkpointRef"] != evidence["checkpoint"]["checkpointRef"]
        or receipt["anchorRef"] != evidence["liveAnchor"]["anchorRef"]
    ):
        raise CustodyContractError(
            "pending receipt removal event, custody record, artifact, version, checkpoint, or anchor mismatch"
        )


def validate_audit_evidence(evidence: dict[str, Any]) -> None:
    _validate_schema(evidence, "audit_evidence")
    events = evidence["events"]
    seen_ids: set[str] = set()
    replay_fingerprints: dict[str, str] = {}
    previous: dict[str, Any] | None = None
    for event in events:
        if event["eventDigest"] != canonical_event_digest(event):
            raise CustodyContractError("audit event digest does not match canonical event content")
        if event["eventId"] in seen_ids:
            raise CustodyContractError("duplicate audit event ID")
        seen_ids.add(event["eventId"])
        known = replay_fingerprints.setdefault(event["idempotencyRef"], event["requestFingerprint"])
        if known != event["requestFingerprint"]:
            raise CustodyContractError("conflicting idempotency replay fingerprint")
        if previous is None:
            if (
                event["previousEventDigest"] is not None
                or event["partitionSequence"] != 1
                or event["recordVersion"] != 1
            ):
                raise CustodyContractError("audit evidence is truncated or does not start at genesis")
        else:
            if event["previousEventDigest"] != canonical_event_digest(previous):
                raise CustodyContractError("broken audit chain continuity")
            if event["partitionSequence"] != previous["partitionSequence"] + 1:
                raise CustodyContractError("audit partition sequence is not monotonic and contiguous")
            if event["recordVersion"] != previous["recordVersion"] + 1:
                raise CustodyContractError("audit record version is not monotonic and contiguous")
            if (
                event["custodyRecordId"] != previous["custodyRecordId"]
                or event["artifactSha256"] != previous["artifactSha256"]
            ):
                raise CustodyContractError("audit chain mixes custody identities")
        previous = event

    identities = {identity["actorRef"]: identity for identity in evidence["identities"]}
    if len(identities) != len(evidence["identities"]):
        raise CustodyContractError("duplicate identity actor reference")
    for actor_ref in {event["actorRef"] for event in events} | {
        assignment["actorRef"] for assignment in evidence["roleAssignments"]
    }:
        identity = identities.get(actor_ref)
        if identity is None or identity["status"] != "active" or not identity["fresh"]:
            raise CustodyContractError("identity is missing, stale, disabled, or revoked")

    roles_by_person: dict[str, set[str]] = {}
    assigned_pairs: set[tuple[str, str]] = set()
    for assignment in evidence["roleAssignments"]:
        assigned_pairs.add((assignment["actorRef"], assignment["roleCode"]))
        person = identities[assignment["actorRef"]]["personRef"]
        roles_by_person.setdefault(person, set()).add(assignment["roleCode"])
    for event in events:
        if (event["actorRef"], event["roleCode"]) not in assigned_pairs:
            raise CustodyContractError("audit actor does not hold the recorded role")
    for roles in roles_by_person.values():
        for left, right in _ROLE_CONFLICTS:
            if left in roles and right in roles:
                raise CustodyContractError(f"prohibited role collision: {left} and {right}")
        if {"purpose_authorizer", "access_authorizer", "deletion_receipt_verifier"} <= roles:
            raise CustodyContractError("one person cannot authorize purpose, access, and final deletion evidence")

    assert previous is not None
    checkpoint = evidence["checkpoint"]
    anchor = evidence["liveAnchor"]
    if not anchor["valid"] or not anchor["fresh"] or anchor["source"] != "live_independent":
        raise CustodyContractError("live anchor is missing, stale, invalid, or snapshot-sourced")
    if checkpoint["acceptedPartitionSequence"] != previous["partitionSequence"]:
        raise CustodyContractError("checkpoint sequence does not match the audit chain")
    recomputed_head = canonical_event_digest(previous)
    if checkpoint["chainHeadDigest"] != recomputed_head:
        raise CustodyContractError("checkpoint chain head does not match the audit chain")
    if checkpoint["custodyRecordVersion"] != previous["recordVersion"]:
        raise CustodyContractError("checkpoint custody version does not match the audit chain")
    if checkpoint["acceptedPartitionSequence"] < anchor["minimumAcceptedSequence"]:
        raise CustodyContractError("checkpoint is stale relative to the live anchor")
    if (
        checkpoint["acceptedPartitionSequence"] != anchor["minimumAcceptedSequence"]
        or checkpoint["chainHeadDigest"] != anchor["chainHeadDigest"]
        or checkpoint["custodyRecordVersion"] != anchor["custodyRecordVersion"]
    ):
        raise CustodyContractError("checkpoint and live anchor mismatch")

    emergency = evidence["emergencyAccess"]
    if emergency is not None:
        participants = [emergency["requesterRef"], *emergency["approverRefs"]]
        participant_identities = [identities.get(actor) for actor in participants]
        if any(item is None or item["status"] != "active" or not item["fresh"] for item in participant_identities):
            raise CustodyContractError("emergency participant identity is not active and fresh")
        people = [item["personRef"] for item in participant_identities if item is not None]
        if len(set(people)) != 3:
            raise CustodyContractError("emergency requester and approvers must be independent people")
        requester_roles = roles_by_person.get(people[0], set())
        approver_roles = [roles_by_person.get(person, set()) for person in people[1:]]
        if "emergency_requester" not in requester_roles or any(
            "emergency_approver" not in roles for roles in approver_roles
        ):
            raise CustodyContractError("emergency participants are missing required roles")
        required_true = ("digestMatches", "byteSizeMatches", "retentionValid", "purposeAuthorized", "rightsApproved", "privacyApproved", "environmentAllowed", "storageClassAllowed", "auditDurable")
        required_false = ("purposeBlockingHold", "deletionOrRevocationActive", "incidentLockActive")
        if emergency["state"] != "available" or not all(emergency[key] for key in required_true) or any(emergency[key] for key in required_false):
            raise CustodyContractError("emergency access cannot bypass an ordinary denial condition")


def validate_deletion_receipt(
    receipt: dict[str, Any],
    *,
    backup_complete: bool,
    record: dict[str, Any] | None = None,
    identity_evidence: dict[str, Any] | None = None,
) -> None:
    _validate_schema(receipt, "deletion_receipt")
    if receipt["receiptSha256"] != canonical_receipt_digest(receipt):
        raise CustodyContractError("deletion receipt digest does not match canonical receipt content")
    pending = receipt["receiptType"] == "revocation_pending_backup"
    if pending and (
        receipt["deletionStatus"] == "completed"
        or receipt["completedAt"] is not None
        or receipt["backupDisposition"] != "pending_expiry"
    ):
        raise CustodyContractError("pending-backup receipt cannot claim final completion")
    if not pending and (
        not backup_complete
        or receipt["deletionStatus"] != "completed"
        or receipt["completedAt"] is None
        or receipt["backupDisposition"] not in {"expired", "verified_destroyed"}
        or receipt["backupTombstoneStatus"] != "complete"
    ):
        raise CustodyContractError("final deletion receipt is forbidden before backup completion")
    if identity_evidence is None:
        raise CustodyContractError("verified executor and verifier identity evidence is required")
    validate_audit_evidence(identity_evidence)
    identities = {item["actorRef"]: item for item in identity_evidence["identities"]}
    assignments = {
        (item["actorRef"], item["roleCode"])
        for item in identity_evidence["roleAssignments"]
    }
    executor = identities.get(receipt["executorRef"])
    verifier = identities.get(receipt["verifierRef"])
    if executor is None or verifier is None:
        raise CustodyContractError("executor or verifier identity evidence is missing")
    if any(item["status"] != "active" or not item["fresh"] for item in (executor, verifier)):
        raise CustodyContractError("executor or verifier identity evidence is stale or unverified")
    if (
        executor["personRef"] != receipt["executorPersonRef"]
        or verifier["personRef"] != receipt["verifierPersonRef"]
    ):
        raise CustodyContractError("receipt person reference does not match verified actor identity")
    if (
        (receipt["executorRef"], "deletion_executor") not in assignments
        or (receipt["verifierRef"], "deletion_receipt_verifier") not in assignments
    ):
        raise CustodyContractError("executor or verifier is missing the required authorized role")
    if (
        receipt["executorRef"] == receipt["verifierRef"]
        or executor["personRef"] == verifier["personRef"]
    ):
        raise CustodyContractError("deletion executor and receipt verifier must be independent")
    if record is not None:
        validate_custody_record(record)
        expected_version = record["recordVersion"]
        if (
            receipt["custodyRecordId"] != record["custodyRecordId"]
            or receipt["artifactSha256"] != record["artifactSha256"]
            or receipt["recordVersion"] != expected_version
            or receipt["finalAuditEventDigest"] != record["lastAuditEventDigest"]
            or receipt["checkpointRef"] != record["minimumCheckpointRef"]
            or receipt["anchorRef"] != record["liveAnchorRef"]
        ):
            raise CustodyContractError("receipt does not match custody record identity, artifact, version, or evidence")


def validate_restore(
    record: dict[str, Any],
    evidence: dict[str, Any],
    *,
    snapshot_record_version: int,
    retention_valid: bool | None = None,
    evidence_retained: bool | None = None,
    retention_evidence: dict[str, Any] | None = None,
    barrier_evidence: dict[str, Any] | None = None,
    trusted_live_barrier: dict[str, Any] | None = None,
    prior_trusted_barrier: dict[str, Any] | None = None,
    authoritative_time: str | None = None,
) -> None:
    """Reject restore sources that can resurrect stale or revoked custody data."""
    validate_custody_record(record)
    validate_audit_evidence(evidence)
    last = evidence["events"][-1]
    if (
        record["lastAuditEventDigest"] != canonical_event_digest(last)
        or record["auditPartitionSequence"] != last["partitionSequence"]
    ):
        raise CustodyContractError("custody record does not match the recomputed audit chain head")
    _validate_live_barrier(
        barrier_evidence,
        trusted_live_barrier=trusted_live_barrier,
        prior_trusted_barrier=prior_trusted_barrier,
        authoritative_time=authoritative_time,
        record=record,
        evidence=evidence,
        require_advancement=False,
    )
    if snapshot_record_version != record["recordVersion"] or last["recordVersion"] != record["recordVersion"]:
        raise CustodyContractError("restore evidence is stale or predates the custody record")
    if last["custodyRecordId"] != record["custodyRecordId"] or last["artifactSha256"] != record["artifactSha256"]:
        raise CustodyContractError("restore evidence does not match the custody record")
    if record["state"] != "available" or record["revocationStatus"] != "not_revoked":
        raise CustodyContractError("restore cannot resurrect unavailable or revoked data")
    if retention_valid is not None or evidence_retained is not None:
        raise CustodyContractError("caller-controlled retention booleans are not trusted")
    _validate_retention_horizon(retention_evidence, authoritative_time=authoritative_time)


_REMOVAL_TYPES = {
    "none", "rights_revocation", "privacy_revocation", "purpose_revocation",
    "retention_expiry", "incident_lock", "deletion_tombstone",
}


def _utc_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise CustodyContractError(f"security-removal barrier {field} is malformed")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise CustodyContractError(f"security-removal barrier {field} is malformed") from error
    return parsed


def _validate_live_barrier(
    barrier: dict[str, Any] | None,
    *,
    trusted_live_barrier: dict[str, Any] | None,
    prior_trusted_barrier: dict[str, Any] | None,
    authoritative_time: str | None,
    record: dict[str, Any],
    evidence: dict[str, Any],
    require_advancement: bool,
) -> None:
    if barrier is None or trusted_live_barrier is None or authoritative_time is None:
        raise CustodyContractError("fresh live security-removal barrier evidence is required")
    _validate_schema(barrier, "live_removal_barrier")
    _validate_schema(trusted_live_barrier, "live_removal_barrier")
    if prior_trusted_barrier is not None:
        _validate_schema(prior_trusted_barrier, "live_removal_barrier")
    digest = canonical_barrier_fingerprint(barrier)
    if barrier["barrierDigest"] != digest:
        raise CustodyContractError("security-removal barrier canonical digest mismatch")
    if trusted_live_barrier["barrierDigest"] != canonical_barrier_fingerprint(trusted_live_barrier):
        raise CustodyContractError("authenticated live barrier digest is invalid")
    if barrier != trusted_live_barrier:
        raise CustodyContractError("barrier differs from independently authenticated live state")
    minimum = barrier["minimumForbiddenRecordVersion"]
    observed = _utc_timestamp(barrier["authoritativeTime"], "authoritativeTime")
    expires = _utc_timestamp(barrier["validUntil"], "validUntil")
    now = _utc_timestamp(authoritative_time, "authoritative time")
    if observed > now or now > expires or observed >= expires:
        raise CustodyContractError("security-removal barrier is stale")
    if prior_trusted_barrier is not None:
        if prior_trusted_barrier["barrierDigest"] != canonical_barrier_fingerprint(prior_trusted_barrier):
            raise CustodyContractError("prior trusted barrier digest is invalid")
        prior_sequence = prior_trusted_barrier["barrierSequence"]
        if barrier["barrierSequence"] <= prior_sequence:
            raise CustodyContractError("security-removal barrier replay or rollback")
        if barrier["custodyRecordId"] != prior_trusted_barrier["custodyRecordId"] or barrier["artifactSha256"] != prior_trusted_barrier["artifactSha256"]:
            raise CustodyContractError("security-removal barrier fork")
    elif require_advancement:
        raise CustodyContractError("trusted prior barrier is required to prove advancement")

    checkpoint = evidence["checkpoint"]
    anchor = evidence["liveAnchor"]
    if barrier["artifactSha256"] != record["artifactSha256"] or barrier["custodyRecordId"] != record["custodyRecordId"]:
        raise CustodyContractError("security-removal barrier artifact or custody record mismatch")
    if (
        barrier["partitionSequence"] != checkpoint["acceptedPartitionSequence"]
        or barrier["chainHeadDigest"] != checkpoint["chainHeadDigest"]
        or barrier["checkpointRef"] != checkpoint["checkpointRef"]
        or barrier["anchorRef"] != anchor["anchorRef"]
        or barrier["partitionSequence"] != record["auditPartitionSequence"]
        or barrier["checkpointRef"] != record["minimumCheckpointRef"]
        or barrier["anchorRef"] != record["liveAnchorRef"]
    ):
        raise CustodyContractError("security-removal barrier checkpoint or live anchor mismatch")
    # A matching live removal is an absolute deny.  The minimum version is
    # retained and validated to explain which restored versions are stale, but
    # a newer snapshot is not evidence that removed artifact bytes are absent.
    if minimum is not None and not require_advancement:
        raise CustodyContractError("restore source predates a live security removal and cannot resurrect removed data")


_RESTORE_SOURCE_CLASSES = {"primary_replica", "replica", "cache", "transient_store", "backup", "archive"}
_HORIZON_SAFETY_MARGIN_SECONDS = 86400


def _validate_retention_horizon(retention: dict[str, Any] | None, *, authoritative_time: str | None) -> None:
    if retention is None or authoritative_time is None:
        raise CustodyContractError("structured restore-source retention evidence is required")
    _validate_schema(retention, "restore_retention")
    sources = retention["restoreSources"]
    if {item["sourceClass"] for item in sources} != _RESTORE_SOURCE_CLASSES:
        raise CustodyContractError("restore-source classes are missing, duplicated, or unknown")
    observed = _utc_timestamp(retention["observedAt"], "retention observedAt")
    now = _utc_timestamp(authoritative_time, "authoritative time")
    if observed > now or now > _utc_timestamp(retention["validUntil"], "retention validUntil"):
        raise CustodyContractError("restore-source retention evidence is stale")
    expiries = []
    for source in sources:
        expiry = _utc_timestamp(source["expiresAt"], f'{source["sourceClass"]} expiresAt')
        if expiry <= observed or (expiry - observed).total_seconds() > source["maximumLifetimeSeconds"]:
            raise CustodyContractError("restore-source expiry is inconsistent or exceeds its verified maximum lifetime")
        expiries.append(expiry)
    required = max(expiries).timestamp() + _HORIZON_SAFETY_MARGIN_SECONDS
    horizon = _utc_timestamp(retention["antiResurrectionHorizon"], "antiResurrectionHorizon")
    if horizon.timestamp() != required:
        raise CustodyContractError("anti-resurrection horizon is not the maximum verified expiry plus safety margin")
    for field in ("barrierValidThrough", "auditValidThrough", "checkpointValidThrough", "tombstoneValidThrough"):
        if _utc_timestamp(retention[field], field) < horizon:
            raise CustodyContractError("security evidence expires before the anti-resurrection horizon")


def validate_schema_contracts() -> None:
    """Validate that all Stage 1B schemas are valid and version-bound."""
    for name in _SCHEMAS:
        schema = _schema(name)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise CustodyContractError(f"{name} must use JSON Schema Draft 2020-12")
        if schema.get("properties", {}).get("schemaVersion", {}).get("const") != SCHEMA_VERSION:
            raise CustodyContractError(f"{name} schema version drift")
