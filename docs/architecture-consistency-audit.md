# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Active PR:** #84 / `stage2-complete-quality-analysis`  
**Stage 1:** COMPLETE / PASS  
**Stage 2:** ACTIVE  
**Stage 3:** BLOCKED pending Stage 2 exit PASS

## Purpose

This audit separates immutable historical evidence, accepted production-main truth and in-progress PR state. Authority order is merged `main` plus accepted deterministic evidence over stale status prose. Exact-head CI becomes stale after head movement.

## Fresh-read findings

| Area | Result | Interpretation |
|---|---|---|
| Stage 1 final exit | PASS / EFFECTIVE | PR #82 merged; post-merge Run #203 green on Python 3.11/3.12 |
| Stage 1 historical C15/C16 | PRESERVED | historical C16 remains `insufficient` for its original snapshot |
| Expanded-v2 Stage 1 evidence | ACCEPTED | 5 real / 0 synthetic, 3 development families, 2 held-out families, no leakage/digest duplication |
| Ordinary Git artifact custody | PASS | zero real corpus score/PDF/image bytes under Stage 1 evidence |
| Stage 2 entry | SATISFIED | accepted purpose is Complete Quality Analysis evaluation |
| Stage 2 Issue #83 | OPEN / ACTIVE | current stage tracking |
| PR #84 | OPEN / DRAFT | initial deterministic OpenCV quality-analysis core plus docs reconciliation |
| PR #84 core head `0abc5ec9…` | VERIFIED | Run #205 passed Python 3.11/3.12, Stage 2 validator, full tests and compile |
| Architecture/status docs | RECONCILED IN CURRENT PR SLICE | Stage 1 COMPLETE, Stage 2 ACTIVE, Stage 3 BLOCKED |
| Stage 2 thresholds | UNCALIBRATED | engineering defaults only; no held-out tuning |
| Stage 3 | BLOCKED | requires separate Stage 2 exit PASS |

## Stage 1 evidence retained

Canonical expanded-v2 digests:

- catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`;
- snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`;
- report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Exact C17 bindings remain:

- C17A `36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb`;
- C17B `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`;
- C17C `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`;
- C17D `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`.

Historical C15 snapshot canonical SHA-256 remains `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; historical C16 report SHA-256 remains `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Stage 2 architecture truth

The pre-Stage-2 inspector exposed quality finding categories but intentionally left most raster pixel quality `not_assessed`. PR #84 closes that measurement gap with `src/st_score_restore/quality_analysis.py` while preserving the existing OpenCV restoration/safety boundaries.

The analyzer is deterministic and source-bound. It measures orientation, skew, page/perspective geometry, crop risk, blur, glare, shadow, uneven lighting, noise, JPEG compression evidence, low resolution/DPI and geometric staff/TAB visibility.

It does not perform OMR, musical inference, symbol completion or source modification. Digital PDFs remain vector-preservation territory. Scanned/hybrid PDF pixel analysis remains deferred to the Stage 3 renderer boundary.

## CI and PR #84 gate

Run #205 (`33589252594`) succeeded on PR #84 head `0abc5ec924b65fdec6548e75923b1e7456ff4822` for Python 3.11 and 3.12. It validated Stage 1 gates, the new Stage 2 contract, all tests and compile.

This documentation/architecture reconciliation moves the PR head. Therefore Run #205 is historical verification of the code core, not final merge evidence after the reconciliation commit.

Final PR #84 merge requires:

1. new exact-head Python 3.11/3.12 CI success;
2. clean reviews and review threads;
3. fresh base/head read;
4. Draft → Ready only if gates remain clean;
5. merge exact verified head;
6. post-merge main CI success.

## Stage 2 exit boundary

PR #84 merge is not Stage 2 final exit. Before Stage 2 can PASS, the accepted evaluation corpus must be exercised through approved custody without moving real bytes into ordinary Git. Execution evidence must be deterministic, source-digest-bound, reviewable and preserve held-out non-tuning. Known limitations must remain explicit.

Stage 3 remains BLOCKED until a separate Stage 2 exit acceptance is PASS.
