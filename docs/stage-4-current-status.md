# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — REAL DEVELOPMENT CALIBRATION EXECUTED / ABSTAINED / EVIDENCE NOT YET ACCEPTED  
**Readiness:** NOT_READY / 3 remaining prerequisite blockers  
**Tracking:** Issue #104  
**Latest production main:** `4f0346345eb770628928ba1751b4a1d9d5fb51f1`  
**Latest post-merge CI:** Run #304 (`33725160737`) — Python 3.11 / 3.12 SUCCESS  
**Real calibration execution:** EXECUTED for exact Beethoven + Barley development scope; candidate thresholds derived: 0  
**Private-metric runner production baseline:** v0.2.0 from PR #122 → main `1c0b27d9284129577a85bc4d536ac118446a4e8c` → Run #302 SUCCESS  
**private observation metrics:** exact 42 identities accounted for as 24 measured + 18 fail-closed `not_applicable`; raw measured values remain custody-only  
**Candidate derivation methodology:** `strict_empirical_midpoint_boundary_v1`; all six measurable findings abstained; compression had no measured development observations  
**Execution evidence:** PR #123 → main `4f0346345eb770628928ba1751b4a1d9d5fb51f1` → Run #304 SUCCESS; public-safe evidence frozen, governance acceptance still false  
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
- Metric applicability correction / runner v0.2.0: PR #122 → main `1c0b27d9284129577a85bc4d536ac118446a4e8c` → Run #302 (`33722949483`) SUCCESS.
- Real development execution evidence: PR #123 exact head `3f396c4cd693cb0d0b1cc0d90d9775cd8596c0c4` → Run #303 (`33725033413`) SUCCESS → main `4f0346345eb770628928ba1751b4a1d9d5fb51f1` → Run #304 (`33725160737`) SUCCESS.

Stage 4 entry/start decision canonical SHA-256 remains `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 safety-calibration purpose-grant overlay canonical SHA-256 remains `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

Reference and execution evidence digests:
- work package `93e1a61bbdd698dbabf1ba88164453056acf3f2ea37fa159305a0f244b2253ba`;
- human completion `3434e74e7d993db2384711f9c6c31f31d148c65bc5896bd120f82b5dcab2e1fd`;
- bundle `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`;
- accepted receipt `f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33`;
- acceptance `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- execution authorization `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`;
- private metric batch `5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079`;
- real development execution evidence `0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a`.

## Real development execution result

The authorized development run has now been executed inside the private boundary.

Exact applicability remained **24 measured + 18 not-applicable**:

- Beethoven: skew, blur, glare, shadow, uneven lighting and noise were measured on four canonical Stage 3 PNG derivatives = 24 measured rows.
- Beethoven compression: four `not_applicable` rows because the canonical derivative is PNG and the Stage 2 compression metric is JPEG-only.
- Barley: fourteen `not_applicable` rows because the source pages are vector-only and Stage 3 correctly preserved them without rasterization.

The private batch is bound by SHA-256 only in public evidence; raw metric values and row identities remain outside ordinary Git.

Candidate derivation produced no threshold candidate:

- `skew`: abstained;
- `blur`: abstained;
- `glare`: abstained;
- `shadow`: abstained;
- `uneven_lighting`: abstained;
- `noise`: abstained;
- `compression`: no measured development observations / not applicable.

For every measurable finding, the measured evidence came from only one source family and the required `clear` / `possible` / `probable` class support was incomplete. The production methodology therefore abstained rather than inventing thresholds.

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

Historical Stage 1 catalog, earlier Stage 4 purpose/reference decisions, execution authorization and pre-execution current-truth checkpoints remain immutable.

Historical pre-execution compatibility anchor: the production authorization/current-truth checkpoint recorded the development scope as authorized / not yet executed with `realDataCalibrationExecuted=false`. That statement is historical only; the current execution truth below is `realDataCalibrationExecuted=true` after PR #123 / Run #304.

## Current non-claims

- `realDataCalibrationExecutionAuthorized=true`;
- `calibrationAuthorized=true` for the exact development execution scope only;
- `realDataCalibrationExecuted=true`;
- `executionEvidenceAccepted=false`;
- `thresholdsCalibrated=false`;
- `resourceLimitsCalibrated=false`;
- no numerical metric acceptance target policy has been accepted;
- production threshold/resource changes unauthorized;
- training/publication unauthorized;
- held-out tuning unauthorized;
- held-out evaluation has not been executed;
- `stage4ExitPass=false`;
- `stage5EntryEligible=false`.

## Current deterministic readiness decision

**Decision:** `NOT_READY`.

Remaining blocker codes:

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Resolved blockers remain `no_real_artifact_has_granted_safety_calibration_permission` and `no_real_calibration_reference_label_bundle_is_accepted`.

The new execution receipt does not itself resolve blocker 1 because its governance acceptance remains separate and the result contains no frozen threshold candidate. Even after accepting the receipt as an accurate record, additional development evidence is required before held-out candidate evaluation can be meaningful.

Even after all remaining prerequisites are resolved, readiness can only advance to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. Separate evidence-bound final governance acceptance, exact-head CI, merge and post-merge CI remain mandatory before Stage 4 PASS.

## Production behavior remains unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate pixels; 8,000-pixel maximum dimension; page-object depth 15.

No numerical threshold or metric acceptance target was invented by the real development execution.

## Immediate next dependency

The safe next substantive step is corpus expansion on the **development** side: add at least one separately authorized, human-labelled raster source family with genuinely comparable measured metrics and sufficient `clear` / `possible` / `probable` class support. The current exact corpus cannot satisfy the production candidate methodology because all 24 measured rows belong to one source family.

Chopin remains untouched. Held-out evaluation must not start until a frozen development candidate exists and a separate held-out evaluation boundary is satisfied.
