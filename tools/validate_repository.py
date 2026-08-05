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

REQUIRED_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    ".python-version",
    ".gitignore",
    ".editorconfig",
    "src/st_score_restore/__init__.py",
    "src/st_score_restore/fixture_manifest.py",
    "tests/README.md",
    "tests/test_fixture_manifest.py",
    "fixtures/README.md",
    "fixtures/catalog.v1.json",
    "schemas/fixture-manifest.schema.json",
    "models/README.md",
    "api/README.md",
    "examples/README.md",
    "LICENSES/README.md",
    "docs/technical-specification.md",
    "docs/roadmap.md",
    "docs/development-environment.md",
    "docs/dependency-and-license-policy.md",
    "docs/fixture-governance.md",
    "docs/adr/0001-independent-safety-first-engine.md",
    "docs/adr/0002-python-runtime-and-repository-layout.md",
    "docs/adr/0003-fixture-consent-and-usage-governance.md",
    "tools/validate_fixture_catalog.py",
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


def validate_json_documents() -> None:
    for relative_path in (
        Path("schemas/fixture-manifest.schema.json"),
        Path("fixtures/catalog.v1.json"),
    ):
        with (ROOT / relative_path).open("r", encoding="utf-8") as handle:
            try:
                json.load(handle)
            except json.JSONDecodeError as error:
                fail(f"invalid JSON in {relative_path}: {error}")


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
