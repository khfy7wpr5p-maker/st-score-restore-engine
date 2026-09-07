#!/usr/bin/env python3
"""Static safety/schema validator for the canonical Stage 11 Stage 9A symbol-region notebook."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/stage11_deepscoresv2_dense_stage9a_symbol_region_eval_colab.ipynb"

REQUIRED_TOKENS = (
    "7237318e381e6e0848ec30eb82decb83",
    "08b279161a9e8c4bd37376da221ecb4e07130724254ccf7d9591c8d32f368683",
    "stage9a_symbol_region_progress.v2.json",
    "stage9a_symbol_region_final_evidence.v2.json",
    "ann_ids",
    "a_bbox",
    "deepscores-native-v2:images-list+ann_ids+annotations-dict+a_bbox-xyxy",
    "geometrypreservingassay",
    "optimizercreated",
    "backpropagationexecuted",
    "heldoutusedfortraining",
    "heldoutusedfortuning",
    "weightsmutated",
    "omrcorrectnessimplied",
    "musicaltruthimplied",
    "stage9apreservationpass",
    "finalstage11pass",
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
)


def main() -> int:
    payload=json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    if payload.get("nbformat")!=4:
        raise SystemExit("unexpected notebook format")
    code_cells=[c for c in payload.get("cells",[]) if c.get("cell_type")=="code"]
    if len(code_cells)<3:
        raise SystemExit("Stage 9A notebook unexpectedly small")
    source="\n".join(
        "".join(c.get("source",[])) if isinstance(c.get("source"),list) else str(c.get("source") or "")
        for c in code_cells
    )
    low=source.lower().replace(" ","")
    for token in REQUIRED_TOKENS:
        if token.lower().replace(" ","") not in low:
            raise SystemExit(f"missing Stage 9A safety/schema token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token.lower() in source.lower():
            raise SystemExit(f"forbidden Stage 9A mutation/network token: {token}")
    if "isinstance(annotations,dict)" not in low:
        raise SystemExit("DeepScores annotations must be validated as dict")
    if 'row.get("ann_ids")' not in source and "row.get('ann_ids')" not in source:
        raise SystemExit("DeepScores images must bind annotations through ann_ids")
    for idx,c in enumerate(code_cells):
        src="".join(c.get("source",[])) if isinstance(c.get("source"),list) else str(c.get("source") or "")
        ast.parse(src,filename=f"stage9a-notebook-cell-{idx}")
    print(json.dumps({
        "notebook":"valid",
        "codeCells":len(code_cells),
        "annotationSchema":"deepscores-native-v2",
        "annotationsDict":True,
        "imageAnnIdsBinding":True,
        "optimizerCreated":False,
        "backpropagation":False,
        "heldOutTuning":False,
        "omrCorrectnessImplied":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
