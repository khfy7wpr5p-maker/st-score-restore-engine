# ST Score Restore Engine — Technical Specification

**Status:** Current architecture; Stage 4 ACTIVE — framework/governance only / readiness NOT_READY  
**Version:** 1.1.0-doc  
**Date:** 2026-09-02  
**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Latest Stage 4 production main:** `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` / Run #267 (`33670331093`) SUCCESS

## 1. Scope and invariants

ST Score Restore Engine is a safety-first visual restoration and validation service for music-score and guitar-TAB documents. It is not an OMR engine.

Source bytes are immutable; exact SHA-256 defines artifact identity; historical evidence is immutable; real corpus/derivative bytes remain outside ordinary Git; held-out evidence never tunes thresholds or resource limits; vector/hybrid content is never silently rasterized; purpose, custody, split, reference-label provenance and final acceptance rules fail closed.

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

- Python `>=3.11,<3.13`
- CI Python 3.11 / 3.12
- API `0.5.0`
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer exact `pypdfium2==5.13.0`
- ordinary Git real corpus/derivative bytes: zero

## 4. Historical production stages

Stage 1 COMPLETE / PASS. Canonical v2 digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`; historical C15/C16 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Stage 2 COMPLETE / PASS. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`; final acceptance / Stage 3 entry main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`.

Stage 3 COMPLETE / PASS. Production chain: core `29b4244eeaeb2239ff959e6dd6d4128311f005fa`; authorized execution `d834ed42e3f553308aef7f6adb7e8cb873593f0b`; purpose main `6ebe160309c562e9841a3c313d5ca507592f1386`; runner `5e682f1933a7167fc142689306352fe53b4b1833`; evidence main `b15d91ff3fbf21b47a0e484b5a337c4611a17355`; final acceptance `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`.

Stage 3 digests: purpose grants `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution evidence `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

Stage 3 resource values remain uncalibrated engineering defaults: 200 DPI; 64 pages; 40,000,000 pixels/page; 160,000,000 aggregate pixels; 8,000-pixel dimension; page-object depth 15.

## 5. Stage 4 production framework/governance chain

**State:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY.  
**Readiness:** NOT_READY.  
**Tracking:** Issue #104.  
**Entry/start decision:** `evidence/stage4/governance/stage4-entry-start.v1.json`; canonical SHA-256 `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Production checkpoints:

- framework start PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259;
- reference-label contract v0.1.0 PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263;
- public calibration-evidence contract v0.1.0 PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265;
- exit-readiness contract v0.1.0 PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267.

### 5.1 Calibration observations/candidates

`src/st_score_restore/stage4_calibration.py` defines deterministic calibration observations and threshold candidates. Candidate derivation is development-only. Held-out observations can evaluate a frozen candidate but cannot enter derivation or feed results back into candidate selection. Cross-split source-family overlap is rejected.

### 5.2 Reference-label contract

`src/st_score_restore/stage4_reference_labels.py` defines immutable reference-label records/bundles. Real development labels require exact `safety_calibration` purpose permission and human expert-review provenance. Real held-out labels require `held_out_evaluation`. A purpose grant does not itself accept a real reference bundle. Prediction/model output cannot be used as reference evidence.

### 5.3 Public-safe calibration evidence

`src/st_score_restore/stage4_calibration_evidence.py` accepts synthetic contract evidence only in the current slice. Candidate/evaluation public receipts bind deterministic digests and aggregate metrics while keeping row-level observations/results, reviewer/provenance refs, dataset/source-family identities and artifact/derivative bytes non-public. Real calibration evidence is rejected by this public contract slice.

### 5.4 Exit readiness

`src/st_score_restore/stage4_exit_readiness.py` returns `NOT_READY` or `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. It always keeps `stage4ExitPass=false` and `stage5EntryAuthorized=false`. Readiness can never substitute for final governance acceptance.

Current blocker set:

1. `no_real_artifact_has_granted_safety_calibration_permission`
2. `no_real_calibration_reference_label_bundle_is_accepted`
3. `no_real_development_calibration_evidence_is_accepted`
4. `no_real_held_out_evaluation_evidence_is_accepted`
5. `no_stage4_metric_acceptance_target_policy_is_accepted`

## 6. Stage 4 permission and safety boundary

Real-data execution is **BLOCKED / NOT AUTHORIZED**. Real development observations require an already validated exact-artifact `safety_calibration` purpose. Real held-out observations require `held_out_evaluation` and remain evaluation-only.

Therefore `calibrationAuthorized=false`, `realDataCalibrationExecuted=false`, `thresholdsCalibrated=false`, `resourceLimitsCalibrated=false`, `heldOutTuningUsed=false`, `modelTrainingAuthorized=false`, `publicationAuthorized=false`, `stage4ExitPass=false`, and `stage5EntryEligible=false`.

No production Stage 2 quality threshold or Stage 3 page/resource limit changes in this framework-only state. Numerical metric acceptance targets have not been accepted and are not invented by the framework.

## 7. Binding development sequence

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

## 8. Validation and transition

CI validates dependency/repository/architecture contracts, all accepted Stage 1–3 evidence, Stage 4 entry/start governance, reference-label contract, public calibration-evidence contract, exit-readiness contract, full unit tests and Python compile on 3.11 and 3.12.

Stage 4 exit requires production-effective real calibration purpose grants/evidence, accepted real reference-label provenance, development-only candidate derivation, held-out non-tuning evaluation, accepted metric-target policy, limitations review, public-safe evidence freeze, separate final acceptance and exact-head/post-merge CI. Stage 5 remains blocked until final Stage 4 PASS.