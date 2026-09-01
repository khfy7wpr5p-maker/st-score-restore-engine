# Stage 1C C17D Phone-Photo Admission

**Status:** implementation candidate  
**Stage:** Stage 1C / C17D  
**Parent:** Issue #47  
**Purpose:** `held_out_evaluation` only  
**Eligibility/storage:** `restricted_corpus` → `managed_restricted`

## Purpose

C17D adds one genuine photographed sheet-music artifact to the Stage 1 corpus evidence without placing image bytes or provider-specific storage details in ordinary Git.

The exact Stage 1 artifact is a downscaled derivative of a Wikimedia Commons source photograph. The source record identifies a real iPhone capture and is licensed CC BY-SA 3.0. The source original contains device/GPS/time metadata and is therefore not treated as privacy-none evidence.

The exact derivative admitted by this slice has separately verified identity and privacy treatment:

- SHA-256: `abbc9a05e308ad52c8f681ad53b16845f4d2fce38a4628a5efd965293d5852b5`;
- byte size: `647003`;
- media type: `image/jpeg`;
- dimensions: 2048 × 1536;
- Stage 1 input kind: `phone_photo`;
- notation: `staff`;
- readable EXIF: empty in the exact derivative;
- privacy classification: `deidentified`;
- de-identification method: `metadata_scrub`.

The derivative is not represented as the unchanged source original. Source-record privacy metadata remains part of the external provenance evidence and is not rewritten by the derivative.

## Rights and privacy boundary

The source photograph is treated as `licensed` under CC BY-SA 3.0. The exact derivative is therefore not promoted to `open_corpus` merely because the underlying historical sheet music is old.

The binding Stage 1 path is:

```text
licensed + deidentified
        ↓
restricted_corpus
        ↓
managed_restricted
        ↓
held_out_evaluation only
```

Publication, demonstration, model training, calibration, synthetic derivation and external export remain unauthorized by this slice.

## Exact metadata bindings

Dataset item:

`dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1`

Canonical dataset-item SHA-256:

`6df8229e1a23160a21845c73ea195943287b03af77245132dfe2b53078d952bf`

Managed-restricted verification record SHA-256:

`24003f0776816f8282bb6967fc1946fba5f15bb86cca6000f96819d22eb32f4a`

The profile record contains only opaque repository-visible references. Provider, account, folder, file and human-identity evidence remains external/private.

## C11 admission boundary

C11 must independently verify:

- exact dataset-item canonical digest;
- exact artifact SHA-256 and byte size in item metadata;
- approved licensed-source rights evidence;
- approved `deidentified` privacy review;
- exact `held_out_evaluation` permission set;
- held-out split binding;
- `restricted_corpus` → `managed_restricted` compatibility;
- passing managed-restricted profile record and canonical profile digest;
- opaque external storage binding;
- no revocation;
- no artifact bytes in Git.

The admission request keeps every authorization-expansion claim false.

## Historical baseline

C17D does not mutate the historical C15 snapshot or C16 report. Historical C16 therefore remains `insufficient` and continues to report missing phone-photo coverage for that immutable historical snapshot.

C17D can affect coverage only after it is selected into a **new versioned aggregate snapshot** and that new snapshot is evaluated deterministically.

## Safety statement

This slice:

- adds no real JPEG/PDF/image bytes to ordinary Git;
- does not authorize training, calibration, publication, demonstration or synthetic derivation;
- does not authorize Stage 1 exit;
- does not authorize Stage 2;
- does not change C17A or C17C evidence;
- does not weaken the separate `user_provided -> sensitive_custody -> high_assurance_vault` boundary for the user-provided phone photo.
