"""Static fail-closed validation for Stage 11 V2 Colab entrypoints and runtime."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = {
    "train": ROOT / "notebooks/stage11_deepscoresv2_dense_residual_unet_v2_symbol_preservation_colab.ipynb",
    "dev": ROOT / "notebooks/stage11_deepscoresv2_dense_v2_dev_eval_colab.ipynb",
    "heldout": ROOT / "notebooks/stage11_deepscoresv2_dense_v2_heldout_eval_colab.ipynb",
    "stage9a": ROOT / "notebooks/stage11_deepscoresv2_dense_v2_stage9a_symbol_region_eval_colab.ipynb",
}
RUNTIME = ROOT / "tools/stage11_v2_colab_runtime.py"
EXPECTED_BRANCH = "stage11-v2-symbol-preservation-residual-unet"


def notebook_code(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("nbformat") != 4:
        raise ValueError(f"{path.name}: unexpected notebook version")
    cells = payload.get("cells") or []
    if not any(cell.get("cell_type") == "markdown" for cell in cells):
        raise ValueError(f"{path.name}: missing policy markdown")
    code = "\n".join("".join(cell.get("source") or []) for cell in cells if cell.get("cell_type") == "code")
    ast.parse(code)
    return code


def main() -> None:
    for mode, path in NOTEBOOKS.items():
        code = notebook_code(path)
        required = ("drive.mount", EXPECTED_BRANCH, "stage11_v2_colab_runtime.py", f'"{mode}"')
        for token in required:
            if token not in code:
                raise ValueError(f"{path.name}: missing token {token}")
        for forbidden in ("keepalive", "while True", "xset", "caffeinate"):
            if forbidden in code:
                raise ValueError(f"{path.name}: forbidden runtime-bypass token {forbidden}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    ast.parse(runtime)
    for token in (
        "split_source_families", "EXPECTED_ARCHIVE_MD5", "development_gate",
        "development evidence missing; held-out/Stage9A remain gated",
        "weightsMutated", "optimizerCreated", "backpropagationExecuted",
        "heldOutUsedForTraining", "heldOutUsedForTuning", "modelStateSha256Before",
        "modelStateSha256After", "progress_path", "atomic_json",
    ):
        if token not in runtime:
            raise ValueError(f"V2 runtime missing governance token: {token}")
    print({"stage11V2NotebooksValid": True, "modes": sorted(NOTEBOOKS)})


if __name__ == "__main__":
    main()
