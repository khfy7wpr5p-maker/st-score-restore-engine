# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images.

This repository is **not** an OMR engine. Source bytes remain immutable, exact SHA-256 defines artifact identity, real corpus/derivative bytes stay outside ordinary Git, and unsupported derivatives never replace the source fallback.

## Current production truth — 2026-09-02

- **Stage 1:** COMPLETE / PASS / production-effective.
- **Stage 2:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
- **Stage 3:** COMPLETE / PASS / production-effective. Final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`; acceptance digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.
- **Stage 4:** **ACTIVE — FRAMEWORK / GOVERNANCE ONLY.** Latest production main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75`; post-merge Run #267 (`33670331093`) passed Python 3.11 and 3.12.
- **Stage 4 readiness:** **NOT_READY** with five objective prerequisite blockers. This is not Stage 4 PASS.
- **Real-data calibration:** **BLOCKED / NOT AUTHORIZED.** No real calibration has executed and production thresholds/resource limits remain unchanged.
- **Stage 5:** NOT STARTED / BLOCKED pending separate Stage 4 final exit PASS.

Stage 4 entry/start decision: `evidence/stage4/governance/stage4-entry-start.v1.json`, canonical SHA-256 `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 production chain:

- framework start: PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259;
- reference-label contract v0.1.0: PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263;
- public calibration-evidence contract v0.1.0: PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265;
- exit-readiness contract v0.1.0: PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267.

Current Stage 4 readiness blockers:

1. `no_real_artifact_has_granted_safety_calibration_permission`
2. `no_real_calibration_reference_label_bundle_is_accepted`
3. `no_real_development_calibration_evidence_is_accepted`
4. `no_real_held_out_evaluation_evidence_is_accepted`
5. `no_stage4_metric_acceptance_target_policy_is_accepted`

The readiness evaluator can never self-authorize exit. Even when every prerequisite is eventually satisfied, it can only return `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; separate final governance acceptance and exact-head/post-merge CI are mandatory.

## Stage 3 accepted evidence

Production renderer remains exact `pypdfium2==5.13.0` / PDFium. Resource limits remain `uncalibrated_engineering_defaults`: 200 DPI, 64 pages, 40M pixels/page, 160M aggregate pixels, 8,000-pixel dimension, page-object depth 15.

Stage 3 real batch: 3 items / 14 pages / 12 raster pages rendered / 2 vector pages preserved / 0 review-required; page order preserved; no vector rasterization; held-out tuning false.

- Purpose-grant digest: `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.
- Execution-evidence digest: `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.
- Limitations-review digest: `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.

## Binding development order

```text
Stage 0  Roadmap update
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

## Development baseline

- Python `>=3.11,<3.13`
- CI Python 3.11 and 3.12
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer `pypdfium2==5.13.0`
- API `/api/v1`, version `0.5.0`
- ordinary Git real corpus/derivative bytes: zero

## Safety boundary

Held-out evidence may evaluate a frozen Stage 4 candidate but may never derive, select or tune thresholds or resource limits. General project approval is not a dataset purpose grant. Reference labels require separate provenance/acceptance. No numerical acceptance targets are invented. `calibrationAuthorized=false`, `realDataCalibrationExecuted=false`, `stage4ExitPass=false`, training/publication remain unauthorized, and Stage 5 remains blocked.