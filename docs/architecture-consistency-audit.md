# Architecture Consistency Audit — 2026-09-03

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS / production-effective  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 4:** ACTIVE — EXACT REAL DEVELOPMENT CALIBRATION EXECUTION AUTHORIZED / NOT YET EXECUTED  
**Stage 4 readiness:** NOT_READY / 3 blockers  
**Execution-authorization production main:** `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287 (`33686039783`) SUCCESS  
**Real development calibration execution:** AUTHORIZED / NOT YET EXECUTED; private observation metrics pending

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence is immutable. Artifact-specific purpose grants, reference-bundle acceptance and the later execution authorization are separate immutable overlays rather than rewrites. Execution authorization does not prove execution.

## Current findings

| Area | Result |
|---|---|
| Stage 1 final exit | PASS / EFFECTIVE |
| Stage 2 final exit | PASS / EFFECTIVE |
| Stage 2 execution evidence | main `ffea7f5aa618187f3cabcfb49801804e3f6658bf` / digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| Stage 3 final exit | PASS / EFFECTIVE |
| Stage 3 purpose grant | `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8` |
| Stage 3 execution | `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6` |
| Stage 3 limitations | `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d` |
| Stage 3 final acceptance | `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90` |
| Stage 4 framework start | PR #105 / main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259 |
| Stage 4 entry/start digest | `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8` |
| Reference-label contract | PR #107 / main `b184f5e5b780213671597ffa9f4380aa4a1adb47` / Run #263 |
| Public calibration-evidence contract | PR #108 / main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` / Run #265 |
| Exit-readiness contract | PR #109 / main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` / Run #267 |
| Safety-calibration purpose grants | PR #111 / main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272 |
| Human review work package | PR #113 / main `7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12` / Run #278 |
| Human label completion | PR #114 / main `58266dffed529a5d7d247e58651865bbda83981e` / Run #280 |
| Accepted real development reference-label bundle | PR #115 / main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282 / ACCEPTED |
| Reference current-truth checkpoint | PR #116 / main `0c267cb9489cfe023a4d5e26104f5ae684cb95fb` / Run #285 |
| Real development execution authorization | PR #117 exact head `b42ad45656299651897be33b7ea98d940217095c` / Run #286 / main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287 / AUTHORIZED |
| Stage 4 purpose-grant digest | `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc` |
| Stage 4 bundle digest | `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14` |
| Stage 4 bundle acceptance digest | `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c` |
| Stage 4 execution-authorization digest | `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68` |
| Authorized development artifacts | Beethoven + Barley exact identities, 2/2 |
| Human reference labels | 42/42: 36 clear, 5 possible, 1 probable, 0 not_assessed |
| Private observation metrics | REQUIRED / NOT AVAILABLE in ordinary Git or known Stage 3 Actions artifacts |
| Chopin | held-out evaluation only / development candidate derivation and tuning forbidden / not authorized by development decision |
| Accepted real development calibration evidence | NONE |
| Accepted real held-out evaluation evidence | NONE |
| Accepted metric-target policy | NONE |
| Production thresholds/resources | UNCALIBRATED ENGINEERING DEFAULTS / UNCHANGED |
| Stage 5 | BLOCKED pending Stage 4 final exit PASS |

## Immutable evidence retained

Historical Stage 1 catalog remains canonical/unchanged. Historical Stage 4 entry, purpose and reference acceptance records remain unchanged; notably the reference acceptance still says `realDataCalibrationExecutionAuthorized=false`. The later execution authorization is a separate evidence record and is not back-written into earlier decisions. Stage 3 immutable digests remain purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`, execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`, limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`, acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## Stage 4 data boundary

Beethoven exact SHA `c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c` and Barley exact SHA `6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e` are development-only `safety_calibration`. Their human reference bundle is accepted and candidate-derivation eligible, and exact-scope development calibration execution is now authorized. Chopin exact SHA `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3` remains held-out `held_out_evaluation`; development candidate derivation/tuning is forbidden and the development execution decision does not authorize held-out evaluation.

Authorization requires private observation metrics and keeps `realDataCalibrationExecuted=false`. It does not grant threshold/resource changes, training, publication, Stage 4 PASS or Stage 5 entry.

Historical Stage 3 Run #246 (`33641537118`) and Run #251 (`33645607053`) expose no Actions artifacts; no raw metric values can therefore be recovered from those known runs. Raw metrics must not be inferred or fabricated.

## Current readiness blockers

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Resolved: `no_real_artifact_has_granted_safety_calibration_permission` and `no_real_calibration_reference_label_bundle_is_accepted`.

## Non-claims

Stage 4 ACTIVE plus execution authorization does not mean calibration has run. `calibrationAuthorized=true`, `realDataCalibrationExecutionAuthorized=true`, but `realDataCalibrationExecuted=false`, `thresholdsCalibrated=false`, `resourceLimitsCalibrated=false`, `heldOutTuningUsed=false`, `stage4ExitPass=false`. No production threshold/resource change, held-out evaluation, training or publication is authorized. Stage 5 remains BLOCKED.
