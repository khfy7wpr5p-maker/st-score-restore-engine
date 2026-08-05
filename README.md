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
Teacher approval
      ↓
Enhanced PDF and/or image + audit report
```

## Repository boundary

This repository remains an independent service. It accepts PDF, JPG/JPEG, PNG, and phone-captured score/TAB photos. SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway, and ScoreMosaic/Scremosaik will integrate through a versioned API; their repositories are not merged into this engine.

## Initial documents

- [Technical Specification](docs/technical-specification.md)
- [Roadmap](docs/roadmap.md)

## Current status

Architecture and Milestone M0 repository foundation are approved. The Milestone M1 fixture, permission, privacy, retention, and permitted-use contract is under review. No production restoration implementation has been started.

## Development baseline

- Primary runtime: Python 3.12
- Compatibility validation: Python 3.11 and 3.12
- Package layout: `src/st_score_restore`
- Third-party runtime dependencies: none
- Production restoration behavior: not implemented
- Fixture artifact bytes: not included; current catalog is metadata-only

Validate the repository foundation and fixture contract with:

```bash
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

See:

- [Development environment](docs/development-environment.md)
- [Dependency and license policy](docs/dependency-and-license-policy.md)
- [Fixture, permission, and usage governance](docs/fixture-governance.md)
- [Fixture catalog](fixtures/catalog.v1.json)
- [Fixture manifest schema](schemas/fixture-manifest.schema.json)
- [ADR 0002: Python runtime and repository layout](docs/adr/0002-python-runtime-and-repository-layout.md)
- [ADR 0003: Fixture permission and usage governance](docs/adr/0003-fixture-consent-and-usage-governance.md)
