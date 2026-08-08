# ST Score Restore Engine

AI-assisted, safety-first restoration and validation engine for music scores and guitar TAB supplied as PDF, JPG/JPEG, PNG, or phone-captured sheet-music photos.

## Approved processing flow

```text
PDF / JPG / JPEG / PNG / Phone photo
      ↓
Document and quality analysis
      ↓
┌────────────────────────────────┐
│ 1. OpenCV safe restoration     │
│ 2. DocRes AI adapter           │
│ 3. ST Restore engine           │
└────────────────────────────────┘
      ↓
Result comparator
      ↓
Music-score and TAB safety validator
      ↓
Immutable review evidence
      ↓
Teacher approval
      ↓
Enhanced PDF and/or image + audit report
```

## Repository boundary

This repository remains an independent service. SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway, and ScoreMosaic/Scremosaik will integrate through a versioned API; their repositories are not merged into this engine.

## Current status

Architecture, governance, fixture permissions, immutable input inspection, deterministic OpenCV candidate generation, conservative music-score/TAB validation, a non-production `/api/v1` job/teacher-review workflow, optional durable local storage, attempt-bound worker fencing with in-flight recovery, a strict local HTTP/multipart boundary, and immutable reviewer evidence bundles are implemented.

Stage 1 dataset governance is being delivered through explicit gated substages. Stage 1A metadata governance is complete. Stage 1B provider-neutral custody/operations implementation was merged through PR #41, and its ADR/technical-contract acceptance status was synchronized through PR #42. Issue #36 remains the Stage 1B closure record until every stated exit-evidence item, including the independent exact-head security-audit record, is satisfied. Stage 1C artifact onboarding has not started and is not authorized by those merges.

Production deployment, encrypted cloud object storage, an external queue, production identity, arbitrary multi-page PDF processing, a complete browser review UI, automatic teacher approval, DocRes, ST Restore, OMR, and MusicXML integration remain disabled or deferred.

## Binding development order

The project uses a data-first, measurement-first sequence. Later stages may not be pulled forward merely because implementation appears possible.

```text
Roadmap update
      ↓
Real and explicitly authorized test dataset
      ↓
Complete quality-analysis system
      ↓
Multi-page PDF pipeline
      ↓
Safety calibration with real data
      ↓
Accessible teacher review interface
      ↓
Identity, network and production infrastructure
      ↓
Preview release
      ↓
DocRes optional candidate
      ↓
Multi-engine comparator
      ↓
ST Restore Selector
      ↓
ST Restore image model
      ↓
Music-application integrations
```

Each stage requires explicit approval before work begins and separate approval before merge. The detailed entry and exit gates are defined in [the development roadmap](docs/roadmap.md).

**Current Stage 1 gate:** Stage 1A is complete; Stage 1B implementation and acceptance-status changes are merged, while Issue #36 closure evidence is still being finalized. Stage 1C requires formal Stage 1B closure plus a separate explicit start approval.

## Development baseline

- Primary runtime: Python 3.12
- Compatibility validation: Python 3.11 and 3.12
- Runtime lock: `requirements.lock`
- OpenCV backend: `opencv-python-headless==4.13.0.92`
- NumPy runtime: `numpy==2.3.5`
- Job API: `/api/v1`, version `0.5.0`
- Review contract: reviewer-only immutable evidence bundles and stale-screen binding
- HTTP baseline: strict standard-library server with bounded headers/body/timeouts; still not approved for untrusted networks
- HTTP connection model: one request per connection; pipelining, chunked requests, upgrades, and `Expect` are rejected
- Storage baseline: in-memory by default; opt-in local SQLite metadata and content-addressed blobs
- Local worker safety: attempt-bound lease tokens, transaction fencing, and expired in-flight recovery
- Fixture artifact bytes: not included; current catalog is metadata-only
- Source identity: deterministic SHA-256 artifact manifest
- Candidate identity: separate SHA-256 digest and audit manifest
- Safety report: staff and TAB geometry, line continuity, local symbol and component risk
- Review evidence: source-space overlays, deterministic grayscale before/after crops, transform provenance
- Audit: append-only hash-linked events, verified when durable state is loaded
- Digital PDFs: preserved as vector; never implicitly rasterized
- Teacher approval: separate from candidate generation and training consent

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

See:

- [Technical Specification](docs/technical-specification.md)
- [Roadmap](docs/roadmap.md)
- [Stage 1B closure evidence](docs/stage-1b-closure-evidence.md)
- [Stage 1B custody and operations contract](docs/stage-1b-custody-operations-contract.md)
- [Stage 1B decision hardening record](docs/stage-1b-decision-hardening-record.md)
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
- [ADR 0007](docs/adr/0007-in-process-job-api-and-review-workflow.md)
- [ADR 0008](docs/adr/0008-durable-local-persistence.md)
- [ADR 0009](docs/adr/0009-attempt-bound-worker-fencing-and-recovery.md)
- [ADR 0010](docs/adr/0010-strict-local-http-and-multipart-boundary.md)
- [ADR 0011](docs/adr/0011-immutable-review-evidence-and-stale-screen-binding.md)
- [ADR 0014](docs/adr/0014-stage-1b-custody-operations-boundary.md)
