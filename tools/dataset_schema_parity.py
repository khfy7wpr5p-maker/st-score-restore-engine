"""Comprehensive JSON Schema/Python contract parity for Stage 1A."""
from __future__ import annotations
from typing import Any
from st_score_restore.dataset_contract_constants import (
    ARTIFACT_STATES, CATALOG_FIELDS, CATALOG_SCHEMA_VERSION, CODE,
    CUSTODIAN_ACTOR_ID, CUSTODY_ID, DATASET_ACTOR_ID,
    DATASET_REVIEW_STATES, DATE, DEGRADATIONS, DEIDENTIFICATION_METHODS,
    DELETION_STATES, ENTRY_DECISION_ID, EVIDENCE_ID, ID, INPUT_MEDIA,
    ITEM_FIELDS, NOTATION_KINDS, PERMISSION_STATES, POLICY_ID,
    PRIVACY_ACTOR_ID, PRIVACY_CLASSES, PRIVACY_REVIEW_STATES, PURPOSES,
    PURPOSE_ACTOR_ID, RECEIPT_ID, RESTRICTION_TYPES, RETENTION_POLICIES,
    REVOCATION_STATES, RIGHTS_ACTOR_ID, RIGHTS_REVIEW_STATES, SHA,
    SNAPSHOT_FIELDS, SNAPSHOT_SCHEMA_VERSION, SOURCE_KINDS, SPLITS,
    STAGE1_ENVIRONMENT, STORAGE_CLASSES, SUBJECT_ID, USAGE_BASIS_CODES, UTC,
)
from st_score_restore.dataset_manifest import DatasetManifestError
from tools.dataset_schema_helpers import (
    assert_schema_valid, const, enum, pattern, properties, required,
)

def validate_schema_parity(catalog_schema: dict[str, Any], snapshot_schema: dict[str, Any]) -> None:
    """Fail when Draft 2020-12 schemas and Python constants drift."""
    draft = 'https://json-schema.org/draft/2020-12/schema'
    if catalog_schema.get('$schema') != draft:
        raise DatasetManifestError('dataset catalog schema must use Draft 2020-12')
    if snapshot_schema.get('$schema') != draft:
        raise DatasetManifestError('dataset snapshot schema must use Draft 2020-12')
    assert_schema_valid(catalog_schema, 'dataset catalog schema')
    assert_schema_valid(snapshot_schema, 'dataset snapshot schema')
    catalogproperties = properties(catalog_schema, 'catalog')
    snapshotproperties = properties(snapshot_schema, 'snapshot')
    if required(catalog_schema, 'catalog') != CATALOG_FIELDS:
        raise DatasetManifestError('dataset catalog required-field drift')
    if required(snapshot_schema, 'snapshot') != SNAPSHOT_FIELDS:
        raise DatasetManifestError('dataset snapshot required-field drift')
    const(catalogproperties['schemaVersion'], CATALOG_SCHEMA_VERSION, 'catalog.schemaVersion')
    const(snapshotproperties['schemaVersion'], SNAPSHOT_SCHEMA_VERSION, 'snapshot.schemaVersion')
    const(catalogproperties['entryDecisionId'], ENTRY_DECISION_ID, 'catalog.entryDecisionId')
    const(snapshotproperties['entryDecisionId'], ENTRY_DECISION_ID, 'snapshot.entryDecisionId')
    const(snapshotproperties['environment'], STAGE1_ENVIRONMENT, 'snapshot.environment')
    const(snapshotproperties['trainingUseActivated'], False, 'snapshot.trainingUseActivated')
    pattern(catalogproperties['descriptionCode'], CODE.pattern, 'catalog.descriptionCode')
    pattern(snapshotproperties['createdAt'], UTC.pattern, 'snapshot.createdAt')
    pattern(snapshotproperties['version'], '^\\d+\\.\\d+\\.\\d+$', 'snapshot.version')
    pattern(snapshotproperties['catalogSha256'], SHA.pattern, 'snapshot.catalogSha256')
    definitions = catalog_schema.get('$defs', {})
    if not isinstance(definitions, dict):
        raise DatasetManifestError('catalog.$defs must be an object')
    pattern(definitions['id'], ID.pattern, '$defs.id')
    pattern(definitions['nullableId'], ID.pattern, '$defs.nullableId')
    pattern(definitions['nullableDate'], DATE.pattern, '$defs.nullableDate')
    pattern(definitions['nullableSha'], SHA.pattern, '$defs.nullableSha')
    pattern(definitions['nullableEvidence'], EVIDENCE_ID.pattern, '$defs.nullableEvidence')
    item_schema = definitions.get('item', {})
    itemproperties = properties(item_schema, 'catalog.$defs.item')
    if required(item_schema, 'catalog.$defs.item') != ITEM_FIELDS:
        raise DatasetManifestError('dataset item required-field drift')
    artifact = itemproperties['artifact']
    artifactproperties = properties(artifact, 'item.artifact')
    if required(artifact, 'item.artifact') != {'state', 'sha256', 'byteSize', 'storageLocator', 'custodyProfileId', 'encryptionProfileId', 'custodianId'}:
        raise DatasetManifestError('artifact required-field drift')
    if enum(artifactproperties['state'], 'item.artifact.state') != ARTIFACT_STATES:
        raise DatasetManifestError('artifact-state drift')
    pattern(artifactproperties['storageLocator'], CUSTODY_ID.pattern, 'artifact.storageLocator')
    pattern(artifactproperties['custodyProfileId'], POLICY_ID.pattern, 'artifact.custodyProfileId')
    pattern(artifactproperties['encryptionProfileId'], POLICY_ID.pattern, 'artifact.encryptionProfileId')
    pattern(artifactproperties['custodianId'], CUSTODIAN_ACTOR_ID.pattern, 'artifact.custodianId')
    provenance = itemproperties['provenance']
    provenanceproperties = properties(provenance, 'item.provenance')
    if required(provenance, 'item.provenance') != {'sourceKind', 'sourceReference', 'rightsHolderId', 'licenseId', 'usageBasisCode', 'rightsReview'}:
        raise DatasetManifestError('provenance required-field drift')
    if enum(provenanceproperties['sourceKind'], 'provenance.sourceKind') != SOURCE_KINDS:
        raise DatasetManifestError('source-kind drift')
    if enum(provenanceproperties['usageBasisCode'], 'provenance.usageBasisCode') != USAGE_BASIS_CODES:
        raise DatasetManifestError('usage-basis drift')
    pattern(provenanceproperties['sourceReference'], EVIDENCE_ID.pattern, 'provenance.sourceReference')
    pattern(provenanceproperties['rightsHolderId'], SUBJECT_ID.pattern, 'provenance.rightsHolderId')
    pattern(provenanceproperties['licenseId'], CODE.pattern, 'provenance.licenseId')
    rights_review = provenanceproperties['rightsReview']
    rightsproperties = properties(rights_review, 'rightsReview')
    if enum(rightsproperties['status'], 'rightsReview.status') != RIGHTS_REVIEW_STATES:
        raise DatasetManifestError('rights-review state drift')
    pattern(rightsproperties['verifiedBy'], RIGHTS_ACTOR_ID.pattern, 'rightsReview.verifiedBy')
    privacy = itemproperties['privacy']
    privacyproperties = properties(privacy, 'item.privacy')
    if enum(privacyproperties['classification'], 'privacy.classification') != PRIVACY_CLASSES:
        raise DatasetManifestError('privacy-class drift')
    if enum(privacyproperties['reviewStatus'], 'privacy.reviewStatus') != PRIVACY_REVIEW_STATES:
        raise DatasetManifestError('privacy-review state drift')
    if enum(privacyproperties['deidentificationMethodCode'], 'privacy.deidentificationMethodCode') != DEIDENTIFICATION_METHODS | {None}:
        raise DatasetManifestError('de-identification method drift')
    pattern(privacyproperties['reviewedBy'], PRIVACY_ACTOR_ID.pattern, 'privacy.reviewedBy')
    input_schema = itemproperties['input']
    inputproperties = properties(input_schema, 'item.input')
    if enum(inputproperties['kind'], 'input.kind') != set(INPUT_MEDIA):
        raise DatasetManifestError('input-kind drift')
    if enum(inputproperties['mediaType'], 'input.mediaType') != set(INPUT_MEDIA.values()):
        raise DatasetManifestError('input-media drift')
    if enum(inputproperties['notationKinds']['items'], 'input.notationKinds') != NOTATION_KINDS:
        raise DatasetManifestError('notation-kind drift')
    if enum(inputproperties['degradations']['items'], 'input.degradations') != DEGRADATIONS:
        raise DatasetManifestError('degradation drift')
    permissions = itemproperties['permissions']
    if required(permissions, 'item.permissions') != set(PURPOSES):
        raise DatasetManifestError('dataset purpose required-field drift')
    if set(properties(permissions, 'item.permissions')) != set(PURPOSES):
        raise DatasetManifestError('dataset purpose property drift')
    permission = definitions['permission']
    permissionproperties = properties(permission, 'permission')
    if enum(permissionproperties['status'], 'permission.status') != PERMISSION_STATES:
        raise DatasetManifestError('permission-state drift')
    pattern(permissionproperties['authorizedBy'], PURPOSE_ACTOR_ID.pattern, 'permission.authorizedBy')
    if enum(itemproperties['split'], 'item.split') != SPLITS:
        raise DatasetManifestError('dataset split drift')
    retention = itemproperties['retention']
    retentionproperties = properties(retention, 'item.retention')
    if enum(retentionproperties['policy'], 'retention.policy') != RETENTION_POLICIES:
        raise DatasetManifestError('retention-policy drift')
    if enum(retentionproperties['storageClass'], 'retention.storageClass') != STORAGE_CLASSES:
        raise DatasetManifestError('storage-class drift')
    if enum(retentionproperties['deletionStatus'], 'retention.deletionStatus') != DELETION_STATES:
        raise DatasetManifestError('deletion-state drift')
    pattern(retentionproperties['deletionReceiptReference'], RECEIPT_ID.pattern, 'retention.deletionReceiptReference')
    revocationproperties = properties(itemproperties['revocation'], 'item.revocation')
    if enum(revocationproperties['status'], 'revocation.status') != REVOCATION_STATES:
        raise DatasetManifestError('revocation-state drift')
    synthetic_variants = itemproperties['syntheticGeneration']['oneOf']
    synthetic_object = next((variant for variant in synthetic_variants if variant.get('type') == 'object'))
    syntheticproperties = properties(synthetic_object, 'syntheticGeneration')
    pattern(syntheticproperties['derivationAuthorizationReference'], EVIDENCE_ID.pattern, 'syntheticGeneration.derivationAuthorizationReference')
    parameter_variants = definitions['parameterValue']['oneOf']
    parameter_types = {variant.get('type') for variant in parameter_variants}
    if parameter_types != {'null', 'boolean', 'number', 'array', 'object'}:
        raise DatasetManifestError('synthetic parameter type drift or free-text enabled')
    reviewproperties = properties(itemproperties['review'], 'item.review')
    if enum(reviewproperties['status'], 'review.status') != DATASET_REVIEW_STATES:
        raise DatasetManifestError('dataset-review state drift')
    pattern(reviewproperties['reviewedBy'], DATASET_ACTOR_ID.pattern, 'review.reviewedBy')
    assertions = properties(itemproperties['assertions'], 'item.assertions')
    for name in ('teacherApprovalImpliedDatasetPermission', 'teacherApprovalImpliedTrainingPermission', 'originalBytesInGit', 'stage1TrainingExecutionAuthorized'):
        const(assertions[name], False, f'assertions.{name}')
    restriction_variants = definitions['restriction']['oneOf']
    restriction_types = {variant['properties']['type']['const'] for variant in restriction_variants}
    if restriction_types != RESTRICTION_TYPES:
        raise DatasetManifestError('typed-restriction drift')
    snapshot_assignment = snapshotproperties['assignments']['items']
    if required(snapshot_assignment, 'snapshot.assignment') != {'datasetItemId', 'sourceFamilyId', 'split', 'itemSha256'}:
        raise DatasetManifestError('snapshot assignment required-field drift')
    snapshot_review = snapshotproperties['review']
    snapshot_reviewproperties = properties(snapshot_review, 'snapshot.review')
    const(snapshot_reviewproperties['status'], 'approved', 'snapshot.review.status')
    pattern(snapshot_reviewproperties['reviewedBy'], DATASET_ACTOR_ID.pattern, 'snapshot.review.reviewedBy')
    pattern(snapshot_reviewproperties['evidenceReference'], EVIDENCE_ID.pattern, 'snapshot.review.evidenceReference')
