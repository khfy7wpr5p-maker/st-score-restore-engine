# ADR 0025 — Stage 11 General-Clef Successor Architecture

Status: Accepted design; implementation not authorized by this ADR  
Date: 2026-09-26  
Tracking: Linear SES-19 / SES-24

## Context

Stage 11 clef closure remains incomplete. The frozen C-clef P4.14 candidate is a separate path and must remain unchanged. The remaining general-clef scope is treble, bass, TAB and soprano.

The historical 213-box source-only general-clef qualification artifact reported:

- TP = 3
- FP = 582
- FN = 210
- precision = 0.005128205128205128
- recall = 0.014084507042253521
- F1 = 0.007518796992481202

That artifact explicitly did not qualify the detector and did not authorize Stage 11 closure, production, or Stage 12 entry.

Fresh read-only audit found two distinct failure families that must not be collapsed into one explanation:

1. **Coordinate-space inconsistency signal.** Historical page records contain detector coordinates that are materially inconsistent with the teacher/source coordinate regime on multiple pages. Current branch code contains explicit model-output-to-source-image coordinate normalization and a regression test for that normalization. Therefore the historical 582 FP count must not be interpreted as a pure semantic-confusion taxonomy without a coordinate-corrected baseline.
2. **Semantically overbroad candidate generation.** The historical path consumes Oemer's combined `clefs_keys` segmentation channel, derives connected components, and then separates clefs from key-signature candidates largely with geometric rules. That is not a dedicated clef semantic channel. Staff topology, subtype evidence and explicit abstention are insufficient for the required general-clef contract.

Additional limitations are that soprano is not supported as an independent semantic subtype by the legacy general adapter, while TAB is handled by separate marker logic rather than one unified general-clef evidence contract.

The historical result remains rejected. This ADR does not reinterpret it as qualified evidence.

## Decision

Adopt **Hybrid Architecture C** for the next separately versioned general-clef successor.

The architecture is:

`source image -> staff topology -> deterministic high-recall candidate generation -> subtype evidence -> staff-relative semantic validation -> P4.14 collision handling -> duplicate suppression -> confidence/abstention -> stable clef evidence`

The first implementation version must not require a learned classifier. It must be able to operate with deterministic/template/shape evidence. A compact crop classifier may be introduced later only under a separately approved training scope, with its own frozen identity and qualification boundary.

This design is source-only and development-only until an implementation candidate is frozen and independently qualified.

## Development data and labels

The accepted 213 teacher boxes remain **development truth only**:

- treble: 165
- bass: 34
- TAB: 12
- soprano: 2
- total: 213

Required label/evidence fields for the successor design are:

- `clef_presence`
- `clef_type` in `treble | bass | tab | soprano | unknown`
- `staff_index`
- `bbox` in original source-image pixels
- `confidence`
- `abstain_reason`
- `candidate_provenance`

Teacher boxes, teacher subtype labels, page IDs, filenames and source-family identifiers may be used offline to construct development labels and diagnostics. They are forbidden as inference-time features.

Development negatives may come from the same approved development pages. Negative error taxonomy should distinguish at least:

- notehead/stem
- accidental/key-signature
- text
- barline
- ornament
- time/key-signature symbol
- staff fragment
- TAB digit/letter
- other

The historical artifact does not contain trustworthy counts for those categories, so no numeric historical taxonomy is claimed by this ADR.

## Staff-relative semantic contract

All geometry decisions must be normalized by staff spacing and staff topology rather than page-absolute proportions alone.

### Treble

Require five-line staff compatibility plus treble-specific normalized shape evidence. The detector must support both system-start and mid-staff clef changes. A rule equivalent to "only the left page region can contain a clef" is forbidden.

### Bass

Require five-line staff compatibility plus bass-body and two-dot relational evidence or an equivalently explicit subtype signature. Pure height/width acceptance is insufficient.

### TAB

Require six-line staff topology and positive TAB glyph/marker evidence together. Six-line topology alone cannot authorize TAB, and a TAB-like text component on a five-line staff must not be accepted.

### Soprano

Preserve soprano as an explicit semantic label rather than silently collapsing it into a generic C-clef label. Because the development set contains only two soprano examples, no standalone learned-generalization claim is permitted from those two examples.

## P4.14 coexistence

P4.14 is frozen and must not be retuned, rewritten or silently superseded by the general-clef successor.

When the successor and P4.14 refer to the same C-clef region:

- emit one localization result, not two;
- preserve the P4.14 localization authority;
- allow the successor to contribute `soprano` subtype only when its subtype evidence is independently qualified;
- otherwise preserve presence with `clef_type=unknown` or defer to review;
- record the collision/deference reason.

The successor must never convert a P4.14 detection into a negative result merely to improve its own subtype precision.

## Abstention contract

Required outcome states:

- `ACCEPT_TYPED`: clef presence and subtype are sufficiently supported.
- `ACCEPT_PRESENCE_ONLY`: clef presence is supported but subtype is not; emit `unknown`.
- `REVIEW_REQUIRED`: evidence is materially ambiguous.
- `ABSTAIN`: evidence is insufficient or invalid.
- `REJECT_NOT_CLEF`: candidate is rejected as non-clef.

Required abstention/review reasons include:

- `MULTI_CLASS_AMBIGUOUS`
- `TOPOLOGY_MISMATCH`
- `P4_14_COLLISION`
- `INVALID_GEOMETRY`
- `INSUFFICIENT_CLEF_EVIDENCE`

Coverage must never be increased by forcing a subtype when the subtype evidence does not clear its gate.

## Future RED-first TDD contract

Implementation is not part of this ADR, but a future implementation must begin with failing tests for at least the following invariants:

1. model-output coordinates are normalized back to original source-image pixels;
2. no emitted bbox may exceed source-image bounds;
3. same source/config produces byte-identical ordered output;
4. changing teacher metadata cannot change inference output;
5. changing filename, page ID or source-family name cannot change inference output;
6. scale changes preserve the same staff-relative semantic decision;
7. mid-staff clef changes are not suppressed by page-position heuristics;
8. five-line staff cannot be accepted as TAB and six-line topology alone cannot be accepted as TAB;
9. duplicate candidates collapse while distinct clefs remain distinct;
10. P4.14 collision produces one stable localization result;
11. negative pages do not produce high-confidence clefs;
12. ambiguous subtype evidence produces `unknown`, review or abstention rather than a forced class.

## Development freeze gates

The following values are accepted as **design targets for a future development freeze**. They are not qualification thresholds and do not authorize holdout access:

- pooled precision >= 0.90
- pooled recall >= 0.85
- treble recall >= 0.90
- bass recall >= 0.85
- TAB recall >= 0.80
- coordinate validity = 100%
- deterministic A/B output identity = 100%
- development negative specificity target = 100%

For soprano, percentage thresholds are not meaningful at development n=2. The development expectation is 2/2 correct behavior plus an explicit rare-class limitation. No generalization claim follows from that result.

A future freeze must bind:

- candidate/version identity
- exact source blob
- config and thresholds
- output schema
- deterministic A/B hashes
- development corpus identity
- development result artifact

No new independent holdout may be opened before those bindings are frozen.

## Independent qualification protocol

After a candidate and prequalification policy are frozen, a fresh qualification set must:

- be disjoint from the 213-box development corpus;
- not reuse spent P4.7 or P4.9 as qualification evidence;
- prefer new source families;
- contain treble, bass and TAB positives plus genuine negative pages;
- contain enough soprano examples to support any soprano qualification claim, otherwise soprano remains review/presence-only;
- bind exact source bytes before scoring;
- use teacher truth created independently of candidate predictions;
- run the exact frozen candidate and config;
- repeat deterministic A/B inference before truth is opened;
- perform one qualification decision after truth opening;
- prohibit threshold or model retuning after holdout results are observed.

A failed qualification requires a new development iteration and a newly defined future independent evaluation boundary.

## Evidence boundary

This ADR is a design decision only.

It does **not** authorize:

- production code changes;
- test/config changes outside a later explicitly approved implementation task;
- model training or fine-tuning;
- new holdout access;
- reuse of P4.7/P4.9 as future qualification evidence;
- modification of frozen P4.14;
- PR #211 merge;
- production promotion;
- Stage 11 closure;
- Stage 12 entry.

The general-clef successor remains unimplemented and unqualified after this ADR.

## Next safe boundary

Create a separately scoped implementation handoff that translates this accepted design into RED-first tests and a bounded development-only implementation plan. Do not start implementation until that implementation scope is explicitly approved.
