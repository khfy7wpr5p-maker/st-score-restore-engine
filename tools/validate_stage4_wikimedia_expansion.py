from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from st_score_restore.dataset_contract_common import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evidence/stage1c/corpus/catalog.v2.json"
PARENT_GRANT = ROOT / "evidence/stage4/governance/purpose-grants.v1.json"
GRANT = ROOT / "evidence/stage4/corpus-expansion/wikimedia/purpose-grant.v1.json"
WORK_PACKAGE = ROOT / "evidence/stage4/corpus-expansion/wikimedia/reference-label-work-package.v1.json"

CATALOG_DIGEST = "4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3"
PARENT_GRANT_DIGEST = "4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc"
WIKIMEDIA_GRANT_DIGEST = "603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07"
ITEM_ID = "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"
SOURCE_FAMILY_ID = "source.family.wikimedia-guitar-technical-exercise-no1.v1"
ARTIFACT_SHA256 = "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb"
ARTIFACT_BYTE_SIZE = 34636
HELD_OUT_ID = "dataset.item.imslp82860-chopin-op69.v2"
HELD_OUT_SHA256 = "b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3"
EXECUTION_EVIDENCE_SHA256 = "0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a"
FINDINGS = {"skew", "blur", "glare", "shadow", "uneven_lighting", "noise", "compression"}
LABELS = {"clear", "possible", "probable", "not_assessed"}
OPAQUE_EVIDENCE = re.compile(r"^evidence:opq_[0-9a-f]{32}$")
OPAQUE_PURPOSE_ACTOR = re.compile(r"^actor\.purpose:opq_[0-9a-f]{32}$")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    for path in (CATALOG, PARENT_GRANT, GRANT, WORK_PACKAGE):
        require(path.exists(), f"required Wikimedia Stage 4 expansion input missing: {path.relative_to(ROOT)}")
    if failures:
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    catalog = load(CATALOG)
    parent = load(PARENT_GRANT)
    grant = load(GRANT)
    package = load(WORK_PACKAGE)

    require(canonical_sha256(catalog) == CATALOG_DIGEST, "historical Stage 1 catalog digest drifted")
    require(canonical_sha256(parent) == PARENT_GRANT_DIGEST, "historical Beethoven+Barley Stage 4 purpose grant drifted")
    require(canonical_sha256(grant) == WIKIMEDIA_GRANT_DIGEST, "Wikimedia Stage 4 purpose-grant digest drifted")

    items = [item for item in catalog.get("items", []) if item.get("datasetItemId") == ITEM_ID]
    require(len(items) == 1, "Wikimedia development item missing or duplicated in Stage 1 catalog")
    if items:
        item = items[0]
        artifact = item.get("artifact", {})
        input_data = item.get("input", {})
        retention = item.get("retention", {})
        require(item.get("sourceFamilyId") == SOURCE_FAMILY_ID, "Wikimedia source-family binding drifted")
        require(item.get("split") == "development", "Wikimedia expansion item is not development-only")
        require(artifact.get("sha256") == ARTIFACT_SHA256, "Wikimedia artifact SHA-256 drifted")
        require(artifact.get("byteSize") == ARTIFACT_BYTE_SIZE, "Wikimedia artifact byte size drifted")
        require(input_data.get("kind") == "png" and input_data.get("pageCount") == 1, "Wikimedia input must remain one-page PNG")
        require(retention.get("storageClass") == "managed_standard", "Wikimedia storage class drifted")
        require((item.get("revocation") or {}).get("status") == "not_revoked", "Wikimedia item is revoked")

    require(grant.get("schemaVersion") == "1.0.0", "Wikimedia grant schema drifted")
    require(grant.get("grantSetId") == "stage4.purpose-grants.wikimedia-guitar-technical-exercise-safety-calibration.v1", "Wikimedia grant-set ID drifted")
    require(grant.get("authorizationSourceCode") == "explicit_user_authorization", "Wikimedia grant lost explicit-user authorization source")
    require(bool(OPAQUE_EVIDENCE.fullmatch(str(grant.get("authorizationReference", "")))), "Wikimedia grant authorization reference is not opaque evidence")
    require(bool(OPAQUE_PURPOSE_ACTOR.fullmatch(str(grant.get("authorizedBy", "")))), "Wikimedia grant authorizedBy is not an opaque purpose actor")
    require(grant.get("parentGrantSet", {}).get("canonicalSha256") == PARENT_GRANT_DIGEST, "Wikimedia grant lost immutable parent-grant binding")
    require(grant.get("parentGrantSet", {}).get("modified") is False, "Wikimedia grant claims parent grant modification")

    granted = grant.get("grant", {})
    permission = granted.get("permission", {})
    require(granted.get("datasetItemId") == ITEM_ID, "Wikimedia grant item ID drifted")
    require(granted.get("sourceFamilyId") == SOURCE_FAMILY_ID, "Wikimedia grant source family drifted")
    require(granted.get("artifactSha256") == ARTIFACT_SHA256, "Wikimedia grant artifact digest drifted")
    require(granted.get("artifactByteSize") == ARTIFACT_BYTE_SIZE, "Wikimedia grant artifact size drifted")
    require(granted.get("inputKind") == "png" and granted.get("pageCount") == 1, "Wikimedia grant input scope drifted")
    require(granted.get("purpose") == "safety_calibration", "Wikimedia grant purpose drifted")
    require(permission.get("status") == "granted", "Wikimedia safety-calibration permission is not granted")
    restrictions = permission.get("restrictions", [])
    require({entry.get("type") for entry in restrictions} == {"split_allowlist", "storage_class_allowlist", "environment_allowlist", "external_export"}, "Wikimedia grant restrictions drifted")
    by_type = {entry.get("type"): entry for entry in restrictions}
    require(by_type.get("split_allowlist", {}).get("values") == ["development"], "Wikimedia grant crossed development split")
    require(by_type.get("storage_class_allowlist", {}).get("values") == ["managed_standard"], "Wikimedia grant storage allowlist drifted")
    require(by_type.get("environment_allowlist", {}).get("values") == ["stage1_offline"], "Wikimedia grant environment allowlist drifted")
    require(by_type.get("external_export", {}).get("allowed") is False, "Wikimedia grant allowed external export")

    held = grant.get("heldOutBinding", {})
    require(held.get("datasetItemId") == HELD_OUT_ID and held.get("artifactSha256") == HELD_OUT_SHA256, "Wikimedia grant held-out binding drifted")
    require(held.get("split") == "held_out" and held.get("purpose") == "held_out_evaluation", "Wikimedia grant changed held-out purpose")
    require(held.get("candidateDerivationAuthorized") is False and held.get("evaluationExecuted") is False and held.get("tuningAuthorized") is False, "Wikimedia grant crossed held-out boundary")
    require(grant.get("triggerBinding", {}).get("realDevelopmentExecutionEvidenceSha256") == EXECUTION_EVIDENCE_SHA256, "Wikimedia expansion trigger lost executed-abstained evidence binding")
    require(grant.get("triggerBinding", {}).get("candidateDerivedCount") == 0, "Wikimedia expansion trigger falsely claims a candidate")

    assertions = grant.get("assertions", {})
    for key in (
        "historicalCatalogModified",
        "parentPurposeGrantModified",
        "humanReferenceLabelsPresent",
        "referenceLabelBundleAccepted",
        "realDataCalibrationExecutionAuthorized",
        "realDataCalibrationExecuted",
        "trainingAuthorized",
        "publicationAuthorized",
        "demonstrationAuthorized",
        "externalExportAuthorized",
        "heldOutAuthorizationChanged",
        "heldOutTuningAuthorized",
        "heldOutEvaluationExecuted",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(assertions.get(key) is False, f"unsafe Wikimedia grant assertion became true: {key}")
    require(assertions.get("safetyCalibrationPurposeAuthorized") is True, "Wikimedia safety-calibration purpose is not authorized")

    require(package.get("packageId") == "stage4.reference-label-review.wikimedia-guitar-technical-exercise.v1", "Wikimedia work-package ID drifted")
    require(package.get("state") == "awaiting_human_labels", "Wikimedia work package is not awaiting human labels")
    require(package.get("contractVersion") == "0.1.0", "Wikimedia work-package contract drifted")
    require(package.get("purposeGrantDigest") == WIKIMEDIA_GRANT_DIGEST, "Wikimedia work package is not bound to the exact grant")
    scope = package.get("reviewScope", {})
    require(scope.get("split") == "development" and scope.get("purpose") == "safety_calibration", "Wikimedia review scope drifted")
    require(scope.get("reviewMethodRequired") == "human_expert_review", "Wikimedia review method is not human_expert_review")
    require(scope.get("acceptedRealReferenceBundle") is False, "Wikimedia work package prematurely accepts a reference bundle")
    require(scope.get("realDataCalibrationExecutionAuthorized") is False, "Wikimedia work package prematurely authorizes calibration execution")
    require(scope.get("modelPredictionsAllowedAsReference") is False, "Wikimedia work package allows model predictions as reference truth")
    require(set(package.get("labelVocabulary", [])) == LABELS, "Wikimedia label vocabulary drifted")
    require(set(package.get("findingTypes", [])) == FINDINGS, "Wikimedia finding taxonomy drifted")

    review_item = package.get("item", {})
    require(review_item.get("datasetItemId") == ITEM_ID and review_item.get("sourceFamilyId") == SOURCE_FAMILY_ID, "Wikimedia work-package item binding drifted")
    require(review_item.get("artifactSha256") == ARTIFACT_SHA256 and review_item.get("artifactByteSize") == ARTIFACT_BYTE_SIZE, "Wikimedia work-package artifact binding drifted")
    require(review_item.get("inputKind") == "png" and review_item.get("pageCount") == 1, "Wikimedia work-package page/input scope drifted")
    pages = review_item.get("pages", [])
    require(len(pages) == 1 and pages[0].get("pageNumber") == 1, "Wikimedia work package must contain exactly page 1")
    reviews = pages[0].get("reviews", []) if pages else []
    require(len(reviews) == 7, "Wikimedia work package must contain exactly seven human-review slots")
    require({row.get("findingType") for row in reviews} == FINDINGS, "Wikimedia review slots do not cover the exact seven findings")
    require(len({row.get("labelId") for row in reviews}) == 7 and len({row.get("observationId") for row in reviews}) == 7, "Wikimedia review identifiers are not unique")
    for row in reviews:
        require(all(row.get(field) is None for field in ("referenceLabel", "reviewerReference", "provenanceReference", "reviewedOn")), f"Wikimedia review slot {row.get('findingType')} was pre-labelled")

    exclusions = package.get("heldOutExclusions", [])
    require(len(exclusions) == 1 and exclusions[0].get("datasetItemId") == HELD_OUT_ID, "Wikimedia work package lost exact Chopin exclusion")
    require(exclusions[0].get("includedInDevelopmentReview") is False and exclusions[0].get("candidateDerivationAuthorized") is False, "Wikimedia work package crossed held-out boundary")

    package_assertions = package.get("assertions", {})
    for key in (
        "humanLabelsPresent",
        "referenceBundleAccepted",
        "labelsAutomaticallyGenerated",
        "modelPredictionsUsedAsReferenceLabels",
        "heldOutIncludedInDevelopmentReview",
        "expansionCalibrationExecutionAuthorized",
        "expansionCalibrationExecuted",
        "productionThresholdChangeAuthorized",
        "productionResourceLimitChangeAuthorized",
        "stage4ExitPass",
        "stage5EntryAuthorized",
    ):
        require(package_assertions.get(key) is False, f"unsafe Wikimedia work-package assertion became true: {key}")

    if failures:
        print("Stage 4 Wikimedia expansion validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 4 Wikimedia expansion validation: PASS")
    print(f"- purpose grant SHA-256: {WIKIMEDIA_GRANT_DIGEST}")
    print("- exact development item: Wikimedia Guitar Technical Exercise No.1 / one-page PNG")
    print("- human review slots: 7 / labels present: 0")
    print("- held-out included: false / execution authorized: false / Stage 5: blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
