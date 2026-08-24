# Stage 1C Artifact Custody Profile Policy

**Status:** Architecture policy accompanying ADR 0016; no artifact onboarding  
**Stage:** Stage 1C  
**Parent:** Issue #47

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
| `restricted_corpus` | Lawful intended use but license/donor/access/retention restrictions exist; privacy acceptable | `managed_restricted` | Only if artifact terms and provider configuration permit it | No, unless a restriction requires it |
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

## `managed_restricted` additional controls

- provider/environment explicitly compatible with artifact terms;
- deny-by-default project membership;
- no public links;
- access/change history where the provider supports it;
- restriction-compatible deletion and backup behavior;
- any storage/environment allowlist in the artifact permission must match.

## `high_assurance_vault`

Uses ADR 0014 and the Stage 1C C4 vault-verification evidence contract. This retains the stronger requirements for supported host, encryption, offline separation, least privilege, role separation, quarantine, audit anti-rollback, retention, immediate revocation, deletion evidence, backup anti-resurrection, and Git/sync separation.

## Provider neutrality

No provider is approved by brand in this policy. Google Drive or another managed service can qualify only for `managed_standard`/`managed_restricted` after its concrete project configuration is checked. A provider's general marketing or encryption statement is not sufficient evidence by itself.

## Migration guard

This policy is architectural until the machine-readable dataset contract is versioned to represent eligibility class and storage profile. Therefore:

- no current item is automatically reclassified;
- existing `custody_external` metadata is not weakened;
- no new artifact may become `external_available` under the new profile names until the follow-up schema/validator PR is merged and verified;
- Stage 2 remains blocked.