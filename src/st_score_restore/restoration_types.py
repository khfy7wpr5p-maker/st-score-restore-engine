"""Shared types for the deterministic restoration candidate engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any, Literal, Mapping

SCHEMA_VERSION = "1.0.0"
ENGINE_VERSION = "0.2.0"


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
        if self.binarization_profile not in {"none", "otsu", "adaptive"}:
            self._invalid("binarization_profile")
        if not 0 <= self.min_deskew_degrees <= self.max_deskew_degrees <= 15:
            self._invalid("deskew degree limits")
        for name in (
            "deskew_min_confidence",
            "perspective_min_confidence",
            "min_page_area_ratio",
            "max_page_area_ratio",
            "illumination_strength",
            "max_protected_fraction",
        ):
            if not 0 <= float(getattr(self, name)) <= 1:
                self._invalid(name)
        if self.min_page_area_ratio >= self.max_page_area_ratio:
            self._invalid("page area ratios")
        if self.denoise_kernel not in {1, 3, 5}:
            self._invalid("denoise_kernel")
        if self.protected_dilation not in {0, 1, 2}:
            self._invalid("protected_dilation")
        if not 80 <= self.jpeg_quality <= 100 or not 72 <= self.output_dpi <= 1200:
            self._invalid("output settings")
        if not 1 <= self.max_decode_pixels <= 200_000_000:
            self._invalid("max_decode_pixels")

    @staticmethod
    def _invalid(name: str) -> None:
        raise RestorationError("invalid_configuration", f"Invalid {name}.")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "RestorationConfig":
        if value is None:
            return cls()
        unknown = sorted(set(value) - set(cls.__dataclass_fields__))
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
