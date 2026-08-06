"""Shared Draft 2020-12 schema validation helpers for Stage 1A."""
from __future__ import annotations
from typing import Any
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from st_score_restore.dataset_manifest import DatasetManifestError


def required(schema: dict[str, Any], where: str) -> set[str]:
    raw = schema.get("required")
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise DatasetManifestError(f"{where}.required must be a string array")
    return set(raw)


def enum(schema: dict[str, Any], where: str) -> set[Any]:
    raw = schema.get("enum")
    if not isinstance(raw, list):
        raise DatasetManifestError(f"{where}.enum must be an array")
    return set(raw)


def pattern(schema: dict[str, Any], expected: str, where: str) -> None:
    if schema.get("pattern") != expected:
        raise DatasetManifestError(f"{where} pattern drift")


def const(schema: dict[str, Any], expected: Any, where: str) -> None:
    if schema.get("const") != expected:
        raise DatasetManifestError(f"{where} constant drift")


def properties(schema: dict[str, Any], where: str) -> dict[str, Any]:
    value = schema.get("properties")
    if not isinstance(value, dict):
        raise DatasetManifestError(f"{where}.properties must be an object")
    return value


def assert_schema_valid(schema: dict[str, Any], where: str) -> None:
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise DatasetManifestError(
            f"{where} is not valid Draft 2020-12: {error.message}"
        ) from error


def validate_with_schema(instance: dict[str, Any], schema: dict[str, Any], where: str) -> None:
    try:
        Draft202012Validator(schema).validate(instance)
    except ValidationError as error:
        raise DatasetManifestError(
            f"{where} JSON Schema validation failed: {error.message}"
        ) from error
