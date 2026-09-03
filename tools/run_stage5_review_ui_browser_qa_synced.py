from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import run_stage5_review_ui_browser_qa as qa


_ORIGINAL_EVALUATE = qa._evaluate
_ORIGINAL_POLL_EVAL = qa._poll_eval
_ORIGINAL_TEMPORARY_DIRECTORY = qa.tempfile.TemporaryDirectory
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


def _poll_eval_after_review_navigation(ws: qa.DevToolsWebSocket, expression: str, *args, **kwargs):
    if expression == "document.readyState === 'complete'":
        expression = "location.pathname === '/review' && document.readyState === 'complete'"
    return _ORIGINAL_POLL_EVAL(ws, expression, *args, **kwargs)


def _temporary_directory_with_cleanup_race_tolerance(*args, **kwargs):
    """Tolerate Chrome's post-exit profile-file race without weakening QA assertions."""

    kwargs.setdefault("ignore_cleanup_errors", True)
    return _ORIGINAL_TEMPORARY_DIRECTORY(*args, **kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    qa._evaluate = _evaluate_after_ready
    qa._poll_eval = _poll_eval_after_review_navigation
    qa.tempfile.TemporaryDirectory = _temporary_directory_with_cleanup_race_tolerance
    result = qa.run_browser_qa()
    result["harnessSynchronization"] = {
        "reviewNavigationWaitedForExpectedPath": True,
        "firstApproveWaitedUntilEnabled": True,
        "chromeProfileCleanupRaceToleratedAfterProcessExit": True,
        "uiBehaviorChanged": False,
        "qaAssertionsChanged": False,
    }
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
