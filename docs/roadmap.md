# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 4 ACTIVE — framework/governance only / readiness NOT_READY  
**Date:** 2026-09-02  
**Stage 4 tracking:** Issue #104  
**Latest Stage 4 purpose-grant production main:** `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272 (`33672903071`) SUCCESS  
**Real-data calibration:** BLOCKED / NOT AUTHORIZED

## Authority and invariants

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence is immutable. Real corpus/derivative bytes remain outside ordinary Git. Held-out evidence never tunes thresholds/resource limits. Exact-head and post-merge CI are mandatory.

Stage 4 is active for framework/governance work. Beethoven + Barley now have exact production-effective `safety_calibration` purpose grants, but this does **not** authorize real calibration execution. Human-reviewed reference-label evidence must be separately accepted first.

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

## Historical production stages

Stage 1: COMPLETE / PASS / production-effective. Immutable historical bindings: C15 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; C16 `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`; catalog v2 `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; snapshot v2 `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report v2 `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Stage 2: COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Stage 3: COMPLETE / PASS / production-effective. Purpose-grant digest `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution-evidence digest `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations digest `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; final acceptance digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## Stage 4 — Safety calibration with real data

**State:** ACTIVE — FRAMEWORK / GOVERNANCE ONLY.  
**Readiness:** NOT_READY / 4 remaining blockers.  
**Entry/start digest:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.  
**Safety-calibration grant digest:** `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.

Production chain:

- framework PR #105 / main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- reference-label contract PR #107 / main `b184f5e5b780213671597ffa9f4380aa4a1adb47` / Run #263;
- public evidence contract PR #108 / main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` / Run #265;
- exit-readiness PR #109 / main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` / Run #267;
- purpose-grant PR #111 / main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272.

Authorized purpose scope:

- Beethoven development exact artifact: `safety_calibration` granted;
- Barley development exact artifact: `safety_calibration` granted;
- Chopin remains `held_out_evaluation` only; candidate derivation/tuning forbidden;
- historical Stage 1 catalog remains unchanged;
- external export, training, publication and real calibration execution remain unauthorized.

Remaining blockers:

1. `no_real_calibration_reference_label_bundle_is_accepted`
2. `no_real_development_calibration_evidence_is_accepted`
3. `no_real_held_out_evaluation_evidence_is_accepted`
4. `no_stage4_metric_acceptance_target_policy_is_accepted`

Stage 4 readiness may advance only to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; separate final acceptance is mandatory and `stage4ExitPass=false` remains until then.

## Stages 5–12

**State:** NOT STARTED. Stage 5 remains BLOCKED pending Stage 4 final exit PASS.

## Current next safe action

Prepare the real reference-label work package for Beethoven + Barley. Do not fabricate human labels, execute calibration, change production thresholds/resources, or use Chopin for tuning before an accepted human-reviewed reference-label bundle exists.
