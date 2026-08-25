# Stage 1 Dataset Card

**Status:** Realized and frozen; coverage insufficient for Stage 1 exit  
**Stage:** Stage 1C / C16 coverage-bias reconciliation  
**Parent issue:** #47  
**Realized dataset items:** 2  
**Realized pages:** 12  
**Frozen splits:** development + held_out  
**Artifact bytes stored in ordinary Git:** 0  
**Model training authorized:** No  
**Stage 2 authorized:** No

## 1. Purpose

This card describes the currently realized Stage 1 evaluation corpus after C12-C15 onboarding and digest-addressed snapshot freeze. It is bound to `dataset.snapshot.stage1c-freeze.v1`, canonical snapshot SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`.

The current G4 allowlist remains limited to `quality_evaluation` and `held_out_evaluation` in `stage1_offline`.

## 2. Realized corpus

The frozen snapshot contains exactly two independently admitted real items:

- development: 1 public-domain scanned PDF, 4 pages;
- held out: 1 independent public-domain scanned PDF, 8 pages.

Both items are staff-notation only, both use distinct source families and distinct artifact digests, both are classified `open_corpus`, and both are stored under `managed_standard` custody outside ordinary Git.

No real artifact byte, provider/account identifier, local path, credential, or secret-bearing storage detail is stored in repository metadata.

## 3. Snapshot and split boundary

The frozen snapshot has:

- `heldOutFrozen=true`;
- `trainingUseActivated=false`;
- zero revoked item IDs;
- one development source family;
- one held-out source family;
- no source-family or artifact-digest leakage across splits.

The development item grants only `quality_evaluation`; the held-out item grants only `held_out_evaluation`. Held-out data is not authorized for development, tuning, calibration, or training.

## 4. Source, rights and privacy boundary

Both realized items have approved exact-artifact public-domain rights evidence, privacy classification `none`, approved dataset review, immutable artifact digest/size metadata, and opaque custody references.

Possession of a file still does not imply rights or purpose authorization. Any future corpus expansion must pass the same item-level admission chain.

## 5. Coverage measurement

C16 derives aggregate coverage only from the validated catalog and frozen snapshot metadata. It does not inspect pixels and does not run restoration or OMR evaluation.

Observed counts:

| Dimension | Observed |
|---|---:|
| Real items | 2 |
| Development items | 1 |
| Held-out items | 1 |
| Total pages | 12 |
| Staff notation items | 2 |
| Guitar TAB items | 0 |
| Combined staff/TAB items | 0 |
| Scanned-PDF items | 2 |
| Phone-photo items | 0 |
| Items with non-`none` degradation metadata | 0 |

## 6. Coverage decision

Current coverage sufficiency is **INSUFFICIENT**.

Confirmed gap codes:

- `coverage.missing-combined-staff-tab`;
- `coverage.missing-degraded-source`;
- `coverage.missing-guitar-tab`;
- `coverage.missing-phone-photo`;
- `coverage.single-item-development`;
- `coverage.single-item-held-out`;
- `coverage.two-item-corpus`.

The corpus therefore does not establish representativeness and does not support Stage 1 final exit or Stage 2 entry.

## 7. Bias and limitation findings

The current metadata demonstrates concentration in several dimensions:

- all realized items are staff-only;
- all realized items are scanned PDFs;
- all realized items declare only `none` degradation;
- all realized items use a public-domain source basis;
- the held-out split contains only one source family.

Source-family leakage risk is controlled by the frozen split bindings, but absence of bias is **not** established. Balanced counts are not inferred, and no fairness, restoration-effectiveness, OMR-improvement, or musical-correctness claim is made.

## 8. Authorized and prohibited uses

Authorized for the realized items only as item-specific permissions allow:

- development item: quality evaluation;
- held-out item: held-out evaluation.

Not authorized by this card:

- model training;
- quality calibration;
- safety calibration;
- publication;
- demonstration;
- synthetic derivation;
- Stage 2 OpenCV quality-analysis execution.

## 9. Required next step

The current frozen snapshot must not be mutated to hide the observed gaps. Stage 1 requires additional independently authorized corpus items covering missing notation/layout, capture-condition, and degradation dimensions. Any expanded corpus requires a new versioned snapshot after item-level governance and split-isolation checks.

## 10. Safety statement

This card documents observed metadata only. It grants no new permission, stores no artifact bytes in Git, activates no training, performs no restoration, and does not authorize Stage 2.
