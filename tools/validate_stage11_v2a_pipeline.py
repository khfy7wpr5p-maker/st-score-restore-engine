"""Static fail-closed validation for the Stage 11 V2a autonomous Colab pipeline."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/stage11_deepscoresv2_dense_v2a_autonomous_symbol_preservation_colab.ipynb"
RUNTIME = ROOT / "tools/stage11_v2a_colab_runtime.py"
PIPELINE = ROOT / "tools/stage11_v2a_autonomous_pipeline.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source") or []) for cell in notebook.get("cells") or [])
    require("start_new_session=True" in source, "V2a notebook must launch a detached background process")
    require("pipeline_status.v2a.json" in source, "V2a notebook must expose Drive pipeline status")
    require("run_status.v2a.json" in source, "V2a notebook must expose live Drive status")
    require("'main'" in source, "V2a notebook must default to main")
    require("pip install -e" not in source, "editable install bootstrap is forbidden in Colab")
    require("T4 GPU" in source, "V2a notebook must fail closed without GPU")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for token in (
        "EXPECTED_V2_BEST_SHA256",
        "partial.pt",
        "PARTIAL_EVERY_BATCHES = 128",
        "V2A_LOSS_WEIGHTS",
        "v2a_candidate_gate",
        "heldOutUsedForTraining\": False",
        "heldOutUsedForTuning\": False",
        "V2a development gate did not pass; frozen held-out/Stage9A remain forbidden",
    ):
        require(token in runtime, f"V2a runtime safety token missing: {token}")

    pipeline = PIPELINE.read_text(encoding="utf-8")
    gate_pos = pipeline.find("eligibleForFrozenHeldOutEvaluation")
    heldout_pos = pipeline.find('run("heldout")')
    require(gate_pos >= 0 and heldout_pos > gate_pos, "held-out must occur only after the V2a development gate")
    require("productionPromotionAuthorized=False" in pipeline, "production promotion must remain forbidden")
    require("stage12EntryAuthorized=False" in pipeline, "Stage 12 entry must remain forbidden")

    print(json.dumps({
        "status": "pass",
        "notebook": str(NOTEBOOK.relative_to(ROOT)),
        "runtime": str(RUNTIME.relative_to(ROOT)),
        "pipeline": str(PIPELINE.relative_to(ROOT)),
        "backgroundProcess": True,
        "partialCheckpointResume": True,
        "heldOutGateEnforced": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
