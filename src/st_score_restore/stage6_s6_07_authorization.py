"""Validation for the Stage 6 S6-07 synthetic operational drills authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_PATH = Path("evidence/stage6/governance/stage6-s6-07-synthetic-operational-drills-authorization.v1.json")
AUTHORIZATION_ID = "stage6.s6-07.synthetic-operational-drills-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_S6_07_SYNTHETIC_OPERATIONAL_DRILLS"
EXPECTED_ENTRY_MAIN_SHA = "e4968028d0bea5518873fa612db8912256c2da75"
EXPECTED_S6_06_AUTHORIZATION_DIGEST = "dd31e0460352128ba2ed63e0207e506a305e83fb6b462156cdaa2c9651021a10"
EXPECTED_CANONICAL_SHA256 = "d32fbe896fa718ec76de00c1de3802345c599ff667a85d00790291ec82183b1b"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_08_integration_security_regression_authorization"


class Stage6S607AuthorizationError(ValueError):
    pass


def canonical_sha256(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage6_s6_07_authorization(data: Any) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise Stage6S607AuthorizationError("authorization must be a JSON object")
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
            raise Stage6S607AuthorizationError(f"{key} must equal {expected!r}")

    entry = record.get("entry_checkpoint")
    if not isinstance(entry, Mapping):
        raise Stage6S607AuthorizationError("entry_checkpoint must be an object")
    if entry.get("main_sha") != EXPECTED_ENTRY_MAIN_SHA:
        raise Stage6S607AuthorizationError("entry checkpoint must bind the approved main SHA")
    if entry.get("s6_06_authorization_digest") != EXPECTED_S6_06_AUTHORIZATION_DIGEST:
        raise Stage6S607AuthorizationError("entry checkpoint must bind the S6-06 authorization digest")
    if entry.get("s6_06_current_truth_path") != "docs/live/ST_SCORE_RESTORE_STAGE6_S6_06_CURRENT_TRUTH.json":
        raise Stage6S607AuthorizationError("entry checkpoint must bind S6-06 current truth")
    if entry.get("ci_status") != "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows":
        raise Stage6S607AuthorizationError("entry checkpoint must bind successful post-merge CI")

    scope = record.get("authorized_scope")
    required_true = {
        "synthetic_crash_recovery_drills",
        "synthetic_queue_redelivery_and_duplicate_claim_drills",
        "synthetic_stale_worker_fencing_drills",
        "synthetic_idempotent_replay_drills",
        "synthetic_deletion_restore_anti_resurrection_drills",
        "synthetic_backup_restore_publish_gate_drills",
        "synthetic_audit_dependency_fail_closed_drills",
        "synthetic_deployment_candidate_and_rollback_gate_drills",
        "bounded_synthetic_concurrency_and_idempotency_stress",
        "privacy_safe_synthetic_drill_reporting",
    }
    if not isinstance(scope, Mapping):
        raise Stage6S607AuthorizationError("authorized_scope must be an object")
    for key in required_true:
        if scope.get(key) is not True:
            raise Stage6S607AuthorizationError(f"authorized_scope.{key} must be true")

    denied = record.get("explicitly_not_authorized")
    if not isinstance(denied, Mapping) or not denied:
        raise Stage6S607AuthorizationError("explicitly_not_authorized must be a non-empty object")
    if any(value is not False for value in denied.values()):
        raise Stage6S607AuthorizationError("all explicitly_not_authorized values must remain false")

    safety = record.get("safety_assertions")
    if not isinstance(safety, Mapping):
        raise Stage6S607AuthorizationError("safety_assertions must be an object")
    for key in (
        "historical_evidence_immutable",
        "provider_remains_unselected",
        "synthetic_only_no_live_provider_calls",
        "no_real_corpus_or_derivative_bytes_used",
        "drill_failure_must_fail_closed",
        "deleted_data_resurrection_must_be_detected",
        "stale_worker_write_must_be_rejected",
        "audit_dependency_failure_must_block_sensitive_operation",
    ):
        if safety.get(key) is not True:
            raise Stage6S607AuthorizationError(f"safety_assertions.{key} must be true")
    for key in (
        "raw_secrets_or_key_material_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "production_state_mutation_authorized",
    ):
        if safety.get(key) is not False:
            raise Stage6S607AuthorizationError(f"safety_assertions.{key} must be false")

    if canonical_sha256(record) != EXPECTED_CANONICAL_SHA256:
        raise Stage6S607AuthorizationError("authorization canonical digest changed")
    return record


def load_and_validate(path: Path = AUTHORIZATION_PATH) -> dict[str, Any]:
    return validate_stage6_s6_07_authorization(json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "EXPECTED_CANONICAL_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage6S607AuthorizationError",
    "canonical_sha256",
    "load_and_validate",
    "validate_stage6_s6_07_authorization",
]
