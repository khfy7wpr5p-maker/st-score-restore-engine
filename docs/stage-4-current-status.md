# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY  
**Readiness:** NOT_READY  
**Tracking:** Issue #104  
**Latest production main:** `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75`  
**Latest post-merge CI:** Run #267 (`33670331093`) — Python 3.11 / 3.12 SUCCESS  
**Real-data calibration:** BLOCKED / NOT AUTHORIZED  
**Stage 5:** NOT STARTED / BLOCKED pending Stage 4 final exit PASS

## Production Stage 4 chain

- Framework start: PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259 (`33659753403`).
- Reference-label contract v0.1.0: PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263 (`33668750227`).
- Public calibration-evidence contract v0.1.0: PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265 (`33669674783`).
- Exit-readiness contract v0.1.0: PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267 (`33670331093`).

Stage 4 entry/start decision remains historical and immutable: `evidence/stage4/governance/stage4-entry-start.v1.json`, canonical SHA-256 `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

## What is production-effective

`src/st_score_restore/stage4_calibration.py` defines deterministic calibration observations/candidates, development-only derivation, held-out evaluation without feedback, aggregate comparison metrics and source-family anti-leakage.

`src/st_score_restore/stage4_reference_labels.py` requires real development labels to have exact `safety_calibration` purpose permission plus human expert-review provenance; held-out labels remain `held_out_evaluation`. Purpose permission alone does not accept a real reference-label bundle. Model/prediction fields cannot become reference evidence.

`src/st_score_restore/stage4_calibration_evidence.py` defines synthetic-only public-safe candidate/evaluation receipts. Public evidence contains digests and aggregate metrics, not row-level results, reviewer/provenance references, dataset/source-family identities or artifact/derivative bytes. It does not authorize real calibration.

`src/st_score_restore/stage4_exit_readiness.py` deterministically evaluates readiness. It can return only `NOT_READY` or `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; it can never set `stage4ExitPass=true` or authorize Stage 5.

## Current deterministic readiness decision

**Decision:** `NOT_READY`.

Current prerequisite blocker codes:

1. `no_real_artifact_has_granted_safety_calibration_permission`
2. `no_real_calibration_reference_label_bundle_is_accepted`
3. `no_real_development_calibration_evidence_is_accepted`
4. `no_real_held_out_evaluation_evidence_is_accepted`
5. `no_stage4_metric_acceptance_target_policy_is_accepted`

Even after all five prerequisites are eventually resolved, readiness can advance only to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. A separate evidence-bound final governance acceptance, exact-head CI, merge and post-merge CI are required before Stage 4 PASS can exist.

## Non-bypass safety rules

- Accepted Stage 1 catalog currently has zero granted `safety_calibration` permissions.
- Existing Stage 3 purpose grants remain `pdf_pipeline_evaluation`; `calibrationAuthorized=false`.
- Held-out evidence may evaluate a frozen candidate but cannot derive, select or tune thresholds/resource limits.
- Cross-split source-family leakage is forbidden.
- Historical evidence must remain immutable.
- Real corpus and derivative bytes remain outside ordinary Git.
- No numerical metric acceptance target has been accepted or invented.
- No production threshold/resource-limit change is authorized by framework/readiness contracts.
- Model training and publication remain unauthorized.

## Production behavior remains unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate pixels; 8,000-pixel maximum dimension; page-object depth 15.

Current claims remain:

- `calibrationAuthorized=false`;
- `realDataCalibrationExecuted=false`;
- `thresholdsCalibrated=false`;
- `resourceLimitsCalibrated=false`;
- `heldOutTuningUsed=false`;
- `stage4ExitPass=false`;
- `stage5EntryEligible=false`.

The separate sensitive `Fly Me to the Moon` phone-photo path remains independently blocked pending real high-assurance-vault verification.