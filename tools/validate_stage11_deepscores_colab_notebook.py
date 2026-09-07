#!/usr/bin/env python3
"""Static safety/shape validator for the Stage 11 DeepScoresV2 Colab notebook."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "stage11_deepscoresv2_dense_residual_unet_colab.ipynb"

REQUIRED_TOKENS = (
    "7237318e381e6e0848ec30eb82decb83",
    "741814529",
    "deepscores_train.json",
    "deepscores_test.json",
    "1362",
    "352",
    "source-family leakage",
    "patch=512",
    "batch=4",
    "epochs=20",
    "last.pt",
    "best.pt",
    "first_gpu_run_evidence.json",
    "run_held_out_final=false",
    "pretrainedweights\":false",
)
FORBIDDEN_TOKENS = (
    "wget ",
    "curl ",
    "git clone",
    "torch.hub.load",
    "from_pretrained(",
)


def main() -> int:
    payload = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    if payload.get("nbformat") != 4:
        raise SystemExit("unexpected notebook format")
    code_cells = [cell for cell in payload.get("cells", []) if cell.get("cell_type") == "code"]
    if len(code_cells) < 4:
        raise SystemExit("notebook is unexpectedly small")
    source = "\n".join(
        "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else str(cell.get("source") or "")
        for cell in code_cells
    )
    normalized_source = source.casefold()
    for token in REQUIRED_TOKENS:
        if token.casefold() not in normalized_source:
            raise SystemExit(f"missing notebook safety token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token.casefold() in normalized_source:
            raise SystemExit(f"forbidden network/pretrained action in notebook: {token}")
    for idx, cell in enumerate(code_cells):
        cell_source = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else str(cell.get("source") or "")
        ast.parse(cell_source, filename=f"notebook-cell-{idx}")
    print(
        json.dumps(
            {
                "notebook": "valid",
                "codeCells": len(code_cells),
                "heldOutDefault": False,
                "externalPretrainedDownloads": False,
                "tokenMatching": "case_insensitive",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
