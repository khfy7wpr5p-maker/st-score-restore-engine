# Stage 1C High-Assurance Compatibility Contract

**Status:** C10 implementation candidate; structural compatibility only; no artifact onboarding  
**Stage:** Stage 1C  
**Parent:** Issue #47  
**Architecture:** ADR 0016 risk-tiered artifact custody  
**Profile:** `sensitive_custody` → `high_assurance_vault`

## Purpose

C10 proves that the accepted Stage 1C risk-tiered storage model remains structurally compatible with the existing C4 high-assurance vault evidence contract without rewriting, downgrading, or broadening legacy evidence.

C4 predates the risk-tiered profile vocabulary and therefore remains bound to the legacy storage-class value `custody_external`, the `stage1_offline` execution environment, and ADR 0014. C10 does not migrate those C4 records in place. Instead it verifies a one-way compatibility boundary:

```text
sensitive_custody
        ↓
high_assurance_vault
        ↓
legacy C4 evidence format
(storageClass = custody_external)
```

The legacy C4 evidence format is not reusable as proof for `managed_standard` or `managed_restricted`.

## Compatibility invariants

C10 requires all of the following to remain true at the same repository revision:

1. the dataset contract maps `sensitive_custody` to `high_assurance_vault`;
2. no other eligibility class maps to `high_assurance_vault`;
3. the legacy storage-class constant remains `custody_external`;
4. the dataset schema still admits `sensitive_custody` and `high_assurance_vault`;
5. the C4 schema remains `stage1c-vault-verification-v1`;
6. the C4 contract remains bound to ADR 0014;
7. the C4 environment remains `stage1_offline`;
8. the C4 storage class remains `custody_external`;
9. all 13 C4 high-assurance controls remain present and ordered consistently with the C4 validator;
10. every C4 authorization-implying claim remains fixed to `false`;
11. C10 itself cannot claim a real vault is verified, a provider is approved, an artifact is authorized, or Stage 2 is authorized;
12. the repository C4 zero-state remains `incomplete` until concrete external evidence is supplied.

## Why C4 is not rewritten

Changing old C4 records from `custody_external` to `high_assurance_vault` would blur the distinction between historical evidence format and the newer risk-tiered catalog vocabulary. C10 therefore preserves the old evidence contract exactly and validates the compatibility mapping around it.

This also protects the legacy anti-downgrade guarantee introduced by C6: old external custody records are never silently reinterpreted as a weaker managed profile.

## Machine-readable record

`examples/stage1c-high-assurance-compatibility.v1.json` is a repository-visible structural compatibility record. It contains no provider, path, account, credential, person, artifact, or external evidence locator.

Its `compatibilityState=pass` means only that the current repository contracts are structurally compatible. It does **not** mean that a real high-assurance vault has passed C4.

The real operational C4 state remains independently derived from the C4 evidence record. The repository zero-state is intentionally `incomplete`.

## Safety boundary

C10 does not:

- create or configure a vault;
- approve a provider by brand;
- add real score/TAB/PDF/image bytes;
- add a real artifact digest or filename;
- grant artifact-specific rights or purpose permission;
- change restoration runtime, HTTP API, model behavior, calibration, or thresholds;
- begin Stage 2 or OpenCV quality-analysis implementation.

A future real `sensitive_custody` artifact can become eligible only when its item-specific Stage 1 gates pass **and** a concrete C4 vault-verification record independently reaches `pass`.

## Acceptance criteria

C10 is complete only when the exact PR head demonstrates:

- JSON Schema Draft 2020-12 validation for the compatibility record;
- exact `sensitive_custody → high_assurance_vault → custody_external C4` binding;
- rejection of `open_corpus`/`restricted_corpus` reuse of C4 compatibility;
- rejection of managed-standard or managed-restricted profile substitution;
- rejection of C4 schema, storage-class, control-set, or dataset-profile drift;
- all compatibility and C4 authorization claims remain fail-closed;
- repository C4 zero-state remains `incomplete`;
- full repository tests and compile pass on Python 3.11 and 3.12;
- no real provider configuration, credential, artifact bytes, runtime change, model work, or Stage 2 work is introduced.

## Next boundary

After C10 is accepted and merged, the storage-profile implementation sequence C5–C10 is complete. Stage 1C may then proceed to controlled artifact onboarding and corpus realization under exact-artifact rights/privacy/purpose/retention/profile evidence. Stage 2 remains blocked until the full Stage 1 exit evidence is complete and accepted.
