"""Compatibility wrapper for the fail-closed Stage 1A snapshot boundary."""

from __future__ import annotations

from typing import Any

from .dataset_manifest import validate_dataset_snapshot


def validate_authorized_dataset_snapshot(
    data: Any,
    *,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Validate a snapshot through the only public authorized boundary."""
    return validate_dataset_snapshot(data, catalog=catalog)


__all__ = ["validate_authorized_dataset_snapshot"]
