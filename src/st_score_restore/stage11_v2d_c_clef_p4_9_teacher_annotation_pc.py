from __future__ import annotations

import base64
import hashlib
import json
from io import BytesIO
from pathlib import Path

from PIL import Image


ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
PREPARED = ROOT / "_PREPARED"
ANNOTATIONS = ROOT / "_ANNOTATIONS"
MANIFEST_PATH = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
TEMPLATE_PATH = ANNOTATIONS / "c_clef_p4_9_holdout_teacher_boxes.template.v1.json"
OUTPUT_PATH = ANNOTATIONS / "c_clef_p4_9_holdout_teacher_boxes.v1.json"
PROGRESS_PATH = ANNOTATIONS / "c_clef_p4_9_holdout_teacher_progress.v1.json"

ACCEPTED_LABELS = {"C1", "C3", "C4", "AMBIGUOUS"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, obj: dict) -> None:
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def recalc(teacher: dict) -> None:
    completed = 0
    total_boxes = 0
    counts = {"C1": 0, "C3": 0, "C4": 0, "AMBIGUOUS": 0}

    for state in teacher["pages"].values():
        if state.get("completed", False):
            completed += 1
        for box in state.get("boxes", []):
            label = str(box.get("label", "AMBIGUOUS")).upper()
            counts[label] = counts.get(label, 0) + 1
            total_boxes += 1

    teacher["completedPageCount"] = completed
    teacher["boxCount"] = total_boxes
    teacher["labelCounts"] = counts


def load_state() -> tuple[dict, dict, str]:
    if not MANIFEST_PATH.is_file():
        raise RuntimeError(f"Manifest missing. Run P4.9 preparation first: {MANIFEST_PATH}")
    if not TEMPLATE_PATH.is_file():
        raise RuntimeError(f"Teacher template missing. Run P4.9 preparation first: {TEMPLATE_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    manifest_sha = sha256_file(MANIFEST_PATH)

    if manifest.get("pageCount") != 11:
        raise RuntimeError(f"Expected 11 P4.9 pages, got {manifest.get('pageCount')}")
    if template.get("sourceManifestSha256") != manifest_sha:
        raise RuntimeError("Teacher template does not bind the current P4.9 manifest SHA")
    if manifest.get("detectorOutputsAccessed") is not False:
        raise RuntimeError("Manifest provenance violation: detectorOutputsAccessed must be false")

    if OUTPUT_PATH.exists():
        teacher = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        if teacher.get("sourceManifestSha256") != manifest_sha:
            raise RuntimeError("Existing teacher file belongs to a different manifest")
    else:
        teacher = {
            "artifactType": "C_CLEF_P4_9_HOLDOUT_TEACHER_BOXES",
            "schemaVersion": "1.0.0",
            "phase": "Stage 11 v2d / P4.9 independent C-clef holdout",
            "status": "ANNOTATION_IN_PROGRESS",
            "sourceManifestSha256": manifest_sha,
            "pageCount": 11,
            "completedPageCount": 0,
            "boxCount": 0,
            "labelCounts": {"C1": 0, "C3": 0, "C4": 0, "AMBIGUOUS": 0},
            "detectorOutputsAccessed": False,
            "pages": {},
        }
        for page in manifest["pages"]:
            teacher["pages"][page["pageId"]] = {
                "sourcePdfName": page["sourcePdfName"],
                "sourcePageNumber": page["sourcePageNumber"],
                "completed": False,
                "boxes": [],
            }
        save_json(OUTPUT_PATH, teacher)

    recalc(teacher)
    return manifest, teacher, manifest_sha


def annotate_one_page(manifest: dict, teacher: dict, manifest_sha: str, page_index: int) -> None:
    from google.colab import output

    page = manifest["pages"][page_index]
    page_id = page["pageId"]
    state = teacher["pages"][page_id]
    image_path = PREPARED / page["imagePath"]

    if not image_path.is_file():
        raise RuntimeError(f"Prepared image missing: {image_path}")
    if sha256_file(image_path) != page["imageSha256"]:
        raise RuntimeError(f"Prepared image SHA mismatch: {page_id}")

    with Image.open(image_path) as src:
        original = src.convert("RGB")

    ow, oh = original.size
    preview = original.copy()
    preview.thumbnail((2200, 3000))
    pw, ph = preview.size
    sx = pw / ow
    sy = ph / oh

    existing = []
    for box in state.get("boxes", []):
        existing.append(
            {
                "x": box["x"] * sx,
                "y": box["y"] * sy,
                "w": box["w"] * sx,
                "h": box["h"] * sy,
                "label": box["label"],
            }
        )

    buf = BytesIO()
    preview.save(buf, format="JPEG", quality=88, optimize=True)
    image_data = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    cfg = {
        "image": image_data,
        "width": pw,
        "height": ph,
        "pageNo": page_index + 1,
        "pageCount": len(manifest["pages"]),
        "pageId": page_id,
        "source": page["sourcePdfName"],
        "sourcePage": page["sourcePageNumber"],
        "boxes": existing,
    }

    js = r'''
new Promise((resolve) => {
  const cfg = __CONFIG__;
  document.body.style.margin = "0";
  document.body.style.padding = "0";
  document.body.style.minHeight = "1000px";
  document.body.style.overflow = "auto";

  const old = document.getElementById("st-p49-root");
  if (old) old.remove();

  const root = document.createElement("div");
  root.id = "st-p49-root";
  root.style.cssText = `box-sizing:border-box;width:100%;min-height:1000px;padding:14px;background:#202124;color:white;font-family:Arial,sans-serif;`;
  root.innerHTML = `
    <div style="max-width:1240px;margin:0 auto;">
      <h2 style="margin:0 0 6px 0;">P4.9 Blinded C-Clef Teacher Annotation</h2>
      <div style="font-size:16px;margin-bottom:8px;">
        <b>Sayfa ${cfg.pageNo} / ${cfg.pageCount}</b><br>
        ${cfg.source} — PDF sayfa ${cfg.sourcePage}<br>
        <span style="font-size:14px;">Bu sayfadaki bütün C1 / C3 / C4 anahtarlarını kutula. Detector çıktısı gösterilmez.</span>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px;">
        <label>Label:</label>
        <select id="stLabel" style="font-size:18px;padding:7px;">
          <option value="C1">C1 soprano</option>
          <option value="C3">C3 alto</option>
          <option value="C4">C4 tenor</option>
          <option value="AMBIGUOUS">AMBIGUOUS</option>
        </select>
        <label>Zoom:</label>
        <select id="stZoom" style="font-size:17px;padding:7px;">
          <option value="0.5">50%</option>
          <option value="0.75">75%</option>
          <option value="1" selected>100%</option>
          <option value="1.25">125%</option>
          <option value="1.5">150%</option>
        </select>
        <button id="stUndo" style="font-size:16px;padding:8px 12px;">Son Kutuyu Sil</button>
        <button id="stClear" style="font-size:16px;padding:8px 12px;">Tüm Kutuları Sil</button>
      </div>
      <div id="stViewport" style="width:100%;height:760px;overflow:auto;background:white;border:2px solid #888;box-sizing:border-box;">
        <canvas id="stCanvas" style="display:block;max-width:none;cursor:crosshair;"></canvas>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px;padding-bottom:30px;">
        <button id="stSave" style="font-size:19px;font-weight:bold;padding:12px 18px;">Bu Sayfayı Kaydet</button>
        <button id="stEmpty" style="font-size:17px;padding:12px 18px;">Bu Sayfada C-Clef Yok</button>
      </div>
    </div>`;
  document.body.appendChild(root);

  const canvas = document.getElementById("stCanvas");
  const ctx = canvas.getContext("2d");
  const labelSelect = document.getElementById("stLabel");
  const zoomSelect = document.getElementById("stZoom");
  canvas.width = cfg.width;
  canvas.height = cfg.height;

  let boxes = JSON.parse(JSON.stringify(cfg.boxes || []));
  const image = new Image();
  let drawing = false;
  let x0 = 0, y0 = 0, x1 = 0, y1 = 0;

  function applyZoom() {
    const z = Number(zoomSelect.value);
    canvas.style.width = `${Math.round(cfg.width * z)}px`;
    canvas.style.height = `${Math.round(cfg.height * z)}px`;
  }

  function redraw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 3;
    ctx.font = "20px Arial";
    for (const b of boxes) {
      ctx.strokeStyle = "red";
      ctx.fillStyle = "red";
      ctx.strokeRect(b.x, b.y, b.w, b.h);
      ctx.fillText(b.label, b.x, Math.max(20, b.y - 3));
    }
    if (drawing) {
      ctx.strokeStyle = "blue";
      ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
    }
  }

  function point(e) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * canvas.width / rect.width,
      y: (e.clientY - rect.top) * canvas.height / rect.height,
    };
  }

  canvas.onmousedown = (e) => {
    const p = point(e);
    x0 = x1 = p.x; y0 = y1 = p.y; drawing = true; redraw();
  };
  canvas.onmousemove = (e) => {
    if (!drawing) return;
    const p = point(e); x1 = p.x; y1 = p.y; redraw();
  };
  canvas.onmouseup = (e) => {
    if (!drawing) return;
    const p = point(e); x1 = p.x; y1 = p.y; drawing = false;
    const xa = Math.min(x0, x1), ya = Math.min(y0, y1);
    const xb = Math.max(x0, x1), yb = Math.max(y0, y1);
    const w = xb - xa, h = yb - ya;
    if (w >= 8 && h >= 8) boxes.push({x:xa, y:ya, w:w, h:h, label:labelSelect.value});
    redraw();
  };

  zoomSelect.onchange = applyZoom;
  document.getElementById("stUndo").onclick = () => { if (boxes.length) { boxes.pop(); redraw(); } };
  document.getElementById("stClear").onclick = () => { if (confirm("Tüm kutular silinsin mi?")) { boxes = []; redraw(); } };
  document.getElementById("stSave").onclick = () => resolve({action:"save", boxes:boxes});
  document.getElementById("stEmpty").onclick = () => {
    if (confirm("Bu sayfada gerçekten hiç C-clef yok mu?")) resolve({action:"empty", boxes:[]});
  };

  image.onload = () => { applyZoom(); redraw(); };
  image.onerror = () => alert("Nota görüntüsü yüklenemedi.");
  image.src = cfg.image;
});
'''.replace("__CONFIG__", json.dumps(cfg))

    result = output.eval_js(js, timeout_sec=1800)
    if result is None:
        raise RuntimeError("Annotation UI returned no result")

    original_boxes = []
    for box in result.get("boxes", []):
        label = str(box["label"]).upper()
        if label not in ACCEPTED_LABELS:
            raise RuntimeError(f"Invalid teacher label: {label}")
        x = int(round(float(box["x"]) / sx))
        y = int(round(float(box["y"]) / sy))
        w = int(round(float(box["w"]) / sx))
        h = int(round(float(box["h"]) / sy))
        if w <= 0 or h <= 0:
            continue
        original_boxes.append({"x": x, "y": y, "w": w, "h": h, "label": label})

    state["boxes"] = original_boxes
    state["completed"] = True
    recalc(teacher)

    if teacher["completedPageCount"] == teacher["pageCount"]:
        teacher["status"] = "ANNOTATION_COMPLETE_PENDING_FREEZE"
    else:
        teacher["status"] = "ANNOTATION_IN_PROGRESS"

    save_json(OUTPUT_PATH, teacher)
    save_json(
        PROGRESS_PATH,
        {
            "artifactType": "C_CLEF_P4_9_HOLDOUT_TEACHER_PROGRESS",
            "schemaVersion": "1.0.0",
            "pageCount": teacher["pageCount"],
            "completedPageCount": teacher["completedPageCount"],
            "boxCount": teacher["boxCount"],
            "labelCounts": teacher["labelCounts"],
            "sourceManifestSha256": manifest_sha,
            "detectorOutputsAccessed": False,
        },
    )

    print(f"SAVED {page_index + 1}/{teacher['pageCount']} | boxes on page: {len(original_boxes)}")
    print(f"Progress: {teacher['completedPageCount']}/{teacher['pageCount']} | total boxes: {teacher['boxCount']}")


def main() -> None:
    manifest, teacher, manifest_sha = load_state()
    recalc(teacher)

    next_index = None
    for i, page in enumerate(manifest["pages"]):
        if not teacher["pages"][page["pageId"]].get("completed", False):
            next_index = i
            break

    print("=" * 72)
    print("P4.9 BLINDED TEACHER ANNOTATION — ONE PAGE MODE")
    print("=" * 72)
    print(f"Progress       : {teacher['completedPageCount']}/11")
    print(f"Existing boxes : {teacher['boxCount']}")
    print("Detector output : NOT LOADED")

    if next_index is None:
        teacher["status"] = "ANNOTATION_COMPLETE_PENDING_FREEZE"
        save_json(OUTPUT_PATH, teacher)
        print("TEACHER ANNOTATION COMPLETE: 11/11")
        print("Label counts:", teacher["labelCounts"])
        print("Teacher SHA-256:", sha256_file(OUTPUT_PATH))
        print("NEXT: freeze teacher truth before any P4.8 holdout evaluation")
        return

    page = manifest["pages"][next_index]
    print(f"Opening page   : {next_index + 1}/11 — {page['sourcePdfName']} / PDF page {page['sourcePageNumber']}")
    annotate_one_page(manifest, teacher, manifest_sha, next_index)

    recalc(teacher)
    if teacher["completedPageCount"] == 11:
        teacher["status"] = "ANNOTATION_COMPLETE_PENDING_FREEZE"
        save_json(OUTPUT_PATH, teacher)
        print("TEACHER ANNOTATION COMPLETE: 11/11")
        print("Label counts:", teacher["labelCounts"])
        print("Teacher SHA-256:", sha256_file(OUTPUT_PATH))
    else:
        print("Run this same cell again for the next page.")


if __name__ == "__main__":
    main()
