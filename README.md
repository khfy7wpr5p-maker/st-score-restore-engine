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

This repository remains an independent service. SesliTab Guitar Reader, MusicXML-to-Guitar TAB Engine, Cloud OMR Gateway, and ScoreMosaic/Scremosaik will integrate through a versioned API; their repositories are not merged into this engine.

## Current status

Architecture, governance, fixture permissions, immutable input inspection, and the deterministic OpenCV candidate baseline are implemented. The OpenCV result is only a reviewable candidate; production restoration, teacher approval, DocRes, ST Restore, OMR, and MusicXML integration remain disabled.

## Development baseline

- Primary runtime: Python 3.12
- Compatibility validation: Python 3.11 and 3.12
- Runtime lock: `requirements.lock`
- OpenCV backend: `opencv-python-headless==4.13.0.92`
- NumPy runtime: `numpy==2.3.5`
- Fixture artifact bytes: not included; current catalog is metadata-only
- Source identity: deterministic SHA-256 artifact manifest
- Candidate identity: separate SHA-256 digest and audit manifest
- Digital PDFs: preserved as vector; never implicitly rasterized
- Teacher approval: always separate from candidate generation

Validate the repository contracts with:

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

Inspect a source without modifying it:

```bash
python tools/inspect_input.py path/to/score.pdf
```

Create a separate candidate and audit report:

```bash
python tools/restore_image.py source.png candidate.png --audit candidate.audit.json
```

See:

- [Technical Specification](docs/technical-specification.md)
- [Roadmap](docs/roadmap.md)
- [Dependency and license policy](docs/dependency-and-license-policy.md)
- [Fixture, permission, and usage governance](docs/fixture-governance.md)
- [Immutable input inspection contract](docs/input-inspection-contract.md)
- [OpenCV safe-restoration baseline](docs/safe-restoration-baseline.md)
- [Dependency review](docs/dependency-reviews/opencv-python-headless-4.13.0.92.md)
- [Restoration configuration schema](schemas/restoration-config.schema.json)
- [Restoration candidate schema](schemas/restoration-candidate.schema.json)
- [ADR 0005](docs/adr/0005-opencv-safe-restoration-baseline.md)
