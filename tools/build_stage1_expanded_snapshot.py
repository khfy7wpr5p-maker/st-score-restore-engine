"""Build/check post-C17 Stage 1 expanded v2 evidence without mutating C15/C16."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.dataset_contract_constants import DEGRADATIONS, INPUT_MEDIA, NOTATION_KINDS, SOURCE_KINDS  # noqa: E402
from st_score_restore.dataset_manifest import canonical_sha256, load_json_object, validate_dataset_catalog, validate_dataset_snapshot  # noqa: E402
from tools.evaluate_stage1_corpus_readiness import evaluate_corpus_readiness  # noqa: E402

OUT = ROOT / "evidence" / "stage1c" / "corpus"
CATALOG_PATH = OUT / "catalog.v2.json"
SNAPSHOT_PATH = OUT / "snapshot.expanded.v2.json"
REPORT_PATH = OUT / "coverage-bias-report.v2.json"

SOURCES = (
    (OUT / "catalog.v1.json", "dataset.item.imslp799143-beethoven-op48-no3.v1"),
    (ROOT / "evidence/stage1c/wikimedia-guitar-technical-exercise-no1/catalog.v1.json", "dataset.item.wikimedia-guitar-technical-exercise-no1.v1"),
    (ROOT / "evidence/stage1c/imslp911664-c17b-guitar-tab/catalog.v1.json", "dataset.item.barley-your-face-your-tongue-your-wit-guitar-tab.v1"),
    (ROOT / "evidence/stage1c/imslp82860-c17c-noise/catalog.v2.json", "dataset.item.imslp82860-chopin-op69.v2"),
    (ROOT / "evidence/stage1c/nearer-my-god-to-thee-c17d/catalog.v1.json", "dataset.item.wikimedia-nearer-my-god-to-thee-phone-photo.v1"),
)
REVIEW_EVIDENCE = "evidence:opq_07f1e704e60b0fdf88670d5115b32360"
REVIEWED_BY = "actor.dataset:opq_543323ff2e140749c8f6ee4f839e1bd6"
CREATED_AT = "2026-09-01T23:10:00Z"
REVIEWED_ON = "2026-09-01"


class ExpandedSnapshotError(ValueError):
    pass


def canonical_json(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def item_from(path: Path, item_id: str) -> dict[str, Any]:
    matches = [x for x in load_json_object(path)["items"] if x["datasetItemId"] == item_id]
    if len(matches) != 1:
        raise ExpandedSnapshotError(f"expected one {item_id} in {path.relative_to(ROOT)}")
    return matches[0]


def build_catalog() -> dict[str, Any]:
    items = [item_from(path, item_id) for path, item_id in SOURCES]
    ids = [x["datasetItemId"] for x in items]
    if "dataset.item.imslp82860-chopin-op69.v1" in ids:
        raise ExpandedSnapshotError("Chopin v1 must not be selected")
    digests = [x["artifact"]["sha256"] for x in items]
    if len(digests) != len(set(digests)):
        raise ExpandedSnapshotError("duplicate exact artifact digest")
    return validate_dataset_catalog({
        "schemaVersion": "1.3.0",
        "entryDecisionId": "adr-0013-stage-1-entry-v1",
        "catalogId": "dataset.catalog.stage1c-expanded-corpus.v2",
        "descriptionCode": "stage1c-expanded-corpus-v2",
        "items": items,
    })


def build_snapshot(catalog: dict[str, Any]) -> dict[str, Any]:
    readiness = evaluate_corpus_readiness(catalog, as_of=date(2026, 9, 2))
    expected = {"state":"ready","reasonCodes":[],"counts":{"development":3,"held_out":2},"sourceFamilyCounts":{"development":3,"held_out":2}}
    if readiness != expected:
        raise ExpandedSnapshotError(f"unexpected readiness: {readiness}")
    assignments = [{
        "datasetItemId": x["datasetItemId"],
        "sourceFamilyId": x["sourceFamilyId"],
        "split": x["split"],
        "itemSha256": canonical_sha256(x),
    } for x in sorted(catalog["items"], key=lambda x: x["datasetItemId"])]
    return validate_dataset_snapshot({
        "schemaVersion":"1.2.0",
        "entryDecisionId":"adr-0013-stage-1-entry-v1",
        "snapshotId":"dataset.snapshot.stage1c-expanded.v2",
        "datasetId":catalog["catalogId"],
        "version":"2.0.0",
        "createdAt":CREATED_AT,
        "environment":"stage1_offline",
        "catalogSha256":canonical_sha256(catalog),
        "assignments":assignments,
        "heldOutFrozen":True,
        "trainingUseActivated":False,
        "revokedItemIds":[],
        "coverage":{"realItemCount":5,"syntheticItemCount":0,"gapCodes":[]},
        "review":{"status":"approved","reviewedBy":REVIEWED_BY,"reviewedOn":REVIEWED_ON,"evidenceReference":REVIEW_EVIDENCE,"noteCodes":["c17-expanded-snapshot","c17c-v2-replaces-v1","coverage-review-required"]},
    }, catalog=catalog)


def target(code: str, n: int) -> dict[str, Any]:
    return {"code":code,"observedItemCount":n,"state":"covered" if n else "missing"}


def build_report(catalog: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    by_id = {x["datasetItemId"]:x for x in catalog["items"]}
    items = [by_id[a["datasetItemId"]] for a in snapshot["assignments"]]
    splits = Counter(x["split"] for x in items)
    families = {s:len({x["sourceFamilyId"] for x in items if x["split"]==s}) for s in ("development","held_out")}
    pages = {s:sum(x["input"]["pageCount"] for x in items if x["split"]==s) for s in ("development","held_out")}
    notation = {k:0 for k in sorted(NOTATION_KINDS)}
    inputs = {k:0 for k in sorted(INPUT_MEDIA)}
    deg = {k:0 for k in sorted(DEGRADATIONS)}
    sources = {k:0 for k in sorted(SOURCE_KINDS)}
    non_none = 0
    for x in items:
        for k in x["input"]["notationKinds"]: notation[k] += 1
        inputs[x["input"]["kind"]] += 1
        if any(d != "none" for d in x["input"]["degradations"]): non_none += 1
        for d in x["input"]["degradations"]: deg[d] += 1
        sources[x["provenance"]["sourceKind"]] += 1
    targets = [target("notation.staff",notation["staff"]),target("notation.guitar_tab",notation["guitar_tab"]),target("notation.combined_staff_tab",notation["combined_staff_tab"]),target("capture.scanned_pdf",inputs["scanned_pdf"]),target("capture.phone_photo",inputs["phone_photo"]),target("degradation.non_none",non_none)]
    gaps = []
    map_gap = {"notation.guitar_tab":"coverage.missing-guitar-tab","notation.combined_staff_tab":"coverage.missing-combined-staff-tab","capture.phone_photo":"coverage.missing-phone-photo","degradation.non_none":"coverage.missing-degraded-source"}
    for t in targets:
        if t["state"] == "missing" and t["code"] in map_gap: gaps.append(map_gap[t["code"]])
    if splits["development"] < 2: gaps.append("coverage.single-item-development")
    if splits["held_out"] < 2: gaps.append("coverage.single-item-held-out")
    if len(items) <= 2: gaps.append("coverage.two-item-corpus")
    gaps = sorted(set(gaps))
    if gaps:
        raise ExpandedSnapshotError(f"expanded gaps remain: {gaps}")
    return {
        "schemaVersion":"1.0.0","reportId":"dataset.coverage-bias.stage1c-expanded.v2","snapshotId":snapshot["snapshotId"],"snapshotSha256":canonical_sha256(snapshot),"catalogSha256":canonical_sha256(catalog),"evaluatedOn":"2026-09-01","measurementBasis":"validated_catalog_snapshot_metadata",
        "counts":{"itemCount":5,"realItemCount":5,"syntheticItemCount":0,"splitItemCounts":{"development":splits["development"],"held_out":splits["held_out"]},"sourceFamilyCounts":{"development":families["development"],"held_out":families["held_out"],"total":len({x["sourceFamilyId"] for x in items})},"pageCounts":{"development":pages["development"],"held_out":pages["held_out"],"total":sum(pages.values())},"notationItemCounts":notation,"inputKindItemCounts":inputs,"degradationItemCounts":deg,"sourceKindItemCounts":sources},
        "coverageTargets":targets,"gapCodes":[],
        "biasFindings":[
            {"code":"capture_condition_concentration","state":"controlled","evidenceCode":"multiple-capture-kinds"},
            {"code":"degradation_coverage_gap","state":"controlled","evidenceCode":"non-none-degradation-present"},
            {"code":"held_out_coverage_limit","state":"controlled","evidenceCode":"two-held-out-source-families"},
            {"code":"notation_layout_concentration","state":"controlled","evidenceCode":"staff-tab-and-combined-layouts-present"},
            {"code":"source_family_leakage_risk","state":"controlled","evidenceCode":"distinct-source-families-and-digests-across-splits"},
            {"code":"source_selection_concentration","state":"observed","evidenceCode":"public-domain-majority-with-one-licensed-item"}],
        "sufficiency":{"state":"review_required","reasonCodes":[],"requiresCorpusExpansion":False,"stage1ExitSupported":False,"stage2EntrySupported":False},
        "assertions":{"heldOutFrozen":True,"trainingUseActivated":False,"representativenessEstablished":False,"absenceOfBiasEstablished":False,"restorationEffectivenessEstablished":False,"omrImprovementEstablished":False},
    }


def build_all():
    c = build_catalog(); s = build_snapshot(c); r = build_report(c,s); return c,s,r

def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def check(path: Path, expected: dict[str, Any]) -> None:
    if not path.is_file() or canonical_json(load_json_object(path)) != canonical_json(expected):
        raise ExpandedSnapshotError(f"committed evidence drifted: {path.relative_to(ROOT)}")

def main() -> None:
    p=argparse.ArgumentParser(); g=p.add_mutually_exclusive_group(required=True); g.add_argument("--write",action="store_true"); g.add_argument("--check",action="store_true"); g.add_argument("--summary",action="store_true"); a=p.parse_args()
    try:
        c,s,r=build_all()
        if a.write:
            write(CATALOG_PATH,c); write(SNAPSHOT_PATH,s); write(REPORT_PATH,r)
        elif a.check:
            check(CATALOG_PATH,c); check(SNAPSHOT_PATH,s); check(REPORT_PATH,r)
        print(f"catalogSha256={canonical_sha256(c)}"); print(f"snapshotSha256={canonical_sha256(s)}"); print(f"coverageReportSha256={canonical_sha256(r)}"); print("gapCodes="); print("coverageState=review_required"); print(f"splitCounts={r['counts']['splitItemCounts']}"); print(f"sourceFamilyCounts={r['counts']['sourceFamilyCounts']}")
    except (OSError,ValueError,KeyError) as e:
        print(f"ERROR: expanded Stage 1 snapshot build failed: {e}",file=sys.stderr); raise SystemExit(1) from e

if __name__ == "__main__": main()
