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

The target path above is architecture-locked by [ADR 0015](docs/adr/0015-restoration-pipeline-validation-comparator-handoff.md). A restoration derivative must be safety-validated before comparator eligibility; a rejected derivative cannot win; and the immutable original always remains selectable. The future ST Restore Selector may decide which optional engines or profiles to invoke, but it may not bypass or reorder the mandatory validation → comparator → original-aware selection sequence.

This diagram records the target architecture. The current OpenCV-only runtime now implements the validator-before-comparator ordering and records the immutable original as a selectable comparator baseline. It does not activate DocRes, ST Image AI, the Roadmap Stage 9 multi-engine comparator, the Stage 10 selector, ScoreMosaic runtime dispatch, model training, or any later roadmap stage.

## Repository boundary

This repository remains an independent service. SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway, and ScoreMosaic/Scremosaik will integrate through a versioned API; their repositories are not merged into this engine.

ST Score Restore produces visual `restoration_variant` artifacts. It is not an OMR engine and its variants must not be confused with ScoreMosaic OMR candidates. A selected visual source variant must cross ScoreMosaic's own Safe Intake boundary before OMR processing.

## Current status

Architecture, governance, fixture permissions, immutable input inspection, deterministic OpenCV candidate generation, conservative music-score/TAB validation, a non-production `/api/v1` job/teacher-review workflow, optional durable local storage, attempt-bound worker fencing with in-flight recovery, a strict local HTTP/multipart boundary, and immutable reviewer evidence bundles are implemented.

The target multi-engine architecture is explicitly locked as: restoration engines → per-variant safety validation → original-aware comparator → selected source variant → downstream ScoreMosaic Safe Intake/OMR. The current runtime remains OpenCV-only, but its processing order is aligned with ADR 0015: the OpenCV restoration variant is safety-validated before comparator evidence is emitted, rejected variants are excluded from comparator eligibility, and the immutable original remains selectable. This bounded current behavior is not the Roadmap Stage 9 multi-engine comparator.

Stage 1 dataset governance is being delivered through explicit gated substages. Stage 1A metadata governance is complete. Stage 1B provider-neutral high-assurance custody/operations implementation and hardening are complete: Issue #36 closed as `completed` after the final PR #44 exact-head audit evidence, merge, and successful post-merge `main` CI. Stage 1C is active under Issue #47.

The Stage 1C storage architecture is now risk-tiered by [ADR 0016](docs/adr/0016-stage-1c-risk-tiered-artifact-custody.md). The previous G4 rule that forced every real artifact into one encrypted offline vault is superseded once ADR 0016 is accepted. Exact-artifact rights, privacy, purpose, retention and dataset-review evidence are evaluated first. Verified low-risk `open_corpus` artifacts may use a `managed_standard` profile; lawfully usable but restricted artifacts may use `managed_restricted` when their terms permit it; private/personal/student/consent-restricted artifacts remain in `high_assurance_vault`; unresolved or rejected governance is `blocked` and cannot be onboarded. The public-domain status of a musical composition alone is not sufficient: the exact edition/engraving/scan/file must have suitable rights evidence.

The merged C4 vault-verification schema remains the high-assurance evidence mechanism. It is no longer intended as a universal gate for every real document. However, ADR 0016 changes architecture before implementation: the current Stage 1A/1C machine-readable schemas still represent the legacy storage values. Therefore no artifact may yet become `external_available` under the new storage-profile names until a follow-up versioned schema/validator PR is merged and verified. No artifact bytes are added by the architecture change.

Production deployment, encrypted cloud object storage, an external queue, production identity, arbitrary multi-page PDF processing, a complete browser review UI, automatic teacher approval, DocRes, ST Image AI, OMR, and MusicXML integration remain disabled or deferred.

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

**Current Stage 1 gate:** Stage 1A is complete, Stage 1B is formally closed, and Stage 1C is active under Issue #47. ADR 0016 replaces the universal offline-vault storage rule with artifact-specific custody tiers, but the machine-readable profile implementation is not yet merged. Metadata-only Stage 1C architecture/contract work may proceed; artifact onboarding remains fail-closed until the relevant storage-profile schema and validator update is accepted and each item independently satisfies rights, privacy, dataset-review, retention and purpose authorization. Stage 2 remains blocked until the complete Stage 1 corpus exit gate is accepted.

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
- [ADR 0015 — Restoration pipeline validation, comparator, and OMR handoff](docs/adr/0015-restoration-pipeline-validation-comparator-handoff.md)
- [ADR 0016 — Stage 1C risk-tiered artifact custody](docs/adr/0016-stage-1c-risk-tiered-artifact-custody.md)
- [Stage 1C artifact custody profile policy](docs/stage-1c-storage-profile-policy.md)
- [Stage 1C high-assurance vault verification evidence](docs/stage-1c-vault-verification-evidence-contract.md)
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