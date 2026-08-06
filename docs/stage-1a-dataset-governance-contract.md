# Stage 1A Dataset Governance and Metadata Contract

**Status:** Draft implementation in PR #35  
**Issue:** #32  
**Schema version:** `1.1.0`  
**Entry decision:** `adr-0013-stage-1-entry-v1`  
**Artifact policy:** Metadata only  
**Runtime restoration impact:** None

## 1. Scope

Stage 1A defines the fail-closed metadata and validation boundary required
before any real-data onboarding. It does not collect document bytes, select a
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

Git metadata accepts role-scoped opaque identifiers only:

- rights verifier: `actor.rights:*`
- privacy reviewer: `actor.privacy:*`
- purpose authorizer: `actor.purpose:*`
- dataset reviewer: `actor.dataset:*`
- custodian: `actor.custodian:*`
- rights subject: `subject:*`
- evidence: `evidence:*`
- policy: `policy:*`
- custody locator: `custody:*`
- deletion receipt: `receipt:*`

The external identity registry and real-person role-conflict checks remain
Stage 1B work.

## 4. Artifact and custody states

- `metadata_only`: no digest, bytes or custody reference
- `external_available`: digest, byte size, opaque locator, custody policy,
  encryption policy and custodian required
- `revoked`: historical digest/policies remain; active locator is absent and a
  completed deletion receipt is required

Ordinary Git remains metadata-only. No credentials, personal names or personal
paths are valid custody or identity fields.

## 5. Rights, privacy and review

An external or actively authorized item requires:

- approved rights review,
- acceptable privacy review,
- approved dataset review,
- immutable artifact SHA-256,
- external custody metadata.

For `deidentified` data, the privacy-reviewed derivative SHA-256 must equal the
artifact SHA-256 used in the dataset. Identifiable personal/student data cannot
be trained, published, demonstrated or used for synthetic derivation.

## 6. Source families and synthetic lineage

Every source and derivative shares one `sourceFamilyId` and one assigned split.

A synthetic item requires an approved, available, non-synthetic parent; a
synthetic-derivation authorization valid on `generatedOn`; matching
authorization reference; generator name, semantic version, commit SHA-256,
seed and parameters. Synthetic-on-synthetic derivation is rejected. Child
retention cannot exceed parent retention.

## 7. Split policy

- `unassigned`: no active purpose
- `development`: fixture, quality-evaluation and PDF-pipeline evaluation
- `calibration`: quality and safety calibration
- `held_out`: held-out evaluation only
- `training_reserved`: future model-training eligibility only

Held-out and training-reserved items cannot enable active synthetic derivation.
Stage 1A snapshots keep `trainingUseActivated=false`.

## 8. Typed restrictions

Supported restrictions are:

- `split_allowlist`
- `storage_class_allowlist`
- `environment_allowlist`
- `external_export`
- `retention_not_after`

Unknown or contradictory restrictions fail closed. The Stage 1 snapshot
environment is `stage1_offline`.

## 9. Revocation and deletion evidence

Revoked items cannot appear in snapshots. Their active locator is removed.
Completed revocation requires:

- revocation date and opaque evidence reference,
- `deletionStatus=completed`,
- opaque deletion receipt reference,
- deletion receipt SHA-256.

The operational deletion drill across storage and backups remains Stage 1B.

## 10. Snapshot integrity and authorization

A snapshot binds:

- ADR 0013 decision ID,
- catalog canonical SHA-256,
- each item canonical SHA-256,
- source family and split,
- UTC creation time and environment,
- held-out freeze state,
- revoked-item tombstones,
- separate real/synthetic counts,
- approved opaque dataset-review evidence.

`validate_dataset_snapshot` is the only public safe boundary. It includes
integrity, split-purpose, temporal and restriction checks. The compatibility
wrapper delegates to it.

## 11. Schema parity

CI compares JSON Schema and Python constants for versions, entry decision,
required fields, purpose/state enums, split/source/privacy values, typed
restriction kinds and opaque-ID patterns. Drift fails repository validation.
Cross-field and temporal rules remain Python responsibilities.

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

## 14. Deferred work

Stage 1B must separately select and approve storage, encryption/key ownership,
IAM, external identity registry, audit and deletion operations. Stage 1C must
separately authorize real and controlled-synthetic onboarding, split freeze,
dataset card, bias/coverage evidence and Stage 1 exit acceptance.
