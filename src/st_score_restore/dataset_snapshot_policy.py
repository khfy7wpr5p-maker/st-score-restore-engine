"""Fail-closed purpose authorization for Stage 1A dataset snapshots."""

from __future__ import annotations

from typing import Any

from .dataset_manifest import (
    DatasetManifestError,
    validate_dataset_snapshot,
)

_SPLIT_PURPOSES = {
    "development": frozenset(
        {
            "fixture_validation",
            "quality_evaluation",
            "pdf_pipeline_evaluation",
        }
    ),
    "calibration": frozenset(
        {
            "quality_calibration",
            "safety_calibration",
        }
    ),
    "held_out": frozenset({"held_out_evaluation"}),
    "training_reserved": frozenset({"model_training"}),
}


def validate_authorized_dataset_snapshot(
    data: Any,
    *,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Validate snapshot integrity and require a split-relevant grant.

    A split assignment alone is not authorization to include or use an item.
    Every snapshot assignment must have at least one currently granted purpose
    that is relevant to that split. Publication and demonstration grants do not
    authorize evaluation, calibration, held-out, or training inclusion.
    """

    snapshot = validate_dataset_snapshot(data, catalog=catalog)
    item_index = {
        item["datasetItemId"]: item for item in catalog["items"]
    }

    for index, assignment in enumerate(snapshot["assignments"]):
        item_id = assignment["datasetItemId"]
        split = assignment["split"]
        item = item_index[item_id]
        granted = {
            purpose
            for purpose, permission in item["permissions"].items()
            if permission["status"] == "granted"
        }
        relevant = _SPLIT_PURPOSES[split]
        if not granted.intersection(relevant):
            expected = ", ".join(sorted(relevant))
            raise DatasetManifestError(
                "snapshot assignment is not authorized for its split: "
                f"assignments[{index}] item={item_id} split={split}; "
                f"requires at least one granted purpose from [{expected}]"
            )

    return snapshot
