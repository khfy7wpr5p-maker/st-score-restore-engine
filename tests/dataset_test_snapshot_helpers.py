from __future__ import annotations

from st_score_restore.dataset_manifest import canonical_sha256


def catalog(items: list[dict]) -> dict:
    return {
        "schemaVersion": "1.1.0",
        "entryDecisionId": "adr-0013-stage-1-entry-v1",
        "catalogId": "dataset.catalog.stage1a.v1",
        "description": "Stage 1A metadata contract test.",
        "items": items,
    }


def snapshot_for(source_catalog: dict, sources: list[dict], *, created_at: str = "2026-08-06T00:00:00Z") -> dict:
    ordered = sorted(sources, key=lambda source: source["datasetItemId"])
    real_count = sum(source["provenance"]["sourceKind"] != "synthetic" for source in ordered)
    return {
        "schemaVersion": "1.1.0",
        "entryDecisionId": "adr-0013-stage-1-entry-v1",
        "snapshotId": "dataset.snapshot.stage1a.v1",
        "datasetId": source_catalog["catalogId"],
        "version": "1.0.0",
        "createdAt": created_at,
        "environment": "stage1_offline",
        "catalogSha256": canonical_sha256(source_catalog),
        "assignments": [{
            "datasetItemId": source["datasetItemId"],
            "sourceFamilyId": source["sourceFamilyId"],
            "split": source["split"],
            "itemSha256": canonical_sha256(source),
        } for source in ordered],
        "heldOutFrozen": any(source["split"] == "held_out" for source in ordered),
        "trainingUseActivated": False,
        "revokedItemIds": sorted(source["datasetItemId"] for source in source_catalog["items"] if source["artifact"]["state"] == "revoked"),
        "coverage": {"realItemCount": real_count, "syntheticItemCount": len(ordered) - real_count, "gapCodes": []},
        "review": {
            "status": "approved",
            "reviewedBy": "actor.dataset:snapshot-reviewer-001",
            "reviewedOn": "2026-08-06",
            "evidenceReference": "evidence:snapshot-review-001",
            "noteCodes": ["snapshot-approved"],
        },
    }
