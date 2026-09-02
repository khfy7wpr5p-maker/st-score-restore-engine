# Stage 3 Current Status — Multi-page PDF Pipeline

**Status:** ACTIVE — CORE SLICE  
**As of:** 2026-09-02  
**Tracking:** Issue #90  
**Stage 3 entry main:** `87198a5a917ab6b3efc277762016a5f5b0dd3aab`  
**Entry CI:** Run #228 (`33609061197`) — Python 3.11 / 3.12 SUCCESS  
**Active branch:** `stage3-multipage-pdf-core`  
**Stage 4:** NOT STARTED / BLOCKED pending explicit Stage 3 exit PASS

## Entry state

Stage 2 final exit is production-effective. PR #89 merged the separate Stage 2 acceptance into main `87198a5a917ab6b3efc277762016a5f5b0dd3aab`; post-merge Repository validation Run #228 succeeded on Python 3.11 and 3.12, including the Stage 2 final-exit validator, full tests and compile.

Stage 3 therefore started in a new focused branch. Stage 2 historical evidence remains immutable.

## First core slice

The first core slice introduces `src/st_score_restore/pdf_pipeline.py` and selects `pypdfium2==5.13.0` / PDFium as the renderer boundary.

The pipeline:

- preserves the exact source PDF SHA-256 and byte identity;
- uses PDFium page enumeration for Stage 3 page count/order;
- inspects page objects before any rendering decision;
- renders only pages classified `raster_only`;
- preserves `vector_only` pages without rasterization;
- preserves `hybrid` pages and requires review in the first slice;
- sends rendered PNG derivatives through the existing deterministic Stage 2 quality analyzer;
- records derivative SHA-256, source SHA-256 and page index provenance;
- keeps original fallback available for every page;
- applies bounded page-count, dimension and pixel limits;
- uses synthetic PDFs only in Git tests/validation.

## Initial engineering bounds

- render DPI: 200;
- maximum pages: 64;
- maximum rendered page pixels: 40,000,000;
- maximum total rendered pixels: 160,000,000;
- maximum render dimension: 8,000;
- maximum object traversal depth: 15.

These are uncalibrated engineering defaults. Held-out data was not used to select them. Stage 4 owns real-data calibration.

## Vector-content policy

Vector content is not silently rasterized.

- `raster_only` → render to PNG derivative;
- `vector_only` → preserve original PDF page;
- `hybrid` → preserve original page + review required;
- `unknown_or_empty` → original fallback + review required.

This page-level policy replaces the Stage 2 document-level renderer deferral without rewriting Stage 2 evidence.

## Safety/non-claims

Stage 3 does not perform OMR, symbol completion or musical inference. It does not establish musical correctness, OMR improvement, restoration effectiveness, representativeness or absence of bias. Training, calibration and publication remain unauthorized.

Real accepted-corpus artifact bytes remain outside ordinary Git. Detailed restricted evidence rules, including C17D `external_export=false`, remain unchanged.

## Core-slice validation

CI must verify:

1. exact runtime dependency pin `pypdfium2==5.13.0`;
2. deterministic synthetic multi-page processing;
3. exact source and derivative digest provenance;
4. stable page order;
5. raster-only rendering;
6. no silent vector rasterization;
7. original fallback under render bounds;
8. Stage 1/Stage 2 historical evidence immutability;
9. Python 3.11 and 3.12 full repository validation.

Stage 3 is active, but **Stage 3 exit is not yet PASS**. Stage 4 remains blocked until a separate Stage 3 exit decision is accepted.
