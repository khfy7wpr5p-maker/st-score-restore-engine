# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stages 1–5 COMPLETE / PASS; Stage 6 entry eligible but NOT AUTHORIZED / NOT STARTED  
**Date:** 2026-09-04  
**Tracking:** Issue #104

## Authority and invariants

Merged `main` plus production-effective evidence is current truth. Historical evidence remains immutable. Later current-truth overlays may supersede an earlier checkpoint's *current-state interpretation* without rewriting that historical file. Real corpus/derivative bytes and private raw observation metrics remain outside ordinary Git. Held-out evidence never derives, selects, or tunes development candidates. Human reference truth must come from actual human expert review. Insufficient evidence requires abstention.

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

## Completed stages

### Stage 1 — Real and explicitly authorized test dataset

**State:** COMPLETE / PASS / production-effective.

Immutable architecture anchors retained: C15 `b4a58ccc2e21338ef2708fef8352b4d3979547e871ad6fa19d6c256f1560a476`; C16 `0589698059c4bc3cd9e19495f8174c46d9b9d6460a59b6d6890b078a2144aa4e`; catalog v2 `4dd989a16c466027a952c6d8ea7c325e27681b95995554afd55e0b3fee2051b3`; expanded snapshot v2 `c1a315b76bc79f8649abd50e938b8a33362f1deb3e5b004d0e25519e45c23dc7`; coverage report v2 `45136e95006962570ac6d290fe6204c474958a209c595d3fd8cb525bc90f8834`.

### Stage 2 — Complete quality-analysis system

**State:** COMPLETE / PASS / production-effective.

Immutable execution-evidence digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

### Stage 3 — Multi-page PDF pipeline

**State:** COMPLETE / PASS / production-effective.

Immutable digests: purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`; execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`; limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

### Stage 4 — Safety calibration with real data

**State:** COMPLETE / PASS / production-effective.

Final-exit checkpoint: PR #148 / main `4ff1118fe79602b351ad9ab8735937b9e911555d`; final acceptance digest `41923c6c05c7ea015841fd77da7377aad30261a569d287246eb832f856ad599c`.

Accepted Stage 4 truth is deliberately abstention-first:

- zero-candidate safe abstention was accepted;
- candidate thresholds were **not** accepted;
- thresholds and resource limits remain uncalibrated engineering defaults;
- held-out Chopin evaluation evidence was accepted without using held-out data for tuning;
- representativeness, absence of bias, OMR correctness, restoration effectiveness, and model quality were not established.

The detailed immutable/current-truth record is `docs/live/ST_SCORE_RESTORE_STAGE4_FINAL_EXIT_CURRENT_TRUTH.json`.

#### Historical Stage 4 transition checkpoint — immutable, superseded current-state interpretation

The architecture-consistency audit also retains the earlier transition checkpoint verbatim enough to prove that historical governance was not erased when later stages completed. At that historical point **Stage 4 ACTIVE** and **Stage 5 BLOCKED** were the correct states. The Stage 4 framework production anchor was `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`; the Stage 4 entry/start digest was `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`. The later real-development execution-authorization production main was `76f5643dde72c8cc4b02b517133331e9dea00146`, Run #287, with authorization digest `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.

That historical authorization meant real development calibration was **authorized but not yet executed** at that checkpoint, and the private metric dependency still applied. The historical readiness blockers were:

- `no_real_development_calibration_evidence_is_accepted`
- `no_stage4_metric_acceptance_target_policy_is_accepted`
- `no_real_held_out_evaluation_evidence_is_accepted`

Those blockers were resolved by later evidence and acceptance gates; retaining them here is historical binding, not a claim that Stage 4 is currently ACTIVE or Stage 5 is currently BLOCKED.

### Stage 5 — Accessible teacher review interface

**State:** COMPLETE / PASS / production-effective.

Production local UI checkpoint: PR #153 / main `ad3dc11cec311b345fac600316a44d05d444f21b`.

Final-exit checkpoint: PR #155 / main `19aaa35ac212b2a1698cd23b622bfd59c1e721b4`.

Accepted evidence includes:

- real Chrome accessibility, responsive, stale-screen and evidence-bound decision QA;
- real production `/review` screen-reader execution with Orca 46.1 + Chrome 152 + AT-SPI; the probe remained temporary and unmerged as PR #154;
- bounded grayscale display-integrity QA in real Chrome;
- `actual_pixels` at `1.00x` verified against decoded pixel dimensions;
- Stage 5 QA evidence digest `0e7ae71251db637ee9ba99cdcd5e2216fdfd3d655dc5eda23b676ea9ec5699fe`;
- Stage 5 final acceptance digest `467eaf11c451d114d3ef41afd44c87cf2dce5cb68f89a5d6cfc45a81e1eed9fc`.

Display scope remains deliberately bounded: evidence crops are `png_grayscale_8bit`; input color profiles are `not_inspected`; `colorManagementValidated=false`; no color-fidelity certification is claimed. Stage 5 PASS covers the accessible local teacher-review interface and its evidence-display contract. It does **not** authorize an untrusted-network deployment or establish restoration/OMR/model quality.

The later current-truth overlay is `docs/live/ST_SCORE_RESTORE_STAGE5_FINAL_EXIT_CURRENT_TRUTH.json`.

## Stage 6 — Identity, network and production infrastructure

**State:** ENTRY ELIGIBLE / NOT AUTHORIZED / NOT STARTED.

Stage 5 PASS makes Stage 6 entry eligible only. The next safe governance boundary is a **separate explicit Stage 6 entry authorization**. Until then, production identity, TLS/network exposure, secret management, production deployment, production persistence/infrastructure changes, and related Stage 6 execution remain unauthorized.

## Stages 7–12

**State:** NOT STARTED.

They remain sequenced behind Stage 6 and require their own later gates. Stage 5 completion does not authorize preview release, DocRes adoption, multi-engine comparison, selector/model training, publication, or music-application integration work.
