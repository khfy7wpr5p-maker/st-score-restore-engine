# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 4 ACTIVE — exact real development calibration execution authorized / not yet executed / readiness NOT_READY  
**Date:** 2026-09-03  
**Stage 4 tracking:** Issue #104  
**Latest Stage 4 execution-authorization production main:** `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287 (`33686039783`) SUCCESS  
**Real-data development calibration execution:** AUTHORIZED / NOT YET EXECUTED; private observation metrics required

## Authority and invariants

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence is immutable. Real corpus/derivative bytes and private raw observation metrics remain outside ordinary Git. Held-out evidence never tunes thresholds/resource limits. Exact-head and post-merge CI are mandatory.

Stage 4 framework/governance remains active. Beethoven + Barley have exact production-effective `safety_calibration` purpose grants, an accepted 42-record human-reviewed development reference bundle, and a separate exact-scope real development calibration execution authorization. Authorization does **not** prove execution: the actual run remains pending the private observation metrics required by the calibration contract.

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

**State:** ACTIVE — EXACT DEVELOPMENT EXECUTION AUTHORIZED / NOT YET EXECUTED.  
**Readiness:** NOT_READY / 3 remaining blockers.  
**Entry/start digest:** `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.  
**Safety-calibration grant digest:** `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.  
**Accepted reference-bundle digest:** `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`.  
**Reference-bundle acceptance digest:** `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`.  
**Execution-authorization digest:** `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

Production chain:

- framework PR #105 / main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- reference-label contract PR #107 / main `b184f5e5b780213671597ffa9f4380aa4a1adb47` / Run #263;
- public evidence contract PR #108 / main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` / Run #265;
- exit-readiness PR #109 / main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` / Run #267;
- purpose-grant PR #111 / main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272;
- human review work package PR #113 / main `7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12` / Run #278;
- human label completion PR #114 / main `58266dffed529a5d7d247e58651865bbda83981e` / Run #280;
- accepted development reference bundle PR #115 / main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282;
- reference current-truth PR #116 / main `0c267cb9489cfe023a4d5e26104f5ae684cb95fb` / Run #285;
- exact development execution authorization PR #117 exact head `b42ad45656299651897be33b7ea98d940217095c` / Run #286 (`33685839142`) SUCCESS → main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287 (`33686039783`) SUCCESS.

Development scope:

- Beethoven: development-only `safety_calibration` granted; exact execution authorized;
- Barley: development-only `safety_calibration` granted; exact execution authorized;
- 42 human reference labels accepted: 36 clear, 5 possible, 1 probable, 0 not_assessed;
- accepted receipt digest `f5e1f171551d8d1551587c065f796cd5d4dc64df7babb3af86c4555585933c33`;
- private `metricName` + `rawValue` inputs are required and raw values are forbidden in ordinary Git;
- Chopin remains `held_out_evaluation` only; candidate derivation/tuning forbidden and this development authorization does not authorize held-out evaluation;
- historical Stage 1 catalog, purpose grant and reference acceptance remain unchanged;
- external export, training, publication and production threshold/resource changes remain unauthorized.

Remaining readiness blockers:

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Stage 4 readiness may advance only to `READY_FOR_FINAL_ACCEPTANCE_REVIEW`; separate final acceptance is mandatory and `stage4ExitPass=false` remains until then.

## Stages 5–12

**State:** NOT STARTED. Stage 5 remains BLOCKED pending Stage 4 final exit PASS.

## Current next safe action

Build/finalize the fail-closed private observation-metric input and real development calibration runner contract. It must validate the exact Beethoven + Barley identities, execution authorization, accepted 42-label bundle and 1:1 observation binding; it must keep raw metrics outside ordinary Git and emit only public-safe digest/aggregate evidence. Actual execution occurs only when those private metrics are available. No metric values or numerical acceptance targets may be fabricated, and Chopin remains isolated for later held-out evaluation.
