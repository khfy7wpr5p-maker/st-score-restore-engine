# ADR 0029 — Stage 11 V2a Shadow Job-Service Handoff

Status: Accepted for Stage 11 validation only  
Date: 2026-09-08

## Context

The frozen V2a candidate has already passed packaging, arbitrary-size consumer-adapter
validation, and a transport-neutral staging PNG request/response check. The next safe
question is whether that same candidate can be observed beside the existing non-production
restoration job workflow without becoming a selectable restoration candidate or changing
review behavior.

The existing service remains the authority for immutable source custody, deterministic
OpenCV candidate creation, music-safety validation, and evidence-bound teacher review.
V2a is not authorized to replace those decisions, serve production traffic, receive real
user/student data, or enter Stage 12.

## Decision

Add an explicit non-production subclass,
`Stage11V2aShadowRestorationJobService`, that preserves the complete existing
`RestorationJobService` workflow and adds one post-primary method:
`run_stage11_v2a_shadow_job`.

The method may run only when the current attempt is `AWAITING_REVIEW`. It captures the
immutable PNG source, current primary OpenCV candidate, and current safety-report identity;
runs the already validated staging adapter; computes observational pixel differences; and
stores the shadow PNG/evidence under roles that are never assigned to
`currentCandidateArtifactId` or `currentSafetyReportArtifactId`.

All pages in the current attempt are computed before any shadow artifact is committed. The
job/attempt/page identities are rechecked under the store lock before commit. A stale job
fails closed. A deterministic run key makes a repeated call idempotent for the same current
attempt and primary-candidate set.

## Input boundary

Only native 8-bit grayscale PNG pages are accepted by this Stage 11 shadow surface.
`sourceDataKind` must be one of:

- `synthetic_only`
- `nonheldout_test_only`

The committed acceptance execution is synthetic-only. Held-out, private, student, and real
user inputs remain forbidden.

## Selection invariants

A shadow run must not change:

- `currentCandidateArtifactId`;
- `currentSafetyReportArtifactId`;
- `reviewDecision`;
- `selectedArtifactId`;
- the primary comparator/teacher-review semantics.

Shadow output has role `stage11_v2a_shadow_candidate`; its observation record has role
`stage11_v2a_shadow_evidence`. Neither role is a selectable candidate contract.
Comparison metrics are observational only and cannot make a quality decision or trigger
promotion.

## Transport and production boundary

No route is added to `http_api.py`. `api/openapi.v1.json`, `tools/run_api.py`, and the
normal `RestorationJobService` remain unchanged. The shadow subclass must be constructed
explicitly by a validation harness.

Production inference, production promotion, real-user rollout, final production-model
selection, and Stage 12 entry remain unauthorized.

## Execution evidence

The exact frozen private TorchScript package
`7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234`
(7,817,857 bytes) was executed on a synthetic 700x900 score-like page on CPU. The shadow
output SHA-256 was
`7a3033100e433236293700673d847701960252669634a07507069ad045678c60`, matching the
previous staging execution for the same synthetic input. Against the same-pixel PNG
primary comparator, mean absolute difference was `0.0279114954`, maximum absolute
difference `0.4980391860`, and changed-pixel fraction `0.0850507937`. These values are not
quality or promotion gates.

Repository integration tests exercise the actual existing job-service storage and selection
invariants with an injected deterministic staging handle because the private model package
is not committed to the repository.

## Consequences

This establishes a controlled shadow lane beside the existing non-production job workflow
without changing the application result. It does not establish production readiness.

The next safe boundary is an approved non-held-out shadow-corpus observation pass using
public/test custody only. Stage 12 remains closed.
