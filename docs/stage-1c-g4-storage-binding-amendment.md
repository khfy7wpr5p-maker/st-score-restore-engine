# Stage 1C G4 Storage Binding Amendment

**Status:** Accepted through PR #55  
**Date:** 2026-08-24  
**Parent issue:** #47  
**Decision:** ADR 0016 — `adr-0016-stage-1c-risk-tiered-custody-v1`  
**Accepted merge commit:** `c6e6b592c2cef63a15c13fb8b0f72019c7864a84`

## Amendment

The Stage 1C G4 **purpose allowlist remains unchanged**:

- `quality_evaluation`
- `held_out_evaluation`

The prior G4 rule that required every real or controlled-synthetic artifact to use one dedicated encrypted offline `stage1_offline` / `custody_external` vault is superseded by ADR 0016's artifact-specific custody tiers.

The architecture now selects storage only after exact-artifact rights, privacy, purpose, retention, provenance and dataset-review gates are evaluated:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when restrictions permit;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved/rejected governance → `blocked`.

The full Stage 1B/C4 vault-verification boundary remains mandatory for `high_assurance_vault`. It is not a universal requirement for verified `open_corpus` artifacts.

## Current implementation hold

The architecture amendment is accepted, but the merged Stage 1A/1C machine-readable schema still represents legacy `stage1_offline` / `custody_external` values. Therefore no artifact may be onboarded under the new profile names until a follow-up schema/validator implementation PR is accepted, tested and merged.

This hold is fail-closed and migration-safe:

- existing high-assurance records remain authoritative;
- no old `custody_external` record is silently reinterpreted as `managed_standard`;
- unresolved rights/privacy/purpose/review state cannot select a weaker profile;
- no artifact bytes, permissions, split assignments, provider resources, credentials or Stage 2 behavior are created by this amendment.

## Next implementation boundary

The next eligible Stage 1C slice is the versioned storage-profile schema/validator migration implementing `open_corpus`, `restricted_corpus`, `sensitive_custody`, `blocked`, `managed_standard`, `managed_restricted`, and `high_assurance_vault` with deterministic negative tests.