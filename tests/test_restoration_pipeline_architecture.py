from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from st_score_restore.job_api_types import JobApiConfig, UploadedPage
from st_score_restore.job_service import RestorationJobService
from st_score_restore.job_store import InMemoryJobStore


CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class _Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 11, 9, 30, tzinfo=UTC)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


class _Ids:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self, prefix: str) -> str:
        self.value += 1
        return f"{prefix}_{self.value:04d}"


def _encode_png(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return bytes(payload)


def _score_image() -> np.ndarray:
    image = np.full((900, 1200), 248, np.uint8)
    for base in (120, 360):
        for line in range(5):
            cv2.line(image, (80, base + line * 16), (1120, base + line * 16), 20, 1)
        for x in (220, 420, 650, 900):
            cv2.circle(image, (x, base + 32), 6, 0, -1)
            cv2.line(image, (x + 6, base + 32), (x + 6, base - 4), 0, 2)
    tab_base = 650
    for line in range(6):
        cv2.line(image, (80, tab_base + line * 18), (1120, tab_base + line * 18), 30, 1)
    cv2.putText(image, "3", (280, tab_base + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_8)
    cv2.putText(image, "10", (600, tab_base + 92), cv2.FONT_HERSHEY_SIMPLEX, 0.55, 0, 1, cv2.LINE_8)
    return image


def _service() -> RestorationJobService:
    config = JobApiConfig(
        client_api_key=CLIENT_KEY,
        reviewer_api_key=REVIEWER_KEY,
        retention_seconds=3600,
    )
    return RestorationJobService(
        InMemoryJobStore(),
        config,
        clock=_Clock(),
        id_factory=_Ids(),
    )


def _create_and_run(service: RestorationJobService, payload: bytes, *, key: str) -> str:
    created, _ = service.create_job(
        [UploadedPage("score.png", "image/png", payload)],
        idempotency_key=key,
        actor="client-app",
    )
    service.run_pending()
    return created["jobId"]


def _comparison_event(service: RestorationJobService, job_id: str) -> dict:
    events = service.get_audit(job_id)["events"]
    return next(event for event in events if event["eventType"] == "CANDIDATES_COMPARED")


class RestorationPipelineArchitectureRegressionTests(unittest.TestCase):
    def test_safety_validation_precedes_comparator(self) -> None:
        service = _service()
        job_id = _create_and_run(service, _encode_png(_score_image()), key="arch-order-0001")
        events = service.get_audit(job_id)["events"]
        event_types = [event["eventType"] for event in events]

        self.assertLess(
            event_types.index("PAGE_VALIDATED"),
            event_types.index("CANDIDATES_COMPARED"),
            "ADR 0015 requires per-variant safety validation before comparator eligibility.",
        )

    def test_rejected_restoration_variant_is_not_comparator_eligible(self) -> None:
        service = _service()
        source_image = _score_image()
        source_bytes = _encode_png(source_image)

        damaged = source_image.copy()
        cv2.rectangle(damaged, (60, 118), (1140, 126), 248, -1)
        candidate_bytes = _encode_png(damaged)
        source_digest = hashlib.sha256(source_bytes).hexdigest()
        candidate_digest = hashlib.sha256(candidate_bytes).hexdigest()
        manifest = {
            "status": "candidate_ready",
            "sourceDigest": {"algorithm": "sha256", "value": source_digest},
            "candidate": {
                "digest": {"algorithm": "sha256", "value": candidate_digest},
                "teacherApproved": False,
            },
        }

        with patch(
            "st_score_restore.job_service_processing.restore_bytes",
            return_value=SimpleNamespace(output_bytes=candidate_bytes, manifest=manifest),
        ):
            job_id = _create_and_run(service, source_bytes, key="arch-reject-0001")

        current = service.get_job(job_id)
        self.assertEqual("reject", current["pages"][0]["safetyReport"]["verdict"])

        compared = _comparison_event(service, job_id)
        self.assertEqual(
            0,
            compared["details"]["candidateCount"],
            "Rejected restoration variants must not be counted as comparator-eligible inputs.",
        )

    def test_original_is_always_present_as_selectable_comparator_baseline(self) -> None:
        service = _service()
        job_id = _create_and_run(service, _encode_png(_score_image()), key="arch-original-0001")
        current = service.get_job(job_id)
        source_artifact_id = current["pages"][0]["sourceArtifactId"]
        compared = _comparison_event(service, job_id)

        self.assertTrue(
            compared["details"]["originalSelectable"],
            "The immutable original must always remain selectable at the comparator boundary.",
        )
        self.assertEqual(source_artifact_id, compared["details"]["originalArtifactId"])


if __name__ == "__main__":
    unittest.main()
