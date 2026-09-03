from __future__ import annotations

import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from st_score_restore.review_ui import REVIEW_UI_CSS, REVIEW_UI_HTML, REVIEW_UI_JS

REVIEWER_KEY = "reviewer-key-stage5-browser-qa"
ACTOR_ID = "teacher-stage5-browser-qa"
JOB_ID = "job-stage5-browser-qa"
CANDIDATE_ID = "sha256:" + "c" * 64
SOURCE_CROP_ID = "sha256:" + "1" * 64
CANDIDATE_CROP_ID = "sha256:" + "2" * 64
BUNDLE_V1 = "sha256:" + "a" * 64
BUNDLE_V2 = "sha256:" + "b" * 64
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class FixtureState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.bundle_id = BUNDLE_V1
        self.bundle_get_count = 0
        self.review_post_count = 0
        self.accepted_decision_count = 0
        self.last_decision: dict[str, Any] | None = None
        self.review_decision: dict[str, Any] | None = None


STATE = FixtureState()


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _job_payload() -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "apiVersion": "0.5.0",
        "jobId": JOB_ID,
        "state": "AWAITING_REVIEW",
        "currentAttemptId": "attempt-stage5-browser-qa",
        "updatedAt": "2026-09-03T00:00:00Z",
    }


def _page_payload() -> dict[str, Any]:
    with STATE.lock:
        decision = STATE.review_decision
    return {
        "pageNumber": 1,
        "currentAttemptId": "attempt-stage5-browser-qa",
        "sourceArtifactId": "sha256:" + "0" * 64,
        "currentCandidateArtifactId": CANDIDATE_ID,
        "currentSafetyReportArtifactId": "sha256:" + "d" * 64,
        "currentEvidenceBundleArtifactId": STATE.bundle_id,
        "reviewDecision": decision,
        "selectedArtifactId": CANDIDATE_ID if decision else None,
    }


def _bundle_payload(bundle_id: str) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "apiVersion": "0.5.0",
        "jobId": JOB_ID,
        "pageNumber": 1,
        "evidenceBundleArtifactId": bundle_id,
        "bundle": {
            "schemaVersion": "1.0.0",
            "generatorVersion": "0.5.0",
            "status": "completed",
            "automaticApproval": False,
            "semanticRecognitionClaimed": False,
            "pageNumber": 1,
            "attemptId": "attempt-stage5-browser-qa",
            "navigation": {
                "findingCount": 1,
                "regionalFindingCount": 1,
                "pagination": "finding_index",
                "zoom": {
                    "minimum": 0.25,
                    "maximum": 8.0,
                    "step": 0.25,
                    "fitModes": ["fit_width", "fit_region", "actual_pixels"],
                },
                "keyboardOrder": [
                    "previous_finding",
                    "next_finding",
                    "source_view",
                    "candidate_view",
                    "approve",
                    "reject",
                    "reprocess",
                ],
                "screenReaderLabelsRequired": True,
            },
            "displayIntegrity": {
                "cropEncoding": "png_grayscale_8bit",
                "inputColorProfiles": "not_inspected",
                "colorManagementValidated": False,
            },
            "findings": [
                {
                    "findingIndex": 0,
                    "code": "stage5_browser_qa_finding",
                    "severity": "medium",
                    "semanticCertainty": "not_claimed",
                    "sourceRegion": {"x": 10, "y": 20, "width": 30, "height": 40},
                    "normalizedRegion": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
                    "cropBounds": {"x": 8, "y": 18, "width": 34, "height": 44},
                    "sourceCropArtifactId": SOURCE_CROP_ID,
                    "candidateCropArtifactId": CANDIDATE_CROP_ID,
                }
            ],
            "reviewBinding": {
                "requiredEvidenceBundleArtifactId": True,
                "trainingConsentImplied": False,
            },
        },
    }


class FixtureHandler(BaseHTTPRequestHandler):
    server_version = "Stage5BrowserQAFixture/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: int, content_type: str, body: bytes, *, static: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if static:
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
            )
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return self.headers.get("X-Api-Key") == REVIEWER_KEY and self.headers.get("X-Actor-Id") == ACTOR_ID

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/review":
            self._send(200, "text/html; charset=utf-8", REVIEW_UI_HTML, static=True)
            return
        if path == "/review/styles.css":
            self._send(200, "text/css; charset=utf-8", REVIEW_UI_CSS, static=True)
            return
        if path == "/review/app.js":
            self._send(200, "application/javascript; charset=utf-8", REVIEW_UI_JS, static=True)
            return
        if path == "/favicon.ico":
            self._send(404, "text/plain; charset=utf-8", b"")
            return
        if not self._authorized():
            self._send(401, "application/json; charset=utf-8", _json_bytes({"error": {"code": "authentication_required", "message": "fixture auth required"}}))
            return
        if path == f"/api/v1/restoration-jobs/{JOB_ID}":
            self._send(200, "application/json; charset=utf-8", _json_bytes(_job_payload()))
            return
        if path == f"/api/v1/restoration-jobs/{JOB_ID}/pages":
            self._send(200, "application/json; charset=utf-8", _json_bytes({"jobId": JOB_ID, "pages": [_page_payload()]}))
            return
        if path == f"/api/v1/restoration-jobs/{JOB_ID}/pages/1/review-bundle":
            with STATE.lock:
                STATE.bundle_get_count += 1
                bundle_id = STATE.bundle_id
            self._send(200, "application/json; charset=utf-8", _json_bytes(_bundle_payload(bundle_id)))
            return
        if path in {
            f"/api/v1/restoration-jobs/{JOB_ID}/artifacts/{SOURCE_CROP_ID}",
            f"/api/v1/restoration-jobs/{JOB_ID}/artifacts/{CANDIDATE_CROP_ID}",
        }:
            if parsed.query != "purpose=review":
                self._send(403, "application/json; charset=utf-8", _json_bytes({"error": {"code": "artifact_access_forbidden", "message": "review purpose required"}}))
                return
            self._send(200, "image/png", PNG_1X1)
            return
        self._send(404, "application/json; charset=utf-8", _json_bytes({"error": {"code": "route_not_found", "message": path}}))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if not self._authorized():
            self._send(401, "application/json; charset=utf-8", _json_bytes({"error": {"code": "authentication_required", "message": "fixture auth required"}}))
            return
        if path != f"/api/v1/restoration-jobs/{JOB_ID}/review":
            self._send(404, "application/json; charset=utf-8", _json_bytes({"error": {"code": "route_not_found", "message": path}}))
            return
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        decisions = payload.get("decisions") or []
        decision = decisions[0] if decisions else {}
        with STATE.lock:
            STATE.review_post_count += 1
            STATE.last_decision = dict(decision)
            if STATE.review_post_count == 1:
                STATE.bundle_id = BUNDLE_V2
                self._send(
                    409,
                    "application/json; charset=utf-8",
                    _json_bytes({"error": {"code": "stale_review_evidence", "message": "The supplied review evidence bundle is not current.", "details": {"pageNumber": 1}}}),
                )
                return
            if decision.get("evidenceBundleArtifactId") != STATE.bundle_id:
                self._send(
                    409,
                    "application/json; charset=utf-8",
                    _json_bytes({"error": {"code": "stale_review_evidence", "message": "wrong fixture bundle"}}),
                )
                return
            if decision.get("candidateArtifactId") != CANDIDATE_ID or decision.get("action") != "approve":
                self._send(409, "application/json; charset=utf-8", _json_bytes({"error": {"code": "invalid_review_decision", "message": "fixture expected current approve"}}))
                return
            STATE.accepted_decision_count += 1
            STATE.review_decision = {
                "action": "approve",
                "candidateArtifactId": CANDIDATE_ID,
                "selectedArtifactId": CANDIDATE_ID,
                "evidenceBundleArtifactId": STATE.bundle_id,
                "reviewerId": ACTOR_ID,
            }
        self._send(200, "application/json; charset=utf-8", _json_bytes(_job_payload()))


class DevToolsWebSocket:
    def __init__(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "ws" or not parsed.hostname or not parsed.port:
            raise RuntimeError(f"unsupported DevTools websocket URL: {url}")
        self.sock = socket.create_connection((parsed.hostname, parsed.port), timeout=10)
        self.sock.settimeout(10)
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        path = parsed.path + (("?" + parsed.query) if parsed.query else "")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            f"Origin: http://{parsed.hostname}:{parsed.port}\r\n\r\n"
        ).encode("ascii")
        self.sock.sendall(request)
        response = self._recv_until(b"\r\n\r\n")
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"DevTools websocket handshake failed: {response[:200]!r}")
        self.next_id = 1
        self.pending_events: list[dict[str, Any]] = []

    def _recv_until(self, marker: bytes) -> bytes:
        chunks = bytearray()
        while marker not in chunks:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("socket closed during handshake")
            chunks.extend(chunk)
        return bytes(chunks)

    def _send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        first = 0x81
        mask = secrets.token_bytes(4)
        length = len(payload)
        if length < 126:
            header = bytes([first, 0x80 | length])
        elif length < 65536:
            header = bytes([first, 0x80 | 126]) + struct.pack("!H", length)
        else:
            header = bytes([first, 0x80 | 127]) + struct.pack("!Q", length)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(header + mask + masked)

    def _recv_exact(self, count: int) -> bytes:
        result = bytearray()
        while len(result) < count:
            chunk = self.sock.recv(count - len(result))
            if not chunk:
                raise RuntimeError("DevTools websocket closed")
            result.extend(chunk)
        return bytes(result)

    def _recv_message(self) -> str:
        fragments = bytearray()
        started = False
        while True:
            header = self._recv_exact(2)
            fin = bool(header[0] & 0x80)
            opcode = header[0] & 0x0F
            masked = bool(header[1] & 0x80)
            length = header[1] & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._recv_exact(8))[0]
            mask = self._recv_exact(4) if masked else b""
            payload = self._recv_exact(length)
            if masked:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x8:
                raise RuntimeError("DevTools websocket closed by browser")
            if opcode == 0x9:
                self._send_control(0xA, payload)
                continue
            if opcode in {0x1, 0x0}:
                if opcode == 0x1:
                    fragments = bytearray()
                    started = True
                if started:
                    fragments.extend(payload)
                if fin:
                    return fragments.decode("utf-8")

    def _send_control(self, opcode: int, payload: bytes) -> None:
        mask = secrets.token_bytes(4)
        header = bytes([0x80 | opcode, 0x80 | len(payload)])
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(header + mask + masked)

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = self.next_id
        self.next_id += 1
        self._send_text(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self._recv_message())
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"DevTools command failed {method}: {message['error']}")
                return message.get("result") or {}
            self.pending_events.append(message)

    def close(self) -> None:
        try:
            self._send_control(0x8, b"")
        except Exception:
            pass
        self.sock.close()


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def _find_browser() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("No Chromium/Chrome executable is available for Stage 5 browser QA")


def _read_json_url(url: str, *, method: str = "GET") -> Any:
    request = Request(url, method=method)
    with urlopen(request, timeout=5) as response:  # noqa: S310 - localhost DevTools only
        return json.loads(response.read().decode("utf-8"))


def _wait_json_url(url: str, timeout: float = 15.0) -> Any:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            return _read_json_url(url)
        except (URLError, OSError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _evaluate(ws: DevToolsWebSocket, expression: str) -> Any:
    result = ws.command(
        "Runtime.evaluate",
        {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
            "userGesture": True,
        },
    )
    remote = result.get("result") or {}
    if remote.get("subtype") == "error":
        raise RuntimeError(f"browser evaluation failed: {remote}")
    return remote.get("value")


def _poll_eval(ws: DevToolsWebSocket, expression: str, expected: Any = True, timeout: float = 10.0) -> Any:
    deadline = time.time() + timeout
    value: Any = None
    while time.time() < deadline:
        value = _evaluate(ws, expression)
        if value == expected:
            return value
        time.sleep(0.1)
    raise RuntimeError(f"browser condition timed out: {expression!r}; last={value!r}")


def _ax_value(node: dict[str, Any], field: str) -> str:
    value = node.get(field) or {}
    raw = value.get("value")
    return "" if raw is None else str(raw)


def run_browser_qa() -> dict[str, Any]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    server_port = int(server.server_address[1])
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    browser = _find_browser()
    browser_version = subprocess.check_output([browser, "--version"], text=True).strip()
    debug_port = _free_port()
    profile_dir = tempfile.TemporaryDirectory(prefix="stage5-browser-qa-")
    browser_process = subprocess.Popen(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={profile_dir.name}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ws: DevToolsWebSocket | None = None
    try:
        _wait_json_url(f"http://127.0.0.1:{debug_port}/json/version")
        target_url = f"http://127.0.0.1:{server_port}/review"
        target = _read_json_url(
            f"http://127.0.0.1:{debug_port}/json/new?{target_url}",
            method="PUT",
        )
        ws = DevToolsWebSocket(target["webSocketDebuggerUrl"])
        ws.command("Page.enable")
        ws.command("Runtime.enable")
        ws.command("Accessibility.enable")
        ws.command("Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        _poll_eval(ws, "document.readyState === 'complete'")

        initial_title = _evaluate(ws, "document.title")
        if initial_title != "ST Score Restore - Teacher Review":
            raise RuntimeError(f"unexpected Stage 5 review title: {initial_title!r}")

        _evaluate(
            ws,
            f'''(() => {{
              document.querySelector('#job-id').value = {json.dumps(JOB_ID)};
              document.querySelector('#actor-id').value = {json.dumps(ACTOR_ID)};
              document.querySelector('#reviewer-key').value = {json.dumps(REVIEWER_KEY)};
              document.querySelector('#connection-form').requestSubmit();
              return true;
            }})()''',
        )
        _poll_eval(ws, "document.querySelector('#workspace').hidden === false")
        _poll_eval(ws, "document.querySelector('#finding-code').textContent === 'stage5_browser_qa_finding'")
        _poll_eval(ws, "document.querySelector('#source-image').hidden === false && document.querySelector('#candidate-image').hidden === false")

        password_cleared = _evaluate(ws, "document.querySelector('#reviewer-key').value === ''")
        storage_empty = _evaluate(ws, "localStorage.length === 0 && sessionStorage.length === 0")
        if not password_cleared or not storage_empty:
            raise RuntimeError("review credential browser-storage boundary failed")

        order_ok = _evaluate(
            ws,
            '''(() => {
              const ids = ['previous-finding','next-finding','source-view','candidate-view','approve','reject','reprocess'];
              const elements = ids.map(id => document.getElementById(id));
              return elements.every(Boolean) && elements.every((el, i) => i === 0 || (elements[i - 1].compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING));
            })()''',
        )
        if not order_ok:
            raise RuntimeError("required Stage 5 review control DOM order failed")

        ax_tree = ws.command("Accessibility.getFullAXTree")
        nodes = ax_tree.get("nodes") or []
        button_names = sorted(
            _ax_value(node, "name")
            for node in nodes
            if _ax_value(node, "role") == "button"
        )
        expected_buttons = {
            "Load review",
            "Refresh current evidence",
            "Previous page",
            "Next page",
            "Previous finding",
            "Next finding",
            "Approve candidate",
            "Reject candidate",
            "Reprocess page",
        }
        missing_buttons = sorted(expected_buttons - set(button_names))
        if missing_buttons:
            raise RuntimeError(f"Chrome accessibility tree missing button names: {missing_buttons}")
        unnamed_buttons = [name for name in button_names if not name.strip()]
        if unnamed_buttons:
            raise RuntimeError("Chrome accessibility tree contains unnamed buttons")
        ax_names = {_ax_value(node, "name") for node in nodes}
        for expected_name in (
            "Source evidence image. Use the zoom controls to inspect pixels.",
            "Candidate evidence image. Use the zoom controls to inspect pixels.",
            "Page review decision",
            "Finding navigation",
        ):
            if expected_name not in ax_names:
                raise RuntimeError(f"Chrome accessibility tree missing named review region: {expected_name}")

        ws.command("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
        time.sleep(0.2)
        responsive_stacked = _evaluate(
            ws,
            '''(() => {
              const source = document.querySelector('#source-view').getBoundingClientRect();
              const candidate = document.querySelector('#candidate-view').getBoundingClientRect();
              return candidate.top >= source.bottom - 1 && source.width <= 390 && candidate.width <= 390;
            })()''',
        )
        if not responsive_stacked:
            raise RuntimeError("Stage 5 review evidence did not stack at mobile viewport")

        screenshot = ws.command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        screenshot_bytes = base64.b64decode(screenshot["data"])
        if len(screenshot_bytes) < 1000:
            raise RuntimeError("Stage 5 browser screenshot unexpectedly small")
        screenshot_sha256 = hashlib.sha256(screenshot_bytes).hexdigest()

        _evaluate(ws, "document.querySelector('#approve').click(); true")
        _poll_eval(ws, "document.querySelector('#alert-region').hidden === false")
        stale_text = _evaluate(ws, "document.querySelector('#alert-region').textContent")
        if "stale" not in str(stale_text).lower():
            raise RuntimeError(f"stale-screen alert was not announced: {stale_text!r}")
        deadline = time.time() + 10
        while time.time() < deadline:
            with STATE.lock:
                if STATE.bundle_get_count >= 2 and STATE.accepted_decision_count == 0:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("stale-screen recovery did not reload evidence without recording a decision")

        _poll_eval(ws, "document.querySelector('#approve').disabled === false")
        _evaluate(ws, "document.querySelector('#approve').click(); true")
        deadline = time.time() + 10
        while time.time() < deadline:
            with STATE.lock:
                if STATE.accepted_decision_count == 1:
                    break
            time.sleep(0.1)
        else:
            raise RuntimeError("current evidence-bound approval was not accepted")
        _poll_eval(ws, "document.querySelector('#decision-state').textContent.includes('Recorded decision: approve')")
        _poll_eval(ws, "document.querySelector('#approve').disabled === true")

        with STATE.lock:
            final_decision = dict(STATE.last_decision or {})
            review_posts = STATE.review_post_count
            accepted_decisions = STATE.accepted_decision_count
            bundle_gets = STATE.bundle_get_count
        if final_decision.get("evidenceBundleArtifactId") != BUNDLE_V2:
            raise RuntimeError("second browser review decision was not bound to refreshed evidence")
        if final_decision.get("candidateArtifactId") != CANDIDATE_ID:
            raise RuntimeError("browser review decision was not bound to current candidate")
        if final_decision.get("action") != "approve":
            raise RuntimeError("browser review decision action drifted")

        post_storage_empty = _evaluate(ws, "localStorage.length === 0 && sessionStorage.length === 0")
        if not post_storage_empty:
            raise RuntimeError("browser storage was populated during review flow")

        return {
            "schemaVersion": "1.0.0",
            "qaType": "stage5_local_real_browser_accessibility_tree_and_interaction",
            "browser": browser_version,
            "viewportChecks": ["desktop_1280x900", "mobile_390x844"],
            "checks": {
                "realBrowserDomAndJavaScriptExecuted": True,
                "chromeAccessibilityTreeNamesVerified": True,
                "allPrimaryButtonsNamed": True,
                "sourceCandidateRegionsNamed": True,
                "requiredControlOrderVerified": True,
                "responsiveEvidenceStackVerified": True,
                "reviewerPasswordInputClearedAfterLoad": True,
                "browserStorageRemainedEmpty": True,
                "staleScreenRejectedBeforeDecision": True,
                "staleScreenAlertObserved": True,
                "currentEvidenceReloadedAfterStale": True,
                "currentEvidenceBoundApprovalAccepted": True,
                "decisionBoundToCurrentCandidate": True,
            },
            "fixtureCounters": {
                "reviewPosts": review_posts,
                "acceptedDecisions": accepted_decisions,
                "reviewBundleGets": bundle_gets,
            },
            "screenshot": {
                "retained": False,
                "sha256": screenshot_sha256,
                "byteSize": len(screenshot_bytes),
            },
            "dataBoundary": {
                "syntheticFixtureOnly": True,
                "realScoreBytesUsed": False,
                "privateMetricsUsed": False,
                "productionDeploymentUsed": False,
            },
            "assistiveTechnologyBoundary": {
                "chromeAccessibilityTreeExecuted": True,
                "physicalScreenReaderExecuted": False,
                "physicalScreenReaderClaimed": False,
            },
        }
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        browser_process.terminate()
        try:
            browser_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            browser_process.kill()
        profile_dir.cleanup()
        server.shutdown()
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_browser_qa()
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
