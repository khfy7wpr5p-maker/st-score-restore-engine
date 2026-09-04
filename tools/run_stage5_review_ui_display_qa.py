from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer

import run_stage5_review_ui_browser_qa as qa


def _load_review(ws: qa.DevToolsWebSocket) -> None:
    qa._evaluate(
        ws,
        f'''(() => {{
          document.querySelector('#job-id').value = {json.dumps(qa.JOB_ID)};
          document.querySelector('#actor-id').value = {json.dumps(qa.ACTOR_ID)};
          document.querySelector('#reviewer-key').value = {json.dumps(qa.REVIEWER_KEY)};
          document.querySelector('#connection-form').requestSubmit();
          return true;
        }})()''',
    )
    qa._poll_eval(ws, "document.querySelector('#workspace').hidden === false")
    qa._poll_eval(ws, "document.querySelector('#source-image').hidden === false && document.querySelector('#candidate-image').hidden === false")
    qa._poll_eval(ws, "document.querySelector('#source-image').complete && document.querySelector('#source-image').naturalWidth > 0")
    qa._poll_eval(ws, "document.querySelector('#candidate-image').complete && document.querySelector('#candidate-image').naturalWidth > 0")


def _image_probe_expression(image_id: str) -> str:
    return f'''(() => {{
      const img = document.querySelector({json.dumps('#' + image_id)});
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d', {{willReadFrequently: true}});
      ctx.drawImage(img, 0, 0);
      const data = Array.from(ctx.getImageData(0, 0, canvas.width, canvas.height).data);
      let grayscale = true;
      for (let i = 0; i < data.length; i += 4) {{
        if (data[i] !== data[i + 1] || data[i + 1] !== data[i + 2]) grayscale = false;
      }}
      const rect = img.getBoundingClientRect();
      const style = getComputedStyle(img);
      return {{
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight,
        renderedWidth: rect.width,
        renderedHeight: rect.height,
        transform: style.transform,
        grayscale,
        pixelCount: canvas.width * canvas.height,
      }};
    }})()'''


def run_display_qa() -> dict[str, object]:
    with qa.STATE.lock:
        qa.STATE.bundle_id = qa.BUNDLE_V1
        qa.STATE.bundle_get_count = 0
        qa.STATE.review_post_count = 0
        qa.STATE.accepted_decision_count = 0
        qa.STATE.last_decision = None
        qa.STATE.review_decision = None

    server = ThreadingHTTPServer(("127.0.0.1", 0), qa.FixtureHandler)
    server_port = int(server.server_address[1])
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    browser = qa._find_browser()
    browser_version = subprocess.check_output([browser, "--version"], text=True).strip()
    debug_port = qa._free_port()
    profile_dir = tempfile.TemporaryDirectory(prefix="stage5-display-qa-", ignore_cleanup_errors=True)
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
    ws: qa.DevToolsWebSocket | None = None
    try:
        qa._wait_json_url(f"http://127.0.0.1:{debug_port}/json/version")
        target_url = f"http://127.0.0.1:{server_port}/review"
        target = qa._read_json_url(f"http://127.0.0.1:{debug_port}/json/new?{target_url}", method="PUT")
        ws = qa.DevToolsWebSocket(target["webSocketDebuggerUrl"])
        ws.command("Page.enable")
        ws.command("Runtime.enable")
        ws.command("Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        qa._poll_eval(ws, "location.pathname === '/review' && document.readyState === 'complete'")
        _load_review(ws)

        limits_text = str(qa._evaluate(ws, "document.querySelector('.limits').textContent"))
        if "grayscale" not in limits_text.lower() or "color fidelity is not claimed" not in limits_text.lower():
            raise RuntimeError("review UI does not state the bounded grayscale/no-color-fidelity display contract")

        display_integrity = qa._evaluate(
            ws,
            "({cropEncoding: state.bundleResponse.bundle.displayIntegrity.cropEncoding, inputColorProfiles: state.bundleResponse.bundle.displayIntegrity.inputColorProfiles, colorManagementValidated: state.bundleResponse.bundle.displayIntegrity.colorManagementValidated})",
        )
        expected_integrity = {
            "cropEncoding": "png_grayscale_8bit",
            "inputColorProfiles": "not_inspected",
            "colorManagementValidated": False,
        }
        if display_integrity != expected_integrity:
            raise RuntimeError(f"unexpected display-integrity contract: {display_integrity!r}")

        qa._evaluate(
            ws,
            "document.querySelector('#zoom-mode').value='actual_pixels'; document.querySelector('#zoom-slider').value='1'; document.querySelector('#zoom-mode').dispatchEvent(new Event('change', {bubbles:true})); true",
        )
        qa._poll_eval(ws, "document.querySelector('#source-view').classList.contains('actual-pixels')")
        qa._poll_eval(ws, "document.querySelector('#candidate-view').classList.contains('actual-pixels')")
        qa._poll_eval(ws, "document.querySelector('#zoom-value').textContent === '1.00x'")

        source_probe = qa._evaluate(ws, _image_probe_expression("source-image"))
        candidate_probe = qa._evaluate(ws, _image_probe_expression("candidate-image"))
        for name, probe in (("source", source_probe), ("candidate", candidate_probe)):
            if not probe["grayscale"]:
                raise RuntimeError(f"{name} evidence browser decode is not grayscale")
            if probe["naturalWidth"] <= 0 or probe["naturalHeight"] <= 0 or probe["pixelCount"] <= 0:
                raise RuntimeError(f"{name} evidence has invalid decoded dimensions")
            if abs(float(probe["renderedWidth"]) - float(probe["naturalWidth"])) > 0.01:
                raise RuntimeError(f"{name} actual-pixels rendered width does not match decoded pixel width")
            if abs(float(probe["renderedHeight"]) - float(probe["naturalHeight"])) > 0.01:
                raise RuntimeError(f"{name} actual-pixels rendered height does not match decoded pixel height")
            if probe["transform"] not in {"matrix(1, 0, 0, 1, 0, 0)", "none"}:
                raise RuntimeError(f"{name} evidence 1x transform is not identity: {probe['transform']!r}")

        return {
            "schemaVersion": "1.0.0",
            "qa": "stage5_bounded_grayscale_display_integrity",
            "result": "PASS",
            "browser": browser_version,
            "viewport": {"width": 1280, "height": 900, "deviceScaleFactor": 1},
            "displayIntegrity": expected_integrity,
            "uiDisclosure": {
                "grayscaleDisclosed": True,
                "colorFidelityNotClaimed": True,
            },
            "sourceEvidence": source_probe,
            "candidateEvidence": candidate_probe,
            "actualPixelsAtOneX": True,
            "limitations": [
                "Input ICC/color profiles were not inspected.",
                "Color management was not validated and no color-fidelity certification is claimed.",
                "The browser QA uses the repository's synthetic Stage 5 fixture and no real score bytes.",
            ],
        }
    finally:
        if ws is not None:
            ws.close()
        browser_process.terminate()
        try:
            browser_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            browser_process.kill()
            browser_process.wait(timeout=5)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
        time.sleep(0.1)
        profile_dir.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_display_qa()
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
