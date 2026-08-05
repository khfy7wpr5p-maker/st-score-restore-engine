"""Standard-library validator for the versioned fixture catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA_VERSION = "1.0.0"
INPUT_KINDS = {"digital_pdf", "scanned_pdf", "hybrid_pdf", "jpg", "jpeg", "png", "phone_photo"}
NOTATION_KINDS = {"staff", "guitar_tab", "combined_staff_tab"}
DEGRADATIONS = {"none", "skew", "perspective", "page_curl", "shadow", "glare", "uneven_lighting", "blur", "noise", "compression", "low_resolution"}
SOURCE_KINDS = {"synthetic", "public_domain", "licensed", "user_provided"}
RISK_TARGETS = {"staff_lines", "tab_lines", "noteheads", "stems", "flags", "beams", "augmentation_dots", "accidentals", "rests", "barlines", "ties_slurs", "tab_numbers", "guitar_articulations", "text_markings"}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class FixtureCatalogError(ValueError):
    """Fixture metadata violates the approved contract."""


def _object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FixtureCatalogError(f"{where} must be an object")
    return value


def _array(value: Any, where: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise FixtureCatalogError(f"{where} must be a non-empty array")
    return value


def _text(value: Any, where: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise FixtureCatalogError(f"{where} must be a non-empty string")
    return value


def _fields(value: dict[str, Any], required: set[str], where: str) -> None:
    missing = required - value.keys()
    unknown = value.keys() - required
    if missing or unknown:
        raise FixtureCatalogError(f"{where} field mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")


def _enum(value: Any, choices: set[str], where: str) -> str:
    text = _text(value, where)
    assert text is not None
    if text not in choices:
        raise FixtureCatalogError(f"{where} has unsupported value: {text}")
    return text


def _enum_list(value: Any, choices: set[str], where: str) -> set[str]:
    items = _array(value, where)
    result = {_enum(item, choices, f"{where}[]") for item in items}
    if len(result) != len(items):
        raise FixtureCatalogError(f"{where} must contain unique values")
    return result


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise FixtureCatalogError(f"{where} must be a boolean")
    return value


def _validate_fixture(fixture: dict[str, Any], index: int) -> tuple[str, str]:
    where = f"fixtures[{index}]"
    _fields(fixture, {"fixtureId", "title", "input", "degradations", "artifact", "provenance", "privacy", "consent", "permittedUses", "retention", "annotations", "syntheticGeneration", "review"}, where)
    fixture_id = _text(fixture["fixtureId"], f"{where}.fixtureId")
    assert fixture_id is not None
    if not ID_RE.fullmatch(fixture_id):
        raise FixtureCatalogError(f"{where}.fixtureId is invalid")
    _text(fixture["title"], f"{where}.title")

    input_data = _object(fixture["input"], f"{where}.input")
    _fields(input_data, {"kind", "mediaType", "notationKinds", "pageCount"}, f"{where}.input")
    kind = _enum(input_data["kind"], INPUT_KINDS, f"{where}.input.kind")
    expected_media = {"digital_pdf": "application/pdf", "scanned_pdf": "application/pdf", "hybrid_pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "phone_photo": "image/jpeg"}[kind]
    if input_data["mediaType"] != expected_media:
        raise FixtureCatalogError(f"{where}.input.mediaType does not match {kind}")
    _enum_list(input_data["notationKinds"], NOTATION_KINDS, f"{where}.input.notationKinds")
    if not isinstance(input_data["pageCount"], int) or isinstance(input_data["pageCount"], bool) or input_data["pageCount"] < 1:
        raise FixtureCatalogError(f"{where}.input.pageCount must be positive")

    damage = _enum_list(fixture["degradations"], DEGRADATIONS, f"{where}.degradations")
    if "none" in damage and len(damage) > 1:
        raise FixtureCatalogError(f"{where}.degradations cannot combine none with damage")

    artifact = _object(fixture["artifact"], f"{where}.artifact")
    _fields(artifact, {"state", "relativePath", "sha256", "byteSize"}, f"{where}.artifact")
    artifact_state = _enum(artifact["state"], {"planned", "metadata_only", "available", "revoked"}, f"{where}.artifact.state")
    path = _text(artifact["relativePath"], f"{where}.artifact.relativePath", True)
    digest = _text(artifact["sha256"], f"{where}.artifact.sha256", True)
    size = artifact["byteSize"]
    if artifact_state == "available":
        if path is None or digest is None or not isinstance(size, int) or isinstance(size, bool) or size < 1:
            raise FixtureCatalogError(f"{where}.artifact available state requires path, sha256, and byteSize")
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or not SHA_RE.fullmatch(digest):
            raise FixtureCatalogError(f"{where}.artifact path or digest is invalid")
    elif any(item is not None for item in (path, digest, size)):
        raise FixtureCatalogError(f"{where}.artifact metadata must be null unless available")

    provenance = _object(fixture["provenance"], f"{where}.provenance")
    _fields(provenance, {"sourceKind", "sourceReference", "rightsHolder", "licenseId", "usageBasis"}, f"{where}.provenance")
    source_kind = _enum(provenance["sourceKind"], SOURCE_KINDS, f"{where}.provenance.sourceKind")
    for field in ("sourceReference", "rightsHolder", "licenseId", "usageBasis"):
        _text(provenance[field], f"{where}.provenance.{field}")

    privacy = _object(fixture["privacy"], f"{where}.privacy")
    _fields(privacy, {"containsPersonalData", "containsStudentData", "deidentified", "privacyReviewStatus"}, f"{where}.privacy")
    personal = _bool(privacy["containsPersonalData"], f"{where}.privacy.containsPersonalData")
    student = _bool(privacy["containsStudentData"], f"{where}.privacy.containsStudentData")
    deidentified = _bool(privacy["deidentified"], f"{where}.privacy.deidentified")
    privacy_status = _enum(privacy["privacyReviewStatus"], {"not_required", "pending", "approved", "rejected"}, f"{where}.privacy.privacyReviewStatus")
    if student and not personal:
        raise FixtureCatalogError(f"{where}.privacy student data implies personal data")
    if personal and privacy_status == "not_required":
        raise FixtureCatalogError(f"{where}.privacy personal data requires review")

    consent = _object(fixture["consent"], f"{where}.consent")
    _fields(consent, {"teacherApproval", "trainingConsent", "consentReference"}, f"{where}.consent")
    _bool(consent["teacherApproval"], f"{where}.consent.teacherApproval")
    training_consent = _enum(consent["trainingConsent"], {"granted", "denied", "not_requested", "not_applicable", "withdrawn"}, f"{where}.consent.trainingConsent")
    consent_ref = _text(consent["consentReference"], f"{where}.consent.consentReference", True)
    if (training_consent == "granted") != (consent_ref is not None):
        raise FixtureCatalogError(f"{where}.consent granted permission requires exactly one reference")

    uses = _object(fixture["permittedUses"], f"{where}.permittedUses")
    _fields(uses, {"testing", "training", "publication", "demonstration"}, f"{where}.permittedUses")
    testing, training, publication, demonstration = [_bool(uses[name], f"{where}.permittedUses.{name}") for name in ("testing", "training", "publication", "demonstration")]
    if training and training_consent not in {"granted", "not_applicable"}:
        raise FixtureCatalogError(f"{where}.permittedUses.training requires granted or not-applicable consent")
    if source_kind == "user_provided" and training and training_consent != "granted":
        raise FixtureCatalogError(f"{where} user-provided training requires granted permission")
    if personal and not deidentified and any((training, publication, demonstration)):
        raise FixtureCatalogError(f"{where} identifiable personal data cannot be used for training, publication, or demonstration")
    if privacy_status in {"pending", "rejected"} and any((testing, training, publication, demonstration)):
        raise FixtureCatalogError(f"{where} privacy review does not permit use")

    retention = _object(fixture["retention"], f"{where}.retention")
    _fields(retention, {"policy", "expiresOn", "storageLocation"}, f"{where}.retention")
    policy = _enum(retention["policy"], {"metadata_only", "repository_permanent", "external_until_date", "delete_after_validation", "prohibited"}, f"{where}.retention.policy")
    expires = _text(retention["expiresOn"], f"{where}.retention.expiresOn", True)
    _text(retention["storageLocation"], f"{where}.retention.storageLocation")
    if policy == "external_until_date" and (expires is None or not DATE_RE.fullmatch(expires)):
        raise FixtureCatalogError(f"{where}.retention requires YYYY-MM-DD")
    if policy != "external_until_date" and expires is not None:
        raise FixtureCatalogError(f"{where}.retention expiresOn is not allowed")
    if artifact_state in {"planned", "metadata_only"} and policy not in {"metadata_only", "prohibited"}:
        raise FixtureCatalogError(f"{where}.retention does not match metadata-only artifact")

    annotations = _object(fixture["annotations"], f"{where}.annotations")
    _fields(annotations, {"regressionId", "riskTargets", "expectedInvariantNotes"}, f"{where}.annotations")
    regression_id = _text(annotations["regressionId"], f"{where}.annotations.regressionId")
    assert regression_id is not None
    if not ID_RE.fullmatch(regression_id):
        raise FixtureCatalogError(f"{where}.annotations.regressionId is invalid")
    _enum_list(annotations["riskTargets"], RISK_TARGETS, f"{where}.annotations.riskTargets")
    for note in _array(annotations["expectedInvariantNotes"], f"{where}.annotations.expectedInvariantNotes"):
        _text(note, f"{where}.annotations.expectedInvariantNotes[]")

    synthetic = fixture["syntheticGeneration"]
    if source_kind == "synthetic":
        synthetic = _object(synthetic, f"{where}.syntheticGeneration")
        _fields(synthetic, {"derivedFromFixtureId", "generator", "generatorVersion", "seed", "parameters", "cleanSourceApproved"}, f"{where}.syntheticGeneration")
        _text(synthetic["derivedFromFixtureId"], f"{where}.syntheticGeneration.derivedFromFixtureId", True)
        _text(synthetic["generator"], f"{where}.syntheticGeneration.generator")
        _text(synthetic["generatorVersion"], f"{where}.syntheticGeneration.generatorVersion")
        if not isinstance(synthetic["seed"], int) or isinstance(synthetic["seed"], bool) or synthetic["seed"] < 0:
            raise FixtureCatalogError(f"{where}.syntheticGeneration.seed must be non-negative")
        _object(synthetic["parameters"], f"{where}.syntheticGeneration.parameters")
        if synthetic["cleanSourceApproved"] is not True:
            raise FixtureCatalogError(f"{where}.syntheticGeneration clean source must be approved")
    elif synthetic is not None:
        raise FixtureCatalogError(f"{where}.syntheticGeneration is only for synthetic fixtures")

    review = _object(fixture["review"], f"{where}.review")
    _fields(review, {"status", "reviewedBy", "reviewedOn", "notes"}, f"{where}.review")
    review_status = _enum(review["status"], {"planned", "pending", "approved", "rejected", "revoked"}, f"{where}.review.status")
    reviewer = _text(review["reviewedBy"], f"{where}.review.reviewedBy", True)
    reviewed_on = _text(review["reviewedOn"], f"{where}.review.reviewedOn", True)
    if not isinstance(review["notes"], str):
        raise FixtureCatalogError(f"{where}.review.notes must be a string")
    complete = review_status in {"approved", "rejected", "revoked"}
    if complete and (reviewer is None or reviewed_on is None or not DATE_RE.fullmatch(reviewed_on)):
        raise FixtureCatalogError(f"{where}.review completed review requires reviewer and date")
    if not complete and (reviewer is not None or reviewed_on is not None):
        raise FixtureCatalogError(f"{where}.review planned/pending cannot claim reviewer")
    if review_status != "approved" and any((testing, training, publication, demonstration)):
        raise FixtureCatalogError(f"{where} fixture use requires approved review")
    if artifact_state == "available" and review_status != "approved":
        raise FixtureCatalogError(f"{where}.artifact availability requires approved review")
    return fixture_id, regression_id


def validate_catalog(data: Any, *, require_coverage: bool = True) -> dict[str, Any]:
    catalog = _object(data, "catalog")
    _fields(catalog, {"schemaVersion", "catalogId", "description", "fixtures"}, "catalog")
    if catalog["schemaVersion"] != SCHEMA_VERSION:
        raise FixtureCatalogError(f"catalog.schemaVersion must be {SCHEMA_VERSION}")
    catalog_id = _text(catalog["catalogId"], "catalog.catalogId")
    assert catalog_id is not None
    if not ID_RE.fullmatch(catalog_id):
        raise FixtureCatalogError("catalog.catalogId is invalid")
    _text(catalog["description"], "catalog.description")
    fixtures = _array(catalog["fixtures"], "catalog.fixtures")
    ids: set[str] = set()
    regression_ids: set[str] = set()
    input_coverage: set[str] = set()
    notation_coverage: set[str] = set()
    damage_coverage: set[str] = set()
    for index, raw in enumerate(fixtures):
        fixture = _object(raw, f"fixtures[{index}]")
        fixture_id, regression_id = _validate_fixture(fixture, index)
        if fixture_id in ids:
            raise FixtureCatalogError(f"duplicate fixtureId: {fixture_id}")
        if regression_id in regression_ids:
            raise FixtureCatalogError(f"duplicate regressionId: {regression_id}")
        ids.add(fixture_id)
        regression_ids.add(regression_id)
        input_coverage.add(fixture["input"]["kind"])
        notation_coverage.update(fixture["input"]["notationKinds"])
        damage_coverage.update(fixture["degradations"])
    if require_coverage:
        if INPUT_KINDS - input_coverage:
            raise FixtureCatalogError("initial catalog missing input categories: " + ", ".join(sorted(INPUT_KINDS - input_coverage)))
        if NOTATION_KINDS - notation_coverage:
            raise FixtureCatalogError("initial catalog missing notation categories: " + ", ".join(sorted(NOTATION_KINDS - notation_coverage)))
        if (DEGRADATIONS - {"none"}) - damage_coverage:
            raise FixtureCatalogError("initial catalog missing degradation categories: " + ", ".join(sorted((DEGRADATIONS - {"none"}) - damage_coverage)))
    synthetic_ids = {f["fixtureId"] for f in fixtures if f["provenance"]["sourceKind"] == "synthetic"}
    for index, fixture in enumerate(fixtures):
        synthetic = fixture["syntheticGeneration"]
        if synthetic is None:
            continue
        parent = synthetic["derivedFromFixtureId"]
        if parent is not None and parent not in ids:
            raise FixtureCatalogError(f"fixtures[{index}] synthetic parent does not exist")
        if parent == fixture["fixtureId"] or parent in synthetic_ids:
            raise FixtureCatalogError(f"fixtures[{index}] synthetic parent must be a distinct clean origin")
    return catalog


def load_catalog(path: str | Path, *, require_coverage: bool = True) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return validate_catalog(json.load(handle), require_coverage=require_coverage)
