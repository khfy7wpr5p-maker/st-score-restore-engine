"""Stage 1B provider-neutral portability, provider-exit and retention gates.

This module validates metadata-only exit evidence.  It does not select a
provider, create resources, move artifact bytes, export key material, or
perform production migration.  Unknown or incomplete security evidence fails
closed.
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
_SCHEMA_PATH = _ROOT / "schemas" / "stage1b-exit-evidence.schema.json"
_SOURCE_CLASSES = {
    "primary_replica",
    "replica",
    "cache",
    "transient_store",
    "backup",
    "archive",
}
_TOMBSTONE_RANK = {"none": 0, "intent_recorded": 1, "active": 2, "final": 3}
_SECURITY_STATE_FIELDS = (
    "artifactSha256",
    "custodyRecordId",
    "state",
    "recordVersion",
    "purposeDecisionRef",
    "environmentRef",
    "storageClassRef",
    "retentionPolicyRef",
    "holdDecisionRef",
    "revocationStatus",
    "deletionStatus",
    "auditChainHeadDigest",
    "checkpointRef",
    "checkpointSequence",
    "liveAnchorRef",
    "barrierSequence",
    "barrierDigest",
    "tombstoneStatus",
    "antiResurrectionHorizon",
    "pendingBackupReceiptRef",
    "finalDeletionReceiptRef",
)


class Stage1BExitContractError(ValueError):
    """Raised when Stage 1B exit evidence is incomplete, stale, or downgraded."""


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise Stage1BExitContractError(f"{field} must be an authoritative UTC timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise Stage1BExitContractError(f"{field} must be an authoritative UTC timestamp") from error


def _schema() -> dict[str, Any]:
    try:
        value = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(value)
    except (OSError, json.JSONDecodeError, SchemaError) as error:
        raise Stage1BExitContractError(f"invalid Stage 1B exit evidence schema: {error}") from error
    return value


def _validate_schema(evidence: dict[str, Any]) -> None:
    if not isinstance(evidence, dict):
        raise Stage1BExitContractError("Stage 1B exit evidence must be an object")
    try:
        Draft202012Validator(_schema()).validate(evidence)
    except ValidationError as error:
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        raise Stage1BExitContractError(
            f"Stage 1B exit evidence schema validation failed at {location}: {error.message}"
        ) from error


def _validate_defined_object(value: dict[str, Any], definition: str, label: str) -> None:
    if not isinstance(value, dict):
        raise Stage1BExitContractError(f"{label} must be an object")
    try:
        Draft202012Validator(_schema()["$defs"][definition]).validate(value)
    except ValidationError as error:
        location = ".".join(str(part) for part in error.absolute_path) or "root"
        raise Stage1BExitContractError(
            f"{label} schema validation failed at {location}: {error.message}"
        ) from error


def canonical_portability_digest(package: dict[str, Any]) -> str:
    """Hash every portability-package field except the package digest itself."""
    if not isinstance(package, dict):
        raise Stage1BExitContractError("portability package must be an object")
    try:
        encoded = json.dumps(
            {key: value for key, value in package.items() if key != "packageDigest"},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise Stage1BExitContractError("portability package is not canonical JSON encodable") from error
    return hashlib.sha256(encoded).hexdigest()


def canonical_security_state_digest(state: dict[str, Any]) -> str:
    """Bind all security-relevant rollback state to one canonical SHA-256 digest."""
    if not isinstance(state, dict):
        raise Stage1BExitContractError("security state must be an object")
    try:
        content = {field: state[field] for field in _SECURITY_STATE_FIELDS}
        encoded = json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (KeyError, TypeError, ValueError) as error:
        raise Stage1BExitContractError("security state is incomplete or not canonical JSON encodable") from error
    return hashlib.sha256(encoded).hexdigest()


def _require_exact_source_classes(items: list[dict[str, Any]], field: str) -> None:
    classes = [item["sourceClass"] for item in items]
    if len(classes) != len(set(classes)) or set(classes) != _SOURCE_CLASSES:
        raise Stage1BExitContractError(f"{field} must cover every restore-source class exactly once")


def _validate_portability_package(evidence: dict[str, Any]) -> None:
    package = evidence["portabilityPackage"]
    if package["packageDigest"] != canonical_portability_digest(package):
        raise Stage1BExitContractError("portability package digest does not match canonical package content")
    _require_exact_source_classes(package["restoreSourceEvidence"], "portability restore-source evidence")

    # The package is deliberately provider-neutral.  Strict schema properties
    # and opaque refs prevent provider URLs, account IDs, regions, bucket names,
    # credentials, raw keys, or free-text identities from being introduced.
    if package["state"] == "tombstoned" and (
        package["deletionStatus"] != "completed"
        or package["tombstoneStatus"] != "final"
        or package["finalDeletionReceiptRef"] is None
    ):
        raise Stage1BExitContractError("tombstoned portability state requires final deletion evidence")
    if package["state"] in {"revoked", "tombstoned"} and package["pendingBackupReceiptRef"] is None:
        raise Stage1BExitContractError("revoked portability state requires pending-backup receipt evidence")


def _validate_destination(evidence: dict[str, Any]) -> None:
    package = evidence["portabilityPackage"]
    destination = evidence["destinationValidation"]
    if destination["validatedPackageDigest"] != package["packageDigest"]:
        raise Stage1BExitContractError("destination validation is not bound to the canonical portability package")

    exact_bindings = (
        "artifactSha256",
        "custodyRecordId",
        "state",
        "purposeDecisionRef",
        "environmentRef",
        "storageClassRef",
        "retentionPolicyRef",
        "holdDecisionRef",
        "revocationStatus",
        "deletionStatus",
        "auditChainHeadDigest",
        "checkpointRef",
        "liveAnchorRef",
        "barrierDigest",
        "pendingBackupReceiptRef",
        "finalDeletionReceiptRef",
    )
    for field in exact_bindings:
        if destination[field] != package[field]:
            raise Stage1BExitContractError(f"destination validation does not bind current {field}")

    if destination["recordVersion"] < package["recordVersion"]:
        raise Stage1BExitContractError("destination migration lowers the custody record version")
    if destination["checkpointSequence"] < package["checkpointSequence"]:
        raise Stage1BExitContractError("destination migration lowers the anchored checkpoint minimum")
    if destination["barrierSequence"] < package["barrierSequence"]:
        raise Stage1BExitContractError("destination migration lowers the live removal-barrier sequence")
    if _timestamp(destination["antiResurrectionHorizon"], "destination antiResurrectionHorizon") < _timestamp(
        package["antiResurrectionHorizon"], "package antiResurrectionHorizon"
    ):
        raise Stage1BExitContractError("destination migration shortens the anti-resurrection horizon")
    if _TOMBSTONE_RANK[destination["tombstoneStatus"]] < _TOMBSTONE_RANK[package["tombstoneStatus"]]:
        raise Stage1BExitContractError("destination migration lowers tombstone state")


def validate_security_evidence_retention(evidence: dict[str, Any]) -> None:
    """Require deletion receipts and all anti-resurrection evidence through the horizon."""
    _validate_schema(evidence)
    _validate_portability_package(evidence)
    retention = evidence["receiptRetention"]
    package = evidence["portabilityPackage"]
    source_exit = evidence["sourceProviderExit"]

    horizon = _timestamp(retention["antiResurrectionHorizon"], "receipt retention antiResurrectionHorizon")
    if horizon != _timestamp(package["antiResurrectionHorizon"], "package antiResurrectionHorizon"):
        raise Stage1BExitContractError("receipt retention horizon is not bound to the portability package")

    established_minimum = _timestamp(
        retention["establishedMinimumValidThrough"], "establishedMinimumValidThrough"
    )
    policy_minimum = _timestamp(retention["policyMinimumValidThrough"], "policyMinimumValidThrough")
    required_through = max(horizon, established_minimum, policy_minimum)

    pending_ref = package["pendingBackupReceiptRef"]
    final_ref = package["finalDeletionReceiptRef"]
    if pending_ref is None or final_ref is None:
        raise Stage1BExitContractError("exit evidence requires both pending and final deletion receipts")
    if retention["pendingReceiptRef"] != pending_ref or retention["finalReceiptRef"] != final_ref:
        raise Stage1BExitContractError("receipt retention evidence is not bound to the portability receipts")
    if source_exit["pendingBackupReceiptRef"] != pending_ref or source_exit["finalDeletionReceiptRef"] != final_ref:
        raise Stage1BExitContractError("source-provider exit receipts are not bound to portability evidence")

    protected_fields = (
        "pendingReceiptValidThrough",
        "finalReceiptValidThrough",
        "barrierValidThrough",
        "auditValidThrough",
        "checkpointValidThrough",
        "tombstoneValidThrough",
    )
    for field in protected_fields:
        if _timestamp(retention[field], field) < required_through:
            raise Stage1BExitContractError(
                f"{field} expires before the anti-resurrection or stronger policy minimum"
            )


def validate_source_provider_exit(evidence: dict[str, Any]) -> None:
    """Require every old-provider storage boundary to complete normal deletion evidence."""
    _validate_schema(evidence)
    _validate_portability_package(evidence)
    source_exit = evidence["sourceProviderExit"]
    package = evidence["portabilityPackage"]
    _require_exact_source_classes(source_exit["boundaries"], "source-provider exit boundaries")

    if not source_exit["complete"]:
        raise Stage1BExitContractError("source-provider exit remains incomplete")
    if package["pendingBackupReceiptRef"] is None or package["finalDeletionReceiptRef"] is None:
        raise Stage1BExitContractError("source-provider exit requires pending and final deletion receipts")
    if (
        source_exit["pendingBackupReceiptRef"] != package["pendingBackupReceiptRef"]
        or source_exit["finalDeletionReceiptRef"] != package["finalDeletionReceiptRef"]
    ):
        raise Stage1BExitContractError("source-provider exit receipt references do not match the package")
    final_dispositions = {"removed", "not_present", "expired", "verified_destroyed"}
    for boundary in source_exit["boundaries"]:
        if not boundary["verified"] or boundary["disposition"] not in final_dispositions:
            raise Stage1BExitContractError("source-provider exit has an unresolved deletion boundary")


def validate_provider_rollback(
    evidence: dict[str, Any],
    rollback_candidate: dict[str, Any],
    *,
    trusted_live_state: dict[str, Any] | None = None,
) -> None:
    """Allow rollback only when candidate state exactly matches independently trusted live controls."""
    _validate_schema(evidence)
    _validate_portability_package(evidence)
    _validate_destination(evidence)
    if evidence["sourceProviderExit"]["complete"]:
        raise Stage1BExitContractError("a provider with completed source exit cannot become authoritative again")
    if trusted_live_state is None:
        raise Stage1BExitContractError("independently authenticated live security state is required for rollback")

    _validate_defined_object(rollback_candidate, "rollbackCandidate", "rollback candidate")
    _validate_defined_object(trusted_live_state, "trustedLiveState", "trusted live state")

    trusted_digest = canonical_security_state_digest(trusted_live_state)
    candidate_digest = canonical_security_state_digest(rollback_candidate)
    if trusted_live_state["controlDigest"] != trusted_digest:
        raise Stage1BExitContractError("trusted live security-state digest is invalid")
    if rollback_candidate["controlDigest"] != candidate_digest:
        raise Stage1BExitContractError("rollback candidate security-state digest is invalid")
    if candidate_digest != trusted_digest:
        raise Stage1BExitContractError("rollback candidate does not match independently authenticated live security state")

    destination = evidence["destinationValidation"]
    for field in _SECURITY_STATE_FIELDS:
        if trusted_live_state[field] != destination[field]:
            raise Stage1BExitContractError(f"trusted live state differs from accepted destination {field}")

    if trusted_live_state["recordVersion"] < evidence["portabilityPackage"]["recordVersion"]:
        raise Stage1BExitContractError("trusted live state has a stale custody record version")
    if trusted_live_state["checkpointSequence"] < evidence["portabilityPackage"]["checkpointSequence"]:
        raise Stage1BExitContractError("trusted live state has a stale checkpoint minimum")
    if trusted_live_state["barrierSequence"] < evidence["portabilityPackage"]["barrierSequence"]:
        raise Stage1BExitContractError("trusted live state has a stale live removal barrier")


def validate_stage1b_exit_evidence(evidence: dict[str, Any]) -> None:
    """Validate the complete Stage 1B provider-migration and retention exit gate."""
    _validate_schema(evidence)
    _validate_portability_package(evidence)
    _validate_destination(evidence)
    validate_source_provider_exit(evidence)
    validate_security_evidence_retention(evidence)


def validate_exit_schema_contract() -> None:
    schema = _schema()
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise Stage1BExitContractError("Stage 1B exit schema must use JSON Schema Draft 2020-12")
    if schema.get("properties", {}).get("schemaVersion", {}).get("const") != SCHEMA_VERSION:
        raise Stage1BExitContractError("Stage 1B exit schema version drift")
