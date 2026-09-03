# Architecture Consistency Audit — 2026-09-03

**Repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Wikimedia expansion baseline:** main `9d2326931707f65c7eb5f5b22680e8fa85665a60` / PR #125 / Run #324 (`33728459668`) SUCCESS  
**Human-label completion checkpoint:** main `2ce6151e7ce37198c5b264ddd577df71f49da8bf` / PR #128 / Run #340 (`33745945427`) SUCCESS  
**Reference-bundle acceptance checkpoint:** main `3353b281a4022f107929fae296368390da45a4fb` / PR #130 / Run #348 (`33748180036`) SUCCESS  
**Stage 1:** COMPLETE / PASS / production-effective  
**Stage 2:** COMPLETE / PASS / production-effective  
**Stage 3:** COMPLETE / PASS / production-effective  
**Stage 4:** ACTIVE / NOT_READY  
**Stage 5:** BLOCKED pending Stage 4 final exit PASS

## Authority

Merged `main` plus accepted deterministic evidence is production truth. Historical evidence is immutable. Purpose grants, human completion, reference-bundle acceptance, execution authorization, execution evidence, and later corpus-expansion overlays are separate artifacts; later facts never rewrite earlier evidence.

## Current findings

| Area | Current result |
|---|---|
| Stage 1 final exit | PASS / EFFECTIVE |
| Stage 2 final exit | PASS / EFFECTIVE |
| Stage 3 final exit | PASS / EFFECTIVE |
| Stage 4 framework | ACTIVE |
| Stage 4 readiness | NOT_READY / 3 blockers |
| Beethoven+Barley real execution | EXECUTED / ABSTAINED |
| Private observation accounting | 42 identities = 24 measured + 18 `not_applicable` |
| Measured development source families | 1 |
| Threshold candidates | 0 |
| Development execution evidence accepted | false |
| Wikimedia development expansion | production-effective via PR #125 / main `9d2326931707f65c7eb5f5b22680e8fa85665a60` / Run #324 |
| Wikimedia human labels | complete via separate PR #128 evidence: 7/7 `clear` |
| Wikimedia completion snapshot state | `human_labels_complete_pending_separate_acceptance` |
| Wikimedia reference bundle | accepted via separate PR #130 evidence |
| Wikimedia candidate derivation | eligible |
| Wikimedia execution authorization | false |
| Wikimedia execution | false |
| Chopin | held-out only / development tuning forbidden |
| Production thresholds/resources | UNCALIBRATED ENGINEERING DEFAULTS / unchanged |
| Stage 5 | BLOCKED |

## Immutable historical anchors

The audit retains all historical bindings required by the architecture contract:

- Stage 3 purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`;
- Stage 3 execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`;
- Stage 3 limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`;
- Stage 3 final acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`;
- Stage 4 framework main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- Stage 4 entry/start digest `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`;
- Beethoven+Barley purpose main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272; digest `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`;
- accepted Beethoven+Barley reference bundle main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282; bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`; acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- historical exact execution authorization main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287; digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`;
- Wikimedia reference-bundle acceptance main `3353b281a4022f107929fae296368390da45a4fb` / Run #348; bundle digest `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`; acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`.

The old authorization record remains **AUTHORIZED / NOT YET EXECUTED** with `executed=false`. This is a historical compatibility anchor, not the current execution state.

## Current Stage 4 evidence chain

The Beethoven+Barley run subsequently executed. Public-safe execution evidence digest is `0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a`; private metric-batch digest is `5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079`. The execution abstained because support was insufficient, so thresholds/resource limits remain uncalibrated.

PR #125 added the separate Wikimedia development purpose overlay with canonical digest `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07` for `dataset.item.wikimedia-guitar-technical-exercise-no1.v1` / `source.family.wikimedia-guitar-technical-exercise-no1.v1`.

PR #128 then added separate human completion evidence from genuine `human_expert_review`: all seven findings are `clear`; work-package digest is `9ccec309f611f8057b8b4a20a1aba732544c1638f2b959656b9503718206337c`; completion bundle digest is `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`.

That immutable completion snapshot correctly remains `human_labels_complete_pending_separate_acceptance` and does not retroactively claim acceptance. PR #130 separately records governance decision `ACCEPT_REAL_REFERENCE_BUNDLE`, acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`, and makes the exact development bundle candidate-derivation eligible. PR #130 does **not** authorize execution, threshold/resource changes, held-out evaluation, Stage 4 PASS, or Stage 5 entry.

## Human-reference boundary

The Wikimedia review work package has exactly seven finding slots: `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`. Allowed labels: `clear`, `possible`, `probable`, `not_assessed`. The original work package remains null-filled and immutable by design; completed human records and their later governance acceptance are separate evidence artifacts.

Model predictions, automated quality findings, or private raw metrics cannot be promoted to reference truth. Human completion and governance acceptance remain separate decisions.

## Held-out boundary

Chopin `dataset.item.imslp82860-chopin-op69.v2` remains `held_out_evaluation` only. It is excluded from Wikimedia development review and cannot derive/select/tune candidates. Development expansion, human completion, and reference acceptance do not authorize held-out evaluation.

## Current readiness blockers

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Resolved historical blockers remain historical only; none of the three current blockers is closed by PR #130. Reference-bundle acceptance permits candidate derivation only after a separate exact calibration-execution authorization opens that next gate.

## Consistency conclusion

The architecture is consistent only when historical checkpoints, immutable work-package templates, separate human completion evidence, governance acceptance, execution authorization, and execution evidence remain distinct. Raw private metrics stay outside ordinary Git; unavailable metrics use `not_applicable`, not fabricated zeroes; insufficient evidence causes abstention; production thresholds/resources remain unchanged; Stage 4 PASS and Stage 5 entry remain false.