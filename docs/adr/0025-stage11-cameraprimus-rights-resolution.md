# ADR 0025 — Stage 11 Camera-PrIMuS rights resolution

Date: 2026-09-07
Status: Accepted

## Context

PR #190 intentionally failed closed because Camera-PrIMuS was publicly downloadable and widely used in OMR research, but the official dataset page did not expose an explicit license grant for commercial model training.

A focused rights review was then performed against four evidence classes:

1. the official PrIMuS / Camera-PrIMuS dataset page;
2. the 2018 Camera-PrIMuS ISMIR paper;
3. the 2024 *Towards Universal Optical Music Recognition* paper;
4. the RISM data-services license statement for the underlying source data.

## Findings

- The official Camera-PrIMuS page describes and distributes the dataset, but no explicit dataset license covering commercial model training was identified.
- The 2018 Camera-PrIMuS paper is CC BY 4.0. That licenses the paper; it is not treated as an automatic license for the separately distributed dataset package.
- A 2024 OMR publication labels Camera-PrIMuS as `License: public`. `Public` is not a sufficiently specific license term for this commercial product roadmap and does not itself define commercial model-training rights.
- RISM states that its data is available under CC BY 3.0 and may be shared and adapted with attribution. This supports reuse of the underlying RISM data, but does not by itself license the separately rendered and distorted Camera-PrIMuS image package.

## Decision

Camera-PrIMuS is **not admitted for commercial Stage 11 model training under the currently documented rights evidence**.

The existing Drive corpus may remain stored and may continue to serve as a structural/reference source, but its image bytes must not enter a commercial-training manifest unless a later explicit dataset license or written permission establishes that right.

This is a completed rights review, not a pending review.

## Safe training route

Stage 11 remains authorized to train on data whose purpose rights are independently clear, including:

- public-domain score images;
- CC0 material;
- material under an explicit license compatible with commercial model training, with attribution and other obligations recorded;
- deterministic synthetic camera degradations derived from those rights-cleared clean images, with immutable derivation provenance.

The existing Residual U-Net Colab pipeline can be reused for such paired data after admission and digest verification. No Camera-PrIMuS-specific license assumption may be used to bypass the gate.

## Unchanged boundaries

- user, student, and private documents remain excluded without separate explicit consent;
- held-out data remains excluded from training and tuning;
- no production inference is authorized;
- no automatic final selection is authorized;
- no model publication is authorized;
- Stage 12 remains unauthorized;
- no model weights may be claimed until a real GPU execution produces checkpoint evidence.
