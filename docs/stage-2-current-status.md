# Stage 2 Current Status — Complete Quality Analysis

**Status:** ACTIVE / INITIAL IMPLEMENTATION SLICE  
**As of:** 2026-09-02  
**Tracking:** Issue #83  
**Stage 1 accepted main:** `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`  
**Stage 1 post-merge CI:** Run #203 (`33588190548`) — Python 3.11 / 3.12 SUCCESS  
**Stage 3 entry:** BLOCKED until explicit Stage 2 exit acceptance

## 1. Entry gate

Stage 1 final exit is PASS / effective. PR #82 merged the evidence-bound acceptance and Run #203 succeeded on the resulting `main`. Stage 2 may therefore begin on a separate focused branch.

Historical Stage 1 C15/C16 evidence remains immutable. The expanded-v2 automatic report remains `review_required`; the Stage 1 PASS is the separate accepted governance decision and does not rewrite historical or automatic evidence.

## 2. Repository reality at Stage 2 entry

The repository already has a deterministic OpenCV restoration baseline with:

- bounded PNG/JPEG decode;
- EXIF display-orientation handling;
- Hough-line deskew estimation;
- page quadrilateral detection and optional perspective/crop operations;
- illumination normalization;
- conservative denoise;
- CLAHE contrast handling;
- protected notation-pixel preservation.

The pre-Stage-2 `input_inspection` contract lists perspective, crop, glare, shadow, blur, noise, compression and low-resolution finding categories, but intentionally leaves most raster pixel-quality findings `not_assessed`. Stage 2 closes that measurement gap without converting the analyzer into an OMR engine or restoration selector.

## 3. Initial Stage 2 analyzer contract

The focused implementation branch `stage2-complete-quality-analysis` introduces a versioned deterministic quality report bound to the immutable source SHA-256.

Image metrics cover:

- EXIF/display orientation evidence;
- skew angle, confidence and line support;
- page quadrilateral, area ratio, perspective asymmetry and crop margins;
- Laplacian-variance sharpness / blur evidence;
- highlight clipping and spatial glare concentration;
- tile-based local shadow strength;
- uneven-lighting background variation;
- edge-excluded high-frequency noise residuals;
- JPEG block-boundary evidence and JPEG DQT quantization severity;
- pixel dimensions and DPI-based low-resolution evidence;
- geometric five-line / six-line visibility indicators for staff-like and TAB-like structures.

The analyzer uses deterministic engineering thresholds only. These thresholds are explicitly **not held-out calibrated** and are not evidence of production operating points.

## 4. Safety and interpretation boundary

Stage 2 quality analysis:

- never modifies source bytes;
- uses no generative operation;
- performs no symbol completion;
- performs no OMR recognition or correction;
- does not establish musical correctness;
- does not establish restoration effectiveness or OMR improvement;
- does not infer model-training or calibration permission;
- does not infer a phone-photo/scanner origin when provenance is not deterministically known;
- preserves digital PDFs as vector content;
- rejects scanned/hybrid PDF pixel analysis until the Stage 3 renderer boundary exists.

Staff/TAB visibility outputs are geometric evidence only. They are not notation identity, voice/fingering interpretation, or OMR correctness claims.

## 5. Stage 2 exit is not yet satisfied

This initial implementation slice does **not** complete Stage 2. Before Stage 2 exit can be accepted, the project still requires:

1. exact-head Python 3.11 / 3.12 CI for every merged Stage 2 slice;
2. architecture/documentation reconciliation;
3. deterministic regression evidence for all quality dimensions;
4. approved-custody execution against authorized evaluation corpus items without moving real corpus bytes into ordinary Git;
5. explicit limitations and measurement evidence review;
6. a separate Stage 2 exit acceptance bound to exact `main` and CI evidence.

Until those gates are complete, Stage 3 remains BLOCKED.
