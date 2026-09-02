# Stage 2 Current Status — Complete Quality Analysis

**Status:** ACTIVE / DEVELOPMENT-CORPUS HARDENING  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Stage 1 accepted entry main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Production main:** `28aa17c28eb826b4fd860917f5f7b2f72a01bdad`  
**PR #84:** MERGED  
**Post-merge main CI:** Run #207 (`33599776059`) — Python 3.11 / 3.12 SUCCESS  
**Active hardening branch:** `stage2-dev-corpus-hardening`  
**Stage 3:** BLOCKED until explicit Stage 2 exit PASS

## Entry and production baseline

Stage 1 final exit is PASS and effective. PR #82 established the Stage 2 entry decision against accepted main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`. PR #84 subsequently merged the deterministic OpenCV Stage 2 quality-analysis core and architecture reconciliation into production main `28aa17c28eb826b4fd860917f5f7b2f72a01bdad`. Repository validation Run #207 succeeded on that resulting exact main SHA on Python 3.11 and 3.12, including the Stage 2 contract validator, full tests and compile.

Historical Stage 1 C15/C16 evidence remains immutable. Real corpus score/PDF/image bytes remain outside ordinary Git.

## Authorized-corpus custody recheck

The accepted five-item Stage 1 expanded-v2 corpus was re-materialized from approved Google Drive custody only for transient Stage 2 evaluation. Exact byte size and SHA-256 identity matched the accepted catalog for all five items before any analysis decision was made.

The accepted corpus remains:

- Beethoven development scanned PDF;
- C17A development combined staff+TAB PNG;
- C17B development guitar-TAB PDF;
- C17C held-out Chopin scanned PDF metadata-v2 representation;
- C17D held-out deidentified phone-photo JPEG in `managed_restricted` custody.

The separate user-provided `Fly Me to the Moon` sensitive phone photo is not part of this accepted corpus and is not used by Stage 2.

No real corpus bytes are committed to Git. Transient evaluation copies are not repository fixtures.

## Development-corpus hardening finding

The first real development-raster exercise used C17A only. It exposed two measurement-semantics defects in analyzer `0.1.0`:

1. predominantly white score paper could be scored as glare because global white clipping contributed directly to the glare score;
2. a small notation-region quadrilateral could be selected as a page boundary because page geometry lacked a minimum page-area eligibility rule.

These are algorithm correctness defects, not Stage 4 calibration decisions. No held-out metric or threshold was used to choose the fixes.

The focused hardening branch updates analyzer version to `0.1.1` and:

- scores glare from **localized clipped-bright excess relative to the page/tile baseline**, while retaining global clipped fraction as evidence only;
- requires a deterministic minimum page-area ratio before a quadrilateral may become page-boundary evidence;
- fails perspective/crop closed to `not_assessed` when no qualifying page quadrilateral exists;
- adds synthetic regressions that a white score background is not glare and a small inner rectangle is not a page boundary;
- retains the existing regression that a large localized clipped patch is probable glare.

The new page-area rule and glare semantics remain uncalibrated engineering defaults. Stage 4 still owns real-data threshold calibration.

## Held-out boundary

Held-out artifacts are not used to tune Stage 2 thresholds or choose hardening constants. In particular, C17D remains held-out and `managed_restricted`; its permission includes `external_export=false`.

Therefore detailed C17D-derived Stage 2 metrics or reports must not be exported to public Git. Any detailed held-out execution evidence must remain in approved private/restricted custody. Public repository evidence may record only safe execution-state facts and opaque/private evidence references permitted by the custody contract.

C17C likewise remains held-out evaluation material and is not used for threshold selection.

## Current analyzer safety boundary

Stage 2 analysis:

- never modifies source bytes;
- uses no generative operation or symbol completion;
- performs no OMR recognition/correction;
- does not establish musical correctness;
- does not establish restoration effectiveness or OMR improvement;
- does not infer training or calibration permission;
- uses explicitly uncalibrated engineering defaults;
- does not tune thresholds from held-out data;
- preserves digital PDFs as vector content;
- fails closed for scanned/hybrid PDF pixel analysis until the Stage 3 renderer boundary.

Staff/TAB visibility remains geometric image evidence only, not notation identity or OMR correctness.

## Stage 2 exit remains open

Stage 2 is not complete after this hardening slice. Exit still requires:

1. exact-head Python 3.11 / 3.12 CI and post-merge validation for the hardening slice;
2. an approved-custody execution contract that verifies exact digest/size and purpose permission before analysis;
3. safe handling of development versus held-out output, including restricted no-export evidence;
4. deterministic corpus execution evidence without moving real artifact bytes into Git;
5. limitations review;
6. a separate Stage 2 exit acceptance bound to exact main and CI evidence.

Until those gates pass, Stage 3 remains **BLOCKED**.
