# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images. This repository is **not** an OMR engine. Source bytes remain immutable; exact SHA-256 defines artifact identity; real corpus/derivative bytes stay outside ordinary Git.

## Current production truth — 2026-09-02

- **Stage 1:** COMPLETE / PASS / production-effective.
- **Stage 2:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
- **Stage 3:** COMPLETE / PASS / production-effective. Final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`; acceptance digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.
- **Stage 4:** **ACTIVE — FRAMEWORK / GOVERNANCE ONLY.** Purpose-grant production main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd`; post-merge Run #272 (`33672903071`) passed Python 3.11/3.12.
- **Stage 4 readiness:** **NOT_READY / 4 remaining prerequisite blockers.** This is not Stage 4 PASS.
- **Real calibration execution:** **BLOCKED / NOT AUTHORIZED.** Purpose permission is not execution authorization.
- **Stage 5:** NOT STARTED / BLOCKED pending separate Stage 4 final exit PASS.

Stage 4 entry/start decision canonical SHA-256: `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 safety-calibration purpose-grant overlay canonical SHA-256: `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

Production chain:
- framework start PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259;
- reference-label contract PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263;
- public calibration-evidence contract PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265;
- exit-readiness contract PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267;
- safety-calibration purpose grants PR #111 → main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` → Run #272.

## Stage 4 purpose boundary

Exact Beethoven (`c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`) and Barley (`6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`) development artifacts now have production-effective `safety_calibration` purpose grants. Historical Stage 1 catalog bytes/permissions remain immutable; the grant is an overlay. Chopin (`b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`) remains held-out `held_out_evaluation` only and cannot derive/tune candidates.

Remaining readiness blockers:
1. `no_real_calibration_reference_label_bundle_is_accepted`
2. `no_real_development_calibration_evidence_is_accepted`
3. `no_real_held_out_evaluation_evidence_is_accepted`
4. `no_stage4_metric_acceptance_target_policy_is_accepted`

Even if all prerequisites are later satisfied, the evaluator can return only `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; it cannot set `stage4ExitPass=true` or authorize Stage 5.

## Stage 3 accepted evidence

Stage 3 immutable digests: purpose grants `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution evidence `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations review `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; final acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

Production renderer remains exact `pypdfium2==5.13.0`. Stage 2 quality thresholds and Stage 3 page/resource values remain `uncalibrated_engineering_defaults`; no production threshold/resource change is authorized.

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

## Safety boundary

Real labels still require human expert-review provenance and separate bundle acceptance. Held-out evidence remains evaluation-only. Model predictions cannot substitute for reference labels. `calibrationAuthorized=false`, `realDataCalibrationExecuted=false`, `heldOutTuningUsed=false`, training/publication remain unauthorized, and Stage 5 remains blocked.
