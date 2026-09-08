# ADR 0033 — Stage 11 V2a preservation root-cause closure

Status: Accepted for non-production Stage 11 analysis

Date: 2026-09-08

## Context

PR #209 froze the exact V2a package and recorded a five-page non-held-out structural preservation review as blocked. The review intentionally used conservative structural signals and left two separate questions open:

1. why only one of five fresh shadow PNG hashes reproduced the previously committed shadow identities; and
2. whether the legacy binary dark-pixel invention, single maximum component-shift veto, and low-resolution system detector were overstating preservation risk.

The frozen package remains SHA-256 `7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`, 7,817,857 bytes. No held-out data may be re-opened for adaptive tuning and the candidate weights remain immutable.

## Decision

Add a Stage 11-only analysis layer. Do not modify the shared `music_safety_validator`, HTTP API, OpenAPI, normal `RestorationJobService`, production inference boundary, or candidate weights.

### Determinism finding

The exact package and exact Wikimedia development source were re-executed under the same Python/torch/OpenCV/NumPy software versions while changing only the CPU intra-op thread profile.

- intra-op threads `5` reproduced the PR #208 Wikimedia shadow SHA-256 exactly: `0f914fd2508efb7af84de633d8010e66668a32a47ba647aa0aae2e744e7065e3`;
- intra-op threads `4` reproduced the PR #209 Wikimedia shadow SHA-256: `6ecdd820edb5de0bbcf5a560f32015e70f3f44e5d400af58d2de63f01a4711f1`;
- intra-op threads `8` also reproduced the PR #209 Wikimedia identity;
- two independent thread-5 runs were byte-identical and pixel-identical;
- the thread-5 versus thread-4 decoded images differed at exactly one pixel with maximum grayscale difference 1.

Therefore CPU intra-op thread count is sufficient to explain the observed PR #208/PR #209 Wikimedia identity switch. This ADR does **not** claim that thread count is the sole root cause of every historical drift across all five pages.

### Stage 11-only preservation interpretation

The root-cause layer introduces three bounded changes in interpretation:

1. **Near-edge raster tolerance.** Dark-pixel loss/invention is measured again after a two-pixel Euclidean-neighborhood allowance. One-pixel line thickening or sub-pixel registration effects are not automatically reinterpreted as creation of new musical symbols.
2. **Robust component-shift distribution.** Plausible connected components are summarized using a distance-gated centroid distribution. A single maximum displacement outlier is not by itself a reject veto.
3. **Geometry reliability gate.** At 72 DPI, system-count or line-break output from an unreliable detector is retained as review evidence but not promoted into a semantic claim that staff/TAB structure changed.

These rules are isolated to Stage 11 root-cause analysis. The shared application safety validator is unchanged.

## Evidence outcome

On the Wikimedia combined staff+TAB development page, the legacy validator reported 29,866 invented dark pixels. Root-cause analysis found approximately 80.93% within one pixel and 91.74% within two pixels of existing source ink. With a two-pixel allowance, tolerant source-ink loss was 5 of 97,665 source dark pixels and distant invented dark pixels were 2,467 (~2.526%).

The component-shift distribution was approximately median 0.60 px, p95 1.45 px, p99 4.26 px, with one maximum outlier around 19.30 px. The maximum remains visible as evidence but no longer acts as a stand-alone veto.

The Wikimedia page changes from legacy `reject` to Stage 11 redesign `review_required`. It does **not** become `pass`, because semantic per-class identity is not established.

The four Beethoven 72-DPI pages remain `reject` under the redesign because robust component-preservation and/or distant-dark-change risks remain material after the diagnosed false-veto mechanisms are removed. The aggregate becomes:

- `reject`: 4
- `review_required`: 1
- `pass`: 0
- preservation disposition: `blocked`

## Consequences

The root cause of the Wikimedia cross-run hash switch is materially narrowed and reproduced. Two conservative false-veto mechanisms are diagnosed. The redesign does not weaken production behavior and does not authorize automatic approval.

Production inference, production promotion, real-user rollout, final production-model selection, and Stage 12 remain closed.

The next safe boundary is to freeze an explicit canonical CPU inference execution profile and broaden semantic-preservation evidence on additional already-approved non-held-out development sources. Consumed held-out data remains unavailable for retuning.
