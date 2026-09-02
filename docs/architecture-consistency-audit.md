# Architecture Consistency Audit — 2026-09-02

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Stage 1:** COMPLETE / PASS / production-effective  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 4:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY  
**Stage 4 framework main:** `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`  
**Stage 4 framework post-merge CI:** Run #259 (`33659753403`) — Python 3.11 / 3.12 SUCCESS  
**Real-data calibration:** BLOCKED / NOT AUTHORIZED

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence remains immutable. Open PR state is not production-effective. CI is exact-head scoped. Stage 4 framework start is distinct from real-data calibration authorization.

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
| Stage 4 decision digest | `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8` |
| Stage 4 current mode | ACTIVE — framework/governance only |
| Real `safety_calibration` grant | NONE |
| Accepted real reference-label bundle | NONE |
| Production thresholds/resource limits | UNCALIBRATED ENGINEERING DEFAULTS / UNCHANGED |
| Stage 5 | BLOCKED pending Stage 4 exit PASS |

## Immutable evidence retained

Stage 1 canonical digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`; historical C15/C16 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

Stage 3 immutable production evidence: purpose grants `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution evidence `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## Stage 4 production framework

`src/st_score_restore/stage4_calibration.py` defines deterministic observation/candidate contracts and evaluation. Candidate derivation is development-only. Held-out evidence cannot derive or tune a candidate; evaluation is not fed back into candidate selection; cross-split source-family overlap is rejected.

`evidence/stage4/governance/stage4-entry-start.v1.json` authorizes framework implementation and synthetic contract testing only. The historical decision itself retains `stage4Started=false` because it was the pre-start authorization; production-effectiveness of PR #105 plus Run #259 is what permits current repository state to become framework-active.

## Real-data boundary

The accepted Stage 1 catalog currently contains no granted `safety_calibration` purpose. Existing Stage 3 purpose grants remain `pdf_pipeline_evaluation` and explicitly retain `calibrationAuthorized=false`.

Consequently real-data threshold/resource calibration is fail-closed. General project approval cannot substitute for an artifact-specific purpose grant. Held-out observations remain `held_out_evaluation` only.

Current real-calibration blockers:

- `no_real_artifact_has_granted_safety_calibration_permission`;
- `no_real_calibration_reference_label_bundle_is_accepted`.

## Non-claims

Stage 4 ACTIVE does not mean calibration has run. No production quality threshold, PDF page policy, renderer bound or resource limit is changed by the framework start. Training, publication, representativeness, absence of bias, restoration effectiveness, OMR improvement and musical correctness are not established.

The separate `Fly Me to the Moon` phone-photo path remains independently blocked pending real high-assurance-vault verification.