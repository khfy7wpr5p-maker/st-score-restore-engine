"""Execute synthetic-only consumer integration checks for the frozen Stage 11 V2a package.

This is a development validation tool. It does not train, tune, read held-out evaluation
artifacts, or authorize production/Stage 12.
"""
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

from st_score_restore.stage11_v2a_consumer_adapter import (
    CONTRACT_ID,
    EVIDENCE_SCHEMA_VERSION,
    EVIDENCE_TYPE,
    EXPECTED_PACKAGE_SHA256,
    EXPECTED_PACKAGE_SIZE_BYTES,
    TorchScriptConsumerAdapter,
    consumer_adapter_contract,
    synthetic_direct_512,
    synthetic_staff_page,
    synthetic_white_small,
    validate_consumer_adapter_evidence,
)

DEFAULT_PACKAGE = Path(
    "/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_PACKAGING/"
    "deepscoresv2_dense_v2a_candidate/v2a_candidate_512.torchscript.pt"
)
DEFAULT_EVIDENCE = Path(
    "/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_PACKAGING/"
    "deepscoresv2_dense_v2a_candidate/consumer_adapter_evidence.v1.json"
)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _case(name: str, adapter: TorchScriptConsumerAdapter, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    restored, metrics = adapter.restore(image)
    return restored, {"name": name, **metrics}


def run(package_path: Path, evidence_path: Path) -> dict[str, Any]:
    import torch

    torch.set_grad_enabled(False)
    torch.manual_seed(0)
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass

    adapter = TorchScriptConsumerAdapter(package_path)
    white_output, white_case = _case("white_small_u8", adapter, synthetic_white_small())
    staff_output, staff_case = _case("synthetic_staff_float", adapter, synthetic_staff_page())
    direct_input = synthetic_direct_512()
    direct_output, direct_case = _case("direct_512_float", adapter, direct_input)
    direct_repeat, _repeat_metrics = adapter.restore(direct_input)
    package_direct = adapter.infer_patch(direct_input)

    repeat_diff = float(np.max(np.abs(direct_output - direct_repeat)))
    direct_parity = float(np.max(np.abs(direct_output - package_direct)))
    if not bool(np.isfinite(white_output).all() and np.isfinite(staff_output).all()):
        raise RuntimeError("synthetic integration output contains non-finite values")

    evidence: dict[str, Any] = {
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
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "device": "CPU",
        },
        "cases": [white_case, staff_case, direct_case],
        "repeatMaxAbsDiff": repeat_diff,
        "direct512ParityMaxAbsDiff": direct_parity,
        "authorization": {
            "developmentConsumerIntegrationValidationAuthorized": True,
            "productionInferenceAuthorized": False,
            "productionPromotionAuthorized": False,
            "stage12EntryAuthorized": False,
        },
        "contract": consumer_adapter_contract(),
    }
    validate_consumer_adapter_evidence(evidence)
    atomic_json(evidence_path, evidence)
    print(json.dumps(evidence, indent=2), flush=True)
    print(f"Evidence: {evidence_path}", flush=True)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()
    run(args.package, args.evidence)


if __name__ == "__main__":
    main()
