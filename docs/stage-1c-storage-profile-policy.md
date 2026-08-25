# Stage 1C Artifact Custody Profile Policy

**Status:** Accepted architecture; catalog `1.3.0` machine-readable implementation introduced by C6; C7 deterministic eligibility merged; C8 managed-standard verification merged  
**Stage:** Stage 1C  
**Parent:** Issue #47  
**Architecture accepted through:** PR #55 / `c6e6b592c2cef63a15c13fb8b0f72019c7864a84`

## Purpose

Apply storage controls in proportion to the verified risk of the exact artifact instead of forcing every real score/TAB document into one offline vault.

## Classification order

Storage is selected only after this order is evaluated:

```text
exact artifact provenance
        ↓
exact artifact rights / license evidence
        ↓
privacy classification
        ↓
purpose + retention + dataset review
        ↓
artifact eligibility class
        ↓
storage profile
```

A composer/work being public domain is supporting context only. It does not replace rights evidence for the exact edition, engraving, scan, photograph, or acquired file.

## Matrix

| Eligibility class | Typical condition | Allowed profile | Cloud/Drive-style storage | High-assurance C4 vault required? |
| --- | --- | --- | --- | --- |
| `open_corpus` | Exact artifact verified public domain or openly licensed; privacy `none`; purpose/review/retention approved | `managed_standard` | Yes, if configured profile controls pass | No |
| `restricted_corpus` | Lawful intended use but license/donor/access/retention restrictions exist; privacy acceptable | `managed_restricted` | Only if artifact terms and provider configuration permit it | No, unless policy escalates the artifact to `sensitive_custody` |
| `sensitive_custody` | Private/user-provided, personal/student, consent-restricted, or policy requires strongest custody | `high_assurance_vault` | Not as a substitute for the vault | Yes |
| `blocked` | Rights/privacy/purpose/review/provenance missing, pending, rejected, expired, or contradictory | none | No | No onboarding at all |

## `managed_standard` minimum controls

- no real corpus bytes in ordinary Git;
- exact SHA-256 and byte-size binding;
- exact-artifact rights evidence;
- privacy `none`;
- approved dataset review and purpose authorization;
- documented retention/deletion behavior;
- project-managed copies protected against accidental public sharing unless publication is separately authorized;
- encryption in transit and at rest for private managed copies;
- corpus manifest cannot silently drift when a provider version changes;
- provider/account/path details remain outside ordinary Git except for approved opaque evidence references.

C8 operational verification covers only the storage-configuration subset of these requirements. Exact-artifact rights, privacy, dataset review, purpose, retention assignment and final digest/byte-size values remain item-specific Stage 1A/1C admission gates and are not replaced by a profile-level pass.

## `managed_restricted` additional controls

- provider/environment explicitly compatible with artifact terms;
- deny-by-default project membership;
- no public links;
- access/change history where the provider supports it;
- restriction-compatible deletion and backup behavior;
- any storage/environment allowlist in the artifact permission must match.

C9 verifies these restricted-profile controls while inheriting the nine C8 baseline operational controls. It uses an opaque `restrictionSetRef`; the repository does not embed license text, provider details, or artifact-specific restriction content.

## `high_assurance_vault`

Uses ADR 0014 and the Stage 1C C4 vault-verification evidence contract. This retains the stronger requirements for supported host, encryption, offline separation, least privilege, role separation, quarantine, audit anti-rollback, retention, immediate revocation, deletion evidence, backup anti-resurrection, and Git/sync separation.

## Provider neutrality

No provider is approved by brand in this policy. Google Drive or another managed service can qualify only for `managed_standard`/`managed_restricted` after its concrete project configuration is checked. A provider's general marketing or encryption statement is not sufficient evidence by itself.

The Stage 1 snapshot `environment=stage1_offline` describes the bounded evaluation execution environment. It no longer means that every permitted storage profile must itself be an offline vault.

## C6 machine-readable contract

Catalog schema `1.3.0` adds required `eligibilityClass` and changes external `retention.storageClass` values to the ADR 0016 profiles:

- `blocked` + `not_assigned` for metadata-only/pre-admission state;
- `open_corpus` + `managed_standard`;
- `restricted_corpus` + `managed_restricted`;
- `sensitive_custody` + `high_assurance_vault`.

The Python validator rejects illegal class/profile pairs, `open_corpus` with non-`none` privacy, and personal/student data outside `sensitive_custody`.

## C7 deterministic eligibility

C7 derives the minimum required eligibility class from validated structured evidence and rejects declarations weaker than that floor. Explicit security escalation remains permitted, so legacy high-assurance records are never silently downgraded.

## Legacy anti-downgrade guard

Existing catalog `1.2.0` metadata is not silently weakened. The explicit migration maps:

- metadata-only legacy records → `blocked` / `not_assigned`;
- legacy `custody_external` external/revoked records → `sensitive_custody` / `high_assurance_vault`;
- legacy storage allowlist `custody_external` → `high_assurance_vault`.

The migration never infers `managed_standard` or `managed_restricted`. Unknown legacy shapes fail closed.

## Operational hold

C6 and C7 make profile vocabulary and eligibility deterministic; neither proves a real storage configuration or artifact eligible.

- C8 defines fail-closed operational verification for a concrete `managed_standard` configuration. The repository zero state remains `incomplete`; an actual pass requires external evidence.
- C9 defines fail-closed operational verification for `managed_restricted`, including the C8 baseline plus the six accepted restricted-profile controls. Its repository zero state also remains `incomplete`; an actual pass requires external evidence bound to a concrete restriction set.
- C10 preserves/verifies the existing high-assurance boundary.

No governance/profile implementation by itself introduces artifact bytes or grants artifact-specific permission. Stage 2 remains blocked until the complete Stage 1 exit gate is accepted.
