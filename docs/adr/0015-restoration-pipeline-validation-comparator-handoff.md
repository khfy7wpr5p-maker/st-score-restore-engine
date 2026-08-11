# ADR 0015: Restoration Variant Validation, Comparator, and OMR Handoff

- **Status:** Accepted; current OpenCV ordering invariant implemented; later multi-engine and handoff work remains roadmap-gated
- **Date:** 2026-08-11
- **Decision ID:** `adr-0015-restoration-pipeline-validation-comparator-handoff-v1`
- **Repository:** `khfy7wpr5p-maker/st-score-restore-engine`
- **Decision base commit:** `5026ae49a3da6e1be1528482c30e38602f7401b8`
- **Current implementation evidence:** PR #50 merged as `e69ef6807fb48c315b322ea47027db236d7e67a8`
- **Runtime impact:** the current OpenCV job flow is aligned to validate before comparator evidence; DocRes, ST Image AI, Roadmap Stage 9 comparator, and ScoreMosaic runtime integration remain unimplemented

## Context

ST Score Restore Engine exists to improve the visual usability of music-score and guitar-TAB documents supplied as PDF, JPEG/JPG, PNG, or photographed sheet-music pages. Its responsibility is visual restoration and preservation, not OMR, MusicXML generation, semantic note inference, or automatic musical correction.

The long-term engine set is intentionally plural:

- deterministic OpenCV safe restoration,
- DocRes as an optional externally sourced AI restoration engine after its roadmap gate,
- a future project-owned ST Image AI restoration model after its own roadmap gate.

A previous high-level diagram placed the comparator before the music/TAB safety validator. That ordering is not acceptable for the multi-engine target architecture because an unsafe derivative must never become an eligible winner merely because it has an attractive visual score. The target architecture also requires the immutable original to remain a first-class selection option rather than only a last-resort error fallback.

This ADR records the architecture path so later DocRes, selector, ST Image AI, ScoreMosaic, SesliTab, and MusicXML-to-Guitar-TAB integration work cannot silently drift away from it.

### Current implementation status

The initial architecture decision was recorded before runtime alignment. A separately approved regression-and-runtime package was subsequently merged in PR #50. The current OpenCV-only job path now enforces the bounded ordering invariant by:

- entering validation directly after supported restoration processing,
- emitting `PAGE_VALIDATED` before `CANDIDATES_COMPARED`,
- excluding `reject` verdicts from comparator eligibility evidence,
- recording the immutable original as selectable comparator baseline evidence.

This is a current safety-ordering baseline only. It is **not** the Roadmap Stage 9 multi-engine comparator and does not activate any later roadmap stage.

## Decision

### 1. Normative target flow

The following order is the canonical restoration and downstream-OMR architecture:

```text
PDF / JPEG / PNG / phone-captured page
              |
              v
Immutable source + input inspection
              |
              v
Document / quality analysis
              |
              v
+-------------+-----------------+
|             |                 |
v             v                 v
OpenCV      DocRes          ST Image AI
current     future          future
|             |                 |
+-------------+-----------------+
              |
              v
Per-variant Music/TAB Safety Validator
              |
              v
Comparator
(original is always an eligible baseline)
              |
              v
Selected source variant
              |
              v
ScoreMosaic Safe Intake
              |
              v
ScoreMosaic OMR
              |
              v
MusicXML
```

The selector planned for Roadmap Stage 10 may decide which optional restoration engines or profiles are worth invoking, but it may not bypass, reorder, or weaken the mandatory downstream sequence:

```text
restoration variant -> safety validation -> comparator -> original-aware selection
```

### 2. Terminology boundary

ST Score Restore outputs are **restoration variants**. They are not OMR candidates.

Use these terms consistently:

- `immutable_source` — exact original bytes accepted at the ST boundary,
- `restoration_variant` — an immutable visual derivative produced by OpenCV, DocRes, or ST Image AI,
- `safety_report` — source-versus-variant structural preservation evidence,
- `selected_source_variant` — original or an eligible restoration variant selected for downstream use,
- `omr_candidate` — MusicXML/MXL or equivalent OMR-engine output created later by ScoreMosaic engines.

This distinction prevents restoration-engine identities from being mixed with Audiveris, HOMR, Clarity, or other OMR-engine candidate identities.

### 3. Safety validation precedes comparator eligibility

Every restoration derivative must be validated against the exact immutable source before it can become comparator-eligible.

A safety verdict has these consequences:

- `reject` — variant is ineligible for selection and may remain only as audit/debug evidence,
- `review_required` — variant may be retained for controlled comparison/review according to the later calibrated policy, but cannot gain automatic approval,
- `pass` — variant is eligible for comparison, not automatically selected or approved.

The comparator must never convert a validator rejection into eligibility.

### 4. Original is always a first-class comparator baseline

The immutable original is always available to the selection layer and may win even when one or more restoration variants pass validation.

The comparator must support at least these outcomes:

- original preferred,
- one restoration variant preferred,
- review-only because evidence is uncertain,
- no acceptable derivative, therefore original retained.

Visual change alone is never proof of improvement. A derivative that is safe but not measurably better than the original does not need to win.

### 5. Comparator responsibilities

The future multi-engine comparator consumes only trusted identities and validated evidence. It must combine, when those metrics become available:

- safety verdict and veto state,
- structural risk score,
- quality-analysis evidence,
- engine/version provenance,
- source and output identities,
- downstream OMR-effectiveness evidence when explicitly measured,
- deterministic tie-breaking and explainable recommendation.

Appearance metrics cannot override a hard music/TAB safety veto.

The current single-OpenCV safety-oriented comparison helper is not the completed Roadmap Stage 9 comparator.

### 6. Engine-neutral restoration-variant contract

Before DocRes or ST Image AI can enter the trusted path, the project must define an engine-neutral restoration-variant envelope. The envelope must bind, at minimum:

- schema version,
- source artifact ID and SHA-256,
- variant artifact ID and SHA-256,
- byte size and media type,
- dimensions,
- immutable/derived-from relationship,
- engine ID and engine version,
- configuration digest,
- candidate/variant status,
- safety declarations,
- model ID, model version, and model SHA-256 when a learned model is used,
- provenance sufficient to reproduce or disable the exact engine/model path.

OpenCV may retain its richer operation-by-operation audit manifest as engine-specific evidence. The engine-neutral envelope must not erase that evidence.

### 7. AI provenance and training boundary

DocRes and ST Image AI are optional candidates, never automatically trusted replacements for OpenCV or the original.

For any learned engine:

- model identity and checksum are mandatory,
- inference configuration must be versioned and digest-bound,
- model files are not committed to ordinary Git by default,
- online self-training from production/user documents is prohibited,
- training data requires explicit training authorization separate from teacher approval and evaluation permission,
- model rollback and complete disable/kill-switch behavior are mandatory before release activation.

DocRes integration does not itself authorize model training. ST Selector training and ST Image AI training are separate future activities under their roadmap gates.

### 8. Format boundary for the first integration profile

The first practical restoration-integration profile is deliberately narrow:

- JPEG/JPG — supported by the current OpenCV baseline,
- PNG — supported by the current OpenCV baseline,
- digital vector PDF — preserve original vector document; do not implicitly rasterize,
- scanned/hybrid/arbitrary PDF — restoration bypass until the reviewed multi-page PDF/rendering stage is complete.

No integration may claim general PDF restoration merely because the HTTP/API layer accepts `application/pdf` for inspection or job creation.

### 9. Cross-service limits fail closed

When a selected source variant is handed to ScoreMosaic, the receiving service remains authoritative for its own intake limits and trust boundary.

The handoff must therefore use the strictest applicable intersection of sender/receiver constraints or allow ScoreMosaic to reject the variant safely. Size, pixel, media-type, filename, and structural evidence must never be weakened merely to make the two services agree.

### 10. ScoreMosaic handoff boundary

ST Score Restore is not an OMR engine and must not be inserted into ScoreMosaic's OMR engine list.

The selected visual source variant is handed to ScoreMosaic as document input. ScoreMosaic must independently apply its own Safe Intake decision before any OMR dispatch.

The handoff must preserve provenance from:

```text
immutable original
    -> restoration variant, if selected
    -> ScoreMosaic source artifact
    -> OMR engine result
    -> MusicXML
```

A future service-to-service contract must bind the selected variant identity, source identity, safety evidence, authentication, purpose, timeout, and error mapping. This ADR does not create that runtime endpoint or weaken the current teacher-review artifact-access policy.

### 11. Teacher review is not preprocessing identity

Selecting a restoration variant for a controlled downstream OMR experiment is not the same operation as teacher approval of a final user-facing restored document.

Likewise:

- comparator selection is not teacher approval,
- teacher approval is not training consent,
- OMR use is not model-training authorization,
- OMR output is not automatically musical truth.

Current API access rules remain unchanged until a separately reviewed internal handoff contract is implemented at the appropriate roadmap stage.

### 12. OMR effectiveness and visual quality are separate measurements

A restoration can look cleaner without improving OMR, and can sometimes improve OMR without being visually preferred.

Future experiments should therefore report separately:

- visual/document quality change,
- music/TAB structural safety,
- downstream ScoreMosaic OMR effectiveness.

No single metric may silently stand in for all three.

### 13. Architecture lock and change control

This ADR is the normative target-path decision for restoration-engine ordering and ScoreMosaic handoff.

The following invariants are locked:

1. immutable original is never overwritten,
2. restoration engines create separate variants,
3. every derivative is safety-validated before comparator eligibility,
4. rejected derivatives cannot win,
5. original always remains a selectable baseline,
6. comparator selection is not teacher approval,
7. ST Score Restore remains visually focused and does not become OMR,
8. ScoreMosaic independently re-validates selected input at its Safe Intake boundary,
9. DocRes/ST Image AI remain optional and disable-able,
10. training permission remains separate from evaluation, teacher review, and normal processing.

Changing any of these invariants requires a new explicit architecture decision and separate approval. Later implementation work must converge to this architecture rather than changing the architecture implicitly in code.

### 14. Roadmap gates remain binding

This ADR records the target architecture and the implemented current OpenCV ordering invariant. It does not pull future implementation stages forward.

In particular, it does not authorize:

- Stage 2 quality-analysis implementation,
- Stage 3 PDF rendering,
- DocRes runtime integration,
- Stage 9 multi-engine comparator implementation,
- Stage 10 selector implementation or training,
- Stage 11 ST Image AI model development or training,
- ScoreMosaic runtime modification,
- SesliTab or MusicXML-to-Guitar-TAB repository modification,
- production deployment or public upload.

The current roadmap order and explicit stage-entry/merge approvals remain controlling.

## Consequences

The project gains one stable architectural spine for deterministic and AI restoration engines. Future engines can vary internally without changing the safety ordering or downstream trust model.

The comparator cannot optimize for appearance before safety evidence exists. The original remains a legitimate winner, so experimentation with AI does not force AI output into the downstream workflow.

ScoreMosaic can measure whether restoration actually helps OMR while preserving its own intake and candidate-safety boundaries.

Additional work will later be required for an engine-neutral variant schema, quality metrics, AI provenance, internal service authentication, selected-variant handoff, original-aware comparator behavior, and cross-repository compatibility tests.

## Rejected alternatives

- **Comparator before safety validation:** rejected because visually attractive but structurally unsafe variants could become eligible.
- **Use only the best-looking derivative and drop the original:** rejected because restoration may fail to improve or may damage downstream recognition.
- **Treat ST Score Restore as another ScoreMosaic OMR engine:** rejected because restoration variants and MusicXML OMR candidates are different artifact classes.
- **Let DocRes or ST Image AI replace OpenCV automatically:** rejected because AI engines remain optional candidates and require independent provenance, validation, rollback, and disable controls.
- **Reuse teacher approval as training permission:** rejected because processing, review, evaluation, and training are separate purposes.
- **Skip ScoreMosaic Safe Intake for ST-selected bytes:** rejected because cross-service trust must be re-established at the receiver boundary.

## Verification boundary

The initial ADR record was documentation-only. A later separately approved package in PR #50 added three ordering/selection regressions and the minimum current OpenCV runtime alignment needed to satisfy them. That package did not implement DocRes, ST Image AI, the Roadmap Stage 9 multi-engine comparator, ScoreMosaic runtime dispatch, model training, schema expansion, dependency changes, or production infrastructure.

This post-merge convergence update changes documentation only. It records the already-merged runtime state and does not authorize or implement any additional roadmap capability.
