# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 4 ACTIVE — framework/governance only / readiness NOT_READY  
**Version:** 0.8.0  
**Date:** 2026-09-02  
**Stage 4 tracking:** Issue #104  
**Latest Stage 4 production main:** `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75`  
**Latest Stage 4 post-merge CI:** Run #267 (`33670331093`) — Python 3.11 / 3.12 SUCCESS

## Authority and invariant rules

Repository truth is merged `main` plus accepted deterministic evidence. Historical evidence is never rewritten retroactively. Source bytes remain immutable; real corpus/derivative bytes stay outside ordinary Git; held-out data never tunes thresholds, page policy, hardening constants or renderer/resource limits; vector/hybrid content is never silently rasterized; exact-head and post-merge CI are mandatory.

Stage 4 is active only for framework/governance work. Real-data calibration is not authorized merely because Stage 4 started. A real development artifact requires an explicit `safety_calibration` purpose grant; held-out artifacts remain `held_out_evaluation` only.

## Binding delivery sequence

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

## Stage 1

**State:** COMPLETE / PASS / production-effective. Accepted Stage 2 entry main `936f2f9e52cb1009628e8ccf1e7e2af035ec8ef6`.

Canonical digests: catalog `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`; historical C15/C16 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476` / `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`.

## Stage 2

**State:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance / Stage 3 entry main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; frozen execution evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

## Stage 3 — Multi-page PDF pipeline

**State:** COMPLETE / PASS / production-effective.  
Core `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232; authorized execution `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235; purpose grants `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238; runner `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246; evidence main `b15d91ff3fbf21b47a0e484b5a337c4611a17355` / Run #251; final acceptance `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253.

Purpose-grant digest `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution-evidence digest `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations digest `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; final acceptance digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## Stage 4 — Safety calibration with real data

**State:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY.  
**Readiness:** NOT_READY.  
**Tracking:** Issue #104.  
**Entry/start decision:** `evidence/stage4/governance/stage4-entry-start.v1.json`.  
**Decision digest:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

Production chain:

- framework start: PR #105 / main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- reference-label contract v0.1.0: PR #107 / main `b184f5e5b780213671597ffa9f4380aa4a1adb47` / Run #263;
- public calibration-evidence contract v0.1.0: PR #108 / main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` / Run #265;
- exit-readiness contract v0.1.0: PR #109 / main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` / Run #267.

Implemented framework/governance scope:

- deterministic observation/candidate contracts and held-out anti-leakage evaluation;
- reference-label provenance/purpose contract with human-review requirement for real labels;
- synthetic-only public-safe candidate/evaluation evidence receipts;
- deterministic exit-readiness evaluator that cannot self-authorize PASS.

Current readiness blockers:

1. `no_real_artifact_has_granted_safety_calibration_permission`
2. `no_real_calibration_reference_label_bundle_is_accepted`
3. `no_real_development_calibration_evidence_is_accepted`
4. `no_real_held_out_evaluation_evidence_is_accepted`
5. `no_stage4_metric_acceptance_target_policy_is_accepted`

Stage 4 readiness may advance only to `READY_FOR_FINAL_ACCEPTANCE_REVIEW` after those prerequisites and all safety invariants are satisfied. A separate final governance acceptance remains mandatory; readiness never sets `stage4ExitPass=true` or authorizes Stage 5.

Production thresholds/resource limits remain `uncalibrated_engineering_defaults`; model training and publication remain unauthorized. Numerical metric targets must be separately accepted from evidence and must not be invented.

## Stages 5–12

**State:** NOT STARTED. Stage 5 remains blocked until Stage 4 final exit PASS.

## Current next safe action

Autonomous framework/governance work has reached the real-evidence boundary. The next substantive Stage 4 work requires externally supplied, evidence-bound decisions: exact real-artifact `safety_calibration` permission, accepted real reference-label provenance, real development/held-out calibration evidence, and a separately accepted metric-target policy. Do not fabricate or infer these prerequisites.