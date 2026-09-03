# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images. This repository is **not** an OMR engine. Source bytes remain immutable; exact SHA-256 defines artifact identity; real corpus/derivative bytes and private raw observation metrics stay outside ordinary Git.

## Production baseline and latest human-reference checkpoints — 2026-09-03

- **Wikimedia expansion production baseline:** main `9d2326931707f65c7eb5f5b22680e8fa85665a60`, PR #125, `Stage 4: add Wikimedia development calibration expansion`, post-merge Run #324 (`33728459668`) SUCCESS on Python 3.11/3.12.
- **Wikimedia human-label completion checkpoint:** main `2ce6151e7ce37198c5b264ddd577df71f49da8bf`, PR #128, `Stage 4: record Wikimedia human label completion`, post-merge Run #340 (`33745945427`) SUCCESS on Python 3.11/3.12.
- **Wikimedia reference-bundle acceptance checkpoint:** main `3353b281a4022f107929fae296368390da45a4fb`, PR #130, `Stage 4: accept Wikimedia human reference bundle`, post-merge Run #348 (`33748180036`) SUCCESS on Python 3.11/3.12.
- **Stage 1:** COMPLETE / PASS / production-effective.
- **Stage 2:** COMPLETE / PASS / production-effective.
- **Stage 3:** COMPLETE / PASS / production-effective.
- **Stage 4:** **ACTIVE / NOT_READY**.
- **Stage 5:** **BLOCKED** pending separate Stage 4 final exit PASS.

The Beethoven + Barley real development calibration was executed and **abstained**: 42 observation identities were accounted for as 24 measured + 18 `not_applicable`; measured support came from 1 source family; candidate thresholds derived: 0. Execution evidence remains not governance-accepted. Production Stage 2 thresholds and Stage 3 resource limits remain `uncalibrated_engineering_defaults`.

PR #125 added a second raster development source family for Stage 4 support, PR #128 later froze the genuine human review completion as a separate evidence artifact, and PR #130 separately accepted that exact Wikimedia reference bundle for development candidate derivation:

- dataset item `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
- source family `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- one-page PNG, development-only `safety_calibration` purpose grant;
- immutable Wikimedia purpose-grant overlay digest `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07`;
- human labels present in separate completion evidence: **true — 7/7 `clear`**;
- immutable completion snapshot state: `human_labels_complete_pending_separate_acceptance`;
- immutable work package remains pristine/null-filled by design;
- Wikimedia reference bundle accepted by separate PR #130 evidence: **true**;
- candidate derivation eligible: **true**;
- Wikimedia real calibration execution authorized: **false**;
- Wikimedia real calibration executed: **false**;
- production threshold/resource changes authorized: **false**;
- Chopin remains held-out and excluded from development review/tuning.

The Wikimedia review package has exactly seven human-review finding slots: `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`. Allowed human labels are `clear`, `possible`, `probable`, `not_assessed`. The original work package keeps `referenceLabel`, `reviewerReference`, `provenanceReference`, and `reviewedOn` null; the completed human evidence is stored separately in `human-label-completion.v1.json`, and its later governance acceptance is stored separately in `reference-bundle-acceptance.v1.json`. Automated metrics/model predictions cannot be reference truth.

## Historical evidence anchors retained

Historical evidence is immutable. The following checkpoints remain binding history and must not be rewritten:

- Stage 3 purpose digest `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.
- Stage 3 execution digest `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.
- Stage 3 limitations digest `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.
- Stage 3 final acceptance digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.
- Stage 4 framework anchor main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` / Run #259.
- Stage 4 entry/start digest `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.
- Beethoven+Barley purpose-grant main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` / Run #272; digest `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.
- Accepted Beethoven+Barley reference bundle main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` / Run #282; bundle digest `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`; acceptance digest `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`.
- Historical exact execution authorization main `76f5643dde72c8cc4b02b517133331e9dea00146` / Run #287; authorization digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.
- Wikimedia reference-bundle acceptance main `3353b281a4022f107929fae296368390da45a4fb` / Run #348; bundle digest `37af98bbeb04832fc94382f246287da0b738c2520225cdcd9f5ea2028bde71f4`; acceptance digest `79771e291768ba4979abc1e44dd0ecebfd95892ff2e5861d77706c1cb4563eb3`.

The phrase **AUTHORIZED / NOT YET EXECUTED** refers only to that immutable historical pre-execution authorization checkpoint. Current truth is that the Beethoven+Barley run later executed and abstained; the historical record still correctly carries `executed=false` because authorization evidence is not retroactively mutated.

## Stage 4 current blockers

Stage 4 remains `NOT_READY` with these prerequisite blockers:

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Wikimedia reference-bundle acceptance does not close blocker 1. Separate exact execution authorization, custody-only real metrics, expanded development calibration, and later governance acceptance remain distinct gates.

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

Raw private metrics are custody-only and forbidden in ordinary Git. Unavailable metrics must be `not_applicable`, never fabricated numeric zeroes. Model/automatic predictions cannot become human reference truth. Development and held-out evidence remain strictly separated. No Stage 4 final PASS, Stage 5 entry, production threshold/resource change, training, publication, external export, or calibration execution is authorized by PR #125, PR #128, or PR #130.