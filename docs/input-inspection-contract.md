# Immutable Input Inspection Contract

**Status:** Milestone M1 baseline  
**Artifact schema:** `schemas/artifact-manifest.schema.json` version `1.0.0`  
**Analysis schema:** `schemas/input-analysis.schema.json` version `1.0.0`  
**Inspector:** `st_score_restore.input_inspection` version `0.1.0`

## Purpose

Input inspection is the first read-only boundary of ST Score Restore Engine. It identifies a PDF, JPEG, or PNG, calculates a stable SHA-256 digest, records deterministic structural metadata, and reports uncertainty before any restoration engine can run.

Inspection never enhances, rewrites, normalizes, strips metadata from, or rasterizes the source.

## Supported inputs

The baseline accepts content detected by file signature:

- PDF (`application/pdf`)
- JPEG/JPG (`image/jpeg`)
- PNG (`image/png`)

The filename extension is advisory. A mismatch creates a warning; the content signature remains authoritative.

## Immutable artifact manifest

Every accepted input produces a source artifact manifest containing:

- a content-derived `artifactId`,
- immutable source role,
- source filename without a directory path,
- byte size,
- SHA-256 digest,
- detected media type and kind,
- `derivedFrom: null`.

No timestamp is included, so identical bytes and the same inspector version produce identical structural output. The original byte sequence remains unchanged.

When a path is inspected, the inspector rejects symbolic links and compares file identity, size, and modification time before and after reading. A detected change fails with `source_changed_during_read`.

## PDF inspection

The standard-library baseline validates the PDF header, end marker, and encryption flag, then records:

- PDF version,
- page-object marker count when visible,
- page dimensions from visible `MediaBox` entries,
- text/font evidence,
- image XObject evidence,
- compressed object-stream evidence,
- classification as `digital`, `scanned`, `hybrid`, or `unknown`.

Classification is deliberately conservative. Compressed PDF structures may hide evidence. Unknown evidence produces a review-required warning rather than a false claim.

A PDF classified as `digital` receives `preserve_vector_pdf`. It must not be rasterized merely to enter an image-processing pipeline.

## JPEG and PNG inspection

The baseline reads structural metadata without decoding pixels.

JPEG inspection validates segment boundaries and frame dimensions, reads JFIF density where available, and reads EXIF orientation.

PNG inspection validates its signature, chunk boundaries, chunk CRC values, IHDR/IEND presence, dimensions, pHYs density, and eXIf orientation where available.

EXIF orientation affects only reported display dimensions. `appliedToSource` is always `false`.

## Quality findings

Every analysis includes the following finding types:

- perspective
- crop
- glare
- shadow
- blur
- noise
- compression
- low resolution

The standard-library baseline does not decode pixels. It therefore marks glare, shadow, blur, noise, and perspective as `not_assessed`, never as safe. Low resolution may be marked `probable` from dimensions or DPI. Extreme aspect ratio may create a low-confidence crop warning.

A later pixel-analysis adapter may add region-level evidence. Until then, `region` remains `null`, and lack of assessment must not be interpreted as absence of risk.

## Safe rejection codes

Stable error codes include:

- `empty_input`
- `invalid_input_type`
- `input_unreadable`
- `input_not_regular_file`
- `symlink_input_not_allowed`
- `source_changed_during_read`
- `oversized_input`
- `unsupported_media_type`
- `malformed_pdf`
- `encrypted_pdf`
- `malformed_jpeg`
- `malformed_png`

Rejection never creates an enhanced output. Unsupported bytes may include their SHA-256 and leading signature bytes in error details for diagnosis.

## Determinism

For identical bytes, source name, byte limit, and inspector version:

- SHA-256 is identical,
- artifact ID is identical,
- inspection ID is identical,
- structural metadata is identical,
- warning ordering is identical,
- no current time, random value, or filesystem path is embedded.

## Command line

```bash
python tools/inspect_input.py path/to/score.pdf
```

The command prints JSON to standard output. It does not write an output file. A safe rejection exits with status `2` and prints the structured error object.

## Explicit limitations

This milestone does not:

- render or rasterize PDF pages,
- decode JPEG or PNG pixels,
- correct EXIF orientation in the source,
- detect music notation,
- enhance an image,
- remove metadata,
- call OpenCV, DocRes, OMR, or an AI model,
- claim pixel-level quality certainty.

These limitations preserve the separation between source inspection and later restoration.
