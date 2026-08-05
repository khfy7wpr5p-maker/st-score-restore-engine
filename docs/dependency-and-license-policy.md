# Dependency and license policy

**Status:** Milestone M0 baseline

## 1. Default rule

No library, service SDK, model adapter or model weight is added merely because it is technically convenient. Each addition must be necessary, bounded and independently reviewable.

## 2. Required review fields

Every proposed dependency or model must record:

- name, exact version and purpose,
- canonical project and download source,
- code license,
- model-weight license when separate,
- redistribution and commercial-use terms,
- patent or field-of-use restrictions where stated,
- transitive dependencies and native binaries,
- supported platforms and Python versions,
- security and maintenance considerations,
- data sent outside the engine, if any,
- fallback and removal plan,
- approving pull request and ADR when architecturally significant.

## 3. Lock strategy

`pyproject.toml` records dependency intent. The repository currently declares no third-party runtime dependency, so there is no non-empty lock graph to freeze.

The first dependency-bearing pull request must select a reproducible lock tool and commit its generated lock artifact. Thereafter:

- dependency resolution must not occur implicitly in production,
- CI and deployment must install from the frozen lock,
- lock changes must be reviewed with manifest changes,
- hashes or equivalent integrity data must be retained where supported,
- separate platform locks may be used only when native packages require them and the reason is documented.

## 4. Models and large artifacts

Model files are not committed to ordinary Git history by default. Approved weights require a manifest containing source, version, checksum, license, storage location, evaluation status and rollback target.

No model may learn online from production documents. Training data use requires explicit consent separate from teacher approval.

## 5. Candidate technologies

OpenCV, PDF backends, DocRes, ONNX Runtime and future ML frameworks remain candidates until a dependency review approves exact packages and versions. Mention in architecture documents is not dependency approval.

## 6. Removal

A dependency must be removable behind a narrow adapter or contract where practical. Unmaintained, unsafe or license-incompatible dependencies must have a documented replacement or rollback path.
