# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — REAL DEVELOPMENT CALIBRATION EXECUTION AUTHORIZED / NOT YET EXECUTED  
**Readiness:** NOT_READY / 3 remaining prerequisite blockers  
**Tracking:** Issue #104  
**Latest execution-authorization production main:** `76f5643dde72c8cc4b02b517133331e9dea00146`  
**Latest post-merge CI:** Run #287 (`33686039783`) — Python 3.11 / 3.12 SUCCESS  
**Real calibration execution:** AUTHORIZED for exact Beethoven + Barley development scope / NOT YET EXECUTED  
**Immediate execution dependency:** private observation metrics are not available in ordinary Git or known Stage 3 Actions artifacts  
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

The exact-scope execution boundary is now production-effective:

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1`, SHA `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`: development-only `safety_calibration`; execution authorized.
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, SHA `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`: development-only `safety_calibration`; execution authorized.
- Their 42 human-reviewed labels remain accepted: 36 `clear`, 5 `possible`, 1 `probable`, 0 `not_assessed`.
- Execution authorization is digest-bound to the existing purpose grant, reference-bundle acceptance, accepted reference receipt and bundle.
- Raw/private observation metrics are required for actual execution and remain forbidden in ordinary Git.
- Chopin `dataset.item.imslp82860-chopin-op69.v2`, SHA `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`: remains held-out `held_out_evaluation`; this authorization does not authorize its evaluation and candidate derivation/tuning remains forbidden.

Historical Stage 1 catalog, Stage 4 purpose grant and Stage 4 reference acceptance remain immutable; the new execution decision is a separate immutable governance overlay.

## What did not change

Authorization is not execution evidence. Current constraints remain:

- `realDataCalibrationExecutionAuthorized=true`;
- `calibrationAuthorized=true` for the exact development execution scope only;
- `realDataCalibrationExecuted=false`;
- `thresholdsCalibrated=false`;
- `resourceLimitsCalibrated=false`;
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

Execution authorization is deliberately not a readiness prerequisite and therefore does not reduce the three blockers until accepted real development calibration evidence exists.

Even after all remaining prerequisites are resolved, readiness can only advance to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. Separate evidence-bound final governance acceptance, exact-head CI, merge and post-merge CI are still required before Stage 4 PASS.

## Production behavior remains unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate pixels; 8,000-pixel maximum dimension; page-object depth 15.

No numerical threshold or metric acceptance target was invented by the execution authorization.

## Immediate execution dependency

The actual development calibration run requires private observation metrics (`metricName` + `rawValue`) bound 1:1 to the accepted 42 observation IDs. Repository search found no public Beethoven/Barley raw Stage 4 metric values. Historical Stage 3 Run #246 (`33641537118`) and Run #251 (`33645607053`) expose no GitHub Actions artifacts. Therefore metric values cannot be reconstructed from current public Git/Actions evidence and must not be fabricated.

## Next substantive action

Build/finalize a fail-closed **private observation-metric input + development calibration runner contract** that consumes exact Beethoven + Barley metrics outside ordinary Git, validates 1:1 binding to the accepted labels and authorization, and emits only public-safe aggregate/digest evidence. Actual execution can occur only when that private metric input is available. Chopin remains untouched until a separate held-out evaluation authorization/evidence boundary is reached.
