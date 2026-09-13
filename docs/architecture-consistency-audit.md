# Architecture Consistency Audit — 2026-09-03

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Wikimedia expansion baseline:** main `9d2326931707f65c7eb5f5b22680e8fa85665a60` / PR #125 / Run #324 (`33728459668`) SUCCESS  
**Human-label completion checkpoint:** main `2ce6151e7ce37198c5b264ddd577df71f49da8bf` / PR #128 / Run #340 (`33745945427`) SUCCESS  
**Reference-bundle acceptance checkpoint:** main `3353b281a4022f107929fae296368390da45a4fb` / PR #130 / Run #348 (`33748180036`) SUCCESS  
**Stage 1:** COMPLETE / PASS / production-effective  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 4:** ACTIVE / NOT_READY  
**Stage 5:** BLOCKED pending Stage 4 final exit PASS  
**Latest architecture overlay:** 2026-09-13 — Stage 11 V2d `staff_line` independent holdout qualification complete / current detector rejected

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence is immutable. Purpose grants, human completion, reference-bundle acceptance, execution authorization, execution evidence, and later corpus-expansion overlays are separate artifacts; later facts never rewrite earlier evidence.

## Current findings

| Area | Current result |
|---|---|
| Stage 1 final exit | PASS / EFFECTIVE |
| Stage 2 final exit | PASS / EFFECTIVE |
| Stage 3 final exit | PASS / EFFECTIVE |
| Stage 4 framework | ACTIVE |
| Stage 4 readiness | NOT_READY / 3 blockers |
| Beethoven+Barley real execution | EXECUTED / ABSTAINED |
| Private observation accounting | 42 identities = 24 measured + 18 `not_applicable` |
| Measured development source families | 1 |
| Threshold candidates | 0 |
| Development execution evidence accepted | false |
| Wikimedia development expansion | production-effective via PR #125 / main `9d2326931707f65c7eb5f5b22680e8fa85665a60` / Run #324 |
| Wikimedia human labels | complete via separate PR #128 evidence: 7/7 `clear` |
| Wikimedia completion snapshot state | `human_labels_complete_pending_separate_acceptance` |
| Wikimedia reference bundle | accepted via separate PR #130 evidence |
| Wikimedia candidate derivation | eligible |
| Wikimedia execution authorization | false |
| Wikimedia execution | false |
| Chopin | consumed once as Stage 11 `staff_line` independent qualification evidence; forbidden for tuning |
| Production thresholds/resources | UNCALIBRATED ENGINEERING DEFAULTS / unchanged |
| Stage 5 | BLOCKED |

## Immutable historical anchors

The audit retains all historical bindings required by the architecture contract:

- Stage 3 purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`;
- Stage 3 execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`;
- Stage 3 limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`;
- Stage 3 final acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`;
- Stage 4 framework main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- Stage 4 entry/start digest `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`;
- Beethoven+Barley purpose main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272; digest `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`;
- accepted Beethoven+Barley reference bundle main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282; bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`; acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- historical exact execution authorization main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287; authorization digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`;
- Wikimedia reference-bundle acceptance main `3353b281a4022f107929fae296368390da45a4fb` / Run #348; bundle digest `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`; acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`.

The old authorization record remains **AUTHORIZED / NOT YET EXECUTED** with `executed=false`. This is a historical compatibility anchor, not the current execution state.

## Current Stage 4 evidence chain

The Beethoven+Barley run subsequently executed. Public-safe execution evidence digest is `0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a`; private metric-batch digest is `5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079`. The execution abstained because support was insufficient, so thresholds/resource limits remain uncalibrated.

PR #125 added the separate Wikimedia development purpose overlay with canonical digest `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07` for `dataset.item.wikimedia-guitar-technical-exercise-no1.v1` / `source.family.wikimedia-guitar-technical-exercise-no1.v1`.

PR #128 then added separate human completion evidence from genuine `human_expert_review`: all seven findings are `clear`; work-package digest is `9ccec309f611f8057b8b4a20a1aba732544c1638f2b959656b9503718206337c`; completion bundle digest is `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`.

That immutable completion snapshot correctly remains `human_labels_complete_pending_separate_acceptance` and does not retroactively claim acceptance. PR #130 separately records governance decision `ACCEPT_REAL_REFERENCE_BUNDLE`, acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`, and makes the exact development bundle candidate-derivation eligible. PR #130 does **not** authorize execution, threshold/resource changes, held-out evaluation, Stage 4 PASS, or Stage 5 entry.

## Human-reference boundary

The Wikimedia review work package has exactly seven finding slots: `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`. Allowed labels: `clear`, `possible`, `probable`, `not_assessed`. The original work package remains null-filled and immutable by design; completed human records and their later governance acceptance are separate evidence artifacts.

Model predictions, automated quality findings, or private raw metrics cannot be promoted to reference truth. Human completion and governance acceptance remain separate decisions.

## Held-out boundary

Chopin `dataset.item.imslp82860-chopin-op69.v2` remains a held-out source by dataset role. It was later consumed exactly once by the separately authorized Stage 11 V2d `staff_line` qualification workflow. That consumption does not make it development data. It remains forbidden for candidate construction, threshold selection, page-specific tuning or model training.

## Current readiness blockers

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Resolved historical blockers remain historical only; none of the three historical Stage 4 blockers is silently rewritten by later Stage 11 work.

## Stage 11 V2d current architecture overlay — 2026-09-13

This section is a later architecture overlay and does not rewrite the historical Stage 4 evidence above.

### Current Stage 11 semantic-preservation chain

The frozen V2a Restore package remains unchanged. V2c/V2d evaluates semantic preservation through class-specific evidence that is independent of the restoration candidate. The current class matrix remains conservative:

- `PASS`: `notehead` at canonical class-evidence level only;
- `REVIEW_ONLY`: `clef`;
- `REJECTED_CURRENT_DETECTOR`: `accidental`, `barline`, `beam_or_flag`, `rest`, `staff_line`, `stem`;
- `UNSUPPORTED`: `tab_digit`, `tab_line`, `tab_string`, `tie_or_slur`.

Neither class-level progress nor detector development establishes overall semantic preservation.

### Staff-line teacher truth and policy boundary

Independent teacher staff topology is complete on the existing development corpus:

- 20/20 pages complete;
- 18 staff-present pages;
- 2 staff-absent pages;
- 197 confirmed systems;
- 985 confirmed lines;
- 0 ambiguous systems;
- teacher raw SHA-256 `28ea439c30ca75a7935f310a0ae413c50769ba3f457d23f0d2132192555350a7`.

Before any fresh independent holdout access, the qualification policy was frozen at `evidence/stage11/v2d/v2d-staff-line-source-detector-qualification-policy.v1.json` with status `FROZEN_PRE_HOLDOUT`. The policy explicitly separates development readiness from qualification.

### Staff-line development progression

All comparable diagnostics below are on the already-spent 20-page development corpus. They are development evidence, not qualification evidence.

| Diagnostic | baseline | v1 | v1.1 | v1.2 |
|---|---:|---:|---:|---:|
| predicted systems | 10 | 89 | 114 | 187 |
| 0.5-spacing one-to-one matches | 10 | 71 | 91 | 141 |
| teacher-system recall | 0.050761 | 0.360406 | 0.461929 | **0.715736** |
| predicted-system precision | 1.000000 | 0.797753 | 0.798246 | **0.754011** |
| staff-present page coverage | 10/18 | 15/18 | 18/18 | **18/18** |
| staff-absent specificity | 2/2 | 2/2 | 2/2 | **2/2** |

Frozen v1.2 additionally preserves five-line count correctness 1.0, line-order correctness 1.0, source identity 20/20 and byte-repeat determinism. Its synthetic six-line TAB-like regression control is rejected 1/1. Local v1.2 regression tests are 8/8 PASS.

The frozen v1.2 development raw artifact SHA-256 is `b89241345e9ae6d58dd010c111e76bd724f68272fb5b18d6bb3fbf6b02a4ac76`. The scoring implementation reproduced the frozen v1 compatibility anchor of 71/197 matches before scoring v1.2.

V1.2 exceeded the predeclared development-readiness floors and therefore justified requesting an independent qualification. It did not qualify the detector by itself.

### Source identity reconciliation

The v1.2 freeze used the exact current v1.1 parent blob `deb988a359f2f2526c484b2cd49b57597c7733db`, whose current byte SHA-256 is `e676f29889965f33178e3252580b8b358a1d36b3c0691ac7a77928e5484230b5`. The older immutable v1.1 development binding records a different historical SHA-256 (`cb6271d...`). That historical binding was not rewritten. The discrepancy is recorded separately in `evidence/stage11/v2d/v2d-staff-line-v1_1-source-identity-reconciliation.v1.json`.

### Independent holdout qualification — complete

Exactly one fresh independent holdout was separately authorized. The holdout was the pre-existing Chopin Op.69 held-out item. All eight pages were used with no cherry-picking.

The frozen v1.2 holdout raw artifact:

- page count: 8;
- source identity: 8/8;
- predicted systems: 128;
- raw SHA-256: `f2ef8a352d9c1f26e7c460ed0f71b125a33e35838294f741d562ce81d4b077fb`;
- byte-repeat determinism: verified;
- teacher truth accessed before raw freeze: false;
- teacher coordinates used during inference: false;
- restored outputs used during inference: false;
- post-holdout retuning: false.

Independent teacher truth was then completed and frozen:

- pages: 8/8;
- staff-present pages: 7;
- staff-absent pages: 1;
- confirmed systems: 88;
- teacher truth SHA-256: `3b83642b162285eb9cb4b6f806ad82d657eac980003159366ca72b5cef47cfb3`.

Before holdout scoring, the scorer reproduced the historical v1 anchor exactly: 71/197.

The holdout was then scored exactly once against the pre-frozen conjunctive policy:

| Qualification metric | Observed | Required | Result |
|---|---:|---:|---|
| teacher-system recall @ 0.5 spacing | 0.9090909091 | >= 0.65 | PASS |
| predicted-system precision | 0.625 | >= 0.80 | **FAIL** |
| present-page coverage | 1.0 | >= 0.95 | PASS |
| absent-page specificity | 0.0 | 1.0 | **FAIL** |
| five-line count correctness | 1.0 | 1.0 | PASS |
| line-order correctness | 1.0 | 1.0 | PASS |
| six-line/TAB rejection | 1.0 | 1.0 | PASS |
| source identity | 1.0 | 1.0 | PASS |
| byte-repeat determinism | true | required | PASS |

The official result is `QUALIFICATION_COMPLETE_REJECTED_CURRENT_DETECTOR`.

`detectorQualified=false`, `sourceDetectorAdequacyEstablished=false`, and `staff_line=PASS=false` remain binding.

The current failure mode is primarily false-positive control, not source recall. The detector matched 80/88 teacher-confirmed systems but generated 128 predictions overall and five false standard-staff predictions on the single teacher-confirmed staff-absent page.

### Consumed-holdout stop gate

The architecture boundary is now:

1. source-only v1.2 development — complete;
2. development source freeze and scoring — complete;
3. qualification policy frozen before holdout — complete;
4. one independent holdout authorization — consumed;
5. blind teacher truth — complete/frozen;
6. scorer compatibility gate — PASS;
7. independent holdout scoring — complete exactly once;
8. detector qualification — **FAILED**;
9. retuning v1.2 against the consumed holdout — **forbidden**;
10. restored-output staff-topology comparison — **closed**;
11. semantic-preservation PASS, production and Stage 12 governance — **closed**.

Any future candidate must be separately versioned and developed using non-holdout development evidence only. A new independent holdout requires a new candidate freeze and a new explicit authorization.

### Stage 11 safety truth

The following remain false:

- `freshIndependentHoldoutAuthorized`;
- `restoredImageTopologyComparisonAuthorized`;
- `detectorQualified`;
- `sourceDetectorAdequacyEstablished`;
- `staffLinePass`;
- `semanticPreservationEstablished`;
- `overallStage11PassAuthorized`;
- `productionReady`;
- `productionPromotionAuthorized`;
- `stage12EntryAuthorized`;
- `prReadyForMerge`.

PR #211 remains Draft/open/unmerged. Merge is a separate authorization decision.

## Consistency conclusion

The architecture remains consistent only when historical checkpoints, immutable evidence, source-only candidate development, teacher scoring, qualification policy, independent holdout evidence, restored-output comparison and production authorization remain distinct layers.

The staff-line line has now advanced far enough to identify a clearer technical bottleneck: v1.2 has strong independent source recall but insufficient precision and absent-page specificity. The next safe engineering boundary is a separately versioned candidate focused on **generic false-positive suppression**, developed only with authorized non-holdout evidence. The consumed Chopin holdout must not be used for threshold selection or page-specific tuning. Another qualification requires a fresh candidate freeze and a new explicit holdout authorization. Restored-output topology comparison remains closed.
