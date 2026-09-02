# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 4 ACTIVE — exact real development calibration execution authorized / not yet executed / readiness NOT_READY  
**Date:** 2026-09-03  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Latest Stage 4 execution-authorization production main:** `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287 (`33686039783`) SUCCESS

## 1. Scope and invariants

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. It is not an OMR engine. Source bytes and historical evidence remain immutable; exact SHA-256 defines artifact identity; real corpus/derivative bytes and private raw observation metrics remain outside ordinary Git; held-out evidence never tunes thresholds/resources; purpose, reference-label provenance, execution authorization and final acceptance rules fail closed.

## 2. Processing architecture

```text
Input document
    ↓
Immutable source registration / structural inspection
    ↓
Rights / privacy / purpose / custody / exact-byte gates
    ↓
PDF page policy
    ├─ raster_only → bounded PDFium derivative
    ├─ vector_only → preserve vector content
    ├─ hybrid → preserve + review
    └─ unknown/over-limit → original fallback + review
    ↓
Deterministic quality analysis
    ↓
Restoration candidate / safety validation
    ↓
Original fallback / comparator eligibility
    ↓
ScoreMosaic Safe Intake → OMR → MusicXML
```

## 3. Runtime baseline

Python `>=3.11,<3.13`; CI Python 3.11/3.12; API `0.5.0`; exact PDF renderer `pypdfium2==5.13.0`. Production thresholds/resource values remain `uncalibrated_engineering_defaults`.

## 4. Historical production stages

Stage 1 COMPLETE / PASS.

Stage 2 COMPLETE / PASS. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Stage 3 COMPLETE / PASS. Immutable digests: purpose grants `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution evidence `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## 5. Stage 4 production framework/governance and execution-authorization chain

**State:** ACTIVE — EXACT DEVELOPMENT EXECUTION AUTHORIZED / NOT YET EXECUTED.  
**Readiness:** NOT_READY / 3 remaining prerequisite blockers.  
**Entry/start decision digest:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.  
**Safety-calibration purpose-grant digest:** `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.  
**Accepted reference-bundle digest:** `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`.  
**Reference acceptance digest:** `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`.  
**Execution-authorization digest:** `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

Production checkpoints:
- framework PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259;
- reference-label contract PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263;
- public calibration-evidence contract PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265;
- exit-readiness PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267;
- purpose grants PR #111 → main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` → Run #272;
- human work package PR #113 → main `7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12` → Run #278;
- human completion PR #114 → main `58266dffed529a5d7d247e58651865bbda83981e` → Run #280;
- reference-bundle acceptance PR #115 → main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` → Run #282;
- reference current-truth PR #116 → main `0c267cb9489cfe023a4d5e26104f5ae684cb95fb` → Run #285;
- exact development execution authorization PR #117 exact head `b42ad45656299651897be33b7ea98d940217095c` → Run #286 (`33685839142`) SUCCESS → main `76f5643dde72c8cc4b02b517133331e9dea00146` → Run #287 (`33686039783`) SUCCESS.

### 5.1 Calibration observations/candidates

`src/st_score_restore/stage4_calibration.py` defines deterministic observations/candidates. Candidate derivation is development-only; held-out observations may evaluate a frozen candidate only after a separate held-out boundary, and cannot derive/select/tune it. Cross-split source-family leakage is forbidden.

A real observation requires its private raw metric (`metricName` + `rawValue`) in addition to the accepted human label. The accepted 42-label bundle intentionally does not publish those raw values.

### 5.2 Purpose grants

`evidence/stage4/governance/purpose-grants.v1.json` is an immutable overlay; it does not rewrite Stage 1 catalog permissions. Exact Beethoven and Barley development artifacts are granted `safety_calibration`. Chopin remains held-out `held_out_evaluation` only with candidate derivation forbidden.

### 5.3 Human reference-label evidence and acceptance

`src/st_score_restore/stage4_reference_labels.py` requires real labels to carry exact purpose permission plus human expert-review provenance. Model/prediction output cannot become reference truth.

The production-effective development bundle contains 42 human-reviewed labels: 36 `clear`, 5 `possible`, 1 `probable`, 0 `not_assessed`. Completion digest is `3434e74e7d993db2384711f9c6c31f31d148c65bc5896bd120f82b5dcab2e1fd`; accepted receipt digest is `f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33`.

`src/st_score_restore/stage4_reference_label_acceptance.py` validates the separate historical acceptance decision. That evidence remains immutable with `realDataCalibrationExecutionAuthorized=false`; it was never rewritten after the later execution authorization.

### 5.4 Real development execution authorization

`src/st_score_restore/stage4_execution_authorization.py` and `evidence/stage4/governance/real-development-calibration-execution-authorization.v1.json` define the separate production-effective authorization. It is digest-bound to the purpose grant, accepted reference-bundle decision, accepted reference receipt and 42-label bundle.

The authorization grants only:
- exact Beethoven + Barley development items;
- data class `real`;
- purpose `safety_calibration`;
- environment `stage1_offline`;
- storage class `managed_standard`;
- candidate derivation and development evaluation with private observation metrics.

It explicitly does **not** authorize:
- Chopin/held-out evaluation;
- held-out tuning;
- production threshold/resource changes;
- training, publication or external export;
- Stage 4 PASS or Stage 5 entry.

The authorization assertion is `realDataCalibrationExecutionAuthorized=true`, while `realDataCalibrationExecuted=false` remains current truth.

### 5.5 Public calibration evidence and exit readiness

`src/st_score_restore/stage4_calibration_evidence.py` keeps public receipts aggregate/digest-only. Raw metric rows remain outside ordinary Git. `src/st_score_restore/stage4_exit_readiness.py` returns only `NOT_READY` or `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; it cannot set Stage 4 PASS or authorize Stage 5.

Remaining blocker set:
1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Execution authorization itself is not a readiness completion signal; the development blocker closes only after accepted real execution evidence exists.

## 6. Permission and safety boundary

Real development calibration execution is **AUTHORIZED / NOT YET EXECUTED** for exact Beethoven + Barley only. `calibrationAuthorized=true`, `realDataCalibrationExecutionAuthorized=true`, `realDataCalibrationExecuted=false`, `thresholdsCalibrated=false`, `resourceLimitsCalibrated=false`, `heldOutTuningUsed=false`, `modelTrainingAuthorized=false`, `publicationAuthorized=false`, `stage4ExitPass=false`, `stage5EntryEligible=false`.

No production Stage 2 quality threshold or Stage 3 page/resource limit changes are authorized. No numerical acceptance target was created by the execution authorization.

## 7. Private observation-metric boundary

Actual execution requires the private observation metrics bound 1:1 to the 42 accepted observation IDs. They are not present in ordinary Git. Historical Stage 3 Run #246 (`33641537118`) and Run #251 (`33645607053`) expose no GitHub Actions artifacts, so those raw metric values cannot be recovered from the known Actions evidence and must not be inferred or fabricated.

A real execution runner must fail closed if any observation ID, dataset item, artifact SHA, source family, purpose, metric name/value, label binding, authorization digest or environment binding is missing or mismatched. Public evidence may expose only deterministic digests and aggregate metrics.

## 8. Binding development sequence

```text
Stage 1  Real and explicitly authorized test dataset
Stage 2  Complete quality-analysis system
Stage 3  Multi-page PDF pipeline
Stage 4  Safety calibration with real data
Stage 5  Accessible teacher review interface
Stage 6  Identity, network and production infrastructure
Stage 7  Preview release
Stage 8  DocRes optional candidate
Stage 9  Multi-engine comparator
Stage 10 ST Restore Selector
Stage 11 ST Restore image model
Stage 12 Music-application integrations
```

## 9. Transition

The next substantive boundary is the fail-closed private observation-metric input + real development calibration runner. Actual calibration may run only when the exact Beethoven + Barley private metrics are available and bound to the accepted 42 labels and production-effective authorization. Chopin remains isolated for a later, separate held-out evaluation boundary. Stage 5 remains BLOCKED pending Stage 4 final exit PASS.
