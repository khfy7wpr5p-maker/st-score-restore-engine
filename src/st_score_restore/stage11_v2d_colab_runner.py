"""Crash-safe Colab runner for Stage 11 V2d detector benchmarking.

Development-only, inference-only. Restore is frozen; Oemer runs on pinned ORT CPU.
All reusable work is persisted to Google Drive and verified before reuse.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np

from .stage11_v2c_teacher_review import materialize_teacher_review_manifest
from .stage11_v2d_detector_benchmark import (
    benchmark_coverage_from_present_pairs,
    teacher_present_class_pairs,
    validate_detector_benchmark_result,
)
from .stage11_v2c_semantic_preservation import conservative_line_system_detector

PINNED_ORT_VERSION = "1.20.1"
OEMER_UPSTREAM_COMMIT = "dbe2a933d630d0f74805d717960eb259473f5978"
CACHE_SCHEMA_VERSION = "stage11.v2d.colab-cache.v1"
DETECTOR_PROGRESS_SCHEMA_VERSION = "stage11.v2d.detector-page-progress.v1"
CACHE_ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/V2D_CACHE_V1")
RESULT_ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/V2D_RESULTS")
RESULT_FILENAME = "v2d_colab_gpu_detector_benchmark_result.json"
SOURCE_RENDER_VERSION = "pdftoppm-72dpi-singlepage.v1"
RESTORE_ALGORITHM_VERSION = "v2d-frozen-restore-512-overlap64-png3.v1"
DETECTOR_LOGIC_VERSION = "oemer-dbe2a933-semantic-boxes.v1"

TARGETS: dict[str, dict[str, Any]] = {
    "restore_model": {"drive_id":"1oJ9lOEpq7trDD8XZpVwCzQzMQ2mk-wWD","sha256":"7ff4023466f6b18eda41d9e8af7a9f6858429354621781dd9bd93b26210ba234","size":7817857,"kind":"torchscript","filename":"v2a_candidate_512.torchscript.pt"},
    "beethoven": {"drive_id":"1F6Xp6mmwsjmpk64GkcDqw6t0XpH_1IGk","sha256":"c25a5c5979ae076f8fc3607926ddb1d6aeb96a394498c2c1ebc54c27d884053c","size":1182561,"kind":"pdf","filename":"beethoven-op48-no3.pdf","pages":[1,2,3,4],"page_ids":["beethoven-op48-no3-p1","beethoven-op48-no3-p2","beethoven-op48-no3-p3","beethoven-op48-no3-p4"]},
    "wikimedia": {"drive_id":"1JYyN_nk0lYarszlBlC9nqVfeJxB0FEmz","sha256":"36484c2bfbb57643d992ca77fc0c8f9de0991f52d035d91bb0c780f097de3dcb","size":34636,"kind":"png","filename":"wikimedia-guitar-technical-exercise-no1.png","pages":[1],"page_ids":["wikimedia-guitar-technical-exercise-no1-p1"]},
    "barley": {"drive_id":"1TsmQFpcM4uv52MH37ilKFj1jYY4pyCrG","sha256":"6b3044422b4df58dc4e458cba3de75fd99c88e13c2060498db191238cfdbac6e","size":84689,"kind":"pdf","filename":"barley-your-face-your-tongue-your-wit.pdf","pages":[1,2],"page_ids":["barley-your-face-your-tongue-your-wit-p1","barley-your-face-your-tongue-your-wit-p2"]},
    "carulli": {"drive_id":"1TkE4FVRb16IhVkYH5q10WOs4wPRDdhmi","sha256":"db20e9ce755aa56dd9dbb0436a37a48545442e7961e471f813cde7aaa8fc0f22","size":4662523,"kind":"pdf","filename":"carulli-morceaux-faciles.pdf","pages":list(range(2,11)),"page_ids":[f"carulli-morceaux-faciles-p{i}" for i in range(2,11)]},
    "bach": {"drive_id":"1tgd9EEplOAwJmdurUGctvQ9Rzw6U4zvX","sha256":"692d4317375048b9d520b4d756c3ce992e96ca82b10c3026a5925f1a878fc959","size":3235494,"kind":"pdf","filename":"bach-anna-magdalena.pdf","pages":[4,10,24,40],"page_ids":["bach-anna-magdalena-p4","bach-anna-magdalena-p10","bach-anna-magdalena-p24","bach-anna-magdalena-p40"]},
}
OEMER_CHECKPOINTS: dict[str, dict[str, Any]] = {
    "unet_big/model.onnx": {"url":"https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model.onnx","size":70767752,"sha256":"37512e858731096439746f60b377c049f07055b4a23ec6eb9a178ce92cfba174"},
    "seg_net/model.onnx": {"url":"https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model.onnx","size":38448467,"sha256":"ed2e1a86ea75712ee6cdc740e96f7a36753543cf9bb980227c071c9256d9d82e"},
}

def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()

def _fp(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()

def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_bytes(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())

def _atomic_copy(src: Path, dst: Path) -> None:
    with src.open("rb") as f: _atomic_write_bytes(dst, f.read())

def _validate_exact_file(path: Path, expected_size: int, expected_sha256: str) -> bool:
    return path.is_file() and path.stat().st_size == int(expected_size) and sha256_file(path) == str(expected_sha256)

def _file_record(path: Path, fingerprint: str) -> dict[str, Any]:
    return {"fingerprint":fingerprint,"byteSize":path.stat().st_size,"sha256":sha256_file(path)}

def _cache_record_valid(record: Any, path: Path, expected_fingerprint: str, *, require_image: bool=False) -> bool:
    if not isinstance(record, Mapping) or record.get("fingerprint") != expected_fingerprint: return False
    size, sha = record.get("byteSize"), record.get("sha256")
    if not isinstance(size, int) or size <= 0 or not isinstance(sha, str) or len(sha) != 64: return False
    if not _validate_exact_file(path, size, sha): return False
    return not require_image or cv2.imread(str(path), cv2.IMREAD_GRAYSCALE) is not None

def _new_cache_manifest() -> dict[str, Any]:
    return {"schemaVersion":CACHE_SCHEMA_VERSION,"sourcePages":{},"restoredPages":{},"detectorPages":{}}

def _load_cache_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file(): return _new_cache_manifest()
    try: p = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return _new_cache_manifest()
    if not isinstance(p, dict) or p.get("schemaVersion") != CACHE_SCHEMA_VERSION: return _new_cache_manifest()
    if not isinstance(p.get("sourcePages"), dict) or not isinstance(p.get("restoredPages"), dict): return _new_cache_manifest()
    if not isinstance(p.get("detectorPages", {}), dict): return _new_cache_manifest()
    p.setdefault("detectorPages", {})
    return p

def _save_cache_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest.get("sourcePages"), dict) or not isinstance(manifest.get("restoredPages"), dict) or not isinstance(manifest.get("detectorPages"), dict):
        raise RuntimeError("invalid cache manifest maps")
    _atomic_write_json(path, manifest)

def _page_descriptors() -> list[tuple[str,int,str]]:
    out=[]
    for family,spec in TARGETS.items():
        if family == "restore_model": continue
        out.extend((family,int(n),str(pid)) for n,pid in zip(spec["pages"],spec["page_ids"]))
    if len(out) != 20 or out[0][2] != "beethoven-op48-no3-p1" or len({x[2] for x in out}) != 20:
        raise RuntimeError("V2d development page order mismatch")
    return out

def _download_exact_drive_targets(dest: Path) -> dict[str, Path]:
    from google.colab import auth  # type: ignore
    import google.auth  # type: ignore
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.http import MediaIoBaseDownload  # type: ignore
    dest.mkdir(parents=True, exist_ok=True)
    missing=[k for k,s in TARGETS.items() if not _validate_exact_file(dest/str(s["filename"]),int(s["size"]),str(s["sha256"]))]
    service=None
    if missing:
        auth.authenticate_user(); credentials,_=google.auth.default(); service=build("drive","v3",credentials=credentials,cache_discovery=False)
    found={}
    for key,spec in TARGETS.items():
        out=dest/str(spec["filename"])
        if not _validate_exact_file(out,int(spec["size"]),str(spec["sha256"])):
            tmp=out.with_name(f".{out.name}.download.tmp")
            request=service.files().get_media(fileId=str(spec["drive_id"]))
            with io.FileIO(tmp,"wb") as fh:
                dl=MediaIoBaseDownload(fh,request,chunksize=1024*1024); done=False
                while not done: _,done=dl.next_chunk()
            if not _validate_exact_file(tmp,int(spec["size"]),str(spec["sha256"])):
                tmp.unlink(missing_ok=True); raise RuntimeError(f"exact Drive artifact mismatch: {key}")
            os.replace(tmp,out)
        found[key]=out
        print(f"exact input PASS: {key} {sha256_file(out)[:12]}...")
    return found

def _ensure_url_file(rel: str, spec: Mapping[str, Any]) -> Path:
    dest=CACHE_ROOT/"oemer_checkpoints"/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    if not _validate_exact_file(dest,int(spec["size"]),str(spec["sha256"])):
        tmp=dest.with_name(f".{dest.name}.download.tmp"); urllib.request.urlretrieve(str(spec["url"]),tmp)
        if not _validate_exact_file(tmp,int(spec["size"]),str(spec["sha256"])):
            tmp.unlink(missing_ok=True); raise RuntimeError(f"Oemer checkpoint mismatch: {rel}")
        os.replace(tmp,dest)
    return dest

def _prepare_oemer_checkpoints() -> tuple[Any, dict[str,str]]:
    from oemer import MODULE_PATH  # type: ignore
    from oemer.ete import generate_pred  # type: ignore
    hashes={}
    for rel,spec in OEMER_CHECKPOINTS.items():
        persistent=_ensure_url_file(rel,spec); target=Path(MODULE_PATH)/"checkpoints"/rel; target.parent.mkdir(parents=True,exist_ok=True)
        if not _validate_exact_file(target,int(spec["size"]),str(spec["sha256"])): _atomic_copy(persistent,target)
        if not _validate_exact_file(target,int(spec["size"]),str(spec["sha256"])): raise RuntimeError(f"Oemer installed checkpoint mismatch: {rel}")
        hashes[rel]=sha256_file(target)
    return generate_pred,hashes

def _preflight_oemer_onnx() -> tuple[Any,dict[str,str],Any]:
    import onnxruntime as ort  # type: ignore
    if ort.__version__ != PINNED_ORT_VERSION or "CPUExecutionProvider" not in ort.get_available_providers():
        raise RuntimeError(f"Oemer requires onnxruntime {PINNED_ORT_VERSION} CPUExecutionProvider")
    generate_pred,hashes=_prepare_oemer_checkpoints()
    from oemer import MODULE_PATH  # type: ignore
    for rel in OEMER_CHECKPOINTS:
        session=ort.InferenceSession(str(Path(MODULE_PATH)/"checkpoints"/rel),providers=["CPUExecutionProvider"])
        if session.get_providers()[0] != "CPUExecutionProvider" or not session.get_inputs() or not session.get_outputs(): raise RuntimeError(f"Oemer ONNX preflight failed: {rel}")
        print(f"Oemer preflight PASS: {rel} / ORT {ort.__version__} / CPU")
    return generate_pred,hashes,ort

def _render_pdf_page(pdf: Path, page: int, out: Path) -> None:
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent) as d:
        base=Path(d)/"page"; subprocess.run(["pdftoppm","-f",str(page),"-l",str(page),"-singlefile","-r","72","-png",str(pdf),str(base)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        rendered=base.with_suffix(".png")
        if not rendered.is_file(): raise FileNotFoundError(rendered)
        _atomic_copy(rendered,out)

def _restore_gray(model: Any, gray: np.ndarray, device: Any) -> np.ndarray:
    import torch
    patch,overlap=512,64; stride=patch-overlap; h,w=gray.shape
    acc=np.zeros((h,w),np.float32); cnt=np.zeros((h,w),np.float32)
    with torch.inference_mode():
        for y in range(0,h,stride):
            for x in range(0,w,stride):
                y2,x2=min(y+patch,h),min(x+patch,w); tile=np.full((patch,patch),255,np.uint8); tile[:y2-y,:x2-x]=gray[y:y2,x:x2]
                inp=torch.from_numpy(tile.astype(np.float32)/255.0)[None,None].to(device); pred=model(inp); pred=pred[0] if isinstance(pred,(tuple,list)) else pred
                arr=np.clip(pred.detach().float().cpu().numpy().squeeze(),0,1); crop=(arr*255+0.5).astype(np.uint8)[:y2-y,:x2-x].astype(np.float32)
                acc[y:y2,x:x2]+=crop; cnt[y:y2,x:x2]+=1
    return np.clip(acc/np.maximum(cnt,1),0,255).astype(np.uint8)

def _component_boxes(mask: np.ndarray, min_area: int=4) -> list[tuple[int,int,int,int,int]]:
    n,_,stats,_=cv2.connectedComponentsWithStats((mask>0).astype(np.uint8),connectivity=8); out=[]
    for i in range(1,n):
        x,y,w,h,area=stats[i]
        if area>=min_area and w>0 and h>0: out.append((int(x),int(y),int(x+w),int(y+h),int(area)))
    return out

def _estimate_unit(staff: np.ndarray) -> float:
    rows=np.flatnonzero((staff>0).mean(axis=1)>=0.20)
    if len(rows)<5: return 10.0
    groups=[]
    for row in rows.tolist():
        if not groups or row>groups[-1][-1]+1: groups.append([row])
        else: groups[-1].append(row)
    c=np.array([np.mean(g) for g in groups]); d=np.diff(c); d=d[(d>=3)&(d<=40)]
    return float(np.median(d)) if len(d) else 10.0

def _iou(a: tuple[float,float,float,float],b: tuple[float,float,float,float]) -> float:
    ax1,ay1,ax2,ay2=a; bx1,by1,bx2,by2=b; iw=max(0,min(ax2,bx2)-max(ax1,bx1)); ih=max(0,min(ay2,by2)-max(ay1,by1)); inter=iw*ih
    return inter/max(1e-9,(ax2-ax1)*(ay2-ay1)+(bx2-bx1)*(by2-by1)-inter) if inter else 0.0

def _greedy_recall(src: list[tuple[float,float,float,float]], cand: list[tuple[float,float,float,float]], threshold: float=.20) -> tuple[float,int,int]:
    pairs=sorted(((_iou(a,b),i,j) for i,a in enumerate(src) for j,b in enumerate(cand) if _iou(a,b)>=threshold),reverse=True); si=set(); ci=set(); matched=0
    for _,i,j in pairs:
        if i not in si and j not in ci: si.add(i); ci.add(j); matched+=1
    return matched/max(1,len(src)),matched,max(0,len(cand)-matched)

def _detect_semantic_boxes(path: Path, generate_pred: Any) -> dict[str,list[tuple[float,float,float,float]]]:
    staff,symbols,stems_rests,notehead,clefs_keys=generate_pred(str(path),use_tf=False); unit=_estimate_unit(staff)
    out={k:[] for k in ["staff_line","tab_line","notehead","stem","beam_or_flag","rest","accidental","clef","barline"]}
    for x1,y1,x2,y2,_ in _component_boxes(notehead,max(3,int(unit*unit*.08))):
        w,h=x2-x1,y2-y1
        if .35*unit<=w<=2.2*unit and .35*unit<=h<=2.2*unit: out["notehead"].append(tuple(map(float,(x1,y1,x2,y2))))
    for x1,y1,x2,y2,_ in _component_boxes(stems_rests,max(3,int(unit*.5))):
        w,h=x2-x1,y2-y1; b=tuple(map(float,(x1,y1,x2,y2)))
        if h>=3.6*unit and w<=1.5*unit: out["barline"].append(b)
        elif h>=1.8*unit and w<=1.2*unit: out["stem"].append(b)
        elif .45*unit<=w<=3*unit and .45*unit<=h<=3.6*unit: out["rest"].append(b)
    for x1,y1,x2,y2,_ in _component_boxes(clefs_keys,max(3,int(unit*unit*.10))):
        w,h=x2-x1,y2-y1; b=tuple(map(float,(x1,y1,x2,y2)))
        if h>=2.4*unit and w>=.8*unit: out["clef"].append(b)
        elif .45*unit<=h<=3*unit and .25*unit<=w<=2.2*unit: out["accidental"].append(b)
    residue=(symbols>0).astype(np.uint8); residue[(notehead>0)|(stems_rests>0)|(clefs_keys>0)|(staff>0)]=0
    for x1,y1,x2,y2,_ in _component_boxes(residue,max(3,int(unit*unit*.10))):
        w,h=x2-x1,y2-y1
        if (w>=1.4*unit and h<=1.8*unit) or (h>=.8*unit and w<=1.8*unit): out["beam_or_flag"].append(tuple(map(float,(x1,y1,x2,y2))))
    gray=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
    if gray is None: raise RuntimeError(f"cannot read {path}")
    for d in conservative_line_system_detector(gray): out[d.class_id].append(tuple(map(float,d.bbox)))
    return out

def _teacher_manifest(repo: Path) -> dict[str,Any]:
    def load(name: str) -> Any: return json.loads((repo/"evidence/stage11/v2c"/name).read_text())
    teacher=materialize_teacher_review_manifest(load("v2c-expected-class-manifest.v1.json"),load("v2c-teacher-review-overlay.v1.json"),load("v2c-teacher-review-resolution.v1.json"))["manifest"]
    if len(teacher_present_class_pairs(teacher))!=171: raise RuntimeError("teacher present-pair count mismatch")
    return teacher

def _source_fp(family: str,page: int) -> str:
    s=TARGETS[family]; return _fp({"family":family,"page":page,"inputSha256":s["sha256"],"render":SOURCE_RENDER_VERSION})

def _restore_fp(source_record: Mapping[str,Any]) -> str:
    return _fp({"sourceSha256":source_record["sha256"],"modelSha256":TARGETS["restore_model"]["sha256"],"algorithm":RESTORE_ALGORITHM_VERSION})

def _detector_progress_fingerprint(page_id: str,source_record: Mapping[str,Any],restored_record: Mapping[str,Any],teacher_page: Mapping[str,Any],checkpoint_hashes: Mapping[str,str]) -> str:
    return _fp({"pageId":page_id,"sourceSha256":source_record["sha256"],"restoredSha256":restored_record["sha256"],"teacherClasses":teacher_page["classes"],"oemerCommit":OEMER_UPSTREAM_COMMIT,"checkpoints":dict(checkpoint_hashes),"logic":DETECTOR_LOGIC_VERSION})

def _ensure_source(family: str,page: int,page_id: str,inputs: Mapping[str,Path],manifest: dict[str,Any],manifest_path: Path) -> tuple[Path,dict[str,Any]]:
    path=CACHE_ROOT/"source_pages"/f"{page_id}.png"; fp=_source_fp(family,page); record=manifest["sourcePages"].get(page_id)
    if not _cache_record_valid(record,path,fp,require_image=True):
        if TARGETS[family]["kind"]=="pdf": _render_pdf_page(inputs[family],page,path)
        else: _atomic_copy(inputs[family],path)
        if cv2.imread(str(path),cv2.IMREAD_GRAYSCALE) is None: raise RuntimeError(f"source page unreadable: {page_id}")
        record=_file_record(path,fp); manifest["sourcePages"][page_id]=record; _save_cache_manifest(manifest_path,manifest); print(f"source SAVED: {page_id}")
    else: print(f"source cache reuse: {page_id}")
    return path,dict(record)

def _restored_cached(page_id: str,source_record: Mapping[str,Any],manifest: Mapping[str,Any]) -> tuple[Path,dict[str,Any]]|None:
    path=CACHE_ROOT/"restored_pages"/f"{page_id}.png"; fp=_restore_fp(source_record); rec=manifest["restoredPages"].get(page_id)
    return (path,dict(rec)) if _cache_record_valid(rec,path,fp,require_image=True) else None

def _save_restored(page_id: str,image: np.ndarray,source_record: Mapping[str,Any],manifest: dict[str,Any],manifest_path: Path) -> tuple[Path,dict[str,Any]]:
    ok,buf=cv2.imencode(".png",image,[cv2.IMWRITE_PNG_COMPRESSION,3])
    if not ok: raise RuntimeError(f"PNG encode failed: {page_id}")
    path=CACHE_ROOT/"restored_pages"/f"{page_id}.png"; _atomic_write_bytes(path,buf.tobytes()); rec=_file_record(path,_restore_fp(source_record)); manifest["restoredPages"][page_id]=rec; _save_cache_manifest(manifest_path,manifest); print(f"restore SAVED: {page_id}"); return path,rec

def _compute_detector_page_record(page_id: str,teacher_page: Mapping[str,Any],fingerprint: str,src_path: Path,cand_path: Path,generate_pred: Any,*,source_dets: Any=None,restored_dets: Any=None) -> dict[str,Any]:
    sd=source_dets if source_dets is not None else _detect_semantic_boxes(src_path,generate_pred); cd=restored_dets if restored_dets is not None else _detect_semantic_boxes(cand_path,generate_pred)
    evaluable=[]; matched_pairs=[]; metrics=[]
    for class_id,record in teacher_page["classes"].items():
        if record["state"]!="present": continue
        sb=sd.get(class_id,[]); cb=cd.get(class_id,[])
        if not sb: continue
        evaluable.append([page_id,class_id]); recall,matched,cand_only=_greedy_recall(sb,cb)
        if recall>=.80: matched_pairs.append([page_id,class_id])
        metrics.append({"pageId":page_id,"classId":class_id,"sourceCount":len(sb),"candidateCount":len(cb),"matchedCount":matched,"sourceRecall":recall,"candidateOnlyCount":cand_only})
    return {"schemaVersion":DETECTOR_PROGRESS_SCHEMA_VERSION,"pageId":page_id,"fingerprint":fingerprint,"sourceEvaluablePairs":evaluable,"semanticMatchedPairs":matched_pairs,"pairMetrics":metrics}

def _load_detector_page_record(path: Path,record: Any,page_id: str,fingerprint: str) -> dict[str,Any]|None:
    if not _cache_record_valid(record,path,fingerprint): return None
    try: p=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return None
    if not isinstance(p,dict) or p.get("schemaVersion")!=DETECTOR_PROGRESS_SCHEMA_VERSION or p.get("pageId")!=page_id or p.get("fingerprint")!=fingerprint: return None
    if not all(isinstance(p.get(k),list) for k in ("sourceEvaluablePairs","semanticMatchedPairs","pairMetrics")): return None
    return p

def _get_torch_gpu_model(model_path: Path) -> tuple[Any,Any,Any]:
    import torch
    if not torch.cuda.is_available(): raise RuntimeError("CUDA required because one or more restored pages are missing")
    device=torch.device("cuda"); model=torch.jit.load(str(model_path),map_location=device).to(device).eval(); return torch,device,model

def run_colab_benchmark() -> Path:
    my_drive=Path("/content/drive/MyDrive")
    if not my_drive.exists(): raise FileNotFoundError(f"Drive not mounted: {my_drive}")
    CACHE_ROOT.mkdir(parents=True,exist_ok=True); RESULT_ROOT.mkdir(parents=True,exist_ok=True)
    manifest_path=CACHE_ROOT/"cache_manifest.json"; manifest=_load_cache_manifest(manifest_path)
    repo=Path(__file__).resolve().parents[2]; descriptors=_page_descriptors()

    # 1) Exact inputs, then 2) both pinned ORT CPU sessions. No Restore before these pass.
    inputs=_download_exact_drive_targets(CACHE_ROOT/"exact_inputs")
    generate_pred,checkpoint_hashes,ort=_preflight_oemer_onnx()
    teacher=_teacher_manifest(repo); teacher_pages={p["pageId"]:p for p in teacher["pages"]}

    source_paths={}; source_records={}; restored_paths={}; restored_records={}
    first_family,first_page,first_id=descriptors[0]
    p,r=_ensure_source(first_family,first_page,first_id,inputs,manifest,manifest_path); source_paths[first_id]=p; source_records[first_id]=r
    first_source_dets=_detect_semantic_boxes(p,generate_pred); print("Oemer real-image smoke PASS: source")

    # 3) restore/reuse Beethoven p1, then real Oemer restored smoke before all remaining Restore.
    first_cached=_restored_cached(first_id,r,manifest); torch=None; device=None; model=None
    if first_cached is None:
        torch,device,model=_get_torch_gpu_model(inputs["restore_model"]); gray=cv2.imread(str(p),cv2.IMREAD_GRAYSCALE)
        if gray is None: raise RuntimeError(f"cannot read {p}")
        first_cached=_save_restored(first_id,_restore_gray(model,gray,device),r,manifest,manifest_path)
    restored_paths[first_id],restored_records[first_id]=first_cached
    first_restored_dets=_detect_semantic_boxes(restored_paths[first_id],generate_pred); print("Oemer real-image smoke PASS: source + restored")

    # 4) Materialize/reuse remaining sources, then determine exactly which Restore pages are missing.
    for family,page,page_id in descriptors[1:]:
        p,r=_ensure_source(family,page,page_id,inputs,manifest,manifest_path); source_paths[page_id]=p; source_records[page_id]=r
    missing=[]
    for _,_,page_id in descriptors[1:]:
        c=_restored_cached(page_id,source_records[page_id],manifest)
        if c is None: missing.append(page_id)
        else: restored_paths[page_id],restored_records[page_id]=c
    if missing and model is None: torch,device,model=_get_torch_gpu_model(inputs["restore_model"])
    for i,(_,_,page_id) in enumerate(descriptors[1:],2):
        if page_id in restored_records: print(f"restore cache reuse {i:02d}/20 {page_id}"); continue
        gray=cv2.imread(str(source_paths[page_id]),cv2.IMREAD_GRAYSCALE)
        if gray is None: raise RuntimeError(f"cannot read {source_paths[page_id]}")
        path,rec=_save_restored(page_id,_restore_gray(model,gray,device),source_records[page_id],manifest,manifest_path); restored_paths[page_id]=path; restored_records[page_id]=rec; print(f"restore {i:02d}/20 {page_id}")
    if model is not None:
        del model
        assert torch is not None
        torch.cuda.empty_cache()

    # 5) Per-page detector progress. Each JSON and its SHA/size manifest record are durable before next page.
    eval_pairs=set(); semantic_pairs=set(); pair_metrics=[]; detector_dir=CACHE_ROOT/"detector_pages"; detector_dir.mkdir(parents=True,exist_ok=True)
    for i,(_,_,page_id) in enumerate(descriptors,1):
        fingerprint=_detector_progress_fingerprint(page_id,source_records[page_id],restored_records[page_id],teacher_pages[page_id],checkpoint_hashes); progress=detector_dir/f"{page_id}.json"
        page_result=_load_detector_page_record(progress,manifest["detectorPages"].get(page_id),page_id,fingerprint)
        if page_result is None:
            page_result=_compute_detector_page_record(page_id,teacher_pages[page_id],fingerprint,source_paths[page_id],restored_paths[page_id],generate_pred,source_dets=first_source_dets if page_id==first_id else None,restored_dets=first_restored_dets if page_id==first_id else None)
            _atomic_write_json(progress,page_result); manifest["detectorPages"][page_id]=_file_record(progress,fingerprint); _save_cache_manifest(manifest_path,manifest); print(f"detector SAVED {i:02d}/20 {page_id}")
        else: print(f"detector cache reuse {i:02d}/20 {page_id}")
        eval_pairs.update(tuple(x) for x in page_result["sourceEvaluablePairs"]); semantic_pairs.update(tuple(x) for x in page_result["semanticMatchedPairs"]); pair_metrics.extend(page_result["pairMetrics"])

    source_cov=benchmark_coverage_from_present_pairs(teacher,eval_pairs); semantic_cov=benchmark_coverage_from_present_pairs(teacher,semantic_pairs)
    try:
        import torch as runtime_torch
        torch_version=runtime_torch.__version__; cuda=runtime_torch.cuda.is_available(); cuda_name=runtime_torch.cuda.get_device_name(0) if cuda else None
    except ImportError: torch_version=None; cuda=False; cuda_name=None
    result={
        "schemaVersion":"stage11.v2d.detector-benchmark-result.v1","contractId":"stage11.v2c.semantic-preservation.nonheldout.v1","generatedOn":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"candidateId":"oemer-onnx-segmentation-dbe2a933",
        "boundary":{"developmentOnly":True,"teacherGroundTruthFrozen":True,"detectorOutputUsedAsGroundTruth":False,"trainingPerformed":False,"fineTuningPerformed":False,"heldOutAccessed":False,"productionPromotionAuthorized":False,"stage12EntryAuthorized":False},
        "runtime":{"purpose":"exploratory_detector_benchmark","device":"GPU_RESTORE_PLUS_CPU_DETECTOR" if missing else "CPU_DETECTOR_WITH_VERIFIED_GPU_RESTORE_CACHE","torchVersion":torch_version,"cudaAvailable":cuda,"cudaDevice":cuda_name,"onnxruntimeVersion":ort.__version__,"onnxProviders":ort.get_available_providers(),"detectorExecutionProvider":"CPUExecutionProvider","restoreExecutionMode":"GPU exploratory; verified Drive cache reusable; final canonical CPU rerun required","finalCanonicalCpuRerunRequired":True,"restoredPagesRecomputed":len(missing),"restoredPagesReusedAtStart":20-len(missing)},
        "inputs":{"teacherPresentClassPageCount":171,"sourceFiles":{k:{"sha256":TARGETS[k]["sha256"],"byteSize":TARGETS[k]["size"],"driveFileId":TARGETS[k]["drive_id"],"cachedPath":str(v)} for k,v in inputs.items()},"oemerUpstreamCommit":OEMER_UPSTREAM_COMMIT,"oemerCheckpointSha256":checkpoint_hashes,"oemerCompatibilityRuntime":{"onnxruntime":PINNED_ORT_VERSION,"provider":"CPUExecutionProvider","preflightPassed":True}},
        "coverage":{"eligibleExpectedPresentClassPageCount":source_cov["eligibleExpectedPresentClassPageCount"],"confidentlyEvaluatedExpectedPresentClassPageCount":source_cov["confidentlyEvaluatedExpectedPresentClassPageCount"],"applicableClassDetectorCoverage":source_cov["applicableClassDetectorCoverage"],"classCoverage":source_cov["classCoverage"]},
        "semanticExploration":{"matchedAtRecallAtLeast0_80ClassPageCount":semantic_cov["confidentlyEvaluatedExpectedPresentClassPageCount"],"matchedAtRecallAtLeast0_80Coverage":semantic_cov["applicableClassDetectorCoverage"],"pairMetrics":pair_metrics},
        "claimBoundary":{"semanticPreservationEstablished":False,"productionReady":False,"canonicalCpuEvidenceRequiredBeforeAnyUpgrade":True},
    }
    print(validate_detector_benchmark_result(result)); out=RESULT_ROOT/RESULT_FILENAME; _atomic_write_json(out,result); print("V2D RECOVERY PASS"); print("SAVED:",out); return out

def main(argv: list[str]|None=None) -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--run",action="store_true"); args=p.parse_args(argv)
    if not args.run: raise SystemExit("Refusing implicit execution; pass --run")
    run_colab_benchmark(); return 0

if __name__ == "__main__": raise SystemExit(main())
