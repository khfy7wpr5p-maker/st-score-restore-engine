# ST Score Restore Engine — Development Roadmap

**Document status:** Binding sequence; Stage 3 COMPLETE / PASS / production-effective  
**Version:** 0.6.0  
**Date:** 2026-09-02  
**Stage 3 tracking:** Issue #90  
**Stage 3 final acceptance main:** `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`  
**Stage 3 final post-merge CI:** Run #253 (`33646323461`) — Python 3.11 / 3.12 SUCCESS  
**Stage 4:** ENTRY ELIGIBLE / NOT STARTED

## Authority and invariant rules

Repository truth is merged `main` plus accepted deterministic evidence. Historical evidence is never rewritten retroactively. Source bytes remain immutable; real corpus/derivative bytes stay outside ordinary Git; held-out data never tunes Stage 2/3 thresholds, page policy, hardening constants or renderer/resource limits; vector/hybrid content is never silently rasterized; exact-head and post-merge CI are mandatory.

Stage 3 PASS makes Stage 4 **entry eligible only**. It does not start Stage 4, calibrate thresholds or grant training/calibration/publication permission.

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

**State:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; final acceptance / Stage 3 entry main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; Run #228 (`33609061197`) Python 3.11/3.12 SUCCESS. Frozen execution evidence digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.

## Stage 3 — Multi-page PDF pipeline

**State:** COMPLETE / PASS / production-effective.  
**Tracking:** Issue #90.  
**Core main / CI:** `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232.  
**Authorized-execution main / CI:** `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235.  
**Purpose-grant main / CI:** `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238.  
**Runner runtime main / CI:** `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246.  
**Execution-evidence main / CI:** `b15d91ff3fbf21b47a0e484b5a337c4611a17355` / Run #251.  
**Final acceptance main / CI:** `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253.

ADR 0017 selects exact `pypdfium2==5.13.0` / PDFium. Resource defaults remain uncalibrated: 200 DPI; 64 pages; 40M pixels/page; 160M aggregate; 8,000-pixel dimension; page-object depth 15.

Stage 3 real-corpus execution used exact Beethoven, Barley and held-out Chopin source identities. Results: 3 items / 14 pages / 12 raster pages rendered / 2 vector pages preserved / 0 review-required / page order preserved / no vector rasterization / no held-out threshold tuning.

Public-safe execution evidence digest: `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.

Limitations review digest: `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`; decision `PASS_WITH_ACCEPTED_LIMITATIONS`.

Final acceptance: `evidence/stage3/corpus/stage3-exit-acceptance.v1.json`; decision `PASS`; canonical SHA-256 `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`; `stage4EntryEligible=true`; `stage4Started=false`.

Purpose overlay remains exact and separate from historical Stage 1 metadata. Grant SHA-256: `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`. Chopin remains evaluation-only and non-tuning.

## Stage 4 — Safety calibration with real data

**State:** ENTRY ELIGIBLE / NOT STARTED.

Stage 4 owns calibration. A separate Stage 4 entry/start decision must define its scope, eligible development/held-out use, calibration objectives, metrics, anti-leakage rules and new acceptance gates before any thresholds or resource limits are changed.

Stage 3 PASS does **not** by itself authorize calibration, training or publication.

## Stages 5–12

**State:** NOT STARTED.

## Current next safe action

Close Stage 3 tracking Issue #90 after the production-truth checkpoint is merged and post-merge CI is green. Then prepare a separate Stage 4 entry plan; do not begin calibration implicitly.