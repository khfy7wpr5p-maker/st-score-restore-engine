# Stage 1C Vault Verification Evidence Contract

**Status:** C4 implementation contract; metadata-only; no artifact onboarding  
**Parent:** Issue #47  
**Roadmap stage:** Stage 1C — authorized artifact onboarding and corpus realization  
**Depends on:** Stage 1B custody/operations contract and ADR 0016 risk-tiered custody once accepted

## 1. Purpose

This contract defines the repository-visible evidence record used to determine whether a concrete **high-assurance Stage 1 vault** has passed the operational verification required for artifacts classified into the `sensitive_custody` tier.

It is not a universal precondition for every real score/TAB artifact. Under ADR 0016, verified low-risk `open_corpus` artifacts may use the separately defined `managed_standard` profile after the follow-up machine-readable storage-profile implementation is accepted. Restricted artifacts may use `managed_restricted` only when their artifact-specific terms permit it.

The record is deliberately provider-neutral and metadata-only. It must never contain local filesystem paths, provider URLs, bucket/container names, account identifiers, credentials, key material, real-person identifiers, document bytes, or real artifact digests.

A vault-verification record can prove only the high-assurance environment gate. It does not grant artifact-specific rights, privacy approval, dataset-review approval, purpose authorization, processing eligibility, or Stage 2 authorization.

## 2. C4 implementation scope

C4 added only:

- a JSON Schema for repository-visible vault-verification evidence;
- a deterministic validator for that evidence;
- a metadata-only zero-state example;
- focused positive and negative tests;
- repository/CI wiring needed to make the contract mandatory.

C4 did not:

- create or configure a storage resource;
- read, copy, hash, upload, transform, or delete real/private/copyrighted score or TAB artifacts;
- record a real local path, provider URL, account ID, bucket/container name, credential, key, or identity map;
- change custody runtime behavior, dataset item authorization, split policy, restoration behavior, quality metrics, safety thresholds, API behavior, or music-application repositories;
- declare any vault compliant merely because the schema/validator exists;
- begin Stage 2 or any later roadmap stage.

## 3. Bound decisions

Every existing C4 record is bound to:

- `adr-0014-stage-1b-custody-operations-v1`;
- the legacy Stage 1C G4 environment `stage1_offline`;
- the legacy Stage 1C G4 storage class `custody_external`;
- the repository-visible opaque locator policy.

ADR 0016 does not reinterpret those records. They remain the evidence format for the `high_assurance_vault` profile. A later schema migration may introduce explicit profile identifiers, but old records must not be silently downgraded or reclassified.

The record uses only opaque references for the assessed vault, assessor, and per-control evidence. Opaque evidence references point to externally retained operational evidence; they do not embed the evidence itself.

## 4. Required control set

The validator requires an explicit result for every control below:

1. `supported_host` — the custody host/platform is supported and maintained;
2. `encryption_at_rest` — the custody boundary provides the accepted encryption-at-rest protection;
3. `offline_boundary` — the selected high-assurance environment satisfies the approved offline boundary;
4. `private_by_default` — no broad/default read exposure exists;
5. `least_privilege_access` — access is narrowly scoped and deny-by-default;
6. `separation_of_duties` — conflicting real-person roles are prevented by the external identity/authorization boundary;
7. `quarantine_isolation` — untrusted intake/inspection cannot silently become processing-eligible;
8. `audit_integrity_and_anti_rollback` — security events, checkpoints, and independent anti-rollback evidence are available and fail closed;
9. `retention_enforcement` — expiry/hold policy can block access independently of physical deletion completion;
10. `immediate_revocation` — valid revocation can block active/cached/queued/in-flight access without an access-authorizer veto;
11. `deletion_receipts` — pending-backup and final-deletion evidence are distinguishable and independently verifiable;
12. `backup_anti_resurrection` — restore cannot make revoked, expired, deletion-pending, or tombstoned material available;
13. `git_and_sync_separation` — the high-assurance vault remains outside ordinary Git and automatic cloud-sync folders.

Each control result is exactly one of `pass`, `fail`, or `not_verified`.

- `pass` and `fail` require an opaque external evidence reference.
- `not_verified` must not carry an evidence reference.

## 5. Deterministic overall state

The overall state is computed fail-closed from the controls:

- `pass` is valid only when all 13 controls are `pass`;
- `fail` is valid when at least one control is `fail`;
- `incomplete` is valid only when there are no `fail` controls and at least one control is `not_verified`.

A caller cannot force a `pass` by setting only the top-level state. Any contradiction between the top-level state and the control set is invalid.

A `pass` record still sets all authorization-implying claims to `false`.

## 6. Repository-visible privacy boundary

The schema intentionally has no free-text notes field. Repository-visible strings are limited to fixed contract values, UTC timestamps, and opaque references matching constrained prefixes.

The following are therefore invalid by construction:

- `C:\\Users\\...` or `/home/...` paths;
- `https://...` provider/resource URLs;
- bucket/container/database names;
- cloud account/project/subscription identifiers;
- email addresses or human-readable actor names;
- credentials, tokens, secrets, encryption keys, recovery material;
- document names, score titles, artifact bytes, or real artifact SHA-256 values.

## 7. Acceptance criteria

C4 was complete only when all of the following were freshly demonstrated on the exact PR head:

- the schema is JSON Schema Draft 2020-12 and rejects undeclared fields;
- the validator accepts the repository zero-state example as `incomplete`;
- a complete synthetic metadata-only record with opaque references validates as `pass`;
- contradictory `pass`, `fail`, and `incomplete` claims are rejected;
- a passing control without evidence is rejected;
- a `not_verified` control carrying evidence is rejected;
- non-opaque vault/actor/evidence references are rejected;
- authorization-implying claims cannot be changed from `false`;
- repository validation, Stage 1A dataset validation, full unit tests, and compile validation remain green on Python 3.11 and 3.12;
- no artifact bytes, storage resource, active item permission, real split, model work, calibration work, or later-stage behavior is introduced.

## 8. Required negative tests before implementation

The implementation includes at least these negative cases:

1. top-level `pass` with one `not_verified` control;
2. top-level `pass` with one `fail` control;
3. top-level `fail` with no failed control;
4. top-level `incomplete` with a failed control;
5. `pass` control without an evidence reference;
6. `fail` control without an evidence reference;
7. `not_verified` control with an evidence reference;
8. local path used as `vaultRef`;
9. URL/provider locator used as an evidence reference;
10. human-readable assessor identity instead of an opaque actor reference;
11. any authorization-implying claim set to `true`;
12. unknown/extra top-level or control fields.

## 9. C4 completion boundary after ADR 0016

C4 remains valid evidence for `high_assurance_vault`. It does **not** make any current vault compliant and it does **not** authorize a storage profile for a particular artifact.

After ADR 0016, an artifact first needs exact-artifact rights/privacy/purpose/retention/dataset classification. A `sensitive_custody` artifact remains blocked until the high-assurance vault actually passes C4 and all item-specific Stage 1A gates pass.

A verified `open_corpus` artifact does not need C4 solely because it is a real document. However, no artifact may use the new `managed_standard` or `managed_restricted` profile until a follow-up implementation PR adds versioned machine-readable profile fields, validator rules, migration behavior, and negative tests. Until that implementation is merged, current validators remain authoritative and artifact onboarding under the new profile names remains blocked.