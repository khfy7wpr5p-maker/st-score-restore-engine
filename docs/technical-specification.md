# ST Score Restore Engine — Technical Specification

**Document status:** Approved architecture baseline; maintenance-aligned with Roadmap v0.2.4 and Stage 1C/C17  
**Version:** 0.2.4-aligned  
**Date:** 2026-08-26  
**Target repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Roadmap authority:** `docs/roadmap.md` v0.2.4  
**Current Stage 1 authority:** Issue #47 and `docs/stage-1c-current-status.md`  
**Primary language:** English identifiers and API contracts; Turkish-first teacher-facing messages may be added by clients.

---

## 1. Purpose

ST Score Restore Engine is an independent, safety-first service for improving scanned or photographed music documents without changing their musical meaning.

The engine is **not** an OMR system and does not convert notation to MusicXML. It does not provide MIDI playback, speech narration, pitch interpretation, rhythm interpretation, or music-theory correction. It prepares and validates visual document derivatives before an OMR, accessibility, or music-application workflow consumes them.

The long-term service boundary is intended to support:

- SesliTab Guitar Reader;
- MusicXML-to-Guitar TAB Engine;
- Cloud OMR Gateway;
- ScoreMosaic / Scremosaik;
- future accessible-music and OMR applications.

Those application integrations are deferred to Roadmap Stage 12. Their repositories are not part of this service and must not be modified by work in this repository unless Stage 12 receives separate authorization.

---

## 2. Authority, status vocabulary, and scope

This specification describes both the implemented baseline and the approved future target architecture. It does not authorize work outside the binding order in `docs/roadmap.md`.

Status labels used here are normative:

- **CURRENT:** implemented on `main` and covered by repository contracts;
- **PARTIAL:** a safe bounded subset exists, but the complete capability is not implemented;
- **DEFERRED — STAGE N:** approved future target architecture that may not begin before preceding roadmap gates are accepted;
- **NOT AUTHORIZED:** not approved as current trusted-path behavior.

A future component described here is not an implemented feature merely because its responsibilities are specified.

### 2.1 Binding development order

```text
Stage 1  Real and explicitly authorized test dataset
      ↓
Stage 2  Complete quality-analysis system
      ↓
Stage 3  Multi-page PDF pipeline
      ↓
Stage 4  Safety calibration with real data
      ↓
Stage 5  Accessible teacher review interface
      ↓
Stage 6  Identity, network and production infrastructure
      ↓
Stage 7  Preview release
      ↓
Stage 8  DocRes optional candidate
      ↓
Stage 9  Multi-engine comparator
      ↓
Stage 10 ST Restore Selector
      ↓
Stage 11 ST Restore image model
      ↓
Stage 12 Music-application integrations
```

Every implementation slice follows fresh-read → focused branch/PR → Draft → exact-head evidence → separate Ready-for-review gate → later exact-head merge gate. A later stage may not begin until the preceding stage's exit evidence is published and accepted.

### 2.2 Current Stage 1 state

Stage 1 is active under parent Issue #32 through gated substages.

- Stage 1A metadata governance is complete.
- Stage 1B custody/operations is formally closed through Issue #36.
- Stage 1C is active under Issue #47.

ADR 0016 risk-tiered custody is **implemented**. The obsolete pre-C6 statement that Stage 1A/1C still uses only legacy storage values no longer applies. Catalog schema `1.3.0`, deterministic eligibility/profile validation, and the C8-C11 operational/admission mechanisms are merged.

Current custody mapping:

- `open_corpus` → `managed_standard`;
- `restricted_corpus` → `managed_restricted` when exact artifact terms permit it;
- `sensitive_custody` → `high_assurance_vault`;
- unresolved/rejected/contradictory governance → `blocked`.

C12 and C14 realized two independently authorized real `open_corpus` items outside ordinary Git. C15 froze the resulting two-item corpus as a digest-addressed historical snapshot. C16 deterministically measured that exact snapshot and concluded `insufficient` for Stage 1 exit.

C17 corpus expansion is active. C17A / PR #68 is currently Draft. Its accepted taxonomy correction classifies the new Public Domain PNG only as `combined_staff_tab`; standalone `guitar_tab` remains a separate missing category. C17A does not mutate the historical C15/C16 snapshot. A future expanded corpus must use a new versioned snapshot and a fresh deterministic coverage evaluation.

A real user-provided phone photo remains blocked unless a real operational `high_assurance_vault` passes the accepted high-assurance evidence boundary. C10 structural compatibility is not operational vault verification.

Stage 2 remains blocked until Stage 1 exit passes.

---

## 3. Core safety objective

The primary objective is preservation of musical information, not visual beauty.

The following invariants apply to every current and future stage:

1. The original input is immutable.
2. Every output is a separate derivative artifact with a separate SHA-256 identity.
3. Music-score and guitar-TAB safety has veto priority over visual improvement.
4. A candidate rejected by the safety validator cannot be selected or approved.
5. Teacher approval, dataset inclusion, calibration permission, and model-training permission are separate decisions.
6. User documents are not dataset or training data without explicit purpose-specific authorization.
7. Missing, unsupported, or uncertain analysis must not be reported as safe.
8. Digital vector PDFs must not be rasterized implicitly.
9. Real student, teacher, private, or copyrighted document bytes must not be committed to ordinary Git.
10. DocRes and ST Restore models may only become optional candidates in their approved future stages.
11. A combined notation layout must not be counted as a separate standalone notation category unless the artifact independently contains that category.
12. Historical frozen dataset evidence must not be rewritten to hide later coverage gaps or later corpus expansion.

A restoration is acceptable only when it improves readability or downstream recognition while preserving, within documented tolerances:

- page identity, order, dimensions, orientation;
- staff and TAB system geometry;
- staff-line and TAB-line counts;
- noteheads, stems, flags, beams, augmentation dots, ties, slurs, rests;
- accidentals, clefs, key signatures, time signatures;
- barlines, repeat marks, volta brackets;
- TAB digits and positions;
- guitar technique markings;
- lyrics, fingering, dynamics, chord symbols, instructional text;
- relationships between notation and TAB systems.

No current component claims semantic certainty about pitch, rhythm, fingering, or TAB digit identity.

---

## 4. Repository and service boundary

ST Score Restore Engine remains a separate repository and future deployable service.

```text
SesliTab Guitar Reader ───────┐
MusicXML-to-Guitar Engine ────┤
Cloud OMR Gateway ────────────┼── versioned API ── ST Score Restore Engine
ScoreMosaic / Scremosaik ─────┘
```

Client applications will submit documents and retrieve approved derivatives through versioned contracts. They must not import or copy restoration implementation details.

This boundary isolates:

- computer-vision and future model dependencies;
- CPU/GPU execution requirements;
- model licensing/versioning;
- storage and retention controls;
- experimental candidate failures;
- document privacy/audit responsibilities.

The current built-in HTTP adapter is a non-production local development boundary and is not approved for exposure to an untrusted network.

---

## 5. Current implemented baseline

### 5.1 Immutable input inspection — CURRENT

- PDF, JPEG/JPG, and PNG content-signature detection;
- immutable SHA-256 source identity;
- bounded byte-size handling;
- malformed, encrypted, unsupported, symlinked, and changing-input rejection;
- limited PDF structural evidence and conservative digital/scanned/hybrid/unknown classification;
- JPEG/PNG dimensions, density evidence, and EXIF-orientation metadata;
- explicit `not_assessed` quality states when approved pixel analysis is unavailable;
- vector-PDF preservation recommendation instead of implicit rasterization.

The current inspector is not a complete PDF parser, renderer, or quality-analysis engine.

### 5.2 Deterministic OpenCV safe restoration — CURRENT FOR JPEG/PNG RASTER INPUTS

- deterministic, non-generative image restoration;
- separate source and candidate identities;
- bounded decoding and decoded-pixel limits;
- EXIF-orientation normalization in derivative coordinates;
- confidence-gated geometry operations;
- conservative illumination, denoise, contrast, and optional binarization profiles;
- dark-structure preservation checks;
- operation manifest/audit evidence;
- immutable-original fallback.

The OpenCV engine does not render arbitrary PDF pages. Digital PDFs are not silently rasterized. Scanned/hybrid PDF restoration remains deferred to Stage 3.

### 5.3 Music-score and guitar-TAB safety validator — CURRENT

- deterministic source/candidate registration;
- separate staff and TAB geometry checks;
- expected five-line staff and six-line TAB checks;
- system-count and line-break risk detection;
- local dark-pixel loss/invention measurements;
- component loss, invention, and movement checks;
- page-region findings with `semanticCertainty: not_claimed`;
- `pass`, `review_required`, and `reject` verdicts;
- unknown/unrecognized geometry routed to review rather than reported safe;
- rejected candidates excluded from selection;
- immutable-original fallback.

The validator is not OMR, OCR, MusicXML interpretation, or semantic notation recognition.

### 5.4 Candidate selection baseline — CURRENT, NOT STAGE 9

The current workflow can compare validated candidates sharing the same immutable source and order them using validator verdict and measured risk. This bounded safety-oriented ordering exists to prevent caller-supplied ranking from bypassing validation.

It is not the Roadmap Stage 9 multi-engine comparator. It does not yet provide:

- calibrated cross-engine visual-quality normalization;
- OpenCV-versus-DocRes benchmarking;
- multi-engine recommendation confidence;
- complete disagreement handling;
- Stage 4 real-data-calibrated ranking;
- a production recommendation policy.

### 5.5 Versioned job and teacher-review workflow — CURRENT, NON-PRODUCTION

- `/api/v1`, current API version `0.5.0`;
- asynchronous job states and immutable retry attempts;
- idempotent ordered uploaded-page records;
- page analysis, candidate, safety report, artifact, status, and audit access;
- page-level approve/reject/reprocess decisions;
- immutable-original fallback;
- teacher approval separated from training-consent records;
- retention expiry and audit tombstones;
- immutable reviewer evidence bundles;
- stale-screen evidence binding on teacher decisions.

Normative current HTTP contracts are `api/openapi.v1.json`, `docs/job-api-and-teacher-review.md`, and `docs/review-evidence-contract.md`.

No automatic teacher approval is implemented or authorized. A machine verdict may constrain or reject a candidate, but it does not substitute for teacher approval.

### 5.6 Local persistence and worker safety — CURRENT, NON-PRODUCTION

- in-memory storage by default;
- optional local SQLite metadata/audit storage;
- content-addressed local blob storage;
- transaction rollback and startup integrity verification;
- attempt-bound worker leases/fencing;
- expired in-flight recovery from immutable source bytes;
- bounded local concurrency regressions;
- idempotent cleanup and pending-deletion recovery.

This is not encrypted cloud object storage, an external broker, a production database, a backup system, or distributed production coordination.

### 5.7 Local HTTP and multipart boundary — CURRENT, NON-PRODUCTION

- strict bounded HTTP/1.1 request grammar;
- duplicate/ambiguous framing rejection;
- route-specific body limits;
- strict multipart parsing and binary-byte preservation;
- connection timeout/concurrency limits;
- structured errors without document-content leakage;
- one request per connection.

TLS, trusted-proxy policy, production rate limiting, WAF compatibility, penetration testing, and public exposure remain Stage 6 work.

### 5.8 Immutable review evidence — CURRENT, UI DEFERRED

- deterministic source/candidate grayscale crops for validator findings;
- source-space and normalized overlay coordinates;
- transform provenance;
- reviewer-only evidence access;
- evidence-bundle identity required for teacher decisions;
- stale-screen conflict handling;
- retry/retention behavior.

A complete accessible browser interface, screen-reader verification, keyboard-only usability testing, color-management validation, and display QA remain Stage 5 work.

---

## 6. Current trusted processing flow

```text
PDF / JPEG / PNG immutable source
      ↓
Read-only input inspection and SHA-256 identity
      ↓
┌──────────────────────────────────────────────────────────────┐
│ Digital vector PDF: preserve; do not rasterize implicitly    │
│ JPEG/PNG raster page: eligible for deterministic OpenCV      │
│ Scanned/hybrid PDF: no full renderer; review/defer safely    │
└──────────────────────────────────────────────────────────────┘
      ↓
Deterministic OpenCV candidate when supported
      ↓
Music-score and TAB safety validation
      ├── reject: candidate cannot be used
      └── pass/review_required: evidence remains available
      ↓
Immutable review-evidence bundle
      ↓
Explicit teacher approve / reject / reprocess decision
      ↓
Separate derivative artifact or immutable-original fallback
      ↓
Append-only audit evidence
```

There is no DocRes candidate, ST Restore candidate, Stage 9 multi-engine comparator, automatic teacher approval, full multi-page PDF export assembly, production identity, or production deployment in this flow.

---

## 7. Input support and document classes

### 7.1 Current accepted inspection formats

- PDF;
- JPG/JPEG;
- PNG.

Phone-captured photographs are represented as JPEG or PNG inputs, but admitting a real phone photograph into the Stage 1 corpus is a separate governance/custody decision.

### 7.2 TIFF status

TIFF and multi-page TIFF are **DEFERRED**. Supporting TIFF requires separately approved decoder/dependency/license review, resource limits, security review, and roadmap placement.

### 7.3 Current document classification limits

The current inspector can emit conservative evidence-based classifications for PDF input and metadata for image input. It does not yet provide the complete calibrated page classifier defined for Stage 2.

Target page classes remain:

- `VECTOR_DIGITAL`;
- `SCANNED_RASTER`;
- `HYBRID`;
- `CAMERA_PHOTO`;
- `UNKNOWN`.

Until Stage 2 is complete, uncertain or unsupported classification remains explicit and must not be treated as safe.

### 7.4 Input limits

Current code enforces bounded upload/request/image-byte/decoded-pixel limits. Production deployments must later define and test maximum file size, page count, rendered pixels, decompressed size, MIME types, retention duration, concurrent CPU/GPU limits, tenant quotas, and abuse controls.

---

## 8. Stage 1 dataset, custody, and evidence boundary

### 8.1 Risk-tiered custody — CURRENT

ADR 0016 supersedes the old universal `custody_external`/offline-vault rule for all artifact classes. The legacy C4 `custody_external` evidence value is preserved only as the historical high-assurance evidence format behind the one-way compatibility mapping:

```text
sensitive_custody
      ↓
high_assurance_vault
      ↓
legacy C4 evidence
(storageClass = custody_external)
```

Legacy C4 evidence must never be reinterpreted as proof for `managed_standard` or `managed_restricted`.

### 8.2 Stage 1C profile/admission machinery — CURRENT

Merged mechanisms include:

- catalog `1.3.0` profile vocabulary and eligibility class;
- deterministic eligibility resolver;
- `managed_standard` operational verification;
- `managed_restricted` operational verification;
- high-assurance compatibility verification;
- deterministic artifact admission gate.

A passing profile record proves only the profile-level operational condition it represents. It does not independently grant exact-artifact rights, privacy approval, dataset review, purpose, split membership, publication, training, or Stage 2 authorization.

### 8.3 Realized and frozen historical corpus — CURRENT EVIDENCE

C12 and C14 admit two independent Public Domain scanned-PDF items using `managed_standard` outside ordinary Git. C15 freezes them into the historical Stage 1C snapshot with source-family/digest isolation between development and held-out.

The C15 snapshot is an integrity result, not a representativeness result.

C16 derives metadata-only coverage evidence from that frozen snapshot:

- 2 real items / 12 pages;
- 1 development item / 4 pages;
- 1 held-out item / 8 pages;
- 2 staff-notation items;
- 0 standalone guitar-TAB items;
- 0 combined staff/TAB items;
- 0 phone-photo items;
- 0 items with non-`none` degradation metadata.

C16 conclusion: **`insufficient`**.

### 8.4 C17 expansion — CURRENT ACTIVE WORK

C17 must address missing categories using independently authorized artifacts without mutating C15. C17A / PR #68 is Draft and currently covers only `combined_staff_tab` after the accepted review correction. Its artifact is not standalone `guitar_tab` and must not satisfy that gap.

A future expanded corpus requires:

1. item-level admission under existing gates;
2. source-family-safe split assignment;
3. a new versioned snapshot;
4. a new deterministic coverage/bias evaluation;
5. dataset-card/exit-evidence reconciliation.

### 8.5 Sensitive/phone-photo boundary

A real user-provided phone image maps to `sensitive_custody` unless independent evidence establishes a different admissible classification. `sensitive_custody` requires a real operational `high_assurance_vault` pass. C10's structural compatibility record intentionally has no power to claim `realVaultVerified=true` or authorize artifact onboarding.

Synthetic degradation or relabeling of a scan as a phone photo must not be used to fabricate real coverage.

---

## 9. Future stages and target components

### 9.1 Stage 2 — Complete quality analysis — DEFERRED

Target capabilities:

- vector/scanned/hybrid/photo classification confidence;
- dimensions/orientation/DPI evidence;
- skew/perspective estimates with uncertainty;
- page-boundary confidence;
- motion/defocus blur;
- glare/specular highlights;
- shadow/illumination non-uniformity;
- local/global contrast;
- background/paper-aging indicators;
- compression artifacts/noise/clipping/saturation;
- notation scale and staff/TAB line-thickness indicators;
- deterministic metric versions/failure states;
- per-page and document-level reports;
- measurement against the authorized Stage 1 corpus.

Current metadata checks and `not_assessed` findings do not satisfy Stage 2.

### 9.2 Stage 3 — Multi-page PDF renderer/export — DEFERRED

Target responsibilities:

- reviewed `PdfBackend` and explicit renderer dependency/license decision;
- bounded deterministic page rendering;
- encrypted/malformed/oversized PDF handling;
- stable page identity/order;
- vector/scanned/hybrid per-page policy;
- vector pass-through unless explicit rasterization authorized;
- page-level analysis/restoration/validation/evidence lifecycle;
- partial-page failure with original fallback;
- deterministic PDF reassembly;
- page box/orientation/size/order preservation;
- multi-page retry/cancellation/retention/audit behavior.

No `pypdfium2`, `pikepdf`, QPDF, PyMuPDF, or equivalent dependency is selected merely by this specification.

### 9.3 Stage 4 — Safety calibration — DEFERRED

Requires separate staff/TAB evaluation, controlled structural mutations, real unchanged pairs, false-negative/false-positive/review-rate measurement, held-out isolation, degradation/page-class stratification, and reproducible rollbackable threshold reports. Current synthetic regressions are not real-data calibration.

### 9.4 Stage 5 — Accessible teacher review UI — DEFERRED

Requires source/candidate comparison, risk overlays, page/finding navigation, bounded zoom, keyboard-only actions, screen-reader semantics, focus/error recovery, stale-screen handling, contrast/responsive behavior, display integrity/color management, and recorded accessibility results.

### 9.5 Stage 6 — Production identity/network/infrastructure — DEFERRED

Requires production identity/ownership, TLS/proxy policy, secret rotation, encrypted object storage, production database/external queue, distributed coordination, backup/restore, observability, quotas/abuse controls, threat model/security review, load/race tests, deployment/rollback/incident runbooks.

### 9.6 Stage 7 — Preview — DEFERRED

The initial preview uses deterministic OpenCV plus explicit teacher review. It excludes DocRes, Selector, and ST Restore image model.

### 9.7 Stage 8 — DocRes optional candidate — DEFERRED

DocRes may be evaluated only after the deterministic Stage 7 preview baseline is frozen. Code/weights require license review, exact checksum/provenance, isolated execution, resource limits, disable switch, output normalization, and the same safety/review boundary as OpenCV.

### 9.8 Stage 9 — Multi-engine comparator — DEFERRED

Future comparator ranks immutable original, OpenCV, and approved optional candidates using normalized quality, structural-change evidence, hard safety vetoes, deterministic ranking, explainable recommendations, disagreement/no-safe-candidate outcomes, and teacher override evidence. Original may win.

### 9.9 Stage 10 — ST Restore Selector — DEFERRED

A project-owned learning component may recommend engines/profiles but does not generate pixels. It requires explicit training permission, offline reproducible training, shadow-mode evaluation, registry/model card/rollback, disagreement analysis, no online self-training, and safe fallback for uncertainty.

### 9.10 Stage 11 — ST Restore image model — DEFERRED

Permitted research may include shadow reduction, illumination normalization, conservative deblurring, background cleanup, noise reduction, and bounded thin-line enhancement.

Prohibited behavior includes filling missing notation, guessing unreadable TAB digits, generative reconstruction in symbol regions, theory correction, or changing symbol placement.

### 9.11 Stage 12 — Music-application integrations — DEFERRED

Applications integrate through versioned contracts/feature flags. Restoration logic is not copied into client repositories. Downstream OMR effectiveness is measured separately from visual quality/safety.

---

## 10. Target component architecture

### 10.1 API gateway

- **CURRENT:** bounded non-production `/api/v1` adapter with development roles and strict local HTTP/multipart handling.
- **DEFERRED — STAGE 6:** production identity, ownership, TLS, proxy policy, quotas, signed/authenticated delivery, operational controls.

### 10.2 Job manager

- **CURRENT:** append-only job states, immutable attempts, retry, cancellation, review, expiry, local persistence, local worker fencing.
- **DEFERRED — STAGE 6:** external durable queue, production database, distributed claims, failover, production recovery objectives.

Canonical flow remains:

```text
UPLOADED
  → ANALYZING
  → READY_FOR_PROCESSING
  → PROCESSING
  → COMPARING
  → VALIDATING
  → AWAITING_REVIEW
  → APPROVED
  → EXPORTING
  → COMPLETED
```

Alternate/terminal states:

```text
REJECTED
FAILED
CANCELLED
EXPIRED
```

A cancelled or failed attempt cannot silently resume; retry creates a new attempt identity.

### 10.3 Input integrity service

- **CURRENT:** SHA-256 identity, signature checks, metadata inspection, bounded reads, stable rejection codes, conservative PDF evidence.
- **DEFERRED — STAGE 3/6:** full renderer-backed PDF handling, production malware controls, tenant storage policy, deployment-scale decompression defenses.

### 10.4 PDF inspector/renderer/exporter

- **CURRENT:** read-only limited PDF inspection and vector-preservation recommendation.
- **DEFERRED — STAGE 3:** approved `PdfBackend`, deterministic rendering, page lifecycle, vector pass-through, PDF reassembly/export.

### 10.5 Document quality analyzer

- **PARTIAL:** metadata-derived and explicitly unassessed findings.
- **DEFERRED — STAGE 2:** complete deterministic metrics, uncertainty, evaluation, document-level reports.

### 10.6 Music structure/protection logic

- **CURRENT:** conservative staff/TAB geometry and component-risk measurements plus dark-structure preservation.
- **FUTURE:** richer versioned protection masks only in approved stages and never weakening validator vetoes.

### 10.7 Restoration engines

- **CURRENT:** deterministic OpenCV safe restoration.
- **DEFERRED — STAGE 8:** DocRes optional candidate.
- **DEFERRED — STAGE 11:** ST Restore image-model optional candidate.

### 10.8 Comparator/selector

- **CURRENT:** bounded same-source validator-based safety ordering.
- **DEFERRED — STAGE 9:** calibrated multi-engine comparator.
- **DEFERRED — STAGE 10:** learned ST Restore Selector.

### 10.9 Teacher review/evidence

- **CURRENT:** backend review service, immutable evidence bundles, stale-screen binding, separate training-consent records, append-only audit.
- **DEFERRED — STAGE 5:** accessible browser UI/display QA.
- **DEFERRED — STAGE 6:** production identity/resource ownership.

### 10.10 Storage/cleanup

- **CURRENT RUNTIME:** in-memory default plus optional local SQLite metadata/content-addressed blobs for non-production service operation.
- **CURRENT STAGE 1 DATASET GOVERNANCE:** artifact-risk-specific external custody under ADR 0016; real corpus bytes remain outside ordinary Git.
- **DEFERRED — STAGE 6:** production encrypted object storage, database, backup/restore, data residency, secure deletion, monitoring.

---

## 11. API contract boundary

All current endpoints are versioned under `/api/v1`; current API version is `0.5.0`.

Normative contracts:

- `api/openapi.v1.json`;
- `docs/job-api-and-teacher-review.md`;
- `docs/review-evidence-contract.md`;
- `docs/http-transport-and-multipart-security.md`.

Current API safety rules include:

- original artifacts immutable;
- uploaded pages retain stable order/identity;
- candidates/reports have separate identities;
- rejected candidates cannot be approved;
- reviewer evidence required for teacher decisions;
- stale evidence causes conflict instead of a decision;
- approved-candidate download blocked before approval;
- training consent recorded separately;
- expiry deletes bytes according to current retention behavior while retaining audit tombstone.

The ordered multi-page upload abstraction must not be described as arbitrary multi-page PDF rendering/export assembly.

---

## 12. Data, learning, and model governance

Evaluation, calibration, training, publication, demonstration, and synthetic derivation are distinct purposes. Permission for one does not imply another.

Teacher approval of a restoration does not imply dataset inclusion, calibration permission, training permission, publication permission, or demonstration permission.

### 12.1 Current Stage 1 data state

The historical C15 Stage 1 snapshot contains two real, externally retained Public Domain scanned-PDF items / 12 pages with source-family-isolated development and held-out assignments. Real artifact bytes are not stored in ordinary Git.

C16 measured that frozen snapshot and concluded `insufficient`. C17 is expanding the corpus under the same fail-closed admission rules. No current Stage 1 evidence authorizes model training or safety/quality calibration.

### 12.2 Local drill boundary

Historical Stage 1B project-authored non-musical marker drills do not constitute Stage 1 corpus data. The earlier Windows 7 high-assurance-vault assessment failed because the inspected host was unsupported/unencrypted. That remains relevant only to a proposed `high_assurance_vault`; it is not a universal blocker for independently verified `open_corpus` / `managed_standard` artifacts.

### 12.3 Future learning loop

```text
Purpose-authorized examples
      ↓
Curated versioned dataset and frozen splits
      ↓
Offline training
      ↓
Independent regression and safety evaluation
      ↓
Shadow deployment
      ↓
Explicit release approval
      ↓
Immutable model release with rollback
```

Prohibited:

- online weight updates in production request path;
- training on files without explicit training permission;
- using teacher approval as blanket training consent;
- tuning on held-out set;
- replacing model versions without regression evidence/rollback;
- autonomous learning from user uploads.

---

## 13. Security and privacy status

### 13.1 Current local service controls

- bounded request/image sizes;
- strict multipart parsing;
- static development client/reviewer keys;
- local artifact-role checks;
- append-only audit evidence;
- local private file modes where supported;
- no document content in ordinary structured errors;
- no implicit outbound model network access because no model worker exists.

### 13.2 Stage 1 dataset controls

- exact-artifact rights/provenance binding;
- privacy classification;
- purpose-specific authorization;
- dataset review;
- retention/revocation semantics;
- exact digest/byte-size identity;
- risk-tiered custody outside ordinary Git;
- provider details represented by approved opaque references in repository-visible evidence;
- fail-closed admission when required evidence is missing or contradictory.

### 13.3 Deferred production controls

Stage 6 includes encrypted transport/trusted-proxy policy, approved identity provider, cross-tenant ownership, encrypted object storage, secret manager/rotation, external durable queue, production database, backups/disaster recovery, WAF/reverse-proxy validation, penetration testing, observability, and public-exposure approval.

Document contents must not appear in ordinary application logs.

---

## 14. Testing and evidence strategy

### 14.1 Current repository verification

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

CI validates Python 3.11 and 3.12.

### 14.2 Current test-data boundary

- generated in-memory synthetic inputs are permitted for deterministic unit/regression tests;
- project-authored non-sensitive marker bytes may be used for bounded local operational drills without constituting corpus data;
- real Stage 1 corpus bytes remain outside ordinary Git;
- repository-visible real-corpus evidence is metadata/opaque-reference based;
- synthetic/local drill evidence is not a substitute for real item authorization or real category coverage.

### 14.3 Frozen and expanding corpus evidence

C15/C16 is the immutable historical baseline. C17 additions are not retroactively added to it. Once C17 has enough independently admitted material, a new snapshot version must be created and checked deterministically before new coverage claims are made.

Golden-image, restoration-effectiveness, OMR-improvement, or musical-correctness claims require separately authorized evidence and cannot be inferred from metadata coverage alone.

---

## 15. Release boundaries

### 15.1 Current baseline

Non-production development system suitable for repository-level deterministic testing and bounded local workflow validation.

### 15.2 Preview — Stage 7

Authorized only after Stages 1-6 are accepted. Uses deterministic OpenCV and explicit teacher review; excludes DocRes/Selector/ST Restore image model initially.

### 15.3 AI candidate releases

- DocRes begins only at Stage 8.
- Multi-engine comparator begins only at Stage 9.
- ST Restore Selector begins only at Stage 10.
- ST Restore image model begins only at Stage 11.

Every AI component remains optional, disableable, versioned, reversible, and subordinate to safety validation and teacher review.

---

## 16. Technology and licensing status

### 16.1 Current runtime dependencies

- Python 3.12 primary runtime with Python 3.11 compatibility validation;
- NumPy;
- `opencv-python-headless`;
- exact versions controlled by `requirements.lock` and repository validators.

### 16.2 Deferred technology candidates

Future candidates only, not selected by this specification:

- `pypdfium2` / PDFium for Stage 3 rendering;
- `pikepdf` / QPDF for Stage 3 structure/export;
- PyMuPDF only after explicit AGPL/commercial-license decision;
- typed production HTTP framework in Stage 6;
- PostgreSQL or equivalent production metadata store in Stage 6;
- encrypted object storage/external queue in Stage 6;
- ONNX Runtime or another approved runtime for Stage 10/11 models;
- DocRes code/weights in Stage 8.

No dependency may be added without scope authorization, license review, security review, version pinning, and repository validation.

This section is an engineering constraint, not legal advice.

---

## 17. Non-goals and prohibited trusted-path behavior

The trusted path shall not:

- invent or reconstruct missing notes;
- guess unreadable TAB digits;
- perform generative inpainting inside notation regions;
- correct music theory;
- modify pitches, durations, or fingering;
- convert PDF to MusicXML;
- act as an OMR engine;
- provide MIDI playback or speech narration;
- infer teacher approval from a machine verdict;
- infer training consent from teacher approval/evaluation permission;
- continuously retrain from production data;
- overwrite the source;
- rasterize digital vector PDFs implicitly;
- use rejected candidates;
- treat unsupported analysis as safe;
- expose the built-in HTTP adapter publicly;
- treat combined staff/TAB as standalone TAB without evidence;
- rewrite frozen historical corpus evidence to claim later coverage;
- fabricate phone-photo/degraded-source coverage using synthetic relabeling;
- activate DocRes, Stage 9 comparator, Selector, or ST Restore image model before their roadmap gates.

Future experimental research, if separately approved, remains isolated from the trusted path and disabled by default.

---

## 18. References

Repository-authoritative references:

- `README.md`
- `docs/roadmap.md`
- `docs/stage-1c-current-status.md`
- `docs/stage-1-dataset-card.md`
- `docs/stage-1-coverage-and-bias-register.md`
- `docs/stage-1-exit-evidence.md`
- `docs/adr/0015-restoration-pipeline-validation-comparator-handoff.md`
- `docs/adr/0016-stage-1c-risk-tiered-artifact-custody.md`
- `docs/stage-1c-storage-profile-policy.md`
- `docs/stage-1c-artifact-admission-contract.md`
- `docs/stage-1c-high-assurance-compatibility-contract.md`
- `docs/stage-1b-custody-operations-contract.md`
- `docs/stage-1b-closure-evidence.md`
- `api/openapi.v1.json`
- `docs/job-api-and-teacher-review.md`
- `docs/review-evidence-contract.md`
- `docs/durable-local-persistence.md`
- `docs/multi-worker-concurrency-and-recovery.md`
- `docs/http-transport-and-multipart-security.md`
- `docs/fixture-governance.md`
- `docs/input-inspection-contract.md`
- `docs/safe-restoration-baseline.md`
- `docs/music-safety-validator.md`
- Issue #32
- Issue #36
- Issue #47

External references are informative only and do not authorize dependencies or implementation.
