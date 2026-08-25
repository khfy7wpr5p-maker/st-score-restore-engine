"""Identity, artifact, rights, privacy, and input validation for dataset items."""

from __future__ import annotations

from typing import Any

from .dataset_contract_common import (
    _arr,
    _date,
    _enum,
    _fields,
    _int,
    _match,
    _obj,
    _review_evidence,
)
from .dataset_contract_constants import (
    ARTIFACT_STATES,
    CODE,
    CUSTODIAN_ACTOR_ID,
    CUSTODY_ID,
    DEGRADATIONS,
    DEIDENTIFICATION_METHODS,
    DatasetManifestError,
    ELIGIBILITY_CLASSES,
    EVIDENCE_ID,
    ID,
    INPUT_MEDIA,
    ITEM_FIELDS,
    NOTATION_KINDS,
    POLICY_ID,
    PRIVACY_ACTOR_ID,
    PRIVACY_CLASSES,
    PRIVACY_REVIEW_STATES,
    RIGHTS_ACTOR_ID,
    RIGHTS_REVIEW_STATES,
    SHA,
    SOURCE_KINDS,
    SPLITS,
    SUBJECT_ID,
    USAGE_BASIS_CODES,
)


def validate_item_core(raw: Any, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    where = f"items[{index}]"
    value = _obj(raw, where)
    _fields(value, ITEM_FIELDS, where)
    item_id = _match(value["datasetItemId"], ID, f"{where}.datasetItemId")
    family_id = _match(value["sourceFamilyId"], ID, f"{where}.sourceFamilyId")
    parent_id = _match(value["parentItemId"], ID, f"{where}.parentItemId", null=True)
    eligibility = _enum(
        value["eligibilityClass"],
        ELIGIBILITY_CLASSES,
        f"{where}.eligibilityClass",
    )
    assert item_id and family_id
    if parent_id == item_id:
        raise DatasetManifestError(f"{where}.parentItemId cannot reference itself")

    artifact = _obj(value["artifact"], f"{where}.artifact")
    _fields(
        artifact,
        {
            "state",
            "sha256",
            "byteSize",
            "storageLocator",
            "custodyProfileId",
            "encryptionProfileId",
            "custodianId",
        },
        f"{where}.artifact",
    )
    state = _enum(artifact["state"], ARTIFACT_STATES, f"{where}.artifact.state")
    digest = _match(artifact["sha256"], SHA, f"{where}.artifact.sha256", null=True)
    size = artifact["byteSize"]
    if size is not None:
        _int(size, f"{where}.artifact.byteSize", 1)
    locator = _match(
        artifact["storageLocator"],
        CUSTODY_ID,
        f"{where}.artifact.storageLocator",
        null=True,
    )
    custody = _match(
        artifact["custodyProfileId"],
        POLICY_ID,
        f"{where}.artifact.custodyProfileId",
        null=True,
    )
    encryption = _match(
        artifact["encryptionProfileId"],
        POLICY_ID,
        f"{where}.artifact.encryptionProfileId",
        null=True,
    )
    custodian = _match(
        artifact["custodianId"],
        CUSTODIAN_ACTOR_ID,
        f"{where}.artifact.custodianId",
        null=True,
    )
    evidence = (digest, size, locator, custody, encryption, custodian)
    if state == "metadata_only" and any(v is not None for v in evidence):
        raise DatasetManifestError(
            f"{where}.artifact metadata_only cannot reference bytes or custody"
        )
    if state == "external_available" and any(v is None for v in evidence):
        raise DatasetManifestError(
            f"{where}.artifact external_available requires digest, size, locator, "
            "custody/encryption policy, and opaque custodian"
        )
    if state == "revoked" and (
        digest is None
        or size is None
        or locator is not None
        or any(v is None for v in (custody, encryption, custodian))
    ):
        raise DatasetManifestError(
            f"{where}.artifact revoked keeps digest/custody evidence but no locator"
        )

    provenance = _obj(value["provenance"], f"{where}.provenance")
    _fields(
        provenance,
        {
            "sourceKind",
            "sourceReference",
            "rightsHolderId",
            "licenseId",
            "usageBasisCode",
            "rightsReview",
        },
        f"{where}.provenance",
    )
    source = _enum(
        provenance["sourceKind"], SOURCE_KINDS, f"{where}.provenance.sourceKind"
    )
    _match(
        provenance["sourceReference"],
        EVIDENCE_ID,
        f"{where}.provenance.sourceReference",
    )
    _match(
        provenance["rightsHolderId"],
        SUBJECT_ID,
        f"{where}.provenance.rightsHolderId",
    )
    _match(provenance["licenseId"], CODE, f"{where}.provenance.licenseId")
    basis = _enum(
        provenance["usageBasisCode"],
        USAGE_BASIS_CODES,
        f"{where}.provenance.usageBasisCode",
    )
    rights, _, rights_on, _ = _review_evidence(
        provenance["rightsReview"],
        f"{where}.provenance.rightsReview",
        states=RIGHTS_REVIEW_STATES,
        actor_pattern=RIGHTS_ACTOR_ID,
        actor_field="verifiedBy",
        date_field="verifiedOn",
        evidence_field="evidenceReference",
    )
    if (source == "synthetic") != (basis == "synthetic_derivation"):
        raise DatasetManifestError(
            f"{where}.provenance source and usage basis are inconsistent"
        )

    privacy = _obj(value["privacy"], f"{where}.privacy")
    _fields(
        privacy,
        {
            "classification",
            "reviewStatus",
            "reviewedBy",
            "reviewedOn",
            "evidenceReference",
            "deidentificationMethodCode",
            "deidentifiedArtifactSha256",
        },
        f"{where}.privacy",
    )
    privacy_class = _enum(
        privacy["classification"],
        PRIVACY_CLASSES,
        f"{where}.privacy.classification",
    )
    privacy_review = _enum(
        privacy["reviewStatus"],
        PRIVACY_REVIEW_STATES,
        f"{where}.privacy.reviewStatus",
    )
    actor = _match(
        privacy["reviewedBy"],
        PRIVACY_ACTOR_ID,
        f"{where}.privacy.reviewedBy",
        null=True,
    )
    privacy_on = _date(
        privacy["reviewedOn"], f"{where}.privacy.reviewedOn", null=True
    )
    privacy_evidence = _match(
        privacy["evidenceReference"],
        EVIDENCE_ID,
        f"{where}.privacy.evidenceReference",
        null=True,
    )
    method = privacy["deidentificationMethodCode"]
    if method is not None:
        method = _enum(
            method,
            DEIDENTIFICATION_METHODS,
            f"{where}.privacy.deidentificationMethodCode",
        )
    deid_sha = _match(
        privacy["deidentifiedArtifactSha256"],
        SHA,
        f"{where}.privacy.deidentifiedArtifactSha256",
        null=True,
    )
    completed = privacy_review in {"approved", "rejected"}
    if completed != (
        actor is not None and privacy_on is not None and privacy_evidence is not None
    ):
        raise DatasetManifestError(
            f"{where}.privacy actor/date/evidence do not match review status"
        )
    if not completed and any(
        v is not None for v in (actor, privacy_on, privacy_evidence)
    ):
        raise DatasetManifestError(
            f"{where}.privacy incomplete review cannot claim evidence"
        )
    if privacy_class == "none":
        if (
            privacy_review not in {"not_required", "approved"}
            or method is not None
            or deid_sha is not None
        ):
            raise DatasetManifestError(
                f"{where}.privacy none classification is inconsistent"
            )
    elif privacy_class == "deidentified":
        if (
            privacy_review != "approved"
            or method is None
            or deid_sha is None
            or state not in {"external_available", "revoked"}
            or deid_sha != digest
        ):
            raise DatasetManifestError(
                f"{where}.privacy de-identification digest must match an "
                "available or revoked artifact digest"
            )
    elif privacy_review == "not_required" or method is not None or deid_sha is not None:
        raise DatasetManifestError(
            f"{where}.privacy identifiable data requires review and cannot claim "
            "de-identification"
        )

    input_data = _obj(value["input"], f"{where}.input")
    _fields(
        input_data,
        {"kind", "mediaType", "notationKinds", "pageCount", "degradations"},
        f"{where}.input",
    )
    kind = _enum(input_data["kind"], set(INPUT_MEDIA), f"{where}.input.kind")
    if input_data["mediaType"] != INPUT_MEDIA[kind]:
        raise DatasetManifestError(f"{where}.input.mediaType does not match kind")
    for field, choices in (
        ("notationKinds", NOTATION_KINDS),
        ("degradations", DEGRADATIONS),
    ):
        raw_values = _arr(input_data[field], f"{where}.input.{field}")
        values = [
            _enum(v, choices, f"{where}.input.{field}[]") for v in raw_values
        ]
        if len(set(values)) != len(values):
            raise DatasetManifestError(f"{where}.input.{field} must be unique")
        if field == "degradations" and "none" in values and len(values) > 1:
            raise DatasetManifestError(
                f"{where}.input.degradations cannot mix none and damage"
            )
    _int(input_data["pageCount"], f"{where}.input.pageCount", 1)
    split = _enum(value["split"], SPLITS, f"{where}.split")
    return value, {
        "where": where,
        "id": item_id,
        "family": family_id,
        "parent": parent_id,
        "eligibility": eligibility,
        "source": source,
        "artifact": state,
        "digest": digest,
        "rights": rights,
        "rightsOn": rights_on,
        "privacy": privacy_review,
        "privacyOn": privacy_on,
        "privacyClass": privacy_class,
        "split": split,
    }
