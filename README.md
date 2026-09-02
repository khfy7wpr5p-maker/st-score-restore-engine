# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images. This repository is **not** an OMR engine. Source bytes remain immutable; exact SHA-256 defines artifact identity; real corpus/derivative bytes stay outside ordinary Git.

## Current production truth — 2026-09-03

- **Stage 1:** COMPLETE / PASS / production-effective.
- **Stage 2:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
- **Stage 3:** COMPLETE / PASS / production-effective. Final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`; immutable digests: purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`, execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`, limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`, acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.
- **Stage 4:** **ACTIVE — REAL DEVELOPMENT CALIBRATION EXECUTION AUTHORIZED / NOT YET EXECUTED.** Latest authorization production main `76f5643dde72c8cc4b02b517133331e9dea00146`; post-merge Run #287 (`33686039783`) passed Python 3.11/3.12.
- **Stage 4 readiness:** **NOT_READY / 3 remaining prerequisite blockers.** This is not Stage 4 PASS.
- **Real calibration execution:** **AUTHORIZED for exact Beethoven + Barley development scope; NOT YET EXECUTED.** Private observation metrics are required before the run can occur.
- **Stage 5:** NOT STARTED / BLOCKED pending separate Stage 4 final exit PASS.

Stage 4 entry/start decision canonical SHA-256: `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Stage 4 safety-calibration purpose-grant overlay canonical SHA-256: `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

Accepted Stage 4 development reference evidence:
- work-package digest `93e1a61bbdd698dbabf1ba88164453056acf3f2ea37fa159305a0f244b2253ba`;
- human-completion digest `3434e74e7d993db2384711f9c6c31f31d148c65bc5896bd120f82b5dcab2e1fd`;
- bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`;
- accepted receipt digest `f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33`;
- acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- real development execution-authorization digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

Production chain:
- framework start PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259;
- reference-label contract PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263;
- public calibration-evidence contract PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265;
- exit-readiness contract PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267;
- safety-calibration purpose grants PR #111 → main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` → Run #272;
- human review work package PR #113 → main `7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12` → Run #278;
- completed human labels PR #114 → main `58266dffed529a5d7d247e58651865bbda83981e` → Run #280;
- real development reference-bundle acceptance PR #115 → main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` → Run #282;
- real development calibration execution authorization PR #117 exact head `b42ad45656299651897be33b7ea98d940217095c` → Run #286 (`33685839142`) SUCCESS → main `76f5643dde72c8cc4b02b517133331e9dea00146` → Run #287 (`33686039783`) SUCCESS.

## Stage 4 data boundary

Beethoven (`c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c`) and Barley (`6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e`) are development-only `safety_calibration` artifacts. Their 42 human-reviewed reference labels are accepted for candidate derivation, and exact-scope real development calibration execution is now authorized. Chopin (`b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`) remains held-out `held_out_evaluation` only and cannot derive/select/tune candidates; this authorization does not authorize its held-out evaluation.

The actual development run still requires private observation metrics bound 1:1 to the accepted observation IDs. Raw observation metrics remain forbidden in ordinary Git. Historical Stage 3 Runs #246 and #251 expose no GitHub Actions artifacts containing such metrics, so no metric values are inferred or fabricated from repository evidence.

Remaining readiness blockers:
1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Even if all prerequisites are later satisfied, readiness can advance only to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; it cannot set `stage4ExitPass=true` or authorize Stage 5.

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

Human reference evidence is accepted and exact Beethoven+Barley development execution is authorized, but `realDataCalibrationExecuted=false`, `thresholdsCalibrated=false`, `resourceLimitsCalibrated=false`, `heldOutTuningUsed=false`; production threshold/resource changes, held-out evaluation, training and publication remain unauthorized. The next substantive execution step requires the private observation-metric input contract/data; no raw metric values are stored in ordinary Git. Stage 5 remains BLOCKED.
