# ST Score Restore Engine — Technical Specification

**Document status:** Approved architecture baseline  
**Version:** 0.1.1-draft  
**Date:** 2026-08-05  
**Target repository:** `khfy7wpr5p-maker/st-score-restore-engine`  
**Primary language:** English identifiers and API contracts; Turkish-first teacher-facing messages may be added by clients.

---

## 1. Purpose

ST Score Restore Engine is an independent, safety-first service for improving scanned or photographed music documents without changing their musical meaning.

The engine accepts PDF documents, JPG/JPEG images, PNG images, and phone-captured score or guitar-TAB photos. It analyzes document quality, executes one or more restoration strategies, compares the results, validates preservation of music notation and guitar TAB structures, and requires teacher approval when a result is not provably low risk.

The engine is designed to become a shared preprocessing service for:

- SesliTab Guitar Reader,
- MusicXML-to-Guitar TAB Engine,
- Cloud OMR Gateway,
- ScoreMosaic / Scremosaik,
- future accessible-music and OMR applications.

The engine is not an OMR system and does not convert notation to MusicXML. It prepares and validates visual documents before an OMR or accessibility workflow consumes them.

---

## 2. Core safety objective

The primary objective is not visual beauty. The primary objective is preservation of musical information.

A restoration is acceptable only when it improves readability or downstream recognition while preserving, within defined tolerances:

- page count and page order,
- page dimensions and orientation,
- staff and TAB system geometry,
- staff-line and TAB-line counts,
- noteheads, stems, flags, beams, dots, ties, slurs and rests,
- accidentals, clefs, key signatures and time signatures,
- barlines, repeat marks and volta brackets,
- TAB numbers and their positions,
- guitar technique markings,
- lyrics, fingering, dynamics and instructional text,
- relationships between notation and TAB systems.

The original input is immutable. Every processed output is a new derivative artifact.

---

## 3. Non-goals

The first production line shall not:

- invent or reconstruct missing notes,
- guess unreadable TAB numbers,
- perform generative inpainting inside notation regions,
- correct music theory,
- modify pitches, durations or fingering,
- convert PDF to MusicXML,
- provide MIDI playback or speech narration,
- replace teacher review for medium- or high-risk pages,
- continuously retrain itself from unreviewed production data,
- overwrite or destructively edit the source file.

Future experimental reconstruction features, if ever introduced, must be isolated from the trusted restoration pipeline and must never be enabled by default.

---

## 4. System context and repository boundary

ST Score Restore Engine remains a separate repository and deployable service.

```text
SesliTab Guitar Reader ───────┐
MusicXML-to-Guitar Engine ────┤
Cloud OMR Gateway ────────────┼── REST/JSON API ── ST Score Restore Engine
ScoreMosaic / Scremosaik ─────┘
```

Client applications submit documents and retrieve approved outputs. They do not import the restoration implementation directly.

This boundary isolates:

- heavy computer-vision and AI dependencies,
- GPU/CPU execution requirements,
- model licensing and model versioning,
- temporary storage and document privacy controls,
- failures caused by experimental restoration models.

A client may use synchronous analysis for small images, but document restoration jobs are asynchronous.

---

## 5. Approved high-level pipeline

```text
PDF / JPG / JPEG / PNG / Phone photo
      ↓
Input integrity and file-type validation
      ↓
Document and quality analysis
      ↓
Page classification: vector / scanned / hybrid / photo
      ↓
Music-structure protection mask
      ↓
┌─────────────────────────────────────────────┐
│ OpenCV safe restoration                    │
│ DocRes adapter                             │
│ ST Restore engine                          │
└─────────────────────────────────────────────┘
      ↓
Candidate normalization and comparison
      ↓
Music-score and TAB safety validation
      ↓
Risk decision
  ├── low risk: eligible for auto-approval policy
  ├── medium risk: teacher review required
  └── high risk: reject or restore with safer profile
      ↓
Teacher approval
      ↓
Enhanced PDF and/or approved image / manifest / audit report
```

---

## 6. Input support

### 6.1 Accepted formats

Initial supported formats:

- PDF,
- JPG and JPEG,
- PNG,
- TIFF, including multipage TIFF when supported by the chosen decoder.

Phone-captured photographs are first-class inputs, not an experimental afterthought. A phone photo may be supplied as JPG/JPEG or PNG and may contain perspective distortion, EXIF rotation, shadows, glare, page curvature, surrounding desk/background content, or partial page boundaries.

### 6.2 Input limits

Limits are deployment configuration, not hard-coded business logic. A deployment must define:

- maximum file size,
- maximum page count,
- maximum rendered pixel count per page,
- maximum decompressed image size,
- permitted MIME types,
- job retention duration,
- concurrent CPU and GPU job limits.

Files must be validated by content signature as well as filename extension. JPG and JPEG are treated as the same media family. EXIF orientation and embedded color-profile metadata must be read safely and normalized without altering the immutable source file.

### 6.3 Document classes

Each page receives one class:

- `VECTOR_DIGITAL`: digitally generated page dominated by vector notation,
- `SCANNED_RASTER`: page dominated by a raster scan,
- `HYBRID`: meaningful vector and raster content coexist,
- `CAMERA_PHOTO`: a phone/camera image with perspective, illumination, page-boundary, glare, curvature or surrounding-background characteristics,
- `UNKNOWN`: classification confidence below threshold.

Default behavior:

- vector-digital pages are passed through unchanged unless explicit processing is requested,
- scanned pages are eligible for restoration,
- hybrid pages must preserve vector objects and process only eligible raster regions where technically safe,
- camera-photo pages are eligible for page-boundary detection, EXIF-orientation normalization, conservative crop, perspective correction, illumination/shadow correction and dewarping only when confidence thresholds are satisfied,
- unknown pages require conservative processing or teacher review.


### 6.4 Phone-photo acceptance requirements

Phone-captured notation and TAB photos are a first-class use case. The initial implementation must be tested with representative JPG/JPEG and PNG images from common phone cameras.

A phone-photo job must preserve the following invariants:

- the original image remains immutable,
- EXIF orientation is applied only to the derivative coordinate system,
- page crop and perspective transforms are reversible through recorded transform matrices,
- no finger, desk, stand or background removal may alter notation regions,
- glare or shadow removal must not erase dots, accidentals, beams, staff lines or TAB digits,
- a partially missing page edge must not be invented,
- the approved master derivative should be PNG when lossless preservation is required,
- JPEG export is a compatibility derivative and must record its quality setting.

Minimum phone-photo test classes:

- overhead photo with mild rotation,
- oblique photo with keystone perspective,
- uneven indoor lighting and page shadow,
- mild glare on glossy paper,
- curved book page near the binding,
- surrounding desk/background visible,
- motion blur or autofocus failure,
- cropped or partially missing page boundary,
- combined standard notation and six-line guitar TAB.

---

## 7. Main components

### 7.1 API Gateway

Responsibilities:

- authentication and authorization,
- request validation,
- idempotency handling,
- rate and quota enforcement,
- job creation,
- signed or authenticated artifact delivery,
- API version negotiation.

### 7.2 Job Manager

Canonical job states:

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

Terminal or alternate states:

```text
REJECTED
FAILED
CANCELLED
EXPIRED
```

State transitions must be append-only in the audit log. A cancelled or failed job cannot silently return to processing; retry creates a new attempt identifier.

### 7.3 Input Integrity Service

Responsibilities:

- calculate SHA-256 of the original file,
- store immutable input metadata,
- reject encrypted or unsupported PDFs unless an approved decryption flow exists,
- detect malformed, truncated or suspiciously recursive documents,
- prevent zip bombs, image bombs and path traversal,
- record page dimensions and page count before processing,
- record image dimensions, color space, bit depth, EXIF orientation and decoder identity for JPG/JPEG/PNG inputs,
- ignore or strip unsafe metadata from derivatives while preserving required provenance in the audit manifest.

### 7.4 PDF Inspector and Renderer

Preferred initial implementation:

- `pypdfium2` / PDFium for permissively licensed PDF rendering and inspection,
- `pikepdf` / QPDF for low-level PDF structure, repair and writing,
- an internal `PdfBackend` interface so alternatives can be replaced without affecting the pipeline.

PyMuPDF must not be a default dependency until the project makes an explicit AGPL/commercial-license decision.

Required capabilities:

- inspect page object composition,
- render page regions at deterministic DPI,
- preserve page boxes and rotation,
- extract or identify embedded raster images,
- produce a new PDF without modifying the source,
- preserve vector pages whenever no restoration is required.

Default render target for scanned notation evaluation: configurable, initially 300–400 DPI. Rendering must be deterministic for a fixed backend version and profile.

### 7.5 Document Quality Analyzer

Produces page-level measurements:

- skew angle,
- perspective distortion estimate,
- page-boundary confidence,
- EXIF-orientation status,
- camera rotation and horizon estimate,
- page-curvature estimate,
- glare/specular-highlight score,
- surrounding-background and crop confidence,
- motion-blur and defocus-blur scores,
- local and global contrast,
- illumination nonuniformity,
- shadow score,
- background color and paper aging score,
- compression artifact score,
- noise density,
- clipping and saturation,
- estimated notation scale,
- estimated staff/TAB line thickness,
- vector/raster/hybrid confidence.

Output is a structured `QualityAnalysis` object and not only a single quality score.

### 7.6 Music Structure Detector

Detects and describes protected content:

- staff systems and five-line groups,
- TAB systems and expected six-line groups,
- barlines and system connectors,
- dense symbol regions,
- text and lyric regions,
- thin-line regions,
- uncertain regions requiring conservative treatment.

The first version may use classical computer vision. Later versions may add trained detectors.

### 7.7 Protection Mask Builder

Produces masks with at least three levels:

- `LOCKED`: no generative or destructive transformation permitted,
- `CONSERVATIVE`: only bounded contrast/denoise operations permitted,
- `BACKGROUND`: background-focused restoration permitted.

Music symbols and TAB numbers are `LOCKED` or `CONSERVATIVE` by default. Background areas may receive stronger deshadowing and normalization.

Masks must be versioned and retained with the job for auditability.

### 7.8 OpenCV Safe Restoration Engine

This is the deterministic baseline and must exist before AI restoration is enabled.

Supported operations may include:

- orientation correction,
- bounded deskew,
- EXIF-orientation normalization for image inputs,
- page-boundary crop when confidence is high,
- perspective correction when page boundaries are reliable,
- conservative camera-lens distortion correction when calibrated or strongly supported,
- page dewarping when geometry confidence is sufficient,
- illumination normalization,
- shadow and mild glare reduction outside protected notation regions,
- background whitening,
- conservative denoising,
- local contrast enhancement,
- adaptive binarization for preview or OMR-specific derivatives,
- border cleanup outside protected notation areas,
- resolution normalization without hallucinated detail.

Every operation is profile-driven and records parameters in the manifest.

The safe engine must support a `dry_run` mode that reports planned operations without generating a final derivative.

### 7.9 DocRes Adapter

DocRes is an optional third-party AI candidate engine for document restoration tasks such as dewarping, deshadowing, appearance enhancement, deblurring and binarization.

The adapter must:

- isolate third-party model code and weights,
- record exact repository commit, model checksum and runtime version,
- verify license terms before distribution or hosted use,
- expose only approved tasks,
- enforce input and output size limits,
- apply protection masks where technically possible,
- prevent DocRes output from becoming trusted without comparison and validation,
- support complete disablement by configuration.

The adapter output is always a candidate, never an automatically authoritative result.

### 7.10 ST Restore Engine

ST Restore is the project-owned model family.

It is divided into two products:

1. **ST Restore Selector** — recommends the safest engine and parameter profile.
2. **ST Restore Image Model** — performs project-owned restoration after sufficient approved training data exists.

The selector should be delivered before the image model because it can improve routing without changing notation pixels directly.

The image model must be trained with losses and evaluation criteria that explicitly penalize changes to:

- staff/TAB line topology,
- symbol contours,
- connected components in protected regions,
- TAB digit identity,
- notehead/stem/beam geometry,
- dot and accidental preservation,
- OMR structural consistency.

### 7.11 Candidate Result Comparator

Inputs:

- original normalized page,
- OpenCV candidate,
- DocRes candidate when enabled,
- ST Restore candidate when enabled.

Outputs:

- quality-improvement measurements,
- structural-change measurements,
- protected-region differences,
- candidate ranking,
- rejection reasons,
- recommended candidate and confidence.

No candidate can win solely because it looks cleaner. Structural safety has veto power over visual quality.

### 7.12 Music and TAB Safety Validator

The validator applies hard and soft checks.

Hard-fail examples:

- page count changed unexpectedly,
- page dimensions changed outside tolerance,
- a five-line staff becomes four or six lines,
- a six-line TAB system changes line count,
- protected-region connected components disappear or are added beyond threshold,
- alignment transform exceeds approved bounds,
- TAB digit classifier detects an identity change with high confidence,
- the output contains generated pixels in a forbidden region,
- a vector-only page was rasterized without explicit authorization.

Soft-risk examples:

- local symbol contour difference,
- uncertain dot preservation,
- possible beam merge or split,
- text degradation,
- remaining shadow or blur,
- ambiguous perspective correction.

The validator produces:

- page risk score,
- document risk score,
- categorized findings,
- region coordinates,
- before/after crops,
- machine-readable evidence.

### 7.13 Teacher Review Service

Review actions:

- approve document,
- approve selected pages and reject others,
- choose a different candidate per page,
- request reprocessing with a safer or stronger profile,
- annotate a risk region,
- mark output as too light, too dark, blurred, altered or correct,
- allow or deny use as approved training data.

Teacher approval must record:

- reviewer identity,
- timestamp,
- selected candidate and profile,
- reviewed pages,
- findings acknowledged,
- training-data consent state.

The service must never infer consent from approval alone.

### 7.14 Artifact Exporter

Required outputs:

- enhanced PDF for PDF jobs or when an image-to-PDF derivative is explicitly requested,
- approved PNG derivative for lossless image delivery,
- optional JPEG derivative only when the user requests JPEG compatibility,
- optional page PNG/TIFF derivatives,
- comparison preview,
- risk map,
- processing manifest,
- audit report.

The exporter must:

- preserve page order and dimensions for PDF jobs,
- preserve the original image aspect ratio unless an approved page-boundary crop or perspective transform is recorded,
- avoid repeated lossy JPEG recompression and prefer PNG for validated master image derivatives,
- retain vector pages when unchanged,
- avoid unnecessary recompression,
- embed only approved page candidates,
- label experimental outputs in metadata,
- produce a unique derivative hash,
- never overwrite the source object.

### 7.15 Storage and Cleanup

Logical storage classes:

- immutable input,
- working pages,
- candidate outputs,
- approved outputs,
- audit manifests,
- optional approved training examples.

Retention periods are independent. Working files should expire sooner than approved outputs. Training-data copies require separate consent and policy.

Cleanup must be idempotent and auditable.

---

## 8. API contract baseline

All endpoints are versioned under `/api/v1`.

### 8.1 Create restoration job

```http
POST /api/v1/restoration-jobs
Content-Type: multipart/form-data
Idempotency-Key: <unique-client-key>
```

Form fields:

- `file`: required,
- `profile`: `safe | balanced | experimental`, default `safe`,
- `document_hint`: `auto | score | tab | score_and_tab | handwritten`, default `auto`,
- `auto_approve_low_risk`: boolean, default `false`,
- `training_consent`: boolean, default `false`.

Response:

```json
{
  "job_id": "rst_01...",
  "status": "UPLOADED",
  "input_sha256": "...",
  "created_at": "2026-08-05T09:00:00Z"
}
```

### 8.2 Read job

```http
GET /api/v1/restoration-jobs/{job_id}
```

Returns status, progress, page counts, active processing attempt and risk summary.

### 8.3 Read analysis

```http
GET /api/v1/restoration-jobs/{job_id}/analysis
```

Returns document classification, quality findings and proposed processing plan.

### 8.4 List candidates

```http
GET /api/v1/restoration-jobs/{job_id}/candidates
```

Returns page-level candidates with engine, profile, metrics and preview identifiers.

### 8.5 Read safety report

```http
GET /api/v1/restoration-jobs/{job_id}/safety-report
```

### 8.6 Submit review

```http
POST /api/v1/restoration-jobs/{job_id}/review
Content-Type: application/json
```

Example:

```json
{
  "decision": "approve",
  "page_selections": [
    {"page": 1, "candidate_id": "cand_01"},
    {"page": 2, "candidate_id": "cand_07"}
  ],
  "acknowledged_finding_ids": ["finding_12"],
  "training_consent": false,
  "notes": "TAB digits verified at 400% zoom."
}
```

### 8.7 Reprocess

```http
POST /api/v1/restoration-jobs/{job_id}/attempts
```

Creates a new immutable attempt with a different profile or bounded parameter overrides.

### 8.8 Download approved artifacts

```http
GET /api/v1/restoration-jobs/{job_id}/artifacts/enhanced-pdf
GET /api/v1/restoration-jobs/{job_id}/artifacts/enhanced-image
GET /api/v1/restoration-jobs/{job_id}/artifacts/audit-report
GET /api/v1/restoration-jobs/{job_id}/artifacts/manifest
```

Approved PDF or image download is unavailable before the job reaches `APPROVED` or `COMPLETED`. For JPG/JPEG/PNG inputs, `enhanced-image` returns the approved master image derivative; an enhanced PDF is optional.

### 8.9 Cancel and delete

```http
POST   /api/v1/restoration-jobs/{job_id}/cancel
DELETE /api/v1/restoration-jobs/{job_id}
```

Deletion follows retention and audit policy; it does not rewrite history silently.

---

## 9. Core data objects

### 9.1 Processing manifest

Minimum fields:

```json
{
  "schema_version": "1.0",
  "job_id": "rst_01...",
  "attempt_id": "att_01...",
  "input": {
    "sha256": "...",
    "mime_type": "application/pdf",
    "source_format": "pdf",
    "capture_class": "scanned_raster",
    "page_count": 12
  },
  "engines": [
    {
      "name": "opencv-safe",
      "version": "...",
      "parameters": {}
    }
  ],
  "models": [],
  "pages": [],
  "review": null,
  "output": null
}
```

### 9.2 Safety finding

```json
{
  "finding_id": "finding_12",
  "page": 2,
  "severity": "medium",
  "category": "possible_tab_digit_change",
  "region": {"x": 121, "y": 884, "width": 63, "height": 48},
  "evidence": {
    "original_crop_id": "...",
    "candidate_crop_id": "...",
    "metric": 0.78
  },
  "requires_review": true
}
```

---

## 10. Risk policy

Suggested normalized document risk bands:

- `0–19 LOW`: no hard failure; eligible for explicit deployment policy allowing auto-approval,
- `20–49 MEDIUM`: teacher review required,
- `50–79 HIGH`: default reject; manual override requires reason,
- `80–100 CRITICAL`: candidate cannot be approved.

The exact scoring model must be calibrated on music documents. A raw visual similarity score is not sufficient.

Any hard-fail condition sets minimum risk to `CRITICAL` regardless of aggregate score.

---

## 11. Learning and model governance

### 11.1 Learning principle

Production use collects feedback, not uncontrolled live model updates.

Approved learning loop:

```text
Production examples
      ↓
Explicit teacher annotation and training consent
      ↓
Curated versioned dataset
      ↓
Offline training
      ↓
Regression and safety evaluation
      ↓
Shadow deployment
      ↓
Human release approval
      ↓
Versioned model release with rollback
```

### 11.2 Dataset categories

- clean source pages,
- synthetic degradations with known clean target,
- teacher-approved real restorations,
- rejected or failure examples,
- notation/TAB safety crops,
- scanner/camera/device profiles.

### 11.3 Prohibited learning behavior

- no online weight updates in the production request path,
- no training on files without explicit consent,
- no replacement of old models without regression comparison,
- no deletion of prior model versions needed for rollback,
- no use of copyrighted documents outside the approved legal/data policy,
- no use of teacher approval as implicit blanket training consent.

### 11.4 Model registry fields

- model identifier and semantic version,
- training code commit,
- dataset versions,
- model checksum,
- framework and runtime versions,
- supported tasks,
- evaluation report,
- known limitations,
- approval identity and date,
- rollback predecessor.

---

## 12. Security and privacy

Required controls:

- encrypted transport,
- encrypted storage where deployment supports it,
- access control per project/user/organization,
- short-lived artifact access URLs or authenticated downloads,
- file signature and decompression-limit checks,
- sandboxed third-party model execution,
- no outbound network access from model workers by default,
- secrets separated from job data,
- structured audit logs without unnecessary document content,
- configurable data residency and retention,
- explicit deletion workflow,
- malware and malformed-document defenses.

Document contents must not appear in ordinary application logs.

---

## 13. Observability

Metrics:

- jobs by status and document class,
- page latency by engine,
- CPU/GPU memory and utilization,
- candidate rejection rates,
- teacher approval and override rates,
- safety findings by category,
- PDF export failures,
- model-version performance,
- OMR improvement metrics when an authorized integration supplies them.

Logs must carry:

- job ID,
- attempt ID,
- page number,
- engine/model version,
- operation name,
- result code.

They must not carry full page images or extracted confidential text.

---

## 14. Testing strategy

### 14.1 Unit tests

- quality metrics,
- page classification,
- transforms and coordinate mapping,
- mask generation,
- state-machine transitions,
- risk scoring,
- manifest serialization,
- API validation.

### 14.2 Golden-image regression tests

A fixed corpus must include:

- clean vector scores,
- clean scans,
- low-resolution scans,
- shadows,
- skew and perspective,
- yellowed paper,
- staff-only notation,
- TAB-only pages,
- combined score and TAB,
- dense beams and tuplets,
- dotted notes and accidentals,
- fingerings and guitar techniques,
- pages known to break denoisers.

Every engine/model release is compared with approved golden outputs and structural metrics.

### 14.3 Safety mutation tests

Create controlled forbidden changes:

- change TAB `3` to `8`,
- remove a rhythm dot,
- merge two beams,
- delete a staff line segment,
- add a notehead-like speck,
- shift a barline,
- rasterize a vector page.

The validator must detect these at required recall thresholds before release.

### 14.4 Integration tests

- PDF upload to approved artifact,
- cancellation and cleanup,
- retry with new attempt,
- mixed vector/raster PDF,
- multi-page selection during teacher review,
- client integration using API contract fixtures.

### 14.5 Performance tests

- large page dimensions,
- multi-page jobs,
- concurrent CPU processing,
- optional GPU queue,
- memory-bound malformed inputs,
- deterministic output checks.

---

## 15. Definition of done for the first trusted release

The first trusted release is complete only when:

- original inputs are immutable and hash-verified,
- vector/scanned/hybrid classification works on the reference corpus,
- OpenCV safe restoration is deterministic,
- page geometry is preserved within documented tolerances,
- staff and TAB line validation is operational,
- result comparison produces machine-readable evidence,
- teacher review can approve per-page candidates,
- export produces a separate approved PDF and/or image derivative plus an audit manifest,
- all hard-fail safety mutation tests pass,
- no AI engine is required for the baseline release,
- integration API fixtures are published,
- retention and deletion are documented and tested.

---

## 16. Technology baseline and licensing notes

Proposed baseline, subject to repository license review:

- Python for orchestration and initial computer-vision implementation,
- OpenCV for deterministic image processing,
- pypdfium2/PDFium for rendering and inspection,
- pikepdf/QPDF for PDF structure and export support,
- FastAPI or equivalent typed HTTP framework,
- PostgreSQL or equivalent durable job metadata store,
- object storage for immutable inputs and generated artifacts,
- ONNX Runtime for portable ST Restore inference when the model is exported to ONNX,
- DocRes behind an optional adapter.

Licensing must be reviewed before distribution:

- current OpenCV releases use Apache-2.0,
- pypdfium2 is Apache-2.0/BSD-3-Clause and PDFium uses a BSD-style license with third-party notices,
- pikepdf uses MPL-2.0,
- PyMuPDF is dual licensed under AGPL or a commercial license and is therefore not the default,
- DocRes code and weights require a separate, explicit license review before product use.

This section is an engineering constraint and not legal advice.

---

## 17. References

- OpenCV repository and license: https://github.com/opencv/opencv
- pypdfium2 documentation and licensing: https://pypdfium2.readthedocs.io/en/stable/readme.html
- pikepdf repository and licensing: https://github.com/pikepdf/pikepdf
- PyMuPDF licensing information: https://pypi.org/project/pymupdf/
- ONNX Runtime documentation: https://onnxruntime.ai/docs/
- DocRes paper: https://openaccess.thecvf.com/content/CVPR2024/html/Zhang_DocRes_A_Generalist_Model_Toward_Unifying_Document_Image_Restoration_Tasks_CVPR_2024_paper.html
- DocRes implementation: https://github.com/ZZZHANG-jx/DocRes


