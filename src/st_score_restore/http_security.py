"""Strict, deterministic HTTP metadata and multipart parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Mapping
from urllib.parse import urlsplit

from .job_api_types import JobApiConfig, JobApiError, UploadedPage

_TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_MEDIA_TYPE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+/[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_BOUNDARY = re.compile(r"^[0-9A-Za-z'()+_,./:=?-]{1,70}$")
_CONTROL = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")
_FILENAME_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_INVALID_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")


@dataclass(frozen=True)
class MultipartResult:
    pages: list[UploadedPage]
    restoration_config: dict


def validate_router_request(
    method: str,
    target: str,
    headers: Mapping[str, str],
    body: bytes,
    config: JobApiConfig,
) -> None:
    if not isinstance(method, str) or not _TOKEN.fullmatch(method):
        raise JobApiError("invalid_http_method", "The HTTP method token is invalid.")
    if not isinstance(target, str):
        raise JobApiError("invalid_request_target", "The request target must be text.")
    try:
        target_size = len(target.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise JobApiError("invalid_request_target", "The request target is not valid UTF-8.") from error
    if target_size > config.max_request_target_bytes:
        raise JobApiError("request_target_too_long", "The HTTP request target exceeds the configured limit.", http_status=414)
    if _CONTROL.search(target) or "\\" in target or _INVALID_PERCENT.search(target):
        raise JobApiError("invalid_request_target", "The HTTP request target contains forbidden or malformed characters.")
    try:
        split = urlsplit(target)
    except ValueError as error:
        raise JobApiError("invalid_request_target", "The HTTP request target could not be parsed.") from error
    lowered_path = split.path.lower()
    if any(encoded in lowered_path for encoded in ("%00", "%2f", "%5c")):
        raise JobApiError("ambiguous_request_target", "Encoded path delimiters and NUL bytes are forbidden.")
    if split.scheme or split.netloc or split.fragment or not split.path.startswith("/"):
        raise JobApiError("ambiguous_request_target", "Only origin-form request targets without fragments are accepted.")
    if len(headers) > config.max_header_count:
        raise JobApiError("too_many_headers", "The request contains too many headers.", http_status=431)
    total = 0
    seen_names: set[str] = set()
    for name, value in headers.items():
        if not isinstance(name, str) or not _TOKEN.fullmatch(name):
            raise JobApiError("invalid_header_name", "A request header name is invalid.", http_status=400)
        lowered_name = name.lower()
        if lowered_name in seen_names:
            raise JobApiError("duplicate_header", "Duplicate request headers are forbidden.", http_status=400, details={"header": lowered_name})
        seen_names.add(lowered_name)
        if not isinstance(value, str) or "\r" in value or "\n" in value or "\x00" in value:
            raise JobApiError("invalid_header_value", "A request header value is invalid.", http_status=400)
        try:
            value_bytes = value.encode("latin-1")
        except UnicodeEncodeError as error:
            raise JobApiError("invalid_header_value", "Request header values must be ISO-8859-1 compatible.", http_status=400) from error
        line_size = len(name.encode("ascii")) + len(value_bytes) + 2
        if line_size > config.max_header_line_bytes:
            raise JobApiError("header_line_too_large", "A request header line exceeds the configured limit.", http_status=431)
        total += line_size + 2
    if total > config.max_header_bytes:
        raise JobApiError("headers_too_large", "The request headers exceed the configured aggregate limit.", http_status=431)
    if not isinstance(body, bytes):
        raise JobApiError("invalid_request_body", "The HTTP request body must be immutable bytes.")
    if len(body) > config.max_request_bytes:
        raise JobApiError("request_body_too_large", "The HTTP request body exceeds the configured limit.", http_status=413)
    if method.upper() in {"GET", "HEAD"} and body:
        raise JobApiError("unexpected_request_body", "This HTTP method does not accept a request body.")


def parse_json_object(body: bytes, config: JobApiConfig) -> dict:
    if not body:
        return {}
    if len(body) > config.max_json_bytes:
        raise JobApiError("json_body_too_large", "The JSON request body exceeds the configured limit.", http_status=413)
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise JobApiError("invalid_json", "The JSON request body is invalid.") from error
    if not isinstance(parsed, dict):
        raise JobApiError("invalid_json_root", "JSON request root must be an object.")
    return parsed


def parse_multipart_form_data(
    content_type: str,
    body: bytes,
    config: JobApiConfig,
) -> MultipartResult:
    media_type, parameters = parse_parameterized_header(content_type, "Content-Type")
    if media_type != "multipart/form-data":
        raise JobApiError("invalid_multipart", "The request is not multipart/form-data.")
    if set(parameters) != {"boundary"}:
        raise JobApiError("ambiguous_multipart_content_type", "multipart/form-data requires exactly one boundary parameter.")
    boundary = parameters.get("boundary")
    if boundary is None or not _BOUNDARY.fullmatch(boundary):
        raise JobApiError("invalid_multipart_boundary", "The multipart boundary is missing or unsafe.")
    try:
        delimiter = b"--" + boundary.encode("ascii")
    except UnicodeEncodeError as error:
        raise JobApiError("invalid_multipart_boundary", "The multipart boundary must be ASCII.") from error
    if not body.startswith(delimiter + b"\r\n"):
        raise JobApiError("invalid_multipart_framing", "Multipart bodies must start with the declared boundary and CRLF.")

    pages: list[UploadedPage] = []
    restoration_config: dict = {}
    saw_restoration_config = False
    position = len(delimiter) + 2
    part_count = 0
    while True:
        part_count += 1
        if part_count > config.max_multipart_parts:
            raise JobApiError("too_many_multipart_parts", "The multipart body contains too many parts.", http_status=413)
        header_end = body.find(b"\r\n\r\n", position)
        if header_end < 0:
            raise JobApiError("invalid_multipart_framing", "A multipart part is missing its header terminator.")
        header_block = body[position:header_end]
        if len(header_block) > config.max_multipart_header_bytes:
            raise JobApiError("multipart_headers_too_large", "Multipart part headers exceed the configured limit.", http_status=413)
        headers = _parse_part_headers(header_block, config)
        data_start = header_end + 4
        marker = b"\r\n" + delimiter
        search_from = data_start
        while True:
            next_boundary = body.find(marker, search_from)
            if next_boundary < 0:
                raise JobApiError("invalid_multipart_framing", "A multipart part is missing its closing boundary.")
            after = next_boundary + len(marker)
            trailer = body[after:after + 2]
            if trailer in {b"--", b"\r\n"}:
                break
            search_from = next_boundary + 2
        payload = body[data_start:next_boundary]
        final = False
        if trailer == b"--":
            final = True
            tail = body[after + 2:]
            if tail not in {b"", b"\r\n"}:
                raise JobApiError("multipart_epilogue_forbidden", "Multipart epilogues are not accepted.")
        else:
            position = after + 2

        disposition = headers.get("content-disposition")
        if disposition is None:
            raise JobApiError("missing_content_disposition", "Every multipart part requires Content-Disposition.")
        disposition_type, disposition_params = parse_parameterized_header(disposition, "Content-Disposition")
        if disposition_type != "form-data":
            raise JobApiError("invalid_content_disposition", "Multipart parts must use form-data disposition.")
        if set(disposition_params) - {"name", "filename"}:
            raise JobApiError("invalid_content_disposition", "Multipart Content-Disposition contains unsupported parameters.")
        field = disposition_params.get("name")
        if field is None:
            raise JobApiError("missing_multipart_field_name", "Every multipart part requires a name parameter.")
        filename = disposition_params.get("filename")
        if "content-transfer-encoding" in headers:
            raise JobApiError("content_transfer_encoding_forbidden", "Multipart transfer encodings are not accepted.")

        part_content_type = headers.get("content-type")
        if field == "file":
            if filename is None:
                raise JobApiError("missing_filename", "Each file field must include a filename.")
            safe_name = safe_upload_name(filename, config.max_filename_bytes)
            if part_content_type is None:
                raise JobApiError("missing_part_content_type", "Each file field requires Content-Type.", http_status=415)
            part_media_type, part_parameters = parse_parameterized_header(part_content_type, "Content-Type")
            if part_parameters:
                raise JobApiError("ambiguous_part_content_type", "File part Content-Type parameters are not accepted.", http_status=415)
            if part_media_type.startswith("multipart/"):
                raise JobApiError("nested_multipart_forbidden", "Nested multipart bodies are not supported.")
            if part_media_type not in config.allowed_content_types:
                raise JobApiError("unsupported_media_type", "The uploaded page media type is not permitted.", http_status=415, details={"contentType": part_media_type})
            if len(pages) >= config.max_pages:
                raise JobApiError("too_many_pages", "The request exceeds the configured page limit.", http_status=413, details={"maxPages": config.max_pages})
            pages.append(UploadedPage(safe_name, part_media_type, bytes(payload)))
        elif field == "restorationConfig":
            if filename is not None:
                raise JobApiError("invalid_restoration_config_part", "restorationConfig must not include a filename.")
            if saw_restoration_config:
                raise JobApiError("duplicate_restoration_config", "Only one restorationConfig field is permitted.")
            saw_restoration_config = True
            if part_content_type is not None:
                config_media, config_parameters = parse_parameterized_header(part_content_type, "Content-Type")
                if config_media not in {"application/json", "text/plain"}:
                    raise JobApiError("invalid_restoration_config_content_type", "restorationConfig must be JSON text.", http_status=415)
                if set(config_parameters) - {"charset"}:
                    raise JobApiError("invalid_restoration_config_content_type", "restorationConfig Content-Type contains unsupported parameters.", http_status=415)
                charset = config_parameters.get("charset", "utf-8").lower()
                if charset not in {"utf-8", "utf8"}:
                    raise JobApiError("unsupported_restoration_config_charset", "restorationConfig must use UTF-8.", http_status=415)
            restoration_config = parse_json_object(bytes(payload), config)
        else:
            raise JobApiError("unexpected_multipart_field", "The multipart request contains an unsupported field.", details={"field": field})

        if final:
            break
    if not pages:
        raise JobApiError("missing_file", "At least one source page is required.")
    return MultipartResult(pages, restoration_config)


def parse_parameterized_header(value: str, header_name: str) -> tuple[str, dict[str, str]]:
    if not isinstance(value, str) or not value or "\r" in value or "\n" in value or "\x00" in value:
        raise JobApiError("invalid_header_value", f"{header_name} is invalid.")
    segments = _split_semicolon(value)
    primary = segments[0].strip().lower()
    if not (_TOKEN.fullmatch(primary) or _MEDIA_TYPE.fullmatch(primary)):
        raise JobApiError("invalid_header_value", f"{header_name} has an invalid primary value.")
    parameters: dict[str, str] = {}
    for segment in segments[1:]:
        if not segment.strip() or "=" not in segment:
            raise JobApiError("invalid_header_parameter", f"{header_name} contains an invalid parameter.")
        name, raw = segment.split("=", 1)
        name = name.strip().lower()
        if not _TOKEN.fullmatch(name) or name in parameters or name.endswith("*"):
            raise JobApiError("invalid_header_parameter", f"{header_name} contains a duplicate or unsupported parameter.", details={"parameter": name})
        parameters[name] = _unquote_parameter(raw.strip(), header_name)
    return primary, parameters


def safe_upload_name(value: str, max_bytes: int) -> str:
    if not isinstance(value, str) or not value or _FILENAME_CONTROL.search(value):
        raise JobApiError("unsafe_filename", "The uploaded filename is empty or contains control characters.")
    name = value.replace("\\", "/").rsplit("/", 1)[-1]
    if name in {"", ".", ".."} or name.startswith("."):
        raise JobApiError("unsafe_filename", "The uploaded filename is not permitted.")
    if len(name.encode("utf-8")) > max_bytes:
        raise JobApiError("filename_too_long", "The uploaded filename exceeds the configured limit.", http_status=413)
    return name


def _parse_part_headers(block: bytes, config: JobApiConfig) -> dict[str, str]:
    if b"\n" in block.replace(b"\r\n", b"") or b"\r" in block.replace(b"\r\n", b""):
        raise JobApiError("invalid_multipart_headers", "Multipart headers must use CRLF line endings.")
    lines = block.split(b"\r\n") if block else []
    if not lines or len(lines) > config.max_multipart_header_count:
        raise JobApiError("invalid_multipart_headers", "Multipart header count is invalid.", http_status=413 if lines else 400)
    result: dict[str, str] = {}
    for line in lines:
        if len(line) > config.max_multipart_header_line_bytes:
            raise JobApiError("multipart_header_line_too_large", "A multipart header line exceeds the configured limit.", http_status=413)
        if not line or line[:1] in {b" ", b"\t"} or b":" not in line:
            raise JobApiError("invalid_multipart_headers", "Multipart header folding and malformed lines are forbidden.")
        raw_name, raw_value = line.split(b":", 1)
        try:
            name = raw_name.decode("ascii").strip().lower()
            value = raw_value.decode("latin-1").strip()
        except UnicodeDecodeError as error:
            raise JobApiError("invalid_multipart_headers", "Multipart header names must be ASCII.") from error
        if not _TOKEN.fullmatch(name) or _CONTROL.search(value):
            raise JobApiError("invalid_multipart_headers", "A multipart header is invalid.")
        if name in result:
            raise JobApiError("duplicate_multipart_header", "Duplicate multipart headers are forbidden.", details={"header": name})
        if name not in {"content-disposition", "content-type", "content-transfer-encoding"}:
            raise JobApiError("unexpected_multipart_header", "The multipart part contains an unsupported header.", details={"header": name})
        result[name] = value
    return result


def _split_semicolon(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    quoted = False
    escaped = False
    for index, character in enumerate(value):
        if escaped:
            escaped = False
        elif character == "\\" and quoted:
            escaped = True
        elif character == '"':
            quoted = not quoted
        elif character == ";" and not quoted:
            parts.append(value[start:index])
            start = index + 1
    if quoted or escaped:
        raise JobApiError("invalid_header_parameter", "A quoted header parameter is not terminated.")
    parts.append(value[start:])
    return parts


def _unquote_parameter(value: str, header_name: str) -> str:
    if not value:
        raise JobApiError("invalid_header_parameter", f"{header_name} contains an empty parameter.")
    if value.startswith('"'):
        if len(value) < 2 or not value.endswith('"'):
            raise JobApiError("invalid_header_parameter", f"{header_name} contains an unterminated parameter.")
        inner = value[1:-1]
        output: list[str] = []
        escaped = False
        for character in inner:
            if escaped:
                if character in {'"', "\\"}:
                    output.append(character)
                elif ord(character) < 32 or ord(character) == 127:
                    raise JobApiError("invalid_header_parameter", f"{header_name} contains an unsafe escape.")
                else:
                    output.extend(("\\", character))
                escaped = False
            elif character == "\\":
                escaped = True
            else:
                output.append(character)
        if escaped:
            raise JobApiError("invalid_header_parameter", f"{header_name} contains an unterminated escape.")
        result = "".join(output)
    else:
        if not _TOKEN.fullmatch(value):
            raise JobApiError("invalid_header_parameter", f"{header_name} contains an unsafe unquoted parameter.")
        result = value
    if not result or _FILENAME_CONTROL.search(result):
        raise JobApiError("invalid_header_parameter", f"{header_name} contains an invalid parameter value.")
    return result
