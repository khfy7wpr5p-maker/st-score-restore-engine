# Stage 1 Dataset Card

**Status:** ACCEPTED / Stage 1 COMPLETE  
**As of:** 2026-09-02  
**Accepted main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Artifact bytes stored in ordinary Git:** 0  
**Model training authorized:** No  
**Calibration authorized:** No  
**Stage 2 evaluation use:** Active / purpose-bound

## Evidence generations

Historical C15/C16 remains immutable. `dataset.snapshot.stage1c-freeze.v1` contains the original two-item corpus and historical C16 concluded `insufficient`. That historical evidence is not rewritten.

Expanded-v2 is the accepted Stage 1 aggregate. Its machine-readable evidence is:

- `evidence/stage1c/corpus/catalog.v2.json`;
- `evidence/stage1c/corpus/snapshot.expanded.v2.json`;
- `evidence/stage1c/corpus/coverage-bias-report.v2.json`;
- `evidence/stage1c/corpus/stage1-exit-acceptance.v1.json`.

## Accepted membership

- `dataset.item.imslp799143-beethoven-op48-no3.v1` — development;
- `dataset.item.wikimedia-guitar-technical-exercise-no1.v1` — development;
- `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` — development;
- `dataset.item.imslp82860-chopin-op69.v2` — held out;
- `dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1` — held out.

Chopin metadata v1 is excluded from expanded-v2; v2 represents the same exact artifact and replaces v1 for this aggregate.

## Corpus structure

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
| Phone-photo items | 1 |
| Non-`none` degradation items | 1 |

Development and held-out source-family sets are disjoint. Selected exact artifact SHA-256 values are unique.

Canonical expanded-v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

## Rights, privacy, custody and purpose

Every selected item remains governed by its own admitted exact-artifact evidence. Aggregate membership grants no new rights.

- open-corpus items use `managed_standard`;
- C17D remains `restricted_corpus -> managed_restricted` and deidentified;
- development use remains `quality_evaluation` where granted;
- held-out use remains `held_out_evaluation` where granted;
- model training and calibration are not inferred or activated;
- real corpus bytes remain outside ordinary Git.

## Coverage and limitations

Expanded-v2 covers the tracked Stage 1 targets for staff notation, standalone guitar TAB, combined staff+TAB, scanned PDF, phone photo and non-`none` degradation. The historical seven C16 gap codes are absent from the expanded-v2 report.

This does not establish representativeness, absence of bias, musical correctness, restoration effectiveness or OMR improvement. `source_selection_concentration` remains an accepted known limitation.

The automatic coverage report remains `review_required` with `stage1ExitSupported=false` and `stage2EntrySupported=false`; Stage 1 PASS is recorded separately in the governance acceptance evidence.

## Stage 2 use boundary

The accepted corpus may be exercised for the expressly accepted Stage 2 Complete Quality Analysis evaluation purpose through approved custody. Held-out items are evaluation-only and must not be used to tune Stage 2 thresholds. No real artifact bytes may be copied into ordinary Git for Stage 2 execution.
