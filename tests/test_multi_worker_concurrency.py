from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

import cv2
import numpy as np

from st_score_restore.durable_job_store import SQLiteJobStore, StaleWorkClaimError
from st_score_restore.job_api_types import JobApiConfig, JobApiError, UploadedPage
from st_score_restore.job_service import RestorationJobService
from st_score_restore.job_service_support import _artifact_id

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class MutableClock:
    def __init__(self, value: datetime) -> None:
        self.value = value
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            return self.value

    def set(self, value: datetime) -> None:
        with self.lock:
            self.value = value


def encode_png(image: np.ndarray) -> bytes:
    ok, payload = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    assert ok
    return bytes(payload)


def synthetic_page(marker: str = "10") -> bytes:
    image = np.full((720, 960), 248, np.uint8)
    for base in (100, 300):
        for line in range(5):
            cv2.line(image, (60, base + line * 14), (900, base + line * 14), 20, 1)
        for x in (180, 360, 560, 760):
            cv2.circle(image, (x, base + 28), 5, 0, -1)
            cv2.line(image, (x + 5, base + 28), (x + 5, base - 3), 0, 1)
    tab_base = 520
    for line in range(6):
        cv2.line(image, (60, tab_base + line * 16), (900, tab_base + line * 16), 30, 1)
    cv2.putText(
        image,
        marker,
        (470, tab_base + 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        0,
        1,
        cv2.LINE_8,
    )
    return encode_png(image)


def config() -> JobApiConfig:
    return JobApiConfig(
        client_api_key=CLIENT_KEY,
        reviewer_api_key=REVIEWER_KEY,
        retention_seconds=3_600,
    )


def make_service(directory: str, clock: MutableClock, *, lease_seconds: int = 10):
    store = SQLiteJobStore(directory, worker_lease_seconds=lease_seconds)
    return store, RestorationJobService(store, config(), clock=clock)


def verify_audit(events: list[dict]) -> None:
    previous = None
    for sequence, event in enumerate(events, 1):
        assert event["sequence"] == sequence
        assert event["previousEventHash"] == previous
        unsigned = {key: value for key, value in event.items() if key != "eventHash"}
        canonical = json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        assert hashlib.sha256(canonical).hexdigest() == event["eventHash"]
        previous = event["eventHash"]


class MultiWorkerConcurrencyTests(unittest.TestCase):
    def test_concurrent_identical_idempotency_creates_one_job(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = MutableClock(datetime.now(UTC))
            pairs = [make_service(directory, clock), make_service(directory, clock)]
            barrier = threading.Barrier(2)
            results: list[tuple[dict, bool]] = []
            errors: list[BaseException] = []
            page = UploadedPage("page.png", "image/png", synthetic_page())

            def create(service: RestorationJobService) -> None:
                try:
                    barrier.wait()
                    results.append(
                        service.create_job(
                            [page],
                            idempotency_key="concurrent-identical-0001",
                            actor="client",
                        )
                    )
                except BaseException as error:
                    errors.append(error)

            threads = [threading.Thread(target=create, args=(service,)) for _, service in pairs]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual([], errors)
            self.assertEqual(2, len(results))
            self.assertEqual(1, len({record[0]["jobId"] for record in results}))
            self.assertEqual([False, True], sorted(record[1] for record in results))
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            self.assertEqual(1, database.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])
            self.assertEqual(1, database.execute("SELECT COUNT(*) FROM idempotency").fetchone()[0])
            database.close()
            for store, _ in pairs:
                store.close()

    def test_concurrent_conflicting_idempotency_has_one_winner(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = MutableClock(datetime.now(UTC))
            pairs = [make_service(directory, clock), make_service(directory, clock)]
            barrier = threading.Barrier(2)
            successes: list[dict] = []
            error_codes: list[str] = []

            def create(service: RestorationJobService, marker: str) -> None:
                try:
                    barrier.wait()
                    record, _ = service.create_job(
                        [UploadedPage("page.png", "image/png", synthetic_page(marker))],
                        idempotency_key="concurrent-conflict-0001",
                        actor="client",
                    )
                    successes.append(record)
                except JobApiError as error:
                    error_codes.append(error.code)

            threads = [
                threading.Thread(target=create, args=(pairs[0][1], "10")),
                threading.Thread(target=create, args=(pairs[1][1], "11")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(1, len(successes))
            self.assertEqual(["idempotency_conflict"], error_codes)
            database = sqlite3.connect(Path(directory) / "store.sqlite3")
            self.assertEqual(1, database.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])
            self.assertEqual(1, database.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0])
            database.close()
            for store, _ in pairs:
                store.close()

    def test_stale_token_is_fenced_and_live_token_is_renewed(self):
        with tempfile.TemporaryDirectory() as directory:
            base = datetime.now(UTC)
            clock = MutableClock(base)
            first, service = make_service(directory, clock, lease_seconds=5)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="fence-claim-0001",
                actor="client",
            )
            second = SQLiteJobStore(directory, worker_lease_seconds=5)
            old = first.claim_next_job(now=base, lease_owner="worker-a", lease_seconds=5)
            self.assertIsNotNone(old)
            current = second.claim_next_job(
                now=base + timedelta(seconds=6),
                lease_owner="worker-b",
                lease_seconds=5,
            )
            self.assertIsNotNone(current)
            with self.assertRaises(StaleWorkClaimError):
                with first.processing_claim(old, now_provider=lambda: base + timedelta(seconds=6)):
                    with first.lock:
                        first.jobs[created["jobId"]]["cancelRequested"] = True
            self.assertEqual("UPLOADED", service.get_job(created["jobId"])["state"])
            with second.processing_claim(
                current,
                now_provider=lambda: base + timedelta(seconds=7),
            ):
                with second.lock:
                    self.assertEqual("UPLOADED", second.jobs[created["jobId"]]["state"])
            second.assert_claim(current, now=base + timedelta(seconds=11))
            first.close()
            second.close()

    def test_expired_inflight_claim_recovers_and_partial_candidate_is_not_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = datetime.now(UTC)
            clock = MutableClock(base)
            first, service = make_service(directory, clock, lease_seconds=5)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="crash-recovery-0001",
                actor="client",
            )
            job_id = created["jobId"]
            claim = first.claim_next_job(now=base, lease_owner="worker-a", lease_seconds=5)
            self.assertIsNotNone(claim)
            partial = b"partial-candidate-not-a-valid-image"
            partial_id = _artifact_id(partial)
            with first.processing_claim(claim, now_provider=lambda: base):
                with first.lock:
                    job = first.jobs[job_id]
                    service._transition(job, "ANALYZING", "worker-a")
                    service._transition(job, "READY_FOR_PROCESSING", "worker-a")
                    service._transition(job, "PROCESSING", "worker-a")
                    service._store_artifact(
                        job,
                        artifact_id=partial_id,
                        attempt_id=job["currentAttemptId"],
                        page_number=1,
                        role="restoration_candidate",
                        name="partial.png",
                        media_type="image/png",
                        data=partial,
                    )
                    job["pages"][0]["currentCandidateArtifactId"] = partial_id
                    service._append_event(
                        job,
                        "CANDIDATE_CREATED",
                        "worker-a",
                        {"pageNumber": 1, "candidateArtifactId": partial_id, "partial": True},
                        job["currentAttemptId"],
                    )
            clock.set(base + timedelta(seconds=6))
            second, recovered_service = make_service(directory, clock, lease_seconds=5)
            self.assertEqual(
                job_id,
                recovered_service.run_pending(actor="worker", lease_owner="worker-b"),
            )
            recovered = recovered_service.get_job(job_id)
            self.assertEqual("AWAITING_REVIEW", recovered["state"])
            self.assertNotEqual(partial_id, recovered["pages"][0]["currentCandidateArtifactId"])
            self.assertIn((job_id, partial_id), second.artifacts)
            events = recovered_service.get_audit(job_id)["events"]
            self.assertIn("WORK_LEASE_RECOVERED", [event["eventType"] for event in events])
            verify_audit(events)
            with self.assertRaises(StaleWorkClaimError):
                with first.processing_claim(
                    claim,
                    now_provider=lambda: base + timedelta(seconds=6),
                ):
                    with first.lock:
                        first.jobs[job_id]["state"] = "FAILED"
            first.close()
            second.close()

    def test_three_workers_process_each_job_once(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = MutableClock(datetime.now(UTC))
            seed, service = make_service(directory, clock, lease_seconds=30)
            job_ids = []
            for index in range(4):
                created, _ = service.create_job(
                    [UploadedPage("page.png", "image/png", synthetic_page(str(index)))],
                    idempotency_key=f"worker-stress-{index:04d}",
                    actor="client",
                )
                job_ids.append(created["jobId"])
            seed.close()
            pairs = [make_service(directory, clock, lease_seconds=30) for _ in range(3)]
            barrier = threading.Barrier(3)
            processed: list[str] = []
            errors: list[BaseException] = []

            def worker(service: RestorationJobService, owner: str) -> None:
                try:
                    barrier.wait()
                    while True:
                        job_id = service.run_pending(actor="worker", lease_owner=owner)
                        if job_id is None:
                            return
                        processed.append(job_id)
                except BaseException as error:
                    errors.append(error)

            threads = [
                threading.Thread(target=worker, args=(pair[1], f"worker-{index}"))
                for index, pair in enumerate(pairs)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual([], errors)
            self.assertCountEqual(job_ids, processed)
            self.assertEqual(len(job_ids), len(set(processed)))
            verifier = pairs[0][1]
            for job_id in job_ids:
                self.assertEqual("AWAITING_REVIEW", verifier.get_job(job_id)["state"])
                verify_audit(verifier.get_audit(job_id)["events"])
            for store, _ in pairs:
                store.close()

    def test_review_cancel_race_serializes_to_one_valid_terminal_state(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = MutableClock(datetime.now(UTC))
            first, service = make_service(directory, clock, lease_seconds=30)
            created, _ = service.create_job(
                [UploadedPage("page.png", "image/png", synthetic_page())],
                idempotency_key="review-cancel-race-0001",
                actor="client",
            )
            job_id = created["jobId"]
            service.run_pending(actor="worker", lease_owner="worker-a")
            second, other = make_service(directory, clock, lease_seconds=30)
            barrier = threading.Barrier(2)
            successes: list[str] = []
            error_codes: list[str] = []

            def review() -> None:
                try:
                    barrier.wait()
                    service.review_job(
                        job_id,
                        [{"pageNumber": 1, "action": "reject"}],
                        reviewer_id="teacher-1",
                    )
                    successes.append("review")
                except JobApiError as error:
                    error_codes.append(error.code)

            def cancel() -> None:
                try:
                    barrier.wait()
                    other.cancel_job(job_id, actor="client")
                    successes.append("cancel")
                except JobApiError as error:
                    error_codes.append(error.code)

            threads = [threading.Thread(target=review), threading.Thread(target=cancel)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(1, len(successes))
            self.assertEqual(1, len(error_codes))
            final = other.get_job(job_id)
            self.assertIn(final["state"], {"COMPLETED", "CANCELLED"})
            verify_audit(other.get_audit(job_id)["events"])
            first.close()
            second.close()


if __name__ == "__main__":
    unittest.main()
