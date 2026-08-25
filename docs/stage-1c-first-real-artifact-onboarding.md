# Stage 1C First Real Artifact Onboarding — IMSLP799143

**Status:** C12 implementation candidate; first real Stage 1 artifact admission  
**Parent:** Issue #47  
**Purpose:** `quality_evaluation` only  
**Split:** `development`  
**Storage profile:** `managed_standard`  
**Artifact bytes in Git:** 0  
**Stage 2 authorized:** no

## Scope

This slice proposes the first real Stage 1 dataset item after C11.

The exact score PDF remains outside ordinary Git. Repository-visible metadata contains the
artifact SHA-256 and byte size required by the Stage 1 catalog contract, plus opaque
references to private external acquisition, rights, storage, and control evidence.

The item is a public-domain scanned score source. Exact-artifact rights were checked against
the source record for the exact downloaded artifact. Privacy classification is `none`.
The only active purpose is `quality_evaluation`, and the item is assigned to `development`.

## Evidence boundary

Private external evidence records:

- exact acquisition/source record;
- exact-artifact public-domain rights review;
- exact byte size and SHA-256 calculation;
- private storage object binding;
- current access-state evidence;
- managed-standard transport/at-rest encryption, version drift, and retention/deletion evidence;
- mapping from repository-safe opaque evidence handles to provider/source details.

Provider names, account identities, folder/file identifiers, local filesystem paths, and
human-readable actor identities are intentionally excluded from ordinary Git.

## Machine-readable files

- `evidence/stage1c/imslp799143/catalog.v1.json`
- `evidence/stage1c/imslp799143/managed-standard-verification.v1.json`
- `evidence/stage1c/imslp799143/admission-request.v1.json`

The CI gate runs C11 with `--require-eligible` against those exact three files.

## Safety boundary

This slice does not:

- add the PDF bytes to Git;
- grant model training, quality/safety calibration, publication, demonstration, or synthetic derivation;
- activate held-out use for this development item;
- freeze a Stage 1 snapshot;
- claim corpus coverage or bias completion;
- begin Stage 2 or change OpenCV quality-analysis behavior;
- modify restoration runtime, HTTP API, or models.

If rights, artifact digest, storage binding, profile evidence, purpose, split, retention, or
review state changes, C11 must be re-evaluated and may fail closed.

## Acceptance

C12 is acceptable only when exact-head CI demonstrates:

1. the catalog validates under Stage 1 schema `1.3.0`;
2. C7 resolves the item to `open_corpus` / `managed_standard`;
3. the real managed-standard profile record validates as `pass`;
4. C11 returns `decision=eligible` with `--require-eligible`;
5. all existing repository tests and compile checks pass on Python 3.11 and 3.12;
6. no artifact bytes, provider identifiers, credentials, Stage 2 work, or authority expansion enter Git.

After merge, corpus realization may add additional independently admitted items. Split freeze,
coverage/bias documentation, dataset card, and Stage 1 exit remain separate later slices.
