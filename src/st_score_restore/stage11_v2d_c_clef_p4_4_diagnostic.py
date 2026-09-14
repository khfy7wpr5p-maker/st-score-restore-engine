"""P4.4 C-clef root-cause diagnostic for the frozen 3-page development slice.

Run only in the same Colab runtime where P4.3 hybrid canary/measurement completed.
This captures raw EOMER staff + clefs_keys masks and compares teacher boxes only
after inference. It is diagnostic-only and cannot qualify a detector.
"""
import cv2
import hashlib
import importlib.metadata as md
import json
import os
import shutil
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import onnxruntime as ort
from oemer import MODULE_PATH
from oemer.ete import generate_pred

PLAN_VERSION = "stage11.v2d.c-clef-p4_4-diagnostic-plan.v1"
SELECTED_PAGE_IDS = [
    "c1_c4_mixed-538f501cc852-p0001",
    "c3_alto-aa0ed21211f2-p0001",
    "c4_tenor-decfc1164a18-p0001",
]
EXPECTED_ORT = "1.20.2"
EXPECTED_OEMER = "0.1.8"
EXPECTED_MANIFEST_SHA256 = "365d45462b9d7b422a640e47bacdd5c8a5f16860198dec37121946411f6b3294"
EXPECTED_TEACHER_SHA256 = "1104d916faaf8d3c391cca9eda0354d21259f722cdcfe0f414c140796a5ffc5b"
EXPECTED_PROFILE = "HYBRID_UNET_CPU_SEGNET_CUDA_WHOLE_SESSION_FALLBACK_DISABLED"
ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/C_CLEF_SOURCE_PAGES")
MANIFEST_PATH = ROOT / "_PREPARED" / "c_clef_source_page_manifest.v1.json"
TEACHER_PATH = ROOT / "_ANNOTATIONS" / "c_clef_teacher_boxes.v1.json"
OUT_ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_DIAGNOSTIC_P4_4")
LOCAL_ROOT = Path("/content/st_score_restore_p4_4_diagnostic")


def fail(message):
    raise RuntimeError("P4.4 DIAGNOSTIC BLOCKED: " + message)


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def atomic_npz(path, **arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(str(tmp), **arrays)
    os.replace(tmp, path)


def write_png_atomic(path, image):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    local_tmp = LOCAL_ROOT / "_png_tmp" / (path.name + ".tmp.png")
    local_tmp.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(local_tmp), image):
        fail("PNG write failed: " + str(path))
    tmp_drive = path.with_name(path.name + ".tmp")
    shutil.copyfile(local_tmp, tmp_drive)
    os.replace(tmp_drive, path)
    local_tmp.unlink(missing_ok=True)


def box_iou(a, b):
    ax1, ay1, ax2, ay2 = map(float, a)
    bx1, by1, bx2, by2 = map(float, b)
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(0.0, (bx2 - bx1) * (by2 - by1))
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def runtime_gate():
    if ort.__version__ != EXPECTED_ORT:
        fail(f"ORT={ort.__version__}; expected {EXPECTED_ORT}")
    try:
        oemer_version = md.version("oemer")
    except Exception as exc:
        fail("Cannot read EOMER version: " + repr(exc))
    if oemer_version != EXPECTED_OEMER:
        fail(f"EOMER={oemer_version}; expected {EXPECTED_OEMER}")

    g = globals()
    if g.get("HYBRID_PROVIDER_PROFILE") != EXPECTED_PROFILE:
        fail("P4.3 hybrid provider profile is not active in this runtime")
    if not hasattr(ort, "_st_p43_original_inference_session"):
        fail("P4.3 provider router is not present")
    if "ST_P43_ROUTE_LOG" not in g:
        fail("P4.3 provider route log is not present")
    if "CHECKPOINTS" not in g:
        fail("P4.3 checkpoint contract is not present")
    if "CUDAExecutionProvider" not in ort.get_available_providers():
        fail("CUDAExecutionProvider is unavailable")

    return oemer_version


def exact_inputs():
    if not MANIFEST_PATH.is_file() or not TEACHER_PATH.is_file():
        fail("Manifest or teacher truth file is missing")
    manifest_sha = sha256_file(MANIFEST_PATH)
    teacher_sha = sha256_file(TEACHER_PATH)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        fail("Manifest SHA mismatch: " + manifest_sha)
    if teacher_sha != EXPECTED_TEACHER_SHA256:
        fail("Teacher truth SHA mismatch: " + teacher_sha)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    teacher = json.loads(TEACHER_PATH.read_text(encoding="utf-8"))
    if manifest.get("pageCount") != 29:
        fail("Manifest is not the frozen 29-page source")
    if teacher.get("pageCount") != 29 or teacher.get("boxCount") != 71:
        fail("Teacher truth is not the frozen 29-page / 71-box artifact")
    if teacher.get("sourceManifestSha256") != manifest_sha:
        fail("Teacher truth is not bound to this source manifest")

    manifest_by_id = {p["pageId"]: p for p in manifest["pages"]}
    for page_id in SELECTED_PAGE_IDS:
        if page_id not in manifest_by_id or page_id not in teacher["pages"]:
            fail("Frozen diagnostic page missing: " + page_id)
    return manifest, teacher, manifest_by_id, manifest_sha, teacher_sha


def checkpoint_gate():
    checkpoint_hashes = {}
    for rel, spec in globals()["CHECKPOINTS"].items():
        path = Path(MODULE_PATH) / "checkpoints" / rel
        if not path.is_file():
            fail("Checkpoint missing: " + rel)
        if path.stat().st_size != int(spec["size"]):
            fail("Checkpoint size mismatch: " + rel)
        actual = sha256_file(path)
        if actual != spec["sha256"]:
            fail("Checkpoint SHA mismatch: " + rel)
        checkpoint_hashes[rel] = actual
    return checkpoint_hashes


def run_page(page_id, page, teacher_page, teacher_sha, manifest_sha, oemer_version, checkpoint_hashes):
    source_path = (ROOT / page["imagePath"]).resolve()
    if source_path != ROOT and ROOT not in source_path.parents:
        fail("Unsafe imagePath: " + page_id)
    if not source_path.is_file():
        fail("Source PNG missing: " + page_id)

    source_sha = sha256_file(source_path)
    if source_sha != page["imageSha256"]:
        fail("Source PNG SHA mismatch: " + page_id)

    page_out = OUT_ROOT / page_id
    page_out.mkdir(parents=True, exist_ok=True)
    page_json = page_out / "diagnostic.v1.json"
    mask_npz = page_out / "raw_masks.v1.npz"

    fp_payload = {
        "planVersion": PLAN_VERSION,
        "pageId": page_id,
        "sourceImageSha256": source_sha,
        "teacherTruthSha256": teacher_sha,
        "manifestSha256": manifest_sha,
        "onnxruntimeVersion": ort.__version__,
        "oemerVersion": oemer_version,
        "executionProfile": EXPECTED_PROFILE,
        "checkpointSha256": checkpoint_hashes,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fp_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    if page_json.is_file() and mask_npz.is_file():
        try:
            cached = json.loads(page_json.read_text(encoding="utf-8"))
        except Exception:
            cached = None
        if isinstance(cached, dict) and cached.get("fingerprint") == fingerprint and cached.get("status") == "COMPLETE":
            return cached, True

    local_source = LOCAL_ROOT / "sources" / f"{page_id}.png"
    local_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, local_source)
    if sha256_file(local_source) != source_sha:
        fail("Local staging SHA mismatch: " + page_id)

    source_image = cv2.imread(str(local_source), cv2.IMREAD_COLOR)
    if source_image is None:
        fail("Source image unreadable: " + page_id)
    original_h, original_w = source_image.shape[:2]
    if int(page["width"]) != original_w or int(page["height"]) != original_h:
        fail("Source dimensions mismatch: " + page_id)

    globals()["ST_P43_ROUTE_LOG"].clear()
    started = time.time()
    outputs = generate_pred(str(local_source), use_tf=False)
    elapsed = time.time() - started

    if not isinstance(outputs, tuple) or len(outputs) != 5:
        fail("EOMER output contract failed: " + page_id)
    staff = (np.asarray(outputs[0]) > 0).astype(np.uint8)
    clefs_keys = (np.asarray(outputs[4]) > 0).astype(np.uint8)
    if staff.shape != clefs_keys.shape:
        fail("staff/clefs_keys shape mismatch: " + page_id)

    routes = {}
    for item in globals()["ST_P43_ROUTE_LOG"]:
        if isinstance(item, dict) and item.get("model"):
            routes[item["model"]] = dict(item)
    if set(routes) != {"unet_big", "seg_net"}:
        fail("Provider route evidence incomplete: " + page_id)
    if routes["unet_big"].get("route") != "CPUExecutionProvider":
        fail("unet_big route changed: " + page_id)
    if routes["seg_net"].get("route") != "CUDAExecutionProvider":
        fail("seg_net route changed: " + page_id)
    if not routes["seg_net"].get("wholeSessionFallbackDisabled"):
        fail("seg_net whole-session fallback is not disabled: " + page_id)

    mask_h, mask_w = clefs_keys.shape[:2]
    scale_x, scale_y = original_w / mask_w, original_h / mask_h

    component_count, _, stats, centroids = cv2.connectedComponentsWithStats(clefs_keys, connectivity=8)
    raw_components = []
    for component_id in range(1, component_count):
        x = int(stats[component_id, cv2.CC_STAT_LEFT])
        y = int(stats[component_id, cv2.CC_STAT_TOP])
        w = int(stats[component_id, cv2.CC_STAT_WIDTH])
        h = int(stats[component_id, cv2.CC_STAT_HEIGHT])
        area = int(stats[component_id, cv2.CC_STAT_AREA])
        raw_components.append({
            "componentId": component_id,
            "bboxInference": [x, y, x + w, y + h],
            "bboxSource": [x * scale_x, y * scale_y, (x + w) * scale_x, (y + h) * scale_y],
            "areaPixels": area,
            "centroidInference": [float(centroids[component_id, 0]), float(centroids[component_id, 1])],
            "leftPageRatio": (x * scale_x) / original_w if original_w else None,
        })

    teacher_diagnostics = []
    for teacher_index, box in enumerate(teacher_page["boxes"]):
        tx1, ty1 = float(box["x"]), float(box["y"])
        tx2 = float(box["x"] + box["width"])
        ty2 = float(box["y"] + box["height"])
        mx1 = max(0, min(mask_w, int(np.floor(tx1 / scale_x))))
        my1 = max(0, min(mask_h, int(np.floor(ty1 / scale_y))))
        mx2 = max(mx1, min(mask_w, int(np.ceil(tx2 / scale_x))))
        my2 = max(my1, min(mask_h, int(np.ceil(ty2 / scale_y))))
        region = clefs_keys[my1:my2, mx1:mx2]
        region_pixels = int(region.size)
        positive_pixels = int(np.count_nonzero(region))
        coverage = positive_pixels / region_pixels if region_pixels else 0.0

        teacher_box = [tx1, ty1, tx2, ty2]
        max_iou = 0.0
        max_component_id = None
        for component in raw_components:
            iou = box_iou(teacher_box, component["bboxSource"])
            if iou > max_iou:
                max_iou = iou
                max_component_id = component["componentId"]

        teacher_diagnostics.append({
            "teacherIndex": teacher_index,
            "teacherBoxId": box["id"],
            "label": box["label"],
            "bboxSource": teacher_box,
            "bboxInference": [mx1, my1, mx2, my2],
            "maskPositivePixels": positive_pixels,
            "maskRegionPixels": region_pixels,
            "maskCoverage": coverage,
            "hasAnyUpstreamMaskPixel": positive_pixels > 0,
            "maxRawComponentIoU": max_iou,
            "maxRawComponentId": max_component_id,
        })

    atomic_npz(mask_npz, staff=staff, clefs_keys=clefs_keys)
    write_png_atomic(page_out / "staff_mask.v1.png", staff * 255)
    write_png_atomic(page_out / "clefs_keys_mask.v1.png", clefs_keys * 255)

    mask_source = cv2.resize(clefs_keys * 255, (original_w, original_h), interpolation=cv2.INTER_NEAREST)
    overlay = source_image.copy()
    mask_idx = mask_source > 0
    overlay[:, :, 1][mask_idx] = 255
    for box in teacher_page["boxes"]:
        x1, y1 = int(box["x"]), int(box["y"])
        x2, y2 = int(box["x"] + box["width"]), int(box["y"] + box["height"])
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(overlay, box["label"], (x1, max(15, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 1, cv2.LINE_AA)
    write_png_atomic(page_out / "teacher_mask_overlay.v1.png", overlay)

    payload = {
        "schemaVersion": "stage11.v2d.c-clef-p4_4-diagnostic-page.v1",
        "status": "COMPLETE",
        "planVersion": PLAN_VERSION,
        "pageId": page_id,
        "sourceGroup": page["sourceGroup"],
        "sourceImage": {"path": page["imagePath"], "sha256": source_sha, "width": original_w, "height": original_h},
        "runtime": {
            "elapsedSeconds": elapsed,
            "onnxruntimeVersion": ort.__version__,
            "oemerVersion": oemer_version,
            "executionProfile": EXPECTED_PROFILE,
            "routes": routes,
            "checkpointSha256": checkpoint_hashes,
        },
        "inference": {
            "maskWidth": mask_w,
            "maskHeight": mask_h,
            "scaleXToSource": scale_x,
            "scaleYToSource": scale_y,
            "staffPositivePixels": int(np.count_nonzero(staff)),
            "clefsKeysPositivePixels": int(np.count_nonzero(clefs_keys)),
            "rawConnectedComponentCount": len(raw_components),
        },
        "rawComponents": raw_components,
        "teacherComparison": {
            "teacherTruthSha256": teacher_sha,
            "teacherTruthConsumedAtInference": False,
            "usedOnlyAfterInference": True,
            "teacherBoxCount": len(teacher_page["boxes"]),
            "boxes": teacher_diagnostics,
        },
        "artifacts": {
            "rawMasksNpz": str(mask_npz),
            "staffMaskPng": str(page_out / "staff_mask.v1.png"),
            "clefsKeysMaskPng": str(page_out / "clefs_keys_mask.v1.png"),
            "teacherMaskOverlayPng": str(page_out / "teacher_mask_overlay.v1.png"),
        },
        "fingerprint": fingerprint,
    }
    atomic_json(page_json, payload)
    return payload, False


def main():
    print("=" * 76)
    print("ST SCORE RESTORE — P4.4 C-CLEF ROOT-CAUSE DIAGNOSTIC")
    print("=" * 76)
    oemer_version = runtime_gate()
    manifest, teacher, manifest_by_id, manifest_sha, teacher_sha = exact_inputs()
    checkpoint_hashes = checkpoint_gate()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)

    print("PASS — runtime:", ort.__version__, oemer_version)
    print("PASS — exact manifest/teacher truth")
    print("PASS — frozen diagnostic pages:", len(SELECTED_PAGE_IDS))
    print("PASS — checkpoint identities")
    print("NOTE — only 3 development pages will run; no held-out access")

    diagnostic_pages = []
    for index, page_id in enumerate(SELECTED_PAGE_IDS, start=1):
        print(f"\nP4.4 START {index:02d}/{len(SELECTED_PAGE_IDS):02d} {page_id}")
        payload, cached = run_page(
            page_id, manifest_by_id[page_id], teacher["pages"][page_id],
            teacher_sha, manifest_sha, oemer_version, checkpoint_hashes
        )
        diagnostic_pages.append(payload)
        if cached:
            print(f"P4.4 CACHE {index:02d}/{len(SELECTED_PAGE_IDS):02d} {page_id}")
        else:
            print(
                f"P4.4 SAVED {index:02d}/{len(SELECTED_PAGE_IDS):02d} {page_id} "
                f"| components={payload['inference']['rawConnectedComponentCount']} "
                f"| time={payload['runtime']['elapsedSeconds']:.1f}s"
            )

    by_label = defaultdict(lambda: {
        "teacherBoxes": 0,
        "boxesWithAnyUpstreamMaskPixel": 0,
        "coverageValues": [],
        "maxRawComponentIoUValues": [],
    })
    for page_payload in diagnostic_pages:
        for item in page_payload["teacherComparison"]["boxes"]:
            agg = by_label[item["label"]]
            agg["teacherBoxes"] += 1
            if item["hasAnyUpstreamMaskPixel"]:
                agg["boxesWithAnyUpstreamMaskPixel"] += 1
            agg["coverageValues"].append(float(item["maskCoverage"]))
            agg["maxRawComponentIoUValues"].append(float(item["maxRawComponentIoU"]))

    summary_by_label = {}
    for label, agg in sorted(by_label.items()):
        cov = agg["coverageValues"]
        iou = agg["maxRawComponentIoUValues"]
        summary_by_label[label] = {
            "teacherBoxes": agg["teacherBoxes"],
            "boxesWithAnyUpstreamMaskPixel": agg["boxesWithAnyUpstreamMaskPixel"],
            "meanTeacherBoxMaskCoverage": float(np.mean(cov)) if cov else 0.0,
            "minimumTeacherBoxMaskCoverage": float(np.min(cov)) if cov else 0.0,
            "maximumTeacherBoxMaskCoverage": float(np.max(cov)) if cov else 0.0,
            "meanMaxRawComponentIoU": float(np.mean(iou)) if iou else 0.0,
            "maximumRawComponentIoU": float(np.max(iou)) if iou else 0.0,
        }

    summary = {
        "schemaVersion": "stage11.v2d.c-clef-p4_4-diagnostic-summary.v1",
        "status": "COMPLETE",
        "planVersion": PLAN_VERSION,
        "developmentDiagnosticOnly": True,
        "heldOutAccessed": False,
        "p4_3Retuned": False,
        "pageCount": len(diagnostic_pages),
        "selectedPageIds": SELECTED_PAGE_IDS,
        "manifestSha256": manifest_sha,
        "teacherTruthSha256": teacher_sha,
        "executionProfile": EXPECTED_PROFILE,
        "byClefSubtype": summary_by_label,
        "interpretationBoundary": {
            "qualificationDecisionAuthorized": False,
            "note": "This artifact localizes failure origin only. It does not qualify a new detector.",
        },
    }
    summary_path = OUT_ROOT / "p4_4_c_clef_root_cause_diagnostic.v1.json"
    atomic_json(summary_path, summary)

    print("\n" + "=" * 76)
    print("P4.4 C-CLEF ROOT-CAUSE DIAGNOSTIC COMPLETE")
    print("=" * 76)
    for label, item in summary_by_label.items():
        print(
            f"{label}: mask present "
            f"{item['boxesWithAnyUpstreamMaskPixel']}/{item['teacherBoxes']} "
            f"| mean coverage={item['meanTeacherBoxMaskCoverage']:.6f} "
            f"| max raw component IoU={item['maximumRawComponentIoU']:.6f}"
        )
    print("SAVED:", summary_path)
    print("NEXT: Send the final C1/C3/C4 summary lines to ChatGPT.")
    return summary_path


if __name__ == "__main__":
    main()
