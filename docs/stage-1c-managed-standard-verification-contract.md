# Stage 1C Managed Standard Verification Contract

**Status:** C8 implementation candidate; metadata-only; no artifact onboarding  
**Stage:** Stage 1C  
**Parent:** Issue #47  
**Architecture:** ADR 0016 risk-tiered artifact custody  
**Profile:** `managed_standard` for `open_corpus`

## Purpose

C8 defines the repository-visible evidence contract used to verify a concrete `managed_standard` storage configuration before any `open_corpus` artifact may rely on that configuration.

The contract is deliberately provider-neutral and proportional to the lower-risk `open_corpus` tier. It does not import the stronger C4 high-assurance vault controls such as offline separation, role separation, quarantine, anti-rollback audit, immediate revocation, deletion receipts, or backup anti-resurrection unless a later policy explicitly escalates the artifact to `sensitive_custody`.

A passing C8 configuration record proves only the `managed_standard` operational profile gate. It does not grant exact-artifact rights, privacy approval, dataset review, purpose authorization, split membership, artifact onboarding, model training, publication, or Stage 2 authorization.

## Repository-visible privacy boundary

The record must never contain:

- provider names or brands;
- account, tenant, project, bucket, folder, share, or resource identifiers;
- provider URLs or local filesystem paths;
- credentials, tokens, secrets, keys, recovery material, or cookies;
- human-readable actor names or email addresses;
- real score/TAB/PDF/image bytes;
- real artifact SHA-256 values or filenames.

The configuration, assessor, and evidence links are repository-safe opaque references only.

## Required control set

C8 requires an explicit result for these nine controls:

1. `git_exclusion` — real corpus bytes remain outside ordinary Git;
2. `object_binding_capability` — the configuration/workflow can bind each admitted object to exact SHA-256 and byte size without relying on a mutable filename alone;
3. `project_managed_access` — the retained project copy is under a controlled project-managed access boundary rather than an uncontrolled public/personal share;
4. `accidental_public_sharing_prevention` — public-link/default-public exposure is prevented unless publication is separately authorized;
5. `encryption_in_transit` — transport protection is enabled for managed transfers;
6. `encryption_at_rest_private_copies` — private managed copies have encryption-at-rest protection;
7. `version_drift_protection` — provider version/replacement behavior cannot silently change the corpus object without manifest/digest mismatch being detected;
8. `retention_deletion_behavior` — retention and deletion behavior for the managed copy is documented and externally evidenced;
9. `opaque_repository_boundary` — provider/account/path/configuration details stay outside ordinary Git and are referenced only through approved opaque evidence handles.

Each control result is exactly `pass`, `fail`, or `not_verified`.

- `pass` and `fail` require an opaque external evidence reference;
- `not_verified` must not carry an evidence reference.

## Deterministic overall state

The verifier derives the only valid aggregate state:

- `pass` only when all nine controls pass;
- `fail` when at least one control fails;
- `incomplete` when no control fails and at least one control is not verified.

The top-level state cannot override the controls.

## Separation from artifact admission

Even when a real configuration later receives C8 `pass`, an artifact remains blocked until its independent Stage 1A/1C item gates pass, including:

- exact-artifact provenance and rights evidence;
- privacy `none` for `open_corpus`;
- deterministic C7 eligibility result compatible with `open_corpus`;
- dataset review;
- current Stage 1 purpose authorization;
- retention and split policy;
- exact artifact SHA-256 and byte-size binding;
- revocation/deletion rules where applicable.

C8 therefore keeps all authorization-implying claims fixed to `false`, including `providerApprovedByBrand`.

## Zero state

The repository example intentionally sets all controls to `not_verified` and the aggregate to `incomplete`. This is the honest default because the repository itself cannot prove an external storage configuration merely by containing a schema or validator.

Tests may construct synthetic metadata-only `pass` records to prove validator semantics. Such test records do not represent or approve a real provider configuration.

## Acceptance criteria

C8 implementation is complete only when the exact PR head demonstrates:

- JSON Schema Draft 2020-12 with undeclared fields rejected;
- zero-state example validates as `incomplete`;
- synthetic metadata-only all-pass record validates;
- contradictory aggregate states fail closed;
- pass/fail controls without evidence are rejected;
- not-verified controls with evidence are rejected;
- path, URL, provider, account, and human-readable identity leakage is rejected or structurally impossible;
- every authorization/provider-by-brand claim remains `false`;
- input records are not mutated;
- existing Stage 1A, C4, C6/C7 and repository tests remain green on Python 3.11 and 3.12;
- no artifact bytes, provider resource, credentials, runtime restoration change, model work, or Stage 2 work is introduced.

## Next boundary

After C8 is accepted and merged, C9 may define the additional operational verification required for `managed_restricted`. A real `managed_standard` configuration still requires external evidence before its record can honestly be changed from `incomplete` to `pass`.
