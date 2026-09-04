"""Stage 6 production identity/authz wrapper around the local ApiV1 contract.

The existing ApiV1 remains a local/internal adapter. This wrapper is the only
Stage 6 production-authenticated entry contract: caller credentials are verified
externally, caller-supplied identity headers and static API keys are rejected,
and only opaque derived principal identifiers are passed into the local router.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
import secrets
from typing import Mapping, Protocol
from urllib.parse import urlsplit

from .http_api import ApiResponse, ApiV1
from .job_api_types import JobApiConfig, JobApiError
from .production_identity import AuthenticatedIdentity, ProductionIdentityAdapter


@dataclass(frozen=True)
class JobAuthorizationContext:
    tenant_key: str
    owner_key: str


class JobAuthorizationStore(Protocol):
    """Durable production implementations are supplied by the Stage 6 storage boundary."""

    def bind_job(self, job_id: str, context: JobAuthorizationContext) -> None:
        """Create or idempotently confirm the security binding for a job."""
        ...

    def get_job_context(self, job_id: str) -> JobAuthorizationContext | None:
        ...


class ProductionApiV1:
    """Provider-neutral production identity and authorization enforcement."""

    def __init__(
        self,
        service,
        local_config: JobApiConfig,
        identity_adapter: ProductionIdentityAdapter,
        authorization_store: JobAuthorizationStore,
    ) -> None:
        if identity_adapter is None or authorization_store is None:
            raise JobApiError(
                "invalid_production_auth_configuration",
                "Production API requires identity and authorization adapters.",
                http_status=500,
            )
        self.identity_adapter = identity_adapter
        self.authorization_store = authorization_store
        self._client_capability = secrets.token_urlsafe(48)
        self._reviewer_capability = secrets.token_urlsafe(48)
        internal_config = replace(
            local_config,
            client_api_key=self._client_capability,
            reviewer_api_key=self._reviewer_capability,
        )
        self._local_api = ApiV1(service, internal_config)

    def handle(
        self,
        method: str,
        target: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> ApiResponse:
        request_id = self._header(headers, "x-request-id") or "request-unassigned"
        try:
            path = urlsplit(target).path.rstrip("/") or "/"
            if path == "/health" and method.upper() == "GET":
                return self._local_api.handle(method, target, headers, body)

            self._reject_untrusted_identity_headers(headers)
            identity = self._authenticate(headers)
            job_id = self._job_id_from_path(path)
            if job_id is not None:
                self._authorize_job(identity, job_id)

            internal_headers = self._internal_headers(headers, identity)
            response = self._local_api.handle(method, target, internal_headers, body)
            if path == "/api/v1/restoration-jobs" and method.upper() == "POST" and response.status in {200, 202}:
                job_id = self._response_job_id(response)
                self._bind_job(identity, job_id)
            return response
        except JobApiError as error:
            return self._error_response(error, request_id)
        except Exception:
            return self._error_response(
                JobApiError(
                    "production_auth_boundary_failure",
                    "The production identity boundary failed closed.",
                    http_status=500,
                ),
                request_id,
            )

    def _authenticate(self, headers: Mapping[str, str]) -> AuthenticatedIdentity:
        authorization = self._header(headers, "authorization") or ""
        if not authorization.lower().startswith("bearer "):
            raise JobApiError(
                "production_authentication_required",
                "A production bearer identity is required.",
                http_status=401,
            )
        token = authorization[7:]
        if not token or token != token.strip():
            raise JobApiError(
                "invalid_bearer_token",
                "The production bearer token is malformed.",
                http_status=401,
            )
        return self.identity_adapter.authenticate_bearer_token(token)

    def _reject_untrusted_identity_headers(self, headers: Mapping[str, str]) -> None:
        if self._header(headers, "x-api-key") is not None:
            raise JobApiError(
                "production_static_credential_forbidden",
                "Static API keys are forbidden as production caller identity.",
                http_status=401,
            )
        if self._header(headers, "x-actor-id") is not None:
            raise JobApiError(
                "caller_supplied_identity_forbidden",
                "Caller-supplied actor identity is forbidden in production.",
                http_status=400,
            )

    def _authorize_job(self, identity: AuthenticatedIdentity, job_id: str) -> None:
        try:
            context = self.authorization_store.get_job_context(job_id)
        except Exception as error:
            raise JobApiError(
                "authorization_store_unavailable",
                "Job authorization state could not be verified.",
                http_status=503,
            ) from error
        if not isinstance(context, JobAuthorizationContext):
            raise JobApiError(
                "job_security_context_missing",
                "The job has no valid production authorization binding.",
                http_status=403,
            )
        if identity.tenant_key is None or context.tenant_key != identity.tenant_key:
            raise JobApiError(
                "tenant_access_forbidden",
                "The authenticated tenant cannot access this job.",
                http_status=403,
            )
        if identity.role == "client":
            if identity.subject_key is None or context.owner_key != identity.subject_key:
                raise JobApiError(
                    "job_ownership_forbidden",
                    "The authenticated client does not own this job.",
                    http_status=403,
                )
        elif identity.role != "reviewer":
            raise JobApiError(
                "identity_role_not_permitted",
                "The authenticated role cannot access production jobs.",
                http_status=403,
            )

    def _bind_job(self, identity: AuthenticatedIdentity, job_id: str) -> None:
        if identity.tenant_key is None or identity.subject_key is None:
            raise JobApiError(
                "invalid_production_principal",
                "Production job creation requires tenant and owner identity.",
                http_status=500,
            )
        context = JobAuthorizationContext(
            tenant_key=identity.tenant_key,
            owner_key=identity.subject_key,
        )
        try:
            self.authorization_store.bind_job(job_id, context)
        except JobApiError:
            raise
        except Exception as error:
            raise JobApiError(
                "authorization_binding_failed",
                "The job security binding could not be committed.",
                http_status=503,
            ) from error
        try:
            confirmed = self.authorization_store.get_job_context(job_id)
        except Exception as error:
            raise JobApiError(
                "authorization_store_unavailable",
                "The job security binding could not be verified.",
                http_status=503,
            ) from error
        if confirmed != context:
            raise JobApiError(
                "authorization_binding_conflict",
                "The job security binding does not match the authenticated principal.",
                http_status=403,
            )

    def _internal_headers(
        self,
        headers: Mapping[str, str],
        identity: AuthenticatedIdentity,
    ) -> dict[str, str]:
        external_idempotency_key = self._header(headers, "idempotency-key")
        sanitized = {
            str(key): str(value)
            for key, value in headers.items()
            if str(key).lower() not in {
                "authorization",
                "x-api-key",
                "x-actor-id",
                "idempotency-key",
            }
        }
        capability = self._reviewer_capability if identity.role == "reviewer" else self._client_capability
        sanitized["Authorization"] = f"Bearer {capability}"
        sanitized["X-Actor-Id"] = identity.actor_id
        if external_idempotency_key is not None:
            self._validate_external_idempotency_key(external_idempotency_key)
            sanitized["Idempotency-Key"] = self._scoped_idempotency_key(
                identity,
                external_idempotency_key,
            )
        return sanitized

    @staticmethod
    def _scoped_idempotency_key(
        identity: AuthenticatedIdentity,
        external_key: str,
    ) -> str:
        if identity.tenant_key is None or identity.subject_key is None:
            raise JobApiError(
                "invalid_production_principal",
                "Production idempotency requires tenant and owner identity.",
                http_status=500,
            )
        material = (
            f"{identity.tenant_key}\x00{identity.subject_key}\x00{external_key}"
        ).encode("utf-8")
        return f"prod-{hashlib.sha256(material).hexdigest()}"

    @staticmethod
    def _validate_external_idempotency_key(value: str) -> None:
        if not 8 <= len(value) <= 128 or any(character.isspace() for character in value):
            raise JobApiError(
                "invalid_idempotency_key",
                "Idempotency-Key must contain 8 to 128 non-whitespace characters.",
            )

    @staticmethod
    def _job_id_from_path(path: str) -> str | None:
        match = re.fullmatch(r"/api/v1/restoration-jobs/([^/]+)(?:/.*)?", path)
        return match.group(1) if match else None

    @staticmethod
    def _response_job_id(response: ApiResponse) -> str:
        try:
            payload = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise JobApiError(
                "invalid_job_creation_response",
                "The local job API returned an invalid creation response.",
                http_status=500,
            ) from error
        job_id = payload.get("jobId") if isinstance(payload, dict) else None
        if not isinstance(job_id, str) or not job_id:
            raise JobApiError(
                "invalid_job_creation_response",
                "The local job API did not return a valid job identifier.",
                http_status=500,
            )
        return job_id

    @staticmethod
    def _header(headers: Mapping[str, str], name: str) -> str | None:
        target = name.lower()
        values = [str(value) for key, value in headers.items() if str(key).lower() == target]
        if not values:
            return None
        if len(values) != 1:
            raise JobApiError(
                "ambiguous_header",
                "A security-sensitive header was supplied more than once.",
                http_status=400,
                details={"header": name},
            )
        return values[0]

    @staticmethod
    def _error_response(error: JobApiError, request_id: str) -> ApiResponse:
        body = json.dumps(error.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return ApiResponse(
            error.http_status,
            {
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": str(len(body)),
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "X-Request-Id": request_id,
            },
            body,
        )
