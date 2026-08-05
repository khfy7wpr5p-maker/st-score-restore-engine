# Stage 1A Dataset Governance and Metadata Contract

**Status:** Stage 1A contract implementation  
**Issue:** #32  
**Artifact policy:** Metadata only  
**Runtime impact:** None

## 1. Scope

Stage 1A defines the metadata and validation boundary required before any real-data onboarding. It does not:

- create or collect document bytes,
- select a cloud or local custody product,
- activate an evaluation, calibration, or training permission,
- freeze a real dataset split,
- tune a quality or safety threshold,
- start Stage 2,
- add DocRes, a comparator, a selector, or an image model.

## 2. Contract separation

The existing fixture catalog remains the regression-fixture planning contract. The Stage 1A dataset contract is separate because dataset governance adds custody, purpose authorization, source-family isolation, frozen snapshots, and revocation semantics.

| Contract | Responsibility |
|---|---|
| `fixtures/catalog.v1.json` | Metadata-only regression fixture coverage plan |
| `dataset-catalog.schema.json` | Source/item, permission, privacy, lineage, split, retention, and review metadata |
| `dataset-snapshot.schema.json` | Digest-bound, reviewed split snapshot |
| `dataset_manifest.py` | Cross-field semantic enforcement |

## 3. Purpose permissions

All purposes are independent and deny-by-default:

- `fixture_validation`
- `quality_evaluation`
- `quality_calibration`
- `pdf_pipeline_evaluation`
- `safety_calibration`
- `held_out_evaluation`
- `model_training`
- `publication`
- `demonstration`

A granted permission requires an authorization reference, authorizer, and authorization date. Expired and withdrawn permissions retain their original authorization evidence. Withdrawn permissions additionally require a revocation date and revocation reference.

Teacher approval cannot create any of these permissions.

## 4. Artifact states

- `metadata_only`: no digest, byte size, or storage locator.
- `external_available`: immutable SHA-256, byte size, and opaque custody locator are required.
- `revoked`: the historical digest and byte size remain, but the storage locator must be absent.

Ordinary Git remains metadata-only. Storage locators are opaque identifiers, not file paths, URLs containing credentials, or personal names.

## 5. Source families and synthetic lineage

Every source and all of its derivatives share one `sourceFamilyId`.

A synthetic item must:

- reference a non-synthetic parent item,
- use the same source family,
- record generator name and version,
- record generator commit SHA-256,
- record a deterministic seed and parameters,
- assert that the clean source was approved.

Synthetic-on-synthetic derivation is rejected to keep lineage and split isolation unambiguous.

## 6. Split policy

Supported metadata states:

- `unassigned`
- `development`
- `calibration`
- `held_out`
- `training_reserved`

Rules:

1. Unassigned items cannot activate any purpose.
2. A source family may occupy only one assigned split.
3. Held-out items may grant only `held_out_evaluation`.
4. Development and calibration items cannot grant held-out or training use.
5. Training-reserved items may grant only explicit model-training use.
6. Stage 1A snapshot metadata always keeps `trainingUseActivated=false`.
7. Assignments are sorted and digest-bound for deterministic review.

No repository example assigns a split. Real split proportions and access separation remain an architectural decision for later Stage 1 work.

## 7. Privacy boundary

Privacy classifications are:

- `none`
- `deidentified`
- `personal`
- `student`

Deidentified data requires an approved privacy review, a documented method, and a distinct derivative SHA-256. Identifiable personal or student data cannot be used for training, publication, or demonstration. Pending or rejected privacy review cannot support an active purpose.

User-provided material cannot be used for model training unless it is deidentified and the model-training purpose is explicitly granted.

## 8. Retention and revocation

Metadata-only items have no custody class. External items require an external custody class and a deletion policy. Revoked items require deletion and cannot retain an active locator.

A snapshot lists all revoked item IDs represented by its catalog and cannot assign a revoked item. Revocation operations and deletion receipts remain Stage 1B custody procedures; Stage 1A defines only the metadata contract.

## 9. Snapshot integrity

A snapshot records:

- catalog identity and canonical SHA-256,
- semantic snapshot version,
- sorted item assignments,
- per-item canonical SHA-256,
- source family and split,
- held-out freeze state,
- revoked item IDs,
- separate real and synthetic counts,
- coverage-gap notes,
- approved review evidence.

Changing catalog metadata or an item changes its digest and invalidates the snapshot.

## 10. Repository example

`examples/dataset-catalog.metadata-only.v1.json` demonstrates structure only:

- no bytes,
- no digest,
- no storage locator,
- no active permission,
- no assigned split,
- no completed review.

It is not a dataset and cannot satisfy the Stage 1 exit gate.

## 11. Validation

```bash
python tools/validate_dataset_manifest.py \
  examples/dataset-catalog.metadata-only.v1.json

python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

The semantic validator rejects unknown fields and enforces purpose evidence, privacy, artifact state, lineage, source-family split isolation, snapshot digest binding, held-out separation, revocation, and Stage 1A training prohibition.

## 12. Deferred decisions

Stage 1A does not select:

- custody storage technology,
- encryption provider or key custodian,
- data-custodian identities,
- reviewer identities,
- backup deletion behavior,
- real corpus composition,
- split proportions,
- coverage acceptance thresholds,
- revocation operational tooling.

Those decisions require separate approval before Stage 1B or Stage 1C.
