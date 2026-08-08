# Stage 1A Dataset Governance and Metadata Contract

**Status:** Accepted and merged Stage 1A governance baseline  
**Issue:** #32  
**Schema version:** `1.2.0`  
**Entry decision:** `adr-0013-stage-1-entry-v1`  
**Artifact policy:** Metadata only  
**Runtime restoration impact:** None  
**Current substage state:** Stage 1A complete; Stage 1B formally closed; Stage 1C active under Issue #47; G4 purpose/storage policy binding complete; real artifact onboarding blocked pending compliant vault verification

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

## 5. Rights, privacy and review

An external or actively authorized item requires approved rights review,
acceptable privacy review, approved dataset review, immutable artifact SHA-256
and external custody metadata.

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
Unknown or contradictory restrictions fail closed. The Stage 1 snapshot
environment is `stage1_offline`.

## 9. Revocation and deletion evidence

Revoked items cannot appear in snapshots. Their active locator is removed.
Completed revocation requires a revocation date and opaque evidence reference,
`deletionStatus=completed`, an opaque deletion receipt reference and deletion
receipt SHA-256. The provider-neutral operational deletion/revocation drill was
completed under Stage 1B and remains binding evidence for later onboarding.

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

Stage 1B's provider-neutral custody, encryption, identity, audit, revocation,
deletion and restore contract is complete and formally closed. Stage 1C received
separate start authorization under Issue #47. G4 separately bound the current
Stage 1 purpose allowlist to `quality_evaluation` and `held_out_evaluation`, the
environment to `stage1_offline`, the storage class to `custody_external`, and
the storage-location policy to a dedicated encrypted offline Stage 1 custody
vault outside ordinary Git and automatic cloud-sync folders.

G4 does not create artifact-specific permissions. Rights, privacy, dataset
review and purpose authorization remain independent and deny-by-default for
every item. `model_training`, publication, demonstration, calibration,
PDF-pipeline evaluation and synthetic derivation remain unauthorized by the G4
binding.

A local host/vault assessment (V2) found the currently inspected Windows 7 host
unsuitable for real/private artifact custody because the operating system is
unsupported and its inspected disks are unencrypted. A separate local
non-sensitive basic marker drill (V3) demonstrated create/size/SHA-256/delete
and post-delete absence for a project-authored non-musical marker. These are
local terminal observations only: they are not GitHub-hosted CI evidence and V3
does not prove a Stage 1B-compliant real artifact vault.

Real or controlled-synthetic artifact onboarding therefore remains blocked
until a supported, encrypted custody environment passes the required
operational controls, including the Stage 1B access, audit, revocation,
deletion, backup/restore anti-resurrection and real-person role-separation
boundaries. Artifact bytes onboarded through this status convergence remain
zero.

Provider-specific production identity, network, secret-management, encrypted
production storage, production database/queue and deployment controls remain
Stage 6 work. This status convergence changes no schema, validator, runtime
behavior, item-level permission or artifact state.