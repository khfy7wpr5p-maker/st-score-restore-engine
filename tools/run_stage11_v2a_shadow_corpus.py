#!/usr/bin/env python3
"""Local/custody runner for Stage 11 V2a approved non-held-out shadow-corpus observation.

Raw source bytes and the frozen package remain outside ordinary Git. The caller explicitly
binds each approved dataset item ID to an exact local custody file.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from st_score_restore.stage11_v2a_shadow_corpus import (
    DEFAULT_RENDER_DPI,
    build_shadow_corpus_plan,
    run_nonheldout_shadow_corpus,
)
from st_score_restore.stage11_v2a_shadow_handoff import Stage11V2aShadowObserver

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"


def _source_bindings(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("--source must use datasetItemId=/path/to/exact-file")
        item_id, path = value.split("=", 1)
        item_id = item_id.strip()
        if not item_id or item_id in result:
            raise SystemExit("duplicate or empty datasetItemId in --source")
        result[item_id] = Path(path).expanduser()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path, help="Exact frozen V2a TorchScript package")
    parser.add_argument("--source", action="append", default=[], help="datasetItemId=/exact/custody/file")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--render-dpi", type=int, default=DEFAULT_RENDER_DPI)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    bindings = _source_bindings(args.source)
    if not bindings:
        raise SystemExit("at least one --source binding is required")
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    plan = build_shadow_corpus_plan(catalog, bindings.keys())
    source_bytes = {item_id: path.read_bytes() for item_id, path in bindings.items()}
    observer = Stage11V2aShadowObserver.from_package(args.package)
    evidence = run_nonheldout_shadow_corpus(
        plan,
        source_bytes,
        observer,
        render_dpi=args.render_dpi,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": evidence["status"],
        "pageObservationCount": evidence["pageObservationCount"],
        "qualityDecisionMade": evidence["aggregate"]["qualityDecisionMade"],
        "productionInferenceAuthorized": evidence["authorization"]["productionInferenceAuthorized"],
        "stage12EntryAuthorized": evidence["authorization"]["stage12EntryAuthorized"],
        "output": str(args.output),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
