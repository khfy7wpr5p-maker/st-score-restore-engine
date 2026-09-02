# Stage 1C Current Status

**Status:** ACTIVE — expanded-v2 acceptance in progress  
**As of:** 2026-09-02  
**Parent issue:** #47 (issue body is stale until separately reconciled)  
**Historical frozen baseline:** C15/C16 — immutable  
**Current production main:** `53ae13d3a1b9bda08c79125674e1b7fca78ee8af`  
**Active work:** PR #81, Draft, branch `stage1c-expanded-snapshot-v2`  
**Stage 1 exit:** BLOCKED pending committed expanded-v2 evidence, exact-head CI, merge, post-merge CI and separate exit acceptance  
**Stage 2 entry:** BLOCKED

## 1. Authority and interpretation

Repository truth is ordered as follows: merged `main` + accepted deterministic evidence > stale status prose. An open PR, even with green CI, is in-progress and is not production truth. Historical C15/C16 evidence remains historical and must not be rewritten to make later C17 coverage appear retroactive.

## 2. Current production truth on main

Stage 1A metadata governance and Stage 1B custody/operations closure are complete. Stage 1C remains active.

The C17 expansion items currently admitted on `main` include:

- **C17A combined staff+TAB:** `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`, exact artifact SHA-256 `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`; taxonomy is `combined_staff_tab` only.
- **C17B standalone guitar TAB:** `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, exact artifact SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`, 84689 bytes, 2 pages, `open_corpus -> managed_standard`, `quality_evaluation` only.
- **C17C degraded held-out representation:** `dataset.item.imslp82860-chopin-op69.v2`, exact artifact SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, degradation `noise` only, held-out. Metadata v2 replaces v1 in any new aggregate snapshot; v1 and v2 must never be double-counted.
- **C17D deidentified phone photo:** `dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1`, exact derivative SHA-256 `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`, 647003 bytes, `phone_photo`, `restricted_corpus -> managed_restricted`, privacy `deidentified`, `held_out_evaluation` only.

The main merge chain contains C17D admission commit `806e01dd78ae0df8852b1f91bfaac7679f791ef6` and current main C17B merge `53ae13d3a1b9bda08c79125674e1b7fca78ee8af`.

Ordinary Git contains metadata/evidence only for real corpus artifacts; real score/PDF/image corpus bytes remain outside ordinary Git.

## 3. Historical C15/C16 baseline

C15 froze the original two-item corpus and C16 evaluated exactly that snapshot. These are immutable historical evidence:

- 2 real items / 12 pages;
- development: 1 item / 1 source family / 4 pages;
- held out: 1 item / 1 source family / 8 pages;
- C16 deterministic sufficiency: `insufficient`;
- C16 report SHA-256: `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

The historical C16 gap codes remain part of that historical report. C17 does not mutate or reinterpret them.

## 4. PR #81 — in-progress expanded-v2 evidence

PR #81 is Draft on `stage1c-expanded-snapshot-v2`. The last candidate-only verified head before committed evidence was `e733d19cf5cb64d86f70017118d8d06c6863c304`. Repository validation Run #177 (`33570409008`) completed successfully on Python 3.11 and 3.12 for that exact head.

Run #177 generated three workflow artifacts independently in both Python matrix jobs. Their file contents were verified byte-for-byte identical across 3.11 and 3.12. The deterministic candidate selects exactly five real items:

1. `dataset.item.imslp799143-beethoven-op48-no3.v1`
2. `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`
3. `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`
4. `dataset.item.imslp82860-chopin-op69.v2`
5. `dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1`

Candidate structure:

- real items: 5; synthetic items: 0;
- development: 3 items / 3 source families;
- held out: 2 items / 2 source families;
- no source-family leakage between splits;
- no duplicate exact artifact SHA-256;
- Chopin v1 excluded and v2 selected exactly once;
- staff, guitar TAB, combined staff+TAB, scanned PDF, phone photo and non-`none` degradation targets are all covered;
- the seven historical C16 gap codes are absent from the v2 candidate.

This does **not** establish representativeness, absence of bias, restoration effectiveness, OMR improvement or musical correctness.

## 5. Expanded-v2 acceptance boundary

The candidate coverage report deliberately remains:

- `sufficiency.state = review_required`;
- `stage1ExitSupported = false`;
- `stage2EntrySupported = false`.

Therefore an empty v2 coverage-gap list is not Stage 1 final PASS.

PR #81 must still:

1. commit `catalog.v2.json`, `snapshot.expanded.v2.json` and `coverage-bias-report.v2.json` as canonical versioned evidence;
2. replace candidate-only generation with deterministic committed-evidence `--check` validation;
3. add focused regression coverage for membership, split/source-family isolation, digest uniqueness, C17C v1/v2 dedup, historical immutability and zero artifact bytes in Git;
4. obtain fresh exact-head Python 3.11/3.12 CI after the final head is established;
5. reconcile review/thread/head movement gates;
6. merge only if all objective gates are clean;
7. pass post-merge `main` CI.

Any head movement invalidates Run #177 as exact-head merge evidence.

## 6. Stage 1 exit and Stage 2 boundary

Stage 1 exit is a separate acceptance decision after PR #81 merge and post-merge CI. It can PASS only with explicit, deterministic, reviewable evidence and no unresolved governance, custody, rights, privacy, source-family, digest, CI or review gate.

Stage 2 / OpenCV Complete Quality Analysis remains blocked until that final Stage 1 exit acceptance is PASS. No Stage 2 implementation or execution is authorized by this document.
