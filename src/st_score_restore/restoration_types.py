"""Shared types for the deterministic restoration candidate engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any, Literal, Mapping

SCHEMA_VERSION = "1.0.0"
ENGINE_VERSION = "0.2.0"

_BOOLEAN_CONFIG_FIELDS = (
    "orientation_enabled",
    "deskew_enabled",
    "perspective_enabled",
    "crop_enabled",
    "illumination_enabled",
    "denoise_enabled",
    "contrast_enabled",
)

_NUMBER_CONFIG_LIMITS = {
    "max_deskew_degrees": (0, 15, True),
    "min_deskew_degrees": (0, 15, True),
    "deskew_min_confidence": (0, 1, True),
    "perspective_min_confidence": (0, 1, True),
    "min_page_area_ratio": (0, 1, True),
    "max_page_area_ratio": (0, 1, True),
    "illumination_kernel_fraction": (0, 0.25, False),
    "illumination_strength": (0, 1, True),
    "clahe_clip_limit": (0, 8, False),
    "max_protected_fraction": (0, 1, True),
}

_INTEGER_CONFIG_LIMITS = {
    "clahe_grid_size": (2, 32),
    "protected_dark_threshold": (0, 255),
    "jpeg_quality": (80, 100),
    "output_dpi": (72, 1200),
    "max_decode_pixels": (1, 200_000_000),
}

_INTEGER_CONFIG_ENUMS = {
    "denoise_kernel": {1, 3, 5},
    "protected_dilation": {0, 1, 2},
}


class RestorationError(ValueError):
    """A safe restoration rejection with a stable machine-readable code."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "rejected",
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


@dataclass(frozen=True)
class RestorationConfig:
    """Fully explicit, deterministic restoration configuration."""

    orientation_enabled: bool = True
    deskew_enabled: bool = True
    perspective_enabled: bool = False
    crop_enabled: bool = False
    illumination_enabled: bool = True
    denoise_enabled: bool = True
    contrast_enabled: bool = True
    binarization_profile: Literal["none", "otsu", "adaptive"] = "none"
    max_deskew_degrees: float = 5.0
    min_deskew_degrees: float = 0.15
    deskew_min_confidence: float = 0.65
    perspective_min_confidence: float = 0.90
    min_page_area_ratio: float = 0.55
    max_page_area_ratio: float = 0.995
    illumination_kernel_fraction: float = 0.035
    illumination_strength: float = 0.35
    denoise_kernel: int = 3
    clahe_clip_limit: float = 1.5
    clahe_grid_size: int = 8
    protected_dark_threshold: int = 190
    protected_dilation: int = 1
    max_protected_fraction: float = 0.55
    jpeg_quality: int = 95
    output_dpi: int = 300
    max_decode_pixels: int = 80_000_000

    def __post_init__(self) -> None:
        for name in _BOOLEAN_CONFIG_FIELDS:
            if not isinstance(getattr(self, name), bool):
                self._invalid(name)

        if (
            not isinstance(self.binarization_profile, str)
            or self.binarization_profile not in {"none", "otsu", "adaptive"}
        ):
            self._invalid("binarization_profile")

        for name, limits in _NUMBER_CONFIG_LIMITS.items():
            minimum, maximum, minimum_is_inclusive = limits
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                self._invalid(name)
            if isinstance(value, float) and not math.isfinite(value):
                self._invalid(name)
            minimum_is_valid = (
                value >= minimum if minimum_is_inclusive else value > minimum
            )
            if not minimum_is_valid or value > maximum:
                self._invalid(name)

        for name, (minimum, maximum) in _INTEGER_CONFIG_LIMITS.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                self._invalid(name)
            if not minimum <= value <= maximum:
                self._invalid(name)

        for name, allowed in _INTEGER_CONFIG_ENUMS.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value not in allowed:
                self._invalid(name)

        if self.min_deskew_degrees > self.max_deskew_degrees:
            self._invalid("deskew degree limits")
        if self.min_page_area_ratio >= self.max_page_area_ratio:
            self._invalid("page area ratios")

    @staticmethod
    def _invalid(name: str) -> None:
        raise RestorationError("invalid_configuration", f"Invalid {name}.")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "RestorationConfig":
        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise RestorationError(
                "invalid_configuration",
                "Configuration must be an object.",
            )
        known_fields = set(cls.__dataclass_fields__)
        unknown = sorted(
            (
                key if isinstance(key, str) else repr(key)
                for key in value
                if key not in known_fields
            )
        )
        if unknown:
            raise RestorationError(
                "invalid_configuration",
                "Unknown configuration fields.",
                details={"fields": unknown},
            )
        return cls(**dict(value))

    def digest(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class RestorationCandidate:
    """Candidate bytes plus an audit manifest; rejection returns the exact source."""

    source_bytes: bytes = field(repr=False)
    output_bytes: bytes = field(repr=False)
    manifest: dict[str, Any]

    def reject(self) -> bytes:
        return self.source_bytes
