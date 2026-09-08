"""Static fail-closed validation for the Stage 11 V2a frozen-candidate packaging flow."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "stage11_v2a_frozen_candidate_packaging_colab.ipynb"
RUNTIME = ROOT / "tools" / "stage11_v2a_candidate_packaging.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source") or []) for cell in notebook.get("cells") or [])
    require("'main'" in source, "packaging notebook must default to main")
    require("drive.mount('/content/drive')" in source, "packaging notebook must mount Drive")
    require("stage11_v2a_candidate_packaging.py" in source, "packaging runtime invocation missing")
    require("candidate_package_evidence.v1.json" in source, "packaging evidence display missing")
    require("v2a_candidate_512.torchscript.pt" in source, "candidate package display missing")
    require("pip install -e" not in source, "editable install bootstrap is forbidden")
    require("stage11_v2a_autonomous_pipeline.py" not in source, "packaging notebook must not relaunch training pipeline")
    require("--mode" not in source, "packaging notebook must not invoke train/eval modes")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for token in (
        "EXPECTED_CHECKPOINT_SHA256",
        "EXPECTED_CONFIG_SHA256",
        "EXPECTED_DATASET_MD5",
        "EXPECTED_MODEL_STATE_SHA256",
        "EXPECTED_SOURCE_V2_CHECKPOINT_SHA256",
        "torch.jit.trace",
        "torch.jit.freeze",
        "heldOutAccessed\": False",
        "weightsMutated\": False",
        "optimizerCreated\": False",
        "backpropagationExecuted\": False",
        "productionInferenceAuthorized\": False",
        "stage12EntryAuthorized\": False",
    ):
        require(token in runtime, f"packaging runtime safety token missing: {token}")
    for forbidden in (
        "make_dataset(",
        "load_dataset_truth(",
        "torch.optim.",
        ".backward(",
        "optimizer.step(",
        "heldout_evidence",
        "stage9a_symbol_region_evidence",
    ):
        require(forbidden not in runtime, f"packaging runtime forbidden token present: {forbidden}")

    print(json.dumps({
        "status": "pass",
        "notebook": str(NOTEBOOK.relative_to(ROOT)),
        "runtime": str(RUNTIME.relative_to(ROOT)),
        "checkpointIdentityPinned": True,
        "heldoutAccessForbidden": True,
        "trainingForbidden": True,
        "productionInferenceAuthorized": False,
        "stage12EntryAuthorized": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
