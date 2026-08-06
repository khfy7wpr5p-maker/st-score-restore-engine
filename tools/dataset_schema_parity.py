"""Fail-closed JSON Schema/Python parity checks for Stage 1A."""
from __future__ import annotations

from typing import Any, Iterable

from st_score_restore.dataset_contract_constants import (
    ARTIFACT_STATES, ASSIGNED_SPLITS, CATALOG_FIELDS, CATALOG_SCHEMA_VERSION,
    CODE, CUSTODIAN_ACTOR_ID, CUSTODY_ID, DATASET_ACTOR_ID,
    DATASET_REVIEW_STATES, DATE, DEGRADATIONS, DEIDENTIFICATION_METHODS,
    DELETION_STATES, ENTRY_DECISION_ID, EVIDENCE_ID, ID, INPUT_MEDIA,
    ITEM_FIELDS, NOTATION_KINDS, PERMISSION_STATES, POLICY_ID,
    PRIVACY_ACTOR_ID, PRIVACY_CLASSES, PRIVACY_REVIEW_STATES, PURPOSES,
    PURPOSE_ACTOR_ID, RECEIPT_ID, RESTRICTION_TYPES, RETENTION_POLICIES,
    REVOCATION_STATES, RIGHTS_ACTOR_ID, RIGHTS_REVIEW_STATES, SEMVER, SHA,
    SNAPSHOT_FIELDS, SNAPSHOT_SCHEMA_VERSION, SOURCE_KINDS, SPLITS,
    STAGE1_ENVIRONMENT, STORAGE_CLASSES, SUBJECT_ID, USAGE_BASIS_CODES, UTC,
)
from st_score_restore.dataset_manifest import DatasetManifestError
from tools.dataset_schema_helpers import assert_schema_valid

Path = tuple[str | int, ...]


def _at(value: Any, path: Path, label: str) -> Any:
    try:
        for part in path:
            value = value[part]
        return value
    except (KeyError, IndexError, TypeError) as error:
        raise DatasetManifestError(f"{label} schema path missing") from error


def _field(schema: dict[str, Any], path: Path, key: str, expected: Any, label: str) -> None:
    actual = _at(schema, path, label)
    if not isinstance(actual, dict) or actual.get(key) != expected:
        suffix = (
            "constant drift"
            if key == "const"
            else "reference drift"
            if key == "$ref"
            else f"{key} drift"
        )
        raise DatasetManifestError(f"{label} {suffix}")


def _set_field(schema: dict[str, Any], path: Path, key: str, expected: Iterable[Any], label: str) -> None:
    actual = _at(schema, path, label)
    raw = actual.get(key) if isinstance(actual, dict) else None
    if not isinstance(raw, list) or set(raw) != set(expected):
        suffix = "required-field drift" if key == "required" else f"{key} drift"
        raise DatasetManifestError(f"{label} {suffix}")


def _assert_closed(value: Any, label: str = "schema") -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_closed(item, f"{label}[{index}]")
        return
    if not isinstance(value, dict):
        return
    if value.get("type") == "object":
        dynamic = value.get("additionalProperties") == {
            "$ref": "#/$defs/parameterValue"
        }
        if not dynamic and value.get("additionalProperties") is not False:
            raise DatasetManifestError(f"{label} object must set additionalProperties=false")
    for key, item in value.items():
        _assert_closed(item, f"{label}.{key}")


def validate_schema_parity(catalog: dict[str, Any], snapshot: dict[str, Any]) -> None:
    draft = "https://json-schema.org/draft/2020-12/schema"
    for schema, label in ((catalog, "catalog"), (snapshot, "snapshot")):
        if schema.get("$schema") != draft:
            raise DatasetManifestError(f"{label} schema must use Draft 2020-12")
        assert_schema_valid(schema, f"dataset {label} schema")
        _assert_closed(schema, f"{label} schema")

    cp = ("properties",)
    ci = ("$defs", "item", "properties")
    cd = ("$defs",)
    sp = ("properties",)

    required_checks = [
        (catalog, (), CATALOG_FIELDS, "catalog"),
        (snapshot, (), SNAPSHOT_FIELDS, "snapshot"),
        (catalog, ("$defs", "item"), ITEM_FIELDS, "item"),
        (catalog, ci + ("artifact",), {"state","sha256","byteSize","storageLocator","custodyProfileId","encryptionProfileId","custodianId"}, "artifact"),
        (catalog, ci + ("provenance",), {"sourceKind","sourceReference","rightsHolderId","licenseId","usageBasisCode","rightsReview"}, "provenance"),
        (catalog, ci + ("provenance","properties","rightsReview"), {"status","verifiedBy","verifiedOn","evidenceReference"}, "rightsReview"),
        (catalog, ci + ("privacy",), {"classification","reviewStatus","reviewedBy","reviewedOn","evidenceReference","deidentificationMethodCode","deidentifiedArtifactSha256"}, "privacy"),
        (catalog, ci + ("input",), {"kind","mediaType","notationKinds","pageCount","degradations"}, "input"),
        (catalog, ci + ("permissions",), set(PURPOSES), "purpose"),
        (catalog, cd + ("permission",), {"status","authorizationReference","authorizedBy","authorizedOn","expiresOn","restrictions","revokedOn","revocationReference"}, "permission"),
        (catalog, ci + ("retention",), {"policy","expiresOn","storageClass","deletionRequired","deletionStatus","deletionReceiptReference","deletionReceiptSha256"}, "retention"),
        (catalog, ci + ("revocation",), {"status","effectiveOn","reference"}, "revocation"),
        (catalog, ci + ("review",), {"status","reviewedBy","reviewedOn","evidenceReference","noteCodes"}, "review"),
        (catalog, ci + ("assertions",), {"teacherApprovalImpliedDatasetPermission","teacherApprovalImpliedTrainingPermission","originalBytesInGit","stage1TrainingExecutionAuthorized"}, "assertions"),
        (snapshot, sp + ("assignments","items"), {"datasetItemId","sourceFamilyId","split","itemSha256"}, "snapshot assignment"),
        (snapshot, sp + ("coverage",), {"realItemCount","syntheticItemCount","gapCodes"}, "coverage"),
        (snapshot, sp + ("review",), {"status","reviewedBy","reviewedOn","evidenceReference","noteCodes"}, "snapshot review"),
    ]
    for schema, path, expected, label in required_checks:
        _set_field(schema, path, "required", expected, label)

    constants = [
        (catalog, cp+("schemaVersion",), CATALOG_SCHEMA_VERSION, "catalog.schemaVersion"),
        (snapshot, sp+("schemaVersion",), SNAPSHOT_SCHEMA_VERSION, "snapshot.schemaVersion"),
        (catalog, cp+("entryDecisionId",), ENTRY_DECISION_ID, "catalog.entryDecisionId"),
        (snapshot, sp+("entryDecisionId",), ENTRY_DECISION_ID, "snapshot.entryDecisionId"),
        (snapshot, sp+("environment",), STAGE1_ENVIRONMENT, "snapshot.environment"),
        (snapshot, sp+("trainingUseActivated",), False, "snapshot.trainingUseActivated"),
        (snapshot, sp+("review","properties","status"), "approved", "snapshot.review.status"),
    ]
    for name in ("teacherApprovalImpliedDatasetPermission","teacherApprovalImpliedTrainingPermission","originalBytesInGit","stage1TrainingExecutionAuthorized"):
        constants.append((catalog, ci+("assertions","properties",name), False, f"assertions.{name}"))
    for schema, path, expected, label in constants:
        _field(schema, path, "const", expected, label)

    refs = [
        (catalog, cp+("catalogId",), "#/$defs/id", "catalogId"),
        (snapshot, sp+("snapshotId",), "#/$defs/id", "snapshotId"),
        (snapshot, sp+("datasetId",), "#/$defs/id", "datasetId"),
        (catalog, ci+("datasetItemId",), "#/$defs/id", "datasetItemId"),
        (catalog, ci+("sourceFamilyId",), "#/$defs/id", "sourceFamilyId"),
        (catalog, ci+("parentItemId",), "#/$defs/nullableId", "parentItemId"),
        (catalog, ci+("artifact","properties","sha256"), "#/$defs/nullableSha", "artifact.sha256"),
        (catalog, ci+("provenance","properties","rightsReview","properties","verifiedOn"), "#/$defs/nullableDate", "rightsReview.verifiedOn"),
        (catalog, ci+("provenance","properties","rightsReview","properties","evidenceReference"), "#/$defs/nullableEvidence", "rightsReview.evidenceReference"),
        (catalog, ci+("privacy","properties","reviewedOn"), "#/$defs/nullableDate", "privacy.reviewedOn"),
        (catalog, ci+("privacy","properties","evidenceReference"), "#/$defs/nullableEvidence", "privacy.evidenceReference"),
        (catalog, ci+("privacy","properties","deidentifiedArtifactSha256"), "#/$defs/nullableSha", "privacy.deidentifiedArtifactSha256"),
        (catalog, ci+("retention","properties","expiresOn"), "#/$defs/nullableDate", "retention.expiresOn"),
        (catalog, ci+("retention","properties","deletionReceiptSha256"), "#/$defs/nullableSha", "deletionReceiptSha256"),
        (catalog, ci+("review","properties","reviewedOn"), "#/$defs/nullableDate", "review.reviewedOn"),
        (catalog, ci+("review","properties","evidenceReference"), "#/$defs/nullableEvidence", "review.evidenceReference"),
        (snapshot, sp+("assignments","items","properties","datasetItemId"), "#/$defs/id", "assignment.datasetItemId"),
        (snapshot, sp+("assignments","items","properties","sourceFamilyId"), "#/$defs/id", "assignment.sourceFamilyId"),
        (snapshot, sp+("revokedItemIds","items"), "#/$defs/id", "revokedItemIds"),
    ]
    for field in ("authorizedOn","expiresOn","revokedOn"):
        refs.append((catalog, cd+("permission","properties",field), "#/$defs/nullableDate", f"permission.{field}"))
    for field, target in (("effectiveOn","#/$defs/nullableDate"),("reference","#/$defs/nullableEvidence")):
        refs.append((catalog, ci+("revocation","properties",field), target, f"revocation.{field}"))
    for schema, path, expected, label in refs:
        _field(schema, path, "$ref", expected, label)

    patterns = [
        (catalog, cp+("descriptionCode",), CODE.pattern, "descriptionCode"),
        (snapshot, sp+("createdAt",), UTC.pattern, "createdAt"),
        (snapshot, sp+("version",), SEMVER.pattern, "snapshot.version"),
        (snapshot, sp+("catalogSha256",), SHA.pattern, "catalogSha256"),
        (snapshot, ("$defs","id"), ID.pattern, "snapshot.$defs.id"),
        (catalog, cd+("id",), ID.pattern, "$defs.id"),
        (catalog, cd+("nullableId",), ID.pattern, "nullableId"),
        (catalog, cd+("nullableDate",), DATE.pattern, "nullableDate"),
        (catalog, cd+("nullableSha",), SHA.pattern, "nullableSha"),
        (catalog, cd+("nullableEvidence",), EVIDENCE_ID.pattern, "nullableEvidence"),
        (catalog, ci+("artifact","properties","storageLocator"), CUSTODY_ID.pattern, "storageLocator"),
        (catalog, ci+("artifact","properties","custodyProfileId"), POLICY_ID.pattern, "custodyProfileId"),
        (catalog, ci+("artifact","properties","encryptionProfileId"), POLICY_ID.pattern, "encryptionProfileId"),
        (catalog, ci+("artifact","properties","custodianId"), CUSTODIAN_ACTOR_ID.pattern, "custodianId"),
        (catalog, ci+("provenance","properties","sourceReference"), EVIDENCE_ID.pattern, "sourceReference"),
        (catalog, ci+("provenance","properties","rightsHolderId"), SUBJECT_ID.pattern, "rightsHolderId"),
        (catalog, ci+("provenance","properties","licenseId"), CODE.pattern, "licenseId"),
        (catalog, ci+("provenance","properties","rightsReview","properties","verifiedBy"), RIGHTS_ACTOR_ID.pattern, "verifiedBy"),
        (catalog, ci+("privacy","properties","reviewedBy"), PRIVACY_ACTOR_ID.pattern, "privacy.reviewedBy"),
        (catalog, cd+("permission","properties","authorizationReference"), EVIDENCE_ID.pattern, "authorizationReference"),
        (catalog, cd+("permission","properties","authorizedBy"), PURPOSE_ACTOR_ID.pattern, "authorizedBy"),
        (catalog, cd+("permission","properties","revocationReference"), EVIDENCE_ID.pattern, "revocationReference"),
        (catalog, ci+("retention","properties","deletionReceiptReference"), RECEIPT_ID.pattern, "deletionReceiptReference"),
        (catalog, ci+("review","properties","reviewedBy"), DATASET_ACTOR_ID.pattern, "review.reviewedBy"),
        (catalog, ci+("review","properties","noteCodes","items"), CODE.pattern, "review.noteCodes"),
        (snapshot, sp+("assignments","items","properties","itemSha256"), SHA.pattern, "assignment.itemSha256"),
        (snapshot, sp+("coverage","properties","gapCodes","items"), CODE.pattern, "coverage.gapCodes"),
        (snapshot, sp+("review","properties","reviewedBy"), DATASET_ACTOR_ID.pattern, "snapshot.reviewedBy"),
        (snapshot, sp+("review","properties","reviewedOn"), DATE.pattern, "snapshot.reviewedOn"),
        (snapshot, sp+("review","properties","evidenceReference"), EVIDENCE_ID.pattern, "snapshot.evidenceReference"),
        (snapshot, sp+("review","properties","noteCodes","items"), CODE.pattern, "snapshot.noteCodes"),
    ]
    synthetic = next(v for v in _at(catalog, ci+("syntheticGeneration","oneOf"), "synthetic") if v.get("type") == "object")
    sy = ("properties",)
    _set_field(synthetic, (), "required", {"generator","generatorVersion","generatorCommit","generatedOn","derivationAuthorizationReference","seed","parameters"}, "syntheticGeneration")
    for field, expected in (("generator",CODE.pattern),("generatorVersion",SEMVER.pattern),("generatorCommit",SHA.pattern),("generatedOn",DATE.pattern),("derivationAuthorizationReference",EVIDENCE_ID.pattern)):
        patterns.append((synthetic, sy+(field,), expected, f"synthetic.{field}"))
    parameter_object = next(v for v in _at(catalog, cd+("parameterValue","oneOf"), "parameterValue") if v.get("type") == "object")
    patterns.extend([
        (synthetic, sy+("parameters","propertyNames"), CODE.pattern, "synthetic.parameters"),
        (parameter_object, ("propertyNames",), CODE.pattern, "parameterValue.propertyNames"),
    ])
    for schema, path, expected, label in patterns:
        _field(schema, path, "pattern", expected, label)

    enum_checks = [
        (catalog, ci+("artifact","properties","state"), ARTIFACT_STATES, "artifact states"),
        (catalog, ci+("provenance","properties","sourceKind"), SOURCE_KINDS, "source kinds"),
        (catalog, ci+("provenance","properties","usageBasisCode"), USAGE_BASIS_CODES, "usage basis"),
        (catalog, ci+("provenance","properties","rightsReview","properties","status"), RIGHTS_REVIEW_STATES, "rights states"),
        (catalog, ci+("privacy","properties","classification"), PRIVACY_CLASSES, "privacy classes"),
        (catalog, ci+("privacy","properties","reviewStatus"), PRIVACY_REVIEW_STATES, "privacy states"),
        (catalog, ci+("privacy","properties","deidentificationMethodCode"), DEIDENTIFICATION_METHODS|{None}, "deidentification methods"),
        (catalog, ci+("input","properties","kind"), set(INPUT_MEDIA), "input kinds"),
        (catalog, ci+("input","properties","mediaType"), set(INPUT_MEDIA.values()), "media types"),
        (catalog, ci+("input","properties","notationKinds","items"), NOTATION_KINDS, "notation kinds"),
        (catalog, ci+("input","properties","degradations","items"), DEGRADATIONS, "degradations"),
        (catalog, cd+("permission","properties","status"), PERMISSION_STATES, "permission states"),
        (catalog, ci+("split",), SPLITS, "item splits"),
        (catalog, ci+("retention","properties","policy"), RETENTION_POLICIES, "retention policies"),
        (catalog, ci+("retention","properties","storageClass"), STORAGE_CLASSES, "storage classes"),
        (catalog, ci+("retention","properties","deletionStatus"), DELETION_STATES, "deletion states"),
        (catalog, ci+("revocation","properties","status"), REVOCATION_STATES, "revocation states"),
        (catalog, ci+("review","properties","status"), DATASET_REVIEW_STATES, "review states"),
        (snapshot, sp+("assignments","items","properties","split"), ASSIGNED_SPLITS, "snapshot assignment splits"),
    ]
    for schema, path, expected, label in enum_checks:
        _set_field(schema, path, "enum", expected, label)
    if set(_at(catalog, ci+("permissions","properties"), "permission properties")) != set(PURPOSES):
        raise DatasetManifestError("permission property drift")

    restrictions = {v["properties"]["type"]["const"]: v for v in _at(catalog, cd+("restriction","oneOf"), "restrictions")}
    if set(restrictions) != RESTRICTION_TYPES:
        raise DatasetManifestError("restriction type drift")
    _set_field(restrictions["split_allowlist"], ("properties","values","items"), "enum", ASSIGNED_SPLITS, "split restriction values")
    _field(restrictions["storage_class_allowlist"], ("properties","values","items"), "const", "custody_external", "storage restriction")
    _field(restrictions["environment_allowlist"], ("properties","values","items"), "const", STAGE1_ENVIRONMENT, "environment restriction")
    _field(restrictions["external_export"], ("properties","allowed"), "type", "boolean", "external export restriction")
    _field(restrictions["retention_not_after"], ("properties","date"), "pattern", DATE.pattern, "retention restriction")
    for name, variant in restrictions.items():
        expected = {"type","allowed"} if name == "external_export" else {"type","date"} if name == "retention_not_after" else {"type","values"}
        _set_field(variant, (), "required", expected, f"restriction.{name}")

    _field(synthetic, sy+("seed",), "minimum", 0, "synthetic.seed")
    _field(catalog, ci+("artifact","properties","byteSize"), "minimum", 1, "byteSize")
    _field(catalog, ci+("input","properties","pageCount"), "minimum", 1, "pageCount")
    _field(snapshot, sp+("coverage","properties","realItemCount"), "minimum", 0, "realItemCount")
    _field(snapshot, sp+("coverage","properties","syntheticItemCount"), "minimum", 0, "syntheticItemCount")
    if synthetic["properties"]["parameters"].get("additionalProperties") != {"$ref":"#/$defs/parameterValue"} or parameter_object.get("additionalProperties") != {"$ref":"#/$defs/parameterValue"}:
        raise DatasetManifestError("parameter recursive reference drift")
    parameter_types = {v.get("type") for v in _at(catalog, cd+("parameterValue","oneOf"), "parameterValue")}
    if parameter_types != {"null","boolean","number","array","object"}:
        raise DatasetManifestError("parameter type drift or free-text enabled")
