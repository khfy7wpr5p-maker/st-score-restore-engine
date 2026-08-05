#!/usr/bin/env python3
"""Validate the repository contract using only the Python standard library."""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.fixture_manifest import FixtureCatalogError, load_catalog  # noqa: E402
from st_score_restore.input_inspection import (  # noqa: E402
    INSPECTOR_VERSION,
    SCHEMA_VERSION as INPUT_SCHEMA_VERSION,
)

REQUIRED_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    ".python-version",
    ".gitignore",
    ".editorconfig",
    "src/st_score_restore/__init__.py",
    "src/st_score_restore/fixture_manifest.py",
    "src/st_score_restore/input_inspection.py",
    "tests/README.md",
    "tests/test_fixture_manifest.py",
    "tests/test_input_inspection.py",
    "fixtures/README.md",
    "fixtures/catalog.v1.json",
    "schemas/fixture-manifest.schema.json",
    "schemas/artifact-manifest.schema.json",
    "schemas/input-analysis.schema.json",
    "models/README.md",
    "api/README.md",
    "examples/README.md",
    "LICENSES/README.md",
    "docs/technical-specification.md",
    "docs/roadmap.md",
    "docs/development-environment.md",
    "docs/dependency-and-license-policy.md",
    "docs/fixture-governance.md",
    "docs/input-inspection-contract.md",
    "docs/adr/0001-independent-safety-first-engine.md",
    "docs/adr/0002-python-runtime-and-repository-layout.md",
    "docs/adr/0003-fixture-consent-and-usage-governance.md",
    "docs/adr/0004-immutable-input-inspection.md",
    "tools/validate_fixture_catalog.py",
    "tools/inspect_input.py",
    ".github/workflows/repository-validation.yml",
)

FORBIDDEN_TRACKED_SUFFIXES = {
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".safetensors",
}

ALLOWED_FIXTURE_FILES = {
    Path("fixtures/README.md"),
    Path("fixtures/catalog.v1.json"),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required files: " + ", ".join(missing))


def validate_pyproject() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)

    project = data.get("project", {})
    if project.get("name") != "st-score-restore-engine":
        fail("unexpected project.name")
    if project.get("requires-python") != ">=3.11,<3.13":
        fail("unexpected project.requires-python")
    if project.get("dependencies") != []:
        fail("the current baseline must not declare third-party runtime dependencies")

    policy = data.get("tool", {}).get("st_score_restore", {})
    if policy.get("primary_python") != "3.12":
        fail("unexpected primary Python runtime")
    if policy.get("production_restoration_enabled") is not False:
        fail("production restoration must remain disabled")


def load_json(relative_path: Path) -> dict:
    with (ROOT / relative_path).open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as error:
            fail(f"invalid JSON in {relative_path}: {error}")
    if not isinstance(data, dict):
        fail(f"JSON root must be an object in {relative_path}")
    return data


def validate_json_documents() -> None:
    fixture_schema = load_json(Path("schemas/fixture-manifest.schema.json"))
    load_json(Path("fixtures/catalog.v1.json"))
    artifact_schema = load_json(Path("schemas/artifact-manifest.schema.json"))
    analysis_schema = load_json(Path("schemas/input-analysis.schema.json"))

    if fixture_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("fixture manifest must use JSON Schema Draft 2020-12")
    if artifact_schema.get("properties", {}).get("schemaVersion", {}).get("const") != INPUT_SCHEMA_VERSION:
        fail("artifact manifest schema version does not match the inspector")
    if analysis_schema.get("properties", {}).get("schemaVersion", {}).get("const") != INPUT_SCHEMA_VERSION:
        fail("input analysis schema version does not match the inspector")
    inspector_pattern = (
        analysis_schema.get("properties", {})
        .get("inspectorVersion", {})
        .get("pattern")
    )
    if inspector_pattern != r"^\d+\.\d+\.\d+$":
        fail("input analysis inspectorVersion pattern is unexpected")
    if not INSPECTOR_VERSION:
        fail("input inspector version must not be empty")


def validate_fixture_contract() -> None:
    try:
        catalog = load_catalog(ROOT / "fixtures" / "catalog.v1.json")
    except (OSError, ValueError, FixtureCatalogError) as error:
        fail(f"fixture catalog validation failed: {error}")

    available = [
        fixture["fixtureId"]
        for fixture in catalog["fixtures"]
        if fixture["artifact"]["state"] == "available"
    ]
    if available:
        fail(
            "Issue #3 establishes metadata rules only; artifact bytes require a later "
            "approved change: "
            + ", ".join(available)
        )


def validate_sensitive_artifacts() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES:
            fail(f"unapproved model weight found: {path.relative_to(ROOT)}")
        if path.stat().st_size > 1_000_000:
            fail(f"unexpected file larger than 1 MB: {path.relative_to(ROOT)}")

    unexpected_fixtures = [
        path.relative_to(ROOT)
        for path in (ROOT / "fixtures").rglob("*")
        if path.is_file() and path.relative_to(ROOT) not in ALLOWED_FIXTURE_FILES
    ]
    if unexpected_fixtures:
        fail(
            "unapproved fixture files found; Issue #3 permits metadata only: "
            + ", ".join(map(str, unexpected_fixtures))
        )


def main() -> None:
    validate_required_files()
    validate_pyproject()
    validate_json_documents()
    validate_fixture_contract()
    validate_sensitive_artifacts()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
