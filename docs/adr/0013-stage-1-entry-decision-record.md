# ADR 0013: Stage 1 Entry Decision Record

- **Status:** Accepted for Stage 1A contract hardening
- **Date:** 2026-08-06
- **Decision ID:** `adr-0013-stage-1-entry-v1`
- **Roadmap stage:** Stage 1 only
- **Issue:** #32
- **Pull request:** #35 remains draft
- **Dataset schema version:** `1.2.0`

## Context

Roadmap v0.2 requires a rights-cleared, privacy-reviewed, purpose-bound and
Git-external dataset before Stage 2 quality analysis, Stage 3 PDF processing or
Stage 4 safety calibration. ADR 0012 accepted a separate dataset-governance
contract, but deliberately deferred the Stage 1 entry decisions for custody,
role separation, time-bound authorization, restrictions, deletion evidence and
real/synthetic handling.

This record binds those decisions without selecting a storage product,
onboarding document bytes, freezing a real split, activating model training or
starting Stage 1B, Stage 1C or Stage 2.

## Decisions

### Purposes

Every purpose is independent and deny-by-default:

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

`model_training` may be recorded only as future eligibility. Stage 1 does not
authorize training execution. Teacher approval implies no dataset, derivation
or training permission.

### Prohibited Stage 1 uses

Stage 1 prohibits model training, held-out tuning, production-upload
collection, automatic consent inference, Git storage of document bytes,
unapproved synthetic derivation, DocRes, multi-engine comparison, selector or
image-model work, and music-application repository changes.

### Custody and encryption boundary

Document bytes remain outside ordinary Git. Any future external artifact must
reference opaque custody, encryption-policy and custodian identifiers. Storage
must be private-by-default, encrypted in transit and at rest, audit logged,
backup-aware and able to propagate deletion. Held-out access must be narrower
than development access. The storage product, region, KMS/HSM and key rotation
period remain Stage 1B decisions.

### Role separation and opaque identity

Repository identity and evidence fields use role-scoped, non-semantic tokens:

- `actor.rights:opq_<32 lowercase hex>`
- `actor.privacy:opq_<32 lowercase hex>`
- `actor.purpose:opq_<32 lowercase hex>`
- `actor.dataset:opq_<32 lowercase hex>`
- `actor.custodian:opq_<32 lowercase hex>`
- `subject:opq_<32 lowercase hex>`
- `evidence:opq_<32 lowercase hex>`
- `policy:opq_<32 lowercase hex>`
- `custody:opq_<32 lowercase hex>`
- `receipt:opq_<32 lowercase hex>`

Names, personal email addresses, phone numbers, student/teacher identities,
personal paths and semantic identity aliases are invalid in those fields.
Catalog descriptions and license values are code fields, not free text.
Synthetic generator parameters cannot contain strings. The external identity
registry must enforce real-person conflict checks between rights verifier,
privacy reviewer, custodian, purpose authorizer and dataset reviewer.

### Split policy

- `development`: fixture, quality-evaluation and PDF-pipeline evaluation
- `calibration`: quality and safety calibration
- `held_out`: held-out evaluation only; no tuning
- `training_reserved`: future model-training eligibility only

All originals and derivatives in one source family remain in one assigned
split. A synthetic child must equal its parent's non-`unassigned` split. Split
changes require a new catalog/snapshot version. Held-out freeze and access
separation are mandatory before Stage 1 exit.

### Temporal authorization and restrictions

A snapshot assignment is valid only when at least one split-relevant permission
is `granted`, was authorized on or before the snapshot date, has not expired and
has not been revoked. Expiry is fail-closed: `snapshotDate < expiresOn`.

Restrictions are typed and machine-enforced. Unknown or unenforceable
restriction forms are rejected. Stage 1A supports split, storage-class and
environment allowlists, external-export control and retention upper bounds.

### Privacy and de-identification

A de-identified item must bind the privacy-reviewed derivative digest to the
artifact digest used by the dataset. Identifiable personal or student data
cannot be trained, published, demonstrated or used as a synthetic parent.

### Synthetic derivation

A synthetic item must use an available, rights/privacy/dataset-approved
non-synthetic parent in the same source family and assigned split. The parent
must have a synthetic-derivation authorization valid at generation time.
Generator version, commit, date, authorization reference, seed and numeric or
boolean parameter values are immutable lineage evidence. Synthetic-on-synthetic
derivation is rejected.

### Retention, revocation and deletion

Revoked items retain historical digest and policy evidence but no active
storage locator. Completed revocation requires an opaque deletion receipt
reference and receipt digest. Stage 1B must demonstrate deletion across primary,
replica, cache and backup boundaries before Stage 1C may start.

### Schema and validator parity

JSON Schema Draft 2020-12 is the structural contract. The exact
`jsonschema==4.26.0` validation stack is test-only and offline. Python enforces
cross-field, temporal, role, restriction, lineage and snapshot rules. CI must:

1. validate both schemas with `Draft202012Validator.check_schema`,
2. compare all contract versions, required fields, enums, constants and patterns
   with Python constants,
3. run shared valid, structural-invalid and semantic-invalid examples through
   the JSON Schema and Python validators,
4. fail on drift, including timestamp patterns and opaque-ID formats.

### Only safe snapshot boundary

`validate_dataset_snapshot` is the public fail-closed boundary. It includes
integrity, purpose, temporal and restriction checks. Any lower-level integrity
helper remains private. Compatibility wrappers delegate to the same boundary.

## Stage boundaries

### Stage 1A

Schema, metadata, ADRs, validators and tests only. No document bytes, storage
account, active repository permission, real split freeze or model execution.

### Stage 1B

Storage selection, encryption/key ownership, IAM, external identity registry,
audit, quarantine, deletion and revocation drills using non-sensitive objects.
Requires separate start approval.

### Stage 1C

Rights/privacy-approved real onboarding, controlled synthetic derivation,
purpose activation, split freeze, dataset card, bias/coverage report and Stage 1
exit evidence. Requires Stage 1B operational evidence and separate start
approval.

Stage 2 remains blocked until Stage 1 exit evidence is separately accepted.

## Consequences

PR #35 may harden the Stage 1A contract to implement this record. It must remain
draft until a separate ready-for-review approval. No merge is authorized by
this ADR.
