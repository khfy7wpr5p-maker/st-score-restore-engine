# ST Score Restore Engine

Safety-first visual restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured images.

This repository is **not** an OMR engine. Source bytes remain immutable, exact SHA-256 is the artifact-identity boundary, real corpus/derivative bytes stay outside ordinary Git, and unsupported derivatives never replace the original fallback.

## Processing boundary

```text
PDF / JPG / JPEG / PNG / Phone photo
              ↓
Immutable source registration + inspection
              ↓
Rights / privacy / purpose / custody / exact-byte gates
              ↓
PDF page policy
              ├─ raster_only → bounded PDFium derivative
              ├─ vector_only → preserve vector content
              ├─ hybrid → preserve + review
              └─ unsupported/over-limit → original fallback + review
              ↓
Deterministic quality analysis
              ↓
Restoration candidate + safety validation
              ↓
Original fallback / comparator eligibility
              ↓
ScoreMosaic Safe Intake → OMR → MusicXML
```

## Current production truth — 2026-09-02

- **Stage 1:** COMPLETE / PASS / production-effective.
- **Stage 2:** COMPLETE / PASS / production-effective. Execution-evidence main: `ffea7f5aa618187f3cabcfb49801804e3f6658bf`; frozen execution evidence digest: `78731c40eda1684565dcf31b379a92be3c0f0cc19acb71ccc2b873ea9cbb011d`.
- **Stage 3:** **COMPLETE / PASS / production-effective.** Final acceptance merged through PR #102 to main `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0`; post-merge Repository validation Run #253 (`33646323461`) passed Python 3.11 and 3.12.
- **Stage 4:** **ENTRY ELIGIBLE / NOT STARTED.** Stage 4 owns real-data safety calibration. Eligibility is not calibration authorization and does not imply work has started.

Stage 3 production evidence chain:

- PDFium core: `29b4244eeaeb2239ff959e6dd6d4128311f005fa` / Run #232;
- authorized execution: `d834ed42e3f553308aef7f6adb7e8cb873593f0b` / Run #235;
- Beethoven/Barley purpose overlay: `6ebe160309c562e9841a3c313d5ca507592f1386` / Run #238;
- real-corpus runner runtime main: `5e682f1933a7167fc142689306352fe53b4b1833` / Run #246;
- real-corpus execution evidence main: `b15d91ff3fbf21b47a0e484b5a337c4611a17355` / Run #251;
- final Stage 3 acceptance main: `c09a10aaa1499c77d1e9df535ac1f1c8cf675ea0` / Run #253.

## Stage 3 accepted evidence

Production renderer: `pypdfium2==5.13.0` / PDFium. Resource limits remain uncalibrated engineering defaults: 200 DPI, 64 pages, 40M pixels/page, 160M aggregate pixels, 8,000-pixel dimension and page-object depth 15.

Real authorized batch: Beethoven + Barley + held-out Chopin, exact accepted source identities, 3 items / 14 pages. Twelve raster-only pages were rendered; two vector-only pages were preserved; page order was preserved; no vector page was silently rasterized; held-out tuning was false.

Public-safe Stage 3 execution evidence: `evidence/stage3/corpus/execution-evidence.v1.json`, canonical SHA-256 `a79723e9c5a4726757ce5d6206d69766f676149ffa131a463605d04d7f98f9f6`.

Limitations review: `evidence/stage3/corpus/limitations-review.v1.json`, decision `PASS_WITH_ACCEPTED_LIMITATIONS`, canonical SHA-256 `5714687bf9f0e09d948a5b3a6c54c69f9fbfd93c084ab3c00b9de09b87af620d`.

Final acceptance: `evidence/stage3/corpus/stage3-exit-acceptance.v1.json`, decision `PASS`, canonical SHA-256 `e9729b40a04ac2cdd60fa01d742e787d262faaf711db8aa367dc3d7159263a90`. It records `stage4EntryEligible=true` and `stage4Started=false`.

Purpose-grant overlay remains separate from the immutable Stage 1 catalog: `evidence/stage3/governance/purpose-grants.v1.json`, canonical SHA-256 `3350b85407b783fff451238932982fdc94618fad404e2f4b70401ca1db010aa8`. Beethoven/Barley are Stage 3 development evaluation only; Chopin remains held-out evaluation only.

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

CI validates Stage 1/2 accepted evidence, Stage 3 PDF/custody/runner/execution-evidence/final-acceptance contracts, architecture consistency, full unit tests and Python compile.

## Safety/non-claims

Stage 3 PASS does not establish corpus representativeness, absence of bias, restoration effectiveness, OMR improvement or musical correctness. It does not authorize model training, calibration or publication. The separate sensitive `Fly Me to the Moon` phone-photo path remains independently blocked pending real high-assurance-vault verification.