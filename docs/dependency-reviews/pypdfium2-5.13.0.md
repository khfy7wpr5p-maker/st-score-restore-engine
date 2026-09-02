# Dependency Review: PDFium Stage 3 PDF Renderer

- **Status:** Approved candidate for Stage 3 multi-page PDF core
- **Reviewed:** 2026-09-02
- **Package:** `pypdfium2==5.13.0`
- **Lock:** `requirements.lock`
- **Tracking:** Issue #90
- **Approving decision:** ADR 0017

## Purpose

`pypdfium2` provides the bounded PDFium renderer boundary required by Stage 3. It supplies deterministic PDF page enumeration, page geometry, page-object inspection and raster rendering primitives. The Stage 3 adapter renders only pages classified `raster_only`; vector/hybrid pages remain original/preserved in the first core slice.

## Canonical source and version

- Package: PyPI `pypdfium2`
- Version: `5.13.0`
- Release date: 2026-08-13
- Upstream: pypdfium2-team/pypdfium2
- Python requirement upstream: Python >=3.6
- Repository support remains narrower: Python 3.11 and 3.12 only

CI installs the manylinux binary wheel with `--only-binary=:all:` and dependency resolution disabled, then verifies installed version `5.13.0`.

## Licenses and redistribution

The pypdfium2 project identifies its own code under Apache-2.0 / BSD-3-Clause terms. PDFium uses a BSD-style license. The binary distribution also includes PDFium dependency license obligations.

Redistribution must preserve PDFium and bundled third-party notices shipped with the installed wheel. This review record is a repository inventory/decision record, not a substitute for the upstream license texts.

## Bundled/native components

The Linux wheel bundles a native PDFium shared library. PDFium itself includes or depends on multiple third-party components whose license set may evolve with the bundled PDFium build. The exact notices shipped with the installed `5.13.0` wheel remain authoritative for redistribution.

No model weights, training data, telemetry SDK or network service is introduced.

## Security considerations

PDF parsing/rendering processes untrusted complex input through native code. Mitigations:

- existing immutable input inspection runs first;
- encrypted inputs remain rejected;
- PDFium page count is bounded;
- page-object traversal depth is bounded;
- raster dimensions and pixels are bounded before rendering;
- total rendered pixels are bounded;
- only raster-only pages may render in the first slice;
- unknown/hybrid/vector content does not broaden rendering authority;
- original fallback remains available;
- synthetic tests exercise the ordinary-Git core.

## External data transfer

None. Rendering is local/in-process and does not send document bytes to a network service.

## Platform decision

Stage 3 CI validates the pinned wheel on Ubuntu x86_64 with Python 3.11 and 3.12. Other production platforms require their own reviewed binary/platform evidence before deployment.

## Removal/fallback plan

Removing `src/st_score_restore/pdf_pipeline.py`, its validator/tests, ADR 0017 and the `pypdfium2` runtime pin restores the Stage 2 fail-closed scanned/hybrid-PDF boundary. Existing vector-preservation behavior and immutable source inspection remain available. There is no unreviewed alternate PDF renderer fallback.
