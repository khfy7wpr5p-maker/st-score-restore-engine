# Stage 11 V2d Clef and Staff-Line Spatial Review Guide

This development-only work package collects the missing independent spatial truth
needed to evaluate clef boxes and staff-line topology. It does not evaluate a
detector, authorize a Colab run, or establish semantic preservation.

## Independence boundary

Annotate only the exact source page identified by the work package. Do not show the
reviewer Restore output, Oemer output, candidate boxes, masks, or other automated
suggestions. Those outputs are measurement candidates and may never supply teacher
ground truth.

The committed work package must stay null-filled. Store completed human annotations
in a separate artifact with reviewer identity/date and hashes for every reviewed PNG
and staff-line mask.

## Source-page preparation

Use the five exact source assets and page numbers in
`evidence/stage11/v2d/v2d-spatial-teacher-review-work-package.v1.json`. Verify each
source byte size and SHA-256 first. Export PDF pages once at 72 DPI with `pdftoppm`;
copy the source PNG without re-encoding. Do not crop, deskew, resize, enhance, or
rotate. Write the specified `source-pages/<pageId>.png` path and record its SHA-256,
byte size, width, height, and renderer version in the separate completion artifact.

## Clef boxes

Draw one tight axis-aligned box around every visible clef, including clef changes
inside a system. Coordinates are integer source-page pixels with a top-left origin;
maximum coordinates are exclusive. Record the clef type, whether it is truncated by
the page boundary, and whether its identity is ambiguous. An empty box list means the
teacher explicitly confirmed that no clef is visible; it is not a skipped response.

## Staff-line masks and topology

Create a single-channel PNG at exactly the source-page dimensions. Use value `255`
for visible staff-line ink and `0` everywhere else. Include interrupted staff-line
fragments, but exclude stems, barlines, beams, text, and page borders.

Group the labeled lines into systems, order lines top-to-bottom, and identify each
system as `standard`, `tablature`, `mixed`, or `unknown`. Mark incomplete or ambiguous
systems explicitly. The mask and topology record must agree on line identifiers.

## Completion boundary

Human completion is not detector qualification. After independent review, a separate
ingestion change must validate image/mask hashes, coordinate bounds, topology, and
reviewer provenance. Only then may source detector precision/recall be measured.
Source-to-restored preservation measurement remains a later, separate step.
