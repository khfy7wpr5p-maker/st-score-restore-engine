from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import run_stage5_review_ui_browser_qa as qa


_ORIGINAL_EVALUATE = qa._evaluate
_FIRST_APPROVE_CLICK = True


def _evaluate_after_ready(ws: qa.DevToolsWebSocket, expression: str):
    global _FIRST_APPROVE_CLICK
    if _FIRST_APPROVE_CLICK and "document.querySelector('#approve').click()" in expression:
        deadline = time.time() + 10.0
        enabled = False
        while time.time() < deadline:
            enabled = bool(_ORIGINAL_EVALUATE(ws, "document.querySelector('#approve').disabled === false"))
            if enabled:
                break
            time.sleep(0.05)
        if not enabled:
            raise RuntimeError("approve action never became enabled after the initial review evidence load")
        _FIRST_APPROVE_CLICK = False
    return _ORIGINAL_EVALUATE(ws, expression)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    qa._evaluate = _evaluate_after_ready
    result = qa.run_browser_qa()
    result["harnessSynchronization"] = {
        "firstApproveWaitedUntilEnabled": True,
        "uiBehaviorChanged": False,
    }
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
