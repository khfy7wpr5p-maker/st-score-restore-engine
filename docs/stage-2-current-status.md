# Stage 2 Current Status — Complete Quality Analysis

**Status:** COMPLETE / PASS / PRODUCTION-EFFECTIVE  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Stage 2 execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Final acceptance merge main / Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Acceptance post-merge CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Stage 3:** ACTIVE under Issue #90; current production baseline `6ebe160309c562e9841a3c313d5ca507592f1386`; Draft PR #98 in progress  
**Stage 4:** NOT STARTED / BLOCKED pending Stage 3 final exit PASS

## Production chain

PRs #84–#87 delivered the deterministic quality analyzer, development-corpus hardening, approved-custody execution contract and frozen five-item execution evidence. Stage 2 final acceptance was recorded separately in `evidence/stage2/corpus/stage2-exit-acceptance.v1.json`; PR #89 merged that acceptance to main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`, and Run #228 passed Python 3.11/3.12.

Stage 2 is closed and production-effective. Production analyzer version remains `0.1.1`; custody execution contract version remains `0.1.0`. Thresholds remain `uncalibrated_engineering_defaults`; Stage 4 owns real-data calibration.

## Real accepted-corpus execution

The five accepted expanded-v2 custody objects were transiently materialized from approved custody and matched exact SHA-256 and exact byte size before Stage 2 analysis.

Frozen public execution evidence:

- `evidence/stage2/corpus/execution-evidence.v1.json`;
- canonical digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`;
- accepted catalog digest `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`.

Historical controlled outcomes remain:

1. Beethoven scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
2. C17A combined staff+TAB PNG — `analyzed`;
3. C17B digital guitar-TAB PDF — `not_applicable_vector_pdf`, vector preserved;
4. C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
5. C17D held-out deidentified phone-photo JPEG — `analyzed` under `managed_restricted` custody.

These historical Stage 2 results are not rewritten now that Stage 3 has a production PDF renderer.

## Custody and held-out boundary

Detailed real-corpus metrics/findings are not committed to public Git. C17D remains `managed_restricted` and `external_export=false`; its detailed report remains restricted custody evidence. Held-out C17C/C17D results did not tune thresholds or choose hardening constants.

The separate sensitive `Fly Me to the Moon` phone-photo path is not part of the accepted corpus and remains blocked pending real high-assurance-vault verification.

## Final acceptance semantics

The frozen Stage 2 execution evidence remains immutable with its original `stage2ExitPass=false` and `stage3EntryAuthorized=false` assertions. Those fields describe the execution-evidence moment and are not changed retroactively.

The later `stage2-exit-acceptance.v1.json` supplies the separate PASS decision. PR #89 plus Run #228 made that PASS production-effective and satisfied Stage 3 entry.

## Current Stage 3 handoff context

Stage 3 is ACTIVE under Issue #90. PDFium core, approved-custody execution boundary and Beethoven/Barley purpose-grant overlay are production-effective through main `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238. Draft PR #98 adds a fail-closed real-corpus runner on branch `stage3-real-corpus-runner`.

This later Stage 3 work does not authorize Stage 4 calibration, training or publication and does not alter Stage 2 evidence. Stage 4 remains blocked until explicit Stage 3 final exit PASS.
