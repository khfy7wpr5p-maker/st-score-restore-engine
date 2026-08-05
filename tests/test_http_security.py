from __future__ import annotations

import json
import random
import unittest

from st_score_restore.http_security import (
    parse_multipart_form_data,
    parse_parameterized_header,
    safe_upload_name,
    validate_router_request,
)
from st_score_restore.job_api_types import JobApiConfig, JobApiError

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


def config(**overrides):
    values = dict(client_api_key=CLIENT_KEY, reviewer_api_key=REVIEWER_KEY)
    values.update(overrides)
    return JobApiConfig(**values)


def multipart(parts, boundary="safe-boundary-01", final_crlf=True):
    chunks=[]
    for headers, data in parts:
        chunks.append(f"--{boundary}\r\n".encode())
        for name,value in headers:
            chunks.append(f"{name}: {value}\r\n".encode("latin-1"))
        chunks.append(b"\r\n")
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--".encode())
    if final_crlf:
        chunks.append(b"\r\n")
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


class MultipartSecurityTests(unittest.TestCase):
    def test_binary_payload_is_preserved_exactly(self):
        binary = b"\x00\xffalpha\r\n--safe-boundary-01-not-a-delimiter\x00\r\n"
        body, content_type = multipart([
            ([
                ("Content-Disposition", 'form-data; name="file"; filename="folder\\score.png"'),
                ("Content-Type", "image/png"),
            ], binary)
        ])
        result = parse_multipart_form_data(content_type, body, config())
        self.assertEqual("score.png", result.pages[0].name)
        self.assertEqual(binary, result.pages[0].data)

    def test_restoration_config_and_file_are_parsed(self):
        body, content_type = multipart([
            ([
                ("Content-Disposition", 'form-data; name="restorationConfig"'),
                ("Content-Type", "application/json; charset=utf-8"),
            ], json.dumps({"deskew_enabled": False}).encode()),
            ([
                ("Content-Disposition", 'form-data; name="file"; filename="page.png"'),
                ("Content-Type", "image/png"),
            ], b"png-bytes"),
        ])
        result = parse_multipart_form_data(content_type, body, config())
        self.assertEqual({"deskew_enabled": False}, result.restoration_config)
        self.assertEqual(b"png-bytes", result.pages[0].data)

    def test_preamble_epilogue_lf_only_and_wrong_boundary_are_rejected(self):
        good, content_type = multipart([
            ([
                ("Content-Disposition", 'form-data; name="file"; filename="a.png"'),
                ("Content-Type", "image/png"),
            ], b"x")
        ])
        candidates = [
            b"preamble" + good,
            good + b"epilogue",
            good.replace(b"\r\n", b"\n"),
            good.replace(b"safe-boundary-01", b"other-boundary"),
        ]
        for body in candidates:
            with self.subTest(body=body[:20]):
                with self.assertRaises(JobApiError):
                    parse_multipart_form_data(content_type, body, config())

    def test_duplicate_and_unsupported_headers_are_rejected(self):
        cases = [
            [
                ("Content-Disposition", 'form-data; name="file"; filename="a.png"'),
                ("Content-Type", "image/png"),
                ("Content-Type", "image/png"),
            ],
            [
                ("Content-Disposition", 'form-data; name="file"; filename="a.png"'),
                ("Content-Type", "image/png"),
                ("Content-Transfer-Encoding", "base64"),
            ],
            [
                ("Content-Disposition", 'form-data; name="file"; filename="a.png"'),
                ("Content-Type", "image/png"),
                ("X-Unknown", "x"),
            ],
        ]
        for headers in cases:
            body, content_type = multipart([(headers, b"x")])
            with self.subTest(headers=headers):
                with self.assertRaises(JobApiError):
                    parse_multipart_form_data(content_type, body, config())

    def test_nested_mime_parameters_and_unsafe_filename_are_rejected(self):
        bad_types = ["multipart/mixed", "image/png; charset=utf-8", "text/plain"]
        for media_type in bad_types:
            body, content_type = multipart([
                ([
                    ("Content-Disposition", 'form-data; name="file"; filename="a.png"'),
                    ("Content-Type", media_type),
                ], b"x")
            ])
            with self.subTest(media_type=media_type):
                with self.assertRaises(JobApiError):
                    parse_multipart_form_data(content_type, body, config())
        for filename in ["..", ".hidden", "bad\x00name.png"]:
            body, content_type = multipart([
                ([
                    ("Content-Disposition", f'form-data; name="file"; filename="{filename}"'),
                    ("Content-Type", "image/png"),
                ], b"x")
            ])
            with self.subTest(filename=filename):
                with self.assertRaises(JobApiError):
                    parse_multipart_form_data(content_type, body, config())

    def test_part_and_header_limits_are_enforced(self):
        tiny = config(max_pages=1, max_multipart_parts=2, max_multipart_header_bytes=512,
                      max_multipart_header_line_bytes=128)
        parts=[]
        for name in ["a.png", "b.png"]:
            parts.append(([
                ("Content-Disposition", f'form-data; name="file"; filename="{name}"'),
                ("Content-Type", "image/png"),
            ], b"x"))
        body, content_type = multipart(parts)
        with self.assertRaises(JobApiError) as ctx:
            parse_multipart_form_data(content_type, body, tiny)
        self.assertEqual("too_many_pages", ctx.exception.code)
        huge_header = "x" * 300
        body, content_type = multipart([([
            ("Content-Disposition", f'form-data; name="file"; filename="{huge_header}.png"'),
            ("Content-Type", "image/png"),
        ], b"x")])
        with self.assertRaises(JobApiError):
            parse_multipart_form_data(content_type, body, tiny)

    def test_duplicate_boundary_parameter_is_rejected(self):
        body, _ = multipart([([
            ("Content-Disposition", 'form-data; name="file"; filename="a.png"'),
            ("Content-Type", "image/png"),
        ], b"x")])
        with self.assertRaises(JobApiError):
            parse_multipart_form_data(
                "multipart/form-data; boundary=safe-boundary-01; boundary=other",
                body,
                config(),
            )

    def test_deterministic_malformed_fuzz_never_escapes_stable_error(self):
        rng = random.Random(20260805)
        content_type = "multipart/form-data; boundary=fuzz-boundary"
        for _ in range(200):
            body = bytes(rng.randrange(0, 256) for _ in range(rng.randrange(0, 300)))
            try:
                parse_multipart_form_data(content_type, body, config())
            except JobApiError:
                pass
            except Exception as error:  # pragma: no cover - the assertion is the test
                self.fail(f"unexpected exception: {type(error).__name__}: {error}")


class RequestMetadataTests(unittest.TestCase):
    def test_duplicate_case_insensitive_headers_are_rejected(self):
        with self.assertRaises(JobApiError) as ctx:
            validate_router_request(
                "GET", "/health", {"X-Test": "a", "x-test": "b"}, b"", config()
            )
        self.assertEqual("duplicate_header", ctx.exception.code)

    def test_ambiguous_and_oversized_targets_are_rejected(self):
        targets = ["http://example.test/health", "/a\\b", "/x#fragment", "/%2fhidden"]
        for target in targets:
            with self.subTest(target=target):
                with self.assertRaises(JobApiError):
                    validate_router_request("GET", target, {}, b"", config())
        with self.assertRaises(JobApiError) as ctx:
            validate_router_request("GET", "/" + "a" * 5000, {}, b"", config())
        self.assertEqual(414, ctx.exception.http_status)

    def test_get_body_header_and_json_limits_are_enforced(self):
        with self.assertRaises(JobApiError):
            validate_router_request("GET", "/health", {}, b"x", config())
        with self.assertRaises(JobApiError):
            validate_router_request("GET", "/health", {"X-Large": "x" * 9000}, b"", config())

    def test_parameter_parser_and_filename_safety(self):
        media, params = parse_parameterized_header(
            'application/json; charset="utf-8"', "Content-Type"
        )
        self.assertEqual("application/json", media)
        self.assertEqual({"charset": "utf-8"}, params)
        self.assertEqual("a.png", safe_upload_name("C:\\fakepath\\a.png", 255))
        for value in ["", "..", ".x", "x\n.png"]:
            with self.assertRaises(JobApiError):
                safe_upload_name(value, 255)


if __name__ == "__main__":
    unittest.main()
