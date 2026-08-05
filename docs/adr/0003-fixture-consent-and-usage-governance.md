# ADR 0003: Fixture Consent and Usage Governance

- **Status:** Accepted
- **Date:** 2026-08-05

## Context

The project needs representative PDF, image, phone-photo, staff-notation, and guitar-TAB evidence without silently storing copyrighted or personal educational documents.

## Decision

1. Fixture metadata uses schema version `1.0.0` in `schemas/fixture-manifest.schema.json`.
2. The initial catalog is `fixtures/catalog.v1.json`.
3. Testing, training, publication, and demonstration permissions are recorded separately.
4. Teacher approval and permission for model training are separate decisions.
5. User-provided material requires explicit training permission and a reference before training use.
6. Identifiable personal data cannot be used for training, publication, or demonstration.
7. Planned metadata may exist without artifact bytes.
8. Available artifacts require approved review, provenance, license, privacy status, retention policy, SHA-256, and byte size.
9. Public-domain and deterministic synthetic fixtures are preferred initially.
10. Synthetic generation records its clean source, generator version, seed, and parameters.
11. The initial catalog must cover all approved input, notation, and degradation categories.
12. A standard-library semantic validator supplements JSON Schema.

## Consequences

The project gains auditable evidence and prevents educational approval from being mistaken for permission to train a model. Fixture onboarding requires more review work, and some documents will remain unavailable when rights or privacy cannot be established.

## Safety and privacy impact

No document becomes training data by default. The initial catalog remains metadata-only and does not add student, teacher, copyrighted, private, or phone-photo bytes.

## Alternatives considered

Adding files before documenting rights and privacy was rejected. Treating teacher approval as training permission was rejected. Using only private real-world documents was rejected as the initial baseline. Relying only on JSON Schema was rejected because cross-field rules require semantic validation.

## Reversal or migration path

A later schema version may supersede `1.0.0` through a new ADR and migration rules. Permissions may be narrowed or revoked without silently rewriting historical review evidence.
