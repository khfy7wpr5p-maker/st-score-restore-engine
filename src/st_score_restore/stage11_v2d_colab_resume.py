"""Compatibility entrypoint for Stage 11 V2d Colab recovery.

All recovery logic lives in :mod:`stage11_v2d_colab_runner`; this wrapper keeps
older notebook/import entrypoints working without maintaining a second cache
implementation.
"""
from __future__ import annotations

from pathlib import Path

from .stage11_v2d_colab_runner import run_colab_benchmark


def run_cached_detector_benchmark() -> Path:
    """Run the robust crash-safe benchmark; valid Drive cache is reused automatically."""
    return run_colab_benchmark()


def main() -> int:
    run_colab_benchmark()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
