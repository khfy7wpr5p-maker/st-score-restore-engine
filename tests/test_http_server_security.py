from __future__ import annotations

import json
import socket
import threading
import time
import unittest

from st_score_restore.http_api import ApiResponse
from st_score_restore.http_server import HardenedThreadingHTTPServer, make_handler
from st_score_restore.job_api_types import JobApiConfig

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class DummyApi:
    def handle(self, method, target, headers, body=b""):
        payload = json.dumps({"method": method, "target": target, "length": len(body)}, sort_keys=True).encode()
        return ApiResponse(
            200,
            {
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
                "Cache-Control": "no-store",
            },
            payload,
        )


class ServerHarness:
    def __init__(self, config: JobApiConfig):
        self.server = HardenedThreadingHTTPServer(
            ("127.0.0.1", 0),
            make_handler(DummyApi(), config=config),
            max_concurrent_requests=config.max_concurrent_requests,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        self.thread.start()

    @property
    def address(self):
        return self.server.server_address

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, data: bytes, *, shutdown_write=False, read_timeout=2.0) -> bytes:
        sock = socket.create_connection(self.address, timeout=2)
        try:
            sock.settimeout(read_timeout)
            sock.sendall(data)
            if shutdown_write:
                sock.shutdown(socket.SHUT_WR)
            chunks=[]
            while True:
                try:
                    chunk=sock.recv(65536)
                except socket.timeout:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            sock.close()


def config(**overrides):
    values=dict(
        client_api_key=CLIENT_KEY,
        reviewer_api_key=REVIEWER_KEY,
        max_header_count=16,
        max_header_line_bytes=256,
        max_header_bytes=2048,
        max_request_target_bytes=512,
        connection_timeout_seconds=0.2,
        max_concurrent_requests=8,
    )
    values.update(overrides)
    return JobApiConfig(**values)


def status(response: bytes) -> int:
    line=response.split(b"\r\n",1)[0]
    return int(line.split()[1])


def body_json(response: bytes):
    body=response.split(b"\r\n\r\n",1)[1]
    return json.loads(body)


class HttpServerSecurityTests(unittest.TestCase):
    def setUp(self):
        self.harness=ServerHarness(config())

    def tearDown(self):
        self.harness.close()

    def test_valid_request_uses_security_headers_and_closes_connection(self):
        response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(200,status(response))
        lowered=response.lower()
        self.assertIn(b"content-security-policy:",lowered)
        self.assertIn(b"x-frame-options: deny",lowered)
        self.assertIn(b"connection: close",lowered)

    def test_duplicate_content_length_and_host_are_rejected(self):
        requests=[
            b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n",
            b"GET /health HTTP/1.1\r\nHost: one\r\nHost: two\r\n\r\n",
        ]
        expected=["duplicate_content_length","invalid_host_header"]
        for raw,code in zip(requests,expected):
            with self.subTest(code=code):
                response=self.harness.request(raw)
                self.assertEqual(400,status(response))
                self.assertEqual(code,body_json(response)["error"]["code"])

    def test_transfer_upgrade_trailer_and_expect_are_rejected(self):
        cases=[
            (b"POST /x HTTP/1.1\r\nHost: localhost\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n\r\n",400,"transfer_encoding_forbidden"),
            (b"GET /health HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: upgrade\r\n\r\n",400,"protocol_upgrade_forbidden"),
            (b"GET /health HTTP/1.1\r\nHost: localhost\r\nTrailer: X-Later\r\n\r\n",400,"trailer_header_forbidden"),
            (b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\nExpect: 100-continue\r\n\r\n",417,"expectation_forbidden"),
        ]
        for raw,expected_status,code in cases:
            with self.subTest(code=code):
                response=self.harness.request(raw)
                self.assertEqual(expected_status,status(response))
                self.assertEqual(code,body_json(response)["error"]["code"])
                self.assertNotIn(b"100 Continue",response)

    def test_target_header_count_line_and_aggregate_limits(self):
        long_target=b"/"+b"a"*600
        response=self.harness.request(b"GET "+long_target+b" HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(414,status(response))
        many=[b"GET /health HTTP/1.1",b"Host: localhost"]+[f"X-{i}: a".encode() for i in range(20)]+[b"",b""]
        response=self.harness.request(b"\r\n".join(many))
        self.assertEqual(431,status(response))
        response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\nX-Large: "+b"a"*300+b"\r\n\r\n")
        self.assertEqual(431,status(response))

    def test_post_requires_length_get_rejects_body_and_incomplete_body_fails(self):
        response=self.harness.request(b"POST /x HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(411,status(response))
        response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1\r\n\r\nx")
        self.assertEqual(400,status(response))
        response=self.harness.request(
            b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 10\r\n\r\nabc",
            shutdown_write=True,
        )
        self.assertEqual(400,status(response))
        self.assertEqual("incomplete_request_body",body_json(response)["error"]["code"])

    def test_slow_body_hits_inactivity_timeout(self):
        sock=socket.create_connection(self.harness.address,timeout=2)
        try:
            sock.settimeout(2)
            sock.sendall(b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 10\r\n\r\na")
            time.sleep(0.35)
            chunks=[]
            while True:
                chunk=sock.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            response=b"".join(chunks)
        finally:
            sock.close()
        self.assertEqual(408,status(response))
        self.assertEqual("request_timeout",body_json(response)["error"]["code"])

    def test_huge_decimal_length_json_route_limit_and_content_encoding_fail_early(self):
        response=self.harness.request(b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 999999999999999999999999999999\r\n\r\n")
        self.assertEqual(413,status(response))
        response=self.harness.request(b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 1000001\r\n\r\n")
        self.assertEqual(413,status(response))
        response=self.harness.request(b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\nContent-Encoding: gzip\r\n\r\n")
        self.assertEqual(415,status(response))
        self.assertEqual("content_encoding_forbidden",body_json(response)["error"]["code"])

    def test_http_1_0_and_ambiguous_connection_are_rejected(self):
        response=self.harness.request(b"GET /health HTTP/1.0\r\nHost: localhost\r\n\r\n")
        self.assertEqual(505,status(response))
        response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: keep-alive, close\r\n\r\n")
        self.assertEqual(400,status(response))
        self.assertEqual("invalid_connection_header",body_json(response)["error"]["code"])

    def test_concurrent_request_limit_returns_503_without_new_worker_thread(self):
        self.harness.close()
        self.harness=ServerHarness(config(max_concurrent_requests=1, connection_timeout_seconds=1.0))
        first=socket.create_connection(self.harness.address,timeout=2)
        try:
            first.sendall(b"POST /x HTTP/1.1\r\nHost: localhost\r\nContent-Length: 10\r\n\r\na")
            time.sleep(0.05)
            response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
            self.assertEqual(503,status(response))
            self.assertEqual("server_busy",body_json(response)["error"]["code"])
        finally:
            first.close()

    def test_unsupported_method_is_structured_405(self):
        response=self.harness.request(b"PUT /health HTTP/1.1\r\nHost: localhost\r\nContent-Length: 0\r\n\r\n")
        self.assertEqual(405,status(response))
        self.assertEqual("method_not_allowed",body_json(response)["error"]["code"])

    def test_obsolete_header_folding_is_rejected(self):
        response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\nX-Test: a\r\n b\r\n\r\n")
        self.assertEqual(400,status(response))
        self.assertEqual("invalid_header_value",body_json(response)["error"]["code"])

    def test_stdlib_parser_errors_and_unknown_methods_are_structured_json(self):
        response=self.harness.request(b"BREW /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(405,status(response))
        self.assertEqual("method_not_allowed",body_json(response)["error"]["code"])
        response=self.harness.request(b"GET /"+b"a"*70000+b" HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(414,status(response))
        self.assertEqual("request_target_too_long",body_json(response)["error"]["code"])
        response=self.harness.request(b"GET /health HTTP/1.1\r\nHost: localhost\r\nX-Large: "+b"a"*70000+b"\r\n\r\n")
        self.assertEqual(431,status(response))
        self.assertEqual("headers_too_large",body_json(response)["error"]["code"])


if __name__ == "__main__":
    unittest.main()
