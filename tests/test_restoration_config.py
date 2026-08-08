from __future__ import annotations

import json
import unittest
from pathlib import Path

from st_score_restore.restoration_types import RestorationConfig, RestorationError


BOOLEAN_FIELDS = {
    "orientation_enabled",
    "deskew_enabled",
    "perspective_enabled",
    "crop_enabled",
    "illumination_enabled",
    "denoise_enabled",
    "contrast_enabled",
}

NUMBER_RANGES = {
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

INTEGER_RANGES = {
    "clahe_grid_size": (2, 32),
    "protected_dark_threshold": (0, 255),
    "jpeg_quality": (80, 100),
    "output_dpi": (72, 1200),
    "max_decode_pixels": (1, 200_000_000),
}

INTEGER_ENUMS = {
    "denoise_kernel": (1, 3, 5),
    "protected_dilation": (0, 1, 2),
}


class RestorationConfigTests(unittest.TestCase):
    def assert_invalid(self, **values: object) -> None:
        with self.assertRaises(RestorationError) as caught:
            RestorationConfig(**values)
        self.assertEqual("invalid_configuration", caught.exception.code)

    def test_validation_matrix_matches_every_schema_property(self) -> None:
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "schemas"
            / "restoration-config.schema.json"
        )
        properties = json.loads(schema_path.read_text(encoding="utf-8"))["properties"]
        covered = (
            BOOLEAN_FIELDS
            | set(NUMBER_RANGES)
            | set(INTEGER_RANGES)
            | set(INTEGER_ENUMS)
            | {"binarization_profile"}
        )
        self.assertEqual(set(properties), covered)
        for field in BOOLEAN_FIELDS:
            self.assertEqual({"type": "boolean"}, properties[field])
        for field, (minimum, maximum, minimum_is_inclusive) in NUMBER_RANGES.items():
            expected = {"type": "number", "maximum": maximum}
            expected["minimum" if minimum_is_inclusive else "exclusiveMinimum"] = minimum
            self.assertEqual(expected, properties[field])
        for field, (minimum, maximum) in INTEGER_RANGES.items():
            self.assertEqual(
                {"type": "integer", "minimum": minimum, "maximum": maximum},
                properties[field],
            )
        for field, allowed in INTEGER_ENUMS.items():
            self.assertEqual({"enum": list(allowed)}, properties[field])
        self.assertEqual(
            {"enum": ["none", "otsu", "adaptive"]},
            properties["binarization_profile"],
        )

    def test_defaults_remain_valid(self) -> None:
        RestorationConfig()

    def test_boolean_fields_require_actual_booleans(self) -> None:
        for field in BOOLEAN_FIELDS:
            for value in (0, 1, "true", None):
                with self.subTest(field=field, value=value):
                    self.assert_invalid(**{field: value})

    def test_binarization_profile_requires_an_allowed_string(self) -> None:
        for value in ("none", "otsu", "adaptive"):
            RestorationConfig(binarization_profile=value)
        for value in ("invalid", 0, True, None):
            with self.subTest(value=value):
                self.assert_invalid(binarization_profile=value)

    def test_number_fields_reject_wrong_types_nan_and_infinity(self) -> None:
        for field in NUMBER_RANGES:
            invalid_values = (
                True,
                "0.5",
                None,
                float("nan"),
                float("inf"),
                -float("inf"),
            )
            for value in invalid_values:
                with self.subTest(field=field, value=repr(value)):
                    self.assert_invalid(**{field: value})

    def test_number_fields_enforce_inclusive_and_exclusive_bounds(self) -> None:
        for field, (minimum, maximum, minimum_is_inclusive) in NUMBER_RANGES.items():
            minimum_values = {field: minimum}
            maximum_values = {field: maximum}
            if field == "max_deskew_degrees":
                minimum_values["min_deskew_degrees"] = minimum
            elif field == "min_deskew_degrees":
                maximum_values["max_deskew_degrees"] = maximum
            elif field == "min_page_area_ratio":
                maximum_values = {field: 0.999, "max_page_area_ratio": 1}
            elif field == "max_page_area_ratio":
                minimum_values = {field: 0.001, "min_page_area_ratio": 0}
            with self.subTest(field=field, boundary="maximum"):
                RestorationConfig(**maximum_values)
            with self.subTest(field=field, boundary="below-minimum"):
                self.assert_invalid(**{field: minimum - 1})
            with self.subTest(field=field, boundary="above-maximum"):
                self.assert_invalid(**{field: maximum + 1})
            if minimum_is_inclusive:
                with self.subTest(field=field, boundary="minimum"):
                    RestorationConfig(**minimum_values)
            else:
                with self.subTest(field=field, boundary="exclusive-minimum"):
                    self.assert_invalid(**{field: minimum})

    def test_integer_fields_require_integers_and_enforce_bounds(self) -> None:
        for field, (minimum, maximum) in INTEGER_RANGES.items():
            for value in (True, float(minimum), "1", None, float("nan"), float("inf")):
                with self.subTest(field=field, value=repr(value)):
                    self.assert_invalid(**{field: value})
            with self.subTest(field=field, boundary="minimum"):
                RestorationConfig(**{field: minimum})
            with self.subTest(field=field, boundary="maximum"):
                RestorationConfig(**{field: maximum})
            with self.subTest(field=field, boundary="below-minimum"):
                self.assert_invalid(**{field: minimum - 1})
            with self.subTest(field=field, boundary="above-maximum"):
                self.assert_invalid(**{field: maximum + 1})

    def test_integer_enums_reject_booleans_and_unlisted_values(self) -> None:
        for field, allowed in INTEGER_ENUMS.items():
            for value in allowed:
                RestorationConfig(**{field: value})
            invalid_values = (
                True,
                False,
                float(allowed[0]),
                float("nan"),
                float("inf"),
                min(allowed) - 1,
                max(allowed) + 1,
            )
            for value in invalid_values:
                with self.subTest(field=field, value=repr(value)):
                    self.assert_invalid(**{field: value})

    def test_extreme_magnitudes_are_rejected_without_overflow(self) -> None:
        extreme = 10**1000
        for field in set(NUMBER_RANGES) | set(INTEGER_RANGES):
            for value in (extreme, -extreme):
                sign = "positive" if value > 0 else "negative"
                with self.subTest(field=field, sign=sign):
                    self.assert_invalid(**{field: value})

    def test_cross_field_safety_constraints_remain_enforced(self) -> None:
        self.assert_invalid(min_deskew_degrees=5, max_deskew_degrees=4)
        self.assert_invalid(min_page_area_ratio=0.5, max_page_area_ratio=0.5)
        self.assert_invalid(min_page_area_ratio=0.8, max_page_area_ratio=0.2)

    def test_from_mapping_rejects_non_objects_and_unknown_fields(self) -> None:
        for value in ([], "", 1, True):
            with self.subTest(value=repr(value)):
                with self.assertRaises(RestorationError) as caught:
                    RestorationConfig.from_mapping(value)  # type: ignore[arg-type]
                self.assertEqual("invalid_configuration", caught.exception.code)
        with self.assertRaises(RestorationError):
            RestorationConfig.from_mapping({"unknown": True})
        with self.assertRaises(RestorationError):
            RestorationConfig.from_mapping({1: True})  # type: ignore[dict-item]


if __name__ == "__main__":
    unittest.main()
