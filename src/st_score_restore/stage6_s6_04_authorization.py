"""Validation for the Stage 6 S6-04 secrets/KMS/IAM implementation authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_PATH = Path("evidence/stage6/governance/stage6-s6-04-secrets-kms-iam-authorization.v1.json")
AUTHORIZATION_ID = "stage6.s6-04.secrets-kms-iam-implementation-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_S6_04_SECRETS_KMS_IAM_IMPLEMENTATION"
EXPECTED_ENTRY_MAIN_SHA = "afc150c6709cb1a825767b72c44bd04cab4520e7"
EXPECTED_S6_03_AUTHORIZATION_DIGEST = "f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39"
EXPECTED_CANONICAL_SHA256 = "a14b4f6dfd8b7a32b3fd9acf9f5a79ecdf6d90cff40e0e842d5e33837d1c0cef"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_05_network_implementation_authorization"


class Stage6S604AuthorizationError(ValueError):
    pass


def canonical_sha256(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage6_s6_04_authorization(data: Any) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise Stage6S604AuthorizationError("authorization must be a JSON object")
    record = dict(data)
    required_equal = {
        "schema_version": "1.0.0",
        "project": "ST Score Restore API / ST Score Restore Engine",
        "repository": "khfy7wpr5p-maker/st-score-restore-engine",
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorized_on": "2026-09-05",
        "authorization_source_code": "explicit_user_authorization",
        "next_safe_boundary": NEXT_SAFE_BOUNDARY,
    }
    for key, expected in required_equal.items():
        if record.get(key) != expected:
            raise Stage6S604AuthorizationError(f"{key} must equal {expected!r}")

    entry = record.get("entry_checkpoint")
    if not isinstance(entry, Mapping):
        raise Stage6S604AuthorizationError("entry_checkpoint must be an object")
    if entry.get("main_sha") != EXPECTED_ENTRY_MAIN_SHA:
        raise Stage6S604AuthorizationError("entry checkpoint must bind the approved main SHA")
    if entry.get("s6_03_authorization_digest") != EXPECTED_S6_03_AUTHORIZATION_DIGEST:
        raise Stage6S604AuthorizationError("entry checkpoint must bind the S6-03 authorization digest")
    if entry.get("ci_status") != "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows":
        raise Stage6S604AuthorizationError("entry checkpoint must bind successful post-merge CI")

    scope = record.get("authorized_scope")
    required_true = {
        "provider_neutral_secret_reference_contract",
        "managed_secret_resolution_boundary",
        "redacted_secret_material_contract",
        "secret_rotation_and_revocation_fail_closed",
        "provider_neutral_kms_envelope_contract",
        "encryption_context_binding",
        "key_state_and_revocation_fail_closed",
        "workload_identity_iam_contract",
        "least_privilege_deny_by_default",
        "environment_separation_enforcement",
        "separation_of_duties_contract",
        "privacy_safe_security_audit_contract",
    }
    if not isinstance(scope, Mapping):
        raise Stage6S604AuthorizationError("authorized_scope must be an object")
    for key in required_true:
        if scope.get(key) is not True:
            raise Stage6S604AuthorizationError(f"authorized_scope.{key} must be true")

    denied = record.get("explicitly_not_authorized")
    if not isinstance(denied, Mapping) or not denied:
        raise Stage6S604AuthorizationError("explicitly_not_authorized must be a non-empty object")
    if any(value is not False for value in denied.values()):
        raise Stage6S604AuthorizationError("all explicitly_not_authorized values must remain false")

    safety = record.get("safety_assertions")
    if not isinstance(safety, Mapping):
        raise Stage6S604AuthorizationError("safety_assertions must be an object")
    for key in (
        "historical_evidence_immutable",
        "provider_remains_unselected",
        "secret_kms_iam_dependency_failure_fails_closed",
    ):
        if safety.get(key) is not True:
            raise Stage6S604AuthorizationError(f"safety_assertions.{key} must be true")
    for key in (
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_in_git_logs_or_committed_env_files_allowed",
        "cryptographic_key_material_generated_or_committed_by_this_scope",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
    ):
        if safety.get(key) is not False:
            raise Stage6S604AuthorizationError(f"safety_assertions.{key} must be false")

    if canonical_sha256(record) != EXPECTED_CANONICAL_SHA256:
        raise Stage6S604AuthorizationError("authorization canonical digest changed")
    return record


def load_and_validate(path: Path = AUTHORIZATION_PATH) -> dict[str, Any]:
    return validate_stage6_s6_04_authorization(json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "EXPECTED_CANONICAL_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage6S604AuthorizationError",
    "canonical_sha256",
    "load_and_validate",
    "validate_stage6_s6_04_authorization",
]
