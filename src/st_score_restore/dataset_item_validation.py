"""Fail-closed per-item Stage 1A dataset metadata validation."""

from __future__ import annotations

from typing import Any

from .dataset_item_core import validate_item_core
from .dataset_item_final import finalize_item
from .dataset_item_policy import validate_item_policy


def _item(raw: Any, index: int) -> dict[str, Any]:
    value, context = validate_item_core(raw, index)
    validate_item_policy(value, context)
    return finalize_item(value, context)
