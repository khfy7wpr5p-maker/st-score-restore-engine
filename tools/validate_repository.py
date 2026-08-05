#!/usr/bin/env python3
"""Validate the repository contract using only approved runtime dependencies."""
from __future__ import annotations
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from st_score_restore.durable_job_store import STORE_SCHEMA_VERSION  # noqa: E402
from st_score_restore.fixture_manifest import FixtureCatalogError, load_catalog  # noqa: E402
from st_score_restore.input_inspection import INSPECTOR_VERSION, SCHEMA_VERSION as INPUT_SCHEMA_VERSION  # noqa: E402
from st_score_restore.job_api_types import API_VERSION  # noqa: E402
from st_score_restore.music_safety_validator import VALIDATOR_VERSION, SCHEMA_VERSION as SAFETY_SCHEMA_VERSION  # noqa: E402
from st_score_restore.safe_restoration import ENGINE_VERSION, SCHEMA_VERSION as RESTORE_SCHEMA_VERSION  # noqa: E402

REQUIRED_FILES = (
    "README.md", "CONTRIBUTING.md", "pyproject.toml", "requirements.lock",
    ".python-version", ".gitignore", ".editorconfig",
    "src/st_score_restore/__init__.py", "src/st_score_restore/fixture_manifest.py",
    "src/st_score_restore/input_inspection.py", "src/st_score_restore/safe_restoration.py",
    "src/st_score_restore/restoration_types.py", "src/st_score_restore/restoration_geometry.py",
    "src/st_score_restore/restoration_photometric.py", "src/st_score_restore/restoration_encoding.py",
    "src/st_score_restore/music_safety_types.py", "src/st_score_restore/music_safety_validator.py",
    "src/st_score_restore/job_api_types.py", "src/st_score_restore/job_store.py",
    "src/st_score_restore/durable_store_support.py", "src/st_score_restore/durable_blob_store.py",
    "src/st_score_restore/durable_job_store.py",
    "src/st_score_restore/durable_job_store_loading.py",
    "src/st_score_restore/durable_job_store_writing.py",
    "src/st_score_restore/durable_job_store_maintenance.py",
    "src/st_score_restore/job_service.py", "src/st_score_restore/job_service_processing.py",
    "src/st_score_restore/job_service_review.py", "src/st_score_restore/job_service_internal.py",
    "src/st_score_restore/job_service_support.py", "src/st_score_restore/http_api.py",
    "src/st_score_restore/http_server.py",
    "tests/README.md", "tests/test_fixture_manifest.py", "tests/test_input_inspection.py",
    "tests/test_safe_restoration.py", "tests/test_music_safety_validator.py",
    "tests/test_music_safety_hardening.py", "tests/test_job_api.py",
    "tests/test_job_review_atomicity.py", "tests/test_durable_job_store.py",
    "tests/test_durable_store_hardening.py", "tests/test_multi_worker_concurrency.py",
    "tests/test_worker_fencing_guard.py",
    "fixtures/README.md", "fixtures/catalog.v1.json",
    "schemas/fixture-manifest.schema.json", "schemas/artifact-manifest.schema.json",
    "schemas/input-analysis.schema.json", "schemas/restoration-config.schema.json",
    "schemas/restoration-candidate.schema.json", "schemas/music-safety-report.schema.json",
    "models/README.md", "api/README.md", "api/openapi.v1.json",
    "examples/README.md", "LICENSES/README.md",
    "LICENSES/opencv-python-headless-4.13.0.92.md", "LICENSES/numpy-2.3.5.md",
    "docs/technical-specification.md", "docs/roadmap.md", "docs/development-environment.md",
    "docs/dependency-and-license-policy.md", "docs/dependency-reviews/opencv-python-headless-4.13.0.92.md",
    "docs/fixture-governance.md", "docs/input-inspection-contract.md",
    "docs/safe-restoration-baseline.md", "docs/music-safety-validator.md",
    "docs/job-api-and-teacher-review.md", "docs/durable-local-persistence.md",
    "docs/multi-worker-concurrency-and-recovery.md",
    "docs/adr/0001-independent-safety-first-engine.md",
    "docs/adr/0002-python-runtime-and-repository-layout.md",
    "docs/adr/0003-fixture-consent-and-usage-governance.md",
    "docs/adr/0004-immutable-input-inspection.md",
    "docs/adr/0005-opencv-safe-restoration-baseline.md",
    "docs/adr/0006-music-tab-safety-validator.md",
    "docs/adr/0007-in-process-job-api-and-review-workflow.md",
    "docs/adr/0008-durable-local-persistence.md",
    "docs/adr/0009-attempt-bound-worker-fencing-and-recovery.md",
    "tools/validate_fixture_catalog.py", "tools/validate_dependency_lock.py",
    "tools/inspect_input.py", "tools/restore_image.py", "tools/validate_music_safety.py",
    "tools/run_api.py", ".github/workflows/repository-validation.yml",
)
FORBIDDEN_TRACKED_SUFFIXES = {".onnx", ".pt", ".pth", ".ckpt", ".safetensors"}
ALLOWED_FIXTURE_FILES = {Path("fixtures/README.md"), Path("fixtures/catalog.v1.json")}
REQUIRED_API_PATHS = {
    "/api/v1/restoration-jobs",
    "/api/v1/restoration-jobs/{jobId}",
    "/api/v1/restoration-jobs/{jobId}/status",
    "/api/v1/restoration-jobs/{jobId}/pages",
    "/api/v1/restoration-jobs/{jobId}/pages/{pageNumber}/candidates",
    "/api/v1/restoration-jobs/{jobId}/pages/{pageNumber}/safety-report",
    "/api/v1/restoration-jobs/{jobId}/review",
    "/api/v1/restoration-jobs/{jobId}/attempts",
    "/api/v1/restoration-jobs/{jobId}/cancel",
    "/api/v1/restoration-jobs/{jobId}/training-consent",
    "/api/v1/restoration-jobs/{jobId}/audit",
    "/api/v1/restoration-jobs/{jobId}/artifacts/{artifactId}",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required files: " + ", ".join(missing))


def validate_pyproject() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project", {})
    if project.get("name") != "st-score-restore-engine":
        fail("unexpected project.name")
    if project.get("version") != API_VERSION:
        fail("project.version must match the active job API version")
    if project.get("requires-python") != ">=3.11,<3.13":
        fail("unexpected project.requires-python")
    expected = ["numpy==2.3.5", "opencv-python-headless==4.13.0.92"]
    if project.get("dependencies") != expected:
        fail("unexpected approved runtime dependency graph")
    policy = data.get("tool", {}).get("st_score_restore", {})
    expected_flags = {
        "primary_python": "3.12",
        "production_restoration_enabled": False,
        "opencv_candidate_enabled": True,
        "music_safety_validator_enabled": True,
        "job_api_enabled": True,
        "in_memory_store_only": False,
        "durable_local_store_enabled": True,
        "multi_worker_fencing_enabled": True,
        "production_deployment_enabled": False,
    }
    for key, expected_value in expected_flags.items():
        if policy.get(key) != expected_value:
            fail(f"unexpected policy value for {key}")


def load_json(relative_path: Path) -> dict:
    with (ROOT / relative_path).open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as error:
            fail(f"invalid JSON in {relative_path}: {error}")
    if not isinstance(data, dict):
        fail(f"JSON root must be an object in {relative_path}")
    return data


def validate_json_documents() -> None:
    fixture_schema = load_json(Path("schemas/fixture-manifest.schema.json"))
    load_json(Path("fixtures/catalog.v1.json"))
    artifact_schema = load_json(Path("schemas/artifact-manifest.schema.json"))
    analysis_schema = load_json(Path("schemas/input-analysis.schema.json"))
    config_schema = load_json(Path("schemas/restoration-config.schema.json"))
    candidate_schema = load_json(Path("schemas/restoration-candidate.schema.json"))
    safety_schema = load_json(Path("schemas/music-safety-report.schema.json"))
    openapi = load_json(Path("api/openapi.v1.json"))
    if fixture_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("fixture manifest must use JSON Schema Draft 2020-12")
    if artifact_schema.get("properties", {}).get("schemaVersion", {}).get("const") != INPUT_SCHEMA_VERSION:
        fail("artifact manifest schema version does not match the inspector")
    if analysis_schema.get("properties", {}).get("schemaVersion", {}).get("const") != INPUT_SCHEMA_VERSION:
        fail("input analysis schema version does not match the inspector")
    if config_schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("restoration config must use JSON Schema Draft 2020-12")
    if candidate_schema.get("properties", {}).get("schemaVersion", {}).get("const") != RESTORE_SCHEMA_VERSION:
        fail("candidate manifest schema version does not match the engine")
    if candidate_schema.get("properties", {}).get("engine", {}).get("const") != "opencv_safe_baseline":
        fail("candidate manifest engine identifier is unexpected")
    if safety_schema.get("properties", {}).get("schemaVersion", {}).get("const") != SAFETY_SCHEMA_VERSION:
        fail("music safety report schema version does not match the validator")
    validator_pattern = safety_schema.get("properties", {}).get("validatorVersion", {}).get("pattern")
    if validator_pattern != r"^\d+\.\d+\.\d+$":
        fail("music safety validatorVersion pattern is unexpected")
    if safety_schema.get("properties", {}).get("automaticApproval", {}).get("const") is not False:
        fail("music safety reports must prohibit automatic approval")
    pixel_limit = config_schema.get("properties", {}).get("max_decode_pixels", {})
    if pixel_limit.get("maximum") != 200_000_000:
        fail("restoration config decoded-pixel ceiling is unexpected")
    candidate_name_pattern = candidate_schema.get("properties", {}).get("candidate", {}).get("properties", {}).get("candidateName", {}).get("pattern")
    try:
        re.compile(candidate_name_pattern or "")
    except re.error as error:
        fail(f"candidateName schema pattern is invalid: {error}")
    if openapi.get("openapi") != "3.1.0":
        fail("OpenAPI contract must use version 3.1.0")
    if openapi.get("info", {}).get("version") != API_VERSION:
        fail("OpenAPI info.version must match the job API version")
    missing_paths = sorted(REQUIRED_API_PATHS - set(openapi.get("paths", {})))
    if missing_paths:
        fail("OpenAPI contract is missing paths: " + ", ".join(missing_paths))
    bearer = openapi.get("components", {}).get("securitySchemes", {}).get("bearerAuth", {})
    if bearer.get("type") != "http" or bearer.get("scheme") != "bearer":
        fail("OpenAPI bearerAuth scheme is missing or invalid")
    review_description = openapi.get("paths", {}).get("/api/v1/restoration-jobs/{jobId}/review", {}).get("post", {}).get("description", "")
    if "never creates training consent" not in review_description:
        fail("OpenAPI review contract must separate approval from training consent")
    if not INSPECTOR_VERSION or not ENGINE_VERSION or not VALIDATOR_VERSION or not API_VERSION:
        fail("runtime component versions must not be empty")
    if STORE_SCHEMA_VERSION != 1:
        fail("unexpected durable local store schema version")


def validate_fixture_contract() -> None:
    try:
        catalog = load_catalog(ROOT / "fixtures" / "catalog.v1.json")
    except (OSError, ValueError, FixtureCatalogError) as error:
        fail(f"fixture catalog validation failed: {error}")
    available = [fixture["fixtureId"] for fixture in catalog["fixtures"] if fixture["artifact"]["state"] == "available"]
    if available:
        fail("fixture artifacts remain prohibited in ordinary Git: " + ", ".join(available))


def validate_sensitive_artifacts() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in FORBIDDEN_TRACKED_SUFFIXES:
            fail(f"unapproved model weight found: {path.relative_to(ROOT)}")
        if path.stat().st_size > 1_000_000:
            fail(f"unexpected tracked file larger than 1 MB: {path.relative_to(ROOT)}")
    unexpected = [path.relative_to(ROOT) for path in (ROOT / "fixtures").rglob("*") if path.is_file() and path.relative_to(ROOT) not in ALLOWED_FIXTURE_FILES]
    if unexpected:
        fail("unapproved fixture files found: " + ", ".join(map(str, unexpected)))


def validate_runtime_data_ignores() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    required = {"runtime-data/", "*.sqlite3", "*.sqlite3-wal", "*.sqlite3-shm"}
    missing = sorted(pattern for pattern in required if pattern not in ignored)
    if missing:
        fail("durable runtime data ignore patterns are missing: " + ", ".join(missing))


def main() -> None:
    validate_required_files()
    validate_pyproject()
    validate_json_documents()
    validate_fixture_contract()
    validate_sensitive_artifacts()
    validate_runtime_data_ignores()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
