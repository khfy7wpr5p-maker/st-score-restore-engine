# Dependency Review: OpenCV Safe-Restoration Runtime

- **Status:** Approved for Milestone M2 candidate generation
- **Reviewed:** 2026-08-05
- **Packages:** `opencv-python-headless==4.13.0.92`, `numpy==2.3.5`
- **Lock:** `requirements.lock`

## Purpose

OpenCV supplies deterministic CPU image decoding, geometry transforms, morphology, filtering, thresholding, contour detection, Hough lines, and output encoding. NumPy supplies the array representation required by OpenCV.

## Canonical sources and licenses

- OpenCV Python wheel project: PyPI `opencv-python-headless`; wheel scripts MIT, OpenCV Apache-2.0.
- OpenCV wheels bundle native code and third-party components; the project documentation identifies FFmpeg under LGPL-2.1 and lists additional notices in `LICENSE-3RD-PARTY.txt`.
- NumPy: PyPI `numpy`; BSD-3-Clause core with bundled component notices.

No network service, telemetry, model weight, or training data is included.

## Version and platform decision

OpenCV 4.13 is selected instead of the new 5.x line to reduce first-baseline migration risk. The headless package avoids GUI/Qt dependencies. Python 3.11 and 3.12 are validated in CI on Linux. Windows 7 is not a supported server runtime; older user devices remain thin clients.

## Integrity and installation

The full runtime graph is exactly pinned. CI installs binary wheels only and validates installed versions. Production deployment must use the same lock or a reviewed platform-specific mirror with retained wheel hashes.

## Risks

- native wheel supply-chain and bundled codec licenses,
- platform-specific numeric or codec behavior,
- large binary download size,
- image decoders process untrusted input.

Mitigations include byte limits from input inspection, malformed-file checks, no GUI modules, no network calls, deterministic tests, exact versions, binary-only installation, and a narrow adapter module.

## Removal and fallback

Removing `safe_restoration.py`, its CLI, schemas, and dependencies restores the standard-library input inspection boundary. Digital PDF preservation and immutable source manifests remain independent of OpenCV.
