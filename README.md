# ST Score Restore Engine

AI-assisted, safety-first restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured sheet-music photos.

## Approved processing flow

```text
PDF / JPG / JPEG / PNG / Phone photo
              ↓
Immutable source + document/quality analysis
              ↓
┌──────────────────────────────────────────────┐
│ OpenCV        DocRes          ST Image AI    │
│ current       future          future         │
└──────────────────────────────────────────────┘
              ↓
Per-variant music-score / TAB safety validation
              ↓
Comparator
(original always remains a selectable baseline)
              ↓
Selected source variant
              ↓
ScoreMosaic Safe Intake
              ↓
ScoreMosaic OMR
              ↓
MusicXML
```

The target path is architecture-locked by [ADR 0015](docs/adr/0015-restoration-pipeline-validation-comparator-handoff.md). A restoration derivative must be safety-validated before comparator eligibility; a rejected derivative cannot win; and the immutable original always remains selectable. The future ST Restore Selector may choose optional engines or profiles, but it may not bypass or reorder the mandatory validation → comparator → original-aware selection sequence.

The current runtime remains OpenCV-only. It implements validator-before-comparator ordering for its bounded current workflow and records the immutable original as a selectable baseline. It does **not** activate DocRes, ST Image AI, the Roadmap Stage 9 multi-engine comparator, the Stage 10 selector, ScoreMosaic runtime dispatch, model training, or any later roadmap stage.

## Repository boundary

This repository remains an independent service. SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway, and ScoreMosaic/Scremosaik integrate only through versioned contracts; their repositories are not merged into this engine.

ST Score Restore produces visual `restoration_variant` artifacts. It is not an OMR engine and its variants must not be confused with ScoreMosaic OMR candidates. A selected visual source variant must cross ScoreMosaic's own Safe Intake boundary before OMR processing.

## Current status

Architecture, governance, fixture permissions, immutable input inspection, deterministic OpenCV candidate generation, conservative music-score/TAB validation, a non-production `/api/v1` job/teacher-review workflow, optional durable local storage, attempt-bound worker fencing with in-flight recovery, a strict local HTTP/multipart boundary, and immutable reviewer evidence bundles are implemented.

The current Stage 1 state is:

- **Stage 1A — metadata governance:** complete;
- **Stage 1B — high-assurance custody/operations boundary:** complete and formally closed;
- **Stage 1C — authorized artifact onboarding and corpus realization:** active under Issue #47;
- **Stage 2 — complete quality analysis:** blocked until the complete Stage 1 exit gate passes.

ADR 0016 risk-tiered custody is implemented, not merely proposed. Catalog schema `1.3.0` and the deterministic profile/eligibility machinery are merged. The binding custody mapping is:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when exact artifact terms permit it;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved/rejected governance → `blocked`.

The G4 Stage 1 purpose allowlist remains limited to `quality_evaluation` and `held_out_evaluation`. Exact-artifact rights, privacy, purpose, retention, dataset review, provenance, digest/size binding, custody verification, and admission remain independent fail-closed gates.

C5-C17A are merged. C12 and C14 realized two independently authorized real public-domain scanned-score items outside ordinary Git. C15 froze that two-item corpus as an immutable digest-addressed historical snapshot. C16 measured the exact C15 snapshot and concluded **`insufficient`**: 2 real items / 12 pages do not provide enough notation-layout, capture-condition, degradation, or split diversity for Stage 1 exit.

C17A / PR #68 is merged at exact reviewed head `3424cc22d686b1d08ec0ff1c6be1d372b1ff4146`; merge commit `010db20a4feb71dd36c9c5378d4d486836c5abc0`. It admits one rights-clean Public Domain PNG as **`combined_staff_tab` only** for `quality_evaluation` under `open_corpus` / `managed_standard`. It is deliberately **not** also counted as standalone `guitar_tab`, so historical and future coverage is not artificially inflated. Repository validation Run #147 passed on Python 3.11 and 3.12.

The historical C15/C16 snapshot remains immutable and unchanged by C17A. C17 additions require a new versioned snapshot before they can alter the deterministic coverage decision.

C17B/C17C/C17D source qualification is the current continuation: standalone guitar TAB, naturally degraded material, and an independently rights-clean genuine phone-photo path have qualified candidates, but their preferred public-source exact bytes are not yet present in the authorized Stage 1 custody workspace. No digest, admission, snapshot membership, or coverage closure is claimed until exact-byte evidence exists.

A real user-provided phone photo remains blocked unless its `sensitive_custody` path has a genuinely verified `high_assurance_vault`. C10 proves structural compatibility only; it does not prove a real vault or authorize sensitive artifact onboarding.

See [Stage 1C current status](docs/stage-1c-current-status.md) for the canonical current-state reconciliation and [Stage 1 exit evidence](docs/stage-1-exit-evidence.md) for the gate evidence.

Production deployment, encrypted cloud object storage, an external queue, production identity, arbitrary multi-page PDF processing, a complete browser review UI, automatic teacher approval, DocRes, ST Image AI, OMR, and MusicXML integration remain disabled or deferred.

## Binding development order

The project uses a data-first, measurement-first sequence. Later stages may not be pulled forward merely because implementation appears possible.

```text
Stage 0  Roadmap update
      ↓
Stage 1  Real and explicitly authorized test dataset
      ↓
Stage 2  Complete quality-analysis system
      ↓
Stage 3  Multi-page PDF pipeline
      ↓
Stage 4  Safety calibration with real data
      ↓
Stage 5  Accessible teacher review interface
      ↓
Stage 6  Identity, network and production infrastructure
      ↓
Stage 7  Preview release
      ↓
Stage 8  DocRes optional candidate
      ↓
Stage 9  Multi-engine comparator
      ↓
Stage 10 ST Restore Selector
      ↓
Stage 11 ST Restore image model
      ↓
Stage 12 Music-application integrations
```

Every implementation slice must publish objective evidence before transition. Draft, Ready-for-review, and merge remain separate objective technical gates with fresh exact-head verification. Under the autonomous authorization recorded in Issue #47, separate per-transition user confirmation is not required while that authorization remains in force. The detailed entry and exit gates are defined in [the development roadmap](docs/roadmap.md).

## Development baseline

- Primary runtime: Python 3.12
- Compatibility validation: Python 3.11 and 3.12
- Runtime lock: `requirements.lock`
- OpenCV backend: `opencv-python-headless==4.13.0.92`
- NumPy runtime: `numpy==2.3.5`
- Job API: `/api/v1`, version `0.5.0`
- Review contract: reviewer-only immutable evidence bundles and stale-screen binding
- HTTP baseline: strict standard-library server with bounded headers/body/timeouts; not approved for untrusted networks
- HTTP connection model: one request per connection; pipelining, chunked requests, upgrades, and `Expect` are rejected
- Storage baseline: in-memory by default; opt-in local SQLite metadata and content-addressed blobs
- Local worker safety: attempt-bound lease tokens, transaction fencing, and expired in-flight recovery
- Real Stage 1 artifact bytes: stored outside ordinary Git; repository metadata uses exact digests plus opaque evidence/custody references
- Source identity: deterministic SHA-256 artifact manifest
- Candidate identity: separate SHA-256 digest and audit manifest
- Safety report: staff and TAB geometry, line continuity, local symbol and component risk
- Review evidence: source-space overlays, deterministic grayscale before/after crops, transform provenance
- Audit: append-only hash-linked events, verified when durable state is loaded
- Digital PDFs: preserved as vector; never implicitly rasterized
- Teacher approval: separate from candidate generation, dataset inclusion, and training consent

Validate the repository contracts with:

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

Inspect, restore, and validate a source:

```bash
python tools/inspect_input.py path/to/score.pdf
python tools/restore_image.py source.png candidate.png --audit candidate.audit.json
python tools/validate_music_safety.py source.png candidate.png \
  --report candidate.safety.json \
  --candidate-manifest candidate.audit.json
```

Run the local non-production API with the default in-memory store:

```bash
export ST_SCORE_CLIENT_API_KEY='replace-with-at-least-16-characters'
export ST_SCORE_REVIEWER_API_KEY='replace-with-a-different-16-character-key'
python tools/run_api.py --host 127.0.0.1 --port 8080
```

Opt into restart-persistent local storage:

```bash
python tools/run_api.py \
  --host 127.0.0.1 \
  --port 8080 \
  --data-dir runtime-data/st-score-restore \
  --worker-lease-seconds 300
```

The selected data directory contains source and derived document bytes and is not encrypted by the application. Use a dedicated private directory. Do not commit it and do not expose the built-in API adapter to an untrusted network.

## Repository references

- [Technical Specification](docs/technical-specification.md)
- [Roadmap](docs/roadmap.md)
- [Stage 1C current status](docs/stage-1c-current-status.md)
- [Stage 1 dataset card](docs/stage-1-dataset-card.md)
- [Stage 1 coverage and bias register](docs/stage-1-coverage-and-bias-register.md)
- [Stage 1 exit evidence](docs/stage-1-exit-evidence.md)
- [ADR 0015 — Restoration pipeline validation, comparator, and OMR handoff](docs/adr/0015-restoration-pipeline-validation-comparator-handoff.md)
- [ADR 0016 — Stage 1C risk-tiered artifact custody](docs/adr/0016-stage-1c-risk-tiered-artifact-custody.md)
- [Stage 1C artifact custody profile policy](docs/stage-1c-storage-profile-policy.md)
- [Stage 1C artifact admission contract](docs/stage-1c-artifact-admission-contract.md)
- [Stage 1C high-assurance compatibility contract](docs/stage-1c-high-assurance-compatibility-contract.md)
- [Stage 1B closure evidence](docs/stage-1b-closure-evidence.md)
- [Stage 1B custody and operations contract](docs/stage-1b-custody-operations-contract.md)
- [Job API and teacher-review baseline](docs/job-api-and-teacher-review.md)
- [Immutable review evidence contract](docs/review-evidence-contract.md)
- [Durable local persistence baseline](docs/durable-local-persistence.md)
- [Local multi-worker concurrency and recovery](docs/multi-worker-concurrency-and-recovery.md)
- [Built-in HTTP and multipart security boundary](docs/http-transport-and-multipart-security.md)
- [OpenAPI contract](api/openapi.v1.json)
- [Dependency and license policy](docs/dependency-and-license-policy.md)
- [Fixture, permission, and usage governance](docs/fixture-governance.md)
- [Immutable input inspection contract](docs/input-inspection-contract.md)
- [OpenCV safe-restoration baseline](docs/safe-restoration-baseline.md)
- [Music-score and guitar-TAB safety validator](docs/music-safety-validator.md)
