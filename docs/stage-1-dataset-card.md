# Stage 1 Dataset Card

**Status:** Historical C15/C16 baseline preserved; expanded-v2 evidence under PR #81 acceptance  
**As of:** 2026-09-02  
**Stage:** Stage 1C  
**Parent issue:** #47  
**Artifact bytes stored in ordinary Git:** 0  
**Model training authorized:** No  
**Stage 2 entry:** BLOCKED

## 1. Scope and evidence versions

This card distinguishes two evidence generations that must not be conflated.

### Historical C15/C16 baseline — immutable

`dataset.snapshot.stage1c-freeze.v1` remains the historical frozen snapshot, with canonical snapshot SHA-256 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`. It contains 2 real items / 12 pages and C16 concluded `insufficient`. Neither the historical catalog, frozen snapshot nor C16 report is rewritten by C17.

### Expanded-v2 evidence — PR #81, not yet production evidence

PR #81 deterministically builds and now commits a new five-item aggregate from already admitted item-level evidence. Until the committed v2 files pass fresh exact-head CI, review/thread/head gates, merge and post-merge validation, this evidence remains in-progress rather than `main` production truth.

## 2. Expanded-v2 membership

The required membership is exactly:

- `dataset.item.imslp799143-beethoven-op48-no3.v1` — development;
- `dataset.item.wikimedia-guitar-technical-exercise-no1.v1` — development;
- `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` — development;
- `dataset.item.imslp82860-chopin-op69.v2` — held out;
- `dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1` — held out.

`dataset.item.imslp82860-chopin-op69.v1` is excluded. Metadata v2 represents the same exact Chopin artifact and replaces v1 for this aggregate; both versions must never be counted as independent real items.

## 3. Corpus structure

The deterministic expanded-v2 evidence reports:

| Dimension | Observation |
|---|---:|
| Real items | 5 |
| Synthetic items | 0 |
| Development items | 3 |
| Development source families | 3 |
| Held-out items | 2 |
| Held-out source families | 2 |
| Total source families | 5 |
| Total pages | 16 |
| Staff notation items | 3 |
| Guitar TAB items | 1 |
| Combined staff/TAB items | 1 |
| Scanned-PDF items | 2 |
| Phone-photo items | 1 |
| Items with non-`none` degradation metadata | 1 |

Development and held-out source-family sets are disjoint. Exact artifact SHA-256 values are unique across selected items.

## 4. Rights, privacy, custody and purpose boundary

Every selected item is backed by its own admitted artifact metadata and evidence. The aggregate does not relax item-level gates.

- open-corpus items remain under `managed_standard`;
- the C17D deidentified phone-photo derivative remains `restricted_corpus -> managed_restricted`;
- development permissions remain `quality_evaluation` only where granted;
- held-out permissions remain `held_out_evaluation` only where granted;
- no aggregate membership creates model-training, calibration, publication or demonstration permission.

Public availability, possession of bytes, provider identity or teacher approval never substitutes for exact-artifact rights/privacy/custody/purpose admission.

## 5. Coverage interpretation

The expanded-v2 evidence closes the explicit historical target gaps for:

- staff notation;
- standalone guitar TAB;
- combined staff+TAB;
- scanned PDF;
- phone photo;
- non-`none` degradation;
- one-item development/held-out thinness;
- two-item-corpus size.

That result is a metadata coverage observation only. It does not establish that the corpus is representative, unbiased, musically correct, restoration-effective, or OMR-improving.

The coverage report remains `review_required` with `stage1ExitSupported=false` and `stage2EntrySupported=false`. Therefore Stage 2 entry remains **BLOCKED**.

## 6. Authorized and prohibited uses

Authorized use remains item-specific and purpose-bound. This card does not authorize:

- model training;
- quality or safety calibration;
- publication or demonstration;
- synthetic derivation;
- Stage 2 execution.

## 7. Acceptance boundary

The deterministic v2 catalog/snapshot/report are committed and CI is wired to committed-evidence `--check`. PR #81 must still pass fresh exact-head Python 3.11/3.12 CI, focused regressions, review/thread/head gates, merge, and post-merge `main` CI.

Only after those steps may Stage 1 final exit be evaluated separately. Stage 2 remains BLOCKED until explicit Stage 1 final PASS.
