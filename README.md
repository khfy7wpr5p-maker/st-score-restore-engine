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

Architecture approved. Milestone M0 repository foundation is under review. No production restoration implementation has been started.

## Development baseline

- Primary runtime: Python 3.12
- Compatibility validation: Python 3.11 and 3.12
- Package layout: `src/st_score_restore`
- Third-party runtime dependencies: none in Milestone M0
- Production restoration behavior: not implemented

Validate the repository foundation with:

```bash
python tools/validate_repository.py
python -m compileall -q src tools
```

See:

- [Development environment](docs/development-environment.md)
- [Dependency and license policy](docs/dependency-and-license-policy.md)
- [ADR 0002: Python runtime and repository layout](docs/adr/0002-python-runtime-and-repository-layout.md)
