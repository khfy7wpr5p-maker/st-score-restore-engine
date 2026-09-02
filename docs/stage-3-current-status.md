# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE + AUTHORIZED EXECUTION PRODUCTION-EFFECTIVE / PURPOSE-GRANT GOVERNANCE SLICE  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Core merge main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Core post-merge CI:** Run #232 (`33615937390`) — Python 3.11 / 3.12 SUCCESS  
**Authorized-execution merge main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Authorized-execution post-merge CI:** Run #235 (`33618108204`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage3-authorized-pdf-execution`  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 exit PASS

## Production-effective Stage 3 boundary

The PDFium core and the Stage 3 custody execution boundary are production-effective. The pipeline uses `pypdfium2==5.13.0`, exact source SHA-256 identity, stable page order, raster-only rendering, vector preservation, hybrid preservation/review, original fallback, bounded resource limits, and deterministic Stage 2 quality analysis on raster derivatives.

The authorized execution layer requires canonical catalog validation, approved review, non-revoked/non-deletion state, valid retention, split-specific purpose, granted/date-valid permission, storage/environment/export restrictions, exact SHA-256 and exact byte size before PDF processing.

## Explicit Beethoven + Barley purpose authorization

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable. Its original `pdf_pipeline_evaluation=not_requested` values are not rewritten.

The user's explicit authorization dated 2026-09-02 is recorded in a separate Stage 3 governance overlay:

`evidence/stage3/governance/purpose-grants.v1.json`

Grant-set canonical SHA-256:

`3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`

The overlay grants `pdf_pipeline_evaluation` only for:

- Beethoven development PDF `dataset.item.imslp799143-beethoven-op48-no3.v1` / artifact SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- Barley development PDF `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` / artifact SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`.

Restrictions remain development-only, `managed_standard`, `stage1_offline`, and `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain unauthorized.

`src/st_score_restore/stage3_purpose_grants.py` accepts only the exact approved grant digest, refuses to override catalog states other than historical `not_requested`, applies the permission to an in-memory catalog copy, and delegates to the existing fail-closed Stage 3 custody executor.

## Held-out boundary

Chopin C17C remains held-out and continues to use only its existing `held_out_evaluation` permission. Held-out data must not tune Stage 2/3 thresholds or hardening constants.

## Remaining Stage 3 exit gates

Stage 3 exit is **not yet PASS**. Remaining work:

- merge and post-merge validate the dedicated purpose-grant overlay slice;
- materialize exact approved custody bytes for Beethoven, Barley and permitted Chopin execution;
- run real authorized-corpus Stage 3 evaluation without writing corpus bytes to ordinary Git;
- freeze public-safe execution evidence while keeping detailed manifests/metrics/derivative bytes custody-only;
- perform explicit limitations review;
- create a separate Stage 3 final-exit acceptance decision;
- require exact-head and post-merge Python 3.11/3.12 CI.

## Safety/non-claims

Real corpus artifact bytes remain outside ordinary Git. Source PDFs remain immutable. Vector/hybrid pages are not silently rasterized. Stage 3 does not perform OMR or musical inference and does not establish musical correctness, OMR improvement, restoration effectiveness, representativeness or absence of bias. Stage 4 calibration remains blocked until explicit Stage 3 exit PASS.

Frozen Stage 2 execution evidence remains `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`; historical Stage 1/2 evidence is unchanged.
