# Stage 1C Metadata-Only Onboarding Gate

**Status:** C1 pre-byte governance gate, amended by ADR 0016 and C6 catalog `1.3.0`  
**Stage:** Stage 1C only  
**Parent issue:** #47  
**Artifact policy:** real corpus bytes remain outside ordinary Git  
**Real-artifact onboarding status:** BLOCKED pending evidence-derived eligibility and applicable operational profile verification

## 1. Purpose

This document defines the fail-closed boundary between repository-safe metadata planning and real artifact onboarding.

C6 makes ADR 0016 eligibility classes and storage profiles machine-readable. That change is necessary but not sufficient to make an artifact `external_available`. No schema value can create rights, privacy approval, purpose permission or operational storage evidence.

The gate separates:

1. repository metadata preparation;
2. evidence-derived artifact eligibility;
3. storage-profile selection;
4. operational profile verification; and
5. the controlled transition to `external_available`.

Unknown, missing, contradictory or stale evidence fails closed.

## 2. Binding authority

This gate is subordinate to:

- `docs/roadmap.md`;
- `docs/stage-1a-dataset-governance-contract.md`;
- ADR 0013;
- ADR 0014 for high-assurance custody;
- accepted ADR 0016;
- `docs/stage-1c-storage-profile-policy.md`;
- Issue #47 and the amended G4 binding.

Stage 1C's purpose allowlist remains only:

- `quality_evaluation`;
- `held_out_evaluation`.

Model training, publication, demonstration, calibration, PDF-pipeline evaluation and synthetic derivation remain unauthorized by the current Stage 1C decision.

## 3. Repository-safe metadata state

A planned item may remain in ordinary Git when:

- `artifact.state = metadata_only`;
- `eligibilityClass = blocked`;
- `split = unassigned`;
- `retention.storageClass = not_assigned`;
- digest, byte size, storage locator, custody/encryption policies and custodian are null;
- no purpose is granted merely because planning metadata exists;
- no provider URL, account ID, credential, secret, local path or personal identity is exposed.

For metadata-only items, retention remains `metadata_only` or `prohibited`, deletion is not required and no deletion receipt is present.

C6 deliberately keeps pre-admission metadata `blocked`. A later resolver may compute a candidate eligibility result from approved evidence, but the catalog must not persist a lower-risk external class in anticipation of successful onboarding.

## 4. Machine-readable eligibility/profile contract

Catalog `1.3.0` represents:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted`;
- `sensitive_custody` → `high_assurance_vault`;
- `blocked` → no external profile.

The validator additionally requires:

- `open_corpus` privacy classification is `none`;
- personal/student data uses `sensitive_custody`;
- external/revoked artifacts cannot use `not_assigned`;
- metadata-only artifacts cannot claim an external profile;
- permission storage restrictions match the selected profile.

Public-domain status of the composition alone is never sufficient. Rights evidence must cover the exact edition, engraving, scan, photograph or acquired file.

## 5. Legacy migration boundary

Catalog `1.2.0` records are migrated only through the explicit migration function.

The safe mapping is:

```text
metadata_only + not_assigned
        ↓
blocked + not_assigned

external/revoked + custody_external
        ↓
sensitive_custody + high_assurance_vault
```

Legacy records are never automatically reclassified as `open_corpus` or `restricted_corpus`. Any unexpected legacy storage state is rejected.

## 6. Operational profile gates

Machine-readable profile selection does not prove the physical/provider controls.

### `managed_standard`

Before use, C8 must establish at least:

- bytes outside ordinary Git;
- exact SHA-256 and byte-size binding;
- exact-artifact rights evidence;
- privacy `none`;
- approved dataset review and allowed Stage 1C purpose;
- documented retention/deletion behavior;
- protection against accidental public sharing for private project copies;
- encryption in transit and at rest for non-public managed copies;
- understood backup/version behavior preventing silent corpus drift;
- no provider/account/path/credential leakage into Git.

Managed cloud/file storage may qualify. No provider is approved merely by brand.

### `managed_restricted`

C9 requires the applicable `managed_standard` controls plus restriction-compatible provider/environment, deny-by-default membership, no public links, appropriate access/change history and restriction-compatible retention/deletion/backup behavior.

### `high_assurance_vault`

C10 retains the accepted Stage 1B/C4 controls: supported host, encryption, least privilege, role separation, quarantine, audit integrity/anti-rollback, retention, immediate revocation, deletion evidence, backup anti-resurrection and Git/sync separation.

The previous Windows 7 failure applies to the inspected high-assurance-vault candidate. It is not a universal blocker for future `open_corpus` managed storage.

## 7. Item-specific pre-admission conditions

Before a specific artifact becomes `external_available`, evidence must establish:

- exact-artifact rights review approved;
- privacy review acceptable;
- dataset review approved;
- provenance sufficient;
- purpose exactly within the current Stage 1C allowlist;
- item-specific purpose authorization current and not revoked;
- retention/restrictions compatible with selected profile;
- deterministic eligibility result compatible with the stored class/profile;
- selected operational profile verification passed;
- held-out isolation preserved;
- no prohibited Stage 1 purpose activated.

Failure of any one gate blocks admission.

## 8. Transition discipline

The artifact-state sequence remains:

```text
metadata_only -> external_available -> revoked
```

C6 does not perform this transition. Repository metadata must never be marked `external_available` in anticipation of a future upload or provider check.

The transition may be recorded only after the actual artifact digest/size, opaque storage references, item authorizations and applicable operational evidence exist and the then-current validators accept the record.

## 9. Current decision table

| Condition | Result |
|---|---|
| Valid metadata-only record | planning allowed; onboarding blocked |
| C6 class/profile schema is valid but C7 evidence-derived resolver is not established | onboarding blocked |
| Exact rights/privacy/review/purpose/provenance unresolved | `blocked`; onboarding blocked |
| `open_corpus` without C8 `managed_standard` verification | onboarding blocked |
| `restricted_corpus` without C9 restriction-compatible verification | onboarding blocked |
| `sensitive_custody` without Stage 1B/C4/C10 high-assurance verification | onboarding blocked |
| Purpose outside current Stage 1C allowlist | onboarding blocked |
| All item, resolver and operational gates pass | eligible for separately controlled onboarding; never automatic approval |

## 10. C6 zero-state assertion

C6:

- onboards **0** artifact bytes;
- creates **0** storage resources;
- creates **0** credentials or keys;
- grants **0** artifact-specific permissions;
- freezes **0** real dataset splits;
- authorizes **0** model training, publication, demonstration, calibration, PDF-pipeline evaluation or synthetic derivation;
- does not start Stage 2.

## 11. Verification boundary

C6 changes the dataset catalog schema, Python validators, schema-parity checks, test helpers, metadata example and a conservative legacy migration function. It does not modify restoration runtime, job API, model behavior, provider infrastructure or artifact bytes.

The C6 PR must pass exact-head repository validation, catalog validation, schema parity, full unit tests and compile checks on Python 3.11 and 3.12 before Ready-for-review. Ready and merge remain separate approval gates.
