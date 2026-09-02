# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — REAL CORPUS EXECUTED / PUBLIC-SAFE EVIDENCE + LIMITATIONS REVIEW FREEZE IN PROGRESS / FINAL EXIT NOT YET PASS  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232 SUCCESS  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235 SUCCESS  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238 SUCCESS  
**Real-corpus runner:** PR #99 — merged  
**Runner exact head / CI:** `a579e82853fe4d674c1013da0531edf995f48aa7` / Run #245 SUCCESS  
**Runtime production main / CI:** `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246 (`33641537118`) SUCCESS  
**Repository documentation checkpoint:** `a86bcd4a4a88fb17e2defa36b10b5f4eb824de0d` / Run #248 SUCCESS  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 final exit PASS

## Production-effective Stage 3 boundary

The PDFium core, approved-custody execution boundary, Beethoven/Barley purpose-grant overlay and fail-closed real-corpus runner are production-effective. The renderer contract remains exactly `pypdfium2==5.13.0`.

The pipeline preserves exact source identity and page order, renders raster-only pages, preserves vector pages, routes hybrid/vector evidence to preservation/review, retains original fallback, applies bounded resources and runs deterministic quality analysis only on permitted raster derivatives.

The custody layer requires canonical catalog validation, approved review, non-revoked/non-deletion state, valid retention, split-specific purpose/restrictions, exact SHA-256 and byte size before processing.

## Authorization and held-out boundary

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable. Beethoven/Barley Stage 3 permission is supplied only through production overlay `evidence/stage3/governance/purpose-grants.v1.json`, grant set `stage3.purpose-grants.beethoven-barley.v1`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

- Beethoven: development / `pdf_pipeline_evaluation` / SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c` / 1,182,561 bytes.
- Barley: development / `pdf_pipeline_evaluation` / SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e` / 84,689 bytes.
- Chopin C17C: held-out / `held_out_evaluation` / SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3` / 1,114,479 bytes.

Beethoven/Barley restrictions remain development-only, `managed_standard`, `stage1_offline`, `external_export=false`. Chopin remains evaluation-only and must not tune thresholds, page policy, hardening constants, renderer/resource limits or calibration.

## Exact-byte materialization checkpoint

The exact three source PDFs were materialized outside ordinary Git and SHA-256/byte-size identities were re-verified immediately before processing. An isolated exact `pypdfium2==5.13.0` runtime was acquired and independently SHA-verified without changing the system `5.8.0` installation or weakening the production version gate.

## Real-corpus execution — COMPLETE

The production Stage 3 runner from runtime main `5e682f1933a7167fc142689306352fe53b4b1833`, bound to post-merge Run #246, completed the exact Beethoven + Barley + held-out Chopin batch on 2026-09-02.

Public-safe execution evidence:

- path: `evidence/stage3/corpus/execution-evidence.v1.json`;
- canonical SHA-256: `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`;
- status: `executed`;
- runner version: `0.1.0`;
- renderer binding: `5.13.0`;
- item count: 3;
- page count: 14;
- raster-only pages: 12;
- rendered raster pages: 12;
- vector-only pages: 2;
- preserved vector pages: 2;
- review-required pages: 0;
- all page order preserved: true;
- any vector pages rasterized: false;
- held-out threshold tuning used: false.

Detailed page manifests, quality evidence, metrics/findings and rendered derivative bytes remain custody-only and are not committed to ordinary Git.

**Acceptance checkpoint:** real execution not yet accepted as production-effective evidence until this evidence-freeze PR passes exact-head CI, merges, and receives successful post-merge main CI.

## Limitations review

Machine-readable limitations review: `evidence/stage3/corpus/limitations-review.v1.json`.

Canonical SHA-256: `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.

Decision: **PASS_WITH_ACCEPTED_LIMITATIONS**. This is not Stage 3 final-exit PASS.

Accepted limitations include:

- the real batch has raster-only and vector-only pages but no real hybrid page; hybrid preservation remains deterministic synthetic-test coverage;
- malformed/encrypted/empty/resource-limit/unclassified fallback paths were not encountered in this real batch and remain contract/test coverage;
- the three-item, fourteen-page corpus does not establish representativeness or absence of bias;
- Stage 3 defaults remain uncalibrated and Stage 4 owns real-data calibration;
- detailed evidence remains custody-only unless separately authorized;
- Stage 3 performs no OMR or musical inference and establishes no musical correctness, OMR improvement or restoration effectiveness claim.

## Evidence-freeze safety assertions

The frozen evidence candidate explicitly preserves:

- `sourceBytesModified=false`;
- `realCorpusBytesInGit=false`;
- `detailedManifestsPublic=false`;
- `renderedDerivativesPublic=false`;
- `heldOutThresholdTuningUsed=false`;
- `trainingAuthorized=false`;
- `calibrationAuthorized=false`;
- `publicationAuthorized=false`;
- `stage3ExitPass=false`;
- `stage4EntryAuthorized=false`.

## Remaining Stage 3 exit gates

1. exact-head Python 3.11/3.12 CI for the execution-evidence + limitations-review freeze slice;
2. clean review/thread/base/head checks;
3. merge only the exact verified evidence-freeze head;
4. pass post-merge main Python 3.11/3.12 CI;
5. create a **separate** machine-readable Stage 3 final-exit acceptance bound to the production-effective execution-evidence and limitations-review digests;
6. keep Stage 4 blocked unless that final acceptance is PASS and production-effective.

## Safety/non-claims

Source PDFs remain immutable. Real corpus and derivative bytes remain outside ordinary Git. Stage 3 establishes no musical correctness, OMR improvement, restoration effectiveness, representativeness or absence-of-bias claim. Frozen Stage 2 execution evidence remains `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.