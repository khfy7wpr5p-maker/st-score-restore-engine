# Stage 1A Dataset Governance and Metadata Contract

**Status:** Accepted Stage 1A baseline extended by Stage 1C C6 profile contract  
**Issue:** #32 / Stage 1C #47  
**Catalog schema version:** `1.3.0`  
**Snapshot schema version:** `1.2.0`  
**Entry decision:** `adr-0013-stage-1-entry-v1`  
**Custody decision:** `adr-0016-stage-1c-risk-tiered-custody-v1`  
**Artifact policy:** real corpus bytes remain outside ordinary Git  
**Runtime restoration impact:** None

## 1. Scope

Stage 1A established the fail-closed dataset metadata boundary. Stage 1C C6
extends that machine-readable catalog contract so ADR 0016 eligibility classes
and storage profiles can be represented and validated without weakening rights,
privacy, purpose, retention, split-isolation or revocation controls.

C6 does not collect document bytes, approve a provider, authorize an artifact,
freeze a real split, run training, tune thresholds, or start Stage 2.

## 2. Bound purposes

All purposes remain independent and deny-by-default:

- `fixture_validation`
- `quality_evaluation`
- `quality_calibration`
- `pdf_pipeline_evaluation`
- `safety_calibration`
- `held_out_evaluation`
- `synthetic_derivation`
- `model_training`
- `publication`
- `demonstration`

Stage 1C's currently approved purpose allowlist remains only
`quality_evaluation` and `held_out_evaluation`. The existence of other schema
fields records future governance possibilities; it does not activate them.
Teacher approval creates no dataset or training permission.

## 3. Opaque identity and evidence

Repository metadata accepts role-scoped opaque identifiers with the exact
suffix `opq_<32 lowercase hex>`:

- rights verifier: `actor.rights:opq_...`
- privacy reviewer: `actor.privacy:opq_...`
- purpose authorizer: `actor.purpose:opq_...`
- dataset reviewer: `actor.dataset:opq_...`
- custodian: `actor.custodian:opq_...`
- rights subject: `subject:opq_...`
- evidence: `evidence:opq_...`
- policy: `policy:opq_...`
- custody/storage locator: `custody:opq_...`
- deletion receipt: `receipt:opq_...`

Person names, email addresses, student identifiers, provider URLs, account IDs,
credentials, secrets and local filesystem paths are not valid substitutes.

## 4. Artifact state and eligibility

Artifact states remain:

- `metadata_only`: no digest, byte-size or active storage/custody reference;
- `external_available`: immutable digest/size plus opaque storage-policy evidence;
- `revoked`: historical digest/policy evidence remains, active locator is absent,
  and completed deletion evidence is required.

Catalog `1.3.0` adds exactly one `eligibilityClass` per item:

- `blocked`
- `open_corpus`
- `restricted_corpus`
- `sensitive_custody`

`metadata_only` items remain `blocked`. C6 does not infer a lower-risk class from
composer age, source label, possession of a file or an old custody record.

## 5. Storage profiles

`retention.storageClass` remains the machine field name for compatibility, but
in catalog `1.3.0` its external values are ADR 0016 storage profiles:

- `managed_standard`
- `managed_restricted`
- `high_assurance_vault`

`not_assigned` remains valid only where no external profile is active.

The validator enforces:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted`;
- `sensitive_custody` → `high_assurance_vault`;
- `blocked` → no external storage profile / no external availability.

`open_corpus` requires privacy classification `none`. Personal or student data
requires `sensitive_custody`. Unknown or contradictory governance never falls
back to a weaker profile.

The existing opaque `artifact.storageLocator` field is provider-neutral. It does
not expose a Google Drive URL, local path, bucket name, account ID or credential.

## 6. Legacy migration rule

Catalog `1.2.0` used the universal `custody_external` storage value. C6 provides
a deterministic migration boundary from `1.2.0` to `1.3.0` with one critical
anti-downgrade invariant:

- legacy `metadata_only` / `not_assigned` → `blocked` / `not_assigned`;
- legacy external or revoked `custody_external` → `sensitive_custody` /
  `high_assurance_vault`;
- legacy `storage_class_allowlist=[custody_external]` →
  `storage_class_allowlist=[high_assurance_vault]`.

The migration never infers `open_corpus`, `restricted_corpus`,
`managed_standard` or `managed_restricted`. Reclassification to those lower
profiles requires current evidence and the later eligibility/operational gates.
Malformed or unexpected legacy storage state is rejected rather than guessed.

## 7. Rights, privacy and review

An external or actively authorized item requires approved exact-artifact rights
review, acceptable privacy review, approved dataset review, immutable artifact
SHA-256 and external storage metadata.

Public-domain status of the underlying composition does not itself establish
rights for a modern edition, engraving, editorial layer, scan, photograph or
acquired file.

For `deidentified` data, the reviewed derivative SHA-256 must equal the artifact
SHA-256 used in the dataset. Identifiable personal/student data cannot be
trained, published, demonstrated or used for synthetic derivation.

## 8. Source families and synthetic lineage

Every source and derivative shares one `sourceFamilyId` and one assigned split.
A synthetic child must share its parent's non-`unassigned` split.

Synthetic derivation requires a valid purpose grant, approved available parent,
authorization reference, generator/version/commit, generation date, seed and
non-text parameters. Synthetic-on-synthetic derivation is rejected and child
retention cannot exceed parent retention.

Current Stage 1C governance still does not authorize synthetic derivation.

## 9. Split policy

- `unassigned`: no active purpose
- `development`: fixture, quality-evaluation and PDF-pipeline evaluation schema capability
- `calibration`: quality and safety calibration schema capability
- `held_out`: held-out evaluation only
- `training_reserved`: future model-training eligibility only

Held-out and training-reserved items cannot enable active synthetic derivation.
Stage 1 snapshots keep `trainingUseActivated=false`.

## 10. Typed restrictions

Supported restrictions remain `split_allowlist`, `storage_class_allowlist`,
`environment_allowlist`, `external_export` and `retention_not_after`.

For catalog `1.3.0`, `storage_class_allowlist` values are restricted to
`managed_standard`, `managed_restricted` and `high_assurance_vault`.

The snapshot `environment=stage1_offline` remains the bounded Stage 1 evaluation
execution environment. It no longer acts as a universal storage-location rule:
a `managed_standard` or `managed_restricted` artifact may reside in an approved
managed store while evaluation remains inside the bounded Stage 1 environment.
Unknown or contradictory restrictions fail closed.

## 11. Revocation and deletion evidence

Revoked items cannot appear in snapshots. Their active locator is removed.
Completed revocation requires a revocation date and opaque evidence reference,
`deletionStatus=completed`, an opaque deletion receipt reference and deletion
receipt SHA-256.

Stage 1B/C4 operational evidence remains mandatory for
`high_assurance_vault`. Lower profiles must satisfy their own operational
verification contracts; C6 does not claim those checks have passed.

## 12. Snapshot integrity and authorization

A snapshot binds ADR 0013, catalog and item canonical SHA-256 values, source
family and split, UTC creation time, held-out freeze state, revoked-item set,
coverage counts and approved opaque review evidence.

`validate_dataset_snapshot` remains the public safe boundary. Catalog version
`1.3.0` changes item metadata and therefore changes the canonical catalog/item
digests naturally; snapshot schema shape remains `1.2.0`.

## 13. Schema parity

CI validates the Draft 2020-12 schemas and Python contract together. Parity now
covers the `eligibilityClass` enum, profile-valued `storageClass`, storage
restriction values, all prior required fields/enums/constants/patterns and the
closed-object invariant. Structural invalid data must fail JSON Schema and
Python; semantic illegal class/profile combinations fail Python.

## 14. Repository example and validation

`examples/dataset-catalog.metadata-only.v1.json` is catalog `1.3.0`, contains
`eligibilityClass=blocked`, and contains no artifact bytes, digest, locator,
active permission, assigned split or completed review.

Validate with:

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python tools/validate_dataset_manifest.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## 15. Current Stage 1C boundary after C6

C6 makes the ADR 0016 classes/profiles machine-readable and adds conservative
legacy migration. It does **not** make any real artifact automatically eligible
or available.

The next planned slices remain:

1. C7 deterministic evidence-derived eligibility resolver;
2. C8 `managed_standard` operational verification;
3. C9 `managed_restricted` operational verification;
4. C10 high-assurance compatibility verification.

Until the relevant item evidence and profile verification pass, artifact
onboarding remains fail-closed. Stage 2 remains blocked until the complete
Stage 1 corpus exit gate is accepted.
