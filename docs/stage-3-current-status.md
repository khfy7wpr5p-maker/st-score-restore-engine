# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE + AUTHORIZED EXECUTION + PURPOSE GRANTS + REAL-CORPUS RUNNER PRODUCTION-EFFECTIVE / REAL EXECUTION NOT YET ACCEPTED  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Core main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232 SUCCESS  
**Authorized-execution main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235 SUCCESS  
**Purpose-grant main:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238 SUCCESS  
**Real-corpus runner PR:** #99 — merged  
**Runner exact head:** `a579e82853fe4d674c1013da0531edf995f48aa7` / Run #245 SUCCESS  
**Current production main:** `5e682f1933a7167fc142689306352fe53b4b1833`  
**Post-merge CI:** Run #246 (`33641537118`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 final exit PASS

## Production-effective Stage 3 boundary

The PDFium core, approved-custody execution boundary, Beethoven/Barley purpose-grant overlay and fail-closed real-corpus runner are production-effective. The production renderer contract remains exactly `pypdfium2==5.13.0`.

The pipeline preserves exact source identity and page order, renders raster-only pages, preserves vector pages, routes hybrid/vector evidence to preservation/review, retains original fallback, applies bounded resources and runs deterministic quality analysis only on permitted raster derivatives.

The custody layer requires canonical catalog validation, approved review, non-revoked/non-deletion state, valid retention, split-specific purpose/restrictions, exact SHA-256 and byte size before processing.

## Beethoven + Barley authorization

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable with original `pdf_pipeline_evaluation=not_requested` fields. Production-effective authorization is separate: `evidence/stage3/governance/purpose-grants.v1.json`, grant set `stage3.purpose-grants.beethoven-barley.v1`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

Authorized exact artifacts:

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1` / SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c` / 1,182,561 bytes;
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` / SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e` / 84,689 bytes.

Restrictions remain development-only, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out permission changes remain unauthorized.

## Held-out boundary

Chopin C17C remains held-out and uses only existing `held_out_evaluation`. Exact admitted identity is SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, 1,114,479 bytes. Held-out data must not tune thresholds, page policy, renderer/resource limits, hardening constants or calibration.

## Runner production history

Draft PR #98 carried the runner plus architecture refresh. Its head passed Run #243, but Draft→Ready failed only at the connector GraphQL response field `Repository.fullDatabaseId`. PR #98 was closed unmerged.

Replacement non-draft PR #99 was opened from the same verified lineage. Final exact head `a579e82853fe4d674c1013da0531edf995f48aa7` passed Run #245 on Python 3.11 and 3.12, PR #99 merged, and production main became `5e682f1933a7167fc142689306352fe53b4b1833`. Post-merge Run #246 then passed Python 3.11 and 3.12, including architecture consistency, Stage 3 PDF/custody/real-corpus-runner validators, full tests and compile.

The runner handles exactly Beethoven, Barley and Chopin. Beethoven/Barley execute through the exact production purpose-grant wrapper; Chopin executes only through held-out custody. Source files and private output must remain outside ordinary Git. Detailed manifests, quality evidence and rendered PNG derivatives remain custody-only. Public assertions remain `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, `stage4EntryAuthorized=false`.

## Exact-byte materialization checkpoint

All three accepted real source files were materialized in a transient connected workspace outside ordinary Git and independently re-hashed immediately after retrieval. SHA-256 and byte size matched the admitted identities exactly for Beethoven, Barley and Chopin. Source bytes were not modified and were not committed to Git.

This exact-byte verification removes the previous source-availability blocker, but it is **not** itself Stage 3 execution evidence.

## Current execution blocker

The current transient execution host exposes `pypdfium2 5.8.0`, while the production runner requires exact `pypdfium2==5.13.0`. The host's outbound package/repository acquisition path is unavailable. The renderer-version gate is therefore preserved fail-closed; it is not weakened, patched or bypassed to fit the host.

This is an execution-environment limitation, not a repository implementation failure.

## Remaining Stage 3 exit gates

1. execute the exact verified Beethoven/Barley/Chopin batch in an approved offline custody host with production main `5e682f1933a7167fc142689306352fe53b4b1833` and exact `pypdfium2==5.13.0`;
2. re-check SHA-256 and byte size immediately before processing;
3. freeze only public-safe execution receipts/evidence in Git while detailed manifests, metrics/findings and derivative bytes remain custody-only;
4. verify no held-out tuning and no silent vector/hybrid rasterization;
5. perform explicit limitations review;
6. create a separate versioned Stage 3 final-exit acceptance decision;
7. keep Stage 4 blocked unless that final decision is PASS and production-effective.

## Safety/non-claims

Source PDFs remain immutable. Real corpus and derivative bytes remain outside ordinary Git. Stage 3 performs no OMR or musical inference and establishes no musical correctness, OMR improvement, restoration effectiveness, representativeness or absence-of-bias claim.

Frozen Stage 2 execution evidence remains `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
