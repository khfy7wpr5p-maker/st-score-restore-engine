# Stage 1A Dataset Governance and Metadata Contract

**Status:** Accepted and merged Stage 1A governance baseline  
**Issue:** #32  
**Schema version:** `1.2.0`  
**Entry decision:** `adr-0013-stage-1-entry-v1`  
**Artifact policy:** Metadata only  
**Runtime restoration impact:** None  
**Current substage state:** Stage 1A complete; Stage 1B formally closed; Stage 1C active under Issue #47; ADR 0016 introduces risk-tiered custody architecture, with machine-readable profile implementation still pending

## 1. Scope

Stage 1A defines the fail-closed metadata and validation boundary required
before any real-data onboarding. It did not collect document bytes, select a
storage provider, freeze a real split, run training, tune thresholds, start
Stage 1B/1C/2 or add restoration engines.

The existing fixture catalog remains the regression-fixture planning contract.
The Stage 1A dataset contract separately models custody references, purpose
authorization, source-family isolation, frozen snapshots, privacy and
revocation.

## 2. Bound purposes

All purposes are independent and deny-by-default:

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

A granted permission carries an opaque authorization reference, a
purpose-authorizer ID, authorization date, optional expiry and typed
restrictions. Snapshot inclusion requires a split-relevant permission that is
valid on the snapshot date. Expiry is fail-closed.

Teacher approval creates none of these permissions. Stage 1 records future
training eligibility but cannot authorize training execution.

## 3. Opaque identity and evidence

Git metadata accepts role-scoped opaque identifiers with the exact suffix
`opq_<32 lowercase hex>`:

- rights verifier: `actor.rights:opq_...`
- privacy reviewer: `actor.privacy:opq_...`
- purpose authorizer: `actor.purpose:opq_...`
- dataset reviewer: `actor.dataset:opq_...`
- custodian: `actor.custodian:opq_...`
- rights subject: `subject:opq_...`
- evidence: `evidence:opq_...`
- policy: `policy:opq_...`
- custody locator: `custody:opq_...`
- deletion receipt: `receipt:opq_...`

Semantic aliases such as person names, email addresses, student identifiers or
personal paths are invalid. Catalog description and license fields are
restricted code values. Synthetic parameter objects cannot contain strings.
Stage 1B subsequently defined and tested the provider-neutral external-identity
and real-person role-conflict boundary. Production identity implementation
remains deferred to Stage 6.

## 4. Artifact and custody states

- `metadata_only`: no digest, bytes or custody reference
- `external_available`: digest, byte size, opaque locator, custody policy,
  encryption policy and custodian required
- `revoked`: historical digest/policies remain; active locator is absent and a
  completed deletion receipt is required

Ordinary Git remains metadata-only. No credentials, personal names or personal
paths are valid custody or identity fields.

The schema version described by this document still exposes the original
Stage 1A storage vocabulary. ADR 0016 changes the architecture before the
machine-readable contract: no item may use a new custody-profile name until a
follow-up versioned schema/validator change is merged and verified.

## 5. Rights, privacy and review

An external or actively authorized item requires approved rights review,
acceptable privacy review, approved dataset review, immutable artifact SHA-256
and external custody metadata.

Rights review applies to the exact artifact used by the project. The fact that
a musical composition is public domain does not by itself establish that a
particular modern edition, engraving, editorial layer, scan, photograph or
acquired file is public domain or freely reusable.

For `deidentified` data, the privacy-reviewed derivative SHA-256 must equal the
artifact SHA-256 used in the dataset. Identifiable personal/student data cannot
be trained, published, demonstrated or used for synthetic derivation.

## 6. Source families and synthetic lineage

Every source and derivative shares one `sourceFamilyId` and one assigned split.
A synthetic child must exactly equal its parent's non-`unassigned` split.

A synthetic item requires an approved, available, non-synthetic parent; a
synthetic-derivation authorization valid on `generatedOn`; matching
authorization reference; generator name, semantic version, commit SHA-256,
seed and non-text parameter values. Synthetic-on-synthetic derivation is
rejected. Child retention cannot exceed parent retention.

## 7. Split policy

- `unassigned`: no active purpose
- `development`: fixture, quality-evaluation and PDF-pipeline evaluation
- `calibration`: quality and safety calibration
- `held_out`: held-out evaluation only
- `training_reserved`: future model-training eligibility only

Held-out and training-reserved items cannot enable active synthetic derivation.
Stage 1A snapshots keep `trainingUseActivated=false`.

## 8. Typed restrictions

Supported restrictions are `split_allowlist`, `storage_class_allowlist`,
`environment_allowlist`, `external_export` and `retention_not_after`.
Unknown or contradictory restrictions fail closed. The current schema version
still uses the legacy Stage 1 snapshot environment `stage1_offline`; ADR 0016
requires a versioned follow-up before additional managed-storage environments
can be represented.

## 9. Revocation and deletion evidence

Revoked items cannot appear in snapshots. Their active locator is removed.
Completed revocation requires a revocation date and opaque evidence reference,
`deletionStatus=completed`, an opaque deletion receipt reference and deletion
receipt SHA-256. The provider-neutral operational deletion/revocation drill was
completed under Stage 1B and remains binding evidence for high-assurance
onboarding and for any lower-tier profile that explicitly adopts those controls.

## 10. Snapshot integrity and authorization

A snapshot binds ADR 0013, catalog and item canonical SHA-256 values, source
family and split, a valid UTC creation timestamp, held-out freeze state,
revoked-item tombstones, separate real/synthetic counts and approved opaque
review evidence.

`validate_dataset_snapshot` is the only public safe boundary. It includes
integrity, split-purpose, temporal and restriction checks. The compatibility
wrapper delegates to it.

## 11. Schema parity

CI uses the exact offline Draft 2020-12 validation stack in
`requirements.validation.lock`. It validates the schemas themselves, executes
shared instances through JSON Schema and Python, and compares all versions,
required fields, enums, constants and patterns. Structural invalid data must be
rejected by both engines; semantic invalid data may pass JSON Schema but must be
rejected by Python.

## 12. Repository example

`examples/dataset-catalog.metadata-only.v1.json` contains no artifact bytes,
digest, locator, active permission, assigned split or completed review. It is
not a dataset and cannot satisfy the Stage 1 exit gate.

## 13. Validation

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python tools/validate_dataset_manifest.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

## 14. Current Stage 1C boundary

Stage 1B's provider-neutral high-assurance custody, encryption, identity, audit,
revocation, deletion and restore contract is complete and formally closed.
Stage 1C received separate start authorization under Issue #47.

The earlier G4 pre-byte decision bound all real/controlled-synthetic artifacts
to one `stage1_offline` / `custody_external` encrypted offline vault. ADR 0016
supersedes **that universal storage-location rule** with artifact-specific risk
tiers while retaining G4's purpose allowlist and all independent Stage 1A
governance gates.

The approved architecture now distinguishes:

- `open_corpus` → `managed_standard` after exact-artifact rights, privacy,
  purpose, retention and dataset-review approval;
- `restricted_corpus` → `managed_restricted` only when artifact-specific terms
  allow the selected provider/environment;
- `sensitive_custody` → `high_assurance_vault`, using the accepted Stage 1B
  boundary and C4 vault-verification evidence;
- `blocked` → no onboarding when rights/privacy/purpose/review/provenance is
  missing, pending, rejected, expired or contradictory.

This architecture change does not itself activate those new profile names in
the current `1.2.0` schema. Until a separately verified schema/validator
migration is merged, current validators remain authoritative and no new
artifact may become `external_available` under `managed_standard` or
`managed_restricted`.

G4's purpose allowlist remains `quality_evaluation` and
`held_out_evaluation`. `model_training`, publication, demonstration,
calibration, PDF-pipeline evaluation and synthetic derivation remain
authorized only by separate future decisions in the correct roadmap stage.

Provider-specific production identity, network, secret-management, encrypted
production storage, production database/queue and deployment controls remain
Stage 6 work. This status convergence changes no restoration runtime behavior
and does not onboard artifact bytes.