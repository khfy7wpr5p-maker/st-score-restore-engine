# ADR 0019 — Stage 8 DocRes optional-candidate boundary

- Status: Accepted for Stage 8 provider/library-neutral contract work
- Date: 2026-09-06

## Context

The roadmap places **Stage 8 — DocRes optional candidate** after the Stage 7 preview-capability milestone and before **Stage 9 — Multi-engine comparator**. Repository safety architecture already requires every optional engine output to remain a restoration candidate, pass Music Safety Validator, and only then become eligible for later comparator logic.

The dependency policy also states that DocRes, ONNX Runtime, and future ML frameworks remain candidates until separate dependency reviews approve exact packages and versions. Stage 8 therefore cannot honestly install, download, activate, or productionize an unspecified DocRes runtime or model artifact.

## Decision

Stage 8 implements a **disabled-by-default optional candidate boundary**, not a live DocRes integration.

The Stage 8 contract requires:

1. the original artifact remains immutable and is always available as fallback;
2. a DocRes-derived output can only be represented as a derived restoration candidate with provenance;
3. normal runtime requests fail closed because the dependency and model artifact are not approved;
4. only injected synthetic executors are callable in CI drills;
5. candidate bytes are not embedded in the metadata envelope;
6. every candidate requires Music Safety Validator before any later comparator eligibility;
7. safety `reject` routes to original, `review_required` or unknown routes to review;
8. safety `pass` produces only `validated_candidate_hold` and never final selection;
9. Stage 9 comparator selection remains separately unauthorized;
10. no external package install, model download, network fetch, real-user cohort, production deployment, training, publication, threshold/resource change, or held-out retuning is authorized.

## Consequences

Stage 8 can be completed as a testable integration contract without fabricating a live DocRes capability. A later decision may approve an exact DocRes implementation, package/model identity, hashes, license, runtime isolation, resource envelope, and security evidence. That approval must extend or replace this contract explicitly; it cannot be inferred from Stage 8 PASS.

## Non-claims

Stage 8 PASS does not establish OMR correctness, musical truth, universal restoration effectiveness, production availability/scalability, provider-specific security certification, or color-fidelity certification.
