# Deterministic OpenCV Safe-Restoration Baseline

**Status:** Milestone M2 candidate baseline  
**Engine:** `opencv_safe_baseline` version `0.2.0`  
**Configuration schema:** `schemas/restoration-config.schema.json`  
**Audit schema:** `schemas/restoration-candidate.schema.json`

## Purpose

The baseline creates a new reviewable image or single-page PDF candidate from JPEG or PNG source bytes. It never overwrites the source, invents notation, completes symbols, or approves its own result.

Digital PDFs return `digital_pdf_must_remain_vector`. Scanned or hybrid PDFs return `pdf_renderer_not_available` until a renderer is separately reviewed.

## Operations

The ordered pipeline is:

1. EXIF orientation correction,
2. confidence-gated deskew,
3. opt-in confidence-gated perspective rectification,
4. opt-in safe crop proposal,
5. illumination normalization,
6. background-only median denoising,
7. conservative CLAHE contrast,
8. optional review-required binarization.

Every operation can be disabled. The audit manifest records whether it was enabled and applied, all parameters, evidence, warnings, and before/after pixel digests.

## Notation protection

The default protected mask conservatively covers dark pixels and a small dilation around them. After geometric alignment, photometric operations may not make a protected pixel lighter than the aligned source. This protects staff lines, TAB lines, noteheads, stems, dots, accidentals, digits, and other small dark marks. A large protected fraction triggers review rather than aggressive cleanup.

This baseline does not claim semantic understanding. Issue #6 will add music/TAB-specific structural validation.

## Geometry safety

Deskew uses near-horizontal line evidence and applies only inside configured angle and confidence limits. Perspective and crop are disabled by default. A page quadrilateral must meet area and confidence limits before either can apply. A perspective warp already rectifies the page boundary, so a second crop is not silently applied.

## Outputs

- PNG: lossless master candidate.
- JPEG: deterministic compatibility derivative with recorded quality.
- PDF: deterministic single-page PDF containing the candidate image at configured DPI.

Source and candidate have distinct content-addressed SHA-256 identities. `teacherApproved` is always `false` at generation time.

## CLI

```bash
python tools/restore_image.py source.png candidate.png --audit candidate.audit.json
```

Optional configuration:

```bash
python tools/restore_image.py source.jpg candidate.pdf \
  --audit candidate.audit.json \
  --config restoration-config.json
```

The source path and candidate path must differ. Existing candidate or audit files are not overwritten.

## Explicit limitations

- no PDF rendering,
- no OMR or MusicXML interpretation,
- no semantic note/TAB recognition,
- no inpainting or symbol completion,
- no DocRes or ST Restore model,
- no automatic teacher approval,
- no real fixture bytes committed to Git.
