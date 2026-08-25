# Stage 1C Managed Restricted Verification Contract

**Status:** C9 implementation candidate; metadata-only; no artifact onboarding  
**Stage:** Stage 1C  
**Parent:** Issue #47  
**Architecture:** ADR 0016 risk-tiered artifact custody  
**Profile:** `managed_restricted` for `restricted_corpus`

## Purpose

C9 defines the repository-visible evidence contract used to verify a concrete `managed_restricted` configuration before a `restricted_corpus` artifact may rely on it.

`managed_restricted` inherits the nine `managed_standard` operational controls from C8 and adds only the controls required by the accepted storage-profile policy for restricted material. It does not import the stronger C4 high-assurance vault requirements unless policy or evidence escalates the artifact to `sensitive_custody`.

A passing C9 record proves only that one opaque restricted-storage configuration has satisfied this profile-level operational gate against one opaque restriction set. It does not grant artifact rights, purpose authorization, dataset admission, publication, training, or Stage 2 authorization.

## Repository-visible privacy boundary

The record contains only fixed contract values, timestamps, result enums, and opaque references. It must not contain provider names, account/project/folder identifiers, URLs, paths, credentials, human identities, filenames, real artifact digests, or artifact bytes.

`configurationRef`, `restrictionSetRef`, `assessorRef`, and each `evidenceRef` are opaque handles to externally retained evidence.

## Required controls

### C8 baseline controls

1. `git_exclusion`
2. `object_binding_capability`
3. `project_managed_access`
4. `accidental_public_sharing_prevention`
5. `encryption_in_transit`
6. `encryption_at_rest_private_copies`
7. `version_drift_protection`
8. `retention_deletion_behavior`
9. `opaque_repository_boundary`

### C9 additional restricted controls

10. `artifact_terms_compatibility` — the selected provider/environment configuration is compatible with the externally retained artifact terms represented by `restrictionSetRef`;
11. `deny_by_default_membership` — project membership/access is deny-by-default and explicitly granted;
12. `public_links_disabled` — unrestricted/public links are disabled for the restricted configuration;
13. `access_change_history` — access/change history is available where the selected environment supports it and its absence cannot be silently treated as present;
14. `restriction_compatible_deletion_backup` — deletion and backup behavior is compatible with the externally retained restriction set;
15. `storage_environment_allowlist_match` — any storage/environment allowlist in the item permission matches the selected configuration.

Each control is exactly `pass`, `fail`, or `not_verified`. `pass` and `fail` require an opaque evidence reference; `not_verified` must not carry one.

## Deterministic aggregate

- `pass`: all 15 controls pass;
- `fail`: at least one control fails;
- `incomplete`: no failures and at least one control is not verified.

The top-level state cannot override the control set.

## Separation from artifact admission

Even a real C9 `pass` does not admit an artifact. The item still needs exact-artifact provenance/rights, compatible privacy, deterministic C7 eligibility, dataset review, active Stage 1 purpose authorization, retention/split rules, exact digest and byte size, and every item-specific restriction check.

The repository cannot approve a provider by brand and cannot infer that arbitrary restrictions are compatible merely because the C9 schema exists.

## Zero state

The repository example keeps every control `not_verified` and `overallState=incomplete`. Synthetic all-pass records exist only to test validator semantics.

## Acceptance criteria

C9 is implementation-complete only when the exact PR head demonstrates:

- JSON Schema Draft 2020-12 and deny-unknown-field behavior;
- valid incomplete zero state;
- valid synthetic all-pass metadata record;
- fail-closed aggregate consistency;
- required opaque evidence for pass/fail controls;
- rejection of evidence attached to not-verified controls;
- immutable profile/eligibility/contract bindings;
- path/URL/provider/account/human-identity leakage rejected or structurally impossible;
- authorization/provider-by-brand claims fixed to false;
- non-mutating validation;
- C8, C4, Stage 1 dataset, full tests, and compile green on Python 3.11 and 3.12;
- no real provider resource, artifact byte, credential, runtime restoration, model, or Stage 2 work introduced.

## Next boundary

After C9 is accepted and merged, C10 may verify compatibility of the existing high-assurance C4 boundary with ADR 0016 `sensitive_custody/high_assurance_vault` semantics. Real restricted-corpus onboarding remains impossible until a concrete C9 configuration has external evidence and all item-specific gates pass.
