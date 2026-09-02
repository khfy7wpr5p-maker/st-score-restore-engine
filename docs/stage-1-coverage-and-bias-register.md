# Stage 1 Coverage and Bias Register

**Status:** ACCEPTED Stage 1 evidence; historical C16 preserved  
**As of:** 2026-09-02  
**Stage 1 final exit:** PASS / COMPLETE  
**Stage 2:** ACTIVE  
**Stage 3:** BLOCKED pending Stage 2 exit PASS

## Measurement boundary

Coverage and bias findings here are metadata-derived. They do not inspect musical correctness, prove restoration effectiveness or measure OMR accuracy. Stage 2 now performs deterministic visual quality analysis separately.

Two evidence generations coexist deliberately:

- historical C16: immutable `snapshot.freeze.v1` + `coverage-bias-report.v1.json`, result `insufficient`;
- accepted expanded-v2: `snapshot.expanded.v2.json` + `coverage-bias-report.v2.json`, accepted through separate Stage 1 exit governance evidence.

Historical evidence is not rewritten when later coverage improves.

## Historical C16 result

Historical C16 measured 2 real items / 12 pages and recorded:

- `coverage.missing-combined-staff-tab`
- `coverage.missing-degraded-source`
- `coverage.missing-guitar-tab`
- `coverage.missing-phone-photo`
- `coverage.single-item-development`
- `coverage.single-item-held-out`
- `coverage.two-item-corpus`

C16 report SHA-256 remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Accepted expanded-v2 coverage

Expanded-v2 contains 5 real items / 0 synthetic items with 3 development source families and 2 held-out source families.

| Coverage target | Observed items | State |
|---|---:|---|
| `notation.staff` | 3 | `covered` |
| `notation.guitar_tab` | 1 | `covered` |
| `notation.combined_staff_tab` | 1 | `covered` |
| `capture.scanned_pdf` | 3 | `covered` |
| `capture.phone_photo` | 1 | `covered` |
| `degradation.non_none` | 1 | `covered` |

Aggregate invariants:

- development: 3 items / 3 source families / 7 pages;
- held out: 2 items / 2 source families / 9 pages;
- total pages: 16;
- exact artifact digests unique;
- cross-split source-family leakage: none;
- Chopin v2 selected once, v1 excluded.

The seven historical C16 gap codes are absent from expanded-v2. This does not alter historical C16.

Canonical v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

## Bias findings

Expanded-v2 records:

| Finding code | State | Interpretation |
|---|---|---|
| `capture_condition_concentration` | `controlled` | multiple capture kinds present |
| `degradation_coverage_gap` | `controlled` | non-`none` degradation present |
| `held_out_coverage_limit` | `controlled` | two held-out source families |
| `notation_layout_concentration` | `controlled` | staff, TAB and combined layouts present |
| `source_family_leakage_risk` | `controlled` | split families/digests separated |
| `source_selection_concentration` | `observed` | public-domain majority with one licensed item |

`controlled` means the specific deterministic concentration check no longer triggers; it does not establish absence of bias.

## Sufficiency interpretation

The expanded-v2 automatic report deliberately remains:

- `sufficiency.state = review_required`;
- `requiresCorpusExpansion = false`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

Stage 1 PASS is therefore a separate evidence-bound governance acceptance and not a rewrite of automatic report fields.

Unsupported claims remain: corpus representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission and calibration permission.

## Stage 2 boundary

Stage 2 may use the accepted corpus for the approved quality-analysis evaluation purpose through approved custody. Held-out items remain evaluation-only and cannot tune thresholds. Stage 2 metrics and results do not retroactively change Stage 1 evidence.
