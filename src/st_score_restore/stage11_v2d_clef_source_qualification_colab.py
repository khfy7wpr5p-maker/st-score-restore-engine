"""Crash-safe Colab execution for Stage 11 V2d P4 clef source qualification.

Development-only and source-only. This runner never loads Restore output or the
Restore model. It reproduces the frozen Oemer clef extraction used by the V2d
feasibility audit, compares it against the accepted 213 independent teacher boxes
at the preregistered IoU >= 0.50, and persists raw boxes plus page/family/pooled
metrics. Measurement never auto-qualifies the detector.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any, Mapping

import cv2

from .stage11_v2d_clef_source_qualification import (
    EXPECTED_CLEF_BOX_COUNT,
    OEMER_CHECKPOINTS,
    OEMER_COMMIT,
    PRIMARY_IOU_THRESHOLD,
    build_clef_source_qualification_measurement,
    greedy_one_to_one_match,
)
from .stage11_v2d_clef_teacher_completion import (
    COMPLETION_IDENTITY,
    validate_clef_teacher_completion,
)
from .stage11_v2d_colab_runner import _detect_semantic_boxes

RESULT_SCHEMA = "stage11.v2d.clef-source-qualification-execution.v1"
PROGRESS_SCHEMA = "stage11.v2d.clef-source-qualification-page.v1"
PINNED_ORT_VERSION = "1.20.1"
DETECTOR_LOGIC_ID = "stage11_v2d_colab_runner._detect_semantic_boxes.clef-adapter-p4_2-v1"
ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_CLEF_SOURCE_QUALIFICATION")
INPUT_ROOT = ROOT / "exact_inputs"
SOURCE_ROOT = ROOT / "source_pages"
PROGRESS_ROOT = ROOT / "page_results"
CHECKPOINT_ROOT = ROOT / "oemer_checkpoints"
RESULT_PATH = ROOT / "v2d_clef_source_qualification_result.json"
COMPLETION_PATH = ROOT / "clef_box_teacher_completion.v1.json"

SOURCE_TARGETS: dict[str, dict[str, Any]] = {
    "beethoven": {
        "driveId": "1F6Xp6mmwsjmpk64GkcDqw6t0XpH_1IGk",
        "filename": "beethoven-op48-no3.pdf",
        "byteSize": 1182561,
        "sha256": "c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c",
        "kind": "pdf",
        "pages": [2, 3],
        "pageIds": ["beethoven-op48-no3-p2", "beethoven-op48-no3-p3"],
    },
    "wikimedia": {
        "driveId": "1JYyN_nk0lYarszlBlC9nqVfeJxB0FEmz",
        "filename": "wikimedia-guitar-technical-exercise-no1.png",
        "byteSize": 34636,
        "sha256": "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb",
        "kind": "png",
        "pages": [1],
        "pageIds": ["wikimedia-guitar-technical-exercise-no1-p1"],
    },
    "barley": {
        "driveId": "1TsmQFpcM4uv52MH37ilKFj1jYY4pyCrG",
        "filename": "barley-your-face-your-tongue-your-wit.pdf",
        "byteSize": 84689,
        "sha256": "6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e",
        "kind": "pdf",
        "pages": [1, 2],
        "pageIds": ["barley-your-face-your-tongue-your-wit-p1", "barley-your-face-your-tongue-your-wit-p2"],
    },
    "carulli": {
        "driveId": "1TkE4FVRb16IhVkYH5q10WOs4wPRDdhmi",
        "filename": "carulli-morceaux-faciles.pdf",
        "byteSize": 4662523,
        "sha256": "db20e9ce755aa56dd9dbb0436a37a48545442e7961e471f813cde7aaa8fc0f22",
        "kind": "pdf",
        "pages": list(range(2, 11)),
        "pageIds": [f"carulli-morceaux-faciles-p{i}" for i in range(2, 11)],
    },
    "bach": {
        "driveId": "1tgd9EEplOAwJmdurUGctvQ9Rzw6U4zvX",
        "filename": "bach-anna-magdalena.pdf",
        "byteSize": 3235494,
        "sha256": "692d4317375048b9d520b4d756c3ce992e96ca82b10c3026a5925f1a878fc959",
        "kind": "pdf",
        "pages": [4, 10, 24, 40],
        "pageIds": ["bach-anna-magdalena-p4", "bach-anna-magdalena-p10", "bach-anna-magdalena-p24", "bach-anna-magdalena-p40"],
    },
}
CHECKPOINT_DOWNLOADS = {
    "unet_big/model.onnx": {
        "url": "https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model.onnx",
        "byteSize": 70767752,
        "sha256": OEMER_CHECKPOINTS["unet_big/model.onnx"],
    },
    "seg_net/model.onnx": {
        "url": "https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model.onnx",
        "byteSize": 38448467,
        "sha256": OEMER_CHECKPOINTS["seg_net/model.onnx"],
    },
}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _exact(path: Path, byte_size: int, sha256: str) -> bool:
    return path.is_file() and path.stat().st_size == byte_size and sha256_file(path) == sha256


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_bytes(path, (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def _download_drive_file(service: Any, drive_id: str, path: Path, byte_size: int, sha256: str) -> None:
    if _exact(path, byte_size, sha256):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.download.tmp")
    request = service.files().get_media(fileId=drive_id)
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore
    with io.FileIO(tmp, "wb") as handle:
        downloader = MediaIoBaseDownload(handle, request, chunksize=1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    if not _exact(tmp, byte_size, sha256):
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Drive artifact identity mismatch: {path.name}")
    os.replace(tmp, path)


def _drive_service() -> Any:
    from google.colab import auth  # type: ignore
    import google.auth  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    auth.authenticate_user()
    credentials, _ = google.auth.default()
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def _render_pdf_page(pdf: Path, page_number: int, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp_dir:
        base = Path(temp_dir) / "page"
        subprocess.run(
            ["pdftoppm", "-f", str(page_number), "-l", str(page_number), "-singlefile", "-r", "72", "-png", str(pdf), str(base)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        rendered = base.with_suffix(".png")
        if not rendered.is_file():
            raise RuntimeError(f"pdftoppm did not create page {page_number}")
        _atomic_bytes(output, rendered.read_bytes())


def _materialize_source_pages(inputs: Mapping[str, Path], completion: Mapping[str, Any]) -> dict[str, Path]:
    teacher_pages = {str(page["pageId"]): page for page in completion["pages"]}
    result: dict[str, Path] = {}
    for family, spec in SOURCE_TARGETS.items():
        for page_number, page_id in zip(spec["pages"], spec["pageIds"]):
            output = SOURCE_ROOT / f"{page_id}.png"
            review = teacher_pages[page_id]["reviewImage"]
            if not _exact(output, int(review["byteSize"]), str(review["sha256"])):
                if spec["kind"] == "pdf":
                    _render_pdf_page(inputs[family], int(page_number), output)
                else:
                    _atomic_bytes(output, inputs[family].read_bytes())
            if not _exact(output, int(review["byteSize"]), str(review["sha256"])):
                raise RuntimeError(f"source page does not match teacher review image: {page_id}")
            image = cv2.imread(str(output), cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise RuntimeError(f"source page unreadable: {page_id}")
            height, width = image.shape
            if width != int(review["width"]) or height != int(review["height"]):
                raise RuntimeError(f"source page dimensions do not match teacher review image: {page_id}")
            result[page_id] = output
            print(f"source exact PASS: {page_id}")
    if len(result) != 18:
        raise RuntimeError("P4 source page count mismatch")
    return result


def _ensure_checkpoint(rel_path: str, spec: Mapping[str, Any]) -> Path:
    path = CHECKPOINT_ROOT / rel_path
    if not _exact(path, int(spec["byteSize"]), str(spec["sha256"])):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.download.tmp")
        urllib.request.urlretrieve(str(spec["url"]), tmp)
        if not _exact(tmp, int(spec["byteSize"]), str(spec["sha256"])):
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"Oemer checkpoint mismatch: {rel_path}")
        os.replace(tmp, path)
    return path


def _prepare_oemer() -> tuple[Any, dict[str, str]]:
    import onnxruntime as ort  # type: ignore
    if ort.__version__ != PINNED_ORT_VERSION:
        raise RuntimeError(f"onnxruntime must be {PINNED_ORT_VERSION}, got {ort.__version__}")
    providers = ort.get_available_providers()
    if "CPUExecutionProvider" not in providers:
        raise RuntimeError("CPUExecutionProvider is required")
    if "CUDAExecutionProvider" in providers:
        raise RuntimeError("P4 canonical source measurement requires CPU-only onnxruntime")
    from oemer import MODULE_PATH  # type: ignore
    from oemer.ete import generate_pred  # type: ignore
    hashes: dict[str, str] = {}
    for rel_path, spec in CHECKPOINT_DOWNLOADS.items():
        persistent = _ensure_checkpoint(rel_path, spec)
        target = Path(MODULE_PATH) / "checkpoints" / rel_path
        if not _exact(target, int(spec["byteSize"]), str(spec["sha256"])):
            _atomic_bytes(target, persistent.read_bytes())
        if not _exact(target, int(spec["byteSize"]), str(spec["sha256"])):
            raise RuntimeError(f"installed Oemer checkpoint mismatch: {rel_path}")
        hashes[rel_path] = sha256_file(target)
        session = ort.InferenceSession(str(target), providers=["CPUExecutionProvider"])
        if session.get_providers()[0] != "CPUExecutionProvider":
            raise RuntimeError(f"Oemer CPU preflight failed: {rel_path}")
        print(f"Oemer checkpoint PASS: {rel_path}")
    return generate_pred, hashes


def _page_descriptors() -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for family, spec in SOURCE_TARGETS.items():
        out.extend((family, int(page), str(page_id)) for page, page_id in zip(spec["pages"], spec["pageIds"]))
    if len(out) != 18 or len({page_id for _, _, page_id in out}) != 18:
        raise RuntimeError("P4 descriptor mismatch")
    return out


def _teacher_boxes(page: Mapping[str, Any]) -> list[list[float]]:
    boxes = []
    for box in page["clefBoxes"]:
        boxes.append([
            float(box["xMin"]),
            float(box["yMin"]),
            float(box["xMaxExclusive"]),
            float(box["yMaxExclusive"]),
        ])
    return boxes


def _fingerprint(page_id: str, source_sha256: str, teacher_boxes: list[list[float]], checkpoint_hashes: Mapping[str, str]) -> str:
    raw = json.dumps(
        {
            "pageId": page_id,
            "sourceSha256": source_sha256,
            "teacherBoxes": teacher_boxes,
            "oemerCommit": OEMER_COMMIT,
            "checkpoints": dict(checkpoint_hashes),
            "detectorLogic": DETECTOR_LOGIC_ID,
            "iouThreshold": PRIMARY_IOU_THRESHOLD,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load_progress(path: Path, fingerprint: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError, RuntimeError):
        return None
    if payload.get("schemaVersion") != PROGRESS_SCHEMA or payload.get("fingerprint") != fingerprint:
        return None
    return payload


def _compute_page(
    family: str,
    page_id: str,
    source_path: Path,
    teacher_page: Mapping[str, Any],
    generate_pred: Any,
    checkpoint_hashes: Mapping[str, str],
) -> dict[str, Any]:
    teacher = _teacher_boxes(teacher_page)
    semantic = _detect_semantic_boxes(source_path, generate_pred)
    detector = [list(map(float, box)) for box in semantic["clef"]]
    clef_types = [str(value) for value in semantic.get("clef_types", [])]
    if clef_types and len(clef_types) != len(detector):
        raise RuntimeError("clef subtype output does not align with detector boxes")
    key_candidates = [list(map(float, box)) for box in semantic.get("accidental", [])]
    match = greedy_one_to_one_match(teacher, detector, iou_threshold=PRIMARY_IOU_THRESHOLD)
    fingerprint = _fingerprint(page_id, sha256_file(source_path), teacher, checkpoint_hashes)
    return {
        "schemaVersion": PROGRESS_SCHEMA,
        "pageId": page_id,
        "sourceFamily": family,
        "sourceOnly": True,
        "fingerprint": fingerprint,
        "sourceImage": {
            "sha256": sha256_file(source_path),
            "byteSize": source_path.stat().st_size,
        },
        "teacherBoxCount": len(teacher),
        "detectorBoxCount": len(detector),
        "teacherBoxes": teacher,
        "detectorBoxes": detector,
        "detectorClefTypes": clef_types,
        "clefSubtypeBoundary": "development_diagnostic_not_preregistered",
        "keyCandidateCount": len(key_candidates),
        "keyCandidateBoxes": key_candidates,
        "keyMeasurementBoundary": "diagnostic_only_no_teacher_truth",
        "matches": match["matches"],
        "tp": match["tp"],
        "fp": match["fp"],
        "fn": match["fn"],
        "precision": match["precision"],
        "recall": match["recall"],
        "f1": match["f1"],
    }


def run() -> Path:
    if not Path("/content/drive/MyDrive").exists():
        raise FileNotFoundError("Google Drive is not mounted")
    ROOT.mkdir(parents=True, exist_ok=True)
    service = _drive_service()

    _download_drive_file(
        service,
        str(COMPLETION_IDENTITY["driveFileId"]),
        COMPLETION_PATH,
        int(COMPLETION_IDENTITY["byteSize"]),
        str(COMPLETION_IDENTITY["sha256"]),
    )
    completion = _load_json(COMPLETION_PATH)
    repo = Path(__file__).resolve().parents[2]
    amendment = _load_json(repo / "evidence/stage11/v2d/v2d-clef-teacher-taxonomy-amendment.v1.json")
    completion_validation = validate_clef_teacher_completion(completion, amendment)
    if completion_validation["clefBoxCount"] != EXPECTED_CLEF_BOX_COUNT:
        raise RuntimeError("teacher clef box count mismatch")
    print("teacher completion PASS:", completion_validation)

    inputs: dict[str, Path] = {}
    for family, spec in SOURCE_TARGETS.items():
        path = INPUT_ROOT / str(spec["filename"])
        _download_drive_file(service, str(spec["driveId"]), path, int(spec["byteSize"]), str(spec["sha256"]))
        inputs[family] = path
        print(f"input exact PASS: {family}")

    source_paths = _materialize_source_pages(inputs, completion)
    generate_pred, checkpoint_hashes = _prepare_oemer()
    teacher_pages = {str(page["pageId"]): page for page in completion["pages"]}

    page_records: list[dict[str, Any]] = []
    for index, (family, _page_number, page_id) in enumerate(_page_descriptors(), 1):
        source_path = source_paths[page_id]
        teacher = _teacher_boxes(teacher_pages[page_id])
        fingerprint = _fingerprint(page_id, sha256_file(source_path), teacher, checkpoint_hashes)
        progress_path = PROGRESS_ROOT / f"{page_id}.json"
        record = _load_progress(progress_path, fingerprint)
        if record is None:
            record = _compute_page(family, page_id, source_path, teacher_pages[page_id], generate_pred, checkpoint_hashes)
            _atomic_json(progress_path, record)
            print(f"P4 detector SAVED {index:02d}/18 {page_id}")
        else:
            print(f"P4 detector cache reuse {index:02d}/18 {page_id}")
        page_records.append(record)

    metrics_input = [
        {
            "pageId": record["pageId"],
            "sourceFamily": record["sourceFamily"],
            "sourceOnly": True,
            "teacherBoxCount": record["teacherBoxCount"],
            "tp": record["tp"],
            "fp": record["fp"],
            "fn": record["fn"],
            "precision": record["precision"],
            "recall": record["recall"],
            "f1": record["f1"],
        }
        for record in page_records
    ]
    measurement = build_clef_source_qualification_measurement(metrics_input)
    result = {
        "schemaVersion": RESULT_SCHEMA,
        "contractId": "stage11.v2c.semantic-preservation.nonheldout.v1",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "P4_SOURCE_ONLY_CLEF_DETECTOR_QUALIFICATION_MEASUREMENT",
        "teacherTruth": dict(COMPLETION_IDENTITY),
        "detector": {
            "candidateId": "oemer-onnx-segmentation-dbe2a933",
            "upstreamCommit": OEMER_COMMIT,
            "checkpointSha256": checkpoint_hashes,
            "executionProvider": "CPUExecutionProvider",
            "onnxruntimeVersion": PINNED_ORT_VERSION,
            "logic": DETECTOR_LOGIC_ID,
            "coordinateSpace": "original_source_image_pixels",
            "clefSubtypeClassificationEvaluated": False,
            "clefSubtypeDiagnosticAvailable": True,
            "supportedClefSubtypeDiagnostics": ["treble", "bass"],
        },
        "matching": {
            "method": "greedy_one_to_one_descending_iou",
            "primaryIouThreshold": PRIMARY_IOU_THRESHOLD,
            "thresholdPreregistered": True,
        },
        "keySignatureDiagnostic": {
            "status": "unscored",
            "teacherTruthAvailable": False,
            "candidateCount": sum(int(record.get("keyCandidateCount", 0)) for record in page_records),
            "reason": "key candidates are recorded separately and never mixed into the clef score",
        },
        "pageEvidence": page_records,
        "sourceFamilyMetrics": measurement["sourceFamilyMetrics"],
        "pooledMetrics": measurement["pooledMetrics"],
        "decisionBoundary": {
            "measurementComplete": True,
            "detectorQualified": False,
            "qualificationDecisionRequired": True,
            "restoredImagesEvaluated": False,
            "semanticPreservationEstablished": False,
            "overallStage11PassAuthorized": False,
            "productionReady": False,
            "stage12EntryAuthorized": False,
        },
    }
    _atomic_json(RESULT_PATH, result)
    print("P4 CLEF SOURCE QUALIFICATION MEASUREMENT PASS")
    print("SAVED:", RESULT_PATH)
    print("SHA-256:", sha256_file(RESULT_PATH))
    print("POOLED:", result["pooledMetrics"])
    return RESULT_PATH


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if not args.run:
        raise SystemExit("Refusing implicit execution; pass --run")
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
