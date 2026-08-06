#!/usr/bin/env python3
"""Validate exact runtime and offline validation dependency locks."""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pins(lines: list[str], source: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_RE.fullmatch(line)
        if not match:
            fail(f"{source} contains a non-exact requirement: {line}")
        name, version = match.groups()
        key = normalize(name)
        if key in pins:
            fail(f"duplicate dependency in {source}: {name}")
        pins[key] = version
    return pins


def read_lock(name: str) -> dict[str, str]:
    return parse_pins(
        (ROOT / name).read_text(encoding="utf-8").splitlines(),
        name,
    )


def main() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    runtime_intent = parse_pins(
        list(project.get("dependencies", [])), "pyproject.toml runtime dependencies"
    )
    runtime_lock = read_lock("requirements.lock")
    if runtime_intent != runtime_lock:
        fail(
            "runtime dependency intent and lock differ: "
            f"intent={runtime_intent}, lock={runtime_lock}"
        )
    expected_runtime = {
        "numpy": "2.3.5",
        "opencv-python-headless": "4.13.0.92",
    }
    if runtime_lock != expected_runtime:
        fail(f"unexpected approved runtime dependency graph: {runtime_lock}")

    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict) or set(optional) != {"validation"}:
        fail("pyproject.toml must define only the validation optional dependency group")
    validation_intent = parse_pins(
        list(optional["validation"]),
        "pyproject.toml validation optional dependencies",
    )
    validation_lock = read_lock("requirements.validation.lock")
    if validation_intent != validation_lock:
        fail(
            "validation dependency intent and lock differ: "
            f"intent={validation_intent}, lock={validation_lock}"
        )
    expected_validation = {
        "attrs": "26.1.0",
        "jsonschema": "4.26.0",
        "jsonschema-specifications": "2025.9.1",
        "referencing": "0.37.0",
        "rpds-py": "2026.5.1",
        "typing-extensions": "4.15.0",
    }
    if validation_lock != expected_validation:
        fail(f"unexpected approved validation dependency graph: {validation_lock}")

    if set(runtime_lock) & set(validation_lock):
        fail("runtime and validation dependency locks must not overlap")

    print("Dependency lock validation passed.")


if __name__ == "__main__":
    main()
