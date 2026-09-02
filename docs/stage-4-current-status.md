# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY  
**Readiness:** NOT_READY / 4 remaining prerequisite blockers  
**Tracking:** Issue #104  
**Latest purpose-grant production main:** `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd`  
**Latest post-merge CI:** Run #272 (`33672903071`) — Python 3.11 / 3.12 SUCCESS  
**Real calibration execution:** BLOCKED / NOT AUTHORIZED  
**Stage 5:** NOT STARTED / BLOCKED pending Stage 4 final exit PASS

## Production Stage 4 chain

- Framework start: PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259.
- Reference-label contract v0.1.0: PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263.
- Public calibration-evidence contract v0.1.0: PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265.
- Exit-readiness contract v0.1.0: PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267.
- Safety-calibration purpose grants: PR #111 exact head `dce3da9184d5995fa57534e1bd978ea4dfd614a5` → Run #271 (`33672712230`) SUCCESS → main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` → Run #272 (`33672903071`) SUCCESS.

Stage 4 entry/start decision canonical SHA-256 remains `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 safety-calibration purpose-grant overlay canonical SHA-256 is `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

## What changed

The first readiness prerequisite is resolved production-effectively:

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1`, SHA `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`: development-only `safety_calibration` purpose granted.
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`, SHA `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`: development-only `safety_calibration` purpose granted.
- Chopin `dataset.item.imslp82860-chopin-op69.v2`, SHA `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`: remains held-out `held_out_evaluation`; candidate derivation/tuning forbidden.

Historical Stage 1 catalog remains immutable; its old `safety_calibration=not_requested` fields are not rewritten. Stage 4 uses an immutable purpose-grant overlay.

## What did not change

A purpose grant is not execution authorization. The overlay explicitly retains:

- `realDataCalibrationExecutionAuthorized=false`;
- `referenceLabelBundleAccepted=false`;
- training/publication/demonstration/external export unauthorized;
- held-out tuning unauthorized.

Therefore `calibrationAuthorized=false`, `realDataCalibrationExecuted=false`, `thresholdsCalibrated=false`, `resourceLimitsCalibrated=false`, `heldOutTuningUsed=false`, `stage4ExitPass=false`, and `stage5EntryEligible=false` remain true current-state constraints.

## Current deterministic readiness decision

**Decision:** `NOT_READY`.

Remaining blocker codes:

1. `no_real_calibration_reference_label_bundle_is_accepted`
2. `no_real_development_calibration_evidence_is_accepted`
3. `no_real_held_out_evaluation_evidence_is_accepted`
4. `no_stage4_metric_acceptance_target_policy_is_accepted`

The removed blocker is `no_real_artifact_has_granted_safety_calibration_permission`; it is now satisfied by two exact development grants.

Even after all remaining prerequisites are resolved, readiness can only advance to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. Separate evidence-bound final governance acceptance, exact-head CI, merge and post-merge CI are still required before Stage 4 PASS.

## Production behavior remains unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate pixels; 8,000-pixel maximum dimension; page-object depth 15.

## Next substantive action

Prepare and complete a human-reviewed real reference-label bundle for the authorized Beethoven + Barley development artifacts. No human labels have been supplied or accepted yet, so no real calibration execution may start. Model predictions or automatic analysis must not be substituted for human reference truth.
