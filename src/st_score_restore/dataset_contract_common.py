"""Shared fail-closed helpers for Stage 1A dataset validation."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from typing import Any

from .dataset_contract_constants import (
    ASSIGNED_SPLITS,
    CODE,
    DATE,
    DatasetManifestError,
    EVIDENCE_ID,
    PERMISSION_STATES,
    PURPOSE_ACTOR_ID,
    RESTRICTION_TYPES,
    SHA,
    STAGE1_ENVIRONMENT,
    UTC,
)


def _obj(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DatasetManifestError(f"{where} must be an object")
    return value


def _arr(value: Any, where: str, *, empty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (not empty and not value):
        qualifier = "an" if empty else "a non-empty"
        raise DatasetManifestError(f"{where} must be {qualifier} array")
    return value


def _fields(value: dict[str, Any], names: set[str], where: str) -> None:
    missing, unknown = names - value.keys(), value.keys() - names
    if missing or unknown:
        raise DatasetManifestError(
            f"{where} field mismatch; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )


def _text(value: Any, where: str, *, null: bool = False) -> str | None:
    if value is None and null:
        return None
    if not isinstance(value, str) or not value.strip():
        raise DatasetManifestError(f"{where} must be a non-empty string")
    return value


def _match(
    value: Any,
    pattern: re.Pattern[str],
    where: str,
    *,
    null: bool = False,
) -> str | None:
    text = _text(value, where, null=null)
    if text is not None and not pattern.fullmatch(text):
        raise DatasetManifestError(f"{where} has invalid opaque identifier or format")
    return text


def _enum(value: Any, choices: set[str], where: str) -> str:
    text = _text(value, where)
    assert text is not None
    if text not in choices:
        raise DatasetManifestError(f"{where} has unsupported value: {text}")
    return text


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise DatasetManifestError(f"{where} must be a boolean")
    return value


def _int(value: Any, where: str, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise DatasetManifestError(f"{where} must be an integer >= {minimum}")
    return value


def _number(value: Any, where: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DatasetManifestError(f"{where} must be a number")
    return value


def _date(value: Any, where: str, *, null: bool = False) -> date | None:
    text = _match(value, DATE, where, null=null)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise DatasetManifestError(f"{where} is not a real calendar date") from error


def _utc_datetime(value: Any, where: str) -> datetime:
    text = _match(value, UTC, where)
    assert text is not None
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as error:
        raise DatasetManifestError(f"{where} is not a valid UTC timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise DatasetManifestError(f"{where} must be UTC")
    return parsed


def _code_array(value: Any, where: str, *, empty: bool = True) -> list[str]:
    raw = _arr(value, where, empty=empty)
    result: list[str] = []
    for index, item in enumerate(raw):
        code = _match(item, CODE, f"{where}[{index}]")
        assert code is not None
        result.append(code)
    if len(set(result)) != len(result):
        raise DatasetManifestError(f"{where} must contain unique codes")
    return result


def _parameter_tree(value: Any, where: str) -> Any:
    """Validate generator parameters without free-text or identity channels."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return _number(value, where)
    if isinstance(value, list):
        return [
            _parameter_tree(item, f"{where}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            code = _match(key, CODE, f"{where}.key")
            assert code is not None
            result[code] = _parameter_tree(item, f"{where}.{code}")
        return result
    raise DatasetManifestError(
        f"{where} cannot contain free-text strings or unsupported values"
    )


def canonical_sha256(value: Any) -> str:
    """Return a deterministic digest for JSON-compatible metadata."""
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _review_evidence(
    raw: Any,
    where: str,
    *,
    states: set[str],
    actor_pattern: re.Pattern[str],
    actor_field: str,
    date_field: str,
    evidence_field: str,
) -> tuple[str, str | None, date | None, str | None]:
    value = _obj(raw, where)
    _fields(value, {"status", actor_field, date_field, evidence_field}, where)
    status = _enum(value["status"], states, f"{where}.status")
    actor = _match(value[actor_field], actor_pattern, f"{where}.{actor_field}", null=True)
    reviewed_on = _date(value[date_field], f"{where}.{date_field}", null=True)
    evidence = _match(
        value[evidence_field], EVIDENCE_ID, f"{where}.{evidence_field}", null=True
    )
    completed = status in {"approved", "rejected", "revoked"}
    if completed != (actor is not None and reviewed_on is not None and evidence is not None):
        raise DatasetManifestError(
            f"{where} actor/date/evidence do not match completed status"
        )
    if not completed and any(item is not None for item in (actor, reviewed_on, evidence)):
        raise DatasetManifestError(
            f"{where} incomplete status cannot claim review evidence"
        )
    return status, actor, reviewed_on, evidence


def _restriction(raw: Any, where: str) -> dict[str, Any]:
    value = _obj(raw, where)
    restriction_type = _enum(
        value.get("type"), RESTRICTION_TYPES, f"{where}.type"
    )
    if restriction_type == "split_allowlist":
        _fields(value, {"type", "values"}, where)
        values = [
            _enum(item, ASSIGNED_SPLITS, f"{where}.values[]")
            for item in _arr(value["values"], f"{where}.values")
        ]
        if len(set(values)) != len(values):
            raise DatasetManifestError(f"{where}.values must be unique")
    elif restriction_type == "storage_class_allowlist":
        _fields(value, {"type", "values"}, where)
        values = [
            _enum(item, {"custody_external"}, f"{where}.values[]")
            for item in _arr(value["values"], f"{where}.values")
        ]
        if len(set(values)) != len(values):
            raise DatasetManifestError(f"{where}.values must be unique")
    elif restriction_type == "environment_allowlist":
        _fields(value, {"type", "values"}, where)
        values = [
            _enum(item, {STAGE1_ENVIRONMENT}, f"{where}.values[]")
            for item in _arr(value["values"], f"{where}.values")
        ]
        if len(set(values)) != len(values):
            raise DatasetManifestError(f"{where}.values must be unique")
    elif restriction_type == "external_export":
        _fields(value, {"type", "allowed"}, where)
        _bool(value["allowed"], f"{where}.allowed")
    else:
        _fields(value, {"type", "date"}, where)
        _date(value["date"], f"{where}.date")
    return value


def _permission(raw: Any, where: str) -> dict[str, Any]:
    value = _obj(raw, where)
    names = {
        "status",
        "authorizationReference",
        "authorizedBy",
        "authorizedOn",
        "expiresOn",
        "restrictions",
        "revokedOn",
        "revocationReference",
    }
    _fields(value, names, where)
    status = _enum(value["status"], PERMISSION_STATES, f"{where}.status")
    authorization_reference = _match(
        value["authorizationReference"],
        EVIDENCE_ID,
        f"{where}.authorizationReference",
        null=True,
    )
    authorized_by = _match(
        value["authorizedBy"], PURPOSE_ACTOR_ID, f"{where}.authorizedBy", null=True
    )
    authorized_on = _date(
        value["authorizedOn"], f"{where}.authorizedOn", null=True
    )
    expires_on = _date(value["expiresOn"], f"{where}.expiresOn", null=True)
    revoked_on = _date(value["revokedOn"], f"{where}.revokedOn", null=True)
    revocation_reference = _match(
        value["revocationReference"],
        EVIDENCE_ID,
        f"{where}.revocationReference",
        null=True,
    )
    restrictions = [
        _restriction(item, f"{where}.restrictions[{index}]")
        for index, item in enumerate(
            _arr(value["restrictions"], f"{where}.restrictions", empty=True)
        )
    ]
    types = [item["type"] for item in restrictions]
    if len(set(types)) != len(types):
        raise DatasetManifestError(f"{where}.restrictions cannot repeat a type")

    authorization = (authorization_reference, authorized_by, authorized_on)
    if status == "granted":
        if None in authorization or revoked_on is not None or revocation_reference is not None:
            raise DatasetManifestError(
                f"{where} granted permission requires authorization evidence only"
            )
    elif status == "expired":
        if (
            None in authorization
            or expires_on is None
            or revoked_on is not None
            or revocation_reference is not None
        ):
            raise DatasetManifestError(
                f"{where} expired permission requires authorization and expiry"
            )
    elif status == "withdrawn":
        if None in authorization or revoked_on is None or revocation_reference is None:
            raise DatasetManifestError(
                f"{where} withdrawn permission requires authorization and revocation evidence"
            )
    elif (
        any(item is not None for item in (*authorization, expires_on, revoked_on, revocation_reference))
        or restrictions
    ):
        raise DatasetManifestError(
            f"{where} {status} permission cannot claim authorization evidence or restrictions"
        )

    if authorized_on is not None and expires_on is not None and expires_on <= authorized_on:
        raise DatasetManifestError(f"{where}.expiresOn must be after authorizedOn")
    if authorized_on is not None and revoked_on is not None and revoked_on < authorized_on:
        raise DatasetManifestError(f"{where}.revokedOn cannot predate authorizedOn")

    return {
        "status": status,
        "authorizationReference": authorization_reference,
        "authorizedBy": authorized_by,
        "authorizedOn": authorized_on,
        "expiresOn": expires_on,
        "restrictions": restrictions,
        "revokedOn": revoked_on,
        "revocationReference": revocation_reference,
    }


def _permission_valid_on(permission: dict[str, Any], when: date) -> bool:
    if permission["status"] != "granted":
        return False
    authorized_on = permission["authorizedOn"]
    expires_on = permission["expiresOn"]
    revoked_on = permission["revokedOn"]
    return (
        authorized_on is not None
        and authorized_on <= when
        and (expires_on is None or when < expires_on)
        and (revoked_on is None or when < revoked_on)
    )


def _restriction_by_type(
    permission: dict[str, Any], restriction_type: str
) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in permission["restrictions"]
            if item["type"] == restriction_type
        ),
        None,
    )
