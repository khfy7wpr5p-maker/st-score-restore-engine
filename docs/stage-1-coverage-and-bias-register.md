# Stage 1 Coverage and Bias Register

**Status:** ACCEPTED Stage 1 evidence; historical C16 preserved  
**As of:** 2026-09-02  
**Stage 1 final exit:** PASS / COMPLETE  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective; final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253  
**Stage 4:** ENTRY ELIGIBLE / NOT STARTED

## Measurement boundary

Coverage and bias findings here are metadata-derived. They do not inspect musical correctness, prove restoration effectiveness or measure OMR accuracy. Later Stage 2/3 work does not retroactively change these Stage 1 measurements.

Two evidence generations coexist deliberately:

- historical C16: immutable `snapshot.freeze.v1` + `coverage-bias-report.v1.json`, result `insufficient`;
- accepted expanded-v2: `snapshot.expanded.v2.json` + `coverage-bias-report.v2.json`, accepted through separate Stage 1 exit governance evidence.

Historical evidence is not rewritten when later coverage or processing capability improves.

## Historical C16 result

Historical C16 measured 2 real items / 12 pages and recorded seven coverage gap codes. C16 report SHA-256 remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`; its bound C15 snapshot remains `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`.

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

- development 3 items / 3 families / 7 pages;
- held out 2 items / 2 families / 9 pages;
- total pages 16;
- exact artifact digests unique;
- cross-split source-family leakage none;
- Chopin v2 selected once, v1 excluded.

Canonical v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

## Bias findings

Expanded-v2 records controlled checks for capture condition, degradation coverage, held-out coverage, notation layout and source-family leakage, plus observed `source_selection_concentration`. `controlled` means the deterministic concentration check no longer triggers; it does not establish absence of bias.

## Sufficiency interpretation

The expanded-v2 automatic report deliberately remains:

- `sufficiency.state = review_required`;
- `requiresCorpusExpansion = false`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

Stage 1 PASS is therefore a separate evidence-bound governance acceptance and not a rewrite of automatic report fields.

Unsupported claims remain corpus representativeness, absence of bias, restoration effectiveness, OMR improvement, musical correctness, model-training permission and calibration permission.

## Later-stage boundary

Stage 2 subsequently completed PASS using approved custody for its authorized quality-analysis purpose. Stage 3 subsequently completed PASS at final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`, Run #253, using only its own purpose/custody boundaries; its Beethoven/Barley overlay does not alter this Stage 1 register or `catalog.v2.json`. Held-out data did not tune Stage 2/3 thresholds, page policy, resource limits or hardening constants. Stage 4 is entry eligible but has not started.
