# Dependency and license policy

**Status:** Runtime baseline plus Stage 1A offline validation stack and Stage 3 PDF renderer

## 1. Default rule

No library, service SDK, model adapter or model weight is added merely because
it is technically convenient. Each addition must be necessary, bounded and
independently reviewable.

## 2. Required review fields

Every proposed dependency or model records its exact version and purpose,
canonical source, licenses, redistribution/commercial terms, bundled and
transitive components, native binaries, supported platforms/Python versions,
security considerations, external data transfer, fallback/removal plan and
approving ADR or pull request.

## 3. Lock strategy

`pyproject.toml` records exact dependency intent. `requirements.lock` records
the complete restoration runtime graph. `requirements.validation.lock` records
the separate offline validation/test graph for Python 3.11–3.12 and the exact
approved wheel SHA-256 values used by the Ubuntu x86_64 CI matrix.

CI validates both locks, installs exact binary wheels with dependency
resolution disabled, verifies installed versions, runs `pip check` and rejects
implicit source builds. The validation graph additionally requires approved
wheel hashes. Any dependency, version, platform or hash change requires review
with the manifest change.

## 4. Models and large artifacts

Model files are not committed to ordinary Git history by default. Approved
weights require source, version, checksum, license, storage location, evaluation
status and rollback target. No model may learn online from production
documents. Training-data use requires explicit consent separate from teacher
approval.

## 5. Approved technologies

Runtime:

- `opencv-python-headless==4.13.0.92`
- `numpy==2.3.5`
- `pypdfium2==5.13.0` — Stage 3 PDFium renderer binding under ADR 0017

Stage 1A offline validation/test only:

- `jsonschema==4.26.0`
- `attrs==26.1.0`
- `jsonschema-specifications==2025.9.1`
- `referencing==0.37.0`
- `rpds-py==2026.5.1`
- `typing-extensions==4.15.0`

DocRes, ONNX Runtime and future ML frameworks remain candidates until separate
dependency reviews approve exact packages and versions.

## 6. Native-binary and license handling

OpenCV, NumPy, pypdfium2/PDFium and rpds-py wheels include native or bundled
components. Distributors must preserve notices shipped inside installed wheels.
Review and license records live under `docs/dependency-reviews/` and `LICENSES/`.

For `pypdfium2==5.13.0`, the upstream project identifies its own code under
Apache-2.0 / BSD-3-Clause terms and PDFium under a BSD-style license. PDFium
bundles additional third-party components; the notices shipped with the exact
installed wheel are authoritative for redistribution and must be retained.

## 7. Removal

OpenCV remains behind `st_score_restore.safe_restoration`. The Stage 3 PDFium
binding remains behind `st_score_restore.pdf_pipeline`; removing that module,
its validator/tests, dependency pin and ADR restores the Stage 2 fail-closed PDF
renderer boundary without changing immutable input inspection. There is no
unreviewed alternate renderer fallback.

The JSON Schema stack is isolated to repository validation and tests; removing
its optional group, lock, review and parity imports does not change restoration
runtime behavior. There is no unreviewed fallback for schema parity.
