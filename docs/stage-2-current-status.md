# Stage 2 Current Status — Complete Quality Analysis

**Status:** ACTIVE / REAL CORPUS EXECUTION EVIDENCE  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Stage 1 accepted entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Production main:** `6ab6e603550559ef701bfba9b2a200c2e5f794b9`  
**PR #84:** MERGED — deterministic quality-analysis core  
**PR #85:** MERGED — development-corpus hardening  
**PR #86:** MERGED — approved-custody execution boundary  
**PR #86 post-merge CI:** Run #217 (`33604394945`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage2-corpus-execution-evidence`  
**Active PR:** #87 — Draft  
**Stage 3:** BLOCKED until explicit Stage 2 exit PASS

## Production boundary

Stage 1 final exit remains PASS and effective. Stage 2 entry remains bound to accepted main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Production main `6ab6e603550559ef701bfba9b2a200c2e5f794b9` contains analyzer `0.1.1` and custody execution contract `0.1.0`. Post-merge Run #217 passed repository validation on Python 3.11 and 3.12, including the quality-analysis validator, approved-custody execution validator, all tests and compile.

Thresholds remain `uncalibrated_engineering_defaults`. Stage 4 owns real-data calibration. Held-out data did not tune Stage 2 thresholds or choose hardening constants.

Historical Stage 1 C15/C16 evidence remains immutable. Real score/PDF/image corpus bytes remain outside ordinary Git.

## Real accepted-corpus execution

The five accepted expanded-v2 custody objects were transiently materialized from approved custody after PR #86 merged. Each object was checked against its admitted exact SHA-256 and exact byte size before the analysis result was recorded.

Public-safe execution evidence is frozen at:

- `evidence/stage2/corpus/execution-evidence.v1.json`
- evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`
- accepted catalog canonical digest `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`

Observed controlled outcomes:

1. Beethoven development scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
2. C17A development combined staff+TAB PNG — `analyzed`;
3. C17B development guitar-TAB digital PDF — `not_applicable_vector_pdf` with vector content preserved;
4. C17C held-out Chopin scanned PDF — `deferred_stage3_renderer` / `pdf_renderer_not_available`;
5. C17D held-out deidentified phone-photo JPEG — `analyzed` under `managed_restricted` custody.

This yields 2 raster analyses, 1 vector not-applicable result and 2 deliberate Stage-3-renderer deferrals.

The scanned/hybrid PDF deferrals are an intentional fail-closed boundary. They are not execution failures and do not mean Stage 3 has started.

## Detailed report custody

Detailed real-corpus quality metrics/findings are not committed to public Git.

Detailed C17A, C17B and C17D analyzer reports were written to approved external custody and then fetched back to verify byte-for-byte raw round-trip identity. Public Git records only deterministic report/receipt digests and opaque evidence references.

C17D remains held-out, `managed_restricted` and `external_export=false`. Its detailed report remains in restricted custody. Public evidence contains no C17D quality metrics/findings and no Google Drive/file/folder locator.

The separate user-provided sensitive `Fly Me to the Moon` phone-photo path remains outside the accepted corpus and was not executed.

## Safety and non-claims

The execution evidence preserves these boundaries:

- source bytes modified: false;
- real artifact bytes in Git: false;
- held-out threshold tuning used: false;
- training authorized: false;
- calibration authorized: false;
- publication authorized: false;
- detailed metrics in public evidence: false;
- Stage 2 exit PASS: false;
- Stage 3 entry authorized: false.

The evidence does not establish musical correctness, OMR correctness/improvement, restoration effectiveness, representativeness or absence of bias.

## PR #87 validation scope

PR #87 adds a deterministic validator for the frozen public execution evidence. CI must verify:

- the exact accepted five-item set;
- catalog SHA-256 and byte-size bindings;
- development/held-out purpose separation;
- expected controlled result states;
- frozen report and public-receipt digests;
- C17D explicit no-export state;
- opaque-only detailed evidence references;
- absence of public metrics/findings and provider/local custody locators;
- zero real corpus artifact bytes under `evidence/stage2`;
- Stage 2 exit and Stage 3 entry remain false/blocked.

## Stage 2 exit remains open

Real corpus execution evidence is now available, but Stage 2 is **not yet PASS**. Remaining gates are:

1. PR #87 final exact-head Python 3.11/3.12 CI;
2. PR #87 merge and post-merge main CI;
3. explicit limitations review, including the two scanned/hybrid PDF Stage 3 deferrals;
4. a separate evidence-bound Stage 2 exit acceptance tied to the resulting exact main SHA and post-merge CI.

Until that separate acceptance is PASS, Stage 3 remains **BLOCKED**.
