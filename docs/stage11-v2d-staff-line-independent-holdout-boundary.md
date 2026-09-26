# Stage 11 V2d — Staff-Line Independent Holdout Boundary

Date: 2026-09-13

This document is a narrow architecture overlay for the `staff_line` qualification line. It does not rewrite historical Stage 4 evidence, ADR 0036, the frozen v1/v1.1/v1.2 development evidence, or the qualification policy that was frozen before holdout access.

## Current state

The source-only detector `stage11-v2d-staff-multisystem-source.v1.2` crossed the preregistered development-readiness floors on the already-spent 20-page development corpus. A separate explicit authorization then opened exactly one fresh independent holdout qualification workflow.

That workflow is now **complete and consumed**.

The holdout source was the pre-existing Stage 1 held-out item `dataset.item.imslp82860-chopin-op69.v2`, source family `source.family.imslp82860-chopin-op69.v1`, exact PDF SHA-256 `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`.

All eight PDF pages were rasterized at 200 dpi using pdfium with no crop, deskew, thresholding or enhancement. The frozen v1.2 detector ran twice with unchanged code/configuration. Both raw outputs are byte-identical with SHA-256 `f2ef8a352d9c1f26e7c460ed0f71b125a33e35838294f741d562ce81d4b077fb`. Source identity matched 8/8 pages. No teacher coordinates or restored outputs were loaded during inference, and no post-holdout retuning occurred.

The source-freeze binding is `evidence/stage11/v2d/v2d-staff-line-independent-holdout-source-freeze.v1.json`.

## Blind human truth — complete and frozen

Independent teacher topology was completed on all 8 exact source pages before scoring. The frozen teacher truth contains:

- completed pages: 8/8;
- staff-present pages: 7;
- staff-absent pages: 1;
- confirmed standard five-line systems: 88;
- active/uncommitted lines: 0;
- teacher truth SHA-256: `3b83642b162285eb9cb4b6f806ad82d657eac980003159366ca72b5cef47cfb3`.

Detector geometry, predicted counts and restored outputs were not exposed to the teacher during the blind review. The temporary annotation-tool grouping defect was repaired only by preserving and regrouping existing human-drawn segments; no detector output was used and no inferred staff line was added.

## Scorer compatibility gate

Before scoring the fresh holdout, the one-to-one ordered five-line 0.5-spacing scorer reproduced the frozen historical v1 anchor exactly:

- expected: 71/197;
- reproduced: 71/197;
- compatibility gate: PASS.

## Independent qualification result

The already-frozen holdout raw output was scored exactly once against the qualification policy frozen before holdout access.

Observed results:

- teacher systems: 88;
- detector predictions: 128;
- matched systems: 80;
- recall @ 0.5 spacing: `0.9090909091` — PASS (`>= 0.65`);
- predicted-system precision: `0.625` — **FAIL** (`>= 0.80` required);
- present-page coverage: `7/7 = 1.0` — PASS;
- absent-page specificity: `0/1 = 0.0` — **FAIL** (`1.0` required);
- five-line count correctness: `1.0` — PASS;
- line-order correctness: `1.0` — PASS;
- six-line/TAB regression rejection: `1.0` — PASS;
- byte-repeat determinism: PASS;
- source identity: `8/8 = 1.0` — PASS.

Because all qualification criteria are conjunctive, the official result is:

`QUALIFICATION_COMPLETE_REJECTED_CURRENT_DETECTOR`

`detectorQualified=false` and `sourceDetectorAdequacyEstablished=false` remain binding.

The primary observed failure mode is false-positive control rather than source recall. The detector found most true systems but produced too many extra systems and produced five standard-staff predictions on the single teacher-confirmed staff-absent page.

The result binding is `evidence/stage11/v2d/v2d-staff-line-independent-holdout-qualification-result-binding.v1.json`.

## Consumed-holdout rule

The one authorized independent holdout is consumed. It may not be used to retune v1.2, move thresholds, derive page-specific rules, or function as an informal development set.

Any future staff-line candidate must be separately versioned and developed from non-holdout development evidence only. Another independent qualification requires a new candidate freeze and a new explicit holdout authorization.

## Next safe engineering boundary

If staff-line work continues, the next candidate should target general false-positive suppression while preserving the recall gains already demonstrated. Candidate development may investigate generic source-derived negative evidence, stronger rejection of text/decorative horizontal structures, bounded spacing/support checks and auditable confidence/routing logic, but must not tune against the consumed Chopin holdout.

The sequence remains:

1. create a separately versioned candidate (for example v1.3);
2. develop and tune only on authorized non-holdout development evidence;
3. freeze code/config/raw candidate output before evaluation claims;
4. establish development readiness without using the consumed holdout for tuning;
5. freeze any changed qualification policy before another fresh holdout;
6. obtain a new explicit authorization for another genuinely independent holdout;
7. only after source-detector qualification may restored-output staff-topology comparison be considered under a separate authorization.

## Closed gates

All of the following remain false/closed:

- `detectorQualified`;
- `staff_line=PASS`;
- `sourceDetectorAdequacyEstablished`;
- restored-output staff-topology comparison;
- semantic preservation establishment;
- overall Stage 11 PASS;
- production promotion/readiness;
- Stage 12 entry;
- PR #211 merge or ready-for-review transition.

The authoritative live staff-line holdout overlay is `docs/live/ST_SCORE_RESTORE_STAGE11_V2D_STAFF_LINE_HOLDOUT_CURRENT_TRUTH.json`.
