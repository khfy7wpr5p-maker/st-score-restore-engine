#!/usr/bin/env python3
"""Validate exact runtime and hash-locked offline validation dependencies."""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s;]+)$")
HASH_RE = re.compile(r"^--hash=sha256:([0-9a-f]{64})$")

EXPECTED_RUNTIME = {
    "numpy": "2.3.5",
    "opencv-python-headless": "4.13.0.92",
    "pypdfium2": "5.13.0",
}
EXPECTED_VALIDATION = {
    "attrs": "26.1.0",
    "jsonschema": "4.26.0",
    "jsonschema-specifications": "2025.9.1",
    "referencing": "0.37.0",
    "rpds-py": "2026.5.1",
    "typing-extensions": "4.15.0",
}
EXPECTED_VALIDATION_HASHES = {
    "attrs": {
        "c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309",
    },
    "jsonschema": {
        "d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce",
    },
    "jsonschema-specifications": {
        "98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe",
    },
    "referencing": {
        "381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231",
    },
    "rpds-py": {
        "613fc4ee9eaef26dc5840666214dd6fbcebcf32f46e76f4abc473059f4e13dda",
        "b6825cc329b290e93c5f6a9be2393118a763f6ccf6abd83704e0c102ca583644",
    },
    "typing-extensions": {
        "f0fa19c6845758ab08074a0cfa8b7aecb71c999ca73d62883bc25cc018c4e548",
    },
}


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


def parse_hashed_pins(
    lines: list[str], source: str
) -> tuple[dict[str, str], dict[str, set[str]]]:
    pins: dict[str, str] = {}
    hashes: dict[str, set[str]] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        match = PIN_RE.fullmatch(parts[0])
        if not match:
            fail(f"{source} contains a non-exact requirement: {parts[0]}")
        name, version = match.groups()
        key = normalize(name)
        if key in pins:
            fail(f"duplicate dependency in {source}: {name}")
        if len(parts) == 1:
            fail(f"{source} dependency has no wheel hash: {name}")
        package_hashes: set[str] = set()
        for token in parts[1:]:
            hash_match = HASH_RE.fullmatch(token)
            if not hash_match:
                fail(f"{source} contains invalid hash token for {name}: {token}")
            digest = hash_match.group(1)
            if digest in package_hashes:
                fail(f"{source} repeats a wheel hash for {name}")
            package_hashes.add(digest)
        pins[key] = version
        hashes[key] = package_hashes
    return pins, hashes


def read_lock(name: str) -> dict[str, str]:
    return parse_pins((ROOT / name).read_text(encoding="utf-8").splitlines(), name)


def read_hashed_lock(name: str) -> tuple[dict[str, str], dict[str, set[str]]]:
    return parse_hashed_pins(
        (ROOT / name).read_text(encoding="utf-8").splitlines(), name
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
    if runtime_lock != EXPECTED_RUNTIME:
        fail(f"unexpected approved runtime dependency graph: {runtime_lock}")

    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict) or set(optional) != {"validation"}:
        fail("pyproject.toml must define only the validation optional dependency group")
    validation_intent = parse_pins(
        list(optional["validation"]),
        "pyproject.toml validation optional dependencies",
    )
    validation_lock, validation_hashes = read_hashed_lock(
        "requirements.validation.lock"
    )
    if validation_intent != validation_lock:
        fail(
            "validation dependency intent and lock differ: "
            f"intent={validation_intent}, lock={validation_lock}"
        )
    if validation_lock != EXPECTED_VALIDATION:
        fail(f"unexpected approved validation dependency graph: {validation_lock}")
    if validation_hashes != EXPECTED_VALIDATION_HASHES:
        fail(
            "validation wheel hash set differs from the approved Python 3.11/3.12 "
            f"Ubuntu x86_64 graph: {validation_hashes}"
        )
    if set(runtime_lock) & set(validation_lock):
        fail("runtime and validation dependency locks must not overlap")

    print("Dependency lock and validation wheel hash verification passed.")


if __name__ == "__main__":
    main()
