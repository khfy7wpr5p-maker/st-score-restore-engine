# Dependency and license policy

**Status:** Milestone M2 runtime baseline

## 1. Default rule

No library, service SDK, model adapter, or model weight is added merely because it is technically convenient. Each addition must be necessary, bounded, and independently reviewable.

## 2. Required review fields

Every proposed dependency or model records its exact version and purpose, canonical source, code and weight licenses, redistribution/commercial terms, bundled and transitive components, native binaries, supported platforms and Python versions, security considerations, external data transfer, fallback/removal plan, and approving ADR or pull request.

## 3. Lock strategy

`pyproject.toml` records exact dependency intent. `requirements.lock` records the complete runtime graph for Python 3.11–3.12. The graph currently contains only NumPy and the headless OpenCV wheel package.

CI must:

- validate that the lock and project metadata match,
- install exact binary wheels with dependency resolution disabled,
- verify installed versions before tests,
- reject implicit source builds.

Deployment may use a reviewed platform-specific wheel mirror, but must retain exact filenames, versions, hashes, and bundled license notices. Any dependency or lock change requires review with the manifest change.

## 4. Models and large artifacts

Model files are not committed to ordinary Git history by default. Approved weights require a manifest containing source, version, checksum, license, storage location, evaluation status, and rollback target.

No model may learn online from production documents. Training-data use requires explicit consent separate from teacher approval.

## 5. Approved and candidate technologies

Approved for the M2 candidate baseline:

- `opencv-python-headless==4.13.0.92`,
- `numpy==2.3.5`.

PDF renderers, DocRes, ONNX Runtime, and future ML frameworks remain candidates until a separate dependency review approves exact packages and versions.

## 6. Native-binary and license handling

OpenCV and NumPy wheels include native and bundled components. The repository keeps dependency-review and license records under `docs/dependency-reviews/` and `LICENSES/`. Distributors must preserve the notices shipped inside installed wheels.

## 7. Removal

OpenCV remains behind `st_score_restore.safe_restoration`. Removing that module, its CLI, schemas, and locked dependencies returns the repository to the standard-library input-inspection baseline without changing source artifact identities.
