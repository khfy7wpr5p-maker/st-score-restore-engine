# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE + AUTHORIZED EXECUTION + PURPOSE GRANTS PRODUCTION-EFFECTIVE / REAL-CORPUS RUNNER IN PR #98  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Core merge main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Core post-merge CI:** Run #232 (`33615937390`) — Python 3.11 / 3.12 SUCCESS  
**Authorized-execution merge main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Authorized-execution post-merge CI:** Run #235 (`33618108204`) — Python 3.11 / 3.12 SUCCESS  
**Purpose-grant merge main:** `6ebe160309c562e9841a3c313d5ca507592f1386`  
**Purpose-grant post-merge CI:** Run #238 (`33620323970`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage3-real-corpus-runner`  
**Active PR:** #98 — Draft  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 exit PASS

## Production-effective Stage 3 boundary

The PDFium core, Stage 3 approved-custody execution boundary, and Beethoven/Barley purpose-grant overlay are production-effective. The pipeline uses `pypdfium2==5.13.0`, exact source SHA-256 identity, stable page order, raster-only rendering, vector preservation, hybrid preservation/review, original fallback, bounded resource limits, and deterministic Stage 2 quality analysis on raster derivatives.

The authorized execution layer requires canonical catalog validation, approved review, non-revoked/non-deletion state, valid retention, split-specific purpose, granted/date-valid permission, storage/environment/export restrictions, exact SHA-256 and exact byte size before PDF processing.

## Beethoven + Barley Stage 3 purpose authorization

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable. Its original `pdf_pipeline_evaluation=not_requested` values are not rewritten.

The user's explicit authorization dated 2026-09-02 is recorded in:

`evidence/stage3/governance/purpose-grants.v1.json`

Grant-set canonical SHA-256:

`3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`

The overlay grants `pdf_pipeline_evaluation` only for:

- Beethoven development PDF `dataset.item.imslp799143-beethoven-op48-no3.v1` / artifact SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- Barley development PDF `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` / artifact SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`.

Restrictions remain development-only, `managed_standard`, `stage1_offline`, and `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain unauthorized.

PR #96 merged this grant overlay and post-merge Run #238 succeeded on Python 3.11 and 3.12. Duplicate Draft PR #97 was closed unmerged.

## Held-out boundary

Chopin C17C remains held-out and continues to use only its existing `held_out_evaluation` permission. Held-out data must not tune Stage 2/3 thresholds, page policies, hardening constants, renderer limits, or resource limits.

## Real-corpus execution runner — PR #98

PR #98 introduces an offline fail-closed execution runner for exactly Beethoven, Barley and Chopin.

The runner:

- requires the exact production renderer binding `pypdfium2==5.13.0` and rejects version mismatch;
- requires the accepted expanded-v2 catalog canonical SHA-256;
- requires exactly the Beethoven, Barley and Chopin dataset item IDs;
- requires all real source PDF paths to remain outside the ordinary Git working tree;
- requires detailed manifest/derivative output to remain outside the ordinary Git working tree;
- executes Beethoven and Barley through the merged purpose-grant wrapper;
- executes Chopin only through the existing held-out custody gate;
- writes public-safe receipts/evidence only;
- keeps detailed manifests, quality evidence and rendered PNG derivatives custody-only;
- records `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, and `stage4EntryAuthorized=false`.

Initial PR #98 Run #239 passed all existing repository tests and compile on Python 3.11 and 3.12 before the final CI-validator/documentation reconciliation commits. A fresh exact-head run is therefore mandatory after this reconciliation.

## Real-corpus byte custody

Accepted exact corpus byte identities remain:

- Beethoven: SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`, 1,182,561 bytes;
- Barley: SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`, 84,689 bytes;
- Chopin C17C: SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, 1,114,479 bytes.

Real PDF bytes must remain outside ordinary Git. Their presence in a connected or transient custody workspace is not by itself frozen Stage 3 execution evidence. Accepted execution evidence must be produced by the exact production runner/runtime and then reviewed as a separate public-safe evidence slice.

## Remaining Stage 3 exit gates

Stage 3 exit is **not yet PASS**. Remaining work:

1. merge and post-merge validate PR #98 real-corpus runner;
2. run the exact Beethoven/Barley/Chopin batch in approved custody with `pypdfium2==5.13.0`;
3. freeze only public-safe execution receipts/evidence in Git while detailed manifests/metrics/derivatives remain custody-only;
4. verify no held-out tuning and no vector/hybrid silent rasterization;
5. perform explicit limitations review;
6. create a separate Stage 3 final-exit acceptance decision;
7. require exact-head and post-merge Python 3.11/3.12 CI for every accepted slice.

## Safety/non-claims

Real corpus artifact bytes remain outside ordinary Git. Source PDFs remain immutable. Vector/hybrid pages are not silently rasterized. Stage 3 does not perform OMR or musical inference and does not establish musical correctness, OMR improvement, restoration effectiveness, representativeness or absence of bias. Stage 4 calibration remains blocked until explicit Stage 3 exit PASS.

Frozen Stage 2 execution evidence remains `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`; historical Stage 1/2 evidence is unchanged.
