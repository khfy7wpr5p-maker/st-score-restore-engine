"""Stage 11 V2d staff-line teacher mask/topology preparation and validation.

This module prepares a source-only annotation template from already-admitted V2c
20-page development evidence and validates completed HUMAN staff-line truth.
It never derives teacher truth from detector output or restored images.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


FULL20_PATH = Path("evidence/stage11/v2c/v2c-full20-repeat-execution.v1.json")
LINE_EVIDENCE_PATH = Path("evidence/stage11/v2c/v2c-line-semantic-evidence.v1.json")
PLAN_PATH = Path("evidence/stage11/v2d/v2d-staff-line-human-mask-topology-plan.v1.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_contracts(repo_root: Path = Path(".")) -> Dict[str, Dict[str, Any]]:
    full20 = _load_json(repo_root / FULL20_PATH)
    line = _load_json(repo_root / LINE_EVIDENCE_PATH)
    expected_staff: Dict[str, bool] = {}
    cols = list(line["pageResultColumns"])
    page_id_index = cols.index("pageId")
    expected_index = cols.index("expectedStaff")
    for row in line["pageResults"]:
        expected_staff[str(row[page_id_index])] = str(row[expected_index]) == "present"

    contracts: Dict[str, Dict[str, Any]] = {}
    for page in full20["pages"]:
        page_id = str(page["pageId"])
        if page_id not in expected_staff:
            raise ValueError(f"Missing staff expectation for {page_id}")
        contracts[page_id] = {
            "pageId": page_id,
            "sourceFamilyId": str(page["sourceFamilyId"]),
            "sourcePage": int(page["sourcePage"]),
            "sourceRenderSha256": str(page["sourceRenderSha256"]),
            "width": int(page["width"]),
            "height": int(page["height"]),
            "expectedStaffPresent": bool(expected_staff[page_id]),
        }
    if len(contracts) != 20:
        raise ValueError(f"Expected 20 V2c pages, found {len(contracts)}")
    if sum(1 for item in contracts.values() if item["expectedStaffPresent"]) != 18:
        raise ValueError("Expected exactly 18 staff-present pages")
    return contracts


def build_template(repo_root: Path = Path(".")) -> Dict[str, Any]:
    contracts = source_contracts(repo_root)
    return {
        "schemaVersion": "stage11.v2d.staff-line-teacher-mask-topology.v1",
        "status": "ANNOTATION_NOT_STARTED",
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
                **contract,
                "completed": False,
                "staffLineMaskPath": None,
                "staffLineMaskSha256": None,
                "systems": [],
                "notes": "",
            }
            for page_id, contract in sorted(contracts.items())
        },
    }


def _bbox_valid(bbox: Sequence[Any], width: int, height: int) -> bool:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return False
    try:
        x1, y1, x2, y2 = map(float, bbox)
    except (TypeError, ValueError):
        return False
    return 0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height


def _point_valid(point: Sequence[Any], width: int, height: int) -> bool:
    if not isinstance(point, (list, tuple)) or len(point) != 2:
        return False
    try:
        x, y = map(float, point)
    except (TypeError, ValueError):
        return False
    return 0 <= x < width and 0 <= y < height


def validate_teacher_truth(
    artifact: Mapping[str, Any],
    repo_root: Path = Path("."),
    *,
    require_complete: bool = True,
    mask_root: Path | None = None,
) -> List[str]:
    """Return validation errors. An empty list means structurally valid truth.

    When ``mask_root`` is supplied, mask PNG bytes are additionally verified as
    exact-size, binary {0,255} images and their SHA-256 values are checked.
    """
    errors: List[str] = []
    contracts = source_contracts(repo_root)

    required_false = (
        "detectorOutputsShownToTeacher",
        "restoredOutputsShownToTeacher",
        "lineDetectorGeometryShownToTeacher",
    )
    for key in required_false:
        if artifact.get(key) is not False:
            errors.append(f"{key} must be false")
    if artifact.get("teacherAnnotationIndependent") is not True:
        errors.append("teacherAnnotationIndependent must be true")
    if artifact.get("developmentOnly") is not True:
        errors.append("developmentOnly must be true")
    if artifact.get("qualificationEvidence") is not False:
        errors.append("qualificationEvidence must be false before post-annotation measurement")

    pages = artifact.get("pages")
    if not isinstance(pages, Mapping):
        return errors + ["pages must be an object"]
    if set(pages) != set(contracts):
        errors.append("page IDs must exactly match the frozen 20-page V2c corpus")

    completed_count = 0
    for page_id, contract in contracts.items():
        page = pages.get(page_id)
        if not isinstance(page, Mapping):
            errors.append(f"{page_id}: missing page record")
            continue
        for key in ("sourceRenderSha256", "width", "height", "expectedStaffPresent"):
            if page.get(key) != contract[key]:
                errors.append(f"{page_id}: {key} does not match frozen source contract")
        completed = page.get("completed") is True
        if completed:
            completed_count += 1
        elif require_complete:
            errors.append(f"{page_id}: annotation incomplete")
            continue

        systems = page.get("systems", [])
        if not isinstance(systems, list):
            errors.append(f"{page_id}: systems must be a list")
            continue
        width, height = contract["width"], contract["height"]
        system_ids: set[str] = set()
        confirmed_count = 0
        for system in systems:
            if not isinstance(system, Mapping):
                errors.append(f"{page_id}: invalid system record")
                continue
            system_id = str(system.get("systemId", ""))
            if not system_id or system_id in system_ids:
                errors.append(f"{page_id}: systemId must be non-empty and unique")
            system_ids.add(system_id)
            status = system.get("status")
            if status not in {"CONFIRMED", "AMBIGUOUS"}:
                errors.append(f"{page_id}/{system_id}: invalid status")
            if not _bbox_valid(system.get("bbox", []), width, height):
                errors.append(f"{page_id}/{system_id}: invalid bbox")
            lines = system.get("lines")
            if not isinstance(lines, list):
                errors.append(f"{page_id}/{system_id}: lines must be a list")
                continue
            if status == "CONFIRMED":
                confirmed_count += 1
                if system.get("lineCount") != 5 or len(lines) != 5:
                    errors.append(f"{page_id}/{system_id}: confirmed staff must have exactly 5 lines")
                indexes = [line.get("lineIndex") for line in lines if isinstance(line, Mapping)]
                if indexes != [1, 2, 3, 4, 5]:
                    errors.append(f"{page_id}/{system_id}: line indexes must be ordered [1,2,3,4,5]")
            median_ys: List[float] = []
            for line in lines:
                if not isinstance(line, Mapping):
                    errors.append(f"{page_id}/{system_id}: invalid line record")
                    continue
                points = line.get("centerlinePoints")
                if not isinstance(points, list) or len(points) < 2:
                    errors.append(f"{page_id}/{system_id}: each line needs at least two centerline points")
                    continue
                if any(not _point_valid(point, width, height) for point in points):
                    errors.append(f"{page_id}/{system_id}: centerline point out of source bounds")
                ys = [float(point[1]) for point in points if _point_valid(point, width, height)]
                if ys:
                    median_ys.append(sorted(ys)[len(ys) // 2])
            if status == "CONFIRMED" and len(median_ys) == 5 and median_ys != sorted(median_ys):
                errors.append(f"{page_id}/{system_id}: lines are not top-to-bottom ordered")

        mask_path = page.get("staffLineMaskPath")
        mask_sha = page.get("staffLineMaskSha256")
        if completed and (not isinstance(mask_path, str) or not mask_path):
            errors.append(f"{page_id}: completed page requires staffLineMaskPath")
        if completed and (not isinstance(mask_sha, str) or len(mask_sha) != 64):
            errors.append(f"{page_id}: completed page requires mask SHA-256")
        if completed and contract["expectedStaffPresent"] and confirmed_count == 0:
            errors.append(f"{page_id}: staff-present page requires at least one CONFIRMED system")
        if completed and not contract["expectedStaffPresent"] and systems:
            errors.append(f"{page_id}: teacher-confirmed staff-absent page must have zero systems")

        if completed and mask_root is not None and isinstance(mask_path, str) and mask_path:
            mask_file = mask_root / mask_path
            if not mask_file.is_file():
                errors.append(f"{page_id}: mask file missing: {mask_file}")
            else:
                if sha256_file(mask_file) != mask_sha:
                    errors.append(f"{page_id}: mask SHA-256 mismatch")
                try:
                    import cv2
                    import numpy as np
                    image = cv2.imread(str(mask_file), cv2.IMREAD_GRAYSCALE)
                    if image is None:
                        errors.append(f"{page_id}: unreadable mask")
                    else:
                        if image.shape != (height, width):
                            errors.append(f"{page_id}: mask dimensions differ from source")
                        values = set(int(v) for v in np.unique(image))
                        if not values.issubset({0, 255}):
                            errors.append(f"{page_id}: mask must contain binary values 0/255 only")
                        if not contract["expectedStaffPresent"] and int(np.count_nonzero(image)) != 0:
                            errors.append(f"{page_id}: staff-absent mask must be empty")
                except ImportError:
                    errors.append("OpenCV/numpy required when mask_root is supplied")

    if artifact.get("pageCount") != 20:
        errors.append("pageCount must be 20")
    if artifact.get("completedPageCount") != completed_count:
        errors.append("completedPageCount does not match page records")
    if require_complete and completed_count != 20:
        errors.append(f"expected 20 completed pages, found {completed_count}")
    return errors


def write_template(path: Path, repo_root: Path = Path(".")) -> None:
    payload = build_template(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--write-template", type=Path)
    parser.add_argument("--validate", type=Path)
    parser.add_argument("--mask-root", type=Path)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    if args.write_template:
        write_template(args.write_template)
        print(f"template: {args.write_template}")
    if args.validate:
        artifact = _load_json(args.validate)
        errs = validate_teacher_truth(
            artifact,
            require_complete=not args.allow_incomplete,
            mask_root=args.mask_root,
        )
        if errs:
            raise SystemExit("\n".join(errs))
        print("VALID staff-line teacher mask/topology artifact")
