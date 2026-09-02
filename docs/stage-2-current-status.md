# Stage 2 Current Status — Complete Quality Analysis

**Status:** COMPLETE / PASS — FINAL EXIT ACCEPTANCE SLICE  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Accepted Stage 2 entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Stage 2 evidence main:** `ffea7f5aa618187f3cabcfb49801804e3f6658bf`  
**Stage 3:** ENTRY ELIGIBLE / NOT STARTED

## Production chain

- PR #84 merged deterministic quality-analysis core.
- PR #85 merged development-corpus hardening.
- PR #86 merged approved-custody execution contract `0.1.0`.
- PR #87 merged frozen five-item corpus execution evidence and validator to main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`.
- PR #87 final exact-head Run #220 (`33606224352`) passed Python 3.11 and 3.12.
- Post-merge main Run #221 (`33607016064`) passed Python 3.11 and 3.12, including Stage 1 gates, Stage 2 quality/custody/execution validators, full tests and compile.

Production analyzer version is `0.1.1`. Thresholds remain `uncalibrated_engineering_defaults`; Stage 4 owns real-data calibration.

## Real accepted-corpus execution

The five accepted expanded-v2 custody objects were transiently materialized from approved custody and each matched admitted exact SHA-256 and exact byte size before analysis.

Frozen public execution evidence:

- path: `evidence/stage2/corpus/execution-evidence.v1.json`;
- canonical digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`;
- accepted catalog digest: `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`.

Controlled outcomes:

1. Beethoven development scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
2. C17A development combined staff+TAB PNG — `analyzed`;
3. C17B development digital guitar-TAB PDF — `not_applicable_vector_pdf`, vector preserved;
4. C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
5. C17D held-out deidentified phone-photo JPEG — `analyzed` under `managed_restricted` custody.

Summary: 5 items, 5/5 exact identities, 2 raster analyses, 1 vector not-applicable result, 2 controlled Stage-3-renderer deferrals, 3 development items, 2 held-out items, 1 restricted no-export item.

## Custody and held-out boundary

Detailed real-corpus metrics/findings are not committed to public Git. Public evidence contains only approved metadata, digests, controlled result states and opaque evidence references.

C17D remains `managed_restricted` and `external_export=false`; its detailed report remains restricted custody evidence. Held-out C17C/C17D results did not tune thresholds or choose hardening constants.

The separate user-provided sensitive `Fly Me to the Moon` phone-photo path is not part of the accepted corpus and remains blocked pending real high-assurance-vault verification.

## Limitations review

The limitations review is PASS for Stage 2 exit purpose:

- scanned/hybrid PDF pixel analysis remains intentionally deferred to the Stage 3 renderer boundary;
- digital PDFs remain vector-preserved;
- thresholds remain uncalibrated until Stage 4;
- detailed real-corpus reports remain custody-only;
- C17D detailed export remains blocked;
- no musical correctness, OMR improvement, restoration effectiveness, representativeness or absence-of-bias claim is established;
- training, calibration and publication remain unauthorized.

The two PDF deferrals are accepted fail-closed boundary outcomes, not hidden execution failures.

## Separate Stage 2 exit acceptance

`evidence/stage2/corpus/stage2-exit-acceptance.v1.json` records `decision=PASS`, bound to exact main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`, exact-head Run #220, post-merge Run #221 and the frozen execution evidence digest.

The earlier execution evidence remains immutable with `stage2ExitPass=false` and `stage3EntryAuthorized=false`. The final PASS is intentionally a separate decision layer rather than a retroactive rewrite.

## Stage 3 boundary

Stage 3 is **ENTRY ELIGIBLE / NOT STARTED**. This acceptance slice contains no Stage 3 renderer implementation. Stage 3 may start only after the acceptance PR itself is merged and its post-merge main CI succeeds, then only in a new focused branch/PR.
