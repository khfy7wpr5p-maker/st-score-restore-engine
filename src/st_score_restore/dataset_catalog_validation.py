"""Catalog-level Stage 1A lineage and split validation."""

from __future__ import annotations

from datetime import date
from typing import Any

from .dataset_contract_common import (
    _arr,
    _fields,
    _match,
    _obj,
    _restriction_by_type,
    _text,
)
from .dataset_contract_constants import (
    CATALOG_FIELDS,
    CATALOG_SCHEMA_VERSION,
    DatasetManifestError,
    ENTRY_DECISION_ID,
    ID,
    STAGE1_ENVIRONMENT,
)
from .dataset_item_validation import _item

def validate_dataset_catalog(data: Any) -> dict[str, Any]:
    """Validate a complete Stage 1A dataset catalog."""
    catalog = _obj(data, "catalog")
    _fields(catalog, CATALOG_FIELDS, "catalog")
    if catalog["schemaVersion"] != CATALOG_SCHEMA_VERSION:
        raise DatasetManifestError(
            f"catalog.schemaVersion must be {CATALOG_SCHEMA_VERSION}"
        )
    if catalog["entryDecisionId"] != ENTRY_DECISION_ID:
        raise DatasetManifestError(
            f"catalog.entryDecisionId must be {ENTRY_DECISION_ID}"
        )
    _match(catalog["catalogId"], ID, "catalog.catalogId")
    _text(catalog["description"], "catalog.description")
    items = [
        _item(raw, index)
        for index, raw in enumerate(_arr(catalog["items"], "catalog.items"))
    ]

    by_id: dict[str, dict[str, Any]] = {}
    digest_family: dict[str, str] = {}
    family_splits: dict[str, set[str]] = {}
    for item in items:
        if item["id"] in by_id:
            raise DatasetManifestError(f"duplicate datasetItemId: {item['id']}")
        by_id[item["id"]] = item
        if item["digest"]:
            prior = digest_family.setdefault(item["digest"], item["family"])
            if prior != item["family"]:
                raise DatasetManifestError(
                    "identical artifact digest crosses source families"
                )
        if item["split"] != "unassigned":
            family_splits.setdefault(item["family"], set()).add(item["split"])

    for item in items:
        if item["parent"] is None:
            continue
        parent = by_id.get(item["parent"])
        if parent is None:
            raise DatasetManifestError(
                f"{item['id']} references unknown parentItemId"
            )
        if parent["source"] == "synthetic":
            raise DatasetManifestError(
                f"{item['id']} cannot derive from synthetic parent"
            )
        if parent["family"] != item["family"]:
            raise DatasetManifestError(
                f"{item['id']} must share sourceFamilyId with parent"
            )
        if (
            parent["artifact"] != "external_available"
            or parent["review"] != "approved"
            or parent["rights"] != "approved"
            or parent["privacy"] not in {"approved", "not_required"}
        ):
            raise DatasetManifestError(
                f"{item['id']} parent is not rights/privacy/dataset approved and available"
            )
        derivation_permission = parent["permissions"]["synthetic_derivation"]
        generated_on = item["generatedOn"]
        if (
            generated_on is None
            or item["derivationReference"]
            != derivation_permission["authorizationReference"]
            or derivation_permission["status"]
            not in {"granted", "expired", "withdrawn"}
            or derivation_permission["authorizedOn"] is None
            or derivation_permission["authorizedOn"] > generated_on
            or (
                derivation_permission["expiresOn"] is not None
                and generated_on >= derivation_permission["expiresOn"]
            )
            or (
                derivation_permission["revokedOn"] is not None
                and generated_on >= derivation_permission["revokedOn"]
            )
            or (
                parent["rightsOn"] is not None
                and parent["rightsOn"] > generated_on
            )
            or (
                parent["privacyOn"] is not None
                and parent["privacyOn"] > generated_on
            )
            or (
                parent["reviewOn"] is not None
                and parent["reviewOn"] > generated_on
            )
        ):
            raise DatasetManifestError(
                f"{item['id']} parent synthetic-derivation authorization or approval was not valid at generation time"
            )

        split_rule = _restriction_by_type(
            derivation_permission, "split_allowlist"
        )
        storage_rule = _restriction_by_type(
            derivation_permission, "storage_class_allowlist"
        )
        environment_rule = _restriction_by_type(
            derivation_permission, "environment_allowlist"
        )
        retention_rule = _restriction_by_type(
            derivation_permission, "retention_not_after"
        )
        parent_retention = parent["retention"]["expiresOn"]
        if (
            (split_rule is not None and parent["split"] not in split_rule["values"])
            or (
                storage_rule is not None
                and parent["retention"]["storageClass"]
                not in storage_rule["values"]
            )
            or (
                environment_rule is not None
                and STAGE1_ENVIRONMENT not in environment_rule["values"]
            )
            or (
                retention_rule is not None
                and (
                    parent_retention is None
                    or parent_retention
                    > date.fromisoformat(retention_rule["date"])
                )
            )
        ):
            raise DatasetManifestError(
                f"{item['id']} parent synthetic-derivation restrictions were not satisfied"
            )

        child_retention = item["retention"]["expiresOn"]
        parent_policy = parent["retention"]["policy"]
        child_policy = item["retention"]["policy"]
        if (
            parent_policy == "delete_after_validation"
            and child_policy != "delete_after_validation"
        ):
            raise DatasetManifestError(
                f"{item['id']} child retention policy cannot be weaker than parent"
            )
        if (
            parent_policy == "external_until_date"
            and child_policy not in {"external_until_date", "delete_after_validation"}
        ):
            raise DatasetManifestError(
                f"{item['id']} child retention policy cannot be weaker than parent"
            )
        if parent_retention is not None and (
            child_retention is None or child_retention > parent_retention
        ):
            raise DatasetManifestError(
                f"{item['id']} child retention cannot exceed parent retention"
            )
        if (
            parent["privacyClass"] == "deidentified"
            and item["privacyClass"] != "deidentified"
        ):
            raise DatasetManifestError(
                f"{item['id']} child privacy cannot be weaker than deidentified parent"
            )

    if any(len(splits) > 1 for splits in family_splits.values()):
        raise DatasetManifestError("source-family split leakage detected")
    return catalog
