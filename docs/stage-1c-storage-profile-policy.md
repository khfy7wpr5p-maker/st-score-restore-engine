# Stage 1C Artifact Custody Profile Policy

**Status:** Accepted and implemented architecture; C5-C10 merged; C11 admission gate merged; used by C12/C14 and active C17 work  
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

| Eligibility class | Typical condition | Allowed profile | Cloud/managed storage | High-assurance C4 vault required? |
| --- | --- | --- | --- | --- |
| `open_corpus` | Exact artifact verified Public Domain or openly licensed; privacy `none`; purpose/review/retention approved | `managed_standard` | Yes, if the concrete profile controls pass | No |
| `restricted_corpus` | Lawful intended use but license/donor/access/retention restrictions exist; privacy acceptable | `managed_restricted` | Only if exact artifact terms and configuration permit it | No, unless policy escalates to `sensitive_custody` |
| `sensitive_custody` | Private/user-provided, personal/student, consent-restricted, or policy requires strongest custody | `high_assurance_vault` | Not as a substitute for the vault | Yes |
| `blocked` | Rights/privacy/purpose/review/provenance missing, pending, rejected, expired, or contradictory | none | No | No onboarding |

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

C8 operational verification covers only the storage-configuration subset of these requirements. Exact-artifact rights, privacy, dataset review, purpose, retention assignment, and final digest/byte-size values remain item-specific Stage 1A/1C gates.

A repository example with `overallState=incomplete` is a zero-state contract example only. It does not mean that every real Stage 1 `managed_standard` configuration remains unverified. C12/C14 use a separately bound concrete managed-standard PASS configuration, and active C17A reuses that same verified configuration only when the exact profile identity/digest and item-level admission bindings match.

## `managed_restricted` additional controls

- provider/environment explicitly compatible with exact artifact terms;
- deny-by-default project membership;
- no public links;
- access/change history where the environment supports it;
- restriction-compatible deletion and backup behavior;
- any storage/environment allowlist in the artifact permission must match.

C9 verifies these restricted-profile controls while inheriting the C8 baseline. Its repository zero-state example remains `incomplete` unless a concrete restricted configuration is independently evidenced. A C9 schema or synthetic all-pass test record does not approve any provider or artifact.

## `high_assurance_vault`

Uses ADR 0014 and the Stage 1C C4 vault-verification evidence contract. This retains the stronger requirements for supported host, encryption, offline separation, least privilege, role separation, quarantine, audit anti-rollback, retention, immediate revocation, deletion evidence, backup anti-resurrection, and Git/sync separation.

C10 verifies structural compatibility without rewriting historical C4 evidence. The one-way compatibility is:

```text
sensitive_custody
        ↓
high_assurance_vault
        ↓
legacy C4 evidence
(storageClass = custody_external)
```

C4 evidence cannot be reinterpreted as proof for `managed_standard` or `managed_restricted`. A C10 structural pass does not verify a real vault, approve a provider, or authorize a sensitive artifact.

## Provider neutrality

No provider is approved by brand in this policy. A managed service can qualify only after its concrete project configuration is checked. General marketing or encryption statements are not sufficient evidence by themselves.

The Stage 1 snapshot `environment=stage1_offline` describes the bounded evaluation environment. It does not require every permitted storage profile to be an offline vault.

## C6 machine-readable contract — MERGED

Catalog schema `1.3.0` adds required `eligibilityClass` and maps external retention storage classes to ADR 0016 profiles:

- `blocked` + `not_assigned` for metadata-only/pre-admission state;
- `open_corpus` + `managed_standard`;
- `restricted_corpus` + `managed_restricted`;
- `sensitive_custody` + `high_assurance_vault`.

The validator rejects illegal class/profile pairs, `open_corpus` with non-`none` privacy, and personal/student data outside `sensitive_custody`.

The earlier statement that this migration is still pending is obsolete.

## C7 deterministic eligibility — MERGED

C7 derives the minimum required eligibility class from validated structured evidence and rejects declarations weaker than that floor. Explicit security escalation remains permitted, so legacy high-assurance records are never silently downgraded.

## Legacy anti-downgrade guard

Existing catalog `1.2.0` metadata is not silently weakened. Explicit migration maps:

- metadata-only legacy records → `blocked` / `not_assigned`;
- legacy `custody_external` external/revoked records → `sensitive_custody` / `high_assurance_vault`;
- legacy storage allowlist `custody_external` → `high_assurance_vault`.

The migration never infers `managed_standard` or `managed_restricted`. Unknown legacy shapes fail closed.

## Operational status

- **C8:** managed-standard verification contract merged. A concrete PASS configuration has been used by admitted `open_corpus` items; the zero-state example remains intentionally incomplete.
- **C9:** managed-restricted verification contract merged. No schema/example alone implies a real restricted configuration has passed.
- **C10:** high-assurance compatibility merged. Structural pass does not prove a real high-assurance vault.
- **C11:** deterministic artifact admission gate merged. Profile verification is only one of several required exact-item bindings.
- **C12/C14:** two independent Public Domain `open_corpus` items admitted under `managed_standard`, with bytes outside ordinary Git.
- **C15/C16:** the historical two-item snapshot is frozen and measured `insufficient`.
- **C17:** corpus expansion active. Any additional item must independently pass the same gates and cannot mutate C15.

## Phone-photo boundary

A user-provided phone photo is not automatically an `open_corpus` item. Under the current policy it normally falls under `sensitive_custody` and therefore requires a real `high_assurance_vault` pass. Until such evidence exists, it remains fail-closed. Synthetic relabeling or image transformation cannot be used to fabricate real phone-photo coverage.

## Safety statement

No governance/profile implementation by itself introduces artifact bytes or grants artifact-specific permission. No profile pass authorizes model training, calibration, publication, demonstration, synthetic derivation, or Stage 2. Stage 2 remains blocked until the complete Stage 1 exit gate is accepted.
