# Stage 1C Deterministic Eligibility Resolver

**Status:** C7 implementation candidate  
**Stage:** Stage 1C  
**Parent:** Issue #47  
**Architecture:** ADR 0016 risk-tiered artifact custody  
**Runtime restoration impact:** None

## Purpose

C7 removes manual trust from `eligibilityClass`. The repository still records the declared class, but validation now derives the **minimum required custody class** from already-validated evidence and rejects any declaration that is weaker.

This resolver classifies storage risk. It does **not** authorize onboarding, activate a purpose, approve a provider, verify a storage environment, or complete Stage 1.

## Deterministic evidence inputs

The resolver consumes only structured, already validated fields:

- artifact state;
- source kind;
- usage-basis code;
- rights-review status;
- privacy classification and privacy-review status;
- dataset-review status;
- active typed permission restrictions.

No composer name, work title, filename, provider brand, local path, free text, URL or human identity participates in the decision.

## Source / usage-basis binding

The exact machine pairs are:

| sourceKind | usageBasisCode |
| --- | --- |
| `project_authored` | `project_authored` |
| `public_domain` | `public_domain` |
| `licensed` | `license_grant` |
| `user_provided` | `user_authorization` |
| `synthetic` | `synthetic_derivation` |

Any contradictory pair fails closed.

## Minimum-class rules

The baseline evidence-derived floor is:

- metadata-only → `blocked`;
- unresolved rights/privacy/review → `blocked`;
- personal/student or user-provided → `sensitive_custody`;
- deidentified or licensed → at least `restricted_corpus`;
- validated public-domain/project-authored/synthetic with privacy `none` → at least `open_corpus`.

Typed restrictions can only raise this floor:

- storage allowlist excluding `managed_standard` → at least `restricted_corpus`;
- storage allowlist permitting only `high_assurance_vault` → `sensitive_custody`;
- environment restriction → at least `restricted_corpus`;
- external-export denial → at least `restricted_corpus`;
- retention-not-after restriction → at least `restricted_corpus`.

A split allowlist does not itself change confidentiality/custody risk.

## Escalation and downgrade rule

Declared eligibility may equal the evidence-derived minimum or be stronger:

```text
open_corpus < restricted_corpus < sensitive_custody
```

Examples:

- evidence requires `open_corpus`, declaration `sensitive_custody` → allowed;
- evidence requires `restricted_corpus`, declaration `open_corpus` → rejected;
- evidence requires `sensitive_custody`, declaration `restricted_corpus` → rejected.

This preserves the C6 legacy migration rule: historical `custody_external` material conservatively mapped to `sensitive_custody/high_assurance_vault` is never weakened merely because later evidence would permit a lower minimum.

## Separation from admission authorization

Eligibility is not admission. An artifact still requires the independent Stage 1C gates for:

- exact-artifact rights/provenance;
- current allowed purpose;
- dataset review;
- retention;
- split policy;
- selected profile operational verification;
- digest/byte-size/storage evidence;
- revocation/deletion rules.

C8 and C9 remain responsible for operational verification of `managed_standard` and `managed_restricted`. C10 retains high-assurance compatibility verification. C7 approves no provider and onboards zero bytes.

## Safety invariants

- no real score/TAB/PDF/image bytes are added;
- no provider/account/path/credential/secret is added;
- Stage 1 purpose allowlist is unchanged;
- model training remains unauthorized;
- Stage 2 remains blocked;
- storage risk can escalate but cannot be silently downgraded;
- resolver output is deterministic and does not mutate input metadata.
