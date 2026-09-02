# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images.

This repository is **not** an OMR engine. Source bytes remain immutable, exact SHA-256 defines artifact identity, real corpus/derivative bytes stay outside ordinary Git, and unsupported derivatives never replace the source fallback.

## Current production truth — 2026-09-02

- **Stage 1:** COMPLETE / PASS / production-effective.
- **Stage 2:** COMPLETE / PASS / production-effective. Execution-evidence main `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; digest `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
- **Stage 3:** COMPLETE / PASS / production-effective. Final acceptance main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`; acceptance digest `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`.
- **Stage 4:** **ACTIVE — FRAMEWORK / GOVERNANCE ONLY.** Framework start became production-effective through PR #105 at main `4a5c3db2d767dac235fe12a6bd0e18ba500e7362`; post-merge Run #259 (`33659753403`) passed Python 3.11 and 3.12.
- **Real-data Stage 4 calibration:** **BLOCKED / NOT AUTHORIZED.** No accepted artifact currently has a granted `safety_calibration` purpose and no accepted real calibration reference-label bundle exists.
- **Stage 5:** NOT STARTED / BLOCKED pending Stage 4 exit PASS.

Stage 4 entry/start decision: `evidence/stage4/governance/stage4-entry-start.v1.json`, canonical SHA-256 `013b29f861a68c755d17d1a0106183db4b35367b4c7bd9ce6c08c90c114171e8`.

The Stage 4 framework provides deterministic calibration observations/candidates, development-only candidate derivation, held-out evaluation without feedback, false-negative/false-positive/coverage metrics and source-family anti-leakage checks. It does **not** authorize production threshold changes, resource-limit changes, model training or publication.

## Stage 3 accepted evidence

Production renderer remains exact `pypdfium2==5.13.0` / PDFium. Resource limits remain `uncalibrated_engineering_defaults`: 200 DPI, 64 pages, 40M pixels/page, 160M aggregate pixels, 8,000-pixel dimension, page-object depth 15.

Stage 3 real batch: 3 items / 14 pages / 12 raster pages rendered / 2 vector pages preserved / 0 review-required; page order preserved; no vector rasterization; held-out tuning false.

- Purpose-grant digest: `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`.
- Execution-evidence digest: `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.
- Limitations-review digest: `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.

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

## Development baseline

- Python `>=3.11,<3.13`
- CI Python 3.11 and 3.12
- OpenCV `opencv-python-headless==4.13.0.92`
- NumPy `2.3.5`
- PDF renderer `pypdfium2==5.13.0`
- API `/api/v1`, version `0.5.0`
- ordinary Git real corpus/derivative bytes: zero

## Safety boundary

Held-out evidence may evaluate a frozen Stage 4 candidate but may never derive, select or tune thresholds or resource limits. General project approval is not a dataset purpose grant. `calibrationAuthorized=false`, `realDataCalibrationExecuted=false`, training remains unauthorized, and Stage 4 has not exited.