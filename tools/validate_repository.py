#!/usr/bin/env python3
"""Validate the Milestone M0 repository contract using only the standard library."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "pyproject.toml",
    ".python-version",
    ".gitignore",
    ".editorconfig",
    "src/st_score_restore/__init__.py",
    "tests/README.md",
    "fixtures/README.md",
    "models/README.md",
    "api/README.md",
    "examples/README.md",
    "LICENSES/README.md",
    "docs/technical-specification.md",
    "docs/roadmap.md",
    "docs/development-environment.md",
    "docs/dependency-and-license-policy.md",
    "docs/adr/0001-independent-safety-first-engine.md",
    "docs/adr/0002-python-runtime-and-repository-layout.md",
    ".github/workflows/repository-validation.yml",
)

FORBIDDEN_TRACKED_SUFFIXES = {
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".safetensors",
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
        fail("Milestone M0 must not declare third-party runtime dependencies")

    policy = data.get("tool", {}).get("st_score_restore", {})
    if policy.get("primary_python") != "3.12":
        fail("unexpected primary Python runtime")
    if policy.get("production_restoration_enabled") is not False:
        fail("production restoration must remain disabled in Milestone M0")


def validate_sensitive_artifacts() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES:
            fail(f"unapproved model weight found: {path.relative_to(ROOT)}")
        if path.stat().st_size > 1_000_000:
            fail(f"unexpected file larger than 1 MB: {path.relative_to(ROOT)}")

    allowed_fixture_files = {ROOT / "fixtures" / "README.md"}
    unexpected_fixtures = [
        path.relative_to(ROOT)
        for path in (ROOT / "fixtures").rglob("*")
        if path.is_file() and path not in allowed_fixture_files
    ]
    if unexpected_fixtures:
        fail(
            "fixture bytes are not allowed before Issue #3 approval: "
            + ", ".join(map(str, unexpected_fixtures))
        )


def main() -> None:
    validate_required_files()
    validate_pyproject()
    validate_sensitive_artifacts()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
