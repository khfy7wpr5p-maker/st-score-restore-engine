from __future__ import annotations
PURPOSES = ('fixture_validation', 'quality_evaluation', 'quality_calibration', 'pdf_pipeline_evaluation', 'safety_calibration', 'held_out_evaluation', 'synthetic_derivation', 'model_training', 'publication', 'demonstration')

def opaque(number: int) -> str:
    return f'opq_{number:032x}'

def permission(status: str='not_requested', *, authorized_on: str='2026-08-01', expires_on: str | None=None, restrictions: list[dict] | None=None, authorization_reference: str | None=None) -> dict:
    value = {'status': status, 'authorizationReference': None, 'authorizedBy': None, 'authorizedOn': None, 'expiresOn': None, 'restrictions': [], 'revokedOn': None, 'revocationReference': None}
    if status in {'granted', 'expired', 'withdrawn'}:
        value.update({'authorizationReference': authorization_reference or f'evidence:{opaque(10)}', 'authorizedBy': f'actor.purpose:{opaque(11)}', 'authorizedOn': authorized_on, 'expiresOn': expires_on, 'restrictions': restrictions or []})
    if status == 'expired' and expires_on is None:
        value['expiresOn'] = '2026-08-05'
    if status == 'withdrawn':
        value.update({'revokedOn': '2026-08-05', 'revocationReference': f'evidence:{opaque(12)}'})
    return value

def item(item_id: str='dataset.item.clean-staff.v1', *, family_id: str='source.family.clean-staff.v1', split: str='unassigned', source_kind: str='public_domain', artifact_state: str='metadata_only', granted_purpose: str | None=None, privacy_class: str='none', artifact_sha: str='a' * 64) -> dict:
    permissions = {name: permission() for name in PURPOSES}
    if granted_purpose:
        permissions[granted_purpose] = permission('granted')
    external = artifact_state in {'external_available', 'revoked'}
    artifact = {'state': artifact_state, 'sha256': artifact_sha if external else None, 'byteSize': 1234 if external else None, 'storageLocator': f'custody:{opaque(20)}' if artifact_state == 'external_available' else None, 'custodyProfileId': f'policy:{opaque(21)}' if external else None, 'encryptionProfileId': f'policy:{opaque(22)}' if external else None, 'custodianId': f'actor.custodian:{opaque(23)}' if external else None}
    rights_approved = external
    rights_review = {'status': 'approved' if rights_approved else 'pending', 'verifiedBy': f'actor.rights:{opaque(30)}' if rights_approved else None, 'verifiedOn': '2026-08-01' if rights_approved else None, 'evidenceReference': f'evidence:{opaque(31)}' if rights_approved else None}
    if privacy_class == 'none':
        privacy = {'classification': 'none', 'reviewStatus': 'not_required', 'reviewedBy': None, 'reviewedOn': None, 'evidenceReference': None, 'deidentificationMethodCode': None, 'deidentifiedArtifactSha256': None}
    elif privacy_class == 'deidentified':
        privacy = {'classification': 'deidentified', 'reviewStatus': 'approved', 'reviewedBy': f'actor.privacy:{opaque(40)}', 'reviewedOn': '2026-08-01', 'evidenceReference': f'evidence:{opaque(41)}', 'deidentificationMethodCode': 'metadata_scrub', 'deidentifiedArtifactSha256': artifact_sha}
    else:
        privacy = {'classification': privacy_class, 'reviewStatus': 'approved', 'reviewedBy': f'actor.privacy:{opaque(40)}', 'reviewedOn': '2026-08-01', 'evidenceReference': f'evidence:{opaque(41)}', 'deidentificationMethodCode': None, 'deidentifiedArtifactSha256': None}
    retention = {'policy': 'delete_after_validation' if external else 'metadata_only', 'expiresOn': None, 'storageClass': 'custody_external' if external else 'not_assigned', 'deletionRequired': artifact_state == 'revoked', 'deletionStatus': 'completed' if artifact_state == 'revoked' else 'not_required', 'deletionReceiptReference': f'receipt:{opaque(50)}' if artifact_state == 'revoked' else None, 'deletionReceiptSha256': 'd' * 64 if artifact_state == 'revoked' else None}
    review_status = 'revoked' if artifact_state == 'revoked' else 'approved' if external else 'planned'
    completed = review_status in {'approved', 'revoked'}
    return {'datasetItemId': item_id, 'sourceFamilyId': family_id, 'parentItemId': None, 'artifact': artifact, 'provenance': {'sourceKind': source_kind, 'sourceReference': f'evidence:{opaque(60)}', 'rightsHolderId': f'subject:{opaque(61)}', 'licenseId': 'public-domain-1.0', 'usageBasisCode': 'synthetic_derivation' if source_kind == 'synthetic' else 'public_domain', 'rightsReview': rights_review}, 'privacy': privacy, 'input': {'kind': 'digital_pdf', 'mediaType': 'application/pdf', 'notationKinds': ['staff'], 'pageCount': 1, 'degradations': ['none']}, 'permissions': permissions, 'split': split, 'retention': retention, 'revocation': {'status': 'completed' if artifact_state == 'revoked' else 'not_revoked', 'effectiveOn': '2026-08-05' if artifact_state == 'revoked' else None, 'reference': f'evidence:{opaque(70)}' if artifact_state == 'revoked' else None}, 'syntheticGeneration': None, 'review': {'status': review_status, 'reviewedBy': f'actor.dataset:{opaque(80)}' if completed else None, 'reviewedOn': '2026-08-01' if completed else None, 'evidenceReference': f'evidence:{opaque(81)}' if completed else None, 'noteCodes': ['contract-test']}, 'assertions': {'teacherApprovalImpliedDatasetPermission': False, 'teacherApprovalImpliedTrainingPermission': False, 'originalBytesInGit': False, 'stage1TrainingExecutionAuthorized': False}}
