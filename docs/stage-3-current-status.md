# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE + AUTHORIZED EXECUTION + PURPOSE GRANTS PRODUCTION-EFFECTIVE / REAL-CORPUS RUNNER IN DRAFT PR #98  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Core merge main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Core post-merge CI:** Run #232 (`33615937390`) — Python 3.11 / 3.12 SUCCESS  
**Authorized-execution merge main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Authorized-execution post-merge CI:** Run #235 (`33618108204`) — Python 3.11 / 3.12 SUCCESS  
**Purpose-grant merge main / production baseline:** `6ebe160309c562e9841a3c313d5ca507592f1386`  
**Purpose-grant post-merge CI:** Run #238 (`33620323970`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage3-real-corpus-runner`  
**Active PR:** #98 — Draft  
**Pre-refresh PR head:** `696729f825ed23ee89edc972cbf46303f3ebba73`  
**Pre-refresh exact-head CI:** Run #242 (`33621535491`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 final exit PASS

## Production-effective Stage 3 boundary

The PDFium core, Stage 3 approved-custody execution boundary, and Beethoven/Barley purpose-grant overlay are production-effective. The pipeline uses `pypdfium2==5.13.0`, exact source SHA-256 identity, stable page order, raster-only rendering, vector preservation, hybrid preservation/review, original fallback, bounded resource limits, and deterministic Stage 2 quality analysis on raster derivatives.

The authorized execution layer requires canonical catalog validation, approved review, non-revoked/non-deletion state, valid retention, split-specific purpose, granted/date-valid permission, storage/environment/export restrictions, exact SHA-256 and exact byte size before PDF processing.

## Beethoven + Barley Stage 3 purpose authorization

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable with its original `pdf_pipeline_evaluation=not_requested` fields.

Production-effective authorization is recorded separately in `evidence/stage3/governance/purpose-grants.v1.json`.

Grant set: `stage3.purpose-grants.beethoven-barley.v1`; canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

The overlay grants `pdf_pipeline_evaluation` only for:

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1` / SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` / SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`.

Restrictions remain development-only, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain unauthorized.

PR #96 merged the overlay and Run #238 succeeded on Python 3.11/3.12.

## Held-out boundary

Chopin C17C remains held-out and continues to use only its existing `held_out_evaluation` permission. Held-out data must not tune Stage 2/3 thresholds, page policies, hardening constants, renderer limits or resource limits.

## Real-corpus execution runner — PR #98

PR #98 introduces an offline fail-closed runner for exactly Beethoven, Barley and Chopin. It:

- requires exact `pypdfium2==5.13.0`;
- requires the accepted expanded-v2 catalog canonical SHA-256;
- requires exactly the three approved dataset item IDs;
- requires real source PDF paths and detailed output paths outside the ordinary Git working tree;
- executes Beethoven and Barley through the production purpose-grant wrapper;
- executes Chopin only through the existing held-out custody gate;
- emits public-safe receipts/evidence only;
- keeps detailed manifests, quality evidence and rendered PNG derivatives custody-only;
- records `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, and `stage4EntryAuthorized=false`.

Run #242 passed on pre-refresh head `696729f825ed23ee89edc972cbf46303f3ebba73`. This architecture/documentation reconciliation changes the PR head; Run #242 must therefore be treated as historical and a fresh exact-head Repository validation is mandatory before merge.

## Real-corpus byte custody

Accepted exact identities remain:

- Beethoven: `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`, 1,182,561 bytes;
- Barley: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`, 84,689 bytes;
- Chopin: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, 1,114,479 bytes.

Real PDF bytes remain outside ordinary Git. Accepted execution evidence must be produced by the exact production runner/runtime in approved custody. Detailed manifests/metrics/derivative bytes remain custody-only.

## Remaining Stage 3 exit gates

Stage 3 exit is **not yet PASS**:

1. fresh exact-head Python 3.11/3.12 CI for the reconciled PR #98 head;
2. clean reviews, unresolved threads, base/head reconciliation;
3. merge PR #98 and pass post-merge main CI;
4. materialize exact approved Beethoven/Barley/Chopin custody bytes;
5. run the production Stage 3 batch;
6. freeze only public-safe execution evidence;
7. verify no held-out tuning and no silent vector/hybrid rasterization;
8. perform explicit limitations review;
9. create separate versioned Stage 3 final-exit acceptance;
10. keep Stage 4 blocked unless PASS becomes production-effective.

## Safety/non-claims

Real corpus artifact bytes remain outside ordinary Git. Source PDFs remain immutable. Vector/hybrid pages are not silently rasterized. Stage 3 does not perform OMR or musical inference and does not establish musical correctness, OMR improvement, restoration effectiveness, representativeness or absence of bias.

Frozen Stage 2 execution evidence remains `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`; historical Stage 1/2 evidence is unchanged.
