# Stage 1 Coverage and Bias Register

**Status:** Zero-state planning register; empirical measurements unavailable  
**Stage:** Stage 1C / C2 metadata planning  
**Parent issue:** #47  
**Realized corpus size:** 0  
**Coverage measurements:** Not yet measured

## 1. Purpose

This register defines the Stage 1 coverage dimensions and disclosure discipline before a realized corpus exists. It must distinguish planned coverage targets, observed evidence and unresolved gaps.

No category is considered representative merely because it appears in this register.

## 2. Current coverage state

| Dimension | Planned category | Current state | Evidence |
|---|---|---|---|
| Notation layout | Staff notation | `not_yet_measured` | No realized items |
| Notation layout | Guitar TAB | `not_yet_measured` | No realized items |
| Notation layout | Mixed score/TAB | `not_yet_measured` | No realized items |
| Capture/source condition | Clean source | `not_yet_measured` | No realized items |
| Capture/source condition | Scanned/degraded source | `not_yet_measured` | No realized items |
| Capture/source condition | Phone-captured source | `not_yet_measured` | No realized items |
| Degradation coverage | Blur / motion blur | `not_yet_measured` | No realized items |
| Degradation coverage | Skew / perspective | `not_yet_measured` | No realized items |
| Degradation coverage | Shadow / uneven illumination | `not_yet_measured` | No realized items |
| Degradation coverage | Glare | `not_yet_measured` | No realized items |
| Degradation coverage | Low contrast / background variation | `not_yet_measured` | No realized items |
| Degradation coverage | Noise / compression artifacts | `not_yet_measured` | No realized items |

The degradation rows are planning dimensions for later measurement. They do not authorize Stage 2 metric implementation or threshold tuning.

## 3. Current known gaps

Because the corpus contains zero realized items, the following gaps are confirmed:

- staff-notation representation is unknown;
- guitar-TAB representation is unknown;
- mixed-layout representation is unknown;
- scan-condition distribution is unknown;
- phone-capture distribution is unknown;
- degradation-frequency distribution is unknown;
- source-family diversity is unknown;
- held-out coverage is not realized;
- no empirical comparison between original and restoration output is available from the Stage 1 corpus.

## 4. Bias register

At zero state, empirical bias cannot be measured. The entries below are **planning risks**, not measured findings.

| Risk code | Potential bias source | Current evidence | Required later check |
|---|---|---|---|
| `source_selection_bias` | Available/authorized sources may overrepresent easily obtainable material | None yet | Compare source-family and rights-basis distributions |
| `notation_layout_bias` | One of staff, TAB or mixed layouts may dominate | None yet | Count and report each layout class |
| `capture_condition_bias` | Clean scans may dominate over difficult phone photos, or vice versa | None yet | Report capture/source-condition distribution |
| `degradation_bias` | Certain degradation classes may be absent or overrepresented | None yet | Report per-degradation counts and co-occurrence |
| `held_out_coverage_bias` | Held-out split may not mirror relevant evaluation diversity | None yet | Compare coverage between eligible development/evaluation and held-out families without leakage |
| `source_family_leakage_risk` | Related pages or derivatives could cross splits | Contract protection exists; no realized split | Verify source-family isolation before snapshot freeze |

## 5. Measurement rules for later corpus realization

When eligible items exist, coverage reporting must:

- use actual validated catalog/snapshot metadata rather than manual estimates;
- count source families as well as items where duplication could distort coverage;
- keep held-out items isolated from tuning and development;
- record unknown/unclassified values explicitly instead of assigning guessed classes;
- distinguish real and separately authorized synthetic items;
- preserve rights/privacy restrictions while reporting aggregate metadata;
- avoid exposing personal identities, local paths or secret-bearing custody details.

## 6. Bias interpretation rules

A future report must not equate balanced counts with absence of bias. It must separately consider:

- authorization-driven source selection;
- notation-layout imbalance;
- capture-device and capture-condition imbalance;
- degradation imbalance;
- source-family duplication;
- held-out representativeness limits.

Any claim that restoration improves OMR or musical correctness belongs to later evidence and cannot be inferred from this Stage 1 planning register.

## 7. Exit condition for this register

This zero-state register becomes an empirical Stage 1 coverage/bias report only after:

1. a compliant vault has passed;
2. authorized items are realized;
3. eligible splits are assigned without source-family leakage;
4. aggregate counts can be derived from validated metadata;
5. the findings are reviewed and their limitations recorded.

Until then, all empirical fields remain `not_yet_measured`.

## 8. Safety statement

This document creates no artifact, permission, split, threshold, model-training authorization or Stage 2 capability.
