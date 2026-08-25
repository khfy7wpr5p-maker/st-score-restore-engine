# Stage 1 Coverage and Bias Register

**Status:** Metadata-derived empirical register; current corpus insufficient  
**Stage:** Stage 1C / C16  
**Parent issue:** #47  
**Frozen snapshot:** `dataset.snapshot.stage1c-freeze.v1`  
**Snapshot SHA-256:** `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`  
**Realized corpus size:** 2 items / 12 pages

## 1. Measurement boundary

This register is derived from validated Stage 1 catalog and frozen-snapshot metadata. It reports observed metadata only. It does not inspect score pixels, run OpenCV, execute restoration, measure OMR accuracy, or establish musical correctness.

## 2. Current coverage state

| Dimension | Planned category | Observed | State |
|---|---|---:|---|
| Notation layout | Staff notation | 2 items | `covered` |
| Notation layout | Guitar TAB | 0 items | `missing` |
| Notation layout | Combined staff/TAB | 0 items | `missing` |
| Capture/source condition | Scanned PDF | 2 items | `covered` |
| Capture/source condition | Phone photo | 0 items | `missing` |
| Degradation coverage | Any non-`none` degradation | 0 items | `missing` |
| Split coverage | Development | 1 item / 1 source family / 4 pages | `present_but_thin` |
| Split coverage | Held out | 1 item / 1 source family / 8 pages | `present_but_thin` |

The two realized items have distinct source families and distinct artifact digests. Cross-split source-family leakage is not present in the frozen snapshot.

## 3. Confirmed gap codes

- `coverage.missing-combined-staff-tab`
- `coverage.missing-degraded-source`
- `coverage.missing-guitar-tab`
- `coverage.missing-phone-photo`
- `coverage.single-item-development`
- `coverage.single-item-held-out`
- `coverage.two-item-corpus`

Current sufficiency decision: **`insufficient`**.

## 4. Bias and concentration register

| Finding code | State | Current evidence |
|---|---|---|
| `source_selection_concentration` | observed | 2/2 items use public-domain source basis |
| `notation_layout_concentration` | observed | 2/2 items are staff-only |
| `capture_condition_concentration` | observed | 2/2 items are scanned PDFs |
| `degradation_coverage_gap` | observed | 0 items contain a non-`none` degradation label |
| `held_out_coverage_limit` | observed | held-out split contains one source family |
| `source_family_leakage_risk` | controlled | development and held-out assignments use distinct families and digests |

These findings demonstrate concentration and coverage limits. They do not prove an absence or presence of every possible bias mechanism.

## 5. Aggregate counts

- real items: 2;
- synthetic items: 0;
- source families: 2;
- development items: 1;
- held-out items: 1;
- total pages: 12;
- staff items: 2;
- guitar-TAB items: 0;
- combined staff/TAB items: 0;
- scanned-PDF items: 2;
- phone-photo items: 0;
- items with non-clean degradation metadata: 0.

## 6. Interpretation rules

The current report must not be interpreted as evidence that:

- the corpus is representative;
- notation/layout balance is adequate;
- capture-condition balance is adequate;
- degradation coverage is adequate;
- the held-out split is broad enough;
- restoration improves OMR or musical correctness;
- model training or calibration is authorized.

## 7. Required corpus expansion

Before Stage 1 exit can be considered, the corpus needs independently authorized additions that materially address the confirmed gaps. Priority dimensions are:

1. guitar TAB;
2. combined staff/TAB;
3. phone-captured sheet music;
4. non-clean/degraded material;
5. greater development and held-out source-family diversity.

Any new artifact must independently pass rights, privacy, dataset-review, purpose, custody, admission, and split-isolation controls. The current frozen snapshot is immutable; expansion requires a new versioned snapshot.

## 8. Machine-readable evidence

`evidence/stage1c/corpus/coverage-bias-report.v1.json` is the deterministic C16 report. `tools/evaluate_stage1_coverage_bias.py --check --require-insufficient` must reproduce it exactly from the validated catalog and frozen snapshot.

## 9. Safety statement

This register grants no new permission, changes no artifact bytes, authorizes no model training, activates no calibration, and does not start Stage 2.
