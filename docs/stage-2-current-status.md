# Stage 2 Current Status — Complete Quality Analysis

**Status:** COMPLETE / PASS / PRODUCTION-EFFECTIVE  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Stage 2 execution-evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Final acceptance merge main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Acceptance post-merge CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Stage 3:** ACTIVE under Issue #90  
**Stage 4:** NOT STARTED / BLOCKED pending Stage 3 exit PASS

## Production chain

- PR #84 merged deterministic quality-analysis core.
- PR #85 merged development-corpus hardening.
- PR #86 merged approved-custody execution contract `0.1.0`.
- PR #87 merged frozen five-item corpus execution evidence and validator to main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`.
- PR #87 final exact-head Run #220 (`33606224352`) passed Python 3.11 and 3.12.
- Post-merge main Run #221 (`33607016064`) passed Python 3.11 and 3.12.
- Final Stage 2 acceptance was recorded separately in `evidence/stage2/corpus/stage2-exit-acceptance.v1.json`.
- PR #89 merged the acceptance slice to main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`.
- Post-merge Run #228 (`33609061197`) passed Python 3.11 and 3.12, including the Stage 2 final-exit validator, full tests and compile.

Stage 2 is therefore closed and production-effective. Production analyzer version remains `0.1.1`. Thresholds remain `uncalibrated_engineering_defaults`; Stage 4 owns real-data calibration.

## Real accepted-corpus execution

The five accepted expanded-v2 custody objects were transiently materialized from approved custody and each matched admitted exact SHA-256 and exact byte size before analysis.

Frozen public execution evidence:

- path: `evidence/stage2/corpus/execution-evidence.v1.json`;
- canonical digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`;
- accepted catalog digest: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`.

Historical controlled outcomes remain:

1. Beethoven development scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
2. C17A development combined staff+TAB PNG — `analyzed`;
3. C17B development digital guitar-TAB PDF — `not_applicable_vector_pdf`, vector preserved;
4. C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
5. C17D held-out deidentified phone-photo JPEG — `analyzed` under `managed_restricted` custody.

These historical Stage 2 results are not rewritten now that Stage 3 has started.

## Custody and held-out boundary

Detailed real-corpus metrics/findings are not committed to public Git. C17D remains `managed_restricted` and `external_export=false`; its detailed report remains restricted custody evidence. Held-out C17C/C17D results did not tune thresholds or choose hardening constants.

The separate user-provided sensitive `Fly Me to the Moon` phone-photo path is not part of the accepted corpus and remains blocked pending real high-assurance-vault verification.

## Final acceptance semantics

The frozen Stage 2 execution evidence remains immutable with its original `stage2ExitPass=false` and `stage3EntryAuthorized=false` assertions. Those fields describe the execution-evidence moment and are not changed retroactively.

The later `stage2-exit-acceptance.v1.json` record supplies the separate PASS decision. PR #89 plus Run #228 made that PASS production-effective and satisfied Stage 3 entry.

## Stage 3 handoff

Stage 3 is now ACTIVE under Issue #90 in focused branch `stage3-multipage-pdf-core`.

Stage 3 owns the scanned/hybrid PDF renderer boundary. Its first core slice selects PDFium via `pypdfium2==5.13.0` and enforces page-level no-silent-vector-rasterization policy.

This transition does not authorize Stage 4 calibration, training or publication. Stage 4 remains blocked until explicit Stage 3 exit PASS.
