"""Core contracts for ST Score Restore Engine.

Input inspection stays importable independently of the OpenCV image backend.
Candidate generation lives in ``st_score_restore.safe_restoration``;
music/TAB validation lives in ``st_score_restore.music_safety_validator``;
the non-production job API lives behind ``st_score_restore.job_service`` and
``st_score_restore.http_api``; and optional restart-persistent local storage
lives in ``st_score_restore.durable_job_store``.

Production deployment, automatic teacher approval, and encrypted cloud
storage remain disabled.
"""

from .input_inspection import (
    DEFAULT_MAX_BYTES,
    INSPECTOR_VERSION,
    InputInspectionError,
    inspect_bytes,
    inspect_path,
)
from .job_api_types import API_VERSION

__all__ = [
    "API_VERSION",
    "DEFAULT_MAX_BYTES",
    "INSPECTOR_VERSION",
    "InputInspectionError",
    "inspect_bytes",
    "inspect_path",
]

__version__ = API_VERSION
