# Stage 2 Current Status — Complete Quality Analysis

**Status:** ACTIVE / APPROVED-CUSTODY EXECUTION CONTRACT  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Stage 1 accepted entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Production main:** `91aba998dc31bc415193a3e8a9e8e40ad0dc73ba`  
**PR #84:** MERGED — Stage 2 quality-analysis core  
**PR #85:** MERGED — development-corpus hardening  
**PR #85 post-merge CI:** Run #211 (`33601886396`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage2-approved-custody-execution`  
**Active PR:** #86 — Draft  
**PR #86 preliminary CI:** Run #214 (`33603120734`) — Python 3.11 / 3.12 SUCCESS  
**Stage 3:** BLOCKED until explicit Stage 2 exit PASS

## Entry and production baseline

Stage 1 final exit remains PASS and effective. PR #82 established Stage 2 entry against accepted main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

PR #84 merged the deterministic OpenCV quality-analysis core. PR #85 then merged the development-corpus hardening that corrected localized glare semantics and page-boundary eligibility without using held-out data to tune thresholds. The resulting production main is `91aba998dc31bc415193a3e8a9e8e40ad0dc73ba`; post-merge Repository validation Run #211 passed on Python 3.11 and 3.12.

Production analyzer version is `0.1.1`. Thresholds remain explicitly `uncalibrated_engineering_defaults`; Stage 4 owns real-data calibration.

Historical Stage 1 C15/C16 evidence remains immutable. Real corpus score/PDF/image bytes remain outside ordinary Git.

## Accepted corpus custody identity

The accepted five-item Stage 1 expanded-v2 corpus was previously re-materialized transiently from approved custody and all five objects matched their admitted exact SHA-256 and byte size. That identity recheck does not itself constitute Stage 2 execution evidence.

The accepted corpus remains:

- Beethoven development scanned PDF;
- C17A development combined staff+TAB PNG;
- C17B development guitar-TAB PDF;
- C17C held-out Chopin scanned PDF metadata-v2 representation;
- C17D held-out deidentified phone-photo JPEG in `managed_restricted` custody.

The separate user-provided `Fly Me to the Moon` sensitive phone photo is not part of this accepted corpus and is not used by Stage 2.

## PR #86 — approved-custody execution boundary

PR #86 adds a fail-closed runtime boundary before real corpus bytes may reach the Stage 2 analyzer. It requires:

1. canonical catalog validation;
2. an admitted `external_available` artifact with approved dataset review and no active revocation/deletion state;
3. valid retention on the execution date;
4. exact Stage 2 split/purpose mapping:
   - `development` → `quality_evaluation`;
   - `held_out` → `held_out_evaluation`;
5. a granted purpose permission valid on the execution date;
6. enforcement of split, storage, environment, retention and external-export restrictions;
7. exact admitted SHA-256 match;
8. exact admitted byte-size match;
9. deterministic public-safe receipt generation with no quality metrics/findings;
10. custody-only handling for detailed real-corpus analyzer output.

A source identity or permission mismatch fails before analysis.

The default execution environment reuses the existing catalog-governed `stage1_offline` custody environment code. This is compatibility with the admitted restriction vocabulary, not a claim that Stage 2 is part of Stage 1.

## Output and held-out boundary

Stage 2 execution does not grant publication. Public repository evidence may contain only the redacted execution receipt and approved opaque references; detailed quality metrics/findings remain custody-only unless separately authorized.

C17D remains held-out, `managed_restricted`, and explicitly `external_export=false`. Its detailed report must not be exported to public Git. Held-out C17C/C17D results must not tune thresholds or choose Stage 2 hardening constants.

Training and calibration remain unauthorized by this execution contract.

## PDF boundary

Digital PDFs remain vector-preserved and may return `not_applicable_vector_pdf` without rasterization.

Accepted scanned/hybrid PDFs may pass custody/source-identity authorization but pixel analysis remains deferred until the approved Stage 3 renderer exists. Their controlled Stage 2 result is `deferred_stage3_renderer` with `pdf_renderer_not_available` rather than silently pulling Stage 3 work forward.

This deferred result does not authorize Stage 3.

## PR #86 preliminary verification

Run #212 initially failed only in the new custody validator because its synthetic deidentified C17D fixture changed the artifact SHA-256 without changing the linked `privacy.deidentifiedArtifactSha256`. The canonical catalog validator correctly rejected that inconsistency. The validator was not weakened; both synthetic fixture builders were corrected to preserve the deidentification digest invariant.

Run #214 then passed on Python 3.11 and 3.12, including:

- repository and architecture consistency;
- all historical Stage 1 admission/freeze/exit gates;
- Stage 2 quality-analysis validator;
- new approved-custody execution validator;
- full repository tests;
- Python compile.

This status update intentionally moves PR #86 head. Therefore Run #214 is preliminary evidence only; a fresh exact-head CI run is required after the final status/live-handoff reconciliation.

## Stage 2 exit remains open

Stage 2 is **not complete** merely because the custody contract passes synthetic CI. Exit still requires:

1. PR #86 final exact-head CI and post-merge main CI;
2. real approved-custody execution against the five accepted items using the merged contract;
3. deterministic public-safe execution receipts without real artifact bytes in Git;
4. custody-only handling of detailed reports, especially C17D no-export evidence;
5. explicit review of the intentional scanned-PDF Stage 3 deferrals and other limitations;
6. a separate evidence-bound Stage 2 exit acceptance tied to exact main and CI evidence.

Until those gates pass, Stage 3 remains **BLOCKED**.
