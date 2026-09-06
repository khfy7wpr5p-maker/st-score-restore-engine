# ST Score Restore Engine — Development Roadmap

**Current production status (2026-09-06):** Stages 1–5 COMPLETE / PASS; Stage 6 ACTIVE; S6-07 synthetic operational safety/recovery drills COMPLETE; provider UNSELECTED; Stage 7 NOT STARTED.  
**Tracking:** Issue #104

## Current production truth

Merged `main` plus later production-effective acceptance/current-truth overlays are authoritative for current state. Historical evidence and historical roadmap checkpoints remain immutable and are retained below because older fail-closed validators intentionally prove that those earlier governance states were not erased.

- Stage 4 final exit: COMPLETE / PASS. Final acceptance digest `41923c6c05c7ea015841fd77da7377aad30261a569d287246eb832f856ad599c`.
- Stage 5 accessible teacher review interface: COMPLETE / PASS / production-effective.
- Stage 5 local UI checkpoint: PR #153 / main `ad3dc11cec311b345fac600316a44d05d444f21b`.
- Stage 5 final-exit checkpoint: PR #155 / main `19aaa35ac212b2a1698cd23b622bfd59c1e721b4`.
- Stage 5 QA evidence digest: `0e7ae71251db637ee9ba99cdcd5e2216fdfd3d655dc5eda23b676ea9ec5699fe`.
- Stage 5 final acceptance digest: `467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc`.
- Real production `/review` screen-reader execution used Orca 46.1 + Chrome 152 + AT-SPI on temporary unmerged PR #154.
- Bounded display scope: `png_grayscale_8bit`, input color profiles `not_inspected`, `colorManagementValidated=false`; no color-fidelity certification is claimed.
- Stage 6 provider-neutral identity, secrets/KMS/IAM, network, storage/queue/recovery, audit and deployment contracts are implemented.
- S6-07 deterministic synthetic-only operational drills passed queue redelivery/stale-worker fencing, crash recovery/idempotent replay, deletion/restore anti-resurrection, audit fail-closed behavior, deployment/rollback gating and bounded concurrency stress.
- Provider selection, live resource creation, production load/soak validation, independent production-security sign-off and production deployment remain separately unauthorized or incomplete.
- The next Stage 6 safe boundary is separate S6-08 integration/security regression authorization.

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
Stage 9A Music-Symbol Preservation Model
Stage 10 ST Restore Selector
Stage 11 ST Restore image model
Stage 12 Music-application integrations
```

### Stage 9A architecture amendment — Music-Symbol Preservation Model

Stage 9A is inserted after the Stage 9 comparator foundation and before Stage 10 Selector without renumbering existing stages. The architectural decision is recorded in ADR 0018.

The Stage 9A component is the **ST Music-Symbol Preservation Model (MSPM)**. It is a future learned semantic safety/veto layer that compares the immutable source with a restoration variant and asks whether musically meaningful notation/TAB symbols were preserved.

Initial target classes include staff/TAB lines, noteheads, stems, flags, beams, augmentation dots, rests, accidentals, clefs, key/time signatures, barlines/repeats, ties/slurs, TAB digits/string relationship and core visually distinguishable guitar articulations.

Stage 9A is not a restoration engine and is not an OMR engine. It does not generate MusicXML or automatically correct notation. It supplements, rather than replaces, the deterministic Music/TAB Safety Validator. High-confidence symbol deletion/invention/displacement may veto a candidate; insufficient or ambiguous evidence must fail closed to abstention/original/teacher review.

Stage 9 may initially compare candidates using deterministic safety evidence. After Stage 9A activation, semantic preservation evidence becomes an additional comparator/selector safety dimension. Stage 10 may consume this evidence but may not override a hard deterministic or semantic veto.

This roadmap amendment records architecture only. It does **not** authorize dataset collection, model training, model-weight publication, production inference or online learning. Stage 9A implementation, training, evaluation and activation require their own explicit authorizations and accepted evidence.

## Historical roadmap snapshot retained for immutable evidence binding

The remainder of this document preserves the earlier Stage 4 ACTIVE / Stage 5 BLOCKED roadmap checkpoint. Every ACTIVE, NOT_READY, BLOCKED, authorization, Run, digest, and blocker statement below is **historical**, not the current production state. It remains present so legacy Stage 4 consistency validators can prove that historical governance was not rewritten.

**Historical document status:** Binding sequence; Stage 4 ACTIVE / NOT_READY after production-effective Wikimedia reference-bundle acceptance  
**Historical date:** 2026-09-03  
**Wikimedia expansion baseline:** main `9d2326931707f65c7eb5f5b22680e8fa85665a60` / PR #125 / Run #324 (`33728459668`) SUCCESS  
**Human-label completion checkpoint:** main `2ce6151e7ce37198c5b264ddd577df71f49da8bf` / PR #128 / Run #340 (`33745945427`) SUCCESS  
**Reference-bundle acceptance checkpoint:** main `3353b281a4022f107929fae296368390da45a4fb` / PR #130 / Run #348 (`33748180036`) SUCCESS

### Historical authority and invariants

Merged `main` plus production-effective evidence was current truth at that checkpoint. Historical evidence remains immutable. Real corpus/derivative bytes and private raw observation metrics remain outside ordinary Git. Held-out evidence never derives/selects/tunes development candidates. Human reference truth must come from actual human expert review. Insufficient evidence requires abstention.

### Historical production stages

Stage 1: COMPLETE / PASS / production-effective. Immutable evidence anchors retained for architecture validation: C15 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; C16 `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`; catalog v2 `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; expanded snapshot v2 `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report v2 `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

Stage 2: COMPLETE / PASS / production-effective. Immutable execution-evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

Stage 3: COMPLETE / PASS / production-effective. Immutable digests: purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

### Historical Stage 4 — Safety calibration with real data

**State:** ACTIVE / NOT_READY.  
**Stage 5:** BLOCKED pending separate Stage 4 final exit PASS.

#### Historical Stage 4 anchors

- framework main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259;
- entry/start digest `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`;
- Beethoven+Barley purpose grant main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272; digest `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`;
- accepted Beethoven+Barley reference bundle main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282; bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`; acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`;
- exact Beethoven+Barley execution authorization main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287; digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

The historical checkpoint **AUTHORIZED / NOT YET EXECUTED** remains immutable and therefore still carries `executed=false`; it is not current execution truth.

#### Historical development calibration truth

Beethoven + Barley execution later ran and abstained. Public-safe evidence records 42 identities = 24 measured + 18 `not_applicable`, 1 measured source family, and 0 threshold candidates. Thresholds/resource limits remain uncalibrated engineering defaults and the execution evidence was not governance-accepted at this historical checkpoint.

PR #125 added a separate Wikimedia raster development family, PR #128 completed its genuine human review, and PR #130 separately accepted the exact completed reference bundle:

- `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
- `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- one-page PNG;
- split `development`;
- purpose `safety_calibration` granted by a separate immutable overlay;
- purpose-grant overlay digest `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07`;
- separate human-label completion: production-effective via PR #128 / main `2ce6151e7ce37198c5b264ddd577df71f49da8bf` / Run #340;
- **7/7 labels: `clear`** (`skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`);
- immutable completion snapshot state `human_labels_complete_pending_separate_acceptance`;
- original work package remains null-filled/pristine by design;
- separate reference-bundle acceptance: production-effective via PR #130 / main `3353b281a4022f107929fae296368390da45a4fb` / Run #348;
- acceptance decision `ACCEPT_REAL_REFERENCE_BUNDLE`;
- acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`;
- reference bundle accepted: true;
- candidate derivation eligible: true;
- calibration execution not authorized and not executed;
- production threshold/resource changes not authorized;
- Chopin held-out boundary unchanged.

Automated metrics/model predictions were not substituted for the human labels. Completion, governance acceptance, execution authorization, execution evidence, and later development evidence acceptance remain separate gates.

#### Historical remaining readiness blockers

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

These three blocker codes are retained as historical evidence. They were later resolved by subsequent Stage 4 acceptance gates and do not describe the current Stage 4 state.

### Historical Stages 5–12 status

At this checkpoint they were NOT STARTED, and Stage 5 was BLOCKED pending Stage 4 final PASS. That statement is historical. Current Stage 5 is COMPLETE / PASS; current Stage 6 is active with S6-07 synthetic operational drills complete, provider still unselected, and Stage 7 not started.