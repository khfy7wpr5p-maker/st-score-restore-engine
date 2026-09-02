# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — REAL DEVELOPMENT CALIBRATION EXECUTION AUTHORIZED / NOT YET EXECUTED  
**Readiness:** NOT_READY / 3 remaining prerequisite blockers  
**Tracking:** Issue #104  
**Latest private-metric runner production main:** `dd392f7be9522319d5d77074641b512dfdfdd930`  
**Latest post-merge CI:** Run #293 (`33693904957`) — Python 3.11 / 3.12 SUCCESS  
**Real calibration execution:** AUTHORIZED for exact Beethoven + Barley development scope / NOT YET EXECUTED  
**Private-metric runner contract:** v0.1.0 / production-effective / exact 42-row fail-closed input boundary  
**Immediate execution dependency:** private observation metrics (`metricName` + `rawValue`) for the real 42-observation Beethoven + Barley batch are not available in ordinary Git or known historical Actions artifacts  
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

Stage 4 entry/start decision canonical SHA-256 remains `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 safety-calibration purpose-grant overlay canonical SHA-256 remains `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

Reference evidence digests:
- work package `93e1a61bbdd698dbabf1ba88164453056acf3f2ea37fa159305a0f244b2253ba`;
- human completion `3434e74e7d993db2384711f9c6c31f31d148c65bc5896bd120f82b5dcab2e1fd`;
- bundle `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`;
- accepted receipt `f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33`;
- acceptance `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- execution authorization `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

## What changed

The private observation-metric development runner contract is now production-effective.

It requires exactly 42 private metric rows and validates them fail-closed against the already accepted development scope. Each row must bind 1:1 to the accepted observation identity, dataset item, exact artifact SHA-256, source family, finding type, canonical metric name/direction, execution-authorization digest and accepted reference-bundle digest. The accepted human reference label is joined only inside the private execution boundary; private metric rows are forbidden from carrying `referenceLabel`, model predictions or reviewer identity.

Canonical Stage 4 metric semantics are fixed as contract metadata, not newly calibrated thresholds:

- `skew` → `absoluteAngleDegrees`, higher is worse;
- `blur` → `laplacianVariance`, lower is worse;
- `glare` → `score`, higher is worse;
- `shadow` → `strength`, higher is worse;
- `uneven_lighting` → `coefficientOfVariation`, higher is worse;
- `noise` → `residualP90`, higher is worse;
- `compression` → `score`, higher is worse.

The runner emits only a public-safe preparation receipt containing digests and aggregate counts. It does not expose raw metric values, observation rows, dataset/source-family identities, artifact bytes or derivative bytes. Repository validation additionally fails if Stage 4 evidence JSON in ordinary Git contains a `rawValue` field.

Exact authorized data remains:

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1`, SHA `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`: development-only `safety_calibration`.
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, SHA `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`: development-only `safety_calibration`.
- Their 42 human-reviewed labels remain accepted: 36 `clear`, 5 `possible`, 1 `probable`, 0 `not_assessed`.
- Chopin `dataset.item.imslp82860-chopin-op69.v2`, SHA `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`: remains held-out `held_out_evaluation`; development candidate derivation/tuning remains forbidden.

Historical Stage 1 catalog, earlier Stage 4 purpose/reference decisions and execution authorization remain immutable. The runner contract adds an execution-input boundary; it does not rewrite those decisions.

## What did not change

Runner readiness is not execution evidence. Current constraints remain:

- `realDataCalibrationExecutionAuthorized=true`;
- `calibrationAuthorized=true` for the exact development execution scope only;
- `realDataCalibrationExecuted=false`;
- `thresholdsCalibrated=false`;
- `resourceLimitsCalibrated=false`;
- no numerical threshold-selection policy has been accepted;
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

Resolved blockers are `no_real_artifact_has_granted_safety_calibration_permission` and `no_real_calibration_reference_label_bundle_is_accepted`.

The runner contract is deliberately not a readiness prerequisite and therefore does not reduce the three blockers until accepted real development calibration evidence exists.

Even after all remaining prerequisites are resolved, readiness can only advance to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. Separate evidence-bound final governance acceptance, exact-head CI, merge and post-merge CI remain mandatory before Stage 4 PASS.

## Production behavior remains unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate pixels; 8,000-pixel maximum dimension; page-object depth 15.

No numerical threshold or metric acceptance target was invented by PR #119.

## Immediate execution dependency

The next real step requires the actual private observation metrics (`metricName` + `rawValue`) for all 42 accepted Beethoven + Barley observations. They must be produced or supplied through approved custody outside ordinary Git and satisfy the production runner contract exactly. Historical Stage 3 Run #246 (`33641537118`) and Run #251 (`33645607053`) expose no GitHub Actions artifacts containing these values, so the values cannot be reconstructed from current public Git/Actions evidence and must not be fabricated.

## Next substantive action

Obtain or generate the exact private Beethoven + Barley observation metrics through approved custody, validate them 42/42 with `stage4_development_calibration_runner.py`, and freeze only a public-safe digest/count preparation receipt. After real development metrics exist, a separate evidence-bound candidate-derivation methodology may be applied; no numerical threshold may be invented in advance. Chopin remains untouched until a separate held-out evaluation authorization/evidence boundary is reached.
