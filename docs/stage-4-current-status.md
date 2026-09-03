# Stage 4 Current Status — Safety Calibration

**State:** ACTIVE / NOT_READY  
**Tracking:** Issue #104  
**Repository current main:** `9d2326931707f65c7eb5f5b22680e8fa85665a60`  
**Latest production merge:** PR #125 — `Stage 4: add Wikimedia development calibration expansion`  
**Latest post-merge CI:** Run #324 (`33728459668`) SUCCESS on Python 3.11 / 3.12  
**Stage 5:** NOT STARTED / BLOCKED pending Stage 4 final exit PASS

## Current execution truth

The exact Beethoven + Barley real development calibration has **executed and abstained**.

- private observation identities: 42;
- measured: 24;
- `not_applicable`: 18;
- measured source families: 1;
- threshold candidates: 0;
- thresholds calibrated: false;
- resource limits calibrated: false;
- execution evidence accepted: false;
- held-out evaluation used: false;
- held-out tuning used: false.

The production candidate methodology abstained because measured source-family support and reference-class support were insufficient. Compression had no applicable measured observations. No threshold was fabricated.

## Historical pre-execution compatibility record

This section preserves immutable earlier Stage 4 checkpoints required by validators; it does **not** override the current execution truth above.

- Historical blocker `no_real_calibration_reference_label_bundle_is_accepted`: **Resolved** by the later separate Beethoven+Barley reference-bundle acceptance evidence.
- The later, separate historical execution-authorization checkpoint records `realDataCalibrationExecutionAuthorized=true` for exact Beethoven+Barley development scope.
- That immutable authorization artifact also records `realDataCalibrationExecuted=false`; it describes the pre-execution checkpoint and is not retroactively rewritten after the later real run executed.
- At that checkpoint, **private observation metrics** were the explicit execution dependency. They later became available in approved custody for the Beethoven+Barley run; raw values remain outside ordinary Git.

## Wikimedia development expansion — production-effective

PR #125 added a separate development-only raster family after the previous execution abstained:

- dataset item: `dataset.item.wikimedia-guitar-technical-exercise-no1.v1`;
- source family: `source.family.wikimedia-guitar-technical-exercise-no1.v1`;
- source kind: PNG;
- page count: 1;
- purpose: `safety_calibration`;
- purpose grant: production-effective;
- human review required: `human_expert_review`;
- human labels present: false;
- reference bundle accepted: false;
- Wikimedia calibration execution authorized: false;
- Wikimedia calibration executed: false;
- production threshold changes authorized: false;
- production resource-limit changes authorized: false;
- Stage 4 exit pass: false;
- Stage 5 entry authorized: false.

The review package contains exactly seven slots: `skew`, `blur`, `glare`, `shadow`, `uneven_lighting`, `noise`, `compression`. Allowed labels are `clear`, `possible`, `probable`, `not_assessed`. `referenceLabel`, `reviewerReference`, `provenanceReference`, and `reviewedOn` remain null until actual human expert review. Model predictions or automated metrics cannot be used as reference truth.

Chopin `dataset.item.imslp82860-chopin-op69.v2` remains isolated as `held_out_evaluation`; it is excluded from Wikimedia development review and candidate derivation/tuning remains forbidden.

## Production Stage 4 chain

Historical checkpoints remain immutable:

- Framework start: PR #105 → main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362` → Run #259.
- Reference-label contract: PR #107 → main `b184f5e5b780213671597ffa9f4380aa4a1adb47` → Run #263.
- Public calibration-evidence contract: PR #108 → main `4c936353ede322f41d009d503bcb4ca7fa64b2b9` → Run #265.
- Exit-readiness contract: PR #109 → main `d4dff6b8c672cec1b2afa864f89bb7a03f29cd75` → Run #267.
- Beethoven+Barley purpose grants: PR #111 → main `c0c306e034322ce0cd74ba9ed6ff2184d3ffe6cd` → Run #272.
- Human review work package: PR #113 → main `7e2552c38b74abc7c60ed6bc6c74c3fc97d62c12` → Run #278.
- Human label completion: PR #114 → main `58266dffed529a5d7d247e58651865bbda83981e` → Run #280.
- Accepted development reference bundle: PR #115 → main `4f663d0c11339b98fd89639fd8f3d5afc8047fb3` → Run #282.
- Reference current-truth checkpoint: PR #116 → main `0c267cb9489cfe023a4d5e26104f5ae684cb95fb` → Run #285.
- Exact Beethoven+Barley execution authorization: PR #117 exact head `b42ad45656299651897be33b7ea98d940217095c` → Run #286 → main `76f5643dde72c8cc4b02b517133331e9dea00146` → Run #287.
- Authorization current-truth checkpoint: PR #118 → main `d833255305315c89efa4aceb2816bd819d6ffd95` → Run #291.
- Private metric runner v0.1.0: PR #119 → main `dd392f7be9522319d5d77074641b512dfdfdd930` → Run #293.
- Runner current-truth checkpoint: PR #120 → main `10c03a2f14bfd9980fc6833f5adb2c04497f74a4` → Run #296.
- Abstain-first candidate derivation: PR #121 → main `53fd096e31a111f35af0194cbd57640041e6319f` → Run #298.
- Applicability correction / runner v0.2.0: PR #122 → main `1c0b27d9284129577a85bc4d536ac118446a4e8c` → Run #302.
- Beethoven+Barley real execution evidence: PR #123 exact head `3f396c4cd693cb0d0b1cc0d90d9775cd8596c0c4` → Run #303 → main `4f0346345eb770628928ba1751b4a1d9d5fb51f1` → Run #304.
- Executed/abstained current-truth checkpoint: PR #124 → main `df053d72591c131eb5ed469cd715e8f602c8b020`.
- Wikimedia development expansion: PR #125 exact head `a99eb1dcaf30aa6e9a062f9e47519fdd2c3dbe22` → main `9d2326931707f65c7eb5f5b22680e8fa85665a60` → Run #324 (`33728459668`) SUCCESS.

## Binding evidence digests

- Stage 4 entry/start: `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.
- Beethoven+Barley safety-calibration purpose grant: `4f122063ba28cd23c1d6343c5cb39b8a92459f336ec05ad03a53f9d4d4dd2dfc`.
- Accepted Beethoven+Barley reference bundle: `edfd7b58fcd7dcebddc8e6fd6178d14ba3064acc02a2bfca1b5b211b50676b14`.
- Reference-bundle acceptance: `88fb2d061e3f63a935369bb2c66caf628f430d2e1e6a3e4e8c49e909ddded62c`.
- Historical execution authorization: `81d5bb62d494094999e106740f90dccf376296aff8bfc004f27643d6cd94ae68`.
- Private metric batch: `5bb2c2e081e6e72697a2c3acb8aacd7b4159dfabf3400fb9a0570ecb1a148079`.
- Real development execution evidence: `0d2ce54066d493e3aa5a8b3c3ef3df407532edb5fa51aee14b8a560678731f1a`.
- Wikimedia purpose-grant overlay: `603e3dc7669e6259ab061a8241d76206e7bd2bf76b170fc6dbc8c1d0b9d6be07`.

The historical execution-authorization evidence remains **AUTHORIZED / NOT YET EXECUTED** with `executed=false`; this is a historical snapshot and is not rewritten after later execution.

## Historical Stage 3 bindings retained

Stage 3 remains COMPLETE / PASS with immutable digests: purpose `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`, execution `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`, limitations `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`, acceptance `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.

## Current readiness blockers

1. `no_real_development_calibration_evidence_is_accepted`
2. `no_real_held_out_evaluation_evidence_is_accepted`
3. `no_stage4_metric_acceptance_target_policy_is_accepted`

Wikimedia purpose authorization alone does not resolve blocker 1. Completion, acceptance, execution authorization, private execution, and governance acceptance remain separate.

## Next safe boundary

The next substantive dependency is real human completion of the seven Wikimedia review slots with opaque non-PII reviewer reference, provenance reference, and ISO review date. Until that external evidence exists, code/tests/validators/documentation may advance, but no completed label set, accepted bundle, execution authorization, private metric result, threshold candidate, Stage 4 PASS, or Stage 5 entry may be claimed.