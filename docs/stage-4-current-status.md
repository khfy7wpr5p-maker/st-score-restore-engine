# Stage 4 Current Status — Safety Calibration

**State:** ENTRY/START CANDIDATE / NOT YET PRODUCTION-EFFECTIVE  
**Tracking:** Issue #104  
**Stage 3 production truth:** `2aac96faffcf46e71c41cfb2a37b36597e95e664` / Run #257 (`33655490406`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4 framework decision:** `evidence/stage4/governance/stage4-entry-start.v1.json`  
**Decision canonical SHA-256:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`

## Scope of this start slice

This slice authorizes only the Stage 4 calibration framework and synthetic contract tests after it becomes production-effective. It does **not** authorize real-data calibration, production threshold changes, resource-limit changes, model training or publication.

`src/st_score_restore/stage4_calibration.py` introduces deterministic observation/candidate contracts, candidate provenance freeze, held-out evaluation, false-negative/false-positive/coverage metrics and source-family anti-leakage checks. It deliberately does not contain an automatic real-data threshold-selection routine.

## Real-data permission state

The accepted Stage 1 catalog currently has no granted `safety_calibration` permission. Existing Stage 3 purpose grants are `pdf_pipeline_evaluation` only and explicitly retain `calibrationAuthorized=false`.

Therefore:

- real development calibration requires a separate exact-artifact `safety_calibration` grant;
- held-out real evidence remains `held_out_evaluation` only;
- held-out observations may evaluate a frozen candidate but may never derive, select or tune a candidate;
- real data stays fail-closed in the Stage 4 framework until a separate purpose-bound execution layer authorizes it;
- real corpus and derivative bytes remain outside ordinary Git.

## Anti-leakage invariants

1. Candidate derivation is development-only.
2. Held-out observations cannot enter candidate derivation.
3. Candidate derivation source families cannot overlap held-out evaluation source families.
4. Evaluation results are never fed back into the candidate.
5. General project approval is not treated as a dataset purpose grant.
6. No production threshold/resource-limit change is authorized by this framework slice.

## Metrics defined by the framework

Where reference labels exist, the framework can report exact-match, false-negative and false-positive counts/rates, coverage/not-assessed rates, deterministic candidate/report digests and source-family leakage count.

Numerical acceptance targets are intentionally **not invented** before purpose-authorized real calibration evidence and accepted reference labels exist.

## Current blockers for real calibration

- `no_real_artifact_has_granted_safety_calibration_permission`;
- `no_real_calibration_reference_label_bundle_is_accepted`.

These blockers do not prevent framework implementation or synthetic anti-leakage tests. They do prevent real-data threshold or resource-limit calibration.

## Transition rule

Until this entry/start slice passes exact-head CI, merges and receives successful post-merge main CI, repository truth remains **Stage 4 ENTRY ELIGIBLE / NOT STARTED**. After that production checkpoint, a separate current-truth update may mark Stage 4 ACTIVE for framework/governance work while keeping `calibrationAuthorized=false` and `realDataCalibrationExecuted=false`.
