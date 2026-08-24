# Stage 1C Metadata-Only Onboarding Gate

**Status:** C1 pre-byte governance gate, amended by accepted ADR 0016  
**Stage:** Stage 1C only  
**Parent issue:** #47  
**Artifact policy:** Metadata only in ordinary Git  
**Real-artifact onboarding status:** BLOCKED until the versioned storage-profile schema/validator migration is accepted and the exact artifact passes all applicable item/profile controls

## 1. Purpose

This document defines the fail-closed checklist that must be satisfied before any Stage 1C item may move from repository-safe metadata planning toward real or controlled-synthetic artifact onboarding.

Passing this checklist does **not** make an artifact `external_available`, does not authorize bytes to be stored, does not create a storage resource, does not activate an item-level purpose grant, and does not complete Stage 1.

The checklist separates three boundaries:

1. **repository metadata preparation**, which may occur with no artifact bytes;
2. **artifact eligibility and storage-profile selection**, which is defined by ADR 0016; and
3. **external operational readiness**, whose required controls depend on the selected profile.

Any unknown, missing, contradictory or stale condition is a gate failure.

## 2. Binding authority

This gate is subordinate to and must not weaken:

- `docs/roadmap.md`;
- `docs/stage-1a-dataset-governance-contract.md`;
- `docs/adr/0013-stage-1-entry-decision-record.md`;
- `docs/adr/0014-stage-1b-custody-operations-boundary.md` for high-assurance custody;
- `docs/adr/0016-stage-1c-risk-tiered-artifact-custody.md`;
- `docs/stage-1c-storage-profile-policy.md`;
- Issue #47 and the amended G4 binding.

The current G4 purpose allowlist remains:

- `quality_evaluation`;
- `held_out_evaluation`.

The universal storage rule is superseded by ADR 0016. The accepted architecture is:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when restrictions permit;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved, rejected, contradictory or expired governance → `blocked`.

`model_training`, `publication`, `demonstration`, `quality_calibration`, `safety_calibration`, `pdf_pipeline_evaluation` and `synthetic_derivation` remain unauthorized by the current Stage 1C decision.

## 3. C1 repository-safe metadata gate

A planned item may exist in ordinary Git only when all of the following are true.

### 3.1 Artifact state

The repository record remains `artifact.state = metadata_only`.

While that state is active, byte/custody evidence remains absent under the currently merged schema:

- `artifact.sha256`;
- `artifact.byteSize`;
- `artifact.storageLocator`;
- `artifact.custodyProfileId`;
- `artifact.encryptionProfileId`;
- `artifact.custodianId`.

A local path, provider URL, bucket/container name, account identifier, credential, secret, person name, email address, student identifier or teacher identifier must never be substituted for an opaque repository field.

### 3.2 Retention and storage state

For a metadata-only item under the current machine-readable schema:

- `retention.policy` is `metadata_only` or `prohibited`;
- `retention.storageClass = not_assigned`;
- `retention.deletionRequired = false`;
- `retention.deletionStatus = not_required`;
- deletion receipt reference and digest remain `null`.

Repository metadata must not claim a new ADR 0016 storage profile before the versioned schema/validator migration exists and validates that profile.

### 3.3 Split and permissions

Before artifact availability:

- `split = unassigned`;
- no purpose permission may have `status = granted` merely because metadata planning exists;
- teacher approval must not imply dataset or training permission;
- Stage 1 training execution remains unauthorized.

Pending, denied, expired, withdrawn, not-requested or not-applicable permission states remain subject to the existing Stage 1A schema and validator rules. C1 creates no new permission state.

### 3.4 Rights, privacy, provenance and review planning

Metadata planning must use only the existing structured fields and opaque evidence/actor identifiers.

C1 does not waive the later requirement for:

- approved exact-artifact rights evidence;
- acceptable privacy review;
- approved dataset review;
- item-specific purpose authorization;
- compatible retention policy;
- immutable artifact SHA-256 and exact byte size once bytes actually exist.

Public-domain status of the underlying composition alone is not sufficient. The exact edition, engraving, scan, photograph or acquired file must have evidence compatible with the intended purpose.

If any rights, privacy, provenance or review fact is unknown, it remains explicitly unresolved and the artifact is `blocked` at the ADR 0016 eligibility layer.

### 3.5 Synthetic boundary

Because the current Stage 1C purpose decision does not authorize `synthetic_derivation`, C1 must not create or activate a controlled-synthetic derivation path. Any future synthetic derivation requires a separate explicit governance decision before use.

## 4. Artifact eligibility and storage-profile gate

ADR 0016 requires deterministic classification before an artifact can be admitted:

### `open_corpus`

Requires exact-artifact rights compatible with the intended Stage 1 purpose, privacy `none`, approved dataset review, current purpose authorization, compatible retention, and no source/license restriction requiring stronger custody.

Only `managed_standard` is the normal profile for this class.

### `restricted_corpus`

Requires lawful use for the intended purpose but has license, donor, access, redistribution, retention or similar restrictions. The selected environment/provider must satisfy those restrictions.

Only `managed_restricted` is the normal profile unless an artifact-specific policy requires escalation to high assurance.

### `sensitive_custody`

Required for private/user-provided, personal/student, consent-restricted or policy-designated sensitive material.

This class requires `high_assurance_vault` and the accepted Stage 1B/C4 high-assurance controls.

### `blocked`

Missing, pending, rejected, expired or contradictory rights/privacy/review/purpose/provenance/retention state produces `blocked`. A blocked artifact has no eligible storage profile and cannot become `external_available`.

## 5. Current machine-readable migration hold

ADR 0016 is accepted on `main`, but the current Stage 1A/1C machine-readable contract still represents legacy storage values.

Therefore the current real-artifact decision remains:

> **BLOCKED — no artifact may become `external_available` under an ADR 0016 storage profile until the versioned storage-profile schema/validator migration is merged and verified.**

The migration must be additive and fail closed. It must not silently reinterpret an existing `custody_external` record as `managed_standard` or otherwise lower a previously recorded security state.

## 6. External operational gate after the migration

Once the machine-readable profile migration exists, the selected profile determines the required operational evidence.

### `managed_standard`

At minimum:

- artifact bytes outside ordinary Git;
- exact SHA-256 and byte-size binding;
- exact-artifact rights evidence;
- privacy `none`;
- approved dataset review and allowed purpose;
- documented retention/deletion behavior;
- protection against accidental public sharing for project-managed private copies;
- encryption in transit and at rest for non-public managed copies;
- known backup/version behavior sufficient to prevent silent corpus drift;
- no provider/account/path/credential leakage into ordinary Git.

A managed cloud/file service or local managed store may qualify if its actual configuration satisfies these controls. No provider is approved merely by brand.

### `managed_restricted`

Requires all applicable `managed_standard` controls plus:

- provider/environment compatibility with binding artifact restrictions;
- deny-by-default project membership;
- no public-link sharing;
- access/change history where available;
- restriction-compatible retention, deletion and backup behavior;
- matching environment/storage allowlists when present.

### `high_assurance_vault`

Requires the accepted Stage 1B/C4 controls, including supported host, encryption, least privilege, role separation, quarantine isolation, audit integrity/anti-rollback, retention enforcement, immediate revocation, deletion evidence, backup anti-resurrection and Git/sync separation.

The prior Windows 7 assessment remains relevant only to a proposed `high_assurance_vault` on that host. It does not block a verified `open_corpus` artifact from later using a valid `managed_standard` profile.

## 7. Item-specific pre-admission conditions

Even after the schema migration and a compatible storage environment exist, every item remains independently deny-by-default.

Before admission of a specific item, evidence must show at least:

- exact-artifact rights review is approved;
- privacy review is acceptable under the Stage 1A contract;
- dataset review is approved;
- requested purpose is exactly within the Stage 1C allowlist;
- purpose authorization is item-specific, current and not revoked;
- retention and restrictions are compatible with the selected storage profile;
- the selected eligibility class/profile pairing is legal;
- held-out items are isolated from tuning and development use;
- no prohibited Stage 1 purpose is activated.

A failure in any one condition blocks admission.

## 8. Transition discipline

C1 does not define a new artifact-state transition. The existing Stage 1A states remain authoritative until a separately versioned migration changes them:

```text
metadata_only -> external_available -> revoked
```

The transition to `external_available` may be recorded only after actual bytes, digest, size, approved opaque storage/custody references, applicable operational evidence and all item-level authorizations exist, and the then-current validators accept the resulting record.

Repository metadata must never be changed to `external_available` in anticipation of a future upload.

## 9. Decision table

| Condition | Result |
|---|---|
| Repository metadata is valid but ADR 0016 machine-readable profile migration is not merged | Metadata planning allowed; artifact onboarding BLOCKED |
| Exact-artifact rights/privacy/review/purpose/provenance is unresolved | `blocked`; artifact onboarding BLOCKED |
| `open_corpus` + verified compatible `managed_standard` controls after migration | Eligible for a separately controlled onboarding operation |
| `restricted_corpus` + incompatible provider/restriction | BLOCKED |
| `sensitive_custody` without passing high-assurance Stage 1B/C4 evidence | BLOCKED |
| Purpose outside the current Stage 1C allowlist | BLOCKED |
| Synthetic derivation requested under the current decision | BLOCKED |
| All repository, profile, operational and item-specific gates pass | Eligible for controlled onboarding; never automatic approval |

## 10. Zero-state assertion

This amended C1 document itself:

- onboards **0** artifact bytes;
- creates **0** storage resources;
- creates **0** credentials or keys;
- activates **0** artifact-specific permissions;
- freezes **0** real dataset splits;
- authorizes **0** model-training, publication, demonstration, calibration, PDF-pipeline or synthetic-derivation uses;
- does not start Stage 2.

## 11. Verification boundary

This C5 status-convergence revision is documentation/governance only. It changes no schema, validator, runtime, test fixture, workflow or dependency.

Repository CI must pass on the exact pull-request head before the revision can be treated as ready. The separate Ready-for-review and merge gates remain binding.