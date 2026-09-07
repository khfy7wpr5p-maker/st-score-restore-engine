#!/usr/bin/env python3
"""Static safety/mobile-resilience validator for the Stage 11 held-out Colab notebook."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/stage11_deepscoresv2_dense_heldout_eval_colab.ipynb"

REQUIRED_TOKENS = (
    "7237318e381e6e0848ec30eb82decb83",
    "08b279161a9e8c4bd37376da221ecb4e07130724254ccf7d9591c8d32f368683",
    "official_held_out_images=352",
    "held_out_variants=2",
    "torch.inference_mode()",
    "torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\")",
    "heldout_eval_progress.v1.json",
    "save_every=8",
    "os.replace",
    "resumedfrompersistedprogress",
    "optimizercreated\":false",
    "backpropagationexecuted\":false",
    "heldoutusedfortraining\":false",
    "heldoutusedfortuning\":false",
    "weightsmutated",
    "heldout_final_evidence.json",
    "finalstage11pass\":false",
)
FORBIDDEN_TOKENS = (
    ".backward(",
    "adam(",
    "adamw(",
    "optimizer.step(",
    "scaler.step(",
    "torch.hub.load",
    "from_pretrained(",
    "wget ",
    "curl ",
    "git clone",
    "nohup",
    "setinterval(",
    "javascript(",
    "keepalive",
)


def main() -> int:
    payload = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    if payload.get("nbformat") != 4:
        raise SystemExit("unexpected notebook format")
    code_cells = [c for c in payload.get("cells", []) if c.get("cell_type") == "code"]
    if len(code_cells) < 2:
        raise SystemExit("held-out notebook is unexpectedly small")
    source = "\n".join(
        "".join(c.get("source", [])) if isinstance(c.get("source"), list) else str(c.get("source") or "")
        for c in code_cells
    )
    source_lower = source.lower()
    for token in REQUIRED_TOKENS:
        if token.lower() not in source_lower:
            raise SystemExit(f"missing held-out safety/resume token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token.lower() in source_lower:
            raise SystemExit(f"forbidden held-out mutation/network/keepalive token: {token}")
    for idx, cell in enumerate(code_cells):
        cell_source = "".join(cell.get("source", [])) if isinstance(cell.get("source"), list) else str(cell.get("source") or "")
        ast.parse(cell_source, filename=f"heldout-notebook-cell-{idx}")
    print(json.dumps({
        "notebook": "valid",
        "codeCells": len(code_cells),
        "optimizerCreated": False,
        "backpropagation": False,
        "heldOutTuning": False,
        "cpuFallback": True,
        "driveProgressResume": True,
        "runtimeLimitBypass": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
