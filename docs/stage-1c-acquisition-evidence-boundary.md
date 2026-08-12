# Stage 1C Acquisition Evidence Boundary

**Status:** C3 metadata-only planning boundary  
**Stage:** Stage 1C  
**Parent issue:** #47  
**Artifact bytes onboarded by this document:** 0  
**Schema/runtime impact:** None

## 1. Purpose

Stage 1 requires every realized source to have auditable provenance together with an immutable source digest and acquisition metadata. The current dataset catalog already carries an opaque `provenance.sourceReference` plus artifact digest/size fields, but it intentionally does not place concrete origin details, local paths, provider URLs, account identifiers or artifact bytes in ordinary Git.

This document defines how those existing fields are to be interpreted before the first real artifact is admitted. It closes the acquisition-evidence boundary without changing the Stage 1A schema or authorizing artifact onboarding.

## 2. Normative binding

For a real Stage 1 candidate, `provenance.sourceReference` is the repository-visible pointer to an **external acquisition evidence record**.

The binding is:

`dataset item -> provenance.sourceReference -> external acquisition evidence -> exact acquired bytes -> SHA-256 + byte size -> custody record when admitted`

Ordinary Git stores only the opaque evidence reference and the already-approved metadata contract. Sensitive acquisition details remain outside ordinary Git.

The acquisition evidence record is evidence of how a source entered the controlled process. It is **not** by itself a rights grant, privacy approval, dataset approval or purpose authorization.

## 3. Minimum external acquisition evidence

Before a real item may become `external_available`, the external acquisition evidence referenced by `provenance.sourceReference` must contain or durably bind at least:

- the opaque acquisition evidence identifier used by `sourceReference`;
- an acquisition event timestamp in UTC;
- the source-kind classification consistent with the dataset catalog;
- an acquisition-channel code describing how the bytes entered the controlled process;
- a durable origin/provenance reference sufficient for later audit without exposing that origin in ordinary Git;
- the exact acquired artifact SHA-256;
- the exact acquired artifact byte size;
- the media type observed at acquisition;
- the evidence-record version or equivalent immutable revision identity;
- the relationship to the applicable external custody record once the artifact is admitted to custody.

Concrete names, personal identifiers, local filesystem paths, credentials, provider URLs, account/bucket identifiers and other secret-bearing details must not be copied into repository metadata merely to satisfy this requirement.

## 4. Acquisition-channel discipline

The external acquisition record must distinguish how the bytes were obtained. Channel values may be implementation-specific outside Git, but they must be able to distinguish at least the governance cases represented by the current Stage 1A source kinds:

- project-authored material;
- public-domain material;
- separately licensed material;
- explicitly user-provided material;
- synthetic material only if synthetic derivation is later separately authorized.

The channel describes acquisition, not legal entitlement. A source being downloadable, possessed, emailed, uploaded or otherwise available does not prove that its use is authorized.

## 5. Metadata-only state

While an item remains `metadata_only`:

- `artifact.sha256` remains `null`;
- `artifact.byteSize` remains `null`;
- custody locator and custody policy fields remain `null` under the existing contract;
- no repository entry may pretend that an artifact has been acquired or admitted when it has not;
- no syntactically valid placeholder SHA-256 may be used as if it were evidence;
- no item-level purpose permission becomes active merely because acquisition planning exists.

This document therefore does not require or authorize filling real digest, size or custody fields before real bytes exist in a compliant custody process.

## 6. Finalization gate before `external_available`

Before any real item changes from `metadata_only` to `external_available`, all of the following must be true:

1. the compliant offline vault gate has passed;
2. the exact bytes have been acquired into the approved controlled process;
3. the external acquisition evidence record exists and is durably identifiable by the catalog `sourceReference`;
4. SHA-256 and byte size have been calculated from those exact bytes;
5. the acquisition evidence digest and byte size equal `artifact.sha256` and `artifact.byteSize` in the dataset catalog;
6. the corresponding custody record, when created, binds the same artifact SHA-256 and byte size;
7. rights review is independently approved;
8. privacy review is independently acceptable;
9. dataset review is independently approved;
10. the requested item-level purpose authorization is current, deny-by-default and within the G4 allowlist.

A mismatch in digest, byte size, source reference or custody binding is fail-closed and blocks `external_available`.

## 7. Separation from rights and permissions

Acquisition evidence answers **what entered the process and how it was obtained**. Separate governance evidence answers **whether and for what purpose it may be used**.

Therefore:

- acquisition does not imply copyright or license permission;
- possession does not imply authorization;
- teacher approval does not imply dataset permission;
- teacher approval does not imply model-training permission;
- rights approval does not imply privacy approval;
- dataset approval does not imply a purpose grant;
- a purpose grant does not waive custody requirements.

All existing Stage 1A deny-by-default rules remain binding.

## 8. Evidence integrity

The external acquisition evidence system must preserve an auditable revision history or equivalent immutable identity so that the evidence used for admission cannot be silently replaced without detection.

If acquisition metadata is corrected, the correction must remain traceable to a new evidence revision or equivalent auditable event. Repository metadata must point to the currently accepted opaque evidence identity without exposing sensitive evidence contents.

This document does not select a storage provider, evidence database, key-management system or production identity mechanism.

## 9. Revocation and deletion

Acquisition provenance may need to remain as minimal audit evidence after artifact revocation or deletion, subject to the accepted retention and privacy rules. Retaining provenance evidence must not resurrect deleted artifact bytes or preserve prohibited personal/source-location detail in ordinary Git.

Artifact deletion receipts and custody tombstones remain governed by Stage 1B and the Stage 1A revocation contract. C3 does not replace those controls.

## 10. Current G4 boundary

C3 does not expand the G4 purpose allowlist. Current allowed purposes remain:

- `quality_evaluation`;
- `held_out_evaluation`.

The following remain unauthorized by G4:

- model training;
- quality calibration;
- safety calibration;
- PDF-pipeline evaluation;
- publication;
- demonstration;
- synthetic derivation.

## 11. No schema change in C3

C3 deliberately does not add acquisition fields to `schemas/dataset-catalog.schema.json`.

The current repository-visible boundary remains:

- `provenance.sourceReference` for the opaque external evidence pointer;
- `artifact.sha256` and `artifact.byteSize` for the immutable admitted-byte identity;
- custody references for external storage state.

A future schema change is warranted only if real onboarding evidence demonstrates that this boundary is insufficient. Such a change would require its own scoped proposal, validation and approval.

## 12. C3 safety statement

This document:

- onboards 0 artifact bytes;
- creates 0 storage resources;
- creates 0 credentials or keys;
- grants 0 item-level permissions;
- creates 0 real SHA-256 values;
- freezes 0 real splits;
- changes no schema, validator, runtime, dependency, test or workflow;
- does not authorize synthetic derivation;
- does not start Stage 2;
- does not authorize DocRes, comparator, selector, ST Image AI, training or downstream application integration.

C3 only makes the future acquisition/provenance evidence boundary explicit. Real onboarding remains blocked until the compliant offline vault and all item-specific governance gates pass.
