# Stage 4 — Human Reference-Label Review Guide

**State:** review template only / no human labels accepted yet  
**Scope:** Beethoven + Barley development artifacts only  
**Purpose:** `safety_calibration`  
**Required review method:** `human_expert_review`

## Safety boundary

This guide prepares human reference evidence; it does not create it. Automated metrics, Model predictions, OMR output or assistant judgment must not be copied into `referenceLabel` as ground truth. The reviewer must inspect the source page and make the judgment independently.

Chopin is excluded from this development review package. It remains `held_out_evaluation` only and must not be inspected for threshold/candidate selection or tuning.

No PDF/image bytes are stored in ordinary Git. The review package contains only exact artifact identities, page numbers and empty review slots.

## Review scope

The work package contains:

- Beethoven: 4 pages;
- Barley: 2 pages;
- 7 finding types per page;
- 42 total human-review slots.

Finding taxonomy is exactly the Stage 4 contract taxonomy:

- `skew`: visible page/staff rotation or tilt;
- `blur`: loss of edge/detail sharpness;
- `glare`: bright reflective or blown-out regions that obscure score content;
- `shadow`: localized dark regions caused by illumination/occlusion;
- `uneven_lighting`: material brightness variation across the page;
- `noise`: visible random/speckle-like image degradation;
- `compression`: visible compression/blocking/ringing degradation.

These descriptions are review prompts, not numerical thresholds. Stage 4 does not invent or change production thresholds from this guide.

## Allowed reference labels

For every page/finding slot choose exactly one:

- `clear` — the finding is not materially present on inspection;
- `possible` — some evidence is visible but the finding is uncertain or weak;
- `probable` — the finding is clearly supported by human inspection;
- `not_assessed` — the reviewer cannot make a reliable judgment from the available source.

Do not infer a label from the engine's current metric score.

## Required human provenance

When a slot is reviewed, all four currently-empty fields must be supplied together:

- `referenceLabel` — one allowed label above;
- `reviewerReference` — an opaque non-personal token, not a name/email;
- `provenanceReference` — an opaque evidence/reference token describing the review record;
- `reviewedOn` — ISO date `YYYY-MM-DD`.

The downstream Stage 4 contract requires `reviewMethod=human_expert_review`, `dataClass=real`, `split=development`, `purpose=safety_calibration`, and an already validated purpose grant.

## Acceptance is separate

Completing review slots does **not** automatically accept the bundle. A later evidence-bound decision must validate the completed records, exact purpose permission, provenance, one-to-one observation bindings and anti-leakage rules before `referenceBundleAccepted=true` can exist.

Until that separate acceptance:

- real calibration execution remains NOT AUTHORIZED;
- no production threshold/resource change is allowed;
- `stage4ExitPass=false`;
- Stage 5 remains blocked.
