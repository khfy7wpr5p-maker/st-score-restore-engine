# ADR 0006: Conservative Music-Score and Guitar-TAB Safety Validator

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision owners:** Project owner and ST Score Restore maintainers

## Context

A restoration candidate can be visually attractive while deleting, merging, shifting, or inventing small musical marks. Pixel similarity alone cannot establish musical preservation. The first validator must veto risky candidates without claiming semantic certainty it does not possess.

## Decision

1. The validator is deterministic and versioned separately from the restoration engine.
2. It compares immutable source and candidate bytes and verifies optional candidate-manifest digests.
3. Registration uncertainty can never result in silent approval.
4. Staff and TAB systems are measured separately; defaults are five staff lines and six TAB lines.
5. Long-line continuity, symbol dark-pixel loss/invention, connected-component loss/invention, and component movement are independent evidence layers.
6. Findings include page regions and `semanticCertainty: not_claimed`.
7. Verdicts are `pass`, `review_required`, or `reject`; `automaticApproval` is always false.
8. Rejected candidates are excluded from comparison. A selected candidate is still not teacher-approved.
9. The unmodified source remains the final fallback.
10. Teacher review records never automatically create training labels or training consent.
11. No new runtime dependency is introduced; the approved OpenCV and NumPy lock remains unchanged.

## Consequences

The project gains an auditable veto boundary and deterministic candidate ranking. The baseline detects structural changes but cannot identify note names, rhythmic meaning, or TAB semantics. Conservative thresholds may send clean candidates for teacher review.

## Safety and privacy impact

The validator operates locally on supplied bytes, makes no network call, stores no training data, and never replaces the source. Teacher decisions and training permission remain distinct records.

## Reversal or migration path

Future OMR or learned validators may add evidence behind a new version. They must not remove the deterministic baseline, weaken fallback behavior, or convert uncertainty into approval. Contract-breaking report changes require a new schema version and migration notes.
