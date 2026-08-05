"""Core contracts for ST Score Restore Engine.

Input inspection stays importable independently of the OpenCV image backend.
Candidate generation lives in ``st_score_restore.safe_restoration`` and
music/TAB validation lives in ``st_score_restore.music_safety_validator``.
Production restoration and automatic teacher approval remain disabled.
"""

from .input_inspection import (
    DEFAULT_MAX_BYTES,
    INSPECTOR_VERSION,
    InputInspectionError,
    inspect_bytes,
    inspect_path,
)

__all__ = [
    "DEFAULT_MAX_BYTES",
    "INSPECTOR_VERSION",
    "InputInspectionError",
    "inspect_bytes",
    "inspect_path",
]

__version__ = "0.3.0"
