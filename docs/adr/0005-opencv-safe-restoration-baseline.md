# ADR 0005: Deterministic OpenCV Safe-Restoration Baseline

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** Project owner and ST Score Restore maintainers

## Context

The engine needs a first restoration candidate that can improve scanned or photographed score images without inventing notes, TAB digits, rhythm marks, or missing content. Each transformation must be reproducible, independently disableable, and auditable.

## Decision

1. The first restoration backend is `opencv-python-headless==4.13.0.92` with `numpy==2.3.5`.
2. The backend is deterministic and non-generative; no inpainting or symbol completion is allowed.
3. Source bytes remain immutable and receive a separate digest from every candidate.
4. Digital PDFs are not rasterized. Scanned/hybrid PDFs require a later approved renderer adapter.
5. EXIF orientation, deskew, perspective, crop, illumination, denoise, contrast, and binarization are separate operations.
6. Perspective and crop are opt-in and confidence-gated. Ambiguity produces review reasons rather than silent geometry changes.
7. Dark notation pixels form a conservative protected mask. Photometric operations may not make protected pixels lighter than the aligned source.
8. Binarization is off by default and always requires review.
9. PNG is the lossless master candidate; JPEG and deterministic single-page PDF are compatibility derivatives.
10. Every operation records configuration, evidence, warnings, and before/after pixel digests.
11. Candidate generation never equals teacher approval.
12. Runtime dependencies are exactly pinned in `requirements.lock`; CI installs binary wheels only.

## Consequences

The project gains a reproducible image candidate and audit record while keeping geometry uncertainty and notation safety visible. The baseline is intentionally conservative and may preserve some dark noise. It does not process PDF pages until a renderer is separately approved.

## Safety and privacy impact

No document is uploaded, retained for training, or modified in place. Candidate rejection returns the exact original bytes. No model or network service is used.

## Alternatives considered

OpenCV 5.x was deferred to avoid a new-major-version migration during the first trusted baseline. Generative restoration, automatic inpainting, unconditional cropping, and implicit PDF rasterization were rejected.

## Reversal or migration path

The OpenCV adapter can be disabled or replaced behind the same candidate/audit contract. Dependency versions, masks, thresholds, or output contracts require review, tests, and an ADR update when materially changed.
