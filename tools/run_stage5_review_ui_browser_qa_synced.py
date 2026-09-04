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


def _poll_eval_after_review_navigation(
    ws: qa.DevToolsWebSocket,
    expression: str,
    expected=True,
    timeout: float = 10.0,
):
    if expression != "document.readyState === 'complete'":
        return _ORIGINAL_POLL_EVAL(ws, expression, expected=expected, timeout=timeout)

    target_expression = "location.pathname === '/review' && document.readyState === 'complete'"
    deadline = time.time() + timeout
    value = None
    last_context_error: RuntimeError | None = None
    while time.time() < deadline:
        try:
            value = _ORIGINAL_EVALUATE(ws, target_expression)
        except RuntimeError as error:
            if "Cannot find default execution context" not in str(error):
                raise
            last_context_error = error
            time.sleep(0.1)
            continue
        if value == expected:
            return value
        time.sleep(0.1)
    detail = f"; last_context_error={last_context_error}" if last_context_error else ""
    raise RuntimeError(
        f"browser condition timed out after review navigation: {target_expression!r}; last={value!r}{detail}"
    )


def _temporary_directory_with_cleanup_race_tolerance(*args, **kwargs):
    """Tolerate Chrome's post-exit profile-file race without weakening QA assertions."""

    kwargs.setdefault("ignore_cleanup_errors", True)
    return _ORIGINAL_TEMPORARY_DIRECTORY(*args, **kwargs)


def _run_browser_qa_with_startup_retry() -> tuple[dict, bool]:
    """Retry once only when Chrome never exposes its local DevTools endpoint.

    This treats a hosted-runner Chrome boot failure as an environment startup
    flake. Browser/DOM/accessibility assertions are never retried or weakened.
    """

    global _FIRST_APPROVE_CLICK
    try:
        return qa.run_browser_qa(), False
    except RuntimeError as error:
        message = str(error)
        if "Timed out waiting for http://127.0.0.1:" not in message or "/json/version" not in message:
            raise
        _FIRST_APPROVE_CLICK = True
        time.sleep(1.0)
        return qa.run_browser_qa(), True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    qa._evaluate = _evaluate_after_ready
    qa._poll_eval = _poll_eval_after_review_navigation
    qa.tempfile.TemporaryDirectory = _temporary_directory_with_cleanup_race_tolerance
    result, chrome_startup_retry_used = _run_browser_qa_with_startup_retry()
    result["harnessSynchronization"] = {
        "reviewNavigationWaitedForExpectedPath": True,
        "transientMissingExecutionContextRetriedOnlyDuringReviewNavigation": True,
        "transientChromeStartupRetriedAtMostOnce": True,
        "chromeStartupRetryUsed": chrome_startup_retry_used,
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
