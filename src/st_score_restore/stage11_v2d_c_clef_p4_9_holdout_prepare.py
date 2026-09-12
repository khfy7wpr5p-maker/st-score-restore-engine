from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pymupdf"])
    import fitz

try:
    from PIL import Image
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pillow"])
    from PIL import Image


ROOT = Path("/content/drive/MyDrive/ST_SCORE_RESTORE_STAGE11_EVAL/P4_C_CLEF_HOLDOUT_P4_9")
INCOMING = ROOT / "INCOMING_PDFS"
PREPARED = ROOT / "_PREPARED"
PAGES_DIR = PREPARED / "pages"
ANNOTATIONS = ROOT / "_ANNOTATIONS"

RENDER_DPI = 200
SOURCE_FREEZE_COMMIT = "f683f964ff764d191345b8db80c17671836b38b9"
SOURCE_FREEZE_PATH = "evidence/stage11/v2d/v2d-c-clef-p4_9-independent-holdout-source-freeze.v1.json"

SELECTED = [
    {
        "index": 1,
        "name": "01_Bach_Matthaeuspassion_BWV244_excerpt.pdf",
        "sha256": "c960952dbab6323c7ec366030629a5f87f36353551bf418ce68dc814bed90c52",
        "pages": [1, 2],
        "rotate_clockwise": 0,
        "slug": "bach-matthaeuspassion",
    },
    {
        "index": 2,
        "name": "02_mixed_old_score_dies_irae.pdf",
        "sha256": "4d5ea958bc397fe9664514ca435b0c91b19ffb5436c56ca447ea8894191c15d2",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "dies-irae",
    },
    {
        "index": 3,
        "name": "03_mixed_old_score_kyrie_a.pdf",
        "sha256": "ea382f190adb605598946ffdbf196d5268a5893ec99a2219ff555e367e8e44d0",
        "pages": [1],
        "rotate_clockwise": 90,
        "slug": "kyrie-a",
    },
    {
        "index": 4,
        "name": "04_mixed_old_score_kyrie_b.pdf",
        "sha256": "3e540a80222f2103689d7159b851b99c26672cc204c960552c0a172c96d60ecd",
        "pages": [1],
        "rotate_clockwise": 90,
        "slug": "kyrie-b",
    },
    {
        "index": 5,
        "name": "05_Haydn_Creation_orchestral_page.pdf",
        "sha256": "e5e2450011908eb89b56b8e3f497d2544a3e0bd6f2a4ef1d7b43a781b3e60f1d",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "haydn-creation",
    },
    {
        "index": 6,
        "name": "06_Agnus_Dei_orchestral_choral_page.pdf",
        "sha256": "64de53d35865cc8bc7a179c72be322619deb3d3a459c1ad7626f31e8be9b50b2",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "agnus-dei",
    },
    {
        "index": 7,
        "name": "07_Mendelssohn_Elijah_orchestral_page.pdf",
        "sha256": "e125ef1f05553a87af6b8c94ad580941b61b985f11a823b7d2962208d5a94823",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "mendelssohn-elijah",
    },
    {
        "index": 8,
        "name": "08_Mozart_Mass_C_minor_page_A.pdf",
        "sha256": "9d10079705ea3b3c40131360100da79b751cd57368f82a40b4db0330430c109a",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "mozart-mass-c-minor",
    },
    {
        "index": 10,
        "name": "10_orchestral_page_viola.pdf",
        "sha256": "2faa289ac0a75575df7605a9b0a9411416633b4fb6135cd573b6f43a9633e507",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "orchestral-viola",
    },
    {
        "index": 11,
        "name": "11_Telemann_TWV52e3_C1_C3_source.pdf",
        "sha256": "bcbda0a9dcf2e9a678f59fdfc36b4b400bcddaa44d1bf6f8aa6c71f125784908",
        "pages": [1],
        "rotate_clockwise": 0,
        "slug": "telemann-twv52e3",
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_atomic(path: Path, payload: dict) -> None:
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def render_page(pdf_path: Path, page_number_1based: int, rotate_clockwise: int) -> Image.Image:
    doc = fitz.open(str(pdf_path))
    try:
        if page_number_1based < 1 or page_number_1based > len(doc):
            raise RuntimeError(f"Page {page_number_1based} out of range for {pdf_path.name} ({len(doc)} pages)")
        page = doc[page_number_1based - 1]
        scale = RENDER_DPI / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    finally:
        doc.close()

    if rotate_clockwise not in (0, 90, 180, 270):
        raise RuntimeError(f"Unsupported rotation: {rotate_clockwise}")
    if rotate_clockwise:
        # PIL positive angles are counter-clockwise; convert clockwise to CCW equivalent.
        image = image.rotate((360 - rotate_clockwise) % 360, expand=True)
    return image


def main() -> None:
    if not ROOT.is_dir():
        raise RuntimeError(f"P4.9 root missing: {ROOT}")
    if not INCOMING.is_dir():
        raise RuntimeError(f"Incoming PDF folder missing: {INCOMING}")

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS.mkdir(parents=True, exist_ok=True)

    source_records = []
    rendered_pages = []
    rendered_hashes: dict[str, str] = {}

    for source in SELECTED:
        pdf_path = INCOMING / source["name"]
        if not pdf_path.is_file():
            raise RuntimeError(f"Frozen source missing: {pdf_path}")

        actual_pdf_sha = sha256_file(pdf_path)
        if actual_pdf_sha != source["sha256"]:
            raise RuntimeError(
                f"Frozen source SHA mismatch for {source['name']}:\n"
                f"expected {source['sha256']}\nactual   {actual_pdf_sha}"
            )

        source_records.append(
            {
                "sourceIndex": source["index"],
                "sourcePdfName": source["name"],
                "sourcePdfSha256": actual_pdf_sha,
                "selectedPages": source["pages"],
                "rotationClockwiseDegrees": source["rotate_clockwise"],
            }
        )

        for page_no in source["pages"]:
            page_id = f"p4_9-{source['index']:02d}-{source['slug']}-p{page_no:04d}"
            file_name = f"{page_id}.png"
            out_path = PAGES_DIR / file_name

            image = render_page(pdf_path, page_no, source["rotate_clockwise"])
            image.save(out_path, format="PNG", optimize=False)
            png_sha = sha256_file(out_path)

            if png_sha in rendered_hashes:
                raise RuntimeError(
                    "Duplicate rendered physical page detected after frozen preprocessing: "
                    f"{page_id} duplicates {rendered_hashes[png_sha]}"
                )
            rendered_hashes[png_sha] = page_id

            rendered_pages.append(
                {
                    "pageId": page_id,
                    "imagePath": f"pages/{file_name}",
                    "imageSha256": png_sha,
                    "width": image.width,
                    "height": image.height,
                    "sourcePdfName": source["name"],
                    "sourcePdfSha256": actual_pdf_sha,
                    "sourcePageNumber": page_no,
                    "renderDpi": RENDER_DPI,
                    "rotationClockwiseDegrees": source["rotate_clockwise"],
                }
            )
            print(
                f"RENDERED {len(rendered_pages):02d}/11 | {page_id} | "
                f"{image.width}x{image.height} | rotCW={source['rotate_clockwise']}"
            )

    if len(source_records) != 10:
        raise RuntimeError(f"Expected 10 frozen PDF sources, got {len(source_records)}")
    if len(rendered_pages) != 11:
        raise RuntimeError(f"Expected 11 unique physical pages, got {len(rendered_pages)}")

    manifest = {
        "artifactType": "C_CLEF_P4_9_HOLDOUT_SOURCE_PAGE_MANIFEST",
        "schemaVersion": "1.0.0",
        "phase": "Stage 11 v2d / P4.9 independent C-clef holdout",
        "status": "PREPARED_PENDING_BLINDED_TEACHER_ANNOTATION",
        "sourceFreezeCommit": SOURCE_FREEZE_COMMIT,
        "sourceFreezePath": SOURCE_FREEZE_PATH,
        "sourceCount": 10,
        "pageCount": 11,
        "renderDpi": RENDER_DPI,
        "detectorOutputsAccessed": False,
        "previousP4_7HoldoutReused": False,
        "duplicatePhysicalPagesCountedOnce": True,
        "sources": source_records,
        "pages": rendered_pages,
    }

    manifest_path = PREPARED / "c_clef_p4_9_holdout_source_page_manifest.v1.json"
    write_json_atomic(manifest_path, manifest)
    manifest_sha = sha256_file(manifest_path)

    template = {
        "artifactType": "C_CLEF_P4_9_HOLDOUT_TEACHER_BOXES_TEMPLATE",
        "schemaVersion": "1.0.0",
        "phase": "Stage 11 v2d / P4.9 independent C-clef holdout",
        "status": "PENDING_TEACHER_ANNOTATION",
        "sourceManifestSha256": manifest_sha,
        "pageCount": 11,
        "acceptedLabels": ["C1", "C3", "C4", "AMBIGUOUS"],
        "annotationPolicy": "Annotate every visible C-clef on every page. Do not load detector/model output. Use AMBIGUOUS only when subtype cannot be determined safely.",
        "detectorOutputsAccessed": False,
        "pages": {
            page["pageId"]: {
                "sourcePdfName": page["sourcePdfName"],
                "sourcePageNumber": page["sourcePageNumber"],
                "completed": False,
                "boxes": [],
            }
            for page in rendered_pages
        },
    }

    template_path = ANNOTATIONS / "c_clef_p4_9_holdout_teacher_boxes.template.v1.json"
    write_json_atomic(template_path, template)
    template_sha = sha256_file(template_path)

    result = {
        "artifactType": "C_CLEF_P4_9_HOLDOUT_PREPARATION_RESULT",
        "schemaVersion": "1.0.0",
        "status": "PREPARATION_COMPLETE_PENDING_TEACHER_ANNOTATION",
        "sourceCount": 10,
        "pageCount": 11,
        "renderDpi": RENDER_DPI,
        "manifestPath": str(manifest_path),
        "manifestSha256": manifest_sha,
        "teacherTemplatePath": str(template_path),
        "teacherTemplateSha256": template_sha,
        "detectorOutputsAccessed": False,
        "qualificationRunAuthorized": False,
        "nextSafeAction": "Complete blinded teacher annotation on all 11 prepared pages, freeze teacher truth, then run frozen P4.8 once with no retuning.",
    }
    result_path = PREPARED / "p4_9_holdout_preparation_result.v1.json"
    write_json_atomic(result_path, result)

    print("=" * 72)
    print("P4.9 HOLDOUT PREPARATION COMPLETE")
    print("=" * 72)
    print("Frozen PDF sources : 10")
    print("Unique pages       : 11")
    print("Render DPI         : 200")
    print("Manifest SHA-256   :", manifest_sha)
    print("Teacher template   :", template_path)
    print("Template SHA-256   :", template_sha)
    print("Detector output    : NOT READ")
    print("NEXT: blinded teacher annotation on 11 pages")


if __name__ == "__main__":
    main()
