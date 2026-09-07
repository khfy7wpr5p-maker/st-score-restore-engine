"""CameraPrIMuS paired-restoration discovery for Stage 11.

This module is intentionally dependency-free so repository CI can validate
pairing, provenance digests, and source-family split isolation without needing
image/ML packages. Image decoding and training happen in the Colab notebook.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "stage11.cameraprimus-paired-restoration.v1"
VALID_SPLITS = {"train", "development", "held_out"}


class Stage11CameraPrIMuSError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Stage11CameraPrIMuSError(message)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def source_family_id(sample_id: str) -> str:
    """Group CameraPrIMuS variants by the stable prefix before the first underscore."""
    value = str(sample_id or "").strip()
    _require(bool(value), "sample id is required")
    return value.split("_", 1)[0]


def split_for_family(family_id: str) -> str:
    """Deterministic 80/10/10 split keyed only by source family."""
    family = str(family_id or "").strip()
    _require(bool(family), "source family id is required")
    bucket = int(hashlib.sha256(family.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "development"
    return "held_out"


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def discover_pairs(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    root = Path(root)
    _require(root.is_dir(), f"CameraPrIMuS corpus directory not found: {root}")
    pairs: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for folder in sorted(path for path in root.iterdir() if path.is_dir()):
        sample_id = folder.name
        source = folder / f"{sample_id}_distorted.jpg"
        target = folder / f"{sample_id}.png"
        if not source.is_file() or not target.is_file():
            rejected.append({"sampleId": sample_id, "reason": "missing_source_or_target"})
            continue

        family = source_family_id(sample_id)
        source_sha = sha256_file(source)
        target_sha = sha256_file(target)
        if source_sha == target_sha:
            rejected.append({"sampleId": sample_id, "reason": "source_target_digest_identical"})
            continue

        record: dict[str, Any] = {
            "pairId": sample_id,
            "sourceFamilyId": family,
            "split": split_for_family(family),
            "sourcePath": _relative(source, root),
            "targetPath": _relative(target, root),
            "sourceSha256": source_sha,
            "targetSha256": target_sha,
            "sourceBytes": source.stat().st_size,
            "targetBytes": target.stat().st_size,
        }
        for suffix, key in (("agnostic", "agnosticPath"), ("semantic", "semanticPath"), ("mei", "meiPath")):
            candidate = folder / f"{sample_id}.{suffix}"
            record[key] = _relative(candidate, root) if candidate.is_file() else None
        pairs.append(record)

    return pairs, rejected


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    _require(manifest.get("contractVersion") == CONTRACT_VERSION, "manifest contract mismatch")
    pairs = manifest.get("pairs")
    _require(isinstance(pairs, list) and bool(pairs), "manifest must contain at least one pair")

    pair_ids: set[str] = set()
    family_splits: dict[str, str] = {}
    for pair in pairs:
        pair_id = str(pair.get("pairId") or "")
        family = str(pair.get("sourceFamilyId") or "")
        split = pair.get("split")
        _require(pair_id and pair_id not in pair_ids, "duplicate or missing pair id")
        pair_ids.add(pair_id)
        _require(bool(family), f"missing source family for {pair_id}")
        _require(split in VALID_SPLITS, f"invalid split for {pair_id}")
        previous = family_splits.setdefault(family, split)
        _require(previous == split, f"source-family split leakage: {family}")
        for key in ("sourceSha256", "targetSha256"):
            value = str(pair.get(key) or "")
            _require(len(value) == 64 and all(ch in "0123456789abcdef" for ch in value), f"invalid {key} for {pair_id}")
        _require(pair["sourceSha256"] != pair["targetSha256"], f"identical source/target digest for {pair_id}")
        for key in ("sourcePath", "targetPath"):
            value = str(pair.get(key) or "")
            _require(value and not value.startswith("/") and ".." not in Path(value).parts, f"unsafe {key} for {pair_id}")

    counts = {split: sum(pair["split"] == split for pair in pairs) for split in sorted(VALID_SPLITS)}
    _require(manifest.get("splitCounts") == counts, "split counts do not match pairs")
    _require(manifest.get("sourceFamilySplitIsolation") is True, "source-family isolation must be asserted")
    return {"pairCount": len(pairs), "sourceFamilyCount": len(family_splits), "splitCounts": counts}


def build_manifest(
    root: Path,
    *,
    rights_status: str = "review_required",
    training_permission_status: str = "granted",
) -> dict[str, Any]:
    pairs, rejected = discover_pairs(Path(root))
    counts = {split: sum(pair["split"] == split for pair in pairs) for split in sorted(VALID_SPLITS)}
    manifest: dict[str, Any] = {
        "contractVersion": CONTRACT_VERSION,
        "dataset": "CameraPrIMuS",
        "datasetRoot": "TEST/CameraPrIMuS/Corpus",
        "pairConvention": {"source": "<id>_distorted.jpg", "target": "<id>.png"},
        "pairCount": len(pairs),
        "rejectedCount": len(rejected),
        "splitCounts": counts,
        "sourceFamilySplitIsolation": True,
        "rightsStatus": rights_status,
        "trainingPermissionStatus": training_permission_status,
        "artifactAccessState": "accessible",
        "trainingExecutable": bool(pairs) and rights_status == "approved" and training_permission_status == "granted",
        "blockingReasonCodes": [] if bool(pairs) and rights_status == "approved" and training_permission_status == "granted" else [
            "CAMERAPRIMUS_RIGHTS_REVIEW_NOT_APPROVED" if rights_status != "approved" else "TRAINING_PERMISSION_NOT_GRANTED"
        ],
        "ordinaryGitArtifactBytesRequired": False,
        "pairs": pairs,
        "rejected": rejected,
    }
    validate_manifest(manifest)
    return manifest


def write_manifest(manifest: dict[str, Any], output_path: Path) -> Path:
    validate_manifest(manifest)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
