#!/usr/bin/env python3
"""Run the frozen V2a preservation review from exact approved non-held-out custody bytes."""
from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import cv2
import numpy as np

from st_score_restore.stage11_v2a_shadow_corpus import build_shadow_corpus_plan
from st_score_restore.stage11_v2a_shadow_handoff import Stage11V2aShadowObserver
from st_score_restore.stage11_v2a_shadow_preservation_review import run_preservation_review

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"


def _source_bindings(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("--source must use datasetItemId=/exact/custody/file")
        item_id, raw_path = value.split("=", 1)
        item_id = item_id.strip()
        if not item_id or item_id in result:
            raise SystemExit("duplicate or empty datasetItemId in --source")
        result[item_id] = Path(raw_path).expanduser()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path, help="Exact frozen V2a TorchScript package")
    parser.add_argument("--source", action="append", default=[], help="datasetItemId=/exact/custody/file")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--render-dpi", type=int, default=72)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    bindings = _source_bindings(args.source)
    if not bindings:
        raise SystemExit("at least one --source binding is required")
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    plan = build_shadow_corpus_plan(catalog, bindings.keys())
    source_bytes = {item_id: path.read_bytes() for item_id, path in bindings.items()}
    observer = Stage11V2aShadowObserver.from_package(args.package)

    try:
        import torch
        torch_version = torch.__version__
    except ImportError:  # pragma: no cover
        torch_version = "unavailable"

    evidence = run_preservation_review(
        plan,
        source_bytes,
        observer,
        render_dpi=args.render_dpi,
        environment={
            "python": platform.python_version(),
            "torch": torch_version,
            "opencv": cv2.__version__,
            "numpy": np.__version__,
            "device": "CPU",
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": evidence["status"],
        "pageCount": evidence["aggregate"]["pageCount"],
        "sourceFamilyCount": evidence["aggregate"]["sourceFamilyCount"],
        "preservationDisposition": evidence["aggregate"]["preservationDisposition"],
        "productionPromotionAuthorized": evidence["authorization"]["productionPromotionAuthorized"],
        "stage12EntryAuthorized": evidence["authorization"]["stage12EntryAuthorized"],
        "output": str(args.output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
