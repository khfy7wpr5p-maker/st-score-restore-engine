# ADR 0035: Stage 11 V2d canonical notehead class evidence

Status: Accepted for the notehead class only
Date: 2026-09-09

## Decision

Accept the completed hash-bound canonical CPU Restore result as positive
semantic-preservation evidence for the **notehead class only**.

The source result is Drive file
`15ZspsDK3jAAtfqmmebBebopEpo3a1Xpn`, 23,228 bytes, SHA-256
`ab6197bcf0dd58407ffd4401d61aefc195e5c8dd63cb68e5a05deee261dd2e54`.
The repository binding independently recomputes 18/18 pages at source recall
greater than or equal to 0.80, mean 0.9361482829653194 and minimum
0.8590476190476191.

This decision does not establish overall semantic preservation. It does not
authorize overall Stage 11 pass, production readiness or promotion, PR
readiness, merge, or Stage 12 entry.

## Evidence

- `evidence/stage11/v2d/v2d-canonical-notehead-result-binding.v1.json`
- `evidence/stage11/v2d/v2d-class-selection-decision.v1.json`
- `evidence/stage11/v2d/v2d-clef-feasibility-audit.v1.json`
- `evidence/stage11/v2d/v2d-next-semantic-class-strategy.v1.json`

The Restore ran on CPU under Python 3.13.5 and torch 2.10.0+cpu. The
measurement-only notehead detector ran from the pinned Oemer `seg_net`
checkpoint on CUDA only after an exact CPU/GPU canary box-equivalence check;
whole-session fallback was disabled.

## Clef disposition

Clef remains `REVIEW_ONLY`. Although all 18 teacher-present pages were
evaluable, only 12 reached the existing 0.80 source-recall marker, the minimum
was 0.46875, and 107 of 557 restored candidates were unmatched to source
candidates. These are detector disagreements, not absolute false positives,
because teacher box truth is not available.

The exploratory implementation also derives clef candidates from Oemer's
combined `clefs_keys` segmentation channel and a local geometry heuristic.
That is not reliable enough to justify another canonical Colab run.

## Consequences

- No new Colab run is required now.
- The next evidence investment is teacher-reviewed box/mask truth for clef and
  staff-line topology.
- Weak and unsupported classes keep their fail-closed dispositions.
- Oemer and ONNX Runtime remain measurement tools, not production dependencies.
