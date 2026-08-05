#!/usr/bin/env python3
"""Validate the approved fixture metadata catalog without external packages."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.fixture_manifest import FixtureCatalogError, load_catalog  # noqa: E402


def main() -> None:
    catalog_path = ROOT / "fixtures" / "catalog.v1.json"
    try:
        catalog = load_catalog(catalog_path)
    except (OSError, ValueError, FixtureCatalogError) as error:
        print(f"ERROR: fixture catalog validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(
        "Fixture catalog validation passed: "
        f"{len(catalog['fixtures'])} metadata-only fixture plans."
    )


if __name__ == "__main__":
    main()
