"""Types and configuration for music-score and guitar-TAB safety validation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Literal, Mapping

SCHEMA_VERSION = "1.0.0"
VALIDATOR_VERSION = "0.3.0"


class MusicSafetyValidationError(ValueError):
    """A safe validation failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "validation_failed",
            "verdict": "review_required",
            "automaticApproval": False,
            "error": {"code": self.code, "message": self.message, "details": self.details},
            "fallback": {"originalAvailable": True, "recommendedAction": "return_original"},
        }


@dataclass(frozen=True)
class MusicSafetyConfig:
    """Auditable thresholds for conservative structural comparison."""

    expected_staff_lines: int = 5
    expected_tab_lines: int = 6
    horizontal_line_min_fraction: float = 0.45
    horizontal_kernel_fraction: float = 0.12
    system_gap_multiplier: float = 2.4
    registration_max_translation_fraction: float = 0.04
    registration_min_response: float = 0.08
    dark_threshold_ceiling: int = 190
    line_break_review_fraction: float = 0.01
    line_break_reject_fraction: float = 0.05
    symbol_loss_review_fraction: float = 0.012
    symbol_loss_reject_fraction: float = 0.04
    symbol_invention_review_fraction: float = 0.01
    symbol_invention_reject_fraction: float = 0.035
    component_loss_review_fraction: float = 0.08
    component_loss_reject_fraction: float = 0.25
    component_invention_review_fraction: float = 0.08
    component_invention_reject_fraction: float = 0.25
    component_shift_review_pixels: float = 3.0
    component_shift_reject_pixels: float = 8.0
    max_component_area: int = 2500
    min_component_area: int = 2
    region_grid_rows: int = 6
    region_grid_columns: int = 6

    def __post_init__(self) -> None:
        if self.expected_staff_lines < 1 or self.expected_tab_lines < 1:
            self._invalid("expected line counts")
        for name in (
            "horizontal_line_min_fraction",
            "horizontal_kernel_fraction",
            "registration_max_translation_fraction",
            "registration_min_response",
            "line_break_review_fraction",
            "line_break_reject_fraction",
            "symbol_loss_review_fraction",
            "symbol_loss_reject_fraction",
            "symbol_invention_review_fraction",
            "symbol_invention_reject_fraction",
            "component_loss_review_fraction",
            "component_loss_reject_fraction",
            "component_invention_review_fraction",
            "component_invention_reject_fraction",
        ):
            value = float(getattr(self, name))
            if not 0 <= value <= 1:
                self._invalid(name)
        if self.line_break_review_fraction >= self.line_break_reject_fraction:
            self._invalid("line break thresholds")
        if self.symbol_loss_review_fraction >= self.symbol_loss_reject_fraction:
            self._invalid("symbol loss thresholds")
        if self.symbol_invention_review_fraction >= self.symbol_invention_reject_fraction:
            self._invalid("symbol invention thresholds")
        if self.component_loss_review_fraction >= self.component_loss_reject_fraction:
            self._invalid("component loss thresholds")
        if self.component_invention_review_fraction >= self.component_invention_reject_fraction:
            self._invalid("component invention thresholds")
        if not 0 <= self.dark_threshold_ceiling <= 255:
            self._invalid("dark_threshold_ceiling")
        if self.min_component_area < 1 or self.max_component_area < self.min_component_area:
            self._invalid("component area limits")
        if not 1 <= self.region_grid_rows <= 20 or not 1 <= self.region_grid_columns <= 20:
            self._invalid("region grid")

    @staticmethod
    def _invalid(name: str) -> None:
        raise MusicSafetyValidationError("invalid_validator_configuration", f"Invalid {name}.")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "MusicSafetyConfig":
        if value is None:
            return cls()
        unknown = sorted(set(value) - set(cls.__dataclass_fields__))
        if unknown:
            raise MusicSafetyValidationError(
                "invalid_validator_configuration",
                "Unknown validator configuration fields.",
                details={"fields": unknown},
            )
        return cls(**dict(value))

    def digest(self) -> str:
        raw = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


TeacherDecision = Literal["approved", "rejected", "reprocess"]
