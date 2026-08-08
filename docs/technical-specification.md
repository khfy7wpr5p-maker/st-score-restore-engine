# ST Score Restore Engine — Technical Specification

**Document status:** Approved architecture baseline, maintenance-aligned with Roadmap v0.2.1  
**Version:** 0.2.1-aligned  
**Date:** 2026-08-08  
**Target repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Roadmap authority:** `docs/roadmap.md` v0.2.1 and PR #33 sequence authority  
**Primary language:** English identifiers and API contracts; Turkish-first teacher-facing messages may be added by clients.

---

## 1. Purpose

ST Score Restore Engine is an independent, safety-first service for improving scanned or photographed music documents without changing their musical meaning.

The engine is not an OMR system and does not convert notation to MusicXML. It does not provide MIDI playback, speech narration, pitch interpretation, rhythm interpretation, or music-theory correction. It prepares and validates visual document derivatives before an OMR, accessibility, or music-application workflow consumes them.

The long-term service boundary is intended to support:

- SesliTab Guitar Reader,
- MusicXML-to-Guitar TAB Engine,
- Cloud OMR Gateway,
- ScoreMosaic / Scremosaik,
- future accessible-music and OMR applications.

Those application integrations are deferred to Roadmap Stage 12. Their repositories are not part of this service and must not be modified by work in this repository unless Stage 12 receives separate approval.

---

## 2. Authority, status vocabulary, and scope

This specification describes both the implemented baseline and the approved future target architecture. It does not authorize work outside the binding order in `docs/roadmap.md`.

The following status labels are normative in this document:

- **CURRENT:** implemented on `main` and covered by the current repository contracts.
- **PARTIAL:** a safe bounded subset exists, but the complete capability is not implemented.
- **DEFERRED — STAGE N:** approved future target architecture that may not begin before the preceding roadmap gates are accepted.
- **NOT AUTHORIZED:** not approved as a current or future trusted-path behavior.

A future component described here is not an implemented feature merely because its responsibilities are specified.

### 2.1 Binding development order

The Roadmap v0.2 order is binding:

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

Each stage requires explicit approval before work begins and separate approval before merge. A later stage may not begin until the previous stage's exit evidence is published and accepted.

**Stage 1 is active under parent Issue #32 through explicit gated substages. Stage 1A metadata governance is complete. Stage 1B custody/operations implementation and acceptance-status changes are merged, while Issue #36 remains the formal closure record until all stated exit evidence is satisfied. Stage 1C artifact onboarding has not started and is not authorized.** This maintenance revision does not collect data, create dataset artifacts, change fixture permissions, or authorize Stage 1C.

---

## 3. Core safety objective

The primary objective is not visual beauty. The primary objective is preservation of musical information.

The following invariants apply to every current and future stage:

1. The original input is immutable.
2. Every output is a separate derivative artifact with a separate SHA-256 identity.
3. Music-score and guitar-TAB safety has veto priority over visual improvement.
4. A candidate rejected by the safety validator cannot be selected or approved.
5. Teacher approval, dataset inclusion, calibration permission, and model-training permission are separate decisions.
6. User documents are not dataset or training data without explicit, purpose-specific authorization.
7. Missing, unsupported, or uncertain analysis must not be reported as safe.
8. Digital vector PDFs must not be rasterized implicitly.
9. Real student, teacher, private, or copyrighted document bytes must not be committed to ordinary Git.
10. DocRes and ST Restore models may only become optional candidates in their approved future stages; they may not replace the OpenCV baseline by implication.

A restoration is acceptable only when it improves readability or downstream recognition while preserving, within documented tolerances:

- page identity, page order, dimensions, and orientation,
- staff and TAB system geometry,
- staff-line and TAB-line counts,
- noteheads, stems, flags, beams, augmentation dots, ties, slurs, and rests,
- accidentals, clefs, key signatures, and time signatures,
- barlines, repeat marks, and volta brackets,
- TAB digits and their positions,
- guitar technique markings,
- lyrics, fingering, dynamics, chord symbols, and instructional text,
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

- computer-vision and future model dependencies,
- CPU/GPU execution requirements,
- model licensing and versioning,
- storage and retention controls,
- experimental candidate failures,
- document privacy and audit responsibilities.

The current built-in HTTP adapter is a non-production local development boundary. It is not approved for exposure to an untrusted network.

---

## 5. Current implemented baseline

The following capabilities are implemented on `main`.

### 5.1 Immutable input inspection — CURRENT

- PDF, JPEG/JPG, and PNG content-signature detection,
- immutable SHA-256 source identity,
- bounded byte-size handling,
- malformed, encrypted, unsupported, symlinked, and changing-input rejection,
- limited PDF structural evidence and conservative digital/scanned/hybrid/unknown classification,
- JPEG/PNG dimensions, density evidence, and EXIF-orientation metadata,
- explicit `not_assessed` quality states when approved pixel analysis is unavailable,
- vector-PDF preservation recommendation rather than implicit rasterization.

The current inspector is not a complete PDF parser, renderer, or quality-analysis engine.

### 5.2 Deterministic OpenCV safe restoration — CURRENT FOR JPEG/PNG RASTER INPUTS

- deterministic, non-generative image restoration,
- separate source and candidate identities,
- bounded decoding and decoded-pixel limits,
- EXIF-orientation normalization in the derivative coordinate system,
- confidence-gated geometry operations,
- conservative illumination, denoise, contrast, and optional binarization profiles,
- dark-structure preservation checks,
- operation manifest and audit evidence,
- immutable-original fallback.

The OpenCV engine does not render arbitrary PDF pages. Digital PDFs are not silently rasterized. Scanned and hybrid PDF restoration remains blocked until Stage 3.

### 5.3 Music-score and guitar-TAB safety validator — CURRENT

- deterministic source/candidate registration,
- separate staff and TAB geometry checks,
- expected five-line staff and six-line TAB checks,
- system-count and line-break risk detection,
- local dark-pixel loss and invention measurements,
- component loss, invention, and movement checks,
- page-region findings with `semanticCertainty: not_claimed`,
- `pass`, `review_required`, and `reject` verdicts,
- unknown or unrecognized geometry routed to review rather than reported safe,
- rejected candidates excluded from selection,
- immutable-original fallback.

The validator is not OMR, OCR, MusicXML interpretation, or semantic notation recognition.

### 5.4 Candidate selection baseline — CURRENT, NOT STAGE 9

The current workflow can compare validated candidates that share the same immutable source and can order them using validator verdict and measured risk. This bounded safety-oriented ordering exists to prevent caller-supplied ranking from bypassing validation.

It is **not** the Roadmap Stage 9 multi-engine comparator. It does not yet provide:

- calibrated cross-engine visual-quality normalization,
- OpenCV-versus-DocRes benchmarking,
- multi-engine recommendation confidence,
- complete disagreement handling,
- Stage 4 real-data-calibrated ranking,
- a production recommendation policy.

Stage 9 remains deferred until Stage 8 supplies versioned DocRes candidate results after the preview baseline.

### 5.5 Versioned job and teacher-review workflow — CURRENT, NON-PRODUCTION

- `/api/v1`, current API version `0.5.0`,
- asynchronous job states and immutable retry attempts,
- idempotent ordered uploaded-page records,
- page analysis, candidate, safety-report, artifact, status, and audit access,
- page-level approve, reject, and reprocess decisions,
- immutable-original fallback,
- teacher approval separated from training-consent records,
- retention expiry and audit tombstones,
- immutable reviewer evidence bundles,
- stale-screen evidence binding on teacher decisions.

The normative current HTTP contract is `api/openapi.v1.json` together with `docs/job-api-and-teacher-review.md` and `docs/review-evidence-contract.md`. Historical examples in this document must not override those files.

No automatic teacher approval is implemented or authorized. A machine safety verdict may constrain or reject a candidate, but it does not substitute for teacher approval in the current workflow.

### 5.6 Local persistence and worker safety — CURRENT, NON-PRODUCTION

- in-memory storage by default,
- optional local SQLite metadata and audit storage,
- content-addressed local blob storage,
- transaction rollback and startup integrity verification,
- attempt-bound worker leases and fencing,
- expired in-flight recovery from immutable source bytes,
- bounded local concurrency regressions,
- idempotent cleanup and pending-deletion recovery.

This is not encrypted cloud object storage, an external broker, a production database, a backup system, or distributed production coordination.

### 5.7 Local HTTP and multipart boundary — CURRENT, NON-PRODUCTION

- strict bounded HTTP/1.1 request grammar,
- duplicate and ambiguous framing rejection,
- route-specific body limits,
- strict multipart parsing and binary-byte preservation,
- connection timeout and concurrency limits,
- structured errors without document-content leakage,
- one request per connection.

TLS, trusted-proxy policy, production rate limiting, WAF compatibility, penetration testing, and public exposure remain Stage 6 work.

### 5.8 Immutable review evidence — CURRENT, UI DEFERRED

- deterministic source/candidate grayscale crops for validator findings,
- source-space and normalized overlay coordinates,
- transform provenance,
- reviewer-only evidence access,
- evidence-bundle identity required for teacher decisions,
- stale-screen conflict handling,
- retry and retention behavior.

A complete accessible browser interface, screen-reader verification, keyboard-only usability testing, color-management validation, and display QA remain Stage 5 work.

---

## 6. Current trusted processing flow

The implemented trusted path is intentionally narrower than the future target architecture.

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

- PDF,
- JPG/JPEG,
- PNG.

Phone-captured photographs are represented as JPEG or PNG inputs.

### 7.2 TIFF status

TIFF and multi-page TIFF are **DEFERRED**. They are not current accepted formats and are not authorized merely by this target specification. Supporting TIFF would require a separately approved decoder, dependency/license review, resource limits, security review, and roadmap placement.

### 7.3 Current document classification limits

The current inspector can emit conservative evidence-based classifications for PDF input and metadata for image input. It does not yet provide the complete calibrated page classifier defined for Stage 2.

Target page classes remain:

- `VECTOR_DIGITAL`,
- `SCANNED_RASTER`,
- `HYBRID`,
- `CAMERA_PHOTO`,
- `UNKNOWN`.

Until Stage 2 calibration is complete, uncertain or unsupported classification must remain explicit and must not be treated as safe.

### 7.4 Input limits

Current code enforces bounded upload, request, image-byte, and decoded-pixel limits. Production deployments must later define and test:

- maximum file size,
- maximum page count,
- maximum rendered pixel count per page,
- maximum decompressed image size,
- permitted MIME types,
- retention duration,
- concurrent CPU/GPU limits,
- tenant and abuse quotas.

Production limits and enforcement are Stage 6 responsibilities.

---

## 8. Binding future stages and target components

### 8.1 Stage 1 — Real and explicitly authorized test dataset

**Status: ACTIVE IN GATED SUBSTAGES. Stage 1A is complete. Stage 1B implementation and acceptance-status changes are merged, with Issue #36 closure evidence still pending. Stage 1C artifact onboarding is NOT AUTHORIZED and has not started.**

Required target outcomes include:

- provenance and rights record for every source,
- separate evaluation, calibration, and training permissions,
- privacy classification and de-identification review,
- retention, deletion, and revocation procedures,
- immutable digests and acquisition metadata,
- frozen evaluation/calibration/held-out split policy,
- dataset card, bias report, and coverage-gap report,
- real bytes stored outside ordinary Git,
- metadata-only fixture references in the repository,
- controlled synthetic mutations kept separate from real documents.

The Stage 1A/1B governance and custody work does not itself create the authorized Stage 1 corpus. Stage 1C requires formal Stage 1B closure plus separate explicit start approval before any artifact onboarding.

### 8.2 Stage 2 — Complete quality-analysis system

**Status: DEFERRED — STAGE 2.**

The complete `QualityAnalysis` target includes:

- vector/scanned/hybrid/photo classification confidence,
- page count, dimensions, orientation, and DPI evidence,
- skew and perspective estimates with uncertainty,
- page-boundary confidence,
- motion and defocus blur,
- glare and specular highlights,
- shadow and illumination non-uniformity,
- local/global contrast,
- background and paper-aging indicators,
- compression artifacts,
- noise density,
- clipping and saturation,
- notation scale and staff/TAB line-thickness indicators,
- deterministic metric versions and failure states,
- per-page and document-level reports,
- calibration and confusion reports on the authorized Stage 1 corpus.

Current metadata checks and `not_assessed` findings do not satisfy Stage 2.

### 8.3 Stage 3 — Multi-page PDF renderer and export assembly

**Status: DEFERRED — STAGE 3. Issue #15.**

Target responsibilities include:

- reviewed `PdfBackend` and explicit renderer dependency/license decision,
- bounded PDF parsing and deterministic rendering,
- encrypted, malformed, recursive, and oversized PDF handling,
- stable page identity and page order,
- vector/scanned/hybrid per-page policy,
- vector pass-through unless explicit rasterization is authorized,
- page-level analysis, restoration, validation, and evidence lifecycle,
- partial-page failure with immutable-original fallback,
- deterministic PDF reassembly,
- page box, orientation, size, and order preservation,
- multi-page retry, cancellation, retention, and audit behavior.

The current API's ordered `UploadedPage` abstraction is not a complete multi-page PDF renderer or export-assembly implementation.

Potential renderer/writer technologies remain candidates only. No `pypdfium2`, `pikepdf`, QPDF, PyMuPDF, or equivalent dependency is selected or approved by this document revision.

### 8.4 Stage 4 — Safety calibration with real data

**Status: DEFERRED — STAGE 4.**

Target responsibilities include:

- separate staff and TAB evaluation,
- controlled deletion, insertion, shift, line-break, and digit-risk mutations,
- unchanged real pairs and known-safe transformations,
- false-negative, false-positive, and mandatory-review measurement,
- degradation/page-class stratification,
- held-out evaluation isolated from threshold selection,
- versioned, reproducible, rollbackable threshold reports,
- no automatic approval.

Current synthetic regressions prove bounded behavior but do not constitute real-data safety calibration.

### 8.5 Stage 5 — Accessible teacher review interface

**Status: DEFERRED — STAGE 5. Issue #16.**

Target responsibilities include:

- source/candidate comparison and risk overlays,
- page and finding navigation,
- bounded zoom and actual-pixel inspection,
- keyboard-only approve/reject/reprocess workflow,
- screen-reader names, roles, states, and announcements,
- focus order and error recovery,
- stale-screen recovery,
- contrast and responsive behavior,
- display-integrity and color-management validation,
- recorded accessibility test results.

Current evidence bundles are backend review evidence, not a complete accessible browser UI.

### 8.6 Stage 6 — Identity, network, and production infrastructure

**Status: DEFERRED — STAGE 6. Issues #13, #14, #17, and #18.**

Target responsibilities include:

- approved production identity provider and token validation,
- client, teacher, operator, and service roles,
- job and artifact ownership authorization,
- TLS and trusted-proxy policy,
- secret management and rotation,
- encrypted object storage,
- production database and external durable queue,
- distributed worker coordination,
- backup/restore and disaster-recovery drills,
- observability and alerting,
- quotas, abuse controls, and production HTTP security review,
- deployment, rollback, and incident runbooks.

The current development API keys, local SQLite store, built-in HTTP adapter, and local worker coordination must not be described as production controls.

### 8.7 Stage 7 — Preview release

**Status: DEFERRED — STAGE 7.**

The initial preview uses the deterministic OpenCV baseline and explicit teacher review. It must not include DocRes, ST Restore Selector, or the ST Restore image model.

Required target evidence includes bounded users and inputs, privacy/retention controls, monitoring, incident response, feature flags, kill switches, rollback, original fallback, release notes, and accepted known limitations.

### 8.8 Stage 8 — DocRes optional candidate

**Status: DEFERRED — STAGE 8.**

DocRes may be evaluated only after the deterministic Stage 7 preview baseline is frozen.

The future adapter must:

- isolate third-party code and model weights,
- record exact code, model checksum, and runtime versions,
- complete explicit code/weight license review,
- expose only approved tasks,
- enforce input, output, memory, and timeout limits,
- support complete disablement,
- normalize output as an immutable candidate,
- pass through the same safety validator and teacher-review boundary as OpenCV.

DocRes output is never automatically authoritative and never replaces OpenCV by default.

### 8.9 Stage 9 — Multi-engine comparator

**Status: DEFERRED — STAGE 9.**

The future comparator may rank the immutable original, OpenCV, and enabled Stage 8 candidates using:

- normalized quality metrics,
- structural-change metrics,
- protected-region differences,
- calibrated hard safety vetoes,
- deterministic ranking,
- explainable recommendations,
- disagreement and no-safe-candidate outcomes,
- teacher override evidence.

No candidate may win solely because it looks cleaner. The immutable original may win. Medium/high-risk results cannot bypass teacher review.

As stated in Section 5.4, the current same-source safety ordering is not this component.

### 8.10 Stage 10 — ST Restore Selector

**Status: DEFERRED — STAGE 10.**

The Selector is a project-owned learning component that recommends engines and parameter profiles without generating pixels directly.

Future requirements include:

- heuristic routing baseline,
- explicit training permission,
- offline reproducible training,
- shadow-mode evaluation,
- model registry and model card,
- rollback,
- disagreement reports against the heuristic and Stage 9 comparator,
- no online self-training,
- safe deterministic routing for uncertain cases.

### 8.11 Stage 11 — ST Restore image model

**Status: DEFERRED — STAGE 11.**

The project-owned image model may research:

- shadow reduction,
- illumination normalization,
- conservative deblurring,
- paper-background cleanup,
- noise reduction,
- bounded thin-line enhancement.

It must not:

- fill missing notation,
- guess unreadable TAB digits,
- perform generative reconstruction in symbol regions,
- correct music theory,
- change symbol placement.

Future training and evaluation must penalize changes to staff/TAB topology, symbol contours, connected components, TAB digits, notehead/stem/beam geometry, dots, and accidentals. The model remains an optional candidate behind the existing validator and teacher-review boundary.

### 8.12 Stage 12 — Music-application integrations

**Status: DEFERRED — STAGE 12.**

Target applications integrate through versioned contracts and feature flags. Restoration logic is not copied into client repositories. OMR effectiveness, when measured by an authorized downstream integration, must be reported separately from visual quality and safety.

---

## 9. Target component architecture

This section preserves the future architecture while explicitly marking non-current components.

### 9.1 API gateway

- **CURRENT:** bounded non-production `/api/v1` adapter with static development roles and strict local HTTP/multipart handling.
- **DEFERRED — STAGE 6:** production identity, ownership, TLS, proxy policy, quotas, signed/authenticated delivery, and operational controls.

### 9.2 Job manager

- **CURRENT:** append-only job states, immutable attempts, retry, cancellation, review, expiry, local persistence, and local worker fencing.
- **DEFERRED — STAGE 6:** external durable queue, production database, distributed claims, failover, and production recovery objectives.

Canonical current/future states remain:

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

Alternate or terminal states:

```text
REJECTED
FAILED
CANCELLED
EXPIRED
```

A cancelled or failed attempt cannot silently resume; retry creates a new attempt identity.

### 9.3 Input integrity service

- **CURRENT:** SHA-256 identity, signature checks, metadata inspection, bounded reads, stable rejection codes, and conservative PDF evidence.
- **DEFERRED — STAGE 3/6:** full renderer-backed PDF structure handling, production malware controls, tenant storage policy, and deployment-scale decompression defenses.

### 9.4 PDF inspector, renderer, and exporter

- **CURRENT:** read-only limited PDF inspection and vector-preservation recommendation.
- **DEFERRED — STAGE 3:** approved `PdfBackend`, deterministic page rendering, page lifecycle, vector pass-through, and PDF reassembly/export.

No PDF dependency is selected by this maintenance change.

### 9.5 Document quality analyzer

- **PARTIAL:** metadata-derived and explicitly unassessed findings.
- **DEFERRED — STAGE 2:** complete deterministic metrics, uncertainty, calibration, and document-level reports.

### 9.6 Music structure and protection logic

- **CURRENT:** conservative staff/TAB geometry and component-risk measurements in the safety validator; dark-structure preservation in OpenCV processing.
- **FUTURE:** richer versioned protection masks may be added only in the applicable approved stage and may not weaken validator vetoes.

### 9.7 Restoration engines

- **CURRENT:** deterministic OpenCV safe restoration.
- **DEFERRED — STAGE 8:** DocRes optional candidate.
- **DEFERRED — STAGE 11:** ST Restore image model optional candidate.

### 9.8 Candidate comparator and selector

- **CURRENT:** bounded same-source validator-based safety ordering only.
- **DEFERRED — STAGE 9:** calibrated multi-engine comparator.
- **DEFERRED — STAGE 10:** learned ST Restore Selector.

### 9.9 Teacher review and evidence

- **CURRENT:** backend review service, immutable evidence bundles, stale-screen binding, separate training-consent records, append-only audit.
- **DEFERRED — STAGE 5:** accessible browser UI and display QA.
- **DEFERRED — STAGE 6:** production identity and resource ownership.

### 9.10 Storage and cleanup

- **CURRENT:** in-memory default plus optional local SQLite metadata and local content-addressed blobs.
- **DEFERRED — STAGE 6:** encrypted object storage, production database, backup/restore, data residency, secure deletion, and operational monitoring.

---

## 10. API contract boundary

All current endpoints are versioned under `/api/v1`; the current API version is `0.5.0`.

The normative current contract is:

- `api/openapi.v1.json`,
- `docs/job-api-and-teacher-review.md`,
- `docs/review-evidence-contract.md`,
- `docs/http-transport-and-multipart-security.md`.

This specification does not introduce new endpoints, request fields, response fields, or automatic-approval options.

Current API safety rules include:

- original artifacts remain immutable,
- uploaded pages retain stable order and identity,
- candidate and report artifacts have separate identities,
- rejected candidates cannot be approved,
- reviewer evidence is required for teacher decisions,
- stale evidence causes a conflict rather than a decision,
- approved-candidate download is blocked before approval,
- training consent is recorded separately,
- expiry deletes bytes according to current retention behavior while retaining the audit tombstone.

The ordered multi-page upload abstraction must not be described as arbitrary multi-page PDF rendering or PDF export assembly.

---

## 11. Data, learning, and model governance

### 11.1 Dataset purposes

Evaluation, calibration, and training are distinct purposes. Permission for one purpose does not imply permission for another.

Teacher approval of a restoration does not imply:

- dataset inclusion,
- calibration permission,
- training permission,
- publication permission,
- demonstration permission.

### 11.2 Current fixture state

The repository fixture catalog is metadata-only. Real document bytes are not present in ordinary Git. Existing in-memory synthetic tests and Stage 1B project-authored non-musical drill objects do not constitute the authorized Stage 1 corpus.

### 11.3 Future learning loop

Any future learning loop is offline, versioned, and human-approved:

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

Prohibited behavior:

- online weight updates in the production request path,
- training on files without explicit training permission,
- using teacher approval as blanket training consent,
- tuning on the held-out set,
- replacing model versions without regression evidence and rollback,
- autonomous learning from user uploads.

---

## 12. Security and privacy status

### 12.1 Current local controls

- bounded request and image sizes,
- strict multipart parsing,
- static development client/reviewer keys,
- local artifact-role checks,
- append-only audit evidence,
- local private file modes where supported,
- no document content in ordinary structured errors,
- no implicit outbound model network access because no model worker exists.

### 12.2 Deferred production controls

The following are target Stage 6 controls, not current claims:

- encrypted transport and trusted-proxy policy,
- approved identity provider,
- cross-tenant ownership enforcement,
- encrypted object storage,
- secret manager and rotation,
- external durable queue,
- production database,
- backups and disaster recovery,
- WAF/reverse-proxy validation,
- penetration testing,
- production dependency scanning,
- operational logging, metrics, traces, and alerting,
- public exposure approval.

Document contents must not appear in ordinary application logs.

---

## 13. Testing and evidence strategy

### 13.1 Current repository verification

The current repository contract is verified with:

```bash
python tools/validate_dependency_lock.py
python tools/validate_repository.py
python tools/validate_fixture_catalog.py
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tools tests
```

CI validates supported Python 3.11 and 3.12 environments.

### 13.2 Current test-data boundary

- generated in-memory synthetic inputs are permitted for deterministic unit/regression tests,
- the fixture catalog remains metadata-only,
- no real student, teacher, private, or copyrighted document bytes are committed,
- current synthetic regressions are not a replacement for Stage 1 authorization or Stage 4 calibration.

### 13.3 Future corpus and calibration evidence

After Stage 1C receives separate authorization and the approved Stage 1 corpus is realized, that corpus must cover representative formats, notation types, and degradation classes. Stage 4 must measure controlled mutation detection, false negatives, false positives, and mandatory-review rates on frozen splits.

Golden-image or real-reference claims must not be made before the relevant source rights, split, and retention evidence exists.

---

## 14. Release boundaries

### 14.1 Current baseline

The current baseline is a non-production development system. It is suitable for repository-level deterministic testing and bounded local workflow validation only.

### 14.2 Preview release — Stage 7

The first bounded preview is authorized only after Stages 1–6 are accepted. It uses the deterministic OpenCV baseline and explicit teacher review. DocRes and ST Restore components are excluded from the initial preview.

### 14.3 AI candidate releases

- DocRes begins only at Stage 8.
- The multi-engine comparator begins only at Stage 9.
- ST Restore Selector begins only at Stage 10.
- ST Restore image model begins only at Stage 11.

Every AI component remains optional, disableable, versioned, reversible, and subordinate to safety validation and teacher review.

---

## 15. Technology and licensing status

### 15.1 Current runtime dependencies

The current runtime baseline is limited to the repository's exact locked dependencies, including:

- Python 3.12 primary runtime with Python 3.11 compatibility validation,
- NumPy,
- `opencv-python-headless`.

Exact versions are controlled by `requirements.lock` and repository validators.

### 15.2 Deferred technology candidates

The following remain future candidates and are not selected by this document revision:

- `pypdfium2` / PDFium for Stage 3 rendering,
- `pikepdf` / QPDF for Stage 3 PDF structure/export,
- PyMuPDF only after an explicit AGPL/commercial-license decision,
- a typed production HTTP framework in Stage 6,
- PostgreSQL or equivalent production metadata storage in Stage 6,
- encrypted object storage and external queue services in Stage 6,
- ONNX Runtime or another approved runtime for Stage 10/11 models,
- DocRes code and weights in Stage 8.

No new dependency may be added without explicit scope approval, license review, security review, version pinning, and repository validation.

This section is an engineering constraint and not legal advice.

---

## 16. Non-goals and prohibited trusted-path behavior

The trusted path shall not:

- invent or reconstruct missing notes,
- guess unreadable TAB digits,
- perform generative inpainting inside notation regions,
- correct music theory,
- modify pitches, durations, or fingering,
- convert PDF to MusicXML,
- act as an OMR engine,
- provide MIDI playback or speech narration,
- infer teacher approval from a machine verdict,
- infer training consent from teacher approval,
- continuously retrain from production data,
- overwrite the source,
- rasterize digital vector PDFs implicitly,
- use rejected candidates,
- treat unsupported analysis as safe,
- expose the built-in HTTP adapter publicly,
- activate DocRes, the Stage 9 comparator, ST Restore Selector, or ST Restore image model before their roadmap gates.

Future experimental research, if separately approved, must remain isolated from the trusted restoration path and disabled by default.

---

## 17. References

Repository-authoritative references:

- `README.md`
- `docs/roadmap.md`
- `CONTRIBUTING.md`
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
- `docs/adr/0014-stage-1b-custody-operations-boundary.md`
- `docs/stage-1b-custody-operations-contract.md`
- `docs/stage-1b-decision-hardening-record.md`
- `docs/stage-1b-closure-evidence.md`
- Issue #32
- Issue #36

External references are informative only and do not authorize dependencies or implementation:

- OpenCV repository and license: https://github.com/opencv/opencv
- pypdfium2 documentation and licensing: https://pypdfium2.readthedocs.io/en/stable/readme.html
- pikepdf repository and licensing: https://github.com/pikepdf/pikepdf
- PyMuPDF licensing information: https://pypi.org/project/pymupdf/
- ONNX Runtime documentation: https://onnxruntime.ai/docs/
- DocRes paper: https://openaccess.thecvf.com/content/CVPR2024/html/Zhang_DocRes_A_Generalist_Model_Toward_Unifying_Document_Image_Restoration_Tasks_CVPR_2024_paper.html
- DocRes implementation: https://github.com/ZZZHANG-jx/DocRes
