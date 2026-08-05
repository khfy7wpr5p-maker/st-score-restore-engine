"""Core contracts for ST Score Restore Engine.

Input inspection stays importable independently of the optional image backend.
The OpenCV candidate engine lives in ``st_score_restore.safe_restoration``.
Production restoration and teacher approval remain disabled.
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

__version__ = "0.2.0"
