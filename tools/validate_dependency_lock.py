#!/usr/bin/env python3
"""Validate that the exact runtime lock matches pyproject dependency intent."""
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


def main() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    intent = parse_pins(list(project.get("dependencies", [])), "pyproject.toml")
    lock = parse_pins((ROOT / "requirements.lock").read_text(encoding="utf-8").splitlines(), "requirements.lock")
    if intent != lock:
        fail(f"dependency intent and lock differ: intent={intent}, lock={lock}")
    expected = {"numpy": "2.3.5", "opencv-python-headless": "4.13.0.92"}
    if lock != expected:
        fail(f"unexpected approved dependency graph: {lock}")
    print("Dependency lock validation passed.")


if __name__ == "__main__":
    main()
