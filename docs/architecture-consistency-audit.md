# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS / production-effective  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 4:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY  
**Stage 4 readiness:** NOT_READY  
**Latest Stage 4 main:** `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75`  
**Latest post-merge CI:** Run #267 (`33670331093`) — Python 3.11 / 3.12 SUCCESS  
**Real-data calibration:** BLOCKED / NOT AUTHORIZED

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence remains immutable. Open PR state is not production-effective. CI is exact-head scoped. Stage 4 framework/readiness contracts are distinct from real-data calibration authorization and final Stage 4 acceptance.

## Current findings

| Area | Result |
|---|---|
| Stage 1 final exit | PASS / EFFECTIVE |
| Historical C15/C16 | PRESERVED |
| Stage 2 final exit | PASS / EFFECTIVE |
| Stage 2 execution evidence | IMMUTABLE / main `ffea7f5aa618187f3cabcfb49801804e3f6658bf` / digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d` |
| Stage 3 final exit | PASS / EFFECTIVE |
| Stage 3 final acceptance | main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90` |
| Stage 3 renderer | PDFium / exact `pypdfium2==5.13.0` |
| Stage 3 real execution | 3 items / 14 pages / 12 raster rendered / 2 vector preserved / 0 review-required |
| Stage 3 held-out tuning | FALSE |
| Stage 4 framework start | EFFECTIVE / PR #105 / main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259 |
| Stage 4 entry/start digest | `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8` |
| Reference-label contract | EFFECTIVE / v0.1.0 / PR #107 / main `b184f5e5b780213671597ffa9f4380aa4a1adb47` / Run #263 |
| Public calibration-evidence contract | EFFECTIVE / v0.1.0 / PR #108 / main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` / Run #265 |
| Exit-readiness contract | EFFECTIVE / v0.1.0 / PR #109 / main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` / Run #267 |
| Stage 4 readiness | NOT_READY / 5 prerequisite blockers |
| Real `safety_calibration` grant | NONE |
| Accepted real reference-label bundle | NONE |
| Accepted real development calibration evidence | NONE |
| Accepted real held-out evaluation evidence | NONE |
| Accepted Stage 4 metric-target policy | NONE |
| Production thresholds/resource limits | UNCALIBRATED ENGINEERING DEFAULTS / UNCHANGED |
| Stage 5 | BLOCKED pending Stage 4 final exit PASS |

## Immutable evidence retained

Stage 1 canonical digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`; historical C15/C16 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Stage 3 immutable production evidence: purpose grants `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution evidence `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

Historical Stage 4 entry/start evidence remains immutable. Its pre-start claims retain `stage4Started=false`; later production-effectiveness of PR #105/Run #259 established current framework-active state without rewriting history.

## Stage 4 production contracts

`src/st_score_restore/stage4_calibration.py` provides deterministic observation/candidate/evaluation and anti-leakage behavior.

`src/st_score_restore/stage4_reference_labels.py` binds reference labels to split, purpose, provenance and reviewer method. Real labels require human expert review; held-out labels cannot derive candidates; model predictions cannot become reference evidence.

`src/st_score_restore/stage4_calibration_evidence.py` provides synthetic-only public-safe receipts with digest/aggregate disclosure and private row/identity redaction.

`src/st_score_restore/stage4_exit_readiness.py` provides deterministic readiness assessment without authority to PASS Stage 4 or enter Stage 5.

## Current readiness blockers

1. `no_real_artifact_has_granted_safety_calibration_permission`
2. `no_real_calibration_reference_label_bundle_is_accepted`
3. `no_real_development_calibration_evidence_is_accepted`
4. `no_real_held_out_evaluation_evidence_is_accepted`
5. `no_stage4_metric_acceptance_target_policy_is_accepted`

A future state with these prerequisites resolved and all safety invariants satisfied can only become `READY_FOR_FINAL_ACCEPTANCE_REVIEW`. Separate final governance acceptance remains mandatory.

## Non-claims

Stage 4 ACTIVE does not mean real calibration has run. No production quality threshold, PDF page policy, renderer bound or resource limit is changed. Numerical acceptance targets are not invented. Training, publication, representativeness, absence of bias, restoration effectiveness, OMR improvement and musical correctness are not established. `stage4ExitPass=false` and Stage 5 remains blocked.

The separate `Fly Me to the Moon` phone-photo path remains independently blocked pending real high-assurance-vault verification.