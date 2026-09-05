"""Validation for the Stage 6 S6-05 production-network implementation authorization."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

AUTHORIZATION_PATH = Path("evidence/stage6/governance/stage6-s6-05-production-network-authorization.v1.json")
AUTHORIZATION_ID = "stage6.s6-05.production-network-implementation-authorization.v1"
AUTHORIZATION_DECISION = "AUTHORIZE_S6_05_PRODUCTION_NETWORK_IMPLEMENTATION"
EXPECTED_ENTRY_MAIN_SHA = "1c9ff79041bacd89a8e4991ffe698929d2637774"
EXPECTED_S6_04_AUTHORIZATION_DIGEST = "a14b4f6dfd8b7a32b3fd9acf9f5a79ecdf6d90cff40e0e842d5e33837d1c0cef"
EXPECTED_CANONICAL_SHA256 = "6815772f8f393b2bf281c75cb4500035808ec7ee5dc083d822dcefca1db9716c"
NEXT_SAFE_BOUNDARY = "separate_explicit_s6_06_storage_deployment_implementation_authorization"


class Stage6S605AuthorizationError(ValueError):
    pass


def canonical_sha256(data: Mapping[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_stage6_s6_05_authorization(data: Any) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise Stage6S605AuthorizationError("authorization must be a JSON object")
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
            raise Stage6S605AuthorizationError(f"{key} must equal {expected!r}")

    entry = record.get("entry_checkpoint")
    if not isinstance(entry, Mapping):
        raise Stage6S605AuthorizationError("entry_checkpoint must be an object")
    if entry.get("main_sha") != EXPECTED_ENTRY_MAIN_SHA:
        raise Stage6S605AuthorizationError("entry checkpoint must bind the approved main SHA")
    if entry.get("s6_04_authorization_digest") != EXPECTED_S6_04_AUTHORIZATION_DIGEST:
        raise Stage6S605AuthorizationError("entry checkpoint must bind the S6-04 authorization digest")
    if entry.get("ci_status") != "success_python_3_11_and_3_12_for_repository_stage4_stage5_and_stage6_workflows":
        raise Stage6S605AuthorizationError("entry checkpoint must bind successful post-merge CI")

    scope = record.get("authorized_scope")
    required_true = {
        "provider_neutral_public_edge_contract",
        "managed_tls_termination_evidence_contract",
        "trusted_proxy_chain_validation",
        "forwarded_header_fail_closed_policy",
        "request_smuggling_normalization_contract",
        "waf_rate_quota_connection_admission_contract",
        "bounded_request_and_slow_client_evidence_contract",
        "private_service_topology_contract",
        "quarantine_no_outbound_enforcement",
        "egress_allowlist_and_ssrf_guard_contract",
        "privacy_safe_network_audit_contract",
        "built_in_stdlib_server_public_exposure_forbidden",
    }
    if not isinstance(scope, Mapping):
        raise Stage6S605AuthorizationError("authorized_scope must be an object")
    for key in required_true:
        if scope.get(key) is not True:
            raise Stage6S605AuthorizationError(f"authorized_scope.{key} must be true")

    denied = record.get("explicitly_not_authorized")
    if not isinstance(denied, Mapping) or not denied:
        raise Stage6S605AuthorizationError("explicitly_not_authorized must be a non-empty object")
    if any(value is not False for value in denied.values()):
        raise Stage6S605AuthorizationError("all explicitly_not_authorized values must remain false")

    safety = record.get("safety_assertions")
    if not isinstance(safety, Mapping):
        raise Stage6S605AuthorizationError("safety_assertions must be an object")
    for key in (
        "historical_evidence_immutable",
        "provider_remains_unselected",
        "built_in_stdlib_server_remains_non_public",
        "untrusted_forwarded_headers_are_never_accepted",
        "network_security_dependency_failure_fails_closed",
    ):
        if safety.get(key) is not True:
            raise Stage6S605AuthorizationError(f"safety_assertions.{key} must be true")
    for key in (
        "real_or_derivative_bytes_in_ordinary_git",
        "raw_private_metrics_in_ordinary_git",
        "raw_secrets_or_key_material_in_ordinary_git",
        "quarantine_outbound_network_allowed",
        "live_resource_creation_authorized",
        "production_deployment_authorized",
    ):
        if safety.get(key) is not False:
            raise Stage6S605AuthorizationError(f"safety_assertions.{key} must be false")

    if canonical_sha256(record) != EXPECTED_CANONICAL_SHA256:
        raise Stage6S605AuthorizationError("authorization canonical digest changed")
    return record


def load_and_validate(path: Path = AUTHORIZATION_PATH) -> dict[str, Any]:
    return validate_stage6_s6_05_authorization(json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "AUTHORIZATION_DECISION",
    "AUTHORIZATION_ID",
    "EXPECTED_CANONICAL_SHA256",
    "NEXT_SAFE_BOUNDARY",
    "Stage6S605AuthorizationError",
    "canonical_sha256",
    "load_and_validate",
    "validate_stage6_s6_05_authorization",
]
