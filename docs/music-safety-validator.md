# Music-Score and Guitar-TAB Safety Validator

**Status:** Milestone M3 baseline  
**Validator:** `music_tab_safety_validator` version `0.3.0`  
**Risk schema:** `schemas/music-safety-report.schema.json` version `1.0.0`

## Purpose

The validator compares an immutable source image with a restoration candidate and can veto the candidate when structural evidence suggests that musical information may have changed. It does not perform OMR and does not claim semantic certainty about notes, rhythms, TAB digits, articulations, or text.

## Evidence layers

1. content-addressed source and candidate identity,
2. deterministic image registration with explicit confidence and byte/pixel ceilings,
3. separate staff-system and TAB-system geometry,
4. expected five-line staff and configurable six-line TAB counts,
5. horizontal-line continuity and break measurements,
6. local dark-pixel loss and invention outside a shared long-line mask using the source threshold,
7. connected-component loss, invention, and movement,
8. page-region findings for teacher review.

Low whole-image difference is never sufficient evidence of preservation. A candidate may look cleaner and still receive `reject`.

## Verdicts

- `pass`: configured structural checks completed without review or reject thresholds.
- `review_required`: uncertainty or moderate structural changes require teacher review.
- `reject`: severe line, symbol, component, or manifest-integrity changes veto the candidate.

`automaticApproval` is always `false`. A validator exception is a structured validation failure with a review-required fallback, never a pass.

## Staff and TAB separation

Staff and TAB systems are measured independently. Staff defaults to five expected horizontal lines per system; guitar TAB defaults to six and remains configurable. Unknown line groups and pages with no recognized staff/TAB system require review instead of being treated as a pass.

## Candidate comparison

`compare_candidate_reports` requires every report to reference the same immutable source, derives ranking from verdict and measured risk rather than trusting caller-supplied rank fields, excludes rejected candidates, then ranks `pass` before `review_required`, lower risk before higher risk, and finally content digest for deterministic ties. Candidate selection is not teacher approval.

## Teacher review and training separation

`record_teacher_review` records `approved`, `rejected`, or `reprocess`, reviewer identity, and notes. The record always preserves:

- `trainingLabelCreated: false`
- `trainingUseConsent: null`

A teacher decision therefore does not automatically become model-training data.

## Supported candidate inputs

- PNG
- JPEG/JPG
- deterministic single-image DCT PDF produced by the OpenCV baseline

Arbitrary or multi-page PDF candidates are rejected as unsupported. Source validation currently requires a decodable image; scanned-PDF page rendering remains a separate future adapter.

## CLI

```bash
python tools/validate_music_safety.py source.png candidate.png \
  --report candidate.safety.json \
  --candidate-manifest candidate.audit.json
```

Exit codes:

- `0`: pass
- `3`: review required
- `4`: reject
- `2`: validation/IO/configuration failure

## Limitations

- no OMR, MusicXML, semantic pitch/rhythm recognition, or OCR,
- translation-only registration after deterministic size normalization,
- configurable 50 MB byte and 80-million-pixel defaults,
- no automatic learning or training-label creation,
- real representative fixture bytes remain outside ordinary Git until separately approved.
