"""Minimal standard-library HTTP adapter and worker for the M4 API baseline."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread
from typing import Type
from uuid import uuid4

from .http_api import ApiV1
from .job_service import RestorationJobService


class JobWorker:
    """One bounded worker with a unique durable lease owner identity."""

    def __init__(
        self,
        service: RestorationJobService,
        *,
        poll_seconds: float = 0.05,
        worker_id: str | None = None,
    ) -> None:
        self.service = service
        self.poll_seconds = max(0.01, float(poll_seconds))
        self.worker_id = (worker_id or f"worker-{uuid4().hex}").strip()
        if not self.worker_id:
            raise ValueError("worker_id must be a non-empty string")
        self._stop = Event()
        self._thread = Thread(
            target=self._run,
            name=f"st-score-{self.worker_id[:32]}",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                processed = self.service.run_pending(
                    actor="worker",
                    lease_owner=self.worker_id,
                )
            except Exception as error:  # fail closed without killing the worker loop
                print(f"worker error: {type(error).__name__}")
                processed = None
            if processed is None:
                self.service.cleanup_expired(actor="cleanup")
                self._stop.wait(self.poll_seconds)


def make_handler(api: ApiV1, *, max_request_bytes: int) -> Type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "STScoreRestore/0.4"
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch()

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch()

        def do_DELETE(self) -> None:  # noqa: N802
            self._dispatch()

        def _dispatch(self) -> None:
            if self.headers.get("Transfer-Encoding"):
                self.send_error(400, "Transfer-Encoding is not supported")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400, "Invalid Content-Length")
                return
            if length < 0 or length > max_request_bytes:
                self.send_error(413, "Request body too large")
                return
            body = self.rfile.read(length) if length else b""
            response = api.handle(self.command, self.path, dict(self.headers.items()), body)
            self.send_response(response.status)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            if response.body:
                self.wfile.write(response.body)

        def log_message(self, format: str, *args) -> None:
            message = format % args
            print(f"{self.client_address[0]} - {message}")

    return Handler


def create_server(
    host: str,
    port: int,
    api: ApiV1,
    service: RestorationJobService,
) -> tuple[ThreadingHTTPServer, JobWorker]:
    server = ThreadingHTTPServer(
        (host, int(port)),
        make_handler(api, max_request_bytes=service.config.max_upload_bytes + 2_000_000),
    )
    worker = JobWorker(service)
    return server, worker
