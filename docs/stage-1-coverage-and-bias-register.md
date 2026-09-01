# Stage 1 Coverage and Bias Register

**Status:** Historical C16 register preserved; expanded-v2 candidate requires acceptance  
**As of:** 2026-09-02  
**Stage:** Stage 1C  
**Parent issue:** #47  
**Stage 1 final exit:** BLOCKED  
**Stage 2 entry:** BLOCKED

## 1. Measurement boundary

Coverage and bias findings in this repository are metadata-derived. They do not inspect score pixels, run restoration, measure OMR accuracy or establish musical correctness.

Two evidence versions coexist deliberately:

- historical C16: `dataset.snapshot.stage1c-freeze.v1` + `coverage-bias-report.v1.json`, immutable and `insufficient`;
- PR #81 expanded candidate: `dataset.snapshot.stage1c-expanded.v2` + `coverage-bias-report.v2.json`, in-progress until committed, checked, merged and post-merge validated.

Historical evidence is not rewritten when later coverage improves.

## 2. Historical C16 result — immutable

Historical C16 measured 2 real items / 12 pages and produced the following gap codes:

- `coverage.missing-combined-staff-tab`
- `coverage.missing-degraded-source`
- `coverage.missing-guitar-tab`
- `coverage.missing-phone-photo`
- `coverage.single-item-development`
- `coverage.single-item-held-out`
- `coverage.two-item-corpus`

Historical deterministic sufficiency remains `insufficient`. C16 report SHA-256 remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## 3. Expanded-v2 candidate coverage

The PR #81 deterministic candidate selects 5 real items / 0 synthetic items with 3 development source families and 2 held-out source families.

| Coverage target | Observed items | Candidate state |
|---|---:|---|
| `notation.staff` | 3 | `covered` |
| `notation.guitar_tab` | 1 | `covered` |
| `notation.combined_staff_tab` | 1 | `covered` |
| `capture.scanned_pdf` | 2 | `covered` |
| `capture.phone_photo` | 1 | `covered` |
| `degradation.non_none` | 1 | `covered` |

Candidate aggregate counts:

- real items: 5;
- synthetic items: 0;
- development: 3 items / 3 source families / 7 pages;
- held out: 2 items / 2 source families / 9 pages;
- total pages: 16;
- source families: 5;
- unique exact artifact digests: 5;
- cross-split source-family leakage: none;
- Chopin v1/v2 double-counting: prohibited; v2 selected once, v1 excluded.

The seven historical C16 gap codes are absent from the v2 candidate. This observation does not alter the historical C16 report.

## 4. Candidate bias findings

The deterministic v2 candidate currently records:

| Finding code | Candidate state | Evidence basis |
|---|---|---|
| `capture_condition_concentration` | `controlled` | multiple capture kinds |
| `degradation_coverage_gap` | `controlled` | non-`none` degradation present |
| `held_out_coverage_limit` | `controlled` | two held-out source families |
| `notation_layout_concentration` | `controlled` | staff, TAB and combined layouts present |
| `source_family_leakage_risk` | `controlled` | distinct source families and digests across splits |
| `source_selection_concentration` | `observed` | public-domain majority with one licensed item |

`controlled` means the specific deterministic concentration check no longer triggers. It does **not** mean absence of bias has been established.

## 5. Sufficiency and interpretation

The expanded-v2 candidate deliberately reports:

- `sufficiency.state = review_required`;
- `requiresCorpusExpansion = false`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

Therefore the following claims remain unsupported:

- corpus representativeness;
- absence of bias;
- restoration effectiveness;
- OMR improvement;
- musical correctness;
- training/calibration readiness;
- Stage 1 final PASS;
- Stage 2 entry.

## 6. Machine-readable evidence boundary

Historical machine-readable evidence remains:

- `evidence/stage1c/corpus/catalog.v1.json`;
- `evidence/stage1c/corpus/snapshot.freeze.v1.json`;
- `evidence/stage1c/corpus/coverage-bias-report.v1.json`.

PR #81 is responsible for adding, without mutating the historical files:

- `evidence/stage1c/corpus/catalog.v2.json`;
- `evidence/stage1c/corpus/snapshot.expanded.v2.json`;
- `evidence/stage1c/corpus/coverage-bias-report.v2.json`.

The final PR head must validate the committed v2 evidence with `python tools/build_stage1_expanded_snapshot.py --check` on Python 3.11 and 3.12.

## 7. Safety statement

This register grants no new permission, changes no historical evidence, stores no real score/PDF/image corpus bytes in ordinary Git, authorizes no model training or calibration, and does not start Stage 2.
