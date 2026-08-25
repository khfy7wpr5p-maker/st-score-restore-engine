# Stage 1C First Held-Out Artifact Onboarding — IMSLP82860

**Status:** C14 implementation candidate  
**Parent:** Issue #47  
**Purpose:** `held_out_evaluation` only  
**Split:** `held_out`  
**Storage profile:** `managed_standard`  
**Artifact bytes in Git:** 0  
**Stage 2 authorized:** no

## Scope

C14 proposes the first independently authorized held-out Stage 1 item and the first
repository corpus catalog containing both a development item and a held-out item.

The held-out artifact is a scanned public-domain score represented by the exact controlled
artifact digest and byte size in repository metadata. The artifact bytes remain outside
ordinary Git. Private external evidence contains the provider-specific object identity,
source-record details, visual review evidence, access state, and mapping from repository-safe
opaque evidence handles to the real external evidence.

The held-out item is deliberately isolated from the C12 development item:

- different dataset item ID;
- different source-family ID;
- different exact artifact SHA-256;
- `held_out_evaluation` is the only active purpose;
- `quality_evaluation` is not granted to the held-out item.

## Exact held-out metadata

- dataset item: `dataset.item.imslp82860-chopin-op69.v1`
- artifact SHA-256: `b45544448622c668702b7a9aa5317960c106a939c40faef36ffbb83e4d3af3d3`
- artifact byte size: `1114479`
- input: scanned PDF, 8 pages, staff notation
- eligibility: `open_corpus`
- storage: `managed_standard`
- privacy: `none`
- split: `held_out`

Exact-artifact rights were reviewed against the public-domain source record and the scanned
pages. Repository metadata contains only opaque evidence references; provider/account/path
identifiers and artifact bytes remain external.

## Machine-readable files

- `evidence/stage1c/corpus/catalog.v1.json`
- `evidence/stage1c/imslp82860/managed-standard-verification.v1.json`
- `evidence/stage1c/imslp82860/admission-request.v1.json`

CI must require both:

1. C11 held-out admission returns `decision=eligible` with `--require-eligible`;
2. C13 structural corpus readiness returns `state=ready` with `--require-ready`.

## Safety boundary

C14 does not:

- put either real PDF into ordinary Git;
- relabel the development item as held-out;
- permit cross-split source-family or artifact-digest reuse;
- grant model training, calibration, publication, demonstration, or synthetic derivation;
- freeze a development/held-out snapshot;
- claim empirical coverage or bias sufficiency;
- complete Stage 1 exit;
- authorize or begin Stage 2/OpenCV quality analysis;
- modify restoration runtime, HTTP API, or models.

## Acceptance

C14 is acceptable only when exact-head CI proves on Python 3.11 and 3.12 that:

1. the two-item corpus catalog validates under the Stage 1 contract;
2. the development artifact remains eligible for its existing purpose;
3. the held-out artifact is independently eligible for `held_out_evaluation`;
4. the held-out managed-standard record is `pass` and digest-bound;
5. C13 reports exactly `development=1`, `held_out=1`, with distinct source families and no
   cross-split digest leakage;
6. the complete unit suite and compile checks pass;
7. artifact bytes, provider/account/path identifiers, credentials, and Stage 2 authority do
   not enter ordinary Git.

A successful C14 only establishes minimum structural readiness for a later digest-addressed
snapshot-freeze proposal. Snapshot freeze, coverage/gap/bias evidence, dataset card completion,
and final Stage 1 exit remain separate controlled slices.
