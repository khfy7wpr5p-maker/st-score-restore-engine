"""Colab-only source-blinded teacher annotation UI for Stage 11 V2d staff-line truth.

The UI shows only source-render PNGs from the prepared Drive package. It never
shows restored output, detector output, or precomputed line geometry.

Human workflow:
- inspect a source page;
- for each standard 5-line staff, add one system;
- trace each of the five staff-line centrelines with >=2 clicks, top to bottom;
- choose a stroke width that matches visible staff-line thickness;
- finish the system and save the page;
- staff-absent pages are explicitly confirmed as empty.

The saved JSON and binary PNG masks are development-only teacher truth.
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/STAFF_LINE_TEACHER_MASK_TOPOLOGY")
SOURCE_DIR = ROOT / "source_pages"
MASK_DIR = ROOT / "masks"
ANNOTATION_DIR = ROOT / "annotations"
ARTIFACT_PATH = ANNOTATION_DIR / "staff_line_teacher_mask_topology.v1.json"
PROGRESS_PATH = ANNOTATION_DIR / "staff_line_teacher_progress.v1.json"

PAGE_IDS = [
    "beethoven-op48-no3-p1",
    "beethoven-op48-no3-p2",
    "beethoven-op48-no3-p3",
    "beethoven-op48-no3-p4",
    "wikimedia-guitar-technical-exercise-no1-p1",
    "barley-your-face-your-tongue-your-wit-p1",
    "barley-your-face-your-tongue-your-wit-p2",
    "carulli-morceaux-faciles-p2",
    "carulli-morceaux-faciles-p3",
    "carulli-morceaux-faciles-p4",
    "carulli-morceaux-faciles-p5",
    "carulli-morceaux-faciles-p6",
    "carulli-morceaux-faciles-p7",
    "carulli-morceaux-faciles-p8",
    "carulli-morceaux-faciles-p9",
    "carulli-morceaux-faciles-p10",
    "bach-anna-magdalena-p4",
    "bach-anna-magdalena-p10",
    "bach-anna-magdalena-p24",
    "bach-anna-magdalena-p40",
]

STAFF_ABSENT = {
    "beethoven-op48-no3-p1",
    "beethoven-op48-no3-p4",
}

SOURCE_SHA256 = {
    "bach-anna-magdalena-p10": "59a8b166e2a26359a82057e73d6546fb06d8a9e479af3d5949fc421b6ccd0819",
    "bach-anna-magdalena-p24": "f67f0f2f5e140bb83446d120ba0a2530405d54fcfe0e75bf68143c1bcdad22c2",
    "bach-anna-magdalena-p4": "f0f3392a7c54b88c148412b16fba54daeaa40041fd842dd401933ed24ec30129",
    "bach-anna-magdalena-p40": "d98d978dd6fa7d3f95b9b404bec4a479bc5512c1149942f81055dbd34caeb97a",
    "barley-your-face-your-tongue-your-wit-p1": "ded7dcd743788adea0d97f561680392ae04acf5e30541161a0d0c06cd15556c9",
    "barley-your-face-your-tongue-your-wit-p2": "de259e9eaa4ac47e21b1105d58c9ce2718ccad8d81c27632f942c98ae7af5f35",
    "beethoven-op48-no3-p1": "84f11e1cbd048cd0699383f59693b98ae7e7e9803907a7120a27328e7cd46b46",
    "beethoven-op48-no3-p2": "fb297382dc68361eae317a8e1734d47b95e3487d0252002a73361ff332bb939f",
    "beethoven-op48-no3-p3": "194a5adaa9f7ad1a9d1c426e1d85444dfb0eb0a55cf8f6ad54962f8fbe5134c8",
    "beethoven-op48-no3-p4": "e65b9da7533f7e1fa1e134f887a53fa3d9c726ac2afe319efdad96c10a82a211",
    "carulli-morceaux-faciles-p10": "b09a3b42c9d759de9af6f9e8d5f9781212a8256fc4640e2a7896e81600b1a1c1",
    "carulli-morceaux-faciles-p2": "b47e5d89c72b0703b9cd2dbf882839fd8e77922c47c5a9c5e39d5073c8c89d2b",
    "carulli-morceaux-faciles-p3": "b2147a6c11a9bff22ccde16ee66c6eff1b843d62f29cc6ff49561c8a66accee8",
    "carulli-morceaux-faciles-p4": "a90febd0b77d8d94e523d61b7ab7b217c17be508e531fb441bb2545231c734da",
    "carulli-morceaux-faciles-p5": "c8de51b93ae850adc834bcacd8a932c53343b9d7786d14df169882aeea1fb5be",
    "carulli-morceaux-faciles-p6": "3c190502ee5dc35d1186f7fa8c5da8b0c26ae8f9eebfa947de94d0a0b8292cce",
    "carulli-morceaux-faciles-p7": "4bb286fb2076b54ae19ae9170cee9e5d9e8a6e5e83cf15ac9b3f4dd58d76f11a",
    "carulli-morceaux-faciles-p8": "a53a8578b956e9d6f9a31df0938e124c24d7bffe239f124124bc36d0a8b2fa1a",
    "carulli-morceaux-faciles-p9": "1da7b81eb27c00221c215858ca521ef1fd5ec1026d6ce45ddaa469165639e3d1",
    "wikimedia-guitar-technical-exercise-no1-p1": "36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _source_path(page_id: str) -> Path:
    return SOURCE_DIR / f"{page_id}.png"


def _read_source_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None or image.ndim not in (2, 3):
        raise RuntimeError(f"Unable to decode source image: {path}")
    if image.ndim == 3 and image.shape[2] not in (1, 3, 4):
        raise RuntimeError(f"Unsupported source image channel count: {path}")
    return image


def validate_prepared_sources() -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    bad_sha: list[str] = []
    for page_id in PAGE_IDS:
        path = _source_path(page_id)
        if not path.is_file():
            missing.append(str(path))
            continue
        actual_sha = sha256_file(path)
        if actual_sha != SOURCE_SHA256[page_id]:
            bad_sha.append(f"{page_id}: {actual_sha}")
            continue
        image = _read_source_image(path)
        height, width = image.shape[:2]
        contracts[page_id] = {
            "pageId": page_id,
            "sourceRenderSha256": actual_sha,
            "width": int(width),
            "height": int(height),
            "expectedStaffPresent": page_id not in STAFF_ABSENT,
        }
    if missing:
        raise RuntimeError("Missing prepared source pages:\n" + "\n".join(missing))
    if bad_sha:
        raise RuntimeError("Source SHA mismatch; stop before annotation:\n" + "\n".join(bad_sha))
    if len(contracts) != 20:
        raise RuntimeError(f"Expected 20 verified source pages, found {len(contracts)}")
    return contracts


def _new_artifact(contracts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schemaVersion": "stage11.v2d.staff-line-teacher-mask-topology.v1",
        "status": "ANNOTATION_IN_PROGRESS",
        "developmentOnly": True,
        "qualificationEvidence": False,
        "teacherAnnotationIndependent": True,
        "detectorOutputsShownToTeacher": False,
        "restoredOutputsShownToTeacher": False,
        "lineDetectorGeometryShownToTeacher": False,
        "pageCount": 20,
        "completedPageCount": 0,
        "pages": {
            page_id: {
                **contracts[page_id],
                "completed": False,
                "staffLineMaskPath": None,
                "staffLineMaskSha256": None,
                "systems": [],
                "notes": "",
            }
            for page_id in PAGE_IDS
        },
    }


def load_or_create_artifact() -> dict[str, Any]:
    contracts = validate_prepared_sources()
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    if ARTIFACT_PATH.is_file():
        artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
        if set(artifact.get("pages", {})) != set(PAGE_IDS):
            raise RuntimeError("Existing annotation artifact page set does not match frozen 20-page set.")
        for page_id, contract in contracts.items():
            page = artifact["pages"][page_id]
            for key in ("sourceRenderSha256", "width", "height", "expectedStaffPresent"):
                if page.get(key) != contract[key]:
                    raise RuntimeError(f"{page_id}: existing artifact {key} differs from prepared source.")
        return artifact
    artifact = _new_artifact(contracts)
    _atomic_json(ARTIFACT_PATH, artifact)
    return artifact


def _make_preview_data_uri(image: np.ndarray, max_width: int = 1800) -> tuple[str, int, int]:
    if image.ndim == 3 and image.shape[2] == 4:
        preview = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    elif image.ndim == 3 and image.shape[2] == 1:
        preview = image[:, :, 0]
    else:
        preview = image.copy()
    height, width = preview.shape[:2]
    if width > max_width:
        ratio = max_width / width
        preview = cv2.resize(
            preview,
            (max_width, max(1, round(height * ratio))),
            interpolation=cv2.INTER_AREA,
        )
    ok, encoded = cv2.imencode(
        ".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    )
    if not ok:
        raise RuntimeError("Unable to encode source preview JPEG")
    preview_height, preview_width = preview.shape[:2]
    uri = "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")
    return uri, int(preview_width), int(preview_height)


def _sanitize_systems(raw_systems: Any, width: int, height: int) -> list[dict[str, Any]]:
    if not isinstance(raw_systems, list):
        raise ValueError("systems must be a list")
    cleaned: list[dict[str, Any]] = []
    for system_index, raw in enumerate(raw_systems, start=1):
        if not isinstance(raw, dict):
            raise ValueError("invalid system record")
        status = str(raw.get("status", "CONFIRMED")).upper()
        if status not in {"CONFIRMED", "AMBIGUOUS"}:
            raise ValueError("status must be CONFIRMED or AMBIGUOUS")
        stroke_width = int(raw.get("strokeWidth", 1))
        if not 1 <= stroke_width <= 8:
            raise ValueError("strokeWidth must be 1..8")
        raw_lines = raw.get("lines")
        if not isinstance(raw_lines, list) or len(raw_lines) != 5:
            raise ValueError("each staff system must contain exactly five lines")
        lines: list[dict[str, Any]] = []
        all_points: list[tuple[int, int]] = []
        for line_index, raw_line in enumerate(raw_lines, start=1):
            points = raw_line.get("centerlinePoints") if isinstance(raw_line, dict) else None
            if not isinstance(points, list) or len(points) < 2:
                raise ValueError(f"system {system_index} line {line_index} requires >=2 points")
            cleaned_points: list[list[int]] = []
            for point in points:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    raise ValueError("invalid point")
                x = int(round(float(point[0])))
                y = int(round(float(point[1])))
                if not (0 <= x < width and 0 <= y < height):
                    raise ValueError("point outside source image")
                cleaned_points.append([x, y])
                all_points.append((x, y))
            lines.append({"lineIndex": line_index, "centerlinePoints": cleaned_points})
        line_medians = []
        for line in lines:
            ys = sorted(point[1] for point in line["centerlinePoints"])
            line_medians.append(ys[len(ys) // 2])
        if line_medians != sorted(line_medians):
            raise ValueError(f"system {system_index}: lines are not top-to-bottom")
        xs = [point[0] for point in all_points]
        ys = [point[1] for point in all_points]
        pad = max(2, stroke_width + 1)
        bbox = [
            max(0, min(xs) - pad),
            max(0, min(ys) - pad),
            min(width, max(xs) + pad + 1),
            min(height, max(ys) + pad + 1),
        ]
        cleaned.append(
            {
                "systemId": f"system-{system_index}",
                "bbox": bbox,
                "lineCount": 5,
                "lines": lines,
                "status": status,
                "strokeWidth": stroke_width,
            }
        )
    return cleaned


def _render_mask(page_id: str, width: int, height: int, systems: list[dict[str, Any]]) -> tuple[str, str]:
    mask = np.zeros((height, width), dtype=np.uint8)
    for system in systems:
        if system["status"] != "CONFIRMED":
            continue
        stroke_width = int(system.get("strokeWidth", 1))
        for line in system["lines"]:
            points = np.asarray(line["centerlinePoints"], dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(
                mask,
                [points],
                isClosed=False,
                color=255,
                thickness=stroke_width,
                lineType=cv2.LINE_8,
            )
    mask_path = MASK_DIR / f"{page_id}.png"
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(mask_path), mask):
        raise RuntimeError(f"Unable to write mask PNG: {mask_path}")
    return f"masks/{page_id}.png", sha256_file(mask_path)


def _progress(artifact: dict[str, Any]) -> None:
    completed = [page_id for page_id in PAGE_IDS if artifact["pages"][page_id].get("completed") is True]
    artifact["completedPageCount"] = len(completed)
    artifact["status"] = "ANNOTATION_COMPLETE" if len(completed) == 20 else "ANNOTATION_IN_PROGRESS"
    _atomic_json(ARTIFACT_PATH, artifact)
    _atomic_json(
        PROGRESS_PATH,
        {
            "schemaVersion": "stage11.v2d.staff-line-teacher-progress.v1",
            "completedPageCount": len(completed),
            "remainingPageCount": 20 - len(completed),
            "completedPages": completed,
            "nextIncompletePage": next((p for p in PAGE_IDS if p not in completed), None),
            "artifactPath": str(ARTIFACT_PATH),
        },
    )


def _annotation_js(config_json: str) -> str:
    return r"""
new Promise((resolve) => {
  const cfg = __CFG__;
  document.body.style.margin = "0";
  document.body.style.background = "#202124";
  document.body.style.color = "white";
  document.body.style.fontFamily = "Arial, sans-serif";
  const old = document.getElementById("st-staff-root");
  if (old) old.remove();
  const root = document.createElement("div");
  root.id = "st-staff-root";
  root.style.cssText = "padding:12px;min-height:1000px;";
  root.innerHTML = `
    <div style="max-width:1500px;margin:0 auto;">
      <h2 style="margin:0 0 6px;">Stage 11 — Staff-line Teacher Truth</h2>
      <div style="margin-bottom:10px;"><b>${cfg.pageNo}/${cfg.pageCount}</b> — ${cfg.pageId}<br>
        <span style="font-size:13px;">Yalnız kaynak nota gösteriliyor. Restore/detector çıktısı yok.</span></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px;">
        <button id="newSystem">Yeni porte sistemi</button><button id="undoPoint">Son noktayı sil</button>
        <button id="nextLine">Sonraki çizgi</button><button id="finishSystem">Porteyi tamamla</button>
        <button id="undoSystem">Son porteyi sil</button>
        <label>Kalınlık: <input id="strokeWidth" type="number" min="1" max="8" value="2" style="width:55px;"></label>
        <label>Durum: <select id="status"><option>CONFIRMED</option><option>AMBIGUOUS</option></select></label>
        <label>Zoom: <select id="zoom"><option value="0.5">50%</option><option value="0.75">75%</option><option value="1" selected>100%</option><option value="1.25">125%</option><option value="1.5">150%</option></select></label>
      </div>
      <div id="msg" style="padding:6px 0;font-weight:bold;">Yeni porte sistemi ile başlayın.</div>
      <div style="width:100%;height:760px;overflow:auto;background:white;border:2px solid #777;">
        <canvas id="canvas" style="display:block;max-width:none;cursor:crosshair;"></canvas></div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;padding-bottom:30px;">
        <button id="save" style="font-size:18px;font-weight:bold;padding:10px 16px;">Sayfayı kaydet</button>
        <button id="empty" style="font-size:17px;padding:10px 16px;">Bu sayfada standart porte yok</button>
        <button id="cancel" style="font-size:16px;padding:10px 16px;">Burada dur</button>
      </div>
    </div>`;
  document.body.appendChild(root);
  const canvas = document.getElementById("canvas");
  const ctx = canvas.getContext("2d");
  const msg = document.getElementById("msg");
  const zoom = document.getElementById("zoom");
  const image = new Image();
  canvas.width = cfg.previewWidth;
  canvas.height = cfg.previewHeight;
  let systems = JSON.parse(JSON.stringify(cfg.existingSystems || []));
  let current = null;
  let currentLine = 0;
  const colors = ["#ff0000", "#00aa00", "#0066ff", "#cc00cc", "#ff8800"];
  function srcToPreview(p) { return [p[0] * cfg.previewWidth / cfg.sourceWidth, p[1] * cfg.previewHeight / cfg.sourceHeight]; }
  function previewToSrc(x, y) { return [x * cfg.sourceWidth / cfg.previewWidth, y * cfg.sourceHeight / cfg.previewHeight]; }
  function setMessage(text) { msg.textContent = text; }
  function applyZoom() { const z = Number(zoom.value); canvas.style.width = `${Math.round(cfg.previewWidth * z)}px`; canvas.style.height = `${Math.round(cfg.previewHeight * z)}px`; }
  function drawPolyline(points, color, width) {
    if (!points || points.length === 0) return;
    const pts = points.map(srcToPreview);
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = Math.max(1, width * cfg.previewWidth / cfg.sourceWidth);
    ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.stroke();
    for (const p of pts) { ctx.beginPath(); ctx.arc(p[0], p[1], 3, 0, Math.PI * 2); ctx.fill(); }
  }
  function redraw() {
    ctx.clearRect(0,0,canvas.width,canvas.height); ctx.drawImage(image,0,0,canvas.width,canvas.height);
    for (const s of systems) for (let i=0;i<5;i++) drawPolyline(s.lines[i].centerlinePoints, colors[i], s.strokeWidth || 2);
    if (current) for (let i=0;i<5;i++) drawPolyline(current.lines[i].centerlinePoints, colors[i], current.strokeWidth || 2);
  }
  function startSystem() {
    if (current) { setMessage("Önce mevcut porteyi tamamlayın veya son noktaları geri alın."); return; }
    const sw = Math.max(1, Math.min(8, Number(document.getElementById("strokeWidth").value || 2)));
    current = {status: document.getElementById("status").value, strokeWidth: sw, lines: [1,2,3,4,5].map(i => ({lineIndex:i, centerlinePoints:[]}))};
    currentLine = 0; setMessage("Porte çizgisi 1/5: soldan sağa en az iki nokta tıklayın."); redraw();
  }
  function canvasPoint(e) {
    const rect = canvas.getBoundingClientRect();
    const px = (e.clientX - rect.left) * canvas.width / rect.width;
    const py = (e.clientY - rect.top) * canvas.height / rect.height;
    return previewToSrc(px, py);
  }
  canvas.addEventListener("click", (e) => { if (!current) return; current.lines[currentLine].centerlinePoints.push(canvasPoint(e)); redraw(); });
  document.getElementById("newSystem").onclick = startSystem;
  document.getElementById("undoPoint").onclick = () => { if (!current) return; const pts = current.lines[currentLine].centerlinePoints; if (pts.length) pts.pop(); redraw(); };
  document.getElementById("nextLine").onclick = () => {
    if (!current) { setMessage("Önce yeni porte sistemi açın."); return; }
    if (current.lines[currentLine].centerlinePoints.length < 2) { setMessage(`Çizgi ${currentLine+1} için en az iki nokta gerekli.`); return; }
    if (currentLine >= 4) { setMessage("5. çizgidesiniz. Porteyi tamamlayın."); return; }
    currentLine += 1; setMessage(`Porte çizgisi ${currentLine+1}/5: soldan sağa en az iki nokta tıklayın.`); redraw();
  };
  document.getElementById("finishSystem").onclick = () => {
    if (!current) { setMessage("Açık porte yok."); return; }
    if (current.lines.some(line => line.centerlinePoints.length < 2)) { setMessage("Beş çizginin her birinde en az iki nokta olmalı."); return; }
    current.strokeWidth = Math.max(1, Math.min(8, Number(document.getElementById("strokeWidth").value || 2)));
    current.status = document.getElementById("status").value; systems.push(current); current = null; currentLine = 0;
    setMessage(`Porte kaydedildi. Toplam ${systems.length}. Başka porte varsa yeni porte sistemi açın.`); redraw();
  };
  document.getElementById("undoSystem").onclick = () => {
    if (current) { current = null; currentLine = 0; redraw(); setMessage("Açık porte silindi."); return; }
    if (systems.length) systems.pop(); redraw(); setMessage(`Son porte silindi. Kalan: ${systems.length}.`);
  };
  zoom.onchange = applyZoom;
  document.getElementById("save").onclick = () => {
    if (current) { setMessage("Açık porteyi önce tamamlayın."); return; }
    if (cfg.expectedStaffPresent && systems.length === 0) { setMessage("Bu sayfa staff-present olarak kayıtlı; en az bir porte girin veya yanlışsa 'porte yok' ile insan kararını açıkça verin."); return; }
    resolve({action:"save", systems}); root.remove();
  };
  document.getElementById("empty").onclick = () => {
    if (!confirm("Bu kaynak sayfada standart 5 çizgili porte bulunmadığını onaylıyor musunuz?")) return;
    resolve({action:"empty", systems:[]}); root.remove();
  };
  document.getElementById("cancel").onclick = () => { resolve({action:"cancel"}); root.remove(); };
  image.onload = () => { applyZoom(); redraw(); };
  image.src = cfg.image;
})
""".replace("__CFG__", config_json)


def annotate_page(page_id: str, artifact: dict[str, Any]) -> str:
    from google.colab import output

    page = artifact["pages"][page_id]
    image_path = _source_path(page_id)
    if sha256_file(image_path) != page["sourceRenderSha256"]:
        raise RuntimeError(f"{page_id}: source changed after preparation")
    source = _read_source_image(image_path)
    source_height, source_width = source.shape[:2]
    image_uri, preview_width, preview_height = _make_preview_data_uri(source)

    config = {
        "image": image_uri,
        "pageId": page_id,
        "pageNo": PAGE_IDS.index(page_id) + 1,
        "pageCount": len(PAGE_IDS),
        "sourceWidth": int(source_width),
        "sourceHeight": int(source_height),
        "previewWidth": preview_width,
        "previewHeight": preview_height,
        "expectedStaffPresent": bool(page["expectedStaffPresent"]),
        "existingSystems": page.get("systems", []) if page.get("completed") else [],
    }
    result = output.eval_js(_annotation_js(json.dumps(config, ensure_ascii=False)))
    if not isinstance(result, dict):
        return "cancel"
    action = str(result.get("action", "cancel"))
    if action == "cancel":
        return "cancel"

    systems = [] if action == "empty" else _sanitize_systems(result.get("systems"), source_width, source_height)
    mask_rel, mask_sha = _render_mask(page_id, source_width, source_height, systems)

    page["systems"] = systems
    page["staffLineMaskPath"] = mask_rel
    page["staffLineMaskSha256"] = mask_sha
    page["completed"] = True
    page["notes"] = "Teacher-confirmed source-only annotation. No restored/detector geometry shown."
    _progress(artifact)
    return "saved"


def run_annotation() -> dict[str, Any]:
    """Mount Drive if needed, verify all 20 source renders, and resume annotation."""
    try:
        from google.colab import drive
    except ImportError as exc:
        raise RuntimeError("This runner is intended for Google Colab.") from exc

    if not Path("/content/drive/MyDrive").exists():
        drive.mount("/content/drive")

    artifact = load_or_create_artifact()
    _progress(artifact)
    print("Verified source pages: 20/20")
    print(f"Completed: {artifact['completedPageCount']}/20")
    print(f"Artifact: {ARTIFACT_PATH}")

    for page_id in PAGE_IDS:
        if artifact["pages"][page_id].get("completed") is True:
            continue
        result = annotate_page(page_id, artifact)
        if result == "cancel":
            print("Stopped safely. Progress saved.")
            break
        print(f"Saved {page_id} — progress {artifact['completedPageCount']}/20")

    if artifact["completedPageCount"] == 20:
        print("ANNOTATION COMPLETE — 20/20 pages")
        print(f"Teacher artifact: {ARTIFACT_PATH}")
        print(f"Masks: {MASK_DIR}")
    else:
        next_page = next((p for p in PAGE_IDS if not artifact["pages"][p].get("completed")), None)
        print(f"Next incomplete page: {next_page}")
    return artifact


if __name__ == "__main__":
    run_annotation()
