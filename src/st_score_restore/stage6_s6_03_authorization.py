"""Validation for the Stage 6 S6-03 identity/authz implementation authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_PATH = Path("evidence/stage6/governance/stage6-s6-03-identity-authz-authorization.v1.json")
AUTHORIZATION_ID = "stage6.s6-03.identity-authz-implementation-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_S6_03_IDENTITY_AUTHZ_IMPLEMENTATION"
EXPECTED_ENTRY_MAIN_SHA = "ed55e10d57655e237e940e14d0af56dd62222ff2"
EXPECTED_S6_02_DECISION_DIGEST = "9485e51f1398c6cff2d9be9264eb8acdf47f8c4ca0fc750062fd9e80298e3865"
EXPECTED_CANONICAL_SHA256 = "f82421eca0ed90defd04609054f47d1972b5327f71a7f35d644ac84c5f57ce39"


class Stage6S603AuthorizationError(ValueError):
    pass


def canonical_sha256(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage6_s6_03_authorization(data: Any) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise Stage6S603AuthorizationError("authorization must be a JSON object")
    record = dict(data)
    required_equal = {
        "schema_version": "1.0.0",
        "project": "ST Score Restore API / ST Score Restore Engine",
        "repository": "khfy7wpr5p-maker/st-score-restore-engine",
        "authorization_id": AUTHORIZATION_ID,
        "decision": AUTHORIZATION_DECISION,
        "authorized_on": "2026-09-04",
        "authorization_source_code": "explicit_user_authorization",
        "next_safe_boundary": "separate_explicit_s6_04_secrets_kms_iam_implementation_authorization",
    }
    for key, expected in required_equal.items():
        if record.get(key) != expected:
            raise Stage6S603AuthorizationError(f"{key} must equal {expected!r}")

    entry = record.get("entry_checkpoint")
    if not isinstance(entry, Mapping):
        raise Stage6S603AuthorizationError("entry_checkpoint must be an object")
    if entry.get("main_sha") != EXPECTED_ENTRY_MAIN_SHA:
        raise Stage6S603AuthorizationError("entry checkpoint must bind the approved main SHA")
    if entry.get("s6_02_decision_digest") != EXPECTED_S6_02_DECISION_DIGEST:
        raise Stage6S603AuthorizationError("entry checkpoint must bind the S6-02 decision digest")
    if entry.get("ci_status") != "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows":
        raise Stage6S603AuthorizationError("entry checkpoint must bind successful post-merge CI")

    scope = record.get("authorized_scope")
    if not isinstance(scope, Mapping) or not scope:
        raise Stage6S603AuthorizationError("authorized_scope must be a non-empty object")
    required_true = {
        "provider_neutral_production_identity_contract_implementation",
        "signed_identity_verification_boundary",
        "issuer_audience_expiry_not_before_key_identity_validation",
        "revocation_fail_closed_contract",
        "tenant_isolation_enforcement",
        "job_ownership_enforcement",
        "role_conflict_enforcement",
        "privacy_safe_principal_derivation",
        "development_static_authentication_compatibility",
        "production_http_integration_contract",
    }
    for key in required_true:
        if scope.get(key) is not True:
            raise Stage6S603AuthorizationError(f"authorized_scope.{key} must be true")

    denied = record.get("explicitly_not_authorized")
    if not isinstance(denied, Mapping) or not denied:
        raise Stage6S603AuthorizationError("explicitly_not_authorized must be a non-empty object")
    if any(value is not False for value in denied.values()):
        raise Stage6S603AuthorizationError("all explicitly_not_authorized values must remain false")

    safety = record.get("safety_assertions")
    if not isinstance(safety, Mapping):
        raise Stage6S603AuthorizationError("safety_assertions must be an object")
    for key in (
        "historical_evidence_immutable",
        "caller_supplied_actor_identity_forbidden_in_production",
        "static_api_keys_forbidden_as_production_user_identity",
        "provider_remains_unselected",
    ):
        if safety.get(key) is not True:
            raise Stage6S603AuthorizationError(f"safety_assertions.{key} must be true")
    for key in (
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
    ):
        if safety.get(key) is not False:
            raise Stage6S603AuthorizationError(f"safety_assertions.{key} must be false")

    if canonical_sha256(record) != EXPECTED_CANONICAL_SHA256:
        raise Stage6S603AuthorizationError("authorization canonical digest changed")
    return record


def load_and_validate(path: Path = AUTHORIZATION_PATH) -> dict[str, Any]:
    return validate_stage6_s6_03_authorization(json.loads(path.read_text(encoding="utf-8")))
