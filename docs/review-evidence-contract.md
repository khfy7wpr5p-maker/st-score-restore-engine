# Immutable Review Evidence Contract

**Status:** Stage 5 local accessible reviewer UI baseline  
**API contract:** `/api/v1`, version `0.5.0`  
**Tracking:** Issues #16 and #28

## Purpose

The music-score/TAB safety validator emits structured findings. The immutable review-evidence layer turns those findings into reviewer-only evidence artifacts so a teacher can inspect the exact source and candidate pixels behind a decision. Evidence never claims that a note, rhythm, staff mark, or TAB number has been semantically recognized.

Stage 5 now includes a non-production same-origin browser interface at `/review`. The interface consumes the existing immutable review-evidence and review APIs rather than creating a second decision path. It is a local review surface only; it does not authorize production deployment, production identity/network controls, or Stage 6.

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

The `/review` HTML/CSS/JavaScript assets themselves contain no review evidence and are served without API credentials. All job, bundle, artifact, and decision requests made by the UI still use the reviewer-authenticated `/api/v1` routes.

## Stale-screen protection

Every API review decision must include the current `evidenceBundleArtifactId`. The service verifies that the bundle still matches:

- job and page;
- current attempt;
- immutable source;
- current candidate;
- current safety report.

A missing or old bundle ID is rejected before any page decision is mutated. Multi-page requests are prevalidated as one batch, so an invalid later page cannot leave an earlier page partially reviewed.

The Stage 5 browser UI always submits the current `evidenceBundleArtifactId`. If the API returns `stale_review_evidence`, `review_evidence_not_ready`, or `candidate_not_current`, the UI reports that no stale-screen decision was recorded and reloads the current page evidence before allowing another decision.

Internal service callers retain compatibility by binding an omitted bundle ID to the current bundle, but an explicitly incorrect ID is always rejected.

## Stage 5 browser interaction contract

The `/review` interface implements the evidence-bundle interaction contract:

- finding-index pagination;
- previous/next finding order;
- source and candidate view order;
- approve, reject, and reprocess action order;
- zoom range `0.25–8.0`, step `0.25`;
- `fit_width`, `fit_region`, and `actual_pixels` modes;
- labeled form controls and evidence views;
- visible focus styles and a skip link;
- status and error announcement regions;
- responsive mobile layout;
- reduced-motion and forced-colors CSS handling;
- minimum 44 px control height for primary controls;
- API credentials kept in page memory only, with no `localStorage` or `sessionStorage` use.

The UI is dependency-free and uses same-origin assets and API requests. Its static responses use a fail-closed Content Security Policy, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, no-store caching, and related same-origin hardening.

Structural accessibility checks are automated in `tests/test_review_ui.py` and `tools/validate_stage5_review_ui.py`. These automated checks do not by themselves prove behavior in every browser/screen-reader combination; the Stage 5 QA record distinguishes automated evidence from any real browser or assistive-technology execution evidence.

## Display-integrity boundary

Crops are deterministic 8-bit grayscale PNGs. The bundle records decoded source/aligned-candidate pixel digests and interpolation modes. Input ICC/color profiles are **not inspected**, and `colorManagementValidated` is always `false`.

The Stage 5 UI therefore explicitly states that evidence crops are grayscale and does not claim color fidelity. This is a truthful display-integrity boundary, not a color-management certification.

## Audit and consent separation

Evidence creation, bundle access, crop access, and teacher decisions are append-only audit events. Teacher review records the evidence bundle ID used for each decision.

Evidence generation and teacher approval never create a training label or training consent. The Stage 5 review UI intentionally contains no training-consent action. Training consent remains a separate endpoint and record.

## Remaining production boundary

The `/review` interface is a local/non-production Stage 5 capability. Issue #14 remains the production reviewer-identity boundary and Issue #13 remains the production deployment/storage boundary. Completing Stage 5 does not grant either boundary and does not authorize Stage 6.
