"""Hardened standard-library HTTP adapter and bounded local worker."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import socket
from threading import BoundedSemaphore, Event, Thread
from typing import Type
from uuid import uuid4

from .http_api import ApiResponse, ApiV1
from .job_api_types import API_SCHEMA_VERSION, API_VERSION, JobApiConfig
from .job_service import RestorationJobService

_HEADER_TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_DIGITS = re.compile(r"^[0-9]+$")
_SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
}


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


class HardenedThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    request_queue_size = 16
    allow_reuse_address = False

    def __init__(self, server_address, handler_class, *, max_concurrent_requests: int):
        self._request_slots = BoundedSemaphore(int(max_concurrent_requests))
        super().__init__(server_address, handler_class)

    def process_request(self, request, client_address) -> None:
        if not self._request_slots.acquire(blocking=False):
            try:
                request.settimeout(0.25)
                request.sendall(_raw_http_response(_transport_error(503, "server_busy", "The local adapter has reached its concurrent request limit.")))
            except OSError:
                pass
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self._request_slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


def make_handler(api: ApiV1, *, config: JobApiConfig) -> Type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "STScoreRestore"
        sys_version = ""
        protocol_version = "HTTP/1.1"

        def setup(self) -> None:
            super().setup()
            self.connection.settimeout(float(config.connection_timeout_seconds))

        def send_error(self, code, message=None, explain=None) -> None:
            """Replace stdlib HTML/parser errors with stable JSON and close."""

            mapping = {
                400: (400, "malformed_http_request", "The HTTP request is malformed."),
                413: (413, "request_body_too_large", "The HTTP request exceeds the configured body limit."),
                414: (414, "request_target_too_long", "The HTTP request target exceeds the configured limit."),
                431: (431, "headers_too_large", "The HTTP request headers exceed the parser limit."),
                501: (405, "method_not_allowed", "The built-in adapter accepts only GET, POST, and DELETE."),
                505: (505, "http_version_not_supported", "The built-in adapter accepts HTTP/1.1 only."),
            }
            status, error_code, error_message = mapping.get(
                int(code),
                (int(code), "http_protocol_error", "The HTTP request was rejected by the protocol parser."),
            )
            self.close_connection = True
            self._safe_write_response(
                _transport_error(status, error_code, error_message),
                force_close=True,
            )

        def handle_expect_100(self) -> bool:
            self.close_connection = True
            self._safe_write_response(
                _transport_error(
                    417,
                    "expectation_forbidden",
                    "Expect request handling is not supported.",
                ),
                force_close=True,
            )
            return False

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch()

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch()

        def do_DELETE(self) -> None:  # noqa: N802
            self._dispatch()

        def do_HEAD(self) -> None:  # noqa: N802
            self._method_not_allowed()

        def do_PUT(self) -> None:  # noqa: N802
            self._method_not_allowed()

        def do_PATCH(self) -> None:  # noqa: N802
            self._method_not_allowed()

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._method_not_allowed()

        def do_TRACE(self) -> None:  # noqa: N802
            self._method_not_allowed()

        def do_CONNECT(self) -> None:  # noqa: N802
            self._method_not_allowed()

        def _method_not_allowed(self) -> None:
            self.close_connection = True
            self._safe_write_response(
                _transport_error(
                    405,
                    "method_not_allowed",
                    "The built-in adapter accepts only GET, POST, and DELETE.",
                ),
                force_close=True,
            )

        def _dispatch(self) -> None:
            try:
                length = self._validated_content_length()
                body = self.rfile.read(length) if length else b""
                if len(body) != length:
                    self.close_connection = True
                    self._safe_write_response(
                        _transport_error(
                            400,
                            "incomplete_request_body",
                            "The request body ended before Content-Length bytes were received.",
                        ),
                        force_close=True,
                    )
                    return
                response = api.handle(
                    self.command,
                    self.path,
                    {name: value for name, value in self.headers.raw_items()},
                    body,
                )
                self._safe_write_response(response, force_close=True)
            except socket.timeout:
                self.close_connection = True
                self._safe_write_response(
                    _transport_error(
                        408,
                        "request_timeout",
                        "The request exceeded the configured connection inactivity timeout.",
                    ),
                    force_close=True,
                )
            except TransportRejection as rejection:
                self.close_connection = True
                self._safe_write_response(
                    _transport_error(rejection.status, rejection.code, rejection.message),
                    force_close=True,
                )
            except (BrokenPipeError, ConnectionResetError, OSError):
                self.close_connection = True

        def _validated_content_length(self) -> int:
            if self.request_version != "HTTP/1.1":
                raise TransportRejection(505, "http_version_not_supported", "The built-in adapter accepts HTTP/1.1 only.")
            if len(self.path.encode("utf-8", "surrogatepass")) > config.max_request_target_bytes:
                raise TransportRejection(414, "request_target_too_long", "The HTTP request target exceeds the configured limit.")
            raw_items = list(self.headers.raw_items())
            if len(raw_items) > config.max_header_count:
                raise TransportRejection(431, "too_many_headers", "The request contains too many headers.")
            total = 0
            seen: set[str] = set()
            for name, value in raw_items:
                lowered = name.lower()
                if not _HEADER_TOKEN.fullmatch(name):
                    raise TransportRejection(400, "invalid_header_name", "A request header name is invalid.")
                if lowered in seen and lowered not in {"content-length", "host"}:
                    raise TransportRejection(400, "duplicate_header", "Duplicate request headers are forbidden.")
                seen.add(lowered)
                if "\r" in value or "\n" in value or "\x00" in value:
                    raise TransportRejection(400, "invalid_header_value", "Header folding and control characters are forbidden.")
                try:
                    value_bytes = value.encode("latin-1")
                except UnicodeEncodeError as error:
                    raise TransportRejection(400, "invalid_header_value", "Header values must be ISO-8859-1 compatible.") from error
                line_size = len(name.encode("ascii")) + len(value_bytes) + 2
                if line_size > config.max_header_line_bytes:
                    raise TransportRejection(431, "header_line_too_large", "A request header line exceeds the configured limit.")
                total += line_size + 2
            if total > config.max_header_bytes:
                raise TransportRejection(431, "headers_too_large", "The request headers exceed the configured aggregate limit.")

            host_values = self.headers.get_all("Host") or []
            if len(host_values) != 1 or not host_values[0].strip():
                raise TransportRejection(400, "invalid_host_header", "HTTP/1.1 requests require exactly one non-empty Host header.")
            if self.headers.get_all("Transfer-Encoding"):
                raise TransportRejection(400, "transfer_encoding_forbidden", "Transfer-Encoding is not supported.")
            if self.headers.get_all("Upgrade"):
                raise TransportRejection(400, "protocol_upgrade_forbidden", "Protocol upgrades are not supported.")
            if self.headers.get_all("Trailer") or self.headers.get_all("TE"):
                raise TransportRejection(400, "trailer_header_forbidden", "Trailer negotiation and trailer headers are not supported.")
            if self.headers.get_all("Proxy-Connection"):
                raise TransportRejection(400, "proxy_connection_forbidden", "Proxy-Connection is not supported.")
            if self.headers.get_all("Content-Range"):
                raise TransportRejection(400, "content_range_forbidden", "Partial request bodies are not supported.")
            content_encoding = self.headers.get("Content-Encoding")
            if content_encoding and content_encoding.strip().lower() != "identity":
                raise TransportRejection(415, "content_encoding_forbidden", "Compressed request bodies are not supported.")
            if self.headers.get_all("Expect"):
                raise TransportRejection(417, "expectation_forbidden", "Expect request handling is not supported.")

            connection = self.headers.get("Connection", "")
            if connection:
                tokens = {item.strip().lower() for item in connection.split(",") if item.strip()}
                if len(tokens) != 1 or not tokens <= {"close", "keep-alive"}:
                    raise TransportRejection(400, "invalid_connection_header", "The Connection header is ambiguous or contains unsupported tokens.")

            values = self.headers.get_all("Content-Length") or []
            if len(values) > 1:
                raise TransportRejection(400, "duplicate_content_length", "Multiple Content-Length headers are forbidden.")
            if values:
                value = values[0].strip()
                if not _DIGITS.fullmatch(value):
                    raise TransportRejection(400, "invalid_content_length", "Content-Length must be one non-negative decimal integer.")
                if len(value) > 20:
                    raise TransportRejection(413, "request_body_too_large", "The request body exceeds the configured limit.")
                length = int(value)
            else:
                if self.command == "POST":
                    raise TransportRejection(411, "content_length_required", "POST requests require Content-Length.")
                length = 0
            if self.command in {"GET", "HEAD", "DELETE"} and length:
                raise TransportRejection(400, "unexpected_request_body", "This method does not accept a request body.")
            route_path = self.path.split("?", 1)[0].rstrip("/") or "/"
            if self.command == "POST" and route_path == "/api/v1/restoration-jobs":
                body_limit = config.max_request_bytes
            elif self.command == "POST":
                body_limit = config.max_json_bytes
            else:
                body_limit = 0
            if length > body_limit:
                raise TransportRejection(413, "request_body_too_large", "The request body exceeds the configured route limit.")
            return length

        def _safe_write_response(self, response: ApiResponse, *, force_close: bool) -> None:
            try:
                self._write_response(response, force_close=force_close)
            except (BrokenPipeError, ConnectionResetError, socket.timeout, OSError):
                self.close_connection = True

        def _write_response(self, response: ApiResponse, *, force_close: bool) -> None:
            self.send_response(response.status)
            emitted = {key.lower() for key in response.headers}
            for key, value in response.headers.items():
                self.send_header(key, value)
            for key, value in _SECURITY_HEADERS.items():
                if key.lower() not in emitted:
                    self.send_header(key, value)
            if force_close:
                self.send_header("Connection", "close")
                self.close_connection = True
            self.end_headers()
            if response.body and self.command != "HEAD":
                self.wfile.write(response.body)
                self.wfile.flush()

        def log_message(self, format: str, *args) -> None:
            message = (format % args).replace("\r", " ").replace("\n", " ")[:1_024]
            address = str(self.client_address[0]).replace("\r", " ").replace("\n", " ")[:128]
            print(f"{address} - {message}")

    return Handler


class TransportRejection(ValueError):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = int(status)
        self.code = code
        self.message = message


def _transport_error(status: int, code: str, message: str) -> ApiResponse:
    body = json.dumps(
        {
            "schemaVersion": API_SCHEMA_VERSION,
            "apiVersion": API_VERSION,
            "status": "error",
            "error": {"code": code, "message": message, "details": {}},
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return ApiResponse(
        int(status),
        {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Request-Id": "transport-rejected",
        },
        body,
    )


def _raw_http_response(response: ApiResponse) -> bytes:
    reason = {400: "Bad Request", 403: "Forbidden", 405: "Method Not Allowed", 408: "Request Timeout", 411: "Length Required", 413: "Content Too Large", 414: "URI Too Long", 415: "Unsupported Media Type", 417: "Expectation Failed", 431: "Request Header Fields Too Large", 503: "Service Unavailable", 505: "HTTP Version Not Supported"}.get(response.status, "Error")
    headers = dict(response.headers)
    headers.update(_SECURITY_HEADERS)
    headers["Connection"] = "close"
    lines = [f"HTTP/1.1 {response.status} {reason}\r\n".encode("ascii")]
    for key, value in headers.items():
        lines.append(f"{key}: {value}\r\n".encode("latin-1"))
    lines.append(b"\r\n")
    lines.append(response.body)
    return b"".join(lines)


def create_server(
    host: str,
    port: int,
    api: ApiV1,
    service: RestorationJobService,
) -> tuple[ThreadingHTTPServer, JobWorker]:
    server = HardenedThreadingHTTPServer(
        (host, int(port)),
        make_handler(api, config=service.config),
        max_concurrent_requests=service.config.max_concurrent_requests,
    )
    worker = JobWorker(service)
    return server, worker
