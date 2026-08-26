# Stage 1C Current Status

**Status:** ACTIVE — C17 corpus expansion  
**As of:** 2026-08-26  
**Parent issue:** #47  
**Historical frozen baseline:** C15/C16  
**Active implementation slice:** C17A / PR #68 (Draft)  
**Stage 1 exit:** BLOCKED  
**Stage 2 entry:** BLOCKED

## 1. Purpose

This document is the repository-visible current-status reconciliation for Stage 1C. It does not replace the historical C12-C16 evidence records or mutate the C15 frozen snapshot. When an older status paragraph conflicts with this document, the current repository state, accepted ADRs, merged implementation evidence, and the exact open-PR state remain authoritative.

## 2. Merged Stage 1C baseline

Stage 1A metadata governance is complete and Stage 1B is formally closed. Stage 1C is active under Issue #47.

The following Stage 1C slices are merged on `main`:

- C5 — governance convergence;
- C6 — catalog `1.3.0` risk-tiered storage-profile migration;
- C7 — deterministic eligibility resolver;
- C8 — managed-standard operational verification contract;
- C9 — managed-restricted operational verification contract;
- C10 — high-assurance compatibility contract;
- C11 — deterministic artifact admission gate;
- C12 — first real authorized development artifact;
- C13 — structural corpus readiness gate;
- C14 — independent held-out artifact and two-item realized corpus;
- C15 — digest-addressed immutable snapshot freeze;
- C16 — deterministic frozen-snapshot coverage/gap/bias evaluation.

The earlier statement that the machine-readable ADR 0016 migration is still pending is obsolete. Catalog `1.3.0`, eligibility/profile validation, and the C8-C11 operational/admission mechanisms are already implemented and merged.

## 3. Binding custody model

ADR 0016 remains the binding risk-tiered custody architecture:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when the exact artifact terms permit it;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved, rejected, contradictory, or incomplete governance → `blocked`.

The G4 Stage 1 purpose allowlist remains limited to:

- `quality_evaluation` for development material;
- `held_out_evaluation` for held-out material.

Artifact rights, privacy, dataset review, retention, purpose, provenance, exact digest/size binding, storage-profile verification, and C11 admission remain independent fail-closed gates. Provider brand, possession of bytes, teacher approval, or public-domain status of the underlying musical work alone never implies admission.

## 4. Historical C15/C16 baseline

C15 froze the two-item Stage 1 corpus as an immutable historical snapshot. C16 measured that exact frozen snapshot and concluded `insufficient`.

Historical C16 corpus:

- 2 real items;
- 12 pages;
- development: 1 item / 4 pages;
- held out: 1 item / 8 pages;
- staff notation: 2 items;
- guitar TAB: 0 items;
- combined staff/TAB: 0 items;
- scanned PDF: 2 items;
- phone photo: 0 items;
- non-`none` degradation coverage: 0 items.

Historical C16 gap codes remain:

- `coverage.missing-combined-staff-tab`;
- `coverage.missing-degraded-source`;
- `coverage.missing-guitar-tab`;
- `coverage.missing-phone-photo`;
- `coverage.single-item-development`;
- `coverage.single-item-held-out`;
- `coverage.two-item-corpus`.

C17 work must not rewrite these historical counts. Any expanded corpus requires a new versioned snapshot and a new deterministic coverage evaluation.

## 5. C17A / PR #68

PR #68 is the current C17A implementation slice and remains Draft.

The corrected exact C17A head before this documentation reconciliation is:

`3424cc22d686b1d08ec0ff1c6be1d372b1ff4146`

The C17A artifact is a rights-clean Public Domain PNG admitted only for `quality_evaluation` under `open_corpus` / `managed_standard`. Its notation taxonomy is intentionally:

```text
combined_staff_tab
```

It is **not** also classified as standalone `guitar_tab`. The Codex P2 review finding that the original metadata would overstate future coverage was accepted and corrected. Standalone guitar TAB therefore remains a separate missing target.

The exact artifact metadata is:

- SHA-256: `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- byte size: `34636`;
- format: PNG;
- pages: 1;
- storage profile: `managed_standard`;
- artifact bytes in ordinary Git: 0;
- model training: not authorized;
- calibration: not authorized;
- publication/demonstration: not authorized;
- Stage 2: not authorized.

The corrected canonical dataset-item digest bound by the admission request is:

`5deed5fac92ff98e10177eb1ff45d742e15863d58235a18af2dedcb4b1880449`

Repository validation Run #147 (`32895593925`) succeeded for the corrected C17A head on Python 3.11 and 3.12. The review thread is resolved. Because the head changed after the earlier review cycle, repository governance still requires a fresh Ready-for-review gate and a later exact-head merge gate.

## 6. Phone-photo boundary

A user-provided real phone photograph remains fail-closed because it maps to `sensitive_custody` and therefore requires a real `high_assurance_vault` verification. The current C10 compatibility evidence proves structural compatibility only; it explicitly does not prove a real vault and does not authorize sensitive artifact onboarding.

A phone-photo gap must not be fabricated by synthetically converting an existing score or by relabeling a non-phone source. It remains missing until independently authorized real evidence exists.

## 7. Current next work

C17 must continue corpus expansion without mutating the C15 historical freeze. The remaining priority dimensions are:

1. standalone rights-clean guitar TAB;
2. real non-clean/degraded source material;
3. real phone-captured sheet music with an admissible custody path;
4. additional independent development and held-out source families.

After enough independently admitted material exists, create a **new versioned snapshot**, re-run deterministic coverage/bias evaluation, reconcile the Stage 1 dataset card and exit evidence, and only then decide whether Stage 1 exit is supportable.

## 8. Safety statement

This status reconciliation grants no new artifact permission, changes no historical snapshot, stores no score/image/PDF bytes in Git, starts no model training or calibration, and does not authorize Stage 2, DocRes, the multi-engine comparator, the selector, the ST Restore image model, production deployment, or downstream music-application integration.
