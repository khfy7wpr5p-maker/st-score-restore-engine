# Stage 1C Metadata-Only Onboarding Gate

**Status:** C1 pre-byte governance gate  
**Stage:** Stage 1C only  
**Parent issue:** #47  
**Artifact policy:** Metadata only in ordinary Git  
**Real-artifact onboarding status:** BLOCKED until the external custody environment passes the accepted Stage 1B operational controls

## 1. Purpose

This document defines the fail-closed checklist that must be satisfied before any Stage 1C item may move from repository-safe metadata planning toward real or controlled-synthetic artifact onboarding.

Passing this checklist does **not** make an artifact `external_available`, does not authorize bytes to be stored, does not create a storage resource, does not activate an item-level purpose grant, and does not complete Stage 1.

The checklist separates two boundaries that must not be conflated:

1. **repository metadata preparation**, which may occur with no artifact bytes; and
2. **external operational readiness**, which must be proven before the first artifact byte is admitted to custody.

Any unknown, missing, contradictory or stale condition is a gate failure.

## 2. Binding authority

This gate is subordinate to and must not weaken:

- `docs/roadmap.md`;
- `docs/stage-1a-dataset-governance-contract.md`;
- `docs/adr/0013-stage-1-entry-decision-record.md`;
- `docs/stage-1b-custody-operations-contract.md`;
- `docs/stage-1b-decision-hardening-record.md`;
- Issue #47 and its approved G4 purpose/storage binding.

The current G4 binding permits only:

- purpose: `quality_evaluation` or `held_out_evaluation`;
- environment: `stage1_offline`;
- storage class: `custody_external`;
- storage-location policy: a dedicated encrypted offline Stage 1 custody vault outside ordinary Git and automatic cloud-sync folders.

`model_training`, `publication`, `demonstration`, `quality_calibration`, `safety_calibration`, `pdf_pipeline_evaluation` and `synthetic_derivation` are not authorized by the current G4 decision.

## 3. C1 repository-safe metadata gate

A planned item may exist in ordinary Git only when all of the following are true.

### 3.1 Artifact state

The repository record remains `artifact.state = metadata_only`.

While that state is active, all byte/custody evidence fields remain `null`:

- `artifact.sha256`;
- `artifact.byteSize`;
- `artifact.storageLocator`;
- `artifact.custodyProfileId`;
- `artifact.encryptionProfileId`;
- `artifact.custodianId`.

A local path, provider URL, bucket/container name, account identifier, credential, secret, person name, email address, student identifier or teacher identifier must never be substituted for an opaque repository field.

### 3.2 Retention and storage state

For a metadata-only item:

- `retention.policy` is `metadata_only` or `prohibited`;
- `retention.storageClass = not_assigned`;
- `retention.deletionRequired = false`;
- `retention.deletionStatus = not_required`;
- deletion receipt reference and digest remain `null`.

Repository metadata must not claim that an external vault exists before the operational vault has actually passed its own acceptance gate.

### 3.3 Split and permissions

Before artifact availability:

- `split = unassigned`;
- no purpose permission may have `status = granted`;
- teacher approval must not imply dataset or training permission;
- Stage 1 training execution remains unauthorized.

Pending, denied, expired, withdrawn, not-requested or not-applicable permission states remain subject to the existing Stage 1A schema and validator rules. C1 creates no new permission state.

### 3.4 Rights, privacy, provenance and review planning

Metadata planning must use only the existing structured fields and opaque evidence/actor identifiers.

C1 does not waive the later requirement for:

- approved rights evidence;
- acceptable privacy review;
- approved dataset review;
- item-specific purpose authorization;
- retention policy;
- immutable artifact SHA-256 and exact byte size once bytes actually exist.

If any rights, privacy, provenance or review fact is unknown, it remains explicitly unresolved. It must not be guessed from document appearance, teacher approval or possession of the file.

### 3.5 Synthetic boundary

Because G4 does not authorize `synthetic_derivation`, C1 must not create or activate a controlled-synthetic onboarding path. Any future synthetic derivation requires a separate explicit governance decision before use.

## 4. External pre-byte operational gate

A metadata record passing Section 3 is **not sufficient** to admit bytes.

Before the first real or controlled-synthetic artifact byte is accepted into external custody, the selected custody environment must separately prove all applicable Stage 1B controls, including:

- supported and maintained host environment;
- dedicated encrypted storage outside ordinary Git and automatic cloud sync;
- private-by-default access;
- quarantine and isolated inspection with no outbound network access;
- immutable digest and exact-size binding;
- environment `stage1_offline` and storage class `custody_external`;
- active, non-conflicting real-person role mappings;
- durable audit-before-access behavior;
- retention enforcement;
- immediate revocation/deletion blocking;
- two-stage deletion evidence where required;
- backup tombstone and anti-resurrection controls;
- restore-time independent anti-rollback validation;
- crash/restart fail-closed behavior.

The currently inspected Windows 7 host did not pass this real-artifact operational gate. The local non-sensitive marker drill demonstrated only basic create/hash/delete/absence behavior and is not evidence that a compliant real-artifact vault exists.

Therefore the current real-artifact decision remains:

> **BLOCKED — no artifact byte may become `external_available` yet.**

## 5. Item-specific pre-admission conditions

Even after a compliant external vault is available, every item remains independently deny-by-default.

Before admission of a specific item, evidence must show at least:

- rights review is approved;
- privacy review is acceptable under the Stage 1A contract;
- dataset review is approved;
- requested purpose is exactly within the current G4 allowlist;
- the purpose authorization is item-specific, current and not revoked;
- restrictions are compatible with the intended split, `stage1_offline`, `custody_external` and retention limit;
- held-out items are isolated from tuning and development use;
- no prohibited Stage 1 purpose is activated;
- the custody/promotion operation can satisfy Stage 1B role-separation and audit requirements.

A failure in any one condition blocks admission.

## 6. Transition discipline

C1 does not define a new catalog state. The existing Stage 1A states remain authoritative:

```text
metadata_only -> external_available -> revoked
```

The transition to `external_available` may be recorded only after the actual bytes, digest, size, approved opaque custody references and operational evidence exist and the existing Stage 1A validators accept the resulting record.

Repository metadata must never be changed to `external_available` in anticipation of a future upload.

## 7. C1 decision table

| Condition | Result |
|---|---|
| Repository record satisfies Section 3, but external custody is unverified | Metadata planning allowed; artifact onboarding BLOCKED |
| Repository record violates Section 3 | BLOCKED |
| External custody fails any Stage 1B control | BLOCKED |
| Item-specific rights/privacy/review/purpose evidence is missing or invalid | BLOCKED |
| Purpose is outside the G4 allowlist | BLOCKED |
| Synthetic derivation is requested under current G4 | BLOCKED |
| All repository, operational and item-specific gates later pass | Eligible for a separately controlled onboarding operation; not automatic approval |

## 8. Zero-state assertion for C1

This C1 document itself:

- onboards **0** artifact bytes;
- creates **0** storage resources;
- creates **0** credentials or keys;
- activates **0** artifact-specific permissions;
- freezes **0** real dataset splits;
- authorizes **0** model-training, publication, demonstration, calibration, PDF-pipeline or synthetic-derivation uses;
- does not start Stage 2.

## 9. Verification boundary

C1 is documentation-only and changes no schema, validator, runtime, test fixture, workflow or dependency.

Repository CI must still pass on the exact pull-request head before this document can be merged. Ready-for-review and merge remain separate approval gates.
