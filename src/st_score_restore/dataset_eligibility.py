"""Deterministic Stage 1C evidence-derived minimum eligibility resolution."""

from __future__ import annotations

from typing import Any

from .dataset_contract_constants import DatasetManifestError

_SOURCE_USAGE_BASIS = {
    "project_authored": "project_authored",
    "public_domain": "public_domain",
    "licensed": "license_grant",
    "user_provided": "user_authorization",
    "synthetic": "synthetic_derivation",
}

_ELIGIBILITY_RANK = {
    "open_corpus": 1,
    "restricted_corpus": 2,
    "sensitive_custody": 3,
}


def _stronger(first: str, second: str) -> str:
    return first if _ELIGIBILITY_RANK[first] >= _ELIGIBILITY_RANK[second] else second


def _restriction_floor(permissions: dict[str, dict[str, Any]]) -> str:
    """Return the minimum class implied by active machine restrictions."""
    floor = "open_corpus"
    for permission in permissions.values():
        if permission["status"] != "granted":
            continue
        for restriction in permission["restrictions"]:
            restriction_type = restriction["type"]
            if restriction_type == "storage_class_allowlist":
                values = set(restriction["values"])
                if "managed_standard" in values:
                    continue
                if values == {"high_assurance_vault"}:
                    floor = "sensitive_custody"
                else:
                    floor = _stronger(floor, "restricted_corpus")
            elif restriction_type == "environment_allowlist":
                floor = _stronger(floor, "restricted_corpus")
            elif restriction_type == "external_export":
                if restriction["allowed"] is False:
                    floor = _stronger(floor, "restricted_corpus")
            elif restriction_type == "retention_not_after":
                floor = _stronger(floor, "restricted_corpus")
    return floor


def resolve_required_eligibility_class(
    *,
    artifact_state: str,
    source_kind: str,
    usage_basis: str,
    rights_status: str,
    privacy_class: str,
    privacy_status: str,
    review_status: str,
    permissions: dict[str, dict[str, Any]],
) -> str:
    """Derive the minimum admissible custody class from validated evidence.

    This function resolves storage *risk*, not permission to onboard. Purpose,
    temporal, retention, split, provider and operational gates remain separate.
    A caller may explicitly escalate to a stronger class, but never downgrade
    below the class returned here.
    """
    expected_basis = _SOURCE_USAGE_BASIS.get(source_kind)
    if expected_basis is None or usage_basis != expected_basis:
        raise DatasetManifestError(
            "provenance sourceKind and usageBasisCode are inconsistent"
        )

    if artifact_state == "metadata_only":
        return "blocked"
    if rights_status != "approved":
        return "blocked"
    if privacy_status in {"pending", "rejected"}:
        return "blocked"
    if review_status not in {"approved", "revoked"}:
        return "blocked"

    if privacy_class in {"personal", "student"} or source_kind == "user_provided":
        floor = "sensitive_custody"
    elif privacy_class == "deidentified" or source_kind == "licensed":
        floor = "restricted_corpus"
    else:
        floor = "open_corpus"

    return _stronger(floor, _restriction_floor(permissions))


def validate_declared_eligibility(
    *,
    declared: str,
    artifact_state: str,
    source_kind: str,
    usage_basis: str,
    rights_status: str,
    privacy_class: str,
    privacy_status: str,
    review_status: str,
    permissions: dict[str, dict[str, Any]],
) -> str:
    """Reject a declared class that is weaker than deterministic evidence."""
    required = resolve_required_eligibility_class(
        artifact_state=artifact_state,
        source_kind=source_kind,
        usage_basis=usage_basis,
        rights_status=rights_status,
        privacy_class=privacy_class,
        privacy_status=privacy_status,
        review_status=review_status,
        permissions=permissions,
    )
    if required == "blocked":
        if artifact_state != "metadata_only":
            raise DatasetManifestError(
                "unresolved eligibility evidence cannot support an external artifact"
            )
        if declared != "blocked":
            raise DatasetManifestError(
                "metadata-only eligibility must remain blocked"
            )
        return required

    if declared == "blocked" or _ELIGIBILITY_RANK[declared] < _ELIGIBILITY_RANK[required]:
        raise DatasetManifestError(
            f"declared eligibility {declared} is weaker than evidence-derived {required}"
        )
    return required
