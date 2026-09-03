# Stage 4 Metric Applicability Contract

Stage 4 real development calibration must preserve the actual Stage 3 page policy instead of inventing numeric measurements for media where the canonical metric is not applicable.

## Exact current development scope

- Beethoven `dataset.item.imslp799143-beethoven-op48-no3.v1`: Stage 3 classified all four pages as `raster_only` and rendered them as PNG derivatives. The canonical Stage 2 metrics for skew, blur, glare, shadow, uneven lighting and noise are measurable on those PNG derivatives. The Stage 2 compression metric is JPEG-only, so compression is `not_applicable` for all four Beethoven pages.
- Barley `dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1`: Stage 3 classified both pages as `vector_only` and preserved them without rasterization. Raster quality metrics are therefore `not_applicable` for all fourteen Barley observation slots.

## Private batch rule

The private batch still carries exactly 42 observation identities so that every accepted human label remains accounted for. Each row has `measurementStatus`:

- `measured`: `rawValue` is a finite canonical metric value and `notApplicableReason` is `null`.
- `not_applicable`: `rawValue` is `null` and `notApplicableReason` is a contract-defined fail-closed reason.

For the currently authorized Beethoven + Barley scope the expected applicability is exactly:

- 24 measured rows: four Beethoven pages × six raster-applicable metrics;
- 18 not-applicable rows: four Beethoven compression rows + fourteen Barley vector-only rows.

No zero, placeholder or inferred numeric value may stand in for `not_applicable`.

## Candidate derivation

Only `measured` rows may materialize into `CalibrationObservation` objects. Candidate derivation remains development-only and abstain-first. Because the current measurable rows come from only one source family, the existing two-source-family requirement forces abstention rather than inventing thresholds.

## Non-claims

This contract does not accept real development calibration evidence, authorize held-out evaluation, define metric acceptance targets, modify production thresholds/resource limits, train a model, authorize publication, grant Stage 4 PASS, or open Stage 5.
