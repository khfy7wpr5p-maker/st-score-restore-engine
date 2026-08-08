"""Provider-neutral, non-production Stage 1B operational reference drill.

The adapter in this module exists only to exercise the custody/operations
contract with run-created, non-sensitive marker bytes.  It does not select or
configure a storage provider, network service, identity provider, key manager,
or production resource.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable


class DrillError(ValueError):
    """Raised when the reference drill must fail closed."""


ROLE_CONFLICTS = (
    ("access_authorizer", "custody_operator"),
    ("key_custodian", "artifact_access_operator"),
    ("key_policy_approver", "key_operation_executor"),
    ("deletion_authority", "deletion_executor"),
    ("deletion_executor", "deletion_receipt_verifier"),
    ("audit_reviewer", "reviewed_operation_executor"),
    ("emergency_requester", "emergency_approver"),
)


@dataclass(frozen=True)
class Identity:
    actor_ref: str
    person_ref: str
    roles: frozenset[str]
    active: bool = True
    fresh: bool = True


@dataclass(frozen=True)
class Snapshot:
    artifact_sha256: str
    data: bytes
    state: str
    record_version: int
    checkpoint_sequence: int
    checkpoint_digest: str


def audit_event_digest(event: dict[str, Any]) -> str:
    content = {key: value for key, value in event.items() if key != "digest"}
    try:
        encoded = json.dumps(
            content,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DrillError("audit event is not canonical JSON") from error
    return hashlib.sha256(encoded).hexdigest()


def validate_audit_chain(
    events: Iterable[dict[str, Any]],
    *,
    anchor_sequence: int,
    anchor_digest: str,
) -> None:
    chain = list(events)
    if not chain:
        raise DrillError("audit chain is missing")
    seen: set[str] = set()
    previous_digest: str | None = None
    for expected_sequence, event in enumerate(chain, 1):
        event_id = event.get("eventId")
        if not isinstance(event_id, str) or event_id in seen:
            raise DrillError("duplicate or malformed audit event")
        seen.add(event_id)
        if event.get("sequence") != expected_sequence:
            raise DrillError("audit sequence is not contiguous")
        if event.get("previousDigest") != previous_digest:
            raise DrillError("audit chain continuity is broken")
        digest = audit_event_digest(event)
        if event.get("digest") != digest:
            raise DrillError("audit event digest mismatch")
        previous_digest = digest
    if anchor_sequence != len(chain) or anchor_digest != previous_digest:
        raise DrillError("audit chain conflicts with the independent live anchor")


class InMemoryCustodyReference:
    """Small fail-closed adapter used only by the Stage 1B operational drill."""

    MAX_MARKER_BYTES = 4096
    MAX_EXPANSION_RATIO = 8.0

    def __init__(self) -> None:
        self.state = "absent"
        self.record_version = 0
        self.artifact_sha256: str | None = None
        self.byte_size = 0
        self.primary: bytes | None = None
        self.replica: bytes | None = None
        self.cache: bytes | None = None
        self.transient: bytes | None = None
        self.backup: bytes | None = None
        self.tombstone_intent = False
        self.backup_tombstone = False
        self.work_fenced = False
        self._identities: dict[str, Identity] = {}
        self._grants: dict[str, tuple[str, str, str, str]] = {}
        self._events: list[dict[str, Any]] = []
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._pending_receipt: dict[str, Any] | None = None
        self._final_receipt: dict[str, Any] | None = None
        self._removal_control: dict[str, Any] = {
            "intents": {},
            "barrier": None,
            "checkpoint": None,
        }
        self.allowed_environment = "environment_reference"
        self.allowed_storage_class = "storage_class_reference"
        self.allowed_purpose = "evaluation_reference"

    @property
    def audit_events(self) -> list[dict[str, Any]]:
        return [dict(event) for event in self._events]

    @property
    def anchor_sequence(self) -> int:
        return len(self._events)

    @property
    def anchor_digest(self) -> str:
        if not self._events:
            raise DrillError("live anchor is unavailable before the first durable event")
        return self._events[-1]["digest"]

    @property
    def pending_receipt(self) -> dict[str, Any] | None:
        return None if self._pending_receipt is None else dict(self._pending_receipt)

    @property
    def final_receipt(self) -> dict[str, Any] | None:
        return None if self._final_receipt is None else dict(self._final_receipt)

    @property
    def removal_checkpoint(self) -> dict[str, Any] | None:
        checkpoint = self._removal_control["checkpoint"]
        return None if checkpoint is None else dict(checkpoint)

    def pending_removal_intent(self, request_id: str) -> dict[str, Any] | None:
        intent = self._removal_control["intents"].get(request_id)
        return None if intent is None else dict(intent)

    def restart(self) -> "InMemoryCustodyReference":
        """Model a process restart while retaining durable security-control state."""
        restarted = copy.deepcopy(self)
        restarted._grants.clear()
        return restarted

    def _removal_fingerprint(self, request_id: str, trigger: str) -> str:
        if not self.artifact_sha256:
            raise DrillError("removal intent requires an artifact identity")
        payload = {
            "artifactSha256": self.artifact_sha256,
            "requestId": request_id,
            "trigger": trigger,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def persist_removal_intent(self, request_id: str, *, trigger: str = "purpose_revocation") -> str:
        fingerprint = self._removal_fingerprint(request_id, trigger)
        known = self._removal_control["intents"].get(request_id)
        if known is not None:
            if known["fingerprint"] != fingerprint:
                raise DrillError("conflicting pending removal intent")
            return fingerprint
        self._removal_control["intents"][request_id] = {
            "requestId": request_id,
            "artifactSha256": self.artifact_sha256,
            "trigger": trigger,
            "fingerprint": fingerprint,
            "acknowledged": False,
            "publicationAttempts": 0,
            "localAuditSequence": None,
            "localAuditDigest": None,
        }
        return fingerprint

    def publish_removal_barrier(
        self,
        request_id: str,
        *,
        acknowledged_fingerprint: str | None = None,
    ) -> str:
        intent = self._removal_control["intents"].get(request_id)
        if intent is None:
            raise DrillError("pending removal intent is missing")
        intent["publicationAttempts"] += 1
        self._removal_control["barrier"] = {
            "requestId": request_id,
            "artifactSha256": intent["artifactSha256"],
            "fingerprint": intent["fingerprint"],
            "committed": True,
        }
        if acknowledged_fingerprint is None:
            return intent["fingerprint"]
        if acknowledged_fingerprint != intent["fingerprint"]:
            raise DrillError("barrier acknowledgement does not match the pending removal intent")
        intent["acknowledged"] = True
        return intent["fingerprint"]

    def _removal_control_blocks_access(self) -> bool:
        for intent in self._removal_control["intents"].values():
            if intent.get("artifactSha256") == self.artifact_sha256:
                return True
        barrier = self._removal_control["barrier"]
        return bool(
            barrier
            and barrier.get("committed")
            and barrier.get("artifactSha256") == self.artifact_sha256
        )

    def _require_acknowledged_barrier(self, request_id: str) -> dict[str, Any]:
        intent = self._removal_control["intents"].get(request_id)
        barrier = self._removal_control["barrier"]
        if intent is None or not intent.get("acknowledged"):
            raise DrillError("removal barrier has not acknowledged the pending intent")
        if (
            not barrier
            or not barrier.get("committed")
            or barrier.get("requestId") != request_id
            or barrier.get("fingerprint") != intent.get("fingerprint")
            or barrier.get("artifactSha256") != self.artifact_sha256
        ):
            raise DrillError("removal barrier does not match the pending intent")
        return intent

    def advance_removal_checkpoint(self, request_id: str) -> None:
        intent = self._require_acknowledged_barrier(request_id)
        sequence = intent.get("localAuditSequence")
        digest = intent.get("localAuditDigest")
        if not isinstance(sequence, int) or not isinstance(digest, str):
            raise DrillError("removal audit event is not available for checkpoint advancement")
        self._removal_control["checkpoint"] = {
            "requestId": request_id,
            "fingerprint": intent["fingerprint"],
            "sequence": sequence,
            "digest": digest,
        }

    def register_identity(
        self,
        actor_ref: str,
        person_ref: str,
        roles: Iterable[str],
        *,
        active: bool = True,
        fresh: bool = True,
    ) -> None:
        if actor_ref in self._identities:
            raise DrillError("duplicate actor reference")
        identity = Identity(actor_ref, person_ref, frozenset(roles), active, fresh)
        self._identities[actor_ref] = identity
        try:
            self._validate_role_separation()
        except DrillError:
            del self._identities[actor_ref]
            raise

    def _validate_role_separation(self) -> None:
        roles_by_person: dict[str, set[str]] = {}
        for identity in self._identities.values():
            roles_by_person.setdefault(identity.person_ref, set()).update(identity.roles)
        for roles in roles_by_person.values():
            for left, right in ROLE_CONFLICTS:
                if left in roles and right in roles:
                    raise DrillError(f"prohibited role collision: {left} and {right}")
            if {"purpose_authorizer", "access_authorizer", "deletion_receipt_verifier"} <= roles:
                raise DrillError("one person cannot authorize purpose, access, and deletion evidence")

    def _require_role(self, actor_ref: str, role: str) -> Identity:
        identity = self._identities.get(actor_ref)
        if identity is None or not identity.active or not identity.fresh:
            raise DrillError("identity is missing, stale, disabled, or revoked")
        if role not in identity.roles:
            raise DrillError(f"actor lacks required role: {role}")
        return identity

    def _check_expected_version(self, expected_version: int) -> None:
        if expected_version != self.record_version:
            raise DrillError("compare-and-swap version conflict")

    def _append_audit(self, operation: str, result: str = "success", *, durable: bool = True) -> None:
        if not durable:
            raise DrillError("audit durability failed")
        sequence = len(self._events) + 1
        previous = self._events[-1]["digest"] if self._events else None
        event = {
            "eventId": f"event-{sequence:04d}",
            "sequence": sequence,
            "recordVersion": self.record_version,
            "operation": operation,
            "result": result,
            "artifactSha256": self.artifact_sha256,
            "previousDigest": previous,
            "digest": "0" * 64,
        }
        event["digest"] = audit_event_digest(event)
        self._events.append(event)

    def ingest(self, marker_bytes: bytes, *, expected_version: int = 0) -> None:
        self._check_expected_version(expected_version)
        if self.state != "absent":
            raise DrillError("intake requires absent state")
        if not isinstance(marker_bytes, bytes) or not marker_bytes or len(marker_bytes) > self.MAX_MARKER_BYTES:
            raise DrillError("reference marker bytes are invalid or out of bounds")
        self.artifact_sha256 = hashlib.sha256(marker_bytes).hexdigest()
        self.byte_size = len(marker_bytes)
        self.primary = bytes(marker_bytes)
        self.record_version = 1
        self.state = "quarantined"
        self._append_audit("quarantine")

    def promote(
        self,
        *,
        expected_version: int,
        inspection_timeout: bool = False,
        inspection_crash: bool = False,
        network_attempt: bool = False,
        expansion_ratio: float = 1.0,
        policy_authorized: bool = True,
        audit_durable: bool = True,
    ) -> None:
        self._check_expected_version(expected_version)
        if self.state != "quarantined":
            raise DrillError("promotion requires quarantined state")
        if inspection_timeout:
            raise DrillError("inspection timeout")
        if inspection_crash:
            raise DrillError("inspection crash")
        if network_attempt:
            raise DrillError("inspection network attempt")
        if expansion_ratio < 0 or expansion_ratio > self.MAX_EXPANSION_RATIO:
            raise DrillError("inspection expansion limit exceeded")
        if not policy_authorized:
            raise DrillError("promotion policy denied")
        if self.primary is None or hashlib.sha256(self.primary).hexdigest() != self.artifact_sha256:
            raise DrillError("quarantine digest mismatch")
        if not audit_durable:
            raise DrillError("audit durability failed")
        self.record_version += 1
        self.state = "available"
        self.replica = bytes(self.primary)
        self.cache = bytes(self.primary)
        self.transient = bytes(self.primary)
        self.backup = bytes(self.primary)
        self._append_audit("promote")

    def grant_read(
        self,
        actor_ref: str,
        *,
        purpose: str,
        environment: str,
        storage_class: str,
        audit_durable: bool = True,
    ) -> str:
        self._require_role(actor_ref, "artifact_access_operator")
        if self.state != "available" or self.work_fenced or self._removal_control_blocks_access():
            raise DrillError("artifact is not readable")
        if purpose != self.allowed_purpose:
            raise DrillError("purpose is not authorized")
        if environment != self.allowed_environment:
            raise DrillError("environment is not authorized")
        if storage_class != self.allowed_storage_class:
            raise DrillError("storage class is not authorized")
        self._append_audit("authorize_read", "allow", durable=audit_durable)
        token = f"grant-{len(self._grants) + 1:04d}"
        self._grants[token] = (actor_ref, purpose, environment, storage_class)
        return token

    def read(self, token: str) -> bytes:
        if (
            self.state != "available"
            or self.work_fenced
            or self._removal_control_blocks_access()
            or token not in self._grants
            or self.primary is None
        ):
            raise DrillError("read is denied")
        return bytes(self.primary)

    def emergency_read(self, requester: str, approvers: tuple[str, str], **conditions: bool) -> bytes:
        requester_identity = self._require_role(requester, "emergency_requester")
        approver_identities = [self._require_role(actor, "emergency_approver") for actor in approvers]
        people = {requester_identity.person_ref, *(identity.person_ref for identity in approver_identities)}
        if len(people) != 3:
            raise DrillError("emergency participants are not independent real people")
        required_true = (
            "digest_matches", "byte_size_matches", "retention_valid", "purpose_authorized",
            "rights_approved", "privacy_approved", "environment_allowed", "storage_class_allowed",
            "audit_durable",
        )
        required_false = ("purpose_blocking_hold", "deletion_or_revocation_active", "incident_lock_active")
        if self.state != "available" or self._removal_control_blocks_access():
            raise DrillError("emergency access cannot bypass custody state")
        if not all(conditions.get(name, False) for name in required_true):
            raise DrillError("emergency access cannot bypass an ordinary allow condition")
        if any(conditions.get(name, False) for name in required_false):
            raise DrillError("emergency access cannot bypass an ordinary denial condition")
        if self.primary is None:
            raise DrillError("emergency payload is unavailable")
        self._append_audit("emergency_access", "allow")
        return bytes(self.primary)

    def begin_revocation(
        self,
        request_id: str,
        *,
        expected_version: int,
        authority_actor: str,
        executor_actor: str,
        verifier_actor: str,
        trigger: str = "purpose_revocation",
        access_authorizer_allows: bool | None = None,
        audit_durable: bool = True,
        fencing_complete: bool = True,
        remove_replica: bool = True,
        remove_cache: bool = True,
        backup_tombstone: bool = True,
        checkpoint_advanced: bool = True,
    ) -> dict[str, Any]:
        del access_authorizer_allows  # Revocation is immediate and cannot be vetoed here.
        fingerprint = (trigger, self.artifact_sha256 or "")
        known = self._idempotency.get(request_id)
        if known is not None:
            if known != fingerprint:
                raise DrillError("conflicting idempotency replay")
            if self._pending_receipt is None:
                raise DrillError("idempotency state is incomplete")
            return dict(self._pending_receipt)

        self._check_expected_version(expected_version)
        if self.state not in {"available", "quarantined"}:
            raise DrillError("revocation requires an active or quarantined object")
        self._require_role(authority_actor, "deletion_authority")
        executor = self._require_role(executor_actor, "deletion_executor")
        verifier = self._require_role(verifier_actor, "deletion_receipt_verifier")
        if executor.actor_ref == verifier.actor_ref or executor.person_ref == verifier.person_ref:
            raise DrillError("deletion executor and verifier are not independent")

        intent = self._removal_control["intents"].get(request_id)
        if intent is None:
            intent_fingerprint = self.persist_removal_intent(request_id, trigger=trigger)
            self.publish_removal_barrier(
                request_id,
                acknowledged_fingerprint=intent_fingerprint,
            )
        else:
            if intent.get("trigger") != trigger or intent.get("artifactSha256") != self.artifact_sha256:
                raise DrillError("pending removal intent conflicts with revocation request")
            self._require_acknowledged_barrier(request_id)

        # Fail closed before any potentially fallible evidence or deletion step.
        self.record_version += 1
        self.state = "deletion_pending"
        self.work_fenced = True
        self._grants.clear()
        self.tombstone_intent = True
        self._idempotency[request_id] = fingerprint

        try:
            self._append_audit("begin_deletion", durable=audit_durable)
        except DrillError:
            raise
        intent = self._removal_control["intents"][request_id]
        intent["localAuditSequence"] = self.anchor_sequence
        intent["localAuditDigest"] = self.anchor_digest
        if not fencing_complete:
            raise DrillError("work fencing is incomplete")
        if checkpoint_advanced:
            self.advance_removal_checkpoint(request_id)

        self.primary = None
        if remove_replica:
            self.replica = None
        if remove_cache:
            self.cache = None
        self.transient = None
        self.backup_tombstone = backup_tombstone
        if self.replica is not None or self.cache is not None:
            raise DrillError("active replica or cache deletion is incomplete")
        if not self.backup_tombstone:
            raise DrillError("backup tombstone is missing")

        receipt = {
            "type": "revocation_pending_backup",
            "requestId": request_id,
            "recordVersion": self.record_version,
            "artifactSha256": self.artifact_sha256,
            "grantsInvalidated": True,
            "workFenced": True,
            "primaryDisposition": "removed",
            "replicaDisposition": "removed",
            "cacheDisposition": "removed",
            "transientDisposition": "removed",
            "backupTombstone": True,
            "backupDisposition": "pending_expiry",
            "deletionStatus": "pending",
            "completed": False,
            "executor": executor.actor_ref,
            "verifier": verifier.actor_ref,
            "auditDigest": self.anchor_digest,
        }
        self.validate_receipt(receipt, backup_complete=False)
        self._pending_receipt = receipt
        return dict(receipt)

    def confirm_revoked(self, *, expected_version: int, audit_durable: bool = True) -> None:
        self._check_expected_version(expected_version)
        if self.state != "deletion_pending":
            raise DrillError("revocation confirmation requires deletion_pending state")
        if self.primary is not None or self.replica is not None or self.cache is not None or self.transient is not None:
            raise DrillError("active copies remain")
        if not self.tombstone_intent or not self.backup_tombstone or self._pending_receipt is None:
            raise DrillError("revocation evidence is incomplete")
        request_id = self._pending_receipt.get("requestId")
        if not isinstance(request_id, str):
            raise DrillError("revocation receipt request binding is missing")
        intent = self._require_acknowledged_barrier(request_id)
        checkpoint = self._removal_control["checkpoint"]
        if (
            checkpoint is None
            or checkpoint.get("requestId") != request_id
            or checkpoint.get("fingerprint") != intent.get("fingerprint")
            or checkpoint.get("sequence") != intent.get("localAuditSequence")
            or checkpoint.get("digest") != intent.get("localAuditDigest")
        ):
            raise DrillError("removal checkpoint has not advanced to the deletion audit event")
        if not audit_durable:
            raise DrillError("audit durability failed")
        self.record_version += 1
        self.state = "revoked"
        self._append_audit("revoke")

    def finalize_deletion(
        self,
        *,
        expected_version: int,
        executor_actor: str,
        verifier_actor: str,
        backup_complete: bool,
        audit_durable: bool = True,
    ) -> dict[str, Any]:
        self._check_expected_version(expected_version)
        if self.state != "revoked":
            raise DrillError("final deletion requires revoked state")
        executor = self._require_role(executor_actor, "deletion_executor")
        verifier = self._require_role(verifier_actor, "deletion_receipt_verifier")
        if executor.actor_ref == verifier.actor_ref or executor.person_ref == verifier.person_ref:
            raise DrillError("final receipt lacks independent verification")
        if not backup_complete:
            raise DrillError("final receipt is forbidden before backup completion")
        if not audit_durable:
            raise DrillError("audit durability failed")

        self.backup = None
        self.record_version += 1
        self.state = "tombstoned"
        self._append_audit("finalize_deletion")
        receipt = {
            "type": "final_deletion_complete",
            "recordVersion": self.record_version,
            "artifactSha256": self.artifact_sha256,
            "backupDisposition": "expired",
            "deletionStatus": "completed",
            "completed": True,
            "executor": executor.actor_ref,
            "verifier": verifier.actor_ref,
            "auditDigest": self.anchor_digest,
        }
        self.validate_receipt(receipt, backup_complete=True)
        self._final_receipt = receipt
        return dict(receipt)

    @staticmethod
    def validate_receipt(receipt: dict[str, Any], *, backup_complete: bool) -> None:
        if receipt.get("type") == "revocation_pending_backup":
            if receipt.get("completed") or receipt.get("deletionStatus") == "completed":
                raise DrillError("pending-backup receipt cannot claim completion")
            if receipt.get("backupDisposition") != "pending_expiry":
                raise DrillError("pending-backup receipt has invalid backup disposition")
        elif receipt.get("type") == "final_deletion_complete":
            if not backup_complete or not receipt.get("completed") or receipt.get("deletionStatus") != "completed":
                raise DrillError("final receipt is forbidden before backup completion")
            if receipt.get("backupDisposition") not in {"expired", "verified_destroyed"}:
                raise DrillError("final receipt has invalid backup disposition")
        else:
            raise DrillError("unknown deletion receipt type")

    def create_snapshot(self) -> Snapshot:
        if self.state != "available" or self.primary is None:
            raise DrillError("only an available object may produce an eligible reference snapshot")
        return Snapshot(
            artifact_sha256=self.artifact_sha256 or "",
            data=bytes(self.primary),
            state=self.state,
            record_version=self.record_version,
            checkpoint_sequence=self.anchor_sequence,
            checkpoint_digest=self.anchor_digest,
        )

    def restore(
        self,
        snapshot: Snapshot,
        *,
        live_anchor_sequence: int | None,
        live_anchor_digest: str | None,
        retention_valid: bool,
    ) -> bytes:
        if live_anchor_sequence is None or live_anchor_digest is None:
            raise DrillError("restore requires a live independent anchor")
        if self.state != "available" or self.tombstone_intent or self.backup_tombstone:
            raise DrillError("restore cannot resurrect unavailable or revoked data")
        if self._removal_control_blocks_access():
            raise DrillError("restore cannot bypass active removal control")
        if snapshot.state != "available" or snapshot.record_version != self.record_version:
            raise DrillError("restore snapshot is stale")
        if snapshot.artifact_sha256 != self.artifact_sha256:
            raise DrillError("restore snapshot artifact mismatch")
        if (
            snapshot.checkpoint_sequence != live_anchor_sequence
            or snapshot.checkpoint_digest != live_anchor_digest
            or live_anchor_sequence != self.anchor_sequence
            or live_anchor_digest != self.anchor_digest
        ):
            raise DrillError("restore checkpoint conflicts with the live anchor")
        if not retention_valid:
            raise DrillError("restore retention evidence is invalid")
        if hashlib.sha256(snapshot.data).hexdigest() != self.artifact_sha256:
            raise DrillError("restore payload digest mismatch")
        return bytes(snapshot.data)
