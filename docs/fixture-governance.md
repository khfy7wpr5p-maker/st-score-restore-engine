# Fixture, Consent, and Usage Governance

**Status:** Milestone M1 contract baseline  
**Schema:** `schemas/fixture-manifest.schema.json` version `1.0.0`  
**Catalog:** `fixtures/catalog.v1.json`

## Purpose

The fixture catalog defines the evidence required to evaluate restoration safety across PDF, JPG/JPEG, PNG, phone photos, staff notation, guitar TAB, and combined staff+TAB systems.

The catalog is metadata-first. A fixture record does not authorize storing its document bytes. Artifact availability, testing, training, publication, and demonstration are separate decisions.

## Required coverage

The initial catalog covers digital PDF, scanned PDF, hybrid PDF, JPG, JPEG, PNG, phone photos, staff notation, guitar TAB, combined systems, and these degradations: skew, perspective, page curl, shadow, glare, uneven lighting, blur, noise, compression, and low resolution. A clean baseline is also included.

## Required metadata

Every fixture records stable fixture and regression identifiers; input kind, media type, page count, and notation type; degradation categories; artifact state, path, SHA-256, and byte size when available; provenance, rights holder, license, and usage basis; privacy and student-data flags; teacher approval and training permission separately; permitted uses; retention policy; notation/TAB risk targets; synthetic-generation details; and review status.

Unknown fields are rejected. Contract changes require a schema-version and compatibility decision.

## Approval and training permission

Teacher approval means a result is suitable for an educational workflow. It does not permit model training. Training permission has its own state: `granted`, `denied`, `not_requested`, `not_applicable`, or `withdrawn`.

User-provided material cannot be used for training unless permission is explicitly `granted` and a permission reference is recorded.

## Privacy rules

- Student data is personal data.
- Identifiable personal data cannot be used for training, publication, or demonstration.
- Pending or rejected privacy review permits no fixture use.
- Phone metadata and unrelated surroundings are privacy-sensitive.
- Metadata may describe a future fixture without storing its bytes.

## Artifact states

- `planned`: described but not created.
- `metadata_only`: governance metadata only.
- `available`: reviewed artifact with safe relative path, SHA-256, and byte size.
- `revoked`: prior availability or permission withdrawn.

Available artifacts require approved review. Original and degraded artifacts must have distinct identifiers and hashes.

## Permitted uses and retention

Testing, training, publication, and demonstration are independent booleans. A planned or pending fixture permits none.

Retention policies are `metadata_only`, `repository_permanent`, `external_until_date`, `delete_after_validation`, or `prohibited`. Private and incoming material remains outside ordinary Git.

## Synthetic generation

Synthetic fixtures are preferred initially because the clean target and applied degradation can be known. Each records an approved clean source, deterministic generator and version, seed, and parameters. A synthetic fixture cannot derive from another synthetic fixture.

## Music and TAB annotations

Risk targets include staff/TAB lines, noteheads, stems, flags, beams, dots, accidentals, rests, barlines, ties/slurs, TAB numbers, guitar articulations, and text markings. Each fixture states expected preservation invariants.

## Validation

```bash
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python tools/validate_repository.py
```

The semantic validator enforces privacy, permission, retention, artifact, identifier, and category-coverage rules that JSON Schema alone does not express clearly.

## Current artifact policy

The initial catalog contains metadata only. No score, TAB, student, teacher, copyrighted, private, training, or phone-photo bytes are added in this milestone.
