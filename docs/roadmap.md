# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 4 ACTIVE — framework/governance only  
**Version:** 0.7.0  
**Date:** 2026-09-02  
**Stage 4 tracking:** Issue #104  
**Stage 4 framework main:** `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`  
**Stage 4 framework post-merge CI:** Run #259 (`33659753403`) — Python 3.11 / 3.12 SUCCESS

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
**Tracking:** Issue #104.  
**Entry/start decision:** `evidence/stage4/governance/stage4-entry-start.v1.json`.  
**Decision digest:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.  
**Framework production main / CI:** `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259 (`33659753403`).

Implemented framework scope:

- deterministic calibration observation/candidate contracts;
- development-only candidate derivation;
- held-out evaluation without feedback into candidate selection;
- false-negative, false-positive, exact-match, coverage/not-assessed metrics;
- deterministic digests and source-family anti-leakage;
- synthetic contract tests and CI validation.

Real calibration remains blocked because no accepted artifact has a granted `safety_calibration` purpose and no accepted real calibration reference-label bundle exists. Production thresholds/resource limits remain `uncalibrated_engineering_defaults`; model training and publication remain unauthorized.

Stage 4 exit requires separate purpose-bound real calibration evidence, accepted limitations, exact-head/post-merge CI and a separate final acceptance. Numerical targets must be evidence-derived rather than invented.

## Stages 5–12

**State:** NOT STARTED. Stage 5 remains blocked until Stage 4 exit PASS.

## Current next safe action

Continue Stage 4 framework/governance and reference-label contract hardening without touching real corpus bytes or production thresholds. Real-data calibration must fail closed until explicit `safety_calibration` grants become production-effective.