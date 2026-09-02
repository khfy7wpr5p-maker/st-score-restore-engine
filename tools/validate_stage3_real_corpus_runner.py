from __future__ import annotations

import json
from pathlib import Path
import sys

from st_score_restore.dataset_contract_common import canonical_sha256
from st_score_restore.pdf_pipeline import RENDERER_BINDING_VERSION
from st_score_restore.stage3_purpose_grants import validate_stage3_purpose_grants
from st_score_restore.stage3_real_corpus_execution import (
    ACCEPTED_CATALOG_CANONICAL_SHA256,
    BARLEY_ID,
    BEETHOVEN_ID,
    CHOPIN_ID,
    EXPECTED_ITEM_IDS,
    REQUIRED_RENDERER_BINDING_VERSION,
    RUNNER_VERSION,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "evidence" / "stage1c" / "corpus" / "catalog.v2.json"
GRANTS_PATH = ROOT / "evidence" / "stage3" / "governance" / "purpose-grants.v1.json"


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    grants = json.loads(GRANTS_PATH.read_text(encoding="utf-8"))
    require(
        RENDERER_BINDING_VERSION == REQUIRED_RENDERER_BINDING_VERSION == "5.13.0",
        f"real corpus runner renderer binding drifted: {RENDERER_BINDING_VERSION}",
    )
    require(
        canonical_sha256(catalog) == ACCEPTED_CATALOG_CANONICAL_SHA256,
        "real corpus runner catalog digest drifted",
    )
    try:
        validate_stage3_purpose_grants(grants)
    except Exception as exc:
        failures.append(f"merged Beethoven/Barley purpose grant failed validation: {type(exc).__name__}: {exc}")
    require(
        EXPECTED_ITEM_IDS == (BEETHOVEN_ID, BARLEY_ID, CHOPIN_ID),
        "real corpus runner item order/set drifted",
    )
    require(len(set(EXPECTED_ITEM_IDS)) == 3, "real corpus runner item set contains duplicates")

    runner_source = (ROOT / "src" / "st_score_restore" / "stage3_real_corpus_execution.py").read_text(encoding="utf-8")
    require("custody_output_inside_repository" in runner_source, "runner does not refuse custody output inside Git")
    require("real_source_inside_repository" in runner_source, "runner does not refuse real corpus source inside Git")
    require('"stage3ExitPass": False' in runner_source, "runner could overstate Stage 3 exit")
    require('"stage4EntryAuthorized": False' in runner_source, "runner could authorize Stage 4")
    require('"heldOutThresholdTuningUsed": False' in runner_source, "runner does not preserve held-out non-tuning")

    if failures:
        print("Stage 3 real-corpus runner validation: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stage 3 real-corpus runner validation: PASS")
    print(f"- runner version: {RUNNER_VERSION}")
    print(f"- renderer binding: pypdfium2 {RENDERER_BINDING_VERSION}")
    print("- batch: Beethoven + Barley + Chopin")
    print("- real sources/private outputs: outside ordinary Git")
    print("- Stage 3 exit / Stage 4 entry: not authorized by runner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
