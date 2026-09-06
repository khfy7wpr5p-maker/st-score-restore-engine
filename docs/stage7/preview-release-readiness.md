# Stage 7 — Provider-neutral Preview Release Readiness

Recorded: 2026-09-06

## Scope

Stage 7 entry and provider-neutral preview-readiness work are authorized by
`evidence/stage7/governance/stage7-entry-authorization.v1.json`.

This scope does **not** authorize preview release activation, a real user cohort,
provider selection, provider-specific adapters, live cloud resources, production
deployment, production load/soak or penetration testing, threshold/resource
changes, held-out retuning, model training/publication, or Stage 8 entry.

## S7-00 — Fresh-read and gap audit

Fresh-read base: main `432646f5ac24a30cc733b8e80243518031c32fe0`.

Confirmed baseline:

- Stage 6 final state is `COMPLETE_PASS_PROVIDER_NEUTRAL`.
- Stage 7 entry is eligible but was not authorized or started in the immutable
  Stage 6 final-exit current truth.
- provider selection remains `UNSELECTED`;
- no provider-specific adapter is active;
- no live resources were created;
- production deployment is neither authorized nor performed;
- production scale/load/soak and independent production-security sign-off remain
  outside accepted evidence.

Gap audit separated provider-neutral readiness from live/provider work:

| Capability | Stage 7 provider-neutral work | Live/provider boundary |
| --- | --- | --- |
| release channel/profile/version | implemented contract | activation separately authorized |
| feature gate / kill switch | implemented contract + synthetic drill | live control-plane wiring separately authorized |
| original fallback | implemented fail-safe route | no live mutation |
| status surface | machine-readable projection implemented | application wiring may occur without claiming activation |
| privacy-safe observability | bounded event schema implemented | production telemetry backend separately governed |
| rollback | original fallback target + synthetic drill | production rollback execution separately governed |
| compatibility | additive versioned contract | provider/app rollout separately governed |
| scale/security certification | explicitly not claimed | production evidence required |

## S7-01 — Entry governance authorization

The authorization is fail-closed and bound to the immutable Stage 6 final-exit
current truth. It permits Stage 7 provider-neutral capability work while keeping
release activation, production and Stage 8 boundaries false.

Validator: `tools/validate_stage7_entry_authorization.py`.

## S7-02 — Preview release contract

Machine-readable contract: `api/stage7-preview-contract.v1.json`.

Implementation: `st_score_restore.preview_release`.

Contract properties:

- channel: `preview`;
- profile: `provider-neutral`;
- version: `stage7.preview-contract.v1`;
- default activation gate: closed;
- rollback target: immutable original;
- kill switch: fail closed to original;
- hard safety reject: cannot route candidate as winner;
- unknown/uncertain evidence: review route;
- missing candidate: original route;
- OMR correctness and musical truth claims: always false in this layer.

## S7-03 — User-facing safety/status contract

`build_preview_status()` projects existing job/page evidence to the bounded
machine-readable states:

- `ORIGINAL`
- `RESTORED`
- `REVIEW_REQUIRED`
- `UNCERTAIN`
- `FAILED_SAFE`

The status contract always exposes original fallback availability, provenance
requirements, and explicit non-claims for OMR correctness, musical truth and
production security certification.

This is a status/projection layer only. It does not change review authority or
turn automated evidence into human musical truth.

## S7-04 — Privacy-safe observability contract

`build_privacy_safe_event()` permits only fixed event types, route reason codes,
coarse latency buckets and bounded failure classes. Job identity is represented
as an opaque SHA-256 reference. Artifact bytes, raw private metrics, secrets and
free text are excluded by construction.

This creates a provider-neutral telemetry contract; it does not activate or
certify any production logging backend.

## S7-05 — Synthetic release drills

`run_synthetic_preview_drills()` and
`tools/run_stage7_preview_release_drills.py` cover:

1. activation gate closed -> original;
2. passing candidate in synthetic active mode -> candidate;
3. hard safety reject -> original;
4. review-required evidence -> review;
5. missing candidate -> original;
6. kill switch -> original.

The drill result records `syntheticOnly=true`, `previewReleaseActivated=false`
and `productionDeploymentPerformed=false`.

Stage 4/5/6 governance workflows remain required regression gates on Stage 7 PRs.
Provider/live tests are not simulated as production evidence.

## S7-06 — Provider-neutral exit/readiness criteria

Stage 7 provider-neutral readiness may be accepted only if all of the following
are true on the exact PR head and again after merge:

- Repository validation succeeds on Python 3.11 and 3.12;
- Stage 4 governance validation succeeds on Python 3.11 and 3.12;
- Stage 5 governance validation succeeds on Python 3.11 and 3.12;
- Stage 6 governance validation succeeds on Python 3.11 and 3.12;
- Stage 7 governance validation succeeds on Python 3.11 and 3.12;
- entry authorization validator passes;
- Stage 7 unit tests pass;
- synthetic preview drills pass;
- no unresolved review thread remains;
- preview activation remains unauthorized;
- production deployment remains unauthorized/unperformed;
- provider remains unselected;
- real/private corpus or derivative bytes and raw private metrics remain outside
  ordinary Git.

A provider-neutral Stage 7 PASS means the reversible preview **capability** is
ready. It does not mean a preview cohort is active and does not certify provider,
scale, availability, restoration accuracy, OMR correctness or production
security.

## Next safe boundary

`separate_explicit_preview_release_activation_or_stage8_entry_authorization`
