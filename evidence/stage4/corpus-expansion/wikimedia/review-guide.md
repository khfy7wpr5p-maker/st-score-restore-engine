# Human Review Guide — Wikimedia Guitar Technical Exercise No.1

Review the single source page without consulting automated metric values or model predictions.

Record exactly one label for each finding type:

1. `skew`
2. `blur`
3. `glare`
4. `shadow`
5. `uneven_lighting`
6. `noise`
7. `compression`

Allowed labels:

- `clear`
- `possible`
- `probable`
- `not_assessed`

Reference truth must come from `human_expert_review`. Automated predictions, private observation metrics, candidate thresholds, and held-out evidence must not be shown during labeling. Completion evidence must use an opaque non-PII reviewer reference, provenance reference, and ISO date. The completed review does not by itself accept a reference bundle or authorize calibration execution.
