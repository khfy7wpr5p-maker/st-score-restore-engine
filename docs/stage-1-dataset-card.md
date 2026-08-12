# Stage 1 Dataset Card

**Status:** Zero-state planning record; no realized corpus yet  
**Stage:** Stage 1C / C2 metadata planning  
**Parent issue:** #47  
**Artifact bytes onboarded:** 0  
**Realized dataset items:** 0  
**Frozen splits:** 0  
**Model training authorized:** No

## 1. Purpose

This card records the intended Stage 1 evaluation-corpus boundary before any real or controlled-synthetic artifact is admitted to custody. It is a planning and disclosure document, not evidence that a dataset currently exists.

The current G4 allowlist permits only:

- `quality_evaluation`;
- `held_out_evaluation`.

The current environment is `stage1_offline` and the required storage class is `custody_external`.

## 2. Current zero state

No artifact byte has been onboarded for Stage 1C. No item is `external_available`, no item-specific purpose permission is active, and no real dataset split has been frozen.

The external custody environment required by Stage 1B has not yet been verified as compliant. Real or controlled-synthetic onboarding therefore remains blocked.

## 3. Intended content categories

The Stage 1 roadmap requires the realized corpus, when later authorized and admitted, to seek representative coverage of:

- staff notation;
- guitar TAB;
- mixed-layout score/TAB material;
- clean and degraded scans;
- phone-captured sheet-music material;
- relevant degradation classes that can later support quality evaluation.

These are coverage targets only. At zero state, none has an empirical item count.

## 4. Source, rights and privacy boundary

Every future included item must independently satisfy the existing Stage 1A governance contract. In particular:

- provenance must be auditable;
- rights review must be approved;
- privacy review must be acceptable;
- dataset review must be approved;
- purpose authorization must be item-specific, current and within the G4 allowlist;
- teacher approval must not be interpreted as dataset or training permission.

No rights, privacy or provenance fact may be inferred from possession of a file or from its appearance.

## 5. Storage and custody

Ordinary Git remains metadata-only. Artifact bytes, credentials, concrete local paths, provider URLs, account identifiers and secret-bearing storage details are prohibited from repository metadata.

Before the first item can become `external_available`, the selected offline vault must pass the accepted Stage 1B operational controls, including encryption, private-by-default access, role separation, audit-before-access, revocation/deletion, backup tombstones, anti-rollback restore checks and anti-resurrection behavior.

Current custody readiness: **BLOCKED / not yet verified**.

## 6. Splits

Current split state: **no realized split**.

The repository contract supports source-family isolation and later digest-bound snapshots, but a real split must not be frozen before eligible `external_available` items and their required approvals exist.

Held-out data, once realized, must remain isolated from tuning and development use.

## 7. Authorized and prohibited uses

### Currently permitted by G4

- quality evaluation;
- held-out evaluation.

### Not currently authorized

- model training;
- quality calibration;
- safety calibration;
- PDF-pipeline evaluation;
- publication;
- demonstration;
- synthetic derivation.

A future governance decision is required before any prohibited purpose can be activated.

## 8. Coverage and quality state

All empirical coverage, balance and bias measurements are currently `not_yet_measured` because the realized corpus contains zero items.

This card must not claim representativeness, fairness, OMR improvement, restoration effectiveness or musical correctness before evidence exists.

The companion `stage-1-coverage-and-bias-register.md` records the zero-state gaps and the dimensions that must later be measured.

## 9. Known limitations at zero state

- no compliant vault has been accepted;
- no artifact is available for evaluation;
- no item-level authorization set has been realized;
- no split is frozen;
- no empirical category coverage is known;
- no empirical degradation distribution is known;
- no empirical bias analysis is possible yet.

These are explicit blockers, not missing values to be guessed.

## 10. Update conditions

This card may move beyond zero state only when direct evidence exists for the claimed state. In particular:

1. the external custody gate passes;
2. each admitted item passes rights, privacy, dataset-review and purpose checks;
3. artifact digest/size and opaque custody references exist;
4. the repository metadata validates under the accepted contracts;
5. split and snapshot claims are supported by actual eligible items.

## 11. Safety statement

This document onboards no artifact bytes, grants no permission, creates no storage resource, freezes no split, activates no model training and does not start Stage 2.
