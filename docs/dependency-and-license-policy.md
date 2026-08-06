# Dependency and license policy

**Status:** Runtime baseline plus Stage 1A offline validation stack

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
the separate offline validation/test graph for Python 3.11–3.12.

CI must validate both locks, install exact binary wheels with dependency
resolution disabled, verify installed versions and reject implicit source
builds. Any dependency or lock change requires review with the manifest change.

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

Stage 1A offline validation/test only:

- `jsonschema==4.26.0`
- `attrs==26.1.0`
- `jsonschema-specifications==2025.9.1`
- `referencing==0.37.0`
- `rpds-py==2026.5.1`

PDF renderers, DocRes, ONNX Runtime and future ML frameworks remain candidates
until separate dependency reviews approve exact packages and versions.

## 6. Native-binary and license handling

OpenCV, NumPy and rpds-py wheels include native or bundled components.
Distributors must preserve notices shipped inside installed wheels. Review and
license records live under `docs/dependency-reviews/` and `LICENSES/`.

## 7. Removal

OpenCV remains behind `st_score_restore.safe_restoration`. The JSON Schema stack
is isolated to repository validation and tests; removing its optional group,
lock, review and parity imports does not change restoration runtime behavior.
There is no unreviewed fallback for schema parity.
