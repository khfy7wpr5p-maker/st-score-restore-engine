"""Synthetic-only staging request/response smoke execution for the frozen V2a package."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.stage11_v2a_consumer_adapter import EXPECTED_PACKAGE_SHA256, EXPECTED_PACKAGE_SIZE_BYTES
from st_score_restore.stage11_v2a_staging_api import (
    CONTRACT_ID,
    EVIDENCE_SCHEMA_VERSION,
    EVIDENCE_TYPE,
    TorchScriptStagingService,
    encode_grayscale_png,
    staging_api_contract,
    validate_staging_api_evidence,
)

DEFAULT_PACKAGE = Path(
    "/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_PACKAGING/"
    "deepscoresv2_dense_v2a_candidate/v2a_candidate_512.torchscript.pt"
)
DEFAULT_EVIDENCE = Path(
    "/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_PACKAGING/"
    "deepscoresv2_dense_v2a_candidate/staging_api_evidence.v1.json"
)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def synthetic_staff_u8() -> np.ndarray:
    page = np.full((700, 900), 255, dtype=np.uint8)
    for base in range(80, 620, 120):
        for offset in range(0, 50, 10):
            page[base + offset:base + offset + 2, 40:860] = 0
    for x in (120, 240, 360, 480, 600, 720):
        page[100:650, x:x + 2] = 0
    return page


def run(package_path: Path, evidence_path: Path) -> dict[str, Any]:
    import cv2
    import torch

    torch.set_grad_enabled(False)
    service = TorchScriptStagingService(package_path)
    request_body = encode_grayscale_png(synthetic_staff_u8())
    metadata = {"requestId": "stage11-synthetic-staff-001", "sourceDataKind": "synthetic_only"}
    response_body, first = service.handle(request_body, metadata)
    repeat_body, repeat = service.handle(request_body, metadata)

    evidence = {
        "schemaVersion": EVIDENCE_SCHEMA_VERSION,
        "artifactType": EVIDENCE_TYPE,
        "status": "completed",
        "contractId": CONTRACT_ID,
        "packageSha256": EXPECTED_PACKAGE_SHA256,
        "packageSizeBytes": EXPECTED_PACKAGE_SIZE_BYTES,
        "packagePath": str(package_path),
        "sourceDataKind": "synthetic_only",
        "heldOutAccessed": False,
        "optimizerCreated": False,
        "backpropagationExecuted": False,
        "weightsMutated": False,
        "networkRouteRegistered": False,
        "existingHttpApiModified": False,
        "realUserDataUsed": False,
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "opencv": cv2.__version__,
            "device": "CPU",
        },
        "execution": {
            **first,
            "repeatResponseSha256": repeat["responseSha256"],
            "repeatMetadataEqual": first == repeat,
        },
        "authorization": staging_api_contract()["authorization"],
        "contract": staging_api_contract(),
    }
    if response_body != repeat_body:
        raise RuntimeError("staging response bytes are not deterministic on repeat")
    validate_staging_api_evidence(evidence)
    atomic_json(evidence_path, evidence)
    print(json.dumps(evidence, indent=2), flush=True)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()
    run(args.package, args.evidence)


if __name__ == "__main__":
    main()
