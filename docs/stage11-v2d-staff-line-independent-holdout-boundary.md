# Stage 11 V2d — Staff-Line Independent Holdout Boundary

Date: 2026-09-13

This document is a narrow architecture overlay for the `staff_line` qualification line. It does not rewrite historical Stage 4 evidence, ADR 0036, the frozen v1/v1.1/v1.2 development evidence, or the frozen qualification policy.

## Current state

The source-only detector `stage11-v2d-staff-multisystem-source.v1.2` crossed the preregistered development-readiness floors on the already-spent 20-page development corpus. A separate explicit authorization then opened exactly one fresh independent holdout qualification workflow.

The holdout source is the pre-existing Stage 1 held-out item `dataset.item.imslp82860-chopin-op69.v2`, source family `source.family.imslp82860-chopin-op69.v1`, exact PDF SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`.

All eight PDF pages were rasterized at 200 dpi using pdfium with no crop, deskew, thresholding or enhancement. The frozen v1.2 detector ran twice with unchanged code/configuration. Both raw outputs are byte-identical with SHA-256 `f2ef8a352d9c1f26e7c460ed0f71b125a33e35838294f741d562ce81d4b077fb`. Source identity matched 8/8 pages. No teacher coordinates or restored outputs were loaded during inference, and no post-holdout retuning occurred.

The source-freeze binding is `evidence/stage11/v2d/v2d-staff-line-independent-holdout-source-freeze.v1.json`.

## Blind human boundary

Qualification scoring is not yet authorized to execute because independent human topology is incomplete. The teacher workspace is physically separated from detector raw evidence. It contains only the eight exact source PNGs, blank annotation state, masks directory, and a source-only annotation notebook.

The teacher work package is `evidence/stage11/v2d/v2d-staff-line-independent-holdout-teacher-work-package.v1.json` and is `READY_FOR_BLIND_HUMAN_ANNOTATION`.

The reviewer must not open the detector evidence folder. Detector geometry, predicted counts, raw detector SHA and restored outputs must remain hidden until teacher truth is complete and frozen.

## Qualification sequence

1. Complete all 8 source-page annotations independently.
2. Freeze teacher truth and verify 8/8 source SHA identity plus topology/mask consistency.
3. Reproduce the historical v1 scorer anchor of 71/197 before holdout scoring.
4. Score the already-frozen holdout raw artifact exactly once against the policy frozen before holdout access.
5. Require every qualification criterion conjunctively; no threshold movement is allowed.
6. If any criterion fails, v1.2 fails qualification and the consumed holdout may not be used to retune it.

## Closed gates

Until qualification completes, all of the following remain false/closed:

- `detectorQualified`
- `staff_line=PASS`
- `sourceDetectorAdequacyEstablished`
- restored-output staff-topology comparison
- semantic preservation establishment
- overall Stage 11 PASS
- production promotion/readiness
- Stage 12 entry
- PR #211 merge

The authoritative live staff-line holdout overlay is `docs/live/ST_SCORE_RESTORE_STAGE11_V2D_STAFF_LINE_HOLDOUT_CURRENT_TRUTH.json`.
