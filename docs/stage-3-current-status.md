# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** COMPLETE / PASS / PRODUCTION-EFFECTIVE  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 final acceptance main:** `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`  
**Stage 3 final post-merge CI:** Run #253 (`33646323461`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4:** ENTRY ELIGIBLE / NOT STARTED

## Production chain

- Stage 3 entry: `87198a5a917ab6b3efc277762016a5f5b0dd3aab` / Run #228.
- PDFium core: `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232.
- Authorized custody execution: `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235.
- Beethoven/Barley purpose overlay: `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238.
- Real-corpus runner runtime: `5e682f1933a7167fc142689306352fe53b4b1833` / PR #99 / Run #246.
- Real-corpus execution evidence: `b15d91ff3fbf21b47a0e484b5a337c4611a17355` / PR #101 / exact-head Run #250 / post-merge Run #251.
- Final acceptance: `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / PR #102 / exact-head Run #252 / post-merge Run #253.

## Accepted Stage 3 contract

The production renderer remains exact `pypdfium2==5.13.0` / PDFium. Raster-only pages may be rendered within bounded resource limits; vector-only pages are preserved; hybrid pages are preserved/reviewed; unknown/empty/over-limit pages retain original fallback. Vector or hybrid content is never silently rasterized.

Resource values remain **uncalibrated engineering defaults**: 200 DPI; 64 pages; 40,000,000 pixels/page; 160,000,000 aggregate rendered pixels; 8,000-pixel maximum render dimension; page-object traversal depth 15.

## Purpose and held-out boundary

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable. Beethoven/Barley Stage 3 permission is supplied only through `evidence/stage3/governance/purpose-grants.v1.json`, grant set `stage3.purpose-grants.beethoven-barley.v1`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

- Beethoven: development / `pdf_pipeline_evaluation` / SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c` / 1,182,561 bytes.
- Barley: development / `pdf_pipeline_evaluation` / SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e` / 84,689 bytes.
- Chopin C17C: held-out / `held_out_evaluation` / SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3` / 1,114,479 bytes.

Held-out data did not tune thresholds, page policy, hardening constants, renderer/resource limits or calibration.

## Real-corpus execution

The exact three PDFs were materialized outside ordinary Git, re-hashed immediately before processing, and executed through the production Stage 3 runner with exact `pypdfium2==5.13.0`.

Accepted public summary:

- item count: 3;
- page count: 14;
- raster-only pages: 12;
- rendered raster pages: 12;
- vector-only pages: 2;
- preserved vector pages: 2;
- review-required pages: 0;
- all page order preserved: true;
- vector pages rasterized: false;
- held-out threshold tuning used: false.

Real source PDFs, detailed page manifests, quality evidence, metrics/findings and rendered derivatives remain outside ordinary Git and custody-only.

## Accepted evidence

Public execution evidence: `evidence/stage3/corpus/execution-evidence.v1.json`, canonical SHA-256 `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.

Limitations review: `evidence/stage3/corpus/limitations-review.v1.json`, decision **PASS_WITH_ACCEPTED_LIMITATIONS**, canonical SHA-256 `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.

Final acceptance: `evidence/stage3/corpus/stage3-exit-acceptance.v1.json`, decision **PASS**, canonical SHA-256 `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

The final acceptance records:

- `stage3ExitPass=true`;
- `stage4EntryEligible=true`;
- `stage4Started=false`;
- `blockerCodes=[]`;
- all unsupported positive claims remain false.

## Accepted limitations / non-claims

The real batch contains no real hybrid page; hybrid behavior remains deterministic synthetic-test coverage. It does not exercise every malformed/encrypted/resource-limit fallback case. Three items / fourteen pages do not establish representativeness or absence of bias. Stage 3 does not perform OMR or musical inference and does not establish musical correctness, OMR improvement or restoration effectiveness.

Stage 3 PASS does not authorize model training, calibration or publication.

## Stage 4 boundary

Stage 4 is now **ENTRY ELIGIBLE / NOT STARTED**. Stage 4 owns real-data safety calibration. A separate Stage 4 entry/start decision must define eligible data use, anti-leakage rules, objectives, metrics, thresholds and acceptance gates before any Stage 4 work changes production behavior.

The separate sensitive `Fly Me to the Moon` phone-photo path remains independently blocked pending real high-assurance-vault verification.