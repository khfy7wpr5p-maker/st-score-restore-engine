# Stage 1C Artifact Admission Contract

**Status:** C11 implementation candidate; deterministic pre-merge admission gate; repository zero-state remains blocked  
**Stage:** Stage 1C  
**Parent issue:** #47  
**Architecture:** ADR 0016 risk-tiered artifact custody  
**Artifact bytes added by C11:** 0

## Purpose

C11 defines the machine-readable gate that must be used when a focused pull request proposes changing a real Stage 1 dataset item to `external_available`.

The gate does not fetch, upload, copy, transform or inspect document bytes. It evaluates repository-visible metadata plus a separately supplied profile-verification record. A proposed admission is `eligible` only when every required binding is present and current; otherwise the decision is `blocked` with stable reason codes.

The admission decision is therefore a **pre-merge verification of a proposed catalog state**, not an automatic authorization service and not proof that external evidence exists merely because an opaque reference was written down.

## Zero-state behavior

`examples/stage1c-artifact-admission.zero-state.v1.json` intentionally targets the metadata-only catalog example and leaves purpose, item digest, profile identity/digest and storage-binding evidence unset.

The expected repository result is `blocked`. C11 must never turn the current zero state into an admitted artifact.

## Allowed Stage 1C purposes

C11 preserves the current G4 allowlist exactly:

- `quality_evaluation` on the `development` split;
- `held_out_evaluation` on the `held_out` split.

For an eligible admission, the active permission set must contain **exactly one** requested Stage 1C purpose. Any additional active purpose, including training, calibration, publication, demonstration, PDF-pipeline evaluation, fixture validation or synthetic derivation, blocks the admission.

This is intentionally narrower than the general dataset schema. A syntactically valid catalog is not automatically eligible for Stage 1C admission.

## Exact evidence bindings

A request that can become eligible must bind:

1. the exact `datasetItemId`;
2. the canonical SHA-256 of the complete proposed dataset item;
3. the existing `provenance.sourceReference` acquisition-evidence identity;
4. the expected evidence-derived eligibility class;
5. the expected ADR 0016 storage profile;
6. the exact profile-verification identifier;
7. the canonical SHA-256 of the exact profile-verification record used for the decision;
8. an opaque external storage-binding evidence reference linking the admitted object to the verified storage configuration or vault;
9. the requested Stage 1C purpose;
10. the UTC evaluation time.

The canonical item and profile-record digests prevent a decision from silently being reused after repository-visible evidence changes under the same logical identifier.

## Profile verification

C11 accepts only the profile implied by deterministic eligibility:

- `open_corpus` → `managed_standard` with a valid C8 record whose `overallState` is `pass`;
- `restricted_corpus` → `managed_restricted` with a valid C9 record whose `overallState` is `pass`;
- `sensitive_custody` → `high_assurance_vault` with a valid C4 vault record whose `overallState` is `pass`, under the C10 compatibility boundary.

A profile verification completed after the admission evaluation time cannot authorize that earlier admission.

A C8/C9/C4 record still does not grant artifact-specific rights or purpose permission. It proves only the relevant operational profile controls. C11 combines, but does not replace, the independent item-specific governance evidence.

## Item conditions

The proposed catalog item must already satisfy the ordinary Stage 1A/1C validators. C11 additionally requires:

- `artifact.state = external_available` in the proposed pre-merge catalog state;
- exact digest, byte size and opaque custody fields required by the catalog contract;
- approved rights and dataset review;
- acceptable privacy state;
- deterministic eligibility/profile compatibility;
- acquisition evidence identity matching the catalog `sourceReference`;
- current requested purpose at evaluation time;
- requested purpose restrictions compatible with split, storage profile, Stage 1 offline evaluation environment and retention;
- no revocation or pending deletion;
- retention not expired;
- rights/privacy/dataset reviews not completed after the admission evaluation time;
- exact item and profile-verification digest bindings;
- passing profile verification and opaque storage-binding evidence.

Unknown, missing, contradictory, future-dated or stale-at-evaluation evidence fails closed.

## Transition discipline

C11 does not directly mutate the catalog. The controlled workflow is:

```text
metadata_only planning
        ↓
external acquisition/custody + exact evidence
        ↓
focused PR proposes external_available item + split/purpose
        ↓
C11 evaluator --require-eligible
        ↓
exact-head repository CI + human approval gates
        ↓
merge records the admitted metadata state
```

The real artifact bytes remain outside ordinary Git throughout this sequence.

## CLI behavior

Running the evaluator without `--require-eligible` validates the request and reports a deterministic `eligible` or `blocked` decision. This mode is used by repository CI to prove that the zero state remains blocked.

A real onboarding PR must invoke the evaluator with:

- the proposed catalog file;
- the admission request;
- the exact profile-verification record;
- `--require-eligible`.

That mode exits non-zero for any blocked decision.

## Safety boundary

C11 does not:

- create a storage account, folder, bucket, vault, credential or key;
- approve a provider by brand;
- put provider URLs, account names, local paths or human identities in ordinary Git;
- create or fabricate an artifact SHA-256;
- create a real storage-binding evidence record;
- authorize model training, calibration, publication, demonstration or synthetic derivation;
- freeze the Stage 1 dataset snapshot;
- claim corpus coverage or bias measurements;
- begin Stage 2 or change OpenCV quality-analysis behavior;
- change restoration runtime, HTTP API or model behavior.

## Acceptance criteria

C11 is complete only when the exact PR head demonstrates:

- JSON Schema Draft 2020-12 validation for the admission request;
- repository zero-state deterministically remains `blocked`;
- synthetic metadata-only test cases can reach `eligible` for each of the three ADR 0016 profiles only when the corresponding profile record is a valid `pass`;
- item and profile-record digest mismatches block admission;
- future profile verification cannot authorize a past decision;
- acquisition-reference mismatch blocks admission;
- missing storage-binding evidence blocks admission;
- non-current purpose, wrong split, expired retention, post-dated reviews or extra active purposes block admission;
- all request claims that would expand Stage 1 authority remain fixed to `false`;
- evaluation is deterministic and does not mutate inputs;
- full repository tests and compile pass on Python 3.11 and 3.12;
- no real artifact, provider configuration, credential, runtime, model or Stage 2 work is introduced.

## Next boundary

After C11 is accepted and merged, the next Stage 1C slice may perform the **first controlled real artifact onboarding** only when concrete external rights/acquisition/storage evidence exists. If no such evidence is available, Stage 1 remains blocked rather than substituting fabricated identifiers or synthetic data for the required real corpus.
