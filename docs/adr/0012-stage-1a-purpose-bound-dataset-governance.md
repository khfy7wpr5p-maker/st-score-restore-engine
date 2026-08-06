# ADR 0012: Stage 1A Purpose-Bound Dataset Metadata Governance

- **Status:** Accepted; extended by ADR 0013
- **Date:** 2026-08-06
- **Roadmap stage:** Stage 1A only
- **Issue:** #32
- **Entry decision:** `adr-0013-stage-1-entry-v1`

## Context

The existing fixture contract is metadata-first and correctly separates
teacher approval from training consent, but its generic `testing` permission
cannot represent evaluation, calibration, held-out, synthetic derivation and
future training independently. It also does not model source-family split
isolation, immutable dataset snapshots or revocation evidence strongly enough
for the Stage 1 exit gate.

## Decision

1. Keep `schemas/fixture-manifest.schema.json` version `1.0.0` and
   `fixtures/catalog.v1.json` unchanged as the regression-fixture planning
   contract.
2. Maintain a separate dataset-governance contract:
   - `schemas/dataset-catalog.schema.json`
   - `schemas/dataset-snapshot.schema.json`
   - `src/st_score_restore/dataset_manifest.py`
3. Make all purposes independent and deny-by-default.
4. Keep teacher approval separate from dataset and model-training permission.
5. Keep document bytes outside ordinary Git.
6. Use role-scoped opaque actor, subject, evidence, policy and custody IDs.
7. Keep every source and deterministic derivative in one source family and one
   assigned split.
8. Bind snapshots to canonical catalog and item SHA-256 values.
9. Keep Stage 1 training execution disabled.
10. Retain revoked digests as tombstones while removing active locators.
11. Validate synthetic parent eligibility from parent metadata rather than a
    child assertion.
12. Use JSON Schema for structure and a standard-library Python validator for
    semantic, temporal and policy enforcement.
13. Bind schema version `1.1.0` to ADR 0013.

## Consequences

The project gains auditable purpose isolation, temporal authorization,
split-leakage prevention, deterministic snapshot identities, typed restrictions,
opaque identity, de-identification binding and deletion-receipt metadata before
real data onboarding.

Storage product selection, KMS/key ownership, IAM, external identity mapping,
backup deletion operations and actual artifact onboarding remain outside
Stage 1A and require separate Stage 1B/1C approvals.

## Safety boundary

- No real, student, teacher, private, copyrighted or synthetic artifact bytes
  are added.
- No permission is active in the repository example.
- No real split is frozen.
- No model training is activated.
- No API, restoration, PDF-rendering, quality-metric or safety-threshold
  behavior changes.
