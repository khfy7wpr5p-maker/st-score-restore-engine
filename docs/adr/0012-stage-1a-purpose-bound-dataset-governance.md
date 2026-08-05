# ADR 0012: Stage 1A Purpose-Bound Dataset Metadata Governance

- **Status:** Accepted for Stage 1A implementation
- **Date:** 2026-08-06
- **Roadmap stage:** Stage 1A only
- **Issue:** #32

## Context

The existing fixture contract is metadata-first and correctly separates teacher approval from training consent, but its generic `testing` permission cannot represent evaluation, calibration, held-out, and future training purposes independently. It also does not model source-family split isolation, immutable dataset snapshots, or revocation evidence strongly enough for the Stage 1 exit gate.

Stage 1A must define those contracts without selecting storage infrastructure, adding document bytes, freezing a real dataset split, activating permissions, training a model, or starting Stage 2.

## Decision

1. Keep `schemas/fixture-manifest.schema.json` version `1.0.0` and `fixtures/catalog.v1.json` unchanged as the regression-fixture planning contract.
2. Introduce a separate dataset-governance contract:
   - `schemas/dataset-catalog.schema.json`,
   - `schemas/dataset-snapshot.schema.json`,
   - `src/st_score_restore/dataset_manifest.py`.
3. Record each use purpose separately: fixture validation, quality evaluation, quality calibration, PDF-pipeline evaluation, safety calibration, held-out evaluation, model training, publication, and demonstration.
4. Every permission is deny-by-default and carries its own authorization, expiry, restriction, withdrawal, and revocation evidence.
5. Teacher approval implies neither dataset permission nor model-training permission.
6. Document bytes remain outside ordinary Git. Repository metadata may use only opaque external storage locators.
7. Each source and all deterministic derivatives share one `sourceFamilyId`.
8. A source family may belong to only one non-unassigned split.
9. Held-out items may activate only held-out evaluation. They cannot activate calibration or training.
10. Snapshot manifests are canonical-JSON digest bound to the catalog and to every included item.
11. Stage 1A snapshot metadata cannot activate model training.
12. Revoked items retain digest and size as tombstone evidence but have no active storage locator and cannot appear in snapshots.
13. Synthetic items must identify an approved non-synthetic parent, generator version, generator commit, seed, and parameters.
14. JSON Schema defines structure; a standard-library semantic validator enforces cross-field safety rules.
15. The repository contains only a metadata-only, unassigned contract example. It is not an active dataset.

## Consequences

The project gains auditable purpose isolation, split-leakage prevention, deterministic snapshot identities, and revocation semantics before real data onboarding. Stage 1B must still select and approve custody storage, encryption, key ownership, access roles, and deletion operations. Stage 1C must separately authorize and onboard real or controlled synthetic artifacts.

The contract is intentionally stricter than the existing fixture schema. It does not modify API behavior, runtime restoration, quality metrics, PDF rendering, safety thresholds, or model behavior.

## Safety and privacy impact

- No real, student, teacher, private, copyrighted, or synthetic artifact bytes are added.
- No permission is active in the repository example.
- No split is frozen by this change.
- No training use is activated.
- Identifiable personal or student data cannot be trained, published, or demonstrated.
- User-provided training requires explicit purpose authorization and de-identification.
- Revocation prevents active storage references and snapshot inclusion.

## Alternatives considered

Extending the fixture schema in place was rejected because it would mix regression-fixture planning with dataset custody and split semantics. A single generic testing flag was rejected because it permits purpose confusion. File-path storage references were rejected because they can leak infrastructure or personal naming. Relying only on JSON Schema was rejected because source-family leakage, digest binding, and purpose/split rules require semantic validation.

## Reversal or migration path

A later ADR may supersede schema version `1.0.0` with explicit migration rules. Existing fixture governance remains independently versioned. Permission narrowing or revocation creates new metadata and snapshot versions; it never silently rewrites historical evidence.
