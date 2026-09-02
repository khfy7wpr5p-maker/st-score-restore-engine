# ADR 0017: Stage 3 PDFium Multi-page PDF Pipeline

- **Status:** Proposed in Stage 3 core branch; becomes accepted only after merge and post-merge main CI
- **Date:** 2026-09-02
- **Decision ID:** `adr-0017-stage3-pdfium-multipage-pipeline-v1`
- **Roadmap stage:** Stage 3 — Multi-page PDF pipeline
- **Tracking issue:** #90
- **Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`
- **Entry verification:** Repository validation Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS

## Context

Stage 2 intentionally failed closed for scanned/hybrid PDF pixel analysis with `pdf_renderer_not_available`. Stage 2 final exit is now production-effective, so Stage 3 owns the explicit renderer boundary.

The renderer must not erase the source PDF's identity or silently flatten vector notation. Page order and page provenance must stay stable. Raster rendering is a derivative operation, not a source replacement.

## Decision

Use **PDFium through `pypdfium2==5.13.0`** for the first Stage 3 production candidate.

Reasons:

- prebuilt wheel-based runtime integration fits the existing Python 3.11/3.12 CI model;
- the Python binding and bundled PDFium distribution use permissive Apache-2.0/BSD-style licensing notices suitable for this repository's dependency model;
- PDFium provides deterministic page enumeration, page geometry, object inspection and raster rendering primitives;
- page-object inspection allows a stricter page-level vector/raster policy instead of document-wide blind rasterization.

Dependency notices and upstream license obligations remain binding. This ADR does not grant any rights to input score content.

## Page policy

Every PDF first passes the existing immutable input inspector and retains exact source SHA-256 identity. PDFium then provides the authoritative Stage 3 page count and page order for rendering decisions.

Page objects are classified conservatively:

- **`raster_only`** — image objects with no detected vector/text/path/shading evidence. Rendering is allowed.
- **`vector_only`** — text/path/shading evidence with no image evidence. Preserve the PDF page; do not rasterize it.
- **`hybrid`** — vector and image evidence coexist. Preserve the original page and require review in the first core slice; do not silently rasterize it.
- **`unknown_or_empty`** — no supported evidence. Use original fallback and require review.

Form objects are traversed to a bounded depth. Unknown content does not authorize rasterization.

## Raster derivative contract

Only a `raster_only` page may produce a Stage 3 PNG derivative. Each derivative records:

- exact parent source SHA-256;
- source page index;
- derivative SHA-256;
- output media type;
- render DPI and pixel dimensions;
- subsequent deterministic Stage 2 quality-analysis report.

The source PDF bytes are never modified or replaced. Derivative bytes are kept separate from the public-safe manifest.

## Resource bounds

Initial engineering defaults are intentionally uncalibrated:

- render DPI: 200;
- maximum pages: 64;
- maximum pixels per rendered page: 40,000,000;
- maximum aggregate rendered pixels: 160,000,000;
- maximum render dimension: 8,000 pixels;
- maximum page-object traversal depth: 15.

A document page-count violation rejects the pipeline. Per-page render limits fail closed to original fallback/review rather than forcing a dangerous render.

Held-out data did not choose or tune these values. Stage 4 owns real-data safety calibration.

## Safety invariants

1. Exact source SHA-256 remains the identity boundary.
2. Page indices are zero-based, ordered and stable.
3. Vector pages are not silently rasterized.
4. Hybrid pages are not rasterized by this first core slice.
5. Raster derivatives never replace source bytes.
6. Original fallback remains available for every page.
7. Encrypted, malformed or unsupported inputs remain fail closed through existing inspection and Stage 3 errors.
8. No OMR, note inference, symbol completion or musical-correctness decision occurs in this pipeline.
9. No training, calibration or publication permission is inferred.
10. Real corpus artifact bytes remain outside ordinary Git.

## Validation

`tools/validate_stage3_pdf_pipeline.py` and `tests/test_pdf_pipeline.py` use synthetic PDFs only. They require deterministic page ordering, exact source/derivative binding, raster-only rendering, vector preservation, original fallback and bounded failure behavior.

CI must run the Stage 3 validator on Python 3.11 and 3.12 before the branch can become merge-eligible.

## Out of scope

This decision does not implement Stage 4 calibration, OMR, ScoreMosaic changes, DocRes, multi-engine comparison, selector logic, learned restoration, production networking or teacher-review UI.
