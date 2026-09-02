# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY  
**Tracking:** Issue #104  
**Framework start PR:** #105  
**Framework production main:** `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`  
**Post-merge CI:** Run #259 (`33659753403`) — Python 3.11 / 3.12 SUCCESS  
**Entry/start decision:** `evidence/stage4/governance/stage4-entry-start.v1.json`  
**Decision canonical SHA-256:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`  
**Real-data calibration:** BLOCKED / NOT AUTHORIZED

## What ACTIVE means

Stage 4 has started only for calibration framework and governance work. The production framework can define and validate calibration observations, threshold candidates, reference-label comparisons, deterministic evidence, metrics and anti-leakage behavior.

ACTIVE does **not** mean real-data calibration has run. Real-data calibration is **not authorized** in the current state.

## Production framework

`src/st_score_restore/stage4_calibration.py` provides:

- deterministic `CalibrationObservation` contracts;
- deterministic `ThresholdCandidate` contracts;
- development-only candidate provenance freeze;
- held-out evaluation without feedback into candidate selection;
- cross-split source-family leakage rejection;
- exact-match, false-negative, false-positive and coverage/not-assessed metrics;
- candidate/report canonical digests;
- fail-closed real-data execution by default.

Synthetic contract tests prove held-out observations cannot derive a candidate and source-family overlap is rejected.

## Real-data permission state

The accepted Stage 1 catalog currently has **zero granted `safety_calibration` permissions**. Stage 3 purpose grants remain exact `pdf_pipeline_evaluation` grants and retain `calibrationAuthorized=false`.

Real development calibration therefore requires a new, exact-artifact, production-effective `safety_calibration` purpose grant. Held-out real evidence remains `held_out_evaluation` only and may never tune or select thresholds/resource limits.

## Current blockers for real calibration

- `no_real_artifact_has_granted_safety_calibration_permission`;
- `no_real_calibration_reference_label_bundle_is_accepted`.

Until both are resolved through separate evidence-bound governance, the following remain false:

- `calibrationAuthorized`;
- `realDataCalibrationExecuted`;
- `thresholdsCalibrated`;
- `resourceLimitsCalibrated`;
- `stage4ExitPass`;
- `stage5EntryEligible`.

## Production behavior unchanged

Stage 2 quality thresholds and Stage 3 PDF/resource limits remain `uncalibrated_engineering_defaults`. Framework start does not change 200 DPI, 64 pages, 40M pixels/page, 160M aggregate pixels, 8,000-pixel maximum dimension or page-object depth 15.

No model training, publication, OMR, musical inference, or real corpus byte export is authorized.

## Next autonomous safe work

Continue framework/governance hardening: define reference-label evidence contracts, calibration-candidate public-safe evidence schemas and deterministic validators. Do not execute real-data calibration or propose production threshold/resource-limit changes until explicit purpose grants and accepted reference-label provenance exist.

Stage 5 remains NOT STARTED / BLOCKED pending a separate Stage 4 final exit PASS.