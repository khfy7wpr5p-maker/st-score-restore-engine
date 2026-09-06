"""Validation for the Stage 6 S6-08 integration/security regression authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_PATH = Path("evidence/stage6/governance/stage6-s6-08-integration-security-regression-authorization.v1.json")
AUTHORIZATION_ID = "stage6.s6-08.integration-security-regression-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_S6_08_INTEGRATION_SECURITY_REGRESSION"
EXPECTED_ENTRY_MAIN_SHA = "ef0374637fb2a2a8791caad78b72f02ed2db99f7"
EXPECTED_S6_07_AUTHORIZATION_DIGEST = "d32fbe896fa718ec76de00c1de3802345c599ff667a85d00790291ec82183b1b"
EXPECTED_CANONICAL_SHA256 = "32f2fb177411cfa4139a659ec614c7117371ace67147cd059234a926b536ccba"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_09_final_exit_authorization"


class Stage6S608AuthorizationError(ValueError):
    pass


def canonical_sha256(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage6_s6_08_authorization(data: Any) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise Stage6S608AuthorizationError("authorization must be a JSON object")
    record = dict(data)
    required_equal = {
        "schema_version": "1.0.0",
        "project": "ST Score Restore API / ST Score Restore Engine",
        "repository": "khfy7wpr5p-maker/st-score-restore-engine",
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorized_on": "2026-09-06",
        "authorization_source_code": "explicit_user_authorization",
        "decision_authority_reference": "authority:project-governance-owner-20260906-stage6-s6-08",
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }
    for key, expected in required_equal.items():
        if record.get(key) != expected:
            raise Stage6S608AuthorizationError(f"{key} must equal {expected!r}")

    entry = record.get("entry_checkpoint")
    if not isinstance(entry, Mapping):
        raise Stage6S608AuthorizationError("entry_checkpoint must be an object")
    expected_entry = {
        "main_sha": EXPECTED_ENTRY_MAIN_SHA,
        "s6_07_authorization_digest": EXPECTED_S6_07_AUTHORIZATION_DIGEST,
        "s6_07_current_truth_path": "docs/live/ST_SCORE_RESTORE_STAGE6_S6_07_CURRENT_TRUTH.json",
        "repository_validation_run_id": 34050826786,
        "repository_validation_run_number": 476,
        "stage4_governance_run_id": 34050826733,
        "stage4_governance_run_number": 87,
        "stage5_governance_run_id": 34050826751,
        "stage5_governance_run_number": 79,
        "stage6_governance_run_id": 34050826729,
        "stage6_governance_run_number": 38,
        "ci_status": "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows",
    }
    if dict(entry) != expected_entry:
        raise Stage6S608AuthorizationError("entry checkpoint drifted")

    scope = record.get("authorized_scope")
    required_true = {
        "provider_neutral_identity_network_storage_security_integration_regression",
        "production_api_identity_header_bypass_regression",
        "signed_identity_claim_and_role_conflict_regression",
        "tenant_and_environment_boundary_regression",
        "secrets_kms_iam_fail_closed_regression",
        "trusted_proxy_and_private_topology_regression",
        "storage_queue_audit_and_deployment_gate_regression",
        "s6_07_operational_drill_regression_replay",
        "privacy_safe_synthetic_integration_reporting",
        "bounded_deterministic_in_memory_execution",
    }
    if not isinstance(scope, Mapping) or set(scope) != required_true:
        raise Stage6S608AuthorizationError("authorized_scope fields drifted")
    for key in required_true:
        if scope.get(key) is not True:
            raise Stage6S608AuthorizationError(f"authorized_scope.{key} must be true")

    denied = record.get("explicitly_not_authorized")
    required_false = {
        "provider_selection_finalization",
        "provider_specific_resource_activation",
        "live_production_resource_creation",
        "production_distributed_stress_validation",
        "production_load_or_soak_tests",
        "production_penetration_test_or_independent_security_signoff",
        "production_operational_drills",
        "production_deployment",
        "stage7_entry",
        "preview_release",
        "threshold_changes",
        "resource_limit_changes",
        "held_out_retuning",
        "model_training",
        "publication",
    }
    if not isinstance(denied, Mapping) or set(denied) != required_false:
        raise Stage6S608AuthorizationError("explicitly_not_authorized fields drifted")
    for key in required_false:
        if denied.get(key) is not False:
            raise Stage6S608AuthorizationError(f"explicitly_not_authorized.{key} must remain false")

    safety = record.get("safety_assertions")
    if not isinstance(safety, Mapping):
        raise Stage6S608AuthorizationError("safety_assertions must be an object")
    for key in (
        "historical_evidence_immutable",
        "provider_remains_unselected",
        "synthetic_only_no_live_provider_calls",
        "no_real_corpus_or_derivative_bytes_used",
        "integration_regression_failure_must_fail_closed",
        "caller_supplied_identity_must_be_rejected",
        "static_api_key_must_not_be_production_identity",
        "cross_tenant_access_must_be_rejected",
        "cross_environment_secret_or_kms_access_must_be_rejected",
        "audit_dependency_failure_must_block_sensitive_operation",
    ):
        if safety.get(key) is not True:
            raise Stage6S608AuthorizationError(f"safety_assertions.{key} must be true")
    for key in (
        "raw_secrets_or_key_material_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
        "production_state_mutation_authorized",
    ):
        if safety.get(key) is not False:
            raise Stage6S608AuthorizationError(f"safety_assertions.{key} must be false")

    if canonical_sha256(record) != EXPECTED_CANONICAL_SHA256:
        raise Stage6S608AuthorizationError("authorization canonical digest changed")
    return record


def load_and_validate(path: Path = AUTHORIZATION_PATH) -> dict[str, Any]:
    return validate_stage6_s6_08_authorization(json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "EXPECTED_CANONICAL_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage6S608AuthorizationError",
    "canonical_sha256",
    "load_and_validate",
    "validate_stage6_s6_08_authorization",
]
