# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — REAL DEVELOPMENT CALIBRATION EXECUTION AUTHORIZED / NOT YET EXECUTED  
**Readiness:** NOT_READY / 3 remaining prerequisite blockers  
**Tracking:** Issue #104  
**Latest production main:** `53fd096e31a111f35af0194cbd57640041e6319f`  
**Latest post-merge CI:** Run #298 (`33695083473`) — Python 3.11 / 3.12 SUCCESS  
**Real calibration execution:** AUTHORIZED for exact Beethoven + Barley development scope / NOT YET EXECUTED  
**Private-metric runner production baseline:** v0.1.0 from PR #119; applicability correction v0.2.0 is under validation on the current branch  
**Private observation metrics:** exact 42 identities remain required, with 24 measured values and 18 fail-closed `not_applicable` records; raw measured values remain custody-only  
**Candidate derivation methodology:** `strict_empirical_midpoint_boundary_v1` from PR #121 / production-effective; abstain-first  
**Stage 5:** NOT STARTED / BLOCKED pending Stage 4 final exit PASS

## Production Stage 4 chain

- Framework start: PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259.
- Reference-label contract v0.1.0: PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263.
- Public calibration-evidence contract v0.1.0: PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265.
- Exit-readiness contract v0.1.0: PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267.
- Safety-calibration purpose grants: PR #111 exact head `dce3da9184d5995fa57534e1bd978ea4dfd614a5` → Run #271 (`33672712230`) SUCCESS → main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` → Run #272 (`33672903071`) SUCCESS.
- Human review work package: PR #113 → main `7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12` → Run #278 (`33677035152`) SUCCESS.
- Completed human labels: PR #114 → main `58266dffed529a5d7d247e58651865bbda83981e` → Run #280 (`33677635302`) SUCCESS.
- Real development reference-bundle acceptance: PR #115 exact head `af0910f1542971576aabb98a66fddb163e9a5767` → Run #281 (`33680370670`) SUCCESS → main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` → Run #282 (`33680628749`) SUCCESS.
- Current-truth reference checkpoint: PR #116 → main `0c267cb9489cfe023a4d5e26104f5ae684cb95fb` → Run #285 (`33681777851`) SUCCESS.
- Real development calibration execution authorization: PR #117 exact head `b42ad45656299651897be33b7ea98d940217095c` → Run #286 (`33685839142`) SUCCESS → main `76f5643dde72c8cc4b02b517133331e9dea00146` → Run #287 (`33686039783`) SUCCESS.
- Execution-authorization current-truth checkpoint: PR #118 exact head `e83483bd0b40fc6a585ce95f1b88a283a70dc5ee` → Run #290 (`33687329899`) SUCCESS → main `d833255305315c89efa4aceb2816bd819d6ffd95` → Run #291 (`33687526381`) SUCCESS.
- Private observation-metric development runner contract v0.1.0: PR #119 exact head `74a05a4976bdeb5e81f88b8082289098d9eb5df4` → Run #292 (`33693675153`) SUCCESS → main `dd392f7be9522319d5d77074641b512dfdfdd930` → Run #293 (`33693904957`) SUCCESS.
- Private runner current-truth checkpoint: PR #120 → main `10c03a2f14bfd9980fc6833f5adb2c04497f74a4` → Run #296 (`33694483053`) SUCCESS.
- Abstain-first candidate derivation methodology: PR #121 exact head `06e9bfb424defd53a9c2a0e1077a861f7a9d478e` → Run #297 (`33694972501`) SUCCESS → main `53fd096e31a111f35af0194cbd57640041e6319f` → Run #298 (`33695083473`) SUCCESS.

Stage 4 entry/start decision canonical SHA-256 remains `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 safety-calibration purpose-grant overlay canonical SHA-256 remains `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

Reference evidence digests:
- work package `93e1a61bbdd698dbabf1ba88164453056acf3f2ea37fa159305a0f244b2253ba`;
- human completion `3434e74e7d993db2384711f9c6c31f31d148c65bc5896bd120f82b5dcab2e1fd`;
- bundle `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`;
- accepted receipt `f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33`;
- acceptance `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- execution authorization `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

## Metric applicability correction discovered during real execution preparation

Fresh execution preparation exposed a real contract mismatch that must be corrected before any private batch can be accepted:

- Stage 3 production evidence classifies Beethoven as four `raster_only` pages rendered as PNG derivatives.
- Stage 3 production evidence classifies Barley as two `vector_only` pages preserved without rasterization.
- Stage 2 `compression.score` is JPEG-only and returns non-applicable for PNG inputs.

Therefore the truthful current 42-observation applicability is **24 measured + 18 not-applicable**, not 42 numeric `rawValue` values:

- Beethoven: skew, blur, glare, shadow, uneven lighting and noise are measured on four canonical Stage 3 PNG derivatives = 24 measured rows.
- Beethoven compression: four `not_applicable` rows because the canonical derivative is PNG and the Stage 2 compression metric is JPEG-only.
- Barley: fourteen `not_applicable` rows because the source pages are vector-only and Stage 3 correctly preserved them without rasterization.

The v0.2.0 runner correction requires every accepted observation identity to remain present, but `not_applicable` rows must use `rawValue=null` with an exact reason. Numeric zero, placeholder or inferred values are forbidden as substitutes for unavailable measurements.

Only measured rows may be materialized into development calibration observations. With the current exact corpus, all measured rows come from the Beethoven source family, so the production candidate methodology's two-source-family requirement will force abstention. This is the intended fail-closed outcome; no threshold will be invented.

## Canonical metric semantics

- `skew` → `absoluteAngleDegrees`, higher is worse;
- `blur` → `laplacianVariance`, lower is worse;
- `glare` → `score`, higher is worse;
- `shadow` → `strength`, higher is worse;
- `uneven_lighting` → `coefficientOfVariation`, higher is worse;
- `noise` → `residualP90`, higher is worse;
- `compression` → `score`, higher is worse when the canonical Stage 2 JPEG metric is applicable.

## Exact authorized data remains unchanged

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1`, SHA `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`: development-only `safety_calibration`.
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, SHA `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`: development-only `safety_calibration`.
- Their 42 human-reviewed labels remain accepted: 36 `clear`, 5 `possible`, 1 `probable`, 0 `not_assessed`.
- Chopin `dataset.item.imslp82860-chopin-op69.v2`, SHA `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`: remains held-out `held_out_evaluation`; development candidate derivation/tuning remains forbidden.

Historical Stage 1 catalog, earlier Stage 4 purpose/reference decisions and execution authorization remain immutable.

## What did not change

- `realDataCalibrationExecutionAuthorized=true`;
- `calibrationAuthorized=true` for the exact development execution scope only;
- `realDataCalibrationExecuted=false`;
- `thresholdsCalibrated=false`;
- `resourceLimitsCalibrated=false`;
- no numerical metric acceptance target policy has been accepted;
- production threshold/resource changes unauthorized;
- training/publication unauthorized;
- held-out tuning unauthorized;
- held-out evaluation not authorized by the development execution decision;
- `stage4ExitPass=false`;
- `stage5EntryEligible=false`.

## Current deterministic readiness decision

**Decision:** `NOT_READY`.

Remaining blocker codes:

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Resolved blockers remain `no_real_artifact_has_granted_safety_calibration_permission` and `no_real_calibration_reference_label_bundle_is_accepted`.

Even after all remaining prerequisites are resolved, readiness can only advance to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. Separate evidence-bound final governance acceptance, exact-head CI, merge and post-merge CI remain mandatory before Stage 4 PASS.

## Production behavior remains unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate pixels; 8,000-pixel maximum dimension; page-object depth 15.

No numerical threshold or metric acceptance target was invented by PR #119, PR #121, or this applicability correction.

## Immediate execution dependency

After the applicability correction is production-effective, the exact 24 measurable Beethoven values can be validated inside approved custody while the remaining 18 observation identities are preserved as `not_applicable`. Raw private values remain outside ordinary Git. A public-safe receipt may contain only digests and aggregate applicability counts.

Because the measurable evidence currently comes from only one source family, candidate derivation will abstain. Progress beyond an abstained real development calibration result will require an additional authorized, human-labelled **raster** development source family (or another separately approved design that provides genuinely comparable measurements). Chopin remains untouched until a separate held-out evaluation authorization/evidence boundary is reached.
