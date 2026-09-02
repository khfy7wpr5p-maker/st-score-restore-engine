# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE + AUTHORIZED EXECUTION + PURPOSE GRANTS PRODUCTION-EFFECTIVE / REAL-CORPUS RUNNER IN NON-DRAFT PR #99  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Core merge main:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa`  
**Core post-merge CI:** Run #232 (`33615937390`) — Python 3.11 / 3.12 SUCCESS  
**Authorized-execution main:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b`  
**Authorized-execution CI:** Run #235 (`33618108204`) — Python 3.11 / 3.12 SUCCESS  
**Purpose-grant main / production baseline:** `6ebe160309c562e9841a3c313d5ca507592f1386`  
**Purpose-grant CI:** Run #238 (`33620323970`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage3-real-corpus-runner`  
**Active PR:** #99 — non-draft replacement  
**Closed predecessor:** Draft PR #98 — closed unmerged after connector Draft→Ready error  
**Pre-replacement exact-head:** `7778cdf790daa806efd166d9d3bf1f5a011ecc71`  
**Pre-replacement exact-head CI:** Run #243 (`33639819769`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 final exit PASS

## Production-effective Stage 3 boundary

PDFium core, approved-custody execution boundary and Beethoven/Barley purpose-grant overlay are production-effective. The pipeline uses `pypdfium2==5.13.0`, exact source identity, stable page order, raster-only rendering, vector preservation, hybrid preservation/review, original fallback, bounded resources and deterministic quality analysis.

The custody layer requires canonical catalog validation, approved review, non-revoked/non-deletion state, valid retention, exact split purpose/restrictions, SHA-256 and byte size before processing.

## Beethoven + Barley authorization

Historical `evidence/stage1c/corpus/catalog.v2.json` remains immutable with original `pdf_pipeline_evaluation=not_requested` fields. Production-effective authorization is separate: `evidence/stage3/governance/purpose-grants.v1.json`, grant set `stage3.purpose-grants.beethoven-barley.v1`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.

Authorized exact artifacts:

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1` / SHA-256 `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`;
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1` / SHA-256 `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`.

Restrictions: development-only, `managed_standard`, `stage1_offline`, `external_export=false`. Training, calibration, publication, demonstration and held-out changes remain unauthorized.

## Held-out boundary

Chopin C17C remains held-out and uses only existing `held_out_evaluation`. It must never tune Stage 2/3 thresholds, page policies, hardening constants, renderer limits or resource limits.

## Runner replacement history

Draft PR #98 carried the runner plus architecture refresh. Its head `7778cdf790daa806efd166d9d3bf1f5a011ecc71` passed Run #243. Draft→Ready then failed at the connector GraphQL response field `Repository.fullDatabaseId`. The PR was closed **unmerged** and non-draft PR #99 was opened from the same branch/head lineage. This replacement is an allowed fail-safe path from the handoff; it does not reuse #98’s CI as the final merge gate.

This PR-number reconciliation itself moves the branch head, so a new PR #99 exact-head Repository validation is required.

## Real-corpus runner — PR #99

The runner handles exactly Beethoven, Barley and Chopin. It requires exact `pypdfium2==5.13.0`, accepted catalog identity and exact item set; source/private-output paths must remain outside the ordinary Git working tree. Beethoven/Barley execute through the production purpose-grant wrapper; Chopin executes only through held-out custody. Public evidence is redacted; detailed manifests, quality evidence and rendered PNG derivatives remain custody-only. Assertions remain `heldOutThresholdTuningUsed=false`, `stage3ExitPass=false`, `stage4EntryAuthorized=false`.

## Exact custody identities

- Beethoven: `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`, 1,182,561 bytes;
- Barley: `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`, 84,689 bytes;
- Chopin: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`, 1,114,479 bytes.

## Remaining Stage 3 exit gates

1. fresh exact-head Python 3.11/3.12 CI for final PR #99 head;
2. clean reviews, unresolved threads, base/head reconciliation;
3. merge PR #99 only at exact verified head;
4. pass post-merge main CI;
5. materialize exact approved Beethoven/Barley/Chopin custody bytes;
6. run production Stage 3 batch;
7. freeze public-safe execution evidence only;
8. verify no held-out tuning and no silent vector/hybrid rasterization;
9. explicit limitations review;
10. separate versioned Stage 3 final-exit acceptance;
11. keep Stage 4 blocked unless PASS is production-effective.

## Safety/non-claims

Source PDFs remain immutable. Real corpus and derivative bytes remain outside ordinary Git. Stage 3 performs no OMR/musical inference and establishes no musical correctness, OMR improvement, restoration effectiveness, representativeness or absence-of-bias claim.

Frozen Stage 2 execution evidence remains `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
