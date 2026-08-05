# Immutable Review Evidence Contract

**Status:** M4.4 bounded reviewer-evidence baseline  
**API contract:** `/api/v1`, version `0.5.0`  
**Tracking:** Issues #16 and #28

## Purpose

The music-score/TAB safety validator emits structured findings. M4.4 turns those findings into immutable, reviewer-only evidence artifacts so a teacher can inspect the exact source and candidate pixels behind a decision. Evidence never claims that a note, rhythm, staff mark, or TAB number has been semantically recognized.

This repository still does not contain a production browser UI. The bundle defines the stable artifact, navigation, keyboard, zoom, and stale-screen contracts that a later accessible UI must follow.

## Generation point

Evidence is generated while the job is still in `VALIDATING`. A job cannot enter `AWAITING_REVIEW` unless each target page has a current evidence bundle. This keeps evidence generation inside the active worker lease and prevents a review-ready state with missing crops.

For each target page the service records:

- immutable source artifact ID;
- current restoration-candidate artifact ID;
- current safety-report artifact ID;
- current attempt ID;
- one JSON evidence-bundle artifact;
- paired source/candidate PNG crops for each finding that has a pixel region.

Findings without a region remain visible in bundle metadata but do not create invented crop coordinates.

## Coordinate and transform contract

All overlays use source-pixel coordinates with a top-left origin. Normalized coordinates are also provided in the range `0.0–1.0`.

Candidate crops are produced from the same resize and registration provenance reported by the safety validator:

1. resize to source dimensions with area interpolation when required;
2. apply the reliable phase-correlation translation with linear interpolation;
3. crop source and aligned candidate with identical clipped bounds.

The bundle records the candidate-to-source affine matrix, reported translations, reliability, resize state, crop bounds, parent artifact IDs, and decoded pixel digests.

## Determinism and immutability

Given identical source bytes, candidate bytes, safety report, attempt ID, page number, and configuration, bundle JSON and PNG crop bytes are byte-identical.

Artifacts are content addressed by SHA-256. Existing source, candidate, safety report, crop, or bundle bytes are never overwritten. Retry clears only the page's **current** evidence pointer; historical bundles remain available to authorized reviewers until retention expiry.

## Access policy

`GET /api/v1/restoration-jobs/{jobId}/pages/{pageNumber}/review-bundle`

- reviewer role only;
- returns only the current page/attempt bundle;
- appends a `REVIEW_EVIDENCE_ACCESSED` audit event;
- fails with `review_evidence_not_ready` or `stale_review_evidence` when the page contract is not current.

Evidence bundle and crop artifact bytes require reviewer credentials and `purpose=review`. Client credentials cannot retrieve them before or after a review decision. Expiry removes their bytes through the existing retention lifecycle while preserving audit tombstones.

## Stale-screen protection

Every API review decision must include the current `evidenceBundleArtifactId`. The service verifies that the bundle still matches:

- job and page;
- current attempt;
- immutable source;
- current candidate;
- current safety report.

A missing or old bundle ID is rejected before any page decision is mutated. Multi-page requests are prevalidated as one batch, so an invalid later page cannot leave an earlier page partially reviewed.

Internal service callers retain compatibility by binding an omitted bundle ID to the current bundle, but an explicitly incorrect ID is always rejected.

## Accessibility contract for a later UI

The bundle specifies:

- finding-index pagination;
- previous/next finding order;
- source and candidate view order;
- approve, reject, and reprocess action order;
- zoom range `0.25–8.0`, step `0.25`;
- `fit_width`, `fit_region`, and `actual_pixels` modes;
- mandatory screen-reader labels.

These metadata are a transport contract, not proof that a browser UI is accessible. Full keyboard testing, screen-reader testing, color-management validation, responsive layout, and display QA remain under Issue #16.

## Display-integrity boundary

Crops are deterministic 8-bit grayscale PNGs. The bundle records decoded source/aligned-candidate pixel digests and interpolation modes. Input ICC/color profiles are **not inspected**, and `colorManagementValidated` is always `false`. A future UI must not claim color fidelity from this baseline.

## Audit and consent separation

Evidence creation, bundle access, crop access, and teacher decisions are append-only audit events. Teacher review records the evidence bundle ID used for each decision.

Evidence generation and teacher approval never create a training label or training consent. Training consent remains a separate endpoint and record.

## Remaining work

Issue #16 remains open for the complete browser review interface, accessible interaction verification, risk-map presentation, color-management checks, and display-integrity QA. Issue #14 remains open for production reviewer identity. Issue #13 remains open for production deployment and storage controls.
