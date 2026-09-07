"""DeepScoresV2 Dense admission, split, and synthetic-degradation planning for Stage 11."""

from __future__ import annotations

import hashlib
import re
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping

DATASET_ID = "deepscoresv2.dense.v2"
DRIVE_FOLDER_ID = "1Ov_cUo6O1guuegX1GiqrRlHvTtCjHpvy"
DRIVE_FILE_ID = "1QjvmZSpWgnc8wdfcwfmcXTdibXQnriJS"
ARCHIVE_FILENAME = "ds2_dense.tar.gz"
ARCHIVE_SIZE_BYTES = 741_814_529
EXPECTED_ARCHIVE_MD5 = "7237318e381e6e0848ec30eb82decb83"
SOURCE_DOI = "10.5281/zenodo.4012193"
LICENSE_ID = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
DENSE_IMAGE_COUNT = 1714

_IMAGE_RE = re.compile(r"\.(?:png|jpe?g)$", re.IGNORECASE)


class Stage11DeepScoresDenseError(ValueError):
    """Raised when the DeepScoresV2 Dense training contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11DeepScoresDenseError(message)


def validate_registration(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("artifactType") == "stage11_deepscoresv2_dense_drive_source_registration", "artifact type mismatch")
    dataset = payload.get("dataset") or {}
    drive = payload.get("driveSource") or {}
    rights = payload.get("rightsReview") or {}
    archive = payload.get("archive") or {}

    _require(dataset.get("datasetId") == DATASET_ID, "dataset id mismatch")
    _require(dataset.get("sourceDoi") == SOURCE_DOI, "source DOI mismatch")
    _require(dataset.get("denseImageCount") == DENSE_IMAGE_COUNT, "dense image count mismatch")

    _require(drive.get("folderId") == DRIVE_FOLDER_ID, "Drive folder id mismatch")
    _require(drive.get("fileId") == DRIVE_FILE_ID, "Drive file id mismatch")
    _require(drive.get("fileName") == ARCHIVE_FILENAME, "Drive archive filename mismatch")
    _require(drive.get("observedSizeBytes") == ARCHIVE_SIZE_BYTES, "Drive archive size mismatch")
    _require(drive.get("shared") is False, "training archive must remain private unless explicitly changed")

    _require(rights.get("status") == "approved", "DeepScoresV2 rights must be approved")
    _require(rights.get("licenseId") == LICENSE_ID, "license id mismatch")
    _require(rights.get("commercialTrainingAllowed") is True, "commercial training must be allowed")
    _require(rights.get("attributionRequired") is True, "CC BY attribution obligation must be recorded")
    _require(rights.get("nonCommercialRestriction") is False, "non-commercial restriction cannot be present")

    _require(archive.get("expectedMd5") == EXPECTED_ARCHIVE_MD5, "expected archive MD5 mismatch")
    _require(archive.get("checksumVerificationState") in {"pending_first_colab_read", "verified"}, "invalid checksum state")
    if archive.get("checksumVerificationState") == "verified":
        _require(archive.get("verifiedMd5") == EXPECTED_ARCHIVE_MD5, "verified MD5 mismatch")

    return {
        "datasetId": DATASET_ID,
        "rightsApproved": True,
        "commercialTrainingAllowed": True,
        "attributionRequired": True,
        "driveArchivePresent": True,
        "checksumVerified": archive.get("checksumVerificationState") == "verified",
    }


def validate_tar_member_name(member_name: str) -> str:
    """Reject absolute paths, traversal, and empty archive members before extraction."""
    _require(bool(member_name and member_name.strip()), "empty tar member name")
    normalized = member_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    _require(not path.is_absolute(), f"absolute tar member path rejected: {member_name}")
    _require(".." not in path.parts, f"path traversal rejected: {member_name}")
    _require(path.parts and path.parts[0] not in {"", "."}, f"invalid tar member path: {member_name}")
    return str(path)


def source_family_id(file_name: str) -> str:
    """Group pages/fonts derived from the same underlying DeepScores source."""
    name = PurePosixPath(file_name).name
    _require(bool(_IMAGE_RE.search(name)), f"unsupported image filename: {file_name}")
    family = name.split("-aug-", 1)[0] if "-aug-" in name else name.rsplit(".", 1)[0]
    _require(bool(family), f"cannot derive source family from {file_name}")
    return family


def split_source_families(
    train_file_names: Iterable[str],
    held_out_file_names: Iterable[str],
    *,
    development_percent: int = 10,
    seed: str = "st-score-restore-stage11-deepscoresv2-dense-v1",
) -> dict[str, Any]:
    """Preserve official test as held-out; split official train by source family."""
    _require(1 <= development_percent <= 40, "development percent out of bounds")
    train_names = [str(name) for name in train_file_names]
    held_names = [str(name) for name in held_out_file_names]
    _require(bool(train_names), "official train image list is empty")
    _require(bool(held_names), "official held-out image list is empty")

    held_families = {source_family_id(name) for name in held_names}
    eligible_train = [name for name in train_names if source_family_id(name) not in held_families]
    leakage_excluded = [name for name in train_names if source_family_id(name) in held_families]

    family_to_split: dict[str, str] = {}
    for family in sorted({source_family_id(name) for name in eligible_train}):
        digest = hashlib.sha256(f"{seed}:{family}".encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % 100
        family_to_split[family] = "development" if bucket < development_percent else "train"

    train = [name for name in eligible_train if family_to_split[source_family_id(name)] == "train"]
    development = [name for name in eligible_train if family_to_split[source_family_id(name)] == "development"]
    _require(bool(train), "train split is empty")
    _require(bool(development), "development split is empty")

    train_families = {source_family_id(name) for name in train}
    dev_families = {source_family_id(name) for name in development}
    _require(train_families.isdisjoint(dev_families), "train/development source-family leakage")
    _require(train_families.isdisjoint(held_families), "train/held-out source-family leakage")
    _require(dev_families.isdisjoint(held_families), "development/held-out source-family leakage")

    return {
        "train": train,
        "development": development,
        "heldOut": held_names,
        "leakageExcludedFromOfficialTrain": leakage_excluded,
        "familyToSplit": family_to_split,
        "counts": {
            "train": len(train),
            "development": len(development),
            "heldOut": len(held_names),
            "leakageExcluded": len(leakage_excluded),
        },
        "sourceFamilyLeakagePrevented": True,
    }


def degradation_recipe(
    file_name: str,
    variant_index: int,
    *,
    seed: str = "st-score-restore-stage11-synthetic-camera-v1",
) -> dict[str, Any]:
    """Return a deterministic camera-like degradation recipe for one clean patch."""
    _require(variant_index >= 0, "variant index must be non-negative")
    token = hashlib.sha256(f"{seed}:{file_name}:{variant_index}".encode("utf-8")).digest()

    def unit(i: int) -> float:
        return token[i] / 255.0

    return {
        "recipeVersion": "stage11.synthetic-camera.v1",
        "rotationDegrees": round(-2.5 + 5.0 * unit(0), 4),
        "perspectiveFraction": round(0.002 + 0.018 * unit(1), 5),
        "gaussianBlurRadius": round(0.15 + 1.6 * unit(2), 4),
        "brightnessFactor": round(0.78 + 0.42 * unit(3), 4),
        "contrastFactor": round(0.82 + 0.36 * unit(4), 4),
        "noiseSigma": round(0.002 + 0.028 * unit(5), 5),
        "jpegQuality": int(52 + 43 * unit(6)),
        "shadowStrength": round(0.0 + 0.22 * unit(7), 4),
        "thinSymbolPreservationRequired": True,
    }


def attribution_record() -> dict[str, Any]:
    return {
        "dataset": "DeepScoresV2",
        "authors": [
            "Lukas Tuggener",
            "Yvan Putra Satyawan",
            "Alexander Pacha",
            "Jürgen Schmidhuber",
            "Thilo Stadelmann",
        ],
        "doi": SOURCE_DOI,
        "license": LICENSE_ID,
        "licenseUrl": LICENSE_URL,
        "attributionRequired": True,
    }
