"""Core contracts for ST Score Restore Engine.

The package currently provides fixture governance and read-only input inspection.
No restoration behavior is enabled.
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

__version__ = "0.1.0"
