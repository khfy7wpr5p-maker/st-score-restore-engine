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

Architecture approved. Documentation baseline prepared. No production implementation has been started.
